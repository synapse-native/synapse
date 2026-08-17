// synapse_rt_concurrency.c �?" Concurrency module for Synapse runtime
// Extracted from synapse_rt.c: channels, thread tracker (thread-safe console
// I/O moved to runtime/core/io.c, F3-1)
// F4.1: fibras ligeras y scheduler M:N (Manual 5 §2.6) �?" Win32 Fiber API en
// Windows, ucontext_t en POSIX.
// Compilar: gcc -c synapse_rt_concurrency.c -o synapse_rt_concurrency.o -lpthread

#if !defined(_WIN32)
  // ucontext_t (Manual 5 §2.6) requiere los feature-test macros ANTES de
  // cualquier include del TU (SUSv3).
  #define _XOPEN_SOURCE 700
#endif

#include "synapse_rt_types.h"
#include "librerias/embedded_libs.h"
#include "axon/tweetnacl.h"

#ifdef _WIN32
  #include <winsock2.h>
  #include <windows.h>
#endif

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
    while (canal->contador == canal->capacidad && !canal->cerrado) {
        pthread_cond_wait(&canal->no_lleno, &canal->mutex);
    }
    if (canal->cerrado) {
        // Manual 5 §3.6: un canal cerrado no acepta más envíos.
        pthread_mutex_unlock(&canal->mutex);
        return;
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
    while (canal->contador == 0 && !canal->cerrado) {
        pthread_cond_wait(&canal->no_vacio, &canal->mutex);
    }
    if (canal->cerrado && canal->contador == 0) {
        // Manual 5 §3.6/§4.3: canal cerrado y vacío -> NULL (el listener
        // del `escuchar` sale del bucle al recibir NULL).
        pthread_mutex_unlock(&canal->mutex);
        return NULL;
    }

    void* paquete = canal->buffer[canal->cola];
    canal->cola = (canal->cola + 1) % canal->capacidad;
    canal->contador--;

    pthread_cond_signal(&canal->no_lleno);
    pthread_mutex_unlock(&canal->mutex);

    return paquete;
}

void cerrar_canal(CanalConcurrencia* canal) {
    // Manual 5 §3.6: cerrar() marca el canal cerrado y despierta a los
    // receptores/emisores bloqueados; los receptores reciben NULL (paridad
    // con el Resultado de cierre del manual) y pueden salir ordenadamente.
    if (!canal) return;

    pthread_mutex_lock(&canal->mutex);
    canal->cerrado = 1;
    pthread_cond_broadcast(&canal->no_vacio);
    pthread_cond_broadcast(&canal->no_lleno);
    pthread_mutex_unlock(&canal->mutex);
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

// ============================================================
// F4.1 �?" Fibras ligeras y Scheduler M:N (Manual 5 §2.6)
// ============================================================
// El modelo del manual: un hilo de usuario ultraligero con pila propia
// (64 KB por defecto), contexto de ejecución e identificador único, que se
// ejecuta sobre un pool de hilos del sistema operativo (M:N). Estructuras
// y API según Manual 5 §2.6 (Fibra, Scheduler, fibra_crear/fibra_esperar/
// fibra_terminar/scheduler_iniciar/scheduler_detener).
//
// Implementación: cooperativa por worker �?" cada fibra corre hasta que
// retorna (la trampolina llama fibra_terminar) o llama fibra_terminar
// explícitamente; al terminar cede el control al worker, que libera pila y
// contexto. Las operaciones de canal (canal_enviar/canal_recibir) siguen
// siendo pthread (F3-6); hacerlas fiber-aware (parquear la fibra en vez de
// bloquear el worker) es la siguiente iteración de Fase 4 (F4.2).

#define FIBRAS_MAX 4096
#define FIBRA_STACK_DEFAULT (64 * 1024)  // Manual 5 §2.1: 64 KB por defecto

typedef struct Fibra {
    void* stack;                // Pila de la fibra
    size_t stack_size;          // Tamaño de la pila
    void* context;              // Win32: LPVOID fiber; POSIX: ucontext_t*
    struct Fibra* next;         // Siguiente fibra en la cola de scheduling
    int id;                     // Identificador único
    int terminada;              // Flag de finalización
    void* resultado;            // Resultado de la fibra (si retorna)
    void (*func)(void*);        // Función de la fibra
    void* arg;                  // Argumento de la fibra
    void* worker_fiber;         // Win32: fiber primaria del worker; POSIX: ucontext_t* del worker
} Fibra;

typedef struct Scheduler {
    Fibra* cola_activa;         // Cola de fibras listas para ejecutar
    Fibra* cola_espera;         // Cola de fibras bloqueadas (reservado F4.2)
    int num_fibras;             // Número total de fibras
    pthread_t* hilos_os;        // Hilos del sistema operativo (pool)
    int num_hilos_os;           // Número de hilos OS (por defecto = núcleos)
    int ejecutando;             // Flag de ejecución
    pthread_mutex_t mutex;      // Mutex para operaciones en colas
    pthread_cond_t cond;        // Despertar workers (implementación F4.1)
    Fibra* cola_activa_tail;    // Cola FIFO (implementación F4.1)
    int proximo_id;             // Contador de ids (implementación F4.1)
} Scheduler;

// Registro de resultados por id (la fibra se libera al terminar; el wait de
// fibra_esperar consulta esta tabla, no el struct ya liberado).
typedef struct {
    int activo;
    int terminada;
    void* resultado;
} _ResultadoFibra;

static Scheduler g_sched;
static _ResultadoFibra g_resultados[FIBRAS_MAX];
static __thread Fibra* _fibra_actual;  // TLS: fibra que corre en este worker

// mutex/cond con inicializadores estáticos (Manual 5 §2.6 no fija el init; el
// static zero-init cubre colas/contadores; usar PTHREAD_MUTEX_INITIALIZER evita
// reinicializarlos desde scheduler_iniciar).
static pthread_mutex_t g_sched_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t g_sched_cond = PTHREAD_COND_INITIALIZER;

// API pública del scheduler de fibras (Manual 5 §2.6). Forward declarations:
// fibra_crear y fibra_terminar se llaman antes de su definición (trampolinas).
void scheduler_iniciar(int num_hilos_os);
void scheduler_detener(void);
void fibra_crear(void (*func)(void*), void* arg, size_t stack_size);
void fibra_esperar(int fibra_id);
void fibra_terminar(void* resultado);

static void* _scheduler_worker(void* arg) {
    (void)arg;
#ifdef _WIN32
    void* primaria = ConvertThreadToFiber(NULL);
#endif

    pthread_mutex_lock(&g_sched_mutex);
    while (g_sched.ejecutando || g_sched.cola_activa) {
        Fibra* f = g_sched.cola_activa;
        if (!f) {
            if (!g_sched.ejecutando) break;
            pthread_cond_wait(&g_sched_cond, &g_sched_mutex);
            continue;
        }
        g_sched.cola_activa = f->next;
        if (g_sched.cola_activa_tail == f) g_sched.cola_activa_tail = NULL;
        f->next = NULL;
        _fibra_actual = f;
#ifdef _WIN32
        f->worker_fiber = primaria;
#endif
        pthread_mutex_unlock(&g_sched_mutex);

#ifdef _WIN32
        SwitchToFiber(f->context);
#else
        // El worker guarda su contexto local; la fibra vuelve aqui al terminar.
        ucontext_t wctx_local;
        f->worker_fiber = &wctx_local;
        if (swapcontext(&wctx_local, (ucontext_t*)f->context) != 0) {
            fprintf(stderr, "ESCAPA_DEL_ALCANCE: swapcontext fallo\n");
            exit(1);
        }
#endif

        // La fibra terminó (fibra_terminar cedió el control): liberar.
        _fibra_actual = NULL;
#ifdef _WIN32
        DeleteFiber(f->context);
#else
        free(f->context);
#endif
        if (f->stack) free(f->stack);
        free(f);

        pthread_mutex_lock(&g_sched_mutex);
    }
    pthread_mutex_unlock(&g_sched_mutex);
#ifdef _WIN32
    ConvertFiberToThread();
#endif
    return NULL;
}

#ifdef _WIN32
static void __stdcall _fibras_trampoline_win(void* param) {
    Fibra* f = (Fibra*)param;
    f->func(f->arg);
    fibra_terminar(NULL);
}
#else
static void _fibras_trampoline_posix(int lo, int hi) {
    // makecontext recibe ints; el puntero a Fibra viaja partido en 2 ints
    // (patr�n est�ndar para 64-bit, evita truncar el puntero).
    uintptr_t p = ((uintptr_t)(unsigned int)hi << 32) | (unsigned int)lo;
    Fibra* f = (Fibra*)p;
    f->func(f->arg);
    fibra_terminar(NULL);
}
#endif

void fibra_crear(void (*func)(void*), void* arg, size_t stack_size) {
    if (stack_size == 0) stack_size = FIBRA_STACK_DEFAULT;

    pthread_mutex_lock(&g_sched_mutex);
    if (!g_sched.ejecutando) {
        pthread_mutex_unlock(&g_sched_mutex);
        scheduler_iniciar(0);   // auto-start con pool por defecto (núcleos)
        pthread_mutex_lock(&g_sched_mutex);
    }

    Fibra* f = (Fibra*)malloc(sizeof(Fibra));
    if (!f) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en fibra_crear\n"); exit(1); }
    memset(f, 0, sizeof(Fibra));
    f->func = func;
    f->arg = arg;
    f->stack_size = stack_size;
    f->id = g_sched.proximo_id++;
    if (f->id >= FIBRAS_MAX) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: FIBRAS_MAX alcanzado\n"); exit(1); }

#ifdef _WIN32
    f->context = (void*)CreateFiber(stack_size, _fibras_trampoline_win, f);
    if (!f->context) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: CreateFiber fallo\n");
        free(f);
        pthread_mutex_unlock(&g_sched_mutex);
        exit(1);
    }
#else
    // POSIX: el puntero a Fibra viaja partido en 2 ints de makecontext
    // (patr�n est�ndar para 64-bit, evita truncar el puntero).
    uintptr_t _p = (uintptr_t)f;
    f->stack = malloc(stack_size);
    if (!f->stack) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en fibra_crear (stack)\n"); free(f); pthread_mutex_unlock(&g_sched_mutex); exit(1); }
    ucontext_t* uc = (ucontext_t*)malloc(sizeof(ucontext_t));
    if (!uc) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en fibra_crear (ctx)\n"); free(f->stack); free(f); pthread_mutex_unlock(&g_sched_mutex); exit(1); }
    if (getcontext(uc) != 0) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: getcontext fallo\n"); exit(1); }
    uc->uc_stack.ss_sp = f->stack;
    uc->uc_stack.ss_size = f->stack_size;
    uc->uc_link = NULL;
    makecontext(uc, (void(*)(void))_fibras_trampoline_posix, 2,
                (int)(_p & 0xFFFFFFFFu), (int)(_p >> 32));
    f->context = (void*)uc;
#endif

    g_resultados[f->id].activo = 1;
    g_resultados[f->id].terminada = 0;
    g_resultados[f->id].resultado = NULL;

    // Encolar FIFO
    if (g_sched.cola_activa_tail) {
        g_sched.cola_activa_tail->next = f;
    } else {
        g_sched.cola_activa = f;
    }
    g_sched.cola_activa_tail = f;
    g_sched.num_fibras++;
    pthread_cond_signal(&g_sched_cond);
    pthread_mutex_unlock(&g_sched_mutex);
}

void fibra_terminar(void* resultado) {
    // Se llama DENTRO de la fibra; publica el resultado y cede el control al
    // worker (que libera pila/contexto). No se retorna a la fibra.
    Fibra* f = _fibra_actual;
    if (!f) return;
    pthread_mutex_lock(&g_sched_mutex);
    if (f->id >= 0 && f->id < FIBRAS_MAX) {
        g_resultados[f->id].resultado = resultado;
        g_resultados[f->id].terminada = 1;
    }
    pthread_cond_broadcast(&g_sched_cond);
    pthread_mutex_unlock(&g_sched_mutex);
#ifdef _WIN32
    SwitchToFiber(f->worker_fiber);
#else
    ucontext_t dummy;
    if (swapcontext(&dummy, (ucontext_t*)f->worker_fiber) != 0) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: swapcontext (terminar) fallo\n");
        exit(1);
    }
#endif
    for (;;) { }  // inalcanzable: el worker libera la fibra
}

void fibra_esperar(int fibra_id) {
    // Espera a que la fibra termine y devuelve su resultado. Llama al mutex
    // protegido: si la fibra no existe (id invalido o ya consumida) retorna
    // sin bloquear (tabla _ResultadoFibra solo se marca, no se reusa).
    pthread_mutex_lock(&g_sched_mutex);
    while (1) {
        if (fibra_id >= 0 && fibra_id < FIBRAS_MAX && g_resultados[fibra_id].activo) {
            if (g_resultados[fibra_id].terminada) {
                pthread_mutex_unlock(&g_sched_mutex);
                return;
            }
            pthread_cond_wait(&g_sched_cond, &g_sched_mutex);
            continue;
        }
        break;
    }
    pthread_mutex_unlock(&g_sched_mutex);
}

void scheduler_iniciar(int num_hilos_os) {
    pthread_mutex_lock(&g_sched_mutex);
    if (g_sched.ejecutando) { pthread_mutex_unlock(&g_sched_mutex); return; }
    if (num_hilos_os <= 0) {
#ifdef _WIN32
        SYSTEM_INFO si;
        GetSystemInfo(&si);
        num_hilos_os = (int)si.dwNumberOfProcessors;
#else
        long n = sysconf(_SC_NPROCESSORS_ONLN);
        num_hilos_os = (n > 0) ? (int)n : 1;
#endif
    }
    g_sched.num_hilos_os = num_hilos_os;
    g_sched.ejecutando = 1;
    g_sched.hilos_os = (pthread_t*)malloc(sizeof(pthread_t) * (size_t)num_hilos_os);
    if (!g_sched.hilos_os) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en scheduler_iniciar\n"); exit(1); }
    pthread_mutex_unlock(&g_sched_mutex);

    for (int i = 0; i < num_hilos_os; i++) {
        if (pthread_create(&g_sched.hilos_os[i], NULL, _scheduler_worker, NULL) != 0) {
            fprintf(stderr, "ESCAPA_DEL_ALCANCE: pthread_create fallo en scheduler_iniciar\n");
            exit(1);
        }
    }
}

void scheduler_detener(void) {
    pthread_mutex_lock(&g_sched_mutex);
    g_sched.ejecutando = 0;
    pthread_cond_broadcast(&g_sched_cond);
    pthread_mutex_unlock(&g_sched_mutex);

    if (g_sched.hilos_os) {
        for (int i = 0; i < g_sched.num_hilos_os; i++) {
            pthread_join(g_sched.hilos_os[i], NULL);
        }
        free(g_sched.hilos_os);
        g_sched.hilos_os = NULL;
    }
}
