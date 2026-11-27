/*
 * test_stress_fibras.c — F4-7 / Checklist 4.4: Estrés con 10,000 fibras
 * concurrentes y comunicación intensiva (ROADMAP Fase 4 L109-110)
 *
 * Criterios de aceptación (ROADMAP L110):
 *   - 0 deadlocks: todas las fibras terminan y el contador global alcanza el
 *     total de transferencias (canal_recibir nunca devuelve NULL por cierre
 *     prematuro ni mensajes se pierden).
 *   - 0 data races: cada mensaje viaja boxeado con su (productor, secuencia);
 *     el consumidor valida la integridad; el contador compartido es atómico
 *     y el contador bajo mutex usa el Mutex del Manual 5 §5.1.
 *
 * Diseño:
 *   - 5,000 fibras productoras + 5,000 fibras consumidoras = 10,000 fibras
 *     M:N (Manual 5 §2.6) sobre un CanalConcurrencia con buffer (Manual 5 §3).
 *   - Cada productor envía MENSAJES_POR_FIBRA mensajes; cada consumidor recibe
 *     el mismo número. Total = NUM_PRODUCTORES * MENSAJES_POR_FIBRA.
 *   - Cada fibra incrementa además un contador protegido por Mutex (F4.5).
 *   - Pila personalizada (32 KB) para mantener la memoria acotada:
 *     10,000 * 32 KB = 320 MB (mismo criterio que test_stress_concurrencia.c).
 *
 * Compilación (patrón test_fibras_espera.py / rt_objs):
 *   gcc -O2 -std=c99 -Wall -I<raíz> test_stress_fibras.c <rt_objs>
 *       -o test_stress_fibras.exe -lm -lpthread -lws2_32
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#endif

/* ===== API del scheduler de fibras (Manual 5 §2.6) — concurrency.c ===== */
extern void scheduler_iniciar(int num_hilos_os);
extern void scheduler_detener(void);
extern void fibra_crear(void (*func)(void*), void* arg, size_t stack_size);
extern void fibra_terminar(void* resultado);
extern void synapse_esperar_fibras(void);

/* ===== API de canales (Manual 5 §3) — concurrency.c ===== */
typedef struct CanalConcurrencia CanalConcurrencia;
extern CanalConcurrencia* canal_crear(uint32_t capacidad);
extern void canal_enviar(CanalConcurrencia* canal, void* paquete);
extern void* canal_recibir(CanalConcurrencia* canal, bool* cerrado);
extern void canal_destruir(CanalConcurrencia* canal);

/* ===== API de Mutex (Manual 5 §5.1) — concurrency.c ===== */
typedef struct Mutex Mutex;
extern Mutex* mutex_crear(void);
extern void mutex_bloquear(Mutex* m);
extern void mutex_desbloquear(Mutex* m);
extern void mutex_destruir(Mutex* m);

/* ============================================================
 * Configuración de la prueba
 * ============================================================ */
#define NUM_PRODUCTORES 5000
#define NUM_CONSUMIDORES 5000
#define NUM_FIBRAS (NUM_PRODUCTORES + NUM_CONSUMIDORES)   /* 10,000 */
#define MENSAJES_POR_FIBRA 2
#define TOTAL_TRANSFERENCIAS (NUM_PRODUCTORES * MENSAJES_POR_FIBRA)  /* 10,000 */
#define STACK_FIBRA (32 * 1024)

/* ===== Atomicos (GCC built-in, paridad test_stress_concurrencia.c) ===== */
static inline int ato_inc(volatile int* p) {
    return __sync_fetch_and_add(p, 1);
}

/* ===== Boxing/unboxing de enteros ===== */
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

/* ===== Reloj de alta resolución ===== */
static double now_sec(void) {
#ifdef _WIN32
    static LARGE_INTEGER freq = {0};
    LARGE_INTEGER pc;
    if (freq.QuadPart == 0) QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&pc);
    return (double)pc.QuadPart / (double)freq.QuadPart;
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
#endif
}

/* ===== Contexto compartido ===== */
typedef struct {
    int fibra_id;                /* ID único de la fibra (espejo del scheduler) */
    CanalConcurrencia* canal;    /* Canal de comunicación */
    volatile int* contador_global;   /* Recibidos (atómico) */
    volatile int* errores;           /* Errores de integridad (atómico) */
    Mutex* mutex;                    /* Mutex compartido (Manual 5 §5.1) */
    volatile int* contador_mutex;    /* Contador bajo mutex */
} ContextoFibra;

static ContextoFibra g_ctx[NUM_FIBRAS];

/* ===== Fibra productora ===== */
static void fibra_productor(void* p) {
    ContextoFibra* ctx = (ContextoFibra*)p;
    int id = ctx->fibra_id;
    CanalConcurrencia* ch = ctx->canal;
    for (int i = 0; i < MENSAJES_POR_FIBRA; i++) {
        int valor = (id << 16) | i;
        canal_enviar(ch, box_int(valor));
    }
    /* Contador bajo mutex: 1 incremento por fibra. */
    mutex_bloquear(ctx->mutex);
    (*ctx->contador_mutex)++;
    mutex_desbloquear(ctx->mutex);
    fibra_terminar(NULL);
}

/* ===== Fibra consumidora ===== */
static void fibra_consumidor(void* p) {
    ContextoFibra* ctx = (ContextoFibra*)p;
    CanalConcurrencia* ch = ctx->canal;
    for (int i = 0; i < MENSAJES_POR_FIBRA; i++) {
        void* paquete = canal_recibir(ch, &(bool){0});
        if (!paquete) {
            /* Cierre prematuro / mensaje perdido: deadlock o data race. */
            ato_inc(ctx->errores);
            fprintf(stderr, "[STRESS] ERROR: canal_recibir devolvio NULL "
                    "(consumidor %d, msg %d)\n", ctx->fibra_id, i);
            fibra_terminar(NULL);
            return;
        }
        int valor = unbox_int(paquete);
        int prod_id = (valor >> 16) & 0xFFFF;
        int seq = valor & 0xFFFF;
        if (prod_id >= NUM_PRODUCTORES || seq >= MENSAJES_POR_FIBRA) {
            ato_inc(ctx->errores);
            fprintf(stderr, "[STRESS] ERROR: integridad del dato "
                    "(consumidor %d, valor=%d)\n", ctx->fibra_id, valor);
        }
        ato_inc(ctx->contador_global);
    }
    mutex_bloquear(ctx->mutex);
    (*ctx->contador_mutex)++;
    mutex_desbloquear(ctx->mutex);
    fibra_terminar(NULL);
}

/* ============================================================
 * Runner
 * ============================================================ */
static int g_recibidos = 0;
static int g_errores = 0;
static int g_contador_mutex = 0;

static int ejecutar_stress(void) {
    printf("=== F4-7: Estrés de 10,000 fibras (checklist 4.4, ROADMAP L109) ===\n\n");
    printf("[STRESS] Config: %d productores + %d consumidores = %d fibras\n",
           NUM_PRODUCTORES, NUM_CONSUMIDORES, NUM_FIBRAS);
    printf("[STRESS] Cada fibra: %d mensajes (total %d transferencias)\n",
           MENSAJES_POR_FIBRA, TOTAL_TRANSFERENCIAS);
    printf("[STRESS] Pila por fibra: %d KB\n", STACK_FIBRA / 1024);

    CanalConcurrencia* canal = canal_crear(1000);   /* buffer 1,000 items */
    if (!canal) {
        fprintf(stderr, "[STRESS] FATAL: canal_crear fallo\n");
        return 1;
    }

    Mutex* mutex = mutex_crear();
    if (!mutex) {
        fprintf(stderr, "[STRESS] FATAL: mutex_crear fallo\n");
        canal_destruir(canal);
        return 1;
    }

    /* Preparar contextos y crear las 10,000 fibras (ids secuenciales desde 0). */
    double t0 = now_sec();
    for (int i = 0; i < NUM_FIBRAS; i++) {
        g_ctx[i].fibra_id = i;
        g_ctx[i].canal = canal;
        g_ctx[i].contador_global = &g_recibidos;
        g_ctx[i].errores = &g_errores;
        g_ctx[i].mutex = mutex;
        g_ctx[i].contador_mutex = &g_contador_mutex;
        fibra_crear(i < NUM_PRODUCTORES ? fibra_productor : fibra_consumidor,
                    &g_ctx[i], STACK_FIBRA);
    }

    /* Esperar a que TODAS las fibras terminen (num_fibras == 0). */
    synapse_esperar_fibras();
    double t1 = now_sec();

    printf("\n[STRESS] Fibras creadas:      %d\n", NUM_FIBRAS);
    printf("[STRESS] Transferencias:      %d\n", TOTAL_TRANSFERENCIAS);
    printf("[STRESS] Recibidos:           %d\n", g_recibidos);
    printf("[STRESS] Errores integridad:  %d\n", g_errores);
    printf("[STRESS] Contador bajo mutex: %d (esperado %d)\n",
           g_contador_mutex, NUM_FIBRAS);
    printf("[STRESS] Duración:            %.3f segundos\n", t1 - t0);

    /* Validación (ROADMAP L110). */
    int exit_code = 0;
    if (g_recibidos != TOTAL_TRANSFERENCIAS) {
        fprintf(stderr, "[STRESS] [FAIL] %d/%d mensajes perdidos (deadlock?)\n",
                TOTAL_TRANSFERENCIAS - g_recibidos, TOTAL_TRANSFERENCIAS);
        exit_code = 1;
    }
    if (g_errores != 0) {
        fprintf(stderr, "[STRESS] [FAIL] %d errores de integridad (data race?)\n",
                g_errores);
        exit_code = 1;
    }
    if (g_contador_mutex != NUM_FIBRAS) {
        fprintf(stderr, "[STRESS] [FAIL] contador mutex %d != %d\n",
                g_contador_mutex, NUM_FIBRAS);
        exit_code = 1;
    }

    mutex_destruir(mutex);
    canal_destruir(canal);

    if (exit_code == 0) {
        fprintf(stderr, "[STRESS] [PASS] 0 Deadlocks | 0 Data Races | "
                "10,000 fibras completaron\n");
    }
    return exit_code;
}

int main(void) {
    int rc = ejecutar_stress();
    scheduler_detener();
    printf(rc == 0 ? "\n=== Resumen: Exitos: 1 Fallos: 0 ===\n"
                   : "\n=== Resumen: Exitos: 0 Fallos: 1 ===\n");
    return rc;
}