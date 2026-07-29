/**
 * stress_canales_sync.c - Test de estres de canal sincrono (capacidad=0)
 * Verifica que el handoff directo entre productor<->consumidor
 * mediante canal sincrono no produzca deadlocks ni perdidas.
 * Conforme a Manual 5 S5.3.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include "synapse_rt_types.h"
#include "synapse_rt.h"

#define NUM_MSGS 1000
static CanalConcurrencia* ch;

static void* productor(void* arg) {
    (void)arg;
    for (int i = 1; i <= NUM_MSGS; i++) {
        int* p = (int*)malloc(sizeof(int));
        if (!p) { fprintf(stderr, "[PROD] malloc fallo\n"); exit(1); }
        *p = i;
        canal_enviar(ch, p);
        if (i % 200 == 0) fprintf(stderr, "[PROD] enviados %d\n", i);
    }
    fprintf(stderr, "[PROD] Completado - %d enviados\n", NUM_MSGS);
    return (void*)1;
}

static void* consumidor(void* arg) {
    (void)arg;
    for (int i = 1; i <= NUM_MSGS; i++) {
        void* p = canal_recibir(ch);
        if (p == NULL) {
            fprintf(stderr, "[CONS] canal_recibir devolvio NULL en msg %d\n", i);
            return NULL;
        }
        int valor = *(int*)p;
        free(p);
        if (valor != i) {
            fprintf(stderr, "[CONS] ERROR: esperaba %d, recibi %d\n", i, valor);
            exit(1);
        }
        if (i % 200 == 0) fprintf(stderr, "[CONS] recibidos %d\n", i);
    }
    fprintf(stderr, "[CONS] Completado - %d recibidos y verificados\n", NUM_MSGS);
    return (void*)1;
}

int main() {
    fprintf(stderr, "=== TEST DE ESTReS: CANAL SINCRONO (capacidad=0) ===\n");
    fprintf(stderr, "Protocolo: productor(1) <-> consumidor(1) x %d msgs\n", NUM_MSGS);

    ch = canal_crear(0);
    if (!ch) {
        fprintf(stderr, "[FAIL] canal_crear(0) devolvio NULL\n");
        return 1;
    }
    fprintf(stderr, "[CANAL] creado cap=0 (sincrono) es_sync=%d cerrado=%d\n", ch->es_sync, ch->cerrado);

    pthread_t prod_tid, cons_tid;
    pthread_create(&prod_tid, NULL, productor, NULL);
    pthread_create(&cons_tid, NULL, consumidor, NULL);
    fprintf(stderr, "[HILOS] lanzados\n");

    void* prod_ret = NULL;
    void* cons_ret = NULL;
    pthread_join(prod_tid, &prod_ret);
    pthread_join(cons_tid, &cons_ret);

    int pass = (prod_ret != NULL && cons_ret != NULL);
    canal_destruir(ch);

    if (pass) {
        fprintf(stderr, "\n=== RESULTADO: PASS - 0 deadlocks, 0 perdidas ===\n");
        return 0;
    } else {
        fprintf(stderr, "\n=== RESULTADO: FAIL ===\n");
        return 1;
    }
}
