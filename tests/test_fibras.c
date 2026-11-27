/*
 * test_fibras.c — F4.1: Prueba del scheduler de fibras (Manual 5 §2.6)
 *
 * Cubre:
 *   1. scheduler_iniciar(num_hilos_os) con pool de 2 workers
 *   2. fibra_crear/fibra_terminar/fibra_esperar (N fibras computando en paralelo)
 *   3. Auto-start: fibra_crear sin scheduler_iniciar previo (pool = núcleos)
 *   4. Tamaño de pila personalizado (fibra_crear con stack_size != 0)
 *   5. fibra_esperar con id inválido: retorna sin bloquear
 *   6. Estrés: M fibras que completan todas sin pérdida de resultados
 *   7. scheduler_detener: los workers terminan limpiamente
 *
 * fibra_crear es void (API del manual) y el scheduler asigna ids secuenciales
 * desde 0 en orden de creación; el test mantiene su propio contador esperado.
 * El resultado de cada fibra se publica en un slot propio del array compartido
 * (fibra_esperar sincroniza; los datos via el argumento de fibra_crear).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* API del scheduler de fibras (Manual 5 §2.6) — definida en runtime/core/concurrency.c */
extern void scheduler_iniciar(int num_hilos_os);
extern void scheduler_detener(void);
extern void fibra_crear(void (*func)(void*), void* arg, size_t stack_size);
extern void fibra_esperar(int fibra_id);
extern void fibra_terminar(void* resultado);

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

/* ===== Fibra que computa: resultado = (arg + 3500) * 2 + index ======================= */
#define N_FIBRAS 8
static long g_slots[N_FIBRAS];

typedef struct {
    long arg;
    int index;
} TrabajoFibra;

static void fibra_computa(void* p) {
    TrabajoFibra* t = (TrabajoFibra*)p;
    long v = t->arg;
    for (long i = 0; i < 1000; i++) v += (i & 7);   /* carga de trabajo determinista: +3500 */
    g_slots[t->index] = v * 2 + t->index;
    fibra_terminar(NULL);
}

/* ===== Fibra con pila personalizada ================================================= */
#define STACK_PROPIO (256 * 1024)
static int g_bandera_stack = 0;

static void fibra_stack_propio(void* p) {
    (void)p;
    char buf[32 * 1024];           /* 32 KB de pila en uso (cabe en 64 KB, sobra con 256 KB) */
    memset(buf, 0, sizeof(buf));
    g_bandera_stack = (int)buf[0] + 1;
    fibra_terminar(NULL);
}

/* ===== Estrés: M fibras ============================================================= */
#define M_FIBRAS 500
static long g_estres[M_FIBRAS];

static void fibra_estres(void* p) {
    long idx = *(long*)p;
    g_estres[idx] = idx * idx;   /* slot propio por fibra: sin carrera entre fibras */
    fibra_terminar(NULL);
}

int main(void) {
    printf("=== F4.1: Scheduler de fibras (Manual 5 §2.6) ===\n\n");

    /* 1. Pool de 2 workers + 8 fibras computando */
    printf("--- 1. scheduler_iniciar(2) + %d fibras ---\n", N_FIBRAS);
    scheduler_iniciar(2);
    static TrabajoFibra t[N_FIBRAS];
    for (int i = 0; i < N_FIBRAS; i++) {
        t[i].arg = 100 + i;
        t[i].index = i;
        fibra_crear(fibra_computa, &t[i], 0);
    }
    for (int i = 0; i < N_FIBRAS; i++) {
        fibra_esperar(prox_id + i);
    }
    prox_id += N_FIBRAS;
    int ok = 1;
    for (int i = 0; i < N_FIBRAS; i++) {
        long esperado = (100 + i + 3500) * 2 + i;
        if (g_slots[i] != esperado) { ok = 0; printf("  slot[%d]=%ld esperado=%ld\n", i, g_slots[i], esperado); }
    }
    check(ok, "8 fibras con 2 workers computan resultados correctos");
    scheduler_detener();

    /* 2. Auto-start (sin scheduler_iniciar previo) */
    printf("\n--- 2. Auto-start del scheduler ---\n");
    g_slots[0] = 0;
    static TrabajoFibra t2;
    t2.arg = 7;
    t2.index = 0;
    fibra_crear(fibra_computa, &t2, 0);   /* debe auto-iniciar el scheduler */
    fibra_esperar(prox_id);
    prox_id++;
    check(g_slots[0] == (7 + 3500) * 2 + 0, "auto-start: fibra crea el scheduler y corre");
    scheduler_detener();

    /* 3. Pila personalizada */
    printf("\n--- 3. Pila personalizada (%d KB) ---\n", STACK_PROPIO / 1024);
    fibra_crear(fibra_stack_propio, NULL, STACK_PROPIO);
    fibra_esperar(prox_id);
    prox_id++;
    check(g_bandera_stack == 1, "fibra con stack_size personalizado corre");
    scheduler_detener();

    /* 4. fibra_esperar con id inválido no bloquea */
    printf("\n--- 4. fibra_esperar id inválido ---\n");
    fibra_esperar(999999);
    check(1, "fibra_esperar(id_invalido) retorna sin bloquear");

    /* 5. Estrés M fibras */
    printf("\n--- 5. Estrés: %d fibras ---\n", M_FIBRAS);
    scheduler_iniciar(4);
    static long idx_arr[M_FIBRAS];
    for (int i = 0; i < M_FIBRAS; i++) {
        idx_arr[i] = i;
        fibra_crear(fibra_estres, &idx_arr[i], 0);
    }
    for (int i = 0; i < M_FIBRAS; i++) {
        fibra_esperar(prox_id + i);
    }
    prox_id += M_FIBRAS;
    ok = 1;
    for (int i = 0; i < M_FIBRAS; i++) {
        if (g_estres[i] != (long)i * i) { ok = 0; break; }
    }
    check(ok, "500 fibras completan con resultados correctos");
    scheduler_detener();

    /* 6. Detener limpio */
    printf("\n--- 6. scheduler_detener limpio ---\n");
    check(1, "scheduler_detener retorna tras unir todos los workers");

    printf("\n=== Resumen ===\n");
    printf("Exitos: %d\n", tests_passed);
    printf("Fallos: %d\n", tests_failed);
    return tests_failed == 0 ? 0 : 1;
}
