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

// F4.2: el parqueo de fibras (sección F4.1) se invoca desde las operaciones
// de canal. Declaraciones adelantadas (Fibra ya es tipo incompleto vía
// synapse_rt_types.h).
static __thread Fibra* _fibra_actual;
static void _fibra_parquear(void);
static void _scheduler_despertar_fibra(Fibra* f);
static void _sched_mover_a_activa(Fibra* f);

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

    // F4.2: colas de espera de fibras parqueadas vacías.
    canal->espera_envio = NULL;
    canal->espera_envio_tail = NULL;
    canal->espera_recepcion = NULL;
    canal->espera_recepcion_tail = NULL;

    pthread_mutex_init(&canal->mutex, NULL);
    pthread_cond_init(&canal->no_vacio, NULL);
    pthread_cond_init(&canal->no_lleno, NULL);

    return canal;
}

// F4.2: encola la fibra actual en la cola de espera del canal y cede el
// control al worker (que sigue con otras fibras). Al reanudar, el envío ya
// fue completado por el waker (o el canal se cerró y el envío se descarta,
// Manual 5 §3.6).
static void _canal_parquear_emisor(CanalConcurrencia* canal, void* paquete) {
    _EsperaFibra* n = (_EsperaFibra*)malloc(sizeof(_EsperaFibra));
    if (!n) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en canal_enviar (parqueo)\n");
        exit(1);
    }
    n->next = NULL;
    n->fibra = _fibra_actual;
    n->dato = paquete;
    n->satisfecho = 0;
    if (canal->espera_envio_tail) {
        canal->espera_envio_tail->next = n;
    } else {
        canal->espera_envio = n;
    }
    canal->espera_envio_tail = n;
    // Despertar a un receptor THREAD que espera en la cond: puede completar
    // este envío tomando el dato del nodo (canal síncrono) o un item del
    // buffer (canal con buffer lleno por otros emisores).
    pthread_cond_signal(&canal->no_vacio);
    pthread_mutex_unlock(&canal->mutex);
    _fibra_parquear();
    free(n);
}

void canal_enviar(CanalConcurrencia* canal, void* paquete) {
    if (!canal) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: canal nulo en canal_enviar\n");
        return;
    }

    pthread_mutex_lock(&canal->mutex);

    for (;;) {
        if (canal->cerrado) {
            // Manual 5 §3.6: un canal cerrado no acepta más envíos.
            pthread_mutex_unlock(&canal->mutex);
            return;
        }

        // 1) Receptor parqueado (fibra): handoff directo (F4.2).
        if (canal->espera_recepcion) {
            _EsperaFibra* r = canal->espera_recepcion;
            canal->espera_recepcion = r->next;
            if (canal->espera_recepcion_tail == r) canal->espera_recepcion_tail = NULL;
            r->dato = paquete;
            r->satisfecho = 1;
            Fibra* rf = r->fibra;
            _scheduler_despertar_fibra(rf);
            pthread_mutex_unlock(&canal->mutex);
            return;
        }

        if (canal->es_sync) {
            // Canal síncrono: rendezvous directo con un receptor thread.
            // Solo hilos OS: una FIBRA jamás bloquea el worker con cond_wait
            // (F4.2) — si no hay receptor disponible se parquea abajo.
            if (!_fibra_actual && canal->contador == 0) {
                canal->sync_item = paquete;
                canal->contador = 1;
                pthread_cond_signal(&canal->no_vacio);
                while (canal->contador != 0 && !canal->cerrado) {
                    pthread_cond_wait(&canal->no_lleno, &canal->mutex);
                }
                pthread_mutex_unlock(&canal->mutex);
                return;
            }
        } else {
            // Canal con buffer (capacidad > 0)
            if (canal->contador < canal->capacidad) {
                canal->buffer[canal->cabeza] = paquete;
                canal->cabeza = (canal->cabeza + 1) % canal->capacidad;
                canal->contador++;
                pthread_cond_signal(&canal->no_vacio);
                pthread_mutex_unlock(&canal->mutex);
                return;
            }
        }

        // 2) Bloquea: buffer lleno o síncrono sin receptor disponible.
        if (_fibra_actual) {
            // Fibra: parquear (F4.2) — el worker sigue con otras fibras.
            _canal_parquear_emisor(canal, paquete);
            return;
        }
        // Hilo OS: bloqueo pthread (comportamiento previo F3-6).
        pthread_cond_wait(&canal->no_lleno, &canal->mutex);
    }
}

void* canal_recibir(CanalConcurrencia* canal, bool* cerrado) {
    if (!canal) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: canal nulo en canal_recibir\n");
        if (cerrado) *cerrado = true;
        return NULL;
    }
    if (cerrado) *cerrado = false;

    pthread_mutex_lock(&canal->mutex);

    for (;;) {
        if (canal->es_sync) {
            // 1) Emisor parqueado (fibra) en canal síncrono: su dato se
            // entrega directo (FIFO entre emisores parqueados, F4.2).
            if (canal->espera_envio) {
                _EsperaFibra* s = canal->espera_envio;
                canal->espera_envio = s->next;
                if (canal->espera_envio_tail == s) canal->espera_envio_tail = NULL;
                void* paquete = s->dato;
                s->satisfecho = 1;
                Fibra* sf = s->fibra;
                _scheduler_despertar_fibra(sf);
                pthread_mutex_unlock(&canal->mutex);
                if (cerrado) *cerrado = false;
                return paquete;
            }
            if (canal->cerrado) {
                pthread_mutex_unlock(&canal->mutex);
                if (cerrado) *cerrado = true;
                return NULL;
            }
            if (canal->contador == 1) {
                // Item de un emisor thread en rendezvous: confirmar recepción.
                void* paquete = canal->sync_item;
                canal->sync_item = NULL;
                canal->contador = 0;
                pthread_cond_signal(&canal->no_lleno);
                pthread_mutex_unlock(&canal->mutex);
                if (cerrado) *cerrado = false;
                return paquete;
            }
        } else {
            // 1) Canal con buffer: FIFO estricto — primero el buffer; el slot
            // liberado se rellena con el item de un emisor parqueado (F4.2).
            if (canal->contador > 0) {
                void* paquete = canal->buffer[canal->cola];
                canal->cola = (canal->cola + 1) % canal->capacidad;
                canal->contador--;
                if (canal->espera_envio) {
                    _EsperaFibra* s = canal->espera_envio;
                    canal->espera_envio = s->next;
                    if (canal->espera_envio_tail == s) canal->espera_envio_tail = NULL;
                    canal->buffer[canal->cabeza] = s->dato;
                    canal->cabeza = (canal->cabeza + 1) % canal->capacidad;
                    canal->contador++;
                    s->satisfecho = 1;
                    Fibra* sf = s->fibra;
                    _scheduler_despertar_fibra(sf);
                }
                pthread_cond_signal(&canal->no_lleno);
                pthread_mutex_unlock(&canal->mutex);
                if (cerrado) *cerrado = false;
                return paquete;
            }
            if (canal->cerrado) {
                // Manual 5 §3.6/§4.3: canal cerrado y vacío -> NULL con
                // *cerrado = true (el listener del `escuchar` sale del bucle).
                // El 0 real se entrega boxeado (NULL) con *cerrado = false,
                // distinguible del cierre (F4-6).
                pthread_mutex_unlock(&canal->mutex);
                if (cerrado) *cerrado = true;
                return NULL;
            }
        }

        // 2) Bloquea: canal vacío (o síncrono sin emisor).
        if (_fibra_actual) {
            // Fibra: parquear (F4.2) — el worker sigue con otras fibras.
            _EsperaFibra* n = (_EsperaFibra*)malloc(sizeof(_EsperaFibra));
            if (!n) {
                fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en canal_recibir (parqueo)\n");
                pthread_mutex_unlock(&canal->mutex);
                if (cerrado) *cerrado = true;
                return NULL;
            }
            n->next = NULL;
            n->fibra = _fibra_actual;
            n->dato = NULL;
            n->satisfecho = 0;
            if (canal->espera_recepcion_tail) {
                canal->espera_recepcion_tail->next = n;
            } else {
                canal->espera_recepcion = n;
            }
            canal->espera_recepcion_tail = n;
            // Despertar a un emisor THREAD que espera en la cond: al reanudar
            // re-chequea y completa este receive (handoff directo al receptor
            // parqueado) o rellenar el slot liberado del buffer.
            pthread_cond_signal(&canal->no_lleno);
            pthread_mutex_unlock(&canal->mutex);
            _fibra_parquear();
            // Reanudada: dato si el waker completó el envío (satisfecho=1);
            // NULL si el canal se cerró (satisfecho=0) — F4-6 distingue el
            // cierre del valor 0 (que se entrega boxeado con satisfecho=1).
            pthread_mutex_lock(&canal->mutex);
            void* paquete = n->dato;
            int satisfecho = n->satisfecho;
            pthread_mutex_unlock(&canal->mutex);
            free(n);
            if (cerrado) *cerrado = (satisfecho == 0);
            return paquete;
        }
        // Hilo OS: bloqueo pthread (comportamiento previo F3-6).
        pthread_cond_wait(&canal->no_vacio, &canal->mutex);
    }
}

void cerrar_canal(CanalConcurrencia* canal) {
    // Manual 5 §3.6: cerrar() marca el canal cerrado y despierta a los
    // receptores/emisores bloqueados; los receptores reciben NULL (paridad
    // con el Resultado de cierre del manual) y pueden salir ordenadamente.
    if (!canal) return;

    pthread_mutex_lock(&canal->mutex);
    canal->cerrado = 1;
    // F4.2: despertar fibras parqueadas — su operación queda insatisfecha
    // (canal_recibir devuelve NULL; canal_enviar descarta el envío). El nodo
    // de espera lo libera la propia fibra al reanudar.
    while (canal->espera_envio) {
        _EsperaFibra* n = canal->espera_envio;
        canal->espera_envio = n->next;
        if (canal->espera_envio_tail == n) canal->espera_envio_tail = NULL;
        Fibra* f = n->fibra;
        _scheduler_despertar_fibra(f);
    }
    while (canal->espera_recepcion) {
        _EsperaFibra* n = canal->espera_recepcion;
        canal->espera_recepcion = n->next;
        if (canal->espera_recepcion_tail == n) canal->espera_recepcion_tail = NULL;
        Fibra* f = n->fibra;
        _scheduler_despertar_fibra(f);
    }
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
// contexto.
// F4.2: las operaciones de canal (canal_enviar/canal_recibir) son
// fiber-aware — cuando una fibra se bloquearía (buffer lleno/vacío o canal
// síncrono sin pareja) se PARQUEA en la cola_espera del scheduler (Manual 5
// §2.6) y cede el control a su worker, que sigue ejecutando otras fibras; el
// waker la re-encola en cola_activa al completar la operación. Los hilos OS
// (no fibras) conservan el bloqueo pthread (comportamiento previo F3-6).

// Estados de una fibra (transiciones bajo g_sched_mutex, F4.2):
//   CORRIENDO  -> PARQUEADA (se bloquea en un canal y cede al worker)
//   PARQUEADA  -> CORRIENDO (la despierta el waker de la operación)
//   CORRIENDO  -> TERMINADA (fibra_terminar publica resultado y cede)
#define F_ESTADO_CORRIENDO  0
#define F_ESTADO_PARQUEADA  1
#define F_ESTADO_TERMINADA  2

#define FIBRAS_MAX 4096
#define FIBRA_STACK_DEFAULT (64 * 1024)  // Manual 5 §2.1: 64 KB por defecto

typedef struct Fibra {
    void* stack;                // Pila de la fibra
    size_t stack_size;          // Tamaño de la pila
    void* context;              // Win32: LPVOID fiber; POSIX: ucontext_t*
    struct Fibra* next;         // Siguiente fibra en la cola de scheduling
    int id;                     // Identificador único
    int terminada;              // Flag de finalización (tabla g_resultados)
    void* resultado;            // Resultado de la fibra (si retorna)
    void (*func)(void*);        // Función de la fibra
    void* arg;                  // Argumento de la fibra
    void* worker_fiber;         // Win32: fiber primaria del worker; POSIX: ucontext_t* del worker
    int estado;                 // F4.2: F_ESTADO_* (bajo g_sched_mutex)
    int despertado;             // F4.2: el waker completó la op antes del park
} Fibra;

typedef struct Scheduler {
    Fibra* cola_activa;         // Cola de fibras listas para ejecutar
    Fibra* cola_espera;         // Cola de fibras bloqueadas (F4.2: parqueadas)
    int num_fibras;             // Número total de fibras
    pthread_t* hilos_os;        // Hilos del sistema operativo (pool)
    int num_hilos_os;           // Número de hilos OS (por defecto = núcleos)
    int ejecutando;             // Flag de ejecución
    pthread_mutex_t mutex;      // Mutex para operaciones en colas
    pthread_cond_t cond;        // Despertar workers (implementación F4.1)
    Fibra* cola_activa_tail;    // Cola FIFO (implementación F4.1)
    Fibra* cola_espera_tail;    // Cola FIFO de parqueadas (implementación F4.2)
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
// _fibra_actual declarada al inicio del TU (la usan las operaciones de canal).

// F4.3: colas FIFO de fibras esperando a una fibra objetivo (fibra_esperar
// llamado DESDE una fibra). El nodo lo libera fibra_terminar de la objetivo
// al despertar; la esperante jamás toca el nodo tras reanudar (patrón F4.2).
typedef struct _EsperaFibraId {
    struct _EsperaFibraId* next;
    Fibra* fibra;                // fibra esperante
} _EsperaFibraId;

static _EsperaFibraId* g_espera_id[FIBRAS_MAX];
static _EsperaFibraId* g_espera_id_tail[FIBRAS_MAX];

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
        // El worker guarda su contexto local; la fibra vuelve aqui al terminar
        // o al parquearse. Se re-vincula por ejecución: si la fibra fue
        // despertada y la toma otro worker, cederá a ESE worker (sin migrar
        // contextos entre hilos).
        ucontext_t wctx_local;
        f->worker_fiber = &wctx_local;
        if (swapcontext(&wctx_local, (ucontext_t*)f->context) != 0) {
            fprintf(stderr, "ESCAPA_DEL_ALCANCE: swapcontext fallo\n");
            exit(1);
        }
#endif

        // La fibra cedió el control: se parqueó (F4.2) o terminó. El worker
        // registra el parqueo AQUÍ, tras el yield — la fibra queda marcada
        // como suspendida antes de ser despertable (sin carrera de doble
        // ejecución con un waker).
        _fibra_actual = NULL;
        pthread_mutex_lock(&g_sched_mutex);
        if (f->despertado && f->estado != F_ESTADO_TERMINADA) {
            // El waker completó la operación mientras la fibra cedía: la
            // fibra NO se parquea — re-encolar en cola_activa para que
            // reanude su operación de canal (aún no está en cola_espera).
            f->despertado = 0;
            f->estado = F_ESTADO_CORRIENDO;
            f->next = NULL;
            if (g_sched.cola_activa_tail) {
                g_sched.cola_activa_tail->next = f;
            } else {
                g_sched.cola_activa = f;
            }
            g_sched.cola_activa_tail = f;
            pthread_cond_signal(&g_sched_cond);
            continue;
        }
        f->despertado = 0;   // residual en estado TERMINADA
        if (f->estado == F_ESTADO_TERMINADA) {
            // F4.4: la fibra terminó — decrementar el contador de fibras
            // activas y señalizar (synapse_esperar_fibras espera a 0 bajo la
            // misma cond).
            g_sched.num_fibras--;
            pthread_cond_broadcast(&g_sched_cond);
            pthread_mutex_unlock(&g_sched_mutex);
            // Terminó (fibra_terminar cedió el control): liberar pila y contexto.
#ifdef _WIN32
            DeleteFiber(f->context);
#else
            free(f->context);
#endif
            if (f->stack) free(f->stack);
            free(f);

            pthread_mutex_lock(&g_sched_mutex);
        } else {
            // La fibra se bloqueó en un canal: registrar el parqueo (F4.2) en
            // cola_espera del scheduler — la fibra ya está suspendida, así
            // que un waker puede moverla a cola_activa sin carrera.
            f->estado = F_ESTADO_PARQUEADA;
            f->next = NULL;
            if (g_sched.cola_espera_tail) {
                g_sched.cola_espera_tail->next = f;
            } else {
                g_sched.cola_espera = f;
            }
            g_sched.cola_espera_tail = f;
        }
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

// F4.2: parquea la fibra actual (se bloqueó en un canal) y cede al worker,
// que sigue ejecutando otras fibras. El PARQUEO lo registra el worker tras el
// yield (estado=PARQUEADA + cola_espera del scheduler, Manual 5 §2.6): la
// fibra solo es despertable cuando está REALMENTE suspendida — si el waker
// la re-encolara antes del yield, otro worker la re-ejecutaría mientras aún
// corre (carrera de doble ejecución). Si el waker completó la operación
// antes de que la fibra ceda (despertado), no se suspende.
static void _fibra_parquear(void) {
    Fibra* f = _fibra_actual;
    if (!f) return;

    pthread_mutex_lock(&g_sched_mutex);
    if (f->despertado) {
        // El waker ya completó la operación: no ceder el control.
        f->despertado = 0;
        pthread_mutex_unlock(&g_sched_mutex);
        return;
    }
    pthread_mutex_unlock(&g_sched_mutex);

#ifdef _WIN32
    SwitchToFiber(f->worker_fiber);
#else
    ucontext_t dummy;
    if (swapcontext(&dummy, (ucontext_t*)f->worker_fiber) != 0) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: swapcontext (parquear) fallo\n");
        exit(1);
    }
#endif
    // Reanudada por _scheduler_despertar_fibra (o por el worker que procesó
    // el despertado): la operación de canal está completa o el canal se cerró.
}

// Mueve la fibra de cola_espera a cola_activa. Requiere g_sched_mutex tomado.
static void _sched_mover_a_activa(Fibra* f) {
    if (g_sched.cola_espera == f) {
        g_sched.cola_espera = f->next;
        if (g_sched.cola_espera_tail == f) g_sched.cola_espera_tail = NULL;
    } else {
        Fibra* prev = g_sched.cola_espera;
        while (prev && prev->next != f) prev = prev->next;
        if (prev) {
            prev->next = f->next;
            if (g_sched.cola_espera_tail == f) g_sched.cola_espera_tail = prev;
        }
    }
    f->next = NULL;
    f->estado = F_ESTADO_CORRIENDO;
    if (g_sched.cola_activa_tail) {
        g_sched.cola_activa_tail->next = f;
    } else {
        g_sched.cola_activa = f;
    }
    g_sched.cola_activa_tail = f;
}

// F4.2: despierta una fibra parqueada — la mueve de cola_espera a cola_activa.
// estado==PARQUEADA solo lo fija el worker tras el yield de la fibra (la fibra
// está suspendida), así que moverla es seguro. Si la fibra aún no cede (o
// está cediendo), se marca despertado: o bien _fibra_parquear no se suspende,
// o el worker la re-encola al procesar el yield.
// Variante bajo mutex (F4.3): asume g_sched_mutex ya tomado — la usa
// fibra_terminar, que publica el resultado y despierta a los esperantes.
static void _sched_despertar_bajo_mutex(Fibra* f) {
    if (!g_sched.ejecutando) {
        // scheduler_detener con fibras parqueadas es un uso inválido
        // (documentado); la fibra no puede reanudarse.
        return;
    }
    if (f->estado == F_ESTADO_PARQUEADA) {
        _sched_mover_a_activa(f);
        pthread_cond_signal(&g_sched_cond);
    } else if (f->estado == F_ESTADO_CORRIENDO) {
        // Aún no se parquea (o está cediendo): notificar.
        f->despertado = 1;
    }
}

static void _scheduler_despertar_fibra(Fibra* f) {
    pthread_mutex_lock(&g_sched_mutex);
    _sched_despertar_bajo_mutex(f);
    pthread_mutex_unlock(&g_sched_mutex);
}

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
    f->estado = F_ESTADO_CORRIENDO;
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
    f->estado = F_ESTADO_TERMINADA;
    if (f->id >= 0 && f->id < FIBRAS_MAX) {
        g_resultados[f->id].resultado = resultado;
        g_resultados[f->id].terminada = 1;
        // F4.3: despertar a las fibras esperantes (fibra_esperar desde una
        // fibra) — el nodo se libera aqui; la esperante solo re-chequea la
        // tabla de resultados al reanudar.
        while (g_espera_id[f->id]) {
            _EsperaFibraId* n = g_espera_id[f->id];
            g_espera_id[f->id] = n->next;
            if (g_espera_id_tail[f->id] == n) g_espera_id_tail[f->id] = NULL;
            Fibra* w = n->fibra;
            free(n);
            _sched_despertar_bajo_mutex(w);
        }
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
    // Espera a que la fibra termine. Si la llama UNA FIBRA, se parquea
    // (F4.3, Manual 5 §2.6) en vez de bloquear a su worker con cond_wait:
    // fibra_terminar de la objetivo la despierta al publicar el resultado.
    // Si la llama un hilo OS, conserva el cond_wait (F4.1). Id inválido o
    // sin registro: retorna sin bloquear.
    Fibra* self = _fibra_actual;
    if (self) {
        pthread_mutex_lock(&g_sched_mutex);
        for (;;) {
            if (fibra_id < 0 || fibra_id >= FIBRAS_MAX || !g_resultados[fibra_id].activo) {
                break;   // no existe: retorna sin bloquear
            }
            if (g_resultados[fibra_id].terminada) {
                break;   // ya terminó
            }
            // Registrarse como esperante de la objetivo y parquear.
            _EsperaFibraId* n = (_EsperaFibraId*)malloc(sizeof(_EsperaFibraId));
            if (!n) {
                fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en fibra_esperar (fibra)\n");
                exit(1);
            }
            n->next = NULL;
            n->fibra = self;
            if (g_espera_id_tail[fibra_id]) {
                g_espera_id_tail[fibra_id]->next = n;
            } else {
                g_espera_id[fibra_id] = n;
            }
            g_espera_id_tail[fibra_id] = n;
            pthread_mutex_unlock(&g_sched_mutex);
            _fibra_parquear();
            pthread_mutex_lock(&g_sched_mutex);
            // Despertada por fibra_terminar de la objetivo: terminada==1.
        }
        pthread_mutex_unlock(&g_sched_mutex);
        return;
    }

    // Hilo OS: cond_wait (comportamiento F4.1).
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

// F4.4: espera a que TODAS las fibras del scheduler terminen (num_fibras == 0).
// El main del programa generado la llama tras principal() — los listeners de
// `escuchar` y las fibras de `lanzar` son fibras M:N (Manual 5 §2.6); el main
// debe esperarlas antes de pool_destroy/salir (paridad con synapse_esperar_hilos
// para los pthreads). Si el scheduler no se inició (0 fibras) retorna al
// instante.
void synapse_esperar_fibras(void) {
    pthread_mutex_lock(&g_sched_mutex);
    while (g_sched.num_fibras > 0) {
        pthread_cond_wait(&g_sched_cond, &g_sched_mutex);
    }
    pthread_mutex_unlock(&g_sched_mutex);
}

// ============================================================================
// Primitivas de sincronización (Manual 5 §5, F4.5)
// ============================================================================
// Bloqueo FIBER-AWARE (patrón F4.2 de los canales): si la operación no puede
// completarse y el llamador es una FIBRA (M:N, Manual 5 §2.6), esta se parquea
// en la cola de espera de la primitiva y cede al worker (que sigue con otras
// fibras); el waker transfiere el recurso marcando `satisfecho` (handoff). Si
// el llamador es un hilo OS (p.ej. `principal`), se usa cond_wait clásico.
// El guard pthread protege estado + cola; g_sched_mutex solo se toma tras el
// guard (orden fijo: primitiva → scheduler, sin ciclos de bloqueo).

// Encola la fibra actual en la cola de espera de la primitiva, libera el guard
// y cede al worker. Al reanudar, el waker completó la operación (satisfecho=1)
// — la fibra NO re-evalúa el estado ni re-intenta.
static void _sync_parquear(_EsperaFibra** cola, _EsperaFibra** cola_tail,
                           pthread_mutex_t* guard) {
    _EsperaFibra* n = (_EsperaFibra*)malloc(sizeof(_EsperaFibra));
    if (!n) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en primitiva de sync (parqueo)\n");
        exit(1);
    }
    n->next = NULL;
    n->fibra = _fibra_actual;
    n->dato = NULL;
    n->satisfecho = 0;
    if (*cola_tail) {
        (*cola_tail)->next = n;
    } else {
        *cola = n;
    }
    *cola_tail = n;
    pthread_mutex_unlock(guard);
    _fibra_parquear();
    free(n);
}

// --- Mutex (Manual 5 §5.1) ---
Mutex* mutex_crear(void) {
    Mutex* m = (Mutex*)malloc(sizeof(Mutex));
    if (!m) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en mutex_crear\n"); exit(1); }
    memset(m, 0, sizeof(Mutex));
    pthread_mutex_init(&m->mutex, NULL);
    pthread_cond_init(&m->cond, NULL);
    m->espera = NULL;
    m->espera_tail = NULL;
    return m;
}

void mutex_bloquear(Mutex* m) {
    pthread_mutex_lock(&m->mutex);
    if (!m->tomado && !m->espera) {
        // Libre y sin fibras en cola: adquisición directa (FIFO estricto).
        m->tomado = 1;
        pthread_mutex_unlock(&m->mutex);
        return;
    }
    if (_fibra_actual) {
        // F4.5: la fibra se parquea; el waker transfiere la propiedad.
        _sync_parquear(&m->espera, &m->espera_tail, &m->mutex);
        return;
    }
    while (m->tomado) {
        pthread_cond_wait(&m->cond, &m->mutex);
    }
    m->tomado = 1;
    pthread_mutex_unlock(&m->mutex);
}

void mutex_desbloquear(Mutex* m) {
    pthread_mutex_lock(&m->mutex);
    if (m->espera) {
        // Handoff: la propiedad pasa al primer esperante (FIFO) — tomado
        // permanece 1, la fibra despertada reanuda con el mutex tomado.
        _EsperaFibra* n = m->espera;
        m->espera = n->next;
        if (m->espera_tail == n) m->espera_tail = NULL;
        n->satisfecho = 1;
        _scheduler_despertar_fibra(n->fibra);
        pthread_mutex_unlock(&m->mutex);
        return;
    }
    m->tomado = 0;
    pthread_cond_signal(&m->cond);
    pthread_mutex_unlock(&m->mutex);
}

void mutex_destruir(Mutex* m) {
    if (!m) return;
    pthread_mutex_lock(&m->mutex);
    if (m->espera) {
        // Destrucción con fibras parqueadas: uso inválido (Manual 5 §5).
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: mutex_destruir con fibras esperando\n");
        exit(1);
    }
    pthread_mutex_unlock(&m->mutex);
    pthread_mutex_destroy(&m->mutex);
    pthread_cond_destroy(&m->cond);
    free(m);
}

// --- Semáforo (Manual 5 §5.2) ---
Semaforo* semaforo_crear(int valor) {
    Semaforo* s = (Semaforo*)malloc(sizeof(Semaforo));
    if (!s) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en semaforo_crear\n"); exit(1); }
    memset(s, 0, sizeof(Semaforo));
    s->valor = valor < 0 ? 0 : valor;
    pthread_mutex_init(&s->mutex, NULL);
    pthread_cond_init(&s->cond, NULL);
    s->espera = NULL;
    s->espera_tail = NULL;
    return s;
}

void semaforo_esperar(Semaforo* s) {
    pthread_mutex_lock(&s->mutex);
    if (s->valor > 0) {
        s->valor--;
        pthread_mutex_unlock(&s->mutex);
        return;
    }
    if (_fibra_actual) {
        // F4.5: la fibra se parquea; el waker (señalar) completa la operación
        // (handoff del permiso) — la fibra no re-decrementa al reanudar.
        _sync_parquear(&s->espera, &s->espera_tail, &s->mutex);
        return;
    }
    while (s->valor <= 0) {
        pthread_cond_wait(&s->cond, &s->mutex);
    }
    s->valor--;
    pthread_mutex_unlock(&s->mutex);
}

void semaforo_señalar(Semaforo* s) {
    pthread_mutex_lock(&s->mutex);
    if (s->espera) {
        // Handoff: entregar el permiso al primer esperante (FIFO).
        _EsperaFibra* n = s->espera;
        s->espera = n->next;
        if (s->espera_tail == n) s->espera_tail = NULL;
        n->satisfecho = 1;
        _scheduler_despertar_fibra(n->fibra);
        pthread_mutex_unlock(&s->mutex);
        return;
    }
    s->valor++;
    pthread_cond_signal(&s->cond);
    pthread_mutex_unlock(&s->mutex);
}

void semaforo_destruir(Semaforo* s) {
    if (!s) return;
    pthread_mutex_lock(&s->mutex);
    if (s->espera) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: semaforo_destruir con fibras esperando\n");
        exit(1);
    }
    pthread_mutex_unlock(&s->mutex);
    pthread_mutex_destroy(&s->mutex);
    pthread_cond_destroy(&s->cond);
    free(s);
}

// --- Barrera (Manual 5 §5.3) ---
Barrera* barrera_crear(int total) {
    Barrera* b = (Barrera*)malloc(sizeof(Barrera));
    if (!b) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en barrera_crear\n"); exit(1); }
    memset(b, 0, sizeof(Barrera));
    b->total = total < 1 ? 1 : total;
    b->esperando = 0;
    b->generacion = 0;
    pthread_mutex_init(&b->mutex, NULL);
    pthread_cond_init(&b->cond, NULL);
    b->espera = NULL;
    b->espera_tail = NULL;
    return b;
}

void barrera_esperar(Barrera* b) {
    pthread_mutex_lock(&b->mutex);
    int mi_gen = b->generacion;
    b->esperando++;
    if (b->esperando >= b->total) {
        // Última llegada de la ronda: reset + generación nueva + despertar a
        // todos (fibras parqueadas y hilos OS en cond).
        b->esperando = 0;
        b->generacion++;
        _EsperaFibra* n = b->espera;
        b->espera = NULL;
        b->espera_tail = NULL;
        pthread_cond_broadcast(&b->cond);
        pthread_mutex_unlock(&b->mutex);
        while (n) {
            _EsperaFibra* sig = n->next;
            n->satisfecho = 1;
            _scheduler_despertar_fibra(n->fibra);
            n = sig;
        }
        return;
    }
    if (_fibra_actual) {
        // F4.5: la fibra se parquea; la última llegada la despierta.
        _sync_parquear(&b->espera, &b->espera_tail, &b->mutex);
        return;
    }
    while (mi_gen == b->generacion) {
        pthread_cond_wait(&b->cond, &b->mutex);
    }
    pthread_mutex_unlock(&b->mutex);
}

void barrera_destruir(Barrera* b) {
    if (!b) return;
    pthread_mutex_lock(&b->mutex);
    if (b->espera) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: barrera_destruir con fibras esperando\n");
        exit(1);
    }
    pthread_mutex_unlock(&b->mutex);
    pthread_mutex_destroy(&b->mutex);
    pthread_cond_destroy(&b->cond);
    free(b);
}
