// synapse_rt_concurrency.c — Concurrency module for Synapse runtime
// Extracted from synapse_rt.c: thread-safe I/O, channels, thread tracker
// Compilar: gcc -c synapse_rt_concurrency.c -o synapse_rt_concurrency.o -lpthread

#include "synapse_rt_types.h"
#include "librerias/embedded_libs.h"
#include "tweetnacl.h"

#ifdef _WIN32
  #include <winsock2.h>
#endif

// ============================================================
// Thread-safe I/O
// ============================================================

pthread_mutex_t io_mutex = PTHREAD_MUTEX_INITIALIZER;

void escribir(CadenaSegura contenido) {
    pthread_mutex_lock(&io_mutex);
    fwrite(contenido.datos, 1, contenido.longitud, stdout);
    fflush(stdout);
    pthread_mutex_unlock(&io_mutex);
}

void escribir_linea(CadenaSegura contenido) {
    pthread_mutex_lock(&io_mutex);
    fwrite(contenido.datos, 1, contenido.longitud, stdout);
    fwrite("\n", 1, 1, stdout);
    fflush(stdout);
    pthread_mutex_unlock(&io_mutex);
}

CadenaSegura leer_linea(void) {
    static char _buf[4096];
    if (fgets(_buf, 4096, stdin)) {
        int _len = (int)strlen(_buf);
        if (_len > 0 && _buf[_len - 1] == '\n') { _buf[_len - 1] = '\0'; _len--; }
        char* _dup = (char*)malloc(_len + 1);
        if (!_dup) { return (CadenaSegura){ .longitud = 0, .datos = "" }; }
        memcpy(_dup, _buf, _len + 1);
        return (CadenaSegura){ .longitud = _len, .datos = _dup };
    }
    return (CadenaSegura){ .longitud = 0, .datos = "" };
}

// ============================================================
// Thread tracker
// ============================================================

static int hilos_activos = 0;
static pthread_mutex_t hilo_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t hilo_cond = PTHREAD_COND_INITIALIZER;

static void* _synapse_hilo_wrapper(void* raw_args) {
    struct _HiloArgs* ha = (struct _HiloArgs*)raw_args;
    void* (*fn)(void*) = ha->fn;
    void* arg = ha->arg;
    free(ha);
    fn(arg);
    pthread_mutex_lock(&hilo_mutex);
    hilos_activos--;
    if (hilos_activos == 0) {
        pthread_cond_broadcast(&hilo_cond);
    }
    pthread_mutex_unlock(&hilo_mutex);
    return NULL;
}

void synapse_lanzar_hilo(void* (*fn)(void*), void* arg) {
    pthread_mutex_lock(&hilo_mutex);
    hilos_activos++;
    pthread_mutex_unlock(&hilo_mutex);
    struct _HiloArgs* ha = (struct _HiloArgs*)malloc(sizeof(struct _HiloArgs));
    if (!ha) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en synapse_lanzar_hilo\n"); exit(1); }
    ha->fn = fn;
    ha->arg = arg;
    pthread_t _t;
    pthread_create(&_t, NULL, _synapse_hilo_wrapper, ha);
    pthread_detach(_t);
}

void synapse_esperar_hilos(void) {
    pthread_mutex_lock(&hilo_mutex);
    while (hilos_activos > 0) {
        pthread_cond_wait(&hilo_cond, &hilo_mutex);
    }
    pthread_mutex_unlock(&hilo_mutex);
    watchdog_report();
}

// ============================================================
// CanalConcurrencia API (Zero-Copy, Thread-Safe)
// ============================================================

CanalConcurrencia* canal_crear(uint32_t capacidad) {
    CanalConcurrencia* canal = (CanalConcurrencia*)malloc(sizeof(CanalConcurrencia));
    if (!canal) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en canal_crear\n");
        return NULL;
    }

    if (capacidad == 0) {
        // Canal síncrono: handoff directo sin buffer (Manual 5 §5.3)
        canal->buffer = NULL;
        canal->es_sync = 1;
        canal->sync_item = NULL;
        canal->cerrado = 0;
    } else {
        canal->buffer = (void**)malloc(capacidad * sizeof(void*));
        if (!canal->buffer) {
            fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en canal_crear (buffer)\n");
            free(canal);
            return NULL;
        }
        canal->es_sync = 0;
        canal->sync_item = NULL;
        canal->cerrado = 0;
    }

    canal->capacidad = capacidad;
    canal->cabeza = 0;
    canal->cola = 0;
    canal->contador = 0;

    pthread_mutex_init(&canal->mutex, NULL);
    pthread_cond_init(&canal->no_vacio, NULL);
    pthread_cond_init(&canal->no_lleno, NULL);

    return canal;
}

void canal_enviar(CanalConcurrencia* canal, void* paquete) {
    if (!canal) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: canal nulo en canal_enviar\n");
        return;
    }

    pthread_mutex_lock(&canal->mutex);

    if (canal->es_sync) {
        // Canal síncrono: handoff directo (Manual 5 §5.3)
        // Esperar hasta que un receptor esté listo (contador==0 significa sin receptor)
        while (canal->contador != 0 && !canal->cerrado) {
            pthread_cond_wait(&canal->no_lleno, &canal->mutex);
        }
        if (canal->cerrado) { pthread_mutex_unlock(&canal->mutex); return; }
        // Marcar que hay un emisor con datos
        canal->sync_item = paquete;
        canal->contador = 1;
        // Despertar al receptor
        pthread_cond_signal(&canal->no_vacio);
        // Esperar a que el receptor confirme recepción
        while (canal->contador != 0 && !canal->cerrado) {
            pthread_cond_wait(&canal->no_lleno, &canal->mutex);
        }
        pthread_mutex_unlock(&canal->mutex);
        return;
    }

    // Canal con buffer (capacidad > 0)
    while (canal->contador == canal->capacidad) {
        pthread_cond_wait(&canal->no_lleno, &canal->mutex);
    }

    canal->buffer[canal->cabeza] = paquete;
    canal->cabeza = (canal->cabeza + 1) % canal->capacidad;
    canal->contador++;

    pthread_cond_signal(&canal->no_vacio);
    pthread_mutex_unlock(&canal->mutex);
}

void* canal_recibir(CanalConcurrencia* canal) {
    if (!canal) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: canal nulo en canal_recibir\n");
        return NULL;
    }

    pthread_mutex_lock(&canal->mutex);

    if (canal->es_sync) {
        // Canal síncrono: esperar a que un emisor entregue datos (Manual 5 §5.3)
        while (canal->contador == 0 && !canal->cerrado) {
            pthread_cond_wait(&canal->no_vacio, &canal->mutex);
        }
        if (canal->cerrado) { pthread_mutex_unlock(&canal->mutex); return NULL; }
        void* paquete = canal->sync_item;
        canal->sync_item = NULL;
        // Marcar que el receptor recibió (contador=0) y despertar al emisor
        canal->contador = 0;
        pthread_cond_signal(&canal->no_lleno);
        pthread_mutex_unlock(&canal->mutex);
        return paquete;
    }

    // Canal con buffer (capacidad > 0)
    while (canal->contador == 0) {
        pthread_cond_wait(&canal->no_vacio, &canal->mutex);
    }

    void* paquete = canal->buffer[canal->cola];
    canal->cola = (canal->cola + 1) % canal->capacidad;
    canal->contador--;

    pthread_cond_signal(&canal->no_lleno);
    pthread_mutex_unlock(&canal->mutex);

    return paquete;
}

void canal_destruir(CanalConcurrencia* canal) {
    if (!canal) return;

    // Manual 5 §5.3: senalizar cierre para despertar hilos bloqueados
    pthread_mutex_lock(&canal->mutex);
    canal->cerrado = 1;
    pthread_cond_broadcast(&canal->no_vacio);
    pthread_cond_broadcast(&canal->no_lleno);
    pthread_mutex_unlock(&canal->mutex);

    pthread_mutex_destroy(&canal->mutex);
    pthread_cond_destroy(&canal->no_vacio);
    pthread_cond_destroy(&canal->no_lleno);

    if (canal->buffer && !canal->es_sync) {
        free(canal->buffer);
    }
    free(canal);
}
