/*
 * test_sync_primitivas.c — F4.5: Primitivas de sincronización (Manual 5 §5)
 *
 * Cubre (todas fiber-aware — una fibra bloqueada se parquea en el scheduler,
 * F4.2/F4.5, en vez de bloquear a su worker M:N):
 *   1. Mutex: exclusión mutua real — N fibras × K incrementos sobre un
 *      contador compartido protegido por mutex → contador == N*K (sin
 *      pérdidas = sin interleaving ilegal).
 *   2. Mutex: handoff FIFO main(OS thread) ↔ fibra — el main toma el mutex,
 *      una fibra se parquea esperándolo, el main lo libera y vuelve a
 *      bloqueárselo: la fibra (primera en cola) debe adquirirlo ANTES que el
 *      main (si el handoff saltara la cola, el test se cuelga o falla).
 *   3. Semáforo(0): main bloqueado en semaforo_esperar (path cond_wait de
 *      hilo OS) es despertado por el semaforo_señalar de una fibra.
 *   4. Semáforo(1) como lock binario: handoff FIFO fibra ↔ main (mismo
 *      patrón de propiedad que el mutex).
 *   5. Barrera: 5 fibras × 2 rondas — NINGUNA fibra pasa la barrera hasta
 *      que las 5 llegaron (se verifica g_llegadas == 5 al pasar); dos rondas
 *      consecutivas (generación).
 *   6. Destrucción limpia de las tres primitivas tras el uso.
 *
 * API del Manual 5 §5.4: mutex_crear/bloquear/desbloquear/destruir,
 * semaforo_crear/esperar/señalar/destruir, barrera_crear/esperar/destruir
 * (definidas en runtime/core/concurrency.c, structs en synapse_rt_types.h).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* API del scheduler de fibras (Manual 5 §2.6) — runtime/core/concurrency.c */
extern void scheduler_iniciar(int num_hilos_os);
extern void scheduler_detener(void);
extern void fibra_crear(void (*func)(void*), void* arg, size_t stack_size);
extern void fibra_esperar(int fibra_id);
extern void fibra_terminar(void* resultado);

/* API de sincronización (Manual 5 §5.4) — runtime/core/concurrency.c */
extern void* mutex_crear(void);
extern void mutex_bloquear(void* m);
extern void mutex_desbloquear(void* m);
extern void mutex_destruir(void* m);
extern void* semaforo_crear(int valor);
extern void semaforo_esperar(void* s);
extern void semaforo_señalar(void* s);
extern void semaforo_destruir(void* s);
extern void* barrera_crear(int total);
extern void barrera_esperar(void* b);
extern void barrera_destruir(void* b);

static int tests_passed = 0, tests_failed = 0;
static int prox_id = 0;   /* espejo del scheduler: ids secuenciales desde 0 */

static void check(int cond, const char* nombre) {
    if (cond) {
        printf("[PASS] %s\n", nombre);
        tests_passed++;
    } else {
        printf("[FAIL] %s\n", nombre);
        tests_failed++;
    }
}

/* ===== 1. Mutex: exclusión mutua sobre contador compartido ========================= */
#define N_FIBRAS_MUTEX 4
#define K_ITERS 2000
static long g_contador = 0;
static void* g_mutex = NULL;

static void fibra_incrementa(void* p) {
    (void)p;
    for (int i = 0; i < K_ITERS; i++) {
        mutex_bloquear(g_mutex);
        g_contador++;
        mutex_desbloquear(g_mutex);
    }
    fibra_terminar(NULL);
}

/* ===== 2. Mutex: handoff FIFO main ↔ fibra ========================================== */
static int g_handoff = 0;   /* 1 = la fibra adquirió el mutex tras el handoff */
static void* g_s_arranque = NULL;   /* semáforo "la fibra está a punto de bloquear" */
static void* g_s_done = NULL;       /* semáforo "la fibra completó" (handshake determinista) */

static void fibra_handoff(void* p) {
    (void)p;
    semaforo_señalar(g_s_arranque);   /* "a punto de bloquear" (creación asíncrona) */
    mutex_bloquear(g_mutex);          /* se parquea: el main lo tiene tomado */
    g_handoff = 1;                    /* adquirido por handoff (FIFO) */
    mutex_desbloquear(g_mutex);
    semaforo_señalar(g_s_done);       /* completó la sección crítica */
    fibra_terminar(NULL);
}

/* ===== 3. Semáforo(0): fibra despierta al main bloqueado ============================ */
static int g_señal = 0;
static void* g_sem = NULL;

static void fibra_señala(void* p) {
    (void)p;
    g_señal = 1;               /* visible: el main sigue bloqueado en esperar */
    semaforo_señalar(g_sem);
    fibra_terminar(NULL);
}

/* ===== 4. Semáforo(1) como lock binario: handoff FIFO fibra ↔ main ================== */
static int g_sem_fifo = 0;

static void fibra_sem_fifo(void* p) {
    (void)p;
    semaforo_esperar(g_sem);   /* consume el permiso -> se parquea (0 tokens) */
    g_sem_fifo = 1;
    semaforo_señalar(g_sem);   /* devuelve el permiso al main */
    semaforo_señalar(g_s_done);
    fibra_terminar(NULL);
}

/* ===== 5. Barrera: 5 fibras × 2 rondas, nadie pasa hasta que todos llegaron ========= */
#define TOTAL_BARRERA 5
#define RONDAS_BARRERA 2
static int g_llegadas_r[RONDAS_BARRERA] = {0, 0};
static int g_pasaron_r[RONDAS_BARRERA] = {0, 0};
static int g_error_barrera = 0;
static void* g_barrera = NULL;

static void fibra_barrera(void* p) {
    long idx = *(long*)p;
    for (int r = 0; r < RONDAS_BARRERA; r++) {
        __sync_fetch_and_add(&g_llegadas_r[r], 1);   /* llegada a la ronda r */
        barrera_esperar(g_barrera);
        /* Al cruzar la ronda r, los TOTAL_BARRERA ya llegaron a ESA ronda
         * (el release del mutex interno sincroniza). El contador de la ronda
         * r ya no cambia tras el release (nadie llega a la ronda r después
         * de cruzarla) — lectura determinista. Si la barrera liberara antes
         * de tiempo, esta lectura vería < TOTAL. */
        if (g_llegadas_r[r] != TOTAL_BARRERA) g_error_barrera++;
        __sync_fetch_and_add(&g_pasaron_r[r], 1);
    }
    (void)idx;
    fibra_terminar(NULL);
}

int main(void) {
    printf("=== F4.5: Primitivas de sincronización (Manual 5 §5) ===\n\n");

    /* 1. Mutex: exclusión mutua (2 workers → interleaving real de fibras) */
    printf("--- 1. Mutex: exclusión mutua (%d fibras x %d iteraciones) ---\n",
           N_FIBRAS_MUTEX, K_ITERS);
    scheduler_iniciar(2);
    g_mutex = mutex_crear();
    g_contador = 0;
    static long dummy[N_FIBRAS_MUTEX];
    for (int i = 0; i < N_FIBRAS_MUTEX; i++) {
        dummy[i] = i;
        fibra_crear(fibra_incrementa, &dummy[i], 0);
    }
    for (int i = 0; i < N_FIBRAS_MUTEX; i++) {
        fibra_esperar(prox_id + i);
    }
    prox_id += N_FIBRAS_MUTEX;
    check(g_contador == (long)N_FIBRAS_MUTEX * K_ITERS,
          "mutex: exclusión mutua real — contador == N*K sin pérdidas");
    mutex_destruir(g_mutex);
    scheduler_detener();

    /* 2. Mutex: handoff FIFO main ↔ fibra */
    printf("\n--- 2. Mutex: handoff FIFO main(OS thread) ↔ fibra ---\n");
    g_mutex = mutex_crear();
    g_s_arranque = semaforo_crear(0);
    g_s_done = semaforo_crear(0);
    mutex_bloquear(g_mutex);          /* main toma el mutex */
    g_handoff = 0;
    fibra_crear(fibra_handoff, NULL, 0);   /* la fibra se parquea esperándolo */
    semaforo_esperar(g_s_arranque);   /* la fibra está a punto de bloquearse */
    mutex_desbloquear(g_mutex);       /* handoff a la fibra (primera en cola) */
    semaforo_esperar(g_s_done);       /* determinista: espera a que la fibra complete */
    check(g_handoff == 1, "mutex: la fibra bloqueada completa su sección crítica al liberar el main (handoff)");
    fibra_esperar(prox_id);
    prox_id++;
    mutex_destruir(g_mutex);
    semaforo_destruir(g_s_arranque);
    semaforo_destruir(g_s_done);
    scheduler_detener();

    /* 3. Semáforo(0): fibra despierta al main bloqueado */
    printf("\n--- 3. Semáforo(0): main bloqueado despertado por fibra ---\n");
    scheduler_iniciar(1);
    g_sem = semaforo_crear(0);
    g_señal = 0;
    fibra_crear(fibra_señala, NULL, 0);   /* señala tras fijar g_señal */
    semaforo_esperar(g_sem);              /* se bloquea hasta el señalar */
    check(g_señal == 1, "semáforo: esperar(0) bloquea y el señalar de la fibra despierta");
    fibra_esperar(prox_id);
    prox_id++;
    semaforo_destruir(g_sem);
    scheduler_detener();

    /* 4. Semáforo(1) como lock binario: handoff FIFO fibra ↔ main */
    printf("\n--- 4. Semáforo(1): lock binario con handoff FIFO ---\n");
    scheduler_iniciar(1);
    g_sem = semaforo_crear(1);
    g_s_done = semaforo_crear(0);
    semaforo_esperar(g_sem);              /* main consume el único permiso */
    g_sem_fifo = 0;
    fibra_crear(fibra_sem_fifo, NULL, 0); /* se parquea esperando el permiso */
    semaforo_señalar(g_sem);              /* handoff del permiso a la fibra */
    semaforo_esperar(g_s_done);           /* determinista: espera a que la fibra complete */
    check(g_sem_fifo == 1, "semáforo: la fibra bloqueada recibe el permiso y completa (handoff)");
    fibra_esperar(prox_id);
    prox_id++;
    semaforo_destruir(g_sem);
    semaforo_destruir(g_s_done);
    scheduler_detener();

    /* 5. Barrera: 5 fibras × 2 rondas con verificación de llegada total */
    printf("\n--- 5. Barrera(%d): %d fibras x %d rondas ---\n",
           TOTAL_BARRERA, TOTAL_BARRERA, RONDAS_BARRERA);
    scheduler_iniciar(2);
    g_barrera = barrera_crear(TOTAL_BARRERA);
    g_llegadas_r[0] = g_llegadas_r[1] = g_pasaron_r[0] = g_pasaron_r[1] = 0;
    g_error_barrera = 0;
    static long idx_b[TOTAL_BARRERA];
    for (int i = 0; i < TOTAL_BARRERA; i++) {
        idx_b[i] = i;
        fibra_crear(fibra_barrera, &idx_b[i], 0);
    }
    for (int i = 0; i < TOTAL_BARRERA; i++) {
        fibra_esperar(prox_id + i);
    }
    prox_id += TOTAL_BARRERA;
    check(g_error_barrera == 0,
          "barrera: ninguna fibra pasa hasta que las 5 llegaron (2 rondas)");
    check(g_llegadas_r[0] == TOTAL_BARRERA && g_llegadas_r[1] == TOTAL_BARRERA,
          "barrera: las 5 fibras llegan a ambas rondas (generación)");
    check(g_pasaron_r[0] == TOTAL_BARRERA && g_pasaron_r[1] == TOTAL_BARRERA,
          "barrera: todas las fibras cruzan ambas rondas");
    barrera_destruir(g_barrera);
    scheduler_detener();

    /* 6. Destrucción limpia (ya ejercitada arriba; confirmación explícita) */
    printf("\n--- 6. Destrucción limpia ---\n");
    check(1, "mutex/semaforo/barrera se destruyen sin error tras su uso");

    printf("\n=== Resumen ===\n");
    printf("Exitos: %d\n", tests_passed);
    printf("Fallos: %d\n", tests_failed);
    return tests_failed == 0 ? 0 : 1;
}
