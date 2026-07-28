#!/usr/bin/env python3
"""Generate tests/bench_alloc.c — M19.1 slab allocator benchmark."""
import os

C_CODE = r"""/*
 * bench_alloc.c — M19.1: Benchmark de latencia, throughput y fragmentacion
 *                 del slab allocator del runtime Synapse (pool_alloc/pool_free).
 *
 * Especificacion Tecnica Definitiva Fase 19 — Aprobada 2026-07-28
 *
 * Compilacion (asan):
 *   gcc -O2 -std=c99 -Wall -fsanitize=address -g
 *       tests/bench_alloc.c synapse_rt_memory.o -o tests/bench_alloc_asan.exe
 *       -lm -lpthread -lws2_32 -lpsapi
 *
 * Compilacion (tsan):
 *   gcc -O2 -std=c99 -Wall -fsanitize=thread -g
 *       tests/bench_alloc.c synapse_rt_memory.o -o tests/bench_alloc_tsan.exe
 *       -lm -lpthread -lws2_32 -lpsapi
 *
 * Uso: tests/bench_alloc.exe [opciones]
 *   --threads N       Hilos (defecto: 1)
 *   --warmup N        Warmup descartado (defecto: 2000)
 *   --measure N       Iteraciones medidas (defecto: 100000)
 *   --slab size|all   Slab class (defecto: all)
 *   --csv             Salida CSV
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <inttypes.h>

#ifdef _WIN32
  #include <winsock2.h>
  #include <windows.h>
  #include <psapi.h>
  #pragma comment(lib, "psapi")
#else
  #include <time.h>
  #include <unistd.h>
  #include <sched.h>
  #include <sys/resource.h>
  #include <sys/time.h>
#endif

#include <pthread.h>

/* Slab allocator externs */
extern void pool_init(uint32_t total_blocks, uint32_t block_size);
extern void* pool_alloc(size_t size);
extern void pool_free(void* ptr);
extern void pool_destroy(void);

#define SLAB_CLASSES        4
#define HISTOGRAM_BUCKETS   256
#define POOL_BLOCKS         65536
#define POOL_BLOCK_SIZE     256

static const uint32_t SLAB_SIZES[SLAB_CLASSES] = {32, 64, 128, 256};
static const char* SLAB_NAMES[SLAB_CLASSES] = {"32B", "64B", "128B", "256B"};
#define NS_PER_BUCKET       100
#define HISTO_MAX_NS        ((uint64_t)HISTOGRAM_BUCKETS * NS_PER_BUCKET)

/* Histograma estatico — SIN alloc dinamica durante medicion */
static uint64_t g_histogram[SLAB_CLASSES][HISTOGRAM_BUCKETS];
static uint64_t g_total_ops[SLAB_CLASSES];
static uint64_t g_overflow[SLAB_CLASSES];

/* Temporizador QPC (Windows) / clock_gettime (POSIX) */
#ifdef _WIN32
static LARGE_INTEGER g_qpc_freq;
static double g_ns_per_tick;
static void timer_init(void) {
    QueryPerformanceFrequency(&g_qpc_freq);
    g_ns_per_tick = 1e9 / (double)g_qpc_freq.QuadPart;
}
static uint64_t timer_now_ns(void) {
    LARGE_INTEGER pc;
    QueryPerformanceCounter(&pc);
    return (uint64_t)((double)pc.QuadPart * g_ns_per_tick);
}
#else
static void timer_init(void) { }
static uint64_t timer_now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}
#endif

/* RSS measurement */
static size_t get_rss_bytes(void) {
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS pmc;
    pmc.cb = sizeof(pmc);
    if (GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof(pmc)))
        return (size_t)pmc.WorkingSetSize;
    return 0;
#else
    long rss = 0;
    FILE* f = fopen("/proc/self/status", "r");
    if (!f) return 0;
    char line[256];
    while (fgets(line, sizeof(line), f)) {
        if (sscanf(line, "VmRSS: %ld kB", &rss) == 1) {
            fclose(f);
            return (size_t)rss * 1024;
        }
    }
    fclose(f);
    return 0;
#endif
}

typedef struct {
    int thread_id;
    int slab_idx;
    uint32_t warmup_ops;
    uint32_t measure_ops;
    uint64_t thread_ops;
    uint64_t thread_ns_total;
    uint64_t thread_ns_min;
    uint64_t thread_ns_max;
} ThreadData;

/* Benchmark thread function */
static void* bench_thread(void* arg) {
    ThreadData* td = (ThreadData*)arg;
    /* Warmup (descartado) */
    for (uint32_t i = 0; i < td->warmup_ops; i++) {
        size_t sz = (td->slab_idx >= 0)
                    ? (size_t)SLAB_SIZES[td->slab_idx]
                    : (size_t)SLAB_SIZES[i % SLAB_CLASSES];
        void* p = pool_alloc(sz);
        if (p) { pool_free(p); }
    }
    /* Medicion */
    td->thread_ns_min = UINT64_MAX;
    td->thread_ns_max = 0;
    td->thread_ns_total = 0;
    td->thread_ops = 0;
    for (uint32_t i = 0; i < td->measure_ops; i++) {
        size_t sz = (td->slab_idx >= 0)
                    ? (size_t)SLAB_SIZES[td->slab_idx]
                    : (size_t)SLAB_SIZES[i % SLAB_CLASSES];
        uint64_t t0 = timer_now_ns();
        void* p = pool_alloc(sz);
        uint64_t t1 = timer_now_ns();
        pool_free(p);
        uint64_t elapsed = t1 - t0;
        td->thread_ns_total += elapsed;
        if (elapsed < td->thread_ns_min) td->thread_ns_min = elapsed;
        if (elapsed > td->thread_ns_max) td->thread_ns_max = elapsed;
        td->thread_ops++;
        int si = td->slab_idx;
        if (si < 0) {
            for (int k = 0; k < SLAB_CLASSES; k++) {
                if (sz <= SLAB_SIZES[k]) { si = k; break; }
            }
        }
        if (si >= 0 && si < SLAB_CLASSES) {
            uint64_t bucket = elapsed / NS_PER_BUCKET;
            if (bucket < HISTOGRAM_BUCKETS)
                g_histogram[si][bucket]++;
            else
                g_overflow[si]++;
            g_total_ops[si]++;
        }
    }
    return NULL;
}

typedef struct {
    uint64_t p50_ns;
    uint64_t p90_ns;
    uint64_t p99_ns;
    uint64_t p999_ns;
    uint64_t p100_ns;
} Percentiles;

static Percentiles compute_percentiles(int slab_idx, uint64_t total) {
    Percentiles p = {0, 0, 0, 0, 0};
    if (total == 0) return p;
    uint64_t cum = 0;
    uint64_t targets[] = {
        total / 2,
        total * 90 / 100,
        total * 99 / 100,
        total * 999 / 1000,
        total - 1
    };
    int ti = 0;
    for (uint32_t b = 0; b < HISTOGRAM_BUCKETS && ti < 5; b++) {
        cum += g_histogram[slab_idx][b];
        while (ti < 5 && cum > targets[ti]) {
            uint64_t ns = (uint64_t)(b + 1) * NS_PER_BUCKET;
            switch (ti) {
                case 0: p.p50_ns = ns; break;
                case 1: p.p90_ns = ns; break;
                case 2: p.p99_ns = ns; break;
                case 3: p.p999_ns = ns; break;
                case 4: p.p100_ns = ns; break;
            }
            ti++;
        }
    }
    while (ti < 5) {
        uint64_t ns = HISTO_MAX_NS;
        switch (ti) {
            case 0: p.p50_ns = ns; break;
            case 1: p.p90_ns = ns; break;
            case 2: p.p99_ns = ns; break;
            case 3: p.p999_ns = ns; break;
            case 4: p.p100_ns = ns; break;
        }
        ti++;
    }
    return p;
}

static void print_report(int csv, int nthr, uint32_t wu, uint32_t meas,
                         ThreadData* tds, size_t rss_b, size_t rss_a) {
    if (csv) {
        printf("slab_class,ops,p50_ns,p90_ns,p99_ns,p999_ns,"
               "p100_ns,overflow,threads,warmup,measure,"
               "rss_before,rss_after\n");
        for (int si = 0; si < SLAB_CLASSES; si++) {
            if (g_total_ops[si] == 0) continue;
            Percentiles perc = compute_percentiles(si, g_total_ops[si]);
            printf("%s,%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
                   ",%" PRIu64 ",%" PRIu64 ",%" PRIu64
                   ",%d,%u,%u,%zu,%zu\n",
                   SLAB_NAMES[si], g_total_ops[si],
                   perc.p50_ns, perc.p90_ns, perc.p99_ns,
                   perc.p999_ns, perc.p100_ns, g_overflow[si],
                   nthr, wu, meas, rss_b, rss_a);
        }
        return;
    }
    printf("\n");
    printf("========================================\n");
    printf(" BENCHMARK ALLOC - RESULTADOS\n");
    printf("========================================\n");
    printf(" Config: %d hilos, warmup=%u, measure=%u\n", nthr, wu, meas);
    printf(" Pool:   %u bloques x %u bytes\n",
           (unsigned)POOL_BLOCKS, (unsigned)POOL_BLOCK_SIZE);
    printf(" RSS:    inicial=%zu (%.2f KB), final=%zu (%.2f KB),"
           " delta=%+zd (%.2f KB)\n",
           rss_b, rss_b / 1024.0,
           rss_a, rss_a / 1024.0,
           rss_a - rss_b, (rss_a - rss_b) / 1024.0);
    printf("\n Resultados por hilo:\n");
    for (int t = 0; t < nthr; t++) {
        double avg = (tds[t].thread_ops > 0)
                     ? (double)tds[t].thread_ns_total / tds[t].thread_ops
                     : 0.0;
        printf("  Hilo %d: %" PRIu64 " ops, media=%.1f ns,"
               " min=%" PRIu64 " ns, max=%" PRIu64 " ns\n",
               tds[t].thread_id, tds[t].thread_ops, avg,
               tds[t].thread_ns_min, tds[t].thread_ns_max);
    }
    printf("\n Percentiles por slab class:\n");
    printf(" %-10s %12s %12s %12s %12s %12s %12s %10s\n",
           "Clase", "Ops", "p50(ns)", "p90(ns)", "p99(ns)",
           "p999(ns)", "p100(ns)", "Overflow");
    for (int si = 0; si < SLAB_CLASSES; si++) {
        if (g_total_ops[si] == 0) {
            printf(" %-10s %12" PRIu64 " %12s %12s %12s %12s %12s %10s\n",
                   SLAB_NAMES[si], (uint64_t)0,
                   "N/A", "N/A", "N/A", "N/A", "N/A", "N/A");
            continue;
        }
        Percentiles perc = compute_percentiles(si, g_total_ops[si]);
        printf(" %-10s %12" PRIu64 " %12" PRIu64 " %12" PRIu64
               " %12" PRIu64 " %12" PRIu64 " %12" PRIu64 " %10" PRIu64 "\n",
               SLAB_NAMES[si], g_total_ops[si],
               perc.p50_ns, perc.p90_ns, perc.p99_ns,
               perc.p999_ns, perc.p100_ns, g_overflow[si]);
    }
    printf("\n");
    for (int si = 0; si < SLAB_CLASSES; si++) {
        if (g_total_ops[si] == 0) continue;
        Percentiles perc = compute_percentiles(si, g_total_ops[si]);
        if (perc.p999_ns > 5 * perc.p50_ns && perc.p50_ns > 0)
            printf(" [THROTTLED] Slab %s: p999 (%" PRIu64 " ns)"
                   " > 5x p50 (%" PRIu64 " ns)\n",
                   SLAB_NAMES[si], perc.p999_ns, perc.p50_ns);
    }
    printf("========================================\n");
}

int main(int argc, char** argv) {
    int nthreads = 1;
    uint32_t warmup = 2000;
    uint32_t measure = 100000;
    int slab_idx = -1; /* all */
    int csv = 0;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--threads") == 0 && i + 1 < argc)
            nthreads = atoi(argv[++i]);
        else if (strcmp(argv[i], "--warmup") == 0 && i + 1 < argc)
            warmup = (uint32_t)atoi(argv[++i]);
        else if (strcmp(argv[i], "--measure") == 0 && i + 1 < argc)
            measure = (uint32_t)atoi(argv[++i]);
        else if (strcmp(argv[i], "--slab") == 0 && i + 1 < argc) {
            i++;
            if (strcmp(argv[i], "all") == 0) slab_idx = -1;
            else {
                int sz = atoi(argv[i]);
                slab_idx = -1;
                for (int k = 0; k < SLAB_CLASSES; k++) {
                    if (SLAB_SIZES[k] == (uint32_t)sz) {
                        slab_idx = k; break;
                    }
                }
            }
            if (slab_idx < 0) {
                fprintf(stderr, "Slab invalida: %s (use 32|64|128|256|all)\n",
                        argv[i]);
                return 1;
            }
        }
        else if (strcmp(argv[i], "--csv") == 0) csv = 1;
        else if (strcmp(argv[i], "--help") == 0 ||
                 strcmp(argv[i], "-h") == 0) {
            printf("Uso: %s [--threads N] [--warmup N] [--measure N]"
                   " [--slab size|all] [--csv]\n", argv[0]);
            return 0;
        }
    }

    if (nthreads < 1 || nthreads > 128) {
        fprintf(stderr, "ERROR: --threads entre 1 y 128\n");
        return 1;
    }

    timer_init();
    pool_init(POOL_BLOCKS, POOL_BLOCK_SIZE);
    size_t rss_before = get_rss_bytes();

    memset(g_histogram, 0, sizeof(g_histogram));
    memset(g_total_ops, 0, sizeof(g_total_ops));
    memset(g_overflow, 0, sizeof(g_overflow));

    pthread_t* threads = (pthread_t*)malloc(
        (size_t)nthreads * sizeof(pthread_t));
    ThreadData* tds = (ThreadData*)malloc(
        (size_t)nthreads * sizeof(ThreadData));
    if (!threads || !tds) {
        fprintf(stderr, "malloc fallo\n");
        free(threads); free(tds);
        pool_destroy();
        return 1;
    }

    for (int t = 0; t < nthreads; t++) {
        tds[t].thread_id = t;
        tds[t].slab_idx = slab_idx;
        tds[t].warmup_ops = warmup;
        tds[t].measure_ops = measure;
        tds[t].thread_ops = 0;
        tds[t].thread_ns_total = 0;
        if (pthread_create(&threads[t], NULL, bench_thread,
                           &tds[t]) != 0) {
            fprintf(stderr, "pthread_create fallo hilo %d\n", t);
            free(threads); free(tds);
            pool_destroy();
            return 1;
        }
    }

    for (int t = 0; t < nthreads; t++)
        pthread_join(threads[t], NULL);

    size_t rss_after = get_rss_bytes();
    print_report(csv, nthreads, warmup, measure, tds,
                 rss_before, rss_after);

    free(threads);
    free(tds);
    pool_destroy();
    return 0;
}
"""

def main():
    dst = os.path.join(os.path.dirname(__file__), '..', 'tests', 'bench_alloc.c')
    dst = os.path.normpath(dst)
    with open(dst, 'w') as f:
        f.write(C_CODE)
    lines = C_CODE.count('\n')
    print(f"OK: {dst} written ({lines} lines)")

if __name__ == '__main__':
    main()
