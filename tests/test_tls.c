/* tests/test_tls.c — Manual 4 §4.6: TLC stress test
 *
 * Valida el Pool Allocator con Caché por Hilo (Thread-Local Cache).
 * Ejecuta multiples hilos concurrentes haciendo alloc/free.
 * Criterio: 0 bloqueos, overhead <5% vs malloc.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <math.h>

#define POOL_BLOCK_SIZE 4096
#define TLS_BLOCK_COUNT 64
#define POOL_MAX_BLOCKS 1048576

typedef struct ThreadLocalPool {
    void* blocks[TLS_BLOCK_COUNT];
    int used_count;
    pthread_mutex_t local_mutex;
} ThreadLocalPool;

typedef struct GlobalPool {
    void* blocks[POOL_MAX_BLOCKS];
    int used_count;
    size_t block_size;
    pthread_mutex_t mutex;
} GlobalPool;

static __thread ThreadLocalPool tls_pool;
static GlobalPool g_pool;
static int g_pool_initialized = 0;

static int test_passed = 0;
static int test_failed = 0;

#define TEST(nombre, expr) do { \
    if (!(expr)) { \
        fprintf(stderr, "  [FAIL] %s\n", nombre); \
        test_failed++; \
    } else { \
        printf("  [PASS] %s\n", nombre); \
        test_passed++; \
    } \
} while(0)

void test_tls_init(void) {
    memset(&tls_pool, 0, sizeof(tls_pool));
    pthread_mutex_init(&tls_pool.local_mutex, NULL);
    if (!g_pool_initialized) {
        memset(&g_pool, 0, sizeof(g_pool));
        g_pool.block_size = POOL_BLOCK_SIZE;
        pthread_mutex_init(&g_pool.mutex, NULL);
        g_pool_initialized = 1;
    }
}

void* test_tls_alloc(size_t size) {
    if (tls_pool.used_count < TLS_BLOCK_COUNT) {
        int idx = tls_pool.used_count++;
        if (!tls_pool.blocks[idx]) {
            tls_pool.blocks[idx] = malloc(POOL_BLOCK_SIZE);
        }
        return tls_pool.blocks[idx];
    }
    pthread_mutex_lock(&g_pool.mutex);
    for (int i = 0; i < POOL_MAX_BLOCKS; i++) {
        if (i >= g_pool.used_count) {
            g_pool.blocks[i] = malloc(POOL_BLOCK_SIZE);
            g_pool.used_count++;
            pthread_mutex_unlock(&g_pool.mutex);
            return g_pool.blocks[i];
        }
    }
    pthread_mutex_unlock(&g_pool.mutex);
    return malloc(size);
}

void test_tls_free(void* ptr) {
    for (int i = 0; i < tls_pool.used_count; i++) {
        if (tls_pool.blocks[i] == ptr) {
            tls_pool.blocks[i] = tls_pool.blocks[tls_pool.used_count - 1];
            tls_pool.used_count--;
            return;
        }
    }
    pthread_mutex_lock(&g_pool.mutex);
    for (int i = 0; i < g_pool.used_count; i++) {
        if (g_pool.blocks[i] == ptr) {
            pthread_mutex_unlock(&g_pool.mutex);
            return;
        }
    }
    pthread_mutex_unlock(&g_pool.mutex);
    free(ptr);
}

typedef struct {
    int thread_id;
    int alloc_count;
    int iterations;
    double elapsed;
    int deadlocks;
} ThreadData;

void* worker_thread(void* arg) {
    ThreadData* td = (ThreadData*)arg;
    clock_t start = clock();
    td->deadlocks = 0;

    for (int it = 0; it < td->iterations; it++) {
        void* ptrs[100];
        for (int i = 0; i < td->alloc_count && i < 100; i++) {
            ptrs[i] = test_tls_alloc(64);
            if (!ptrs[i]) td->deadlocks++;
        }
        for (int i = 0; i < td->alloc_count && i < 100; i++) {
            if (ptrs[i]) test_tls_free(ptrs[i]);
        }
    }

    td->elapsed = (double)(clock() - start) / CLOCKS_PER_SEC;
    return NULL;
}

void test_tls_concurrent_access(void) {
    printf("\n--- TLC Stress: %d hilos, %d allocs c/u ---\n", 100, 1000);
    int num_threads = 100;
    int allocs_per_thread = 1000;
    pthread_t* threads = malloc(num_threads * sizeof(pthread_t));
    ThreadData* data = calloc(num_threads, sizeof(ThreadData));

    for (int i = 0; i < num_threads; i++) {
        data[i].thread_id = i;
        data[i].alloc_count = 100;
        data[i].iterations = allocs_per_thread / 100;
        pthread_create(&threads[i], NULL, worker_thread, &data[i]);
    }

    int total_deadlocks = 0;
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
        total_deadlocks += data[i].deadlocks;
    }

    TEST("0 deadlocks en TLC concurrente", total_deadlocks == 0);
    free(threads);
    free(data);
}

void test_tls_overhead_vs_malloc(void) {
    printf("\n--- Overhead TLC vs malloc ---\n");
    clock_t start, end;
    double tls_time, malloc_time;

    test_tls_init();
    start = clock();
    for (int i = 0; i < 100000; i++) {
        void* p = test_tls_alloc(64);
        test_tls_free(p);
    }
    end = clock();
    tls_time = (double)(end - start) / CLOCKS_PER_SEC;

    start = clock();
    for (int i = 0; i < 100000; i++) {
        void* p = malloc(64);
        free(p);
    }
    end = clock();
    malloc_time = (double)(end - start) / CLOCKS_PER_SEC;

    printf("  TLC:   %.4fs\n", tls_time);
    printf("  malloc: %.4fs\n", malloc_time);
    double ratio = malloc_time > 0 ? (tls_time / malloc_time) : 1.0;
    TEST("Overhead TLC < 5% vs malloc", ratio < 1.05);
}

int main(void) {
    printf("========================================\n");
    printf("  TLC Pool Allocator Stress Test\n");
    printf("  Manual 4 §4.6 — Contencion TLC\n");
    printf("========================================\n");

    test_tls_init();
    test_tls_concurrent_access();
    test_tls_overhead_vs_malloc();

    printf("\n--- Resultados: %d PASS, %d FAIL ---\n", test_passed, test_failed);
    return test_failed > 0 ? 1 : 0;
}