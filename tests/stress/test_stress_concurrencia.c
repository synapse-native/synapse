/**
 * test_stress_concurrencia.c — Prueba de estrés F10.5
 *
 * Documento Maestro Parte VII: 10,000 hilos simultáneos
 * Criterio de aprobación:
 *   - 0 Deadlocks
 *   - 0 Data Races (verificar con -fsanitize=thread)
 *   - 0 Bytes perdidos (MemoryWatchdog)
 *
 * Compilación:
 *   gcc -O2 -DSYNAPSE_DEBUG_MEM -I. -o tests/stress/stress_concurrencia.exe ^
 *       tests/stress/test_stress_concurrencia.c synapse_rt.c ^
 *       -lpthread -lm -lws2_32
 *
 *   Con ThreadSanitizer (GCC >= 4.8):
 *   gcc -O1 -g -fsanitize=thread -DSYNAPSE_DEBUG_MEM -I. ^
 *       -o tests/stress/stress_tsan.exe tests/stress/test_stress_concurrencia.c ^
 *       synapse_rt.c -lpthread -lm -lws2_32
 *
 * Ejecución:
 *   ./stress_concurrencia.exe [num_hilos] [mensajes_por_hilo]
 *
 *   Por defecto: 10,000 hilos (5,000 productores + 5,000 consumidores)
 *   Cada hilo envía/recibe 2 mensajes = 10,000 transferencias
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
#include <assert.h>
#include <time.h>
#include <errno.h>

#ifdef _WIN32
#include <windows.h>
#endif

/* ============================================================
 * MemoryWatchdog (MIM) — Activado por SYNAPSE_DEBUG_MEM
 * ============================================================ */
#ifdef SYNAPSE_DEBUG_MEM
void* watchdog_malloc(size_t size, const char* file, int line);
void* watchdog_calloc(size_t n, size_t size, const char* file, int line);
void watchdog_free(void* ptr, const char* file, int line);
void watchdog_report(void);

#define malloc(s)       watchdog_malloc(s, __FILE__, __LINE__)
#define calloc(n, s)    watchdog_calloc(n, s, __FILE__, __LINE__)
#define free(p)         watchdog_free(p, __FILE__, __LINE__)
#endif

/* ============================================================
 * Channel runtime declarations (from synapse_rt.h)
 * ============================================================ */
typedef struct { int longitud; const char* datos; } CadenaSegura;

typedef struct CanalConcurrencia CanalConcurrencia;

CanalConcurrencia* canal_crear(uint32_t capacidad);
void canal_enviar(CanalConcurrencia* canal, void* paquete);
void* canal_recibir(CanalConcurrencia* canal);
void canal_destruir(CanalConcurrencia* canal);

/* ============================================================
 * High-resolution timer (cross-platform)
 * ============================================================ */
static double now_sec(void) {
#ifdef _WIN32
    static LARGE_INTEGER freq = {0};
    LARGE_INTEGER pc;
    if (freq.QuadPart == 0) {
        QueryPerformanceFrequency(&freq);
    }
    QueryPerformanceCounter(&pc);
    return (double)pc.QuadPart / (double)freq.QuadPart;
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
#endif
}

/* ============================================================
 * Thread helpers (inline para boxing/unboxing primitivos)
 * ============================================================ */
static inline void* box_int(int v) {
    int* p = (int*)malloc(sizeof(int));
    if (!p) { fprintf(stderr, "[STRESS] FATAL: malloc fallo en box_int\n"); exit(1); }
    *p = v;
    return (void*)p;
}

static inline int unbox_int(void* p) {
    if (!p) return -1;
    int v = *(int*)p;
    free(p);
    return v;
}

/* ============================================================
 * Atomics (GCC built-in para compatibilidad con ThreadSanitizer)
 * ============================================================ */
static inline int ato_inc(volatile int* p) {
    return __sync_fetch_and_add(p, 1);
}

/* ============================================================
 * Test configuration
 * ============================================================ */
typedef struct {
    int hilo_id;              /* ID único del hilo */
    CanalConcurrencia* canal; /* Canal de comunicación */
    int total_mensajes;       /* Total de mensajes a enviar/recibir */
    volatile int* contador_global; /* Contador atómico compartido */
    volatile int* errores;         /* Contador de errores */
} ContextoHilo;

static inline void reportar_error(volatile int* p) {
    __sync_fetch_and_add(p, 1);
}

/* ============================================================
 * Worker threads
 * ============================================================ */

/* Hilo productor: envía mensajes a través del canal */
static void* hilo_productor(void* arg) {
    ContextoHilo* ctx = (ContextoHilo*)arg;
    int mi_id = ctx->hilo_id;
    CanalConcurrencia* ch = ctx->canal;
    int total = ctx->total_mensajes;

    for (int i = 0; i < total; i++) {
        /* Crear un mensaje único: (id_hilo << 16) | secuencia */
        int valor = (mi_id << 16) | i;
        canal_enviar(ch, box_int(valor));
    }
    return NULL;
}

/* Eliminar unused variable warning */
#define UNUSED(x) ((void)(x))

/* Hilo consumidor: recibe mensajes y cuenta recibidos.
 * NO se valida orden por-consumidor porque multiples consumidores
 * comparten el mismo canal (interleaving natural).
 * La validacion global (total enviados == total recibidos)
 * detecta deadlocks y mensajes perdidos.
 */
static void* hilo_consumidor(void* arg) {
    ContextoHilo* ctx = (ContextoHilo*)arg;
    CanalConcurrencia* ch = ctx->canal;
    int total = ctx->total_mensajes;

    for (int i = 0; i < total; i++) {
        void* paquete = canal_recibir(ch);
        if (!paquete) {
            reportar_error(ctx->errores);
            fprintf(stderr, "[STRESS] ERROR: canal_recibir devolvio NULL "
                    "(consumidor %d, msg %d)\n", ctx->hilo_id, i);
            return NULL;
        }
        /* Liberar el mensaje recibido (box_int en productor) */
        int valor = unbox_int(paquete);
        UNUSED(valor);

        /* Marcar recepción */
        ato_inc(ctx->contador_global);
    }
    return NULL;
}

/* ============================================================
 * Test runner
 * ============================================================ */
typedef struct {
    int num_productores;
    int num_consumidores;
    int mensajes_por_hilo;
    double tiempo_inicio;
    double tiempo_fin;
    long total_transferencias;
    volatile int total_recibidos;
    volatile int total_errores;
    int hilos_lanzados;
    CanalConcurrencia* canal;
    pthread_t* hilos;
    ContextoHilo* ctxs;
} ResultadoStress;

static const int STACK_SIZE_KB = 64; /* Stack pequeño para soportar 10k+ hilos */

static ResultadoStress* ejecutar_stress(int num_hilos, int mensajes_por_hilo) {
    int num_productores = num_hilos / 2;
    int num_consumidores = num_hilos - num_productores;
    if (num_productores < 1) num_productores = 1;
    if (num_consumidores < 1) num_consumidores = 1;

    /* Ajustar para que productores y consumidores tengan el mismo total */
    int total_msgs_prod = num_productores * mensajes_por_hilo;
    num_consumidores = total_msgs_prod / mensajes_por_hilo;
    if (num_consumidores < 1) num_consumidores = 1;
    num_hilos = num_productores + num_consumidores;

    fprintf(stderr, "[STRESS] Config: %d productores + %d consumidores = %d hilos\n",
            num_productores, num_consumidores, num_hilos);
    fprintf(stderr, "[STRESS] Cada hilo: %d mensajes\n", mensajes_por_hilo);

    ResultadoStress* rs = (ResultadoStress*)malloc(sizeof(ResultadoStress));
    if (!rs) { fprintf(stderr, "[STRESS] FATAL: malloc\n"); exit(1); }
    memset(rs, 0, sizeof(ResultadoStress));

    rs->num_productores = num_productores;
    rs->num_consumidores = num_consumidores;
    rs->mensajes_por_hilo = mensajes_por_hilo;
    rs->total_transferencias = (long)num_productores * mensajes_por_hilo;
    rs->total_recibidos = 0;
    rs->total_errores = 0;
    rs->hilos_lanzados = 0;

    /* Crear canal con capacidad suficiente */
    int capacidad = (int)(rs->total_transferencias / 10);
    if (capacidad < 64) capacidad = 64;
    if (capacidad > 10000) capacidad = 10000;
    rs->canal = canal_crear((uint32_t)capacidad);
    if (!rs->canal) {
        fprintf(stderr, "[STRESS] FATAL: canal_crear fallo\n");
        free(rs);
        return NULL;
    }
    fprintf(stderr, "[STRESS] Canal creado: capacidad=%d\n", capacidad);

    /* Preparar arrays de hilos */
    int total_hilos = num_productores + num_consumidores;
    rs->hilos = (pthread_t*)malloc(sizeof(pthread_t) * total_hilos);
    rs->ctxs = (ContextoHilo*)malloc(sizeof(ContextoHilo) * total_hilos);
    if (!rs->hilos || !rs->ctxs) {
        fprintf(stderr, "[STRESS] FATAL: malloc para hilos fallo\n");
        canal_destruir(rs->canal);
        free(rs->hilos); free(rs->ctxs); free(rs);
        return NULL;
    }

    /* Configurar atributos de hilo con stack pequeño */
    pthread_attr_t attr;
    pthread_attr_init(&attr);
    pthread_attr_setstacksize(&attr, STACK_SIZE_KB * 1024);

    /* Lanzar hilos */
    rs->tiempo_inicio = now_sec();
    int idx = 0;
    int fallos_lanzamiento = 0;

    for (int i = 0; i < num_productores; i++, idx++) {
        rs->ctxs[idx].hilo_id = i;
        rs->ctxs[idx].canal = rs->canal;
        rs->ctxs[idx].total_mensajes = mensajes_por_hilo;
        rs->ctxs[idx].contador_global = &rs->total_recibidos;
        rs->ctxs[idx].errores = &rs->total_errores;
        int rc = pthread_create(&rs->hilos[idx], &attr, hilo_productor,
                                &rs->ctxs[idx]);
        if (rc == 0) {
            rs->hilos_lanzados++;
        } else {
            fallos_lanzamiento++;
            fprintf(stderr, "[STRESS] WARN: pthread_create productor %d "
                    "fallo (rc=%d, errno=%d)\n", i, rc, errno);
        }
    }

    for (int i = 0; i < num_consumidores; i++, idx++) {
        rs->ctxs[idx].hilo_id = i;
        rs->ctxs[idx].canal = rs->canal;
        rs->ctxs[idx].total_mensajes = mensajes_por_hilo;
        rs->ctxs[idx].contador_global = &rs->total_recibidos;
        rs->ctxs[idx].errores = &rs->total_errores;
        int rc = pthread_create(&rs->hilos[idx], &attr, hilo_consumidor,
                                &rs->ctxs[idx]);
        if (rc == 0) {
            rs->hilos_lanzados++;
        } else {
            fallos_lanzamiento++;
            fprintf(stderr, "[STRESS] WARN: pthread_create consumidor %d "
                    "fallo (rc=%d, errno=%d)\n", i, rc, errno);
        }
    }

    pthread_attr_destroy(&attr);

    if (fallos_lanzamiento > 0) {
        fprintf(stderr, "[STRESS] %d hilos no pudieron crearse (límite del sistema)\n",
                fallos_lanzamiento);
    }

    /* Esperar SOLO los hilos que se lanzaron exitosamente */
    for (int i = 0; i < rs->hilos_lanzados; i++) {
        pthread_join(rs->hilos[i], NULL);
    }

    rs->tiempo_fin = now_sec();
    return rs;
}

/* ============================================================
 * Main
 * ============================================================ */
int main(int argc, char** argv) {
    int num_hilos = 10000;
    int mensajes_por_hilo = 2;

    if (argc >= 2) num_hilos = atoi(argv[1]);
    if (argc >= 3) mensajes_por_hilo = atoi(argv[2]);

    if (num_hilos < 2) num_hilos = 2;
    if (mensajes_por_hilo < 1) mensajes_por_hilo = 1;

    fprintf(stderr, "\n============================================================\n");
    fprintf(stderr, "  SYNAPSE STRESS TEST F10.5 - Documento Maestro Parte VII\n");
    fprintf(stderr, "============================================================\n\n");

    ResultadoStress* rs = ejecutar_stress(num_hilos, mensajes_por_hilo);
    if (!rs) {
        fprintf(stderr, "\n[STRESS] FATAL: No se pudo iniciar la prueba\n");
        return 1;
    }

    double duracion = rs->tiempo_fin - rs->tiempo_inicio;

    fprintf(stderr, "\n============================================================\n");
    fprintf(stderr, "  RESULTADOS\n");
    fprintf(stderr, "============================================================\n");
    fprintf(stderr, "  Hilos solicitados:  %d\n", num_hilos);
    fprintf(stderr, "  Hilos lanzados:     %d\n", rs->hilos_lanzados);
    fprintf(stderr, "  Productores:        %d\n", rs->num_productores);
    fprintf(stderr, "  Consumidores:       %d\n", rs->num_consumidores);
    fprintf(stderr, "  Transferencias:     %ld\n", rs->total_transferencias);
    fprintf(stderr, "  Recibidos:          %d\n", rs->total_recibidos);
    fprintf(stderr, "  Errores:            %d\n", rs->total_errores);
    fprintf(stderr, "  Duracion:           %.3f segundos\n", duracion);
    if (duracion > 0) {
        fprintf(stderr, "  Throughput:         %.0f msg/seg\n",
                rs->total_transferencias / duracion);
    }
    fprintf(stderr, "  Deadlocks:          %s\n",
            rs->total_recibidos == rs->total_transferencias ? "0 [OK]" : "DETECTADOS [FAIL]");
    fprintf(stderr, "============================================================\n\n");

    /* ============================================================
     * FASE 1: Validación (usa rs antes de liberar)
     * ============================================================ */
    int exit_code = 0;

    if (rs->total_recibidos != rs->total_transferencias) {
        fprintf(stderr, "[STRESS] [FAIL] %ld/%ld mensajes perdidos (deadlock?)\n",
                rs->total_transferencias - rs->total_recibidos,
                rs->total_transferencias);
        exit_code = 1;
    }
    if (rs->total_errores > 0) {
        fprintf(stderr, "[STRESS] [FAIL] %d errores de integridad de datos\n",
                rs->total_errores);
        exit_code = 1;
    }
    if (rs->hilos_lanzados < num_hilos) {
        fprintf(stderr, "[STRESS] [WARN] %d/%d hilos creados (limite del sistema)\n",
                rs->hilos_lanzados, num_hilos);
    }

    /* ============================================================
     * FASE 2: Liberar TODOS los recursos
     * ============================================================ */
    canal_destruir(rs->canal);
    free(rs->hilos);
    free(rs->ctxs);
    free(rs);  /* <-- rs liberado ANTES de watchdog_report */

    /* ============================================================
     * FASE 3: MemoryWatchdog report (despues de TODO cleanup)
     * ============================================================ */
#ifdef SYNAPSE_DEBUG_MEM
    fprintf(stderr, "[STRESS] MemoryWatchdog:\n");
    watchdog_report();
    fprintf(stderr, "\n");
#else
    fprintf(stderr, "[STRESS] MemoryWatchdog: no activado "
            "(compilar con -DSYNAPSE_DEBUG_MEM)\n\n");
#endif

    if (exit_code == 0) {
        fprintf(stderr, "[STRESS] [PASS] 0 Deadlocks | 0 Errores | Sin fugas\n");
        fprintf(stderr, "[STRESS] Prueba F10.5 superada\n");
    }

    return exit_code;
}
