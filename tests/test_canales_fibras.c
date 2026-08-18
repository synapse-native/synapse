/*
 * test_canales_fibras.c — F4.2: Canales con bloqueo fiber-aware
 * (Manual 5 §2.6 cola_espera / §3 canales FIFO; ROADMAP Fase 4)
 *
 * Cubre:
 *   1. Productor/consumidor de FIBRAS con canal con buffer (capacidad 4):
 *      el productor se parquea cuando el buffer esta lleno y el consumidor
 *      cuando esta vacio — el worker NUNCA se bloquea (pthread).
 *   2. Canal sincrono (capacidad 0) fibra<->fibra: handoff directo.
 *   3. 1 worker + 2 fibras: la 1. se parquea en un receive (canal vacio) y
 *      la 2. IGUAL corre (si el worker se bloqueara, la 2. jamas correria);
 *      luego el hilo principal envia y la fibra parqueada se despierta.
 *   4. Cierre de canal despierta una fibra parqueada en receive -> NULL.
 *   5. Mixto: emisor THREAD -> receptor fibra, y emisor fibra -> receptor
 *      THREAD (paridad del handoff directo con hilos OS).
 *   6. Estres: 40 fibras emisoras x 25 items + 1 consumidor sobre un canal
 *      con buffer 8 (1.000 mensajes), sin deadlocks ni perdidas.
 *   7. Cierre con emisor parqueado (buffer lleno): el envio se descarta
 *      (Manual 5 §3.6) y la fibra termina limpiamente.
 *
 * fibra_crear es void (API del manual) y el scheduler asigna ids secuenciales
 * desde 0; el test mantiene su propio contador esperado (espejo del
 * scheduler, patron test_fibras.c F4.1).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "synapse_rt_types.h"
#include "synapse_rt.h"

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

/* ===== 1. Productor/consumidor de fibras con buffer (capacidad 4) ========== */
#define BUF_CAP 4
#define N_ITEMS 200
static CanalConcurrencia* g_ch_buf;
static int g_buf_ok = 1;

static void fibra_productor(void* p) {
    (void)p;
    for (int i = 0; i < N_ITEMS; i++) {
        int* dato = (int*)malloc(sizeof(int));
        if (!dato) { fprintf(stderr, "[PROD] malloc fallo\n"); exit(1); }
        *dato = i;
        canal_enviar(g_ch_buf, dato);   /* se parquea si el buffer esta lleno */
    }
    fibra_terminar(NULL);
}

static void fibra_consumidor(void* p) {
    (void)p;
    for (int i = 0; i < N_ITEMS; i++) {
        int* dato = (int*)canal_recibir(g_ch_buf, &(bool){0});   /* se parquea si esta vacio */
        if (!dato || *dato != i) { g_buf_ok = 0; break; }
        free(dato);
    }
    fibra_terminar(NULL);
}

/* ===== 2. Canal sincrono (capacidad 0) fibra<->fibra ======================= */
#define SYNC_N 50
static CanalConcurrencia* g_ch_sync;
static int g_sync_ok = 1;

static void fibra_prod_sync(void* p) {
    (void)p;
    for (int i = 0; i < SYNC_N; i++) {
        int* dato = (int*)malloc(sizeof(int));
        if (!dato) { fprintf(stderr, "[SYNC-P] malloc fallo\n"); exit(1); }
        *dato = i + 1000;
        canal_enviar(g_ch_sync, dato);   /* handoff directo (capacidad 0) */
    }
    fibra_terminar(NULL);
}

static void fibra_cons_sync(void* p) {
    (void)p;
    for (int i = 0; i < SYNC_N; i++) {
        int* dato = (int*)canal_recibir(g_ch_sync, &(bool){0});
        if (!dato || *dato != i + 1000) { g_sync_ok = 0; break; }
        free(dato);
    }
    fibra_terminar(NULL);
}

/* ===== 3. 1 worker: fibra parqueada NO bloquea al worker =================== */
static CanalConcurrencia* g_ch3;
static int g_fibra_b_corrio = 0;
static long g_slot3 = -1;

static void fibra3_a_recibe(void* p) {
    (void)p;
    void* dato = canal_recibir(g_ch3, &(bool){0});   /* canal vacio: se parquea */
    long v = dato ? *(long*)dato : -1;
    g_slot3 = v;
    fibra_terminar(NULL);
}

static void fibra3_b_correr(void* p) {
    (void)p;
    g_fibra_b_corrio = 1;   /* solo corre si el worker siguio tras el parqueo */
    fibra_terminar(NULL);
}

/* ===== 4. Cierre despierta una fibra parqueada en receive ================== */
static CanalConcurrencia* g_ch4;
static int g_cierre_vio_nulo = 0;

static void fibra4_recibe(void* p) {
    (void)p;
    void* dato = canal_recibir(g_ch4, &(bool){0});   /* canal vacio: se parquea */
    g_cierre_vio_nulo = (dato == NULL);  /* cerrar_canal -> NULL (Manual 5 §3.6) */
    fibra_terminar(NULL);
}

/* ===== 5. Mixto thread <-> fibra =========================================== */
#define MIX_N 3
static CanalConcurrencia* g_ch_mix_fr;   /* emisor thread -> receptor fibra */
static CanalConcurrencia* g_ch_mix_fs;   /* emisor fibra -> receptor thread */
static int g_mix_fr_ok = 1;
static int g_mix_fs_ok = 1;

static void fibra_mix_receptor(void* p) {
    (void)p;
    for (int i = 0; i < MIX_N; i++) {
        int* dato = (int*)canal_recibir(g_ch_mix_fr, &(bool){0});
        if (!dato || *dato != i) { g_mix_fr_ok = 0; break; }
        free(dato);
    }
    fibra_terminar(NULL);
}

static void fibra_mix_emisor(void* p) {
    (void)p;
    for (int i = 0; i < MIX_N; i++) {
        int* dato = (int*)malloc(sizeof(int));
        if (!dato) { fprintf(stderr, "[MIX-FS] malloc fallo\n"); exit(1); }
        *dato = i + 2000;
        canal_enviar(g_ch_mix_fs, dato);   /* se parquea hasta que el thread reciba */
    }
    fibra_terminar(NULL);
}

/* ===== 6. Estres: 40 emisores x 25 + 1 consumidor (buffer 8) =============== */
#define ESTRES_EMISORES 40
#define ESTRES_POR_EMISOR 25
#define ESTRES_TOTAL (ESTRES_EMISORES * ESTRES_POR_EMISOR)
#define ESTRES_CAP 8
static CanalConcurrencia* g_ch_estres;
static int g_estres_vistos[ESTRES_EMISORES];
static int g_estres_ok = 1;

static void fibra_estres_emisor(void* p) {
    long idx = *(long*)p;
    for (int j = 0; j < ESTRES_POR_EMISOR; j++) {
        int* dato = (int*)malloc(sizeof(int));
        if (!dato) { fprintf(stderr, "[ESTRES-E] malloc fallo\n"); exit(1); }
        *dato = (int)idx;
        canal_enviar(g_ch_estres, dato);
    }
    fibra_terminar(NULL);
}

static void fibra_estres_consumidor(void* p) {
    (void)p;
    for (int i = 0; i < ESTRES_TOTAL; i++) {
        int* dato = (int*)canal_recibir(g_ch_estres, &(bool){0});
        if (!dato) { g_estres_ok = 0; break; }
        if (*dato < 0 || *dato >= ESTRES_EMISORES) { g_estres_ok = 0; free(dato); break; }
        g_estres_vistos[*dato]++;
        free(dato);
    }
    fibra_terminar(NULL);
}

/* ===== 7. Cierre con emisor parqueado (buffer lleno) ======================= */
#define CIERRE_CAP 2
static CanalConcurrencia* g_ch_cierre;
static int g_cierre_emisor_termino = 0;
static int g_cierre_items[3];   /* items estaticos: sin gestion de memoria en el test */

static void fibra_cierre_emisor(void* p) {
    (void)p;
    for (int i = 0; i < 3; i++) {
        canal_enviar(g_ch_cierre, &g_cierre_items[i]);
        /* el 3.er envio se parquea (buffer lleno) y luego se descarta al cerrar */
    }
    g_cierre_emisor_termino = 1;
    fibra_terminar(NULL);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);   /* sin buffer: localizar el crash */
    printf("=== F4.2: Canales con bloqueo fiber-aware (Manual 5 §2.6/§3) ===\n\n");

    /* 1. Buffer capacity 4: productor/consumidor de fibras */
    printf("--- 1. Buffer cap=%d, %d items (fibras) ---\n", BUF_CAP, N_ITEMS);
    scheduler_iniciar(2);
    g_ch_buf = canal_crear(BUF_CAP);
    fibra_crear(fibra_productor, NULL, 0);
    fibra_crear(fibra_consumidor, NULL, 0);
    fibra_esperar(prox_id);
    fibra_esperar(prox_id + 1);
    prox_id += 2;
    check(g_buf_ok == 1, "productor/consumidor de fibras: 200 items en orden (buffer 4)");
    canal_destruir(g_ch_buf);
    scheduler_detener();

    /* 2. Canal sincrono fibra<->fibra */
    printf("\n--- 2. Canal sincrono (capacidad 0), %d items ---\n", SYNC_N);
    g_ch_sync = canal_crear(0);
    fibra_crear(fibra_prod_sync, NULL, 0);
    fibra_crear(fibra_cons_sync, NULL, 0);
    fibra_esperar(prox_id);
    fibra_esperar(prox_id + 1);
    prox_id += 2;
    check(g_sync_ok == 1, "canal sincrono fibra<->fibra: handoff directo 50 items");
    canal_destruir(g_ch_sync);
    scheduler_detener();

    /* 3. 1 worker: la fibra parqueada no bloquea al worker */
    printf("\n--- 3. 1 worker: fibra parqueada NO bloquea al worker ---\n");
    scheduler_iniciar(1);
    g_ch3 = canal_crear(4);
    fibra_crear(fibra3_a_recibe, NULL, 0);   /* se parquea (canal vacio) */
    fibra_crear(fibra3_b_correr, NULL, 0);   /* corre solo si el worker siguio */
    {
        long valor = 42;
        /* dar tiempo a que A se parquee; el envio despierta a la fibra parqueada */
        for (volatile int i = 0; i < 200000; i++) { }
        canal_enviar(g_ch3, &valor);
    }
    fibra_esperar(prox_id);
    fibra_esperar(prox_id + 1);
    prox_id += 2;
    check(g_fibra_b_corrio == 1, "1 worker: la 2. fibra corre mientras la 1. esta parqueada");
    check(g_slot3 == 42, "la fibra parqueada en receive se despierta y recibe el dato");
    canal_destruir(g_ch3);
    scheduler_detener();

    /* 4. Cierre despierta una fibra parqueada en receive */
    printf("\n--- 4. cerrar_canal despierta una fibra parqueada ---\n");
    scheduler_iniciar(2);
    g_ch4 = canal_crear(4);
    fibra_crear(fibra4_recibe, NULL, 0);
    for (volatile int i = 0; i < 200000; i++) { }
    cerrar_canal(g_ch4);
    fibra_esperar(prox_id);
    prox_id++;
    check(g_cierre_vio_nulo == 1, "cerrar_canal -> la fibra parqueada recibe NULL");
    canal_destruir(g_ch4);
    scheduler_detener();

    /* 5. Mixto thread <-> fibra */
    printf("\n--- 5. Mixto thread <-> fibra ---\n");
    scheduler_iniciar(2);
    g_ch_mix_fr = canal_crear(4);
    g_ch_mix_fs = canal_crear(0);
    fibra_crear(fibra_mix_receptor, NULL, 0);
    fibra_crear(fibra_mix_emisor, NULL, 0);
    for (int i = 0; i < MIX_N; i++) {
        int* dato = (int*)malloc(sizeof(int));
        if (!dato) { fprintf(stderr, "[MIX] malloc fallo\n"); exit(1); }
        *dato = i;
        canal_enviar(g_ch_mix_fr, dato);   /* thread -> fibra parqueada */
    }
    for (int i = 0; i < MIX_N; i++) {
        int* dato = (int*)canal_recibir(g_ch_mix_fs, &(bool){0});   /* thread recibe de la fibra */
        if (!dato || *dato != i + 2000) { g_mix_fs_ok = 0; }
        free(dato);
    }
    fibra_esperar(prox_id);
    fibra_esperar(prox_id + 1);
    prox_id += 2;
    check(g_mix_fr_ok == 1, "emisor thread -> receptor fibra parqueada (handoff directo)");
    check(g_mix_fs_ok == 1, "emisor fibra -> receptor thread (handoff directo)");
    canal_destruir(g_ch_mix_fr);
    canal_destruir(g_ch_mix_fs);
    scheduler_detener();

    /* 6. Estres: 40 emisores x 25 + consumidor (buffer 8) */
    printf("\n--- 6. Estres: %d emisores x %d + 1 consumidor (buffer %d) ---\n",
           ESTRES_EMISORES, ESTRES_POR_EMISOR, ESTRES_CAP);
    scheduler_iniciar(4);
    memset(g_estres_vistos, 0, sizeof(g_estres_vistos));
    g_ch_estres = canal_crear(ESTRES_CAP);
    static long idx_arr[ESTRES_EMISORES];
    for (int i = 0; i < ESTRES_EMISORES; i++) {
        idx_arr[i] = i;
        fibra_crear(fibra_estres_emisor, &idx_arr[i], 0);
    }
    fibra_crear(fibra_estres_consumidor, NULL, 0);
    for (int i = 0; i < ESTRES_EMISORES + 1; i++) {
        fibra_esperar(prox_id + i);
    }
    prox_id += ESTRES_EMISORES + 1;
    {
        int ok = g_estres_ok == 1;
        for (int i = 0; i < ESTRES_EMISORES; i++) {
            if (g_estres_vistos[i] != ESTRES_POR_EMISOR) { ok = 0; break; }
        }
        check(ok, "estres: 1.000 mensajes sin deadlocks ni perdidas");
    }
    canal_destruir(g_ch_estres);
    scheduler_detener();

    /* 7. Cierre con emisor parqueado (buffer lleno) */
    printf("\n--- 7. cerrar_canal con emisor parqueado (buffer lleno) ---\n");
    scheduler_iniciar(2);
    for (int i = 0; i < 3; i++) g_cierre_items[i] = i + 1;
    g_ch_cierre = canal_crear(CIERRE_CAP);
    fibra_crear(fibra_cierre_emisor, NULL, 0);
    for (volatile int i = 0; i < 300000; i++) { }
    cerrar_canal(g_ch_cierre);
    fibra_esperar(prox_id);
    prox_id++;
    check(g_cierre_emisor_termino == 1, "el emisor parqueado se despierta al cerrar y termina");
    canal_destruir(g_ch_cierre);
    scheduler_detener();

    printf("\n=== Resumen ===\n");
    printf("Exitos: %d\n", tests_passed);
    printf("Fallos: %d\n", tests_failed);
    return tests_failed == 0 ? 0 : 1;
}
