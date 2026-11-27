/* F4.3 - fibra_esperar fiber-aware (Manual 5, seccion 2.6)
 *
 * Verifica que una fibra que espera a otra se PARQUEA (cede el worker) en vez
 * de bloquear el pthread del worker. Escenarios:
 *   1. pool 2 workers: A espera a B, ambas terminan, resultado correcto
 *   2. cadena: C espera a B que espera a A (sin deadlock)
 *   3. multi-espera: 2 fibras esperan a la misma objetivo
 *   4. ya terminada: fibra_esperar sobre id terminado retorna inmediato
 *   5. estres: N pares esperante/objetivo con slots propios (sin carreras)
 *   6. worker unico: 1 worker, la espera no bloquea al pool
 *   7. fibra_esperar desde el hilo principal (pthread) -> bloqueo pthread
 *
 * NOTA: el id objetivo se pasa por arg (intptr_t); el contador de ids del
 * scheduler es global y NO resetea entre scheduler_iniciar, asi que el espejo
 * local g_prox_id es acumulativo (patron de test_fibras.c, F4.1).
 *
 * Compilacion (desde la raiz del repo):
 *   gcc -O2 -I. -Wall -Wextra tests/test_fibras_espera.c synapse_rt.o -o tests/test_fibras_espera.exe
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "synapse_rt_types.h"
#include "synapse_rt.h"

extern void scheduler_iniciar(int num_hilos_os);
extern void scheduler_detener(void);
extern void fibra_crear(void (*func)(void*), void* arg, size_t stack_size);
extern void fibra_esperar(int fibra_id);
extern void fibra_terminar(void* resultado);

/* espejo del scheduler: ids secuenciales acumulativos desde 0 */
static int g_prox_id = 0;

/* ---- utilidades ---- */

static int g_fallos = 0;
static int g_esc = 0;

static void esc_inicio(const char *nombre) {
    g_esc++;
    printf("[esc %d] %s ...\n", g_esc, nombre);
    fflush(stdout);
}

static void esc_ok(void) {
    printf("[esc %d] OK\n", g_esc);
    fflush(stdout);
}

static void esc_fail(const char *detalle) {
    printf("[esc %d] *** FALLO: %s\n", g_esc, detalle);
    fflush(stdout);
    g_fallos++;
}

#define COMPROBAR(cond, msg) do { \
    if (!(cond)) { esc_fail(msg); return; } \
} while (0)

/* ---- escenario 1: A espera a B ---- */

static volatile int g_s1_b_termino = 0;

static void fibra_s1_b(void *arg) {
    (void)arg;
    g_s1_b_termino = 1;
}

static void fibra_s1_a(void *arg) {
    int id_b = (int)(intptr_t)arg;
    /* A espera a B; el worker queda libre mientras A esta parqueada. */
    fibra_esperar(id_b);
}

/* ---- escenario 2: cadena C->B->A ---- */

static volatile int g_s2_orden = 0;

static void fibra_s2_a(void *arg) {
    (void)arg;
    g_s2_orden = 1;
}

static void fibra_s2_b(void *arg) {
    int id_a = (int)(intptr_t)arg;
    fibra_esperar(id_a);
    g_s2_orden = g_s2_orden * 10 + 2;
}

static void fibra_s2_c(void *arg) {
    int id_b = (int)(intptr_t)arg;
    fibra_esperar(id_b);
    g_s2_orden = g_s2_orden * 10 + 3;
}

/* ---- escenario 3: multi-espera (2 esperantes sobre 1 objetivo) ---- */

static volatile int g_s3_dato = 0;
static volatile int g_s3_e0 = 0;
static volatile int g_s3_e1 = 0;

static void fibra_s3_obj(void *arg) {
    (void)arg;
    for (volatile int i = 0; i < 5000; i++) { }
    g_s3_dato = 42;
}

static void fibra_s3_esp(void *arg) {
    intptr_t par = (intptr_t)arg;
    int id_obj = (int)(par >> 8);
    int cual = (int)(par & 0xFF);
    fibra_esperar(id_obj);
    if (g_s3_dato == 42) {
        if (cual == 0) g_s3_e0 = 1;
        else g_s3_e1 = 1;
    }
}

/* ---- escenario 4: ya terminada ---- */

static void fibra_s4_obj(void *arg) {
    (void)arg;
    for (volatile int i = 0; i < 1000; i++) { }
}

static void fibra_s4_esp(void *arg) {
    int id_obj = (int)(intptr_t)arg;
    /* el objetivo ya termino antes de que esta fibra corra */
    fibra_esperar(id_obj);
}

/* ---- escenario 5: estres N pares ---- */

#define S5_N 300

static volatile int g_s5_slots[S5_N];

static void fibra_s5_obj(void *arg) {
    int i = (int)(intptr_t)arg;
    for (volatile int k = 0; k < 300; k++) { }
    g_s5_slots[i] = 1;
}

static void fibra_s5_esp(void *arg) {
    intptr_t par = (intptr_t)arg;
    int i = (int)(par & 0xFFFF);
    int id_obj = (int)(par >> 16);
    fibra_esperar(id_obj);
    if (g_s5_slots[i] == 1) {
        g_s5_slots[i] = 2;   /* 2 = espera completada correctamente */
    }
}

/* ---- escenario 6: worker unico ---- */

static volatile int g_s6_aux = 0;

static void fibra_s6_aux(void *arg) {
    (void)arg;
    g_s6_aux = 1;
}

static void fibra_s6_main(void *arg) {
    int id_aux = (int)(intptr_t)arg;
    /* si la espera bloquease el unico worker, la auxiliar nunca correria
     * y el probe se colgaria (timeout del harness) */
    fibra_esperar(id_aux);
    if (g_s6_aux != 1) {
        printf("[esc 6] la auxiliar no corrio\n");
        fflush(stdout);
        exit(4);
    }
}

/* ---- escenario 7: espera desde el hilo principal ---- */

static void fibra_s7_obj(void *arg) {
    (void)arg;
    for (volatile int i = 0; i < 100000; i++) { }
}

/* ---- escenarios (cada uno con su scheduler) ---- */

static void esc_1_pool_dos_workers(void) {
    esc_inicio("pool 2 workers, A espera a B");
    scheduler_iniciar(2);
    int id_b = g_prox_id; fibra_crear(fibra_s1_b, NULL, 0); g_prox_id++;
    int id_a = g_prox_id; fibra_crear(fibra_s1_a, (void *)(intptr_t)id_b, 0); g_prox_id++;
    fibra_esperar(id_a);
    fibra_esperar(id_b);
    COMPROBAR(g_s1_b_termino == 1, "B no termino");
    scheduler_detener();
    esc_ok();
}

static void esc_2_cadena(void) {
    esc_inicio("cadena C espera a B espera a A");
    scheduler_iniciar(2);
    int id_a = g_prox_id; fibra_crear(fibra_s2_a, NULL, 0); g_prox_id++;
    int id_b = g_prox_id; fibra_crear(fibra_s2_b, (void *)(intptr_t)id_a, 0); g_prox_id++;
    int id_c = g_prox_id; fibra_crear(fibra_s2_c, (void *)(intptr_t)id_b, 0); g_prox_id++;
    fibra_esperar(id_a);
    fibra_esperar(id_b);
    fibra_esperar(id_c);
    COMPROBAR(g_s2_orden != 0, "la cadena no completo");
    scheduler_detener();
    esc_ok();
}

static void esc_3_multi_espera(void) {
    esc_inicio("multi-espera (2 esperantes sobre 1 objetivo)");
    scheduler_iniciar(2);
    int id_obj = g_prox_id; fibra_crear(fibra_s3_obj, NULL, 0); g_prox_id++;
    intptr_t par0 = ((intptr_t)id_obj << 8) | 0;
    intptr_t par1 = ((intptr_t)id_obj << 8) | 1;
    int id_e0 = g_prox_id; fibra_crear(fibra_s3_esp, (void *)par0, 0); g_prox_id++;
    int id_e1 = g_prox_id; fibra_crear(fibra_s3_esp, (void *)par1, 0); g_prox_id++;
    fibra_esperar(id_obj);
    fibra_esperar(id_e0);
    fibra_esperar(id_e1);
    COMPROBAR(g_s3_e0 == 1 && g_s3_e1 == 1, "multi-espera no completo");
    scheduler_detener();
    esc_ok();
}

static void esc_4_ya_terminada(void) {
    esc_inicio("espera a fibra ya terminada");
    scheduler_iniciar(2);
    int id_obj = g_prox_id; fibra_crear(fibra_s4_obj, NULL, 0); g_prox_id++;
    fibra_esperar(id_obj);
    int id_esp = g_prox_id; fibra_crear(fibra_s4_esp, (void *)(intptr_t)id_obj, 0); g_prox_id++;
    fibra_esperar(id_esp);
    scheduler_detener();
    esc_ok();
}

static void esc_5_estres(void) {
    esc_inicio("estres 300 pares esperante/objetivo");
    scheduler_iniciar(4);
    int ids[S5_N * 2];
    for (int i = 0; i < S5_N; i++) {
        int id_obj = g_prox_id; fibra_crear(fibra_s5_obj, (void *)(intptr_t)i, 0); g_prox_id++;
        intptr_t par = ((intptr_t)id_obj << 16) | (intptr_t)(i & 0xFFFF);
        int id_esp = g_prox_id; fibra_crear(fibra_s5_esp, (void *)par, 0); g_prox_id++;
        ids[2 * i] = id_obj;
        ids[2 * i + 1] = id_esp;
    }
    for (int i = 0; i < S5_N; i++) {
        fibra_esperar(ids[2 * i]);
        fibra_esperar(ids[2 * i + 1]);
    }
    int completadas = 0;
    for (int i = 0; i < S5_N; i++) {
        if (g_s5_slots[i] == 2) completadas++;
    }
    COMPROBAR(completadas == S5_N, "estres incompleto");
    scheduler_detener();
    esc_ok();
}

static void esc_6_worker_unico(void) {
    esc_inicio("worker unico (la espera no bloquea el pool)");
    scheduler_iniciar(1);
    int id_aux = g_prox_id; fibra_crear(fibra_s6_aux, NULL, 0); g_prox_id++;
    int id_main = g_prox_id; fibra_crear(fibra_s6_main, (void *)(intptr_t)id_aux, 0); g_prox_id++;
    fibra_esperar(id_aux);
    fibra_esperar(id_main);
    scheduler_detener();
    esc_ok();
}

static void esc_7_pthread(void) {
    esc_inicio("fibra_esperar desde hilo principal (pthread)");
    scheduler_iniciar(2);
    int id_obj = g_prox_id; fibra_crear(fibra_s7_obj, NULL, 0); g_prox_id++;
    fibra_esperar(id_obj);
    scheduler_detener();
    esc_ok();
}

int main(void) {
    printf("=== test_fibras_espera (F4.3) ===\n");
    fflush(stdout);

    esc_1_pool_dos_workers();
    esc_2_cadena();
    esc_3_multi_espera();
    esc_4_ya_terminada();
    esc_5_estres();
    esc_6_worker_unico();
    esc_7_pthread();

    printf("=== RESULTADO: %s (fallos: %d) ===\n",
           g_fallos == 0 ? "PASS" : "FALLO", g_fallos);
    fflush(stdout);
    return g_fallos == 0 ? 0 : 1;
}
