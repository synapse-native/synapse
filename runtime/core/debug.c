// runtime/core/debug.c — Debug/Trace module (M9.0-M9.4): time-travel debug
// (trace session base, deterministic recording, reversible breakpoints,
// memory snapshots & diff) + distributed multi-node debugging (M9.4).
// Extracted from synapse_rt.c (D-9(d) corte 5, patron cluster.c R40).
// Texto de las funciones BYTE-IDENTICO al original (CRLF preservado).
// El bloque NO era contiguo (partido por los marcadores del corte 4):
// los 3 tramos se concatenan en este archivo. FZ (M10.4) y los helpers de
// std.sistema permanecen en synapse_rt.c.
// Consumido por std.debug (externs Synapse, link-time).

#include "synapse_rt_types.h"
#include "runtime/core/debug.h"
#include "runtime/core/cluster.h"  // M9.4 usa cluster_canal_remoto_enviar (corte 4)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
#include <time.h>
#ifdef _WIN32
  #include <windows.h>
  #include <direct.h>
  #include <io.h>
  #include <fcntl.h>
#else
  #include <unistd.h>
  #include <sys/stat.h>
  #include <sys/time.h>
#endif

// ============================================================
// Debug / Trace System — Time-Travel Debugging Support
// ============================================================// (Tipos TraceEventTag/TraceEvent/TraceSession + TRACE_MAX_EVENTS/TRACE_DIR
//  movidos a runtime/core/debug.h en D-9(d) corte 5 — los usan los prototipos.)



static TraceSession g_trace_session = {0};
static int g_trace_initialized = 0;

long long _get_timestamp_ns(void) {
#ifdef _WIN32
    FILETIME ft;
    GetSystemTimeAsFileTime(&ft);
    ULARGE_INTEGER ul;
    ul.LowPart = ft.dwLowDateTime;
    ul.HighPart = ft.dwHighDateTime;
    return (long long)(ul.QuadPart / 10) - 116444736000000000LL;
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
#endif
}

static const char* _syn_home_dir(void) {
    const char* h = getenv("HOME");
#ifdef _WIN32
    if (h == NULL || h[0] == '\0') h = getenv("USERPROFILE");
#endif
    return (h != NULL && h[0] != '\0') ? h : ".";
}

static void _ensure_trace_dir(void) {
    // ME-R2: la traza se persiste en ~/.synapse/traces (API documentada en
    // std.debug y verificada por tests/unit/test_debug.py); antes se usaba
    // ".synapse/traces" relativo al CWD -> el archivo nunca aparecia en el
    // home del usuario y el test nunca encontraba el .trace.
    char buf[1024];
    const char* home = _syn_home_dir();
    snprintf(buf, sizeof(buf), "%s/.synapse", home);
#ifdef _WIN32
    _mkdir(buf);
#else
    mkdir(buf, 0755);
#endif
    snprintf(buf, sizeof(buf), "%s/%s", home, TRACE_DIR);
#ifdef _WIN32
    _mkdir(buf);
#else
    mkdir(buf, 0755);
#endif
}

static char* _generate_trace_id(void) {
    static char id[64];
    long long ts = _get_timestamp_ns();
    snprintf(id, sizeof(id), "trace_%lld_%d", ts, rand() % 10000);
    return id;
}

static void _init_trace_session(const char* programa) {
    if (g_trace_initialized) return;
    
    _ensure_trace_dir();
    
    g_trace_session.eventos = (TraceEvent*)calloc(TRACE_MAX_EVENTS, sizeof(TraceEvent));
    if (!g_trace_session.eventos) {
        fprintf(stderr, "[Debug] ERROR: No se pudo asignar buffer de traza\n");
        return;
    }
    g_trace_session.capacidad = TRACE_MAX_EVENTS;
    g_trace_session.cabeza = 0;
    g_trace_session.total_eventos = 0;
    g_trace_session.estado = 0;
    
    strncpy(g_trace_session.id, _generate_trace_id(), sizeof(g_trace_session.id)-1);
    strncpy(g_trace_session.programa, programa ? programa : "desconocido", sizeof(g_trace_session.programa)-1);
    
    g_trace_initialized = 1;
    fprintf(stderr, "[Debug] Sesion iniciada: %s (%s)\n", g_trace_session.id, g_trace_session.programa);
}

CadenaSegura _syn_debug_iniciar_sesion(CadenaSegura programa) {
    _init_trace_session(programa.datos ? programa.datos : "");
    
    CadenaSegura id;
    id.longitud = (int)strlen(g_trace_session.id);
    id.datos = g_trace_session.id;
    return id;
}

int _syn_debug_registrar_evento(int tag, const char* funcion, const char* archivo, int linea, 
                                 const char* variable, long long valor_entero, double valor_decimal, const char* valor_texto) {
    if (!g_trace_initialized) {
        _init_trace_session("desconocido");
    }
    if (!g_trace_session.eventos) return -1;
    
    int idx = g_trace_session.cabeza % TRACE_MAX_EVENTS;
    TraceEvent* e = &g_trace_session.eventos[idx];
    
    e->tag = tag;
    e->timestamp = _get_timestamp_ns();
    e->funcion = funcion ? funcion : "";
    e->archivo = archivo ? archivo : "";
    e->linea = linea;
    e->valor_entero = valor_entero;
    e->valor_decimal = valor_decimal;
    e->valor_texto = valor_texto ? valor_texto : "";
    e->variable = variable ? variable : "";
    
    g_trace_session.cabeza = (g_trace_session.cabeza + 1) % TRACE_MAX_EVENTS;
    if (g_trace_session.total_eventos < TRACE_MAX_EVENTS) {
        g_trace_session.total_eventos++;
    }
    
    return 0;
}

int _syn_debug_trace(const char* expresion_texto, void* valor, const char* tipo) {
    // Registrar evento de traza de usuario
    if (!g_trace_initialized) {
        _init_trace_session("desconocido");
    }
    return _syn_debug_registrar_evento(EVENT_USER_TRACE, "trace", "", 0, 
                                        expresion_texto ? expresion_texto : "expr", 
                                        0, 0.0, "");
}

CadenaSegura _syn_debug_finalizar_sesion(void) {
    if (!g_trace_initialized) {
        CadenaSegura vacia = {0, ""};
        return vacia;
    }
    
    if (g_trace_session.estado != 0) {
        CadenaSegura id = {(int)strlen(g_trace_session.id), g_trace_session.id};
        return id;
    }
    
    _ensure_trace_dir();
    
    char filepath[512];
    snprintf(filepath, sizeof(filepath), "%s/%s/%s.trace", _syn_home_dir(), TRACE_DIR, g_trace_session.id);
    
    FILE* f = fopen(filepath, "wb");
    if (!f) {
        fprintf(stderr, "[Debug] ERROR: No se pudo escribir traza: %s\n", filepath);
        CadenaSegura id = {(int)strlen(g_trace_session.id), g_trace_session.id};
        return id;
    }
    
    // Escribir header
    fprintf(f, "TRACE v1\n");
    fprintf(f, "id=%s\n", g_trace_session.id);
    fprintf(f, "programa=%s\n", g_trace_session.programa);
    fprintf(f, "eventos=%d\n", g_trace_session.total_eventos);
    fprintf(f, "capacidad=%d\n", TRACE_MAX_EVENTS);
    fprintf(f, "---\n");
    
    // Escribir eventos en orden cronologico (desde el mas antiguo)
    int inicio = (g_trace_session.total_eventos < TRACE_MAX_EVENTS) ? 0 : 
                 (g_trace_session.cabeza % TRACE_MAX_EVENTS);
    int count = g_trace_session.total_eventos;
    
    for (int i = 0; i < count; i++) {
        int idx = (inicio + i) % TRACE_MAX_EVENTS;
        TraceEvent* e = &g_trace_session.eventos[idx];
        
        fprintf(f, "%d|%lld|%s|%s|%d|%lld|%f|%s|%s\n",
            e->tag,
            e->timestamp,
            e->funcion,
            e->archivo,
            e->linea,
            e->valor_entero,
            e->valor_decimal,
            e->valor_texto ? e->valor_texto : "",
            e->variable ? e->variable : "");
    }
    
    fclose(f);
    
    g_trace_session.estado = 2;  // PERSISTIDA
    
    fprintf(stderr, "[Debug] Traza guardada: %s (%d eventos)\n", filepath, count);
    
    CadenaSegura id;
    id.longitud = (int)strlen(g_trace_session.id);
    id.datos = g_trace_session.id;
    return id;
}

TraceSession _syn_debug_obtener_sesion(void) {
    return g_trace_session;
}

// =========================================================================
// M9.1 — Deterministic Execution Recording (rr-style Time-Travel Debug)
// =========================================================================
// Integrates with existing M9.0 circular buffer. Adds sequential event
// numbering, snapshot mechanism, backward search, and replay simulation.
// =========================================================================

static int _tr_secuencia = 0;
static int _tr_initialized = 0;
static int _tr_ultimo_error_idx = -1;

static pthread_mutex_t _tr_mutex = PTHREAD_MUTEX_INITIALIZER;

// --- Initialize recording with sequence numbering ---
// Resets sequence counter and prepares the trace buffer for deterministic recording.
// Must be called after iniciar_sesion().
int tr_inicializar_recording(void) {
    if (!g_trace_initialized) {
        _init_trace_session("recording");
    }
    if (!g_trace_session.eventos) return -1;

    // Reset buffer for deterministic recording
    pthread_mutex_lock(&_tr_mutex);
    _tr_secuencia = 0;
    _tr_ultimo_error_idx = -1;
    _tr_initialized = 1;
    g_trace_session.total_eventos = 0;
    g_trace_session.cabeza = 0;
    pthread_mutex_unlock(&_tr_mutex);

    return 0;
}

// --- Helper: get next sequence number (thread-safe) ---
static int _tr_next_seq(void) {
    pthread_mutex_lock(&_tr_mutex);
    int s = _tr_secuencia++;
    pthread_mutex_unlock(&_tr_mutex);
    return s;
}

// --- Record a branch decision (which path was taken) ---
// linea: source line of the branch
// rama: 0 = false/else, 1 = true/if
// id_funcion: function name context
int tr_grabar_bifurcacion(int linea, int rama, CadenaSegura id_funcion) {
    if (!_tr_initialized) return -1;
    int seq = _tr_next_seq();
    int rc = _syn_debug_registrar_evento(
        EVENT_BRANCH_TAKEN,
        id_funcion.datos ? id_funcion.datos : "",
        "", linea,
        "branch",
        (long long)seq,
        (double)rama,
        rama ? "true" : "false");
    if (rc != 0) return -1;
    return seq;
}

// --- Record a variable snapshot at current execution point ---
// nombre_variable: name of the variable being snapshotted
// valor_entero: integer value (or 0 if using texto)
// valor_texto: string value (or empty if using entero)
// linea: source line number
int tr_grabar_snapshot(CadenaSegura nombre_variable, int valor_entero,
                       CadenaSegura valor_texto, int linea) {
    if (!_tr_initialized) return -1;
    int seq = _tr_next_seq();
    int rc = _syn_debug_registrar_evento(
        EVENT_VARIABLE_CHANGE,
        "", "", linea,
        nombre_variable.datos ? nombre_variable.datos : "",
        (long long)seq,
        (double)valor_entero,
        valor_texto.datos ? valor_texto.datos : "");
    if (rc != 0) return -1;
    return seq;
}

// --- Record a function call entry ---
// funcion: function name
// linea: source line of the call
// num_args: number of arguments passed
int tr_grabar_llamada(CadenaSegura funcion, int linea, int num_args) {
    if (!_tr_initialized) return -1;
    int seq = _tr_next_seq();
    int rc = _syn_debug_registrar_evento(
        EVENT_FN_CALL,
        funcion.datos ? funcion.datos : "",
        "", linea,
        "args",
        (long long)seq,
        (double)num_args,
        "");
    if (rc != 0) return -1;
    return seq;
}

// --- Record a function return ---
// funcion: function name
// linea: source line of the return
int tr_grabar_retorno(CadenaSegura funcion, int linea) {
    if (!_tr_initialized) return -1;
    int seq = _tr_next_seq();
    int rc = _syn_debug_registrar_evento(
        EVENT_FN_RETURN,
        funcion.datos ? funcion.datos : "",
        "", linea,
        "return",
        (long long)seq,
        0.0, "");
    if (rc != 0) return -1;
    return seq;
}

// --- Record an error event (for fault induction testing) ---
// mensaje: description of the error
// linea: source line where the error occurred
int tr_grabar_error(CadenaSegura mensaje, int linea) {
    if (!_tr_initialized) return -1;
    int seq = _tr_next_seq();
    int idx = g_trace_session.cabeza > 0 ? g_trace_session.cabeza - 1 : 0;
    _tr_ultimo_error_idx = idx;
    int rc = _syn_debug_registrar_evento(
        EVENT_ERROR,
        "", "", linea,
        "error",
        (long long)seq,
        0.0,
        mensaje.datos ? mensaje.datos : "unknown_error");
    if (rc != 0) return -1;
    return seq;
}

// --- Search backwards through recorded events for a specific tag ---
// Returns sequence number of the found event, or -1 if not found.
// Starts from the most recent event and searches backwards.
int tr_buscar_evento(int tag, int desde_secuencia) {
    if (!_tr_initialized || !g_trace_session.eventos) return -1;

    int total = g_trace_session.total_eventos;
    if (total <= 0) return -1;

    int inicio = (g_trace_session.total_eventos < TRACE_MAX_EVENTS) ? 0 :
                 (g_trace_session.cabeza % TRACE_MAX_EVENTS);

    // Search backwards from the end
    for (int i = total - 1; i >= 0; i--) {
        int idx = (inicio + i) % TRACE_MAX_EVENTS;
        TraceEvent* e = &g_trace_session.eventos[idx];
        if (e->tag == tag) {
            // Found an event with matching tag
            // If desde_secuencia >= 0, only return if seq <= desde_secuencia
            long long ev_seq = e->valor_entero;
            if (desde_secuencia < 0 || ev_seq <= (long long)desde_secuencia) {
                return (int)ev_seq;
            }
        }
    }
    return -1;
}

// --- Get recorded event at index as string for inspection ---
// Returns "tag|seq|funcion|linea|variable|valor" or empty if not found
CadenaSegura tr_obtener_evento(int indice) {
    if (!_tr_initialized || !g_trace_session.eventos) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    int total = g_trace_session.total_eventos;
    if (indice < 0 || indice >= total) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    int inicio = (total < TRACE_MAX_EVENTS) ? 0 :
                 (g_trace_session.cabeza % TRACE_MAX_EVENTS);
    int idx = (inicio + indice) % TRACE_MAX_EVENTS;
    TraceEvent* e = &g_trace_session.eventos[idx];

    char buf[256];
    int len = snprintf(buf, sizeof(buf), "%d|%lld|%s|%d|%s|%lld",
                       e->tag, e->valor_entero,
                       e->funcion ? e->funcion : "",
                       e->linea,
                       e->variable ? e->variable : "",
                       (long long)e->valor_decimal);

    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(result, buf, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = len, .datos = result };
}

// --- Simulate replay up to a target event sequence number ---
// In a full rr implementation this would re-execute the program.
// Here, we validate that events exist up to the target seq and return
// the count of events that would be replayed.
int tr_reproducir_hasta(int secuencia_objetivo) {
    if (!_tr_initialized || !g_trace_session.eventos) return -1;
    if (secuencia_objetivo < 0) return -1;

    int total = g_trace_session.total_eventos;
    int inicio = (total < TRACE_MAX_EVENTS) ? 0 :
                 (g_trace_session.cabeza % TRACE_MAX_EVENTS);

    int replayed = 0;
    for (int i = 0; i < total; i++) {
        int idx = (inicio + i) % TRACE_MAX_EVENTS;
        TraceEvent* e = &g_trace_session.eventos[idx];
        if (e->valor_entero <= (long long)secuencia_objetivo) {
            replayed++;
        } else {
            break;
        }
    }
    return replayed;
}

// --- Get the sequence number of the last error event ---
// Returns sequence number, or -1 if no error recorded
int tr_indice_ultimo_error(void) {
    if (!_tr_initialized) return -1;
    return _tr_ultimo_error_idx;
}

// --- Get total number of recorded events (sequence count) ---
int tr_total_eventos(void) {
    if (!_tr_initialized) return 0;
    return _tr_secuencia;
}

// =========================================================================
// M9.2 — Reversible Breakpoints & Historical Snapshot Inspection
// =========================================================================
// Engine for reverse execution replay: set breakpoints on line/variable/tag,
// step backwards through the event trace, inspect call stacks and variable
// values at any recorded point, and jump to the event just before a fault.
// =========================================================================

#define RP_MAX_BREAKPOINTS 16
#define RP_POR_LINEA    0
#define RP_POR_VARIABLE 1
#define RP_POR_TAG      2

typedef struct {
    int activo;
    int tipo;     // 0=linea, 1=variable, 2=tag
    char patron[64];
    int valor_int;
} RpBreakpoint;

static RpBreakpoint _rp_breakpoints[RP_MAX_BREAKPOINTS];
static int _rp_total_bps = 0;
static int _rp_posicion = -1;  // current replay cursor (event index)
static int _rp_initialized = 0;

// --- Helper: get event at logical index (handles circular buffer) ---
static TraceEvent* _rp_get_event(int indice_logico) {
    if (!g_trace_session.eventos) return NULL;
    int total = g_trace_session.total_eventos;
    if (indice_logico < 0 || indice_logico >= total) return NULL;
    int inicio = (total < TRACE_MAX_EVENTS) ? 0 :
                 (g_trace_session.cabeza % TRACE_MAX_EVENTS);
    int idx = (inicio + indice_logico) % TRACE_MAX_EVENTS;
    return &g_trace_session.eventos[idx];
}

// --- Initialize the reversible debug engine ---
int rp_inicializar(void) {
    for (int i = 0; i < RP_MAX_BREAKPOINTS; i++) {
        _rp_breakpoints[i].activo = 0;
    }
    _rp_total_bps = 0;
    _rp_posicion = -1;
    _rp_initialized = 1;
    return 0;
}

// --- Set a reversible breakpoint ---
// tipo: 0=linea, 1=variable, 2=tag
// patron: line number as string for linea, variable name for variable, tag name for tag
// valor_int: for tipo=2 the tag integer, for tipo=0 the line number, for tipo=1 ignored
// Returns breakpoint ID (0-based), or -1 if full
int rp_establecer_breakpoint(int tipo, CadenaSegura patron, int valor_int) {
    if (!_rp_initialized) return -1;
    if (_rp_total_bps >= RP_MAX_BREAKPOINTS) return -1;
    if (tipo < 0 || tipo > 2) return -1;

    int id = _rp_total_bps;
    _rp_breakpoints[id].activo = 1;
    _rp_breakpoints[id].tipo = tipo;
    _rp_breakpoints[id].valor_int = valor_int;
    if (patron.datos) {
        int plen = patron.longitud < 63 ? patron.longitud : 63;
        memcpy(_rp_breakpoints[id].patron, patron.datos, (size_t)plen);
        _rp_breakpoints[id].patron[plen] = '\0';
    } else {
        _rp_breakpoints[id].patron[0] = '\0';
    }
    _rp_total_bps++;
    return id;
}

// --- Remove a breakpoint by ID ---
int rp_eliminar_breakpoint(int id) {
    if (!_rp_initialized) return -1;
    if (id < 0 || id >= _rp_total_bps) return -1;
    _rp_breakpoints[id].activo = 0;
    // Compact: shift remaining breakpoints down
    for (int i = id; i < _rp_total_bps - 1; i++) {
        _rp_breakpoints[i] = _rp_breakpoints[i + 1];
    }
    _rp_total_bps--;
    return 0;
}

// --- Clear all breakpoints ---
int rp_limpiar_breakpoints(void) {
    if (!_rp_initialized) return -1;
    for (int i = 0; i < RP_MAX_BREAKPOINTS; i++) {
        _rp_breakpoints[i].activo = 0;
    }
    _rp_total_bps = 0;
    return 0;
}

// --- Find event index matching a breakpoint, searching backwards ---
// Returns logical event index, or -1 if not found
int rp_buscar_breakpoint(int id) {
    if (!_rp_initialized || !g_trace_session.eventos) return -1;
    if (id < 0 || id >= _rp_total_bps) return -1;
    if (!_rp_breakpoints[id].activo) return -1;

    int total = g_trace_session.total_eventos;
    if (total <= 0) return -1;

    RpBreakpoint* bp = &_rp_breakpoints[id];

    // Search backwards from end
    for (int i = total - 1; i >= 0; i--) {
        TraceEvent* e = _rp_get_event(i);
        if (!e) continue;

        int match = 0;
        switch (bp->tipo) {
            case RP_POR_LINEA:
                match = (e->linea == bp->valor_int);
                break;
            case RP_POR_VARIABLE:
                match = (e->variable && bp->patron[0] &&
                         strcmp(e->variable, bp->patron) == 0);
                break;
            case RP_POR_TAG:
                match = (e->tag == bp->valor_int);
                break;
        }
        if (match) return i;
    }
    return -1;
}

// --- Step backwards N events from a given position ---
// Returns the new position (event index), or -1 if at start
int rp_retroceder(int pasos, int desde_evento) {
    if (!_rp_initialized) return -1;
    int total = g_trace_session.total_eventos;
    if (total <= 0) return -1;

    int inicio = desde_evento >= 0 ? desde_evento : (total - 1);
    if (inicio >= total) inicio = total - 1;
    if (pasos <= 0) {
        _rp_posicion = inicio;
        return _rp_posicion;
    }

    int nueva_pos = inicio - pasos;
    if (nueva_pos < 0) nueva_pos = -1;

    _rp_posicion = nueva_pos;
    return _rp_posicion;
}

// --- Get the current replay cursor position ---
int rp_posicion_actual(void) {
    if (!_rp_initialized) return -1;
    return _rp_posicion;
}

// --- Jump to the event index just before the last error ---
// Returns the event index of the last non-error event before the error, or -1
int rp_ir_a_pre_error(void) {
    if (!_rp_initialized || !g_trace_session.eventos) return -1;
    int total = g_trace_session.total_eventos;
    if (total <= 0) return -1;

    // Find the last ERROR event
    int error_idx = -1;
    for (int i = total - 1; i >= 0; i--) {
        TraceEvent* e = _rp_get_event(i);
        if (e && e->tag == EVENT_ERROR) {
            error_idx = i;
            break;
        }
    }
    if (error_idx < 0) return -1;

    // Return event just before the error
    int pre = error_idx - 1;
    if (pre < 0) return -1;

    _rp_posicion = pre;
    return pre;
}

// --- Inspect a variable's value at a specific event index ---
// Searches backwards from indice_evento (inclusive) for the most recent
// occurrence of the named variable. Returns "entero:<val>" or "texto:<val>",
// or empty CadenaSegura if the variable was never recorded.
CadenaSegura rp_inspeccionar_variable(int indice_evento, CadenaSegura nombre) {
    if (!_rp_initialized || !g_trace_session.eventos) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    if (!nombre.datos || nombre.longitud <= 0) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    int total = g_trace_session.total_eventos;
    if (indice_evento < 0 || indice_evento >= total) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    // Search backwards from indice_evento for the named variable
    for (int i = indice_evento; i >= 0; i--) {
        TraceEvent* e = _rp_get_event(i);
        if (!e) continue;
        if ((e->tag == EVENT_VARIABLE_CHANGE || e->tag == EVENT_ASSIGNMENT)
            && e->variable && strcmp(e->variable, nombre.datos) == 0) {
            // Found the most recent occurrence
            char buf[64];
            int len = 0;
            if (e->valor_texto && strlen(e->valor_texto) > 0) {
                len = snprintf(buf, sizeof(buf), "texto:%s", e->valor_texto);
            } else {
                len = snprintf(buf, sizeof(buf), "entero:%lld", (long long)e->valor_decimal);
            }
            char* result = (char*)pool_alloc((size_t)(len + 1));
            if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
            memcpy(result, buf, (size_t)(len + 1));
            return (CadenaSegura){ .longitud = len, .datos = result };
        }
    }
    return (CadenaSegura){ .longitud = 0, .datos = NULL };
}

// --- Build call stack string at a specific event index ---
// Returns "funcion:linea|funcion:linea|..." (innermost first), or empty
CadenaSegura rp_pila_llamadas(int indice_evento) {
    if (!_rp_initialized || !g_trace_session.eventos) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    int total = g_trace_session.total_eventos;
    if (indice_evento < 0 || indice_evento >= total) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    // Walk backwards from indice_evento, tracking call/return pairs
    // Use a simple stack: push on EVENT_FN_CALL, pop on EVENT_FN_RETURN
    char stack_buf[1024];
    int stack_len = 0;
    int depth = 0;
    // Track unmatched calls
    int call_lineas[64];
    const char* call_funcs[64];

    for (int i = indice_evento; i >= 0; i--) {
        TraceEvent* e = _rp_get_event(i);
        if (!e) break;

        if (e->tag == EVENT_FN_RETURN) {
            depth++;
        } else if (e->tag == EVENT_FN_CALL) {
            if (depth > 0) {
                depth--;  // matched a return
            } else {
                // Unmatched call: add to stack
                int idx = stack_len / 2; // placeholder
                (void)idx;
                // Build "funcion:linea|" segment
                const char* fname = e->funcion ? e->funcion : "?";
                int seg_len = snprintf(stack_buf + stack_len,
                                       sizeof(stack_buf) - (size_t)stack_len,
                                       "%s:%d|", fname, e->linea);
                if (seg_len > 0 && stack_len + seg_len < (int)sizeof(stack_buf)) {
                    stack_len += seg_len;
                }
            }
        }
    }

    // Remove trailing '|'
    if (stack_len > 0 && stack_buf[stack_len - 1] == '|') {
        stack_len--;
    }

    if (stack_len <= 0) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    char* result = (char*)pool_alloc((size_t)(stack_len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(result, stack_buf, (size_t)(stack_len + 1));
    return (CadenaSegura){ .longitud = stack_len, .datos = result };
}

// --- Search backwards for a variable change to a specific value ---
// Returns event index, or -1 if not found
int rp_buscar_cambio_variable(CadenaSegura nombre, int valor) {
    if (!_rp_initialized || !g_trace_session.eventos) return -1;
    if (!nombre.datos || nombre.longitud <= 0) return -1;

    int total = g_trace_session.total_eventos;
    if (total <= 0) return -1;

    for (int i = total - 1; i >= 0; i--) {
        TraceEvent* e = _rp_get_event(i);
        if (!e) continue;
        if ((e->tag == EVENT_VARIABLE_CHANGE || e->tag == EVENT_ASSIGNMENT)
            && e->variable && strcmp(e->variable, nombre.datos) == 0
            && (int)e->valor_decimal == valor) {
            return i;
        }
    }
    return -1;
}

// =========================================================================
// M9.3 — Memory Snapshots & Historical State Diff
// =========================================================================
// Engine for capturing compressed variable-state snapshots from the event
// trace and computing structural diffs between two execution points.
//
// Snapshot format (newline-separated entries):
//     var1|entero|42
//     var2|texto|hello
//
// Diff format (prefix identifies change type):
//     +name|tipo|val          — added in B
//     -name|tipo|val          — removed in B
//     ~name|tipo_a|val_a|tipo_b|val_b  — changed
// =========================================================================

#define MS_MAX_VARS 256
#define MS_LINE_MAX 128

// --- Helper: find event index for a given sequence number ---
// Seq numbers are assigned monotonically by _tr_next_seq. Since events
// are stored consecutively (1:1 with seq), we derive index = seq - 1.
// Returns -1 if out of range.
static int _ms_seq_a_indice(int seq) {
    if (!g_trace_session.eventos) return -1;
    int total = g_trace_session.total_eventos;
    if (total <= 0 || seq < 1) return -1;
    int idx = seq - 1;
    if (idx >= total) idx = total - 1;  // clamp to last event
    return idx;
}

// --- Helper: append one line to a snapshot buffer ---
static int _ms_append_line(char* buf, int offset, int cap,
                           const char* name, const char* tipo,
                           const char* valor) {
    if (!name) name = "?";
    if (!tipo) tipo = "?";
    if (!valor) valor = "";
    int needed = snprintf(buf + offset, (size_t)(cap - offset),
                          "%s|%s|%s\n", name, tipo, valor);
    if (needed < 0) return offset;
    if (offset + needed >= cap) return offset;
    return offset + needed;
}

// --- Helper: parse a snapshot line into name / tipo / valor ---
// Returns 1 if parsed OK, 0 on error
static int _ms_parse_line(const char* line, int line_len,
                          char* name_out, int name_cap,
                          char* tipo_out, int tipo_cap,
                          char* val_out, int val_cap) {
    if (!line || line_len <= 0) return 0;
    const char* p1 = strchr(line, '|');
    if (!p1 || p1 >= line + line_len) return 0;
    int name_len = (int)(p1 - line);
    if (name_len >= name_cap) name_len = name_cap - 1;
    memcpy(name_out, line, (size_t)name_len);
    name_out[name_len] = '\0';

    const char* p2 = strchr(p1 + 1, '|');
    if (!p2 || p2 >= line + line_len) return 0;
    int tipo_len = (int)(p2 - (p1 + 1));
    if (tipo_len >= tipo_cap) tipo_len = tipo_cap - 1;
    memcpy(tipo_out, p1 + 1, (size_t)tipo_len);
    tipo_out[tipo_len] = '\0';

    int val_len = line_len - (int)(p2 + 1 - line);
    if (val_len >= val_cap) val_len = val_cap - 1;
    memcpy(val_out, p2 + 1, (size_t)val_len);
    val_out[val_len] = '\0';
    return 1;
}

// --- Capture a compressed variable-state snapshot at a given sequence ---
// Walks backward from the event matching seq, collecting the most recent
// value of each unique variable.
// Returns serialized snapshot string, or empty CadenaSegura on error.
CadenaSegura ms_tomar_en(int secuencia) {
    if (!g_trace_session.eventos) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    int idx = _ms_seq_a_indice(secuencia);
    if (idx < 0) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    char names[MS_MAX_VARS][64];
    char tipos[MS_MAX_VARS][16];
    char vals[MS_MAX_VARS][64];
    int nvars = 0;

    for (int i = idx; i >= 0 && nvars < MS_MAX_VARS; i--) {
        TraceEvent* e = _rp_get_event(i);
        if (!e) continue;
        if (e->tag != EVENT_VARIABLE_CHANGE && e->tag != EVENT_ASSIGNMENT) continue;
        if (!e->variable || strlen(e->variable) == 0) continue;

        int found = 0;
        for (int j = 0; j < nvars; j++) {
            if (strcmp(names[j], e->variable) == 0) { found = 1; break; }
        }
        if (found) continue;

        int nlen = (int)strlen(e->variable);
        if (nlen >= 64) nlen = 63;
        memcpy(names[nvars], e->variable, (size_t)nlen);
        names[nvars][nlen] = '\0';

        if (e->valor_texto && strlen(e->valor_texto) > 0) {
            memcpy(tipos[nvars], "texto", 6);
            int vlen = (int)strlen(e->valor_texto);
            if (vlen >= 64) vlen = 63;
            memcpy(vals[nvars], e->valor_texto, (size_t)vlen);
            vals[nvars][vlen] = '\0';
        } else {
            memcpy(tipos[nvars], "entero", 7);
            snprintf(vals[nvars], 64, "%lld", (long long)e->valor_decimal);
        }
        nvars++;
    }

    int cap = nvars * 128 + 16;
    char* buf = (char*)pool_alloc((size_t)cap);
    if (!buf) return (CadenaSegura){ .longitud = 0, .datos = NULL };

    int pos = 0;
    for (int i = nvars - 1; i >= 0; i--) {
        pos = _ms_append_line(buf, pos, cap, names[i], tipos[i], vals[i]);
    }

    return (CadenaSegura){ .longitud = pos, .datos = buf };
}

// --- Compare two snapshots and produce a structural diff ---
// Returns diff string, or empty on error.
CadenaSegura ms_diferenciar(CadenaSegura snap_a, CadenaSegura snap_b) {
    if (!snap_a.datos || snap_a.longitud <= 0) return snap_b;
    if (!snap_b.datos || snap_b.longitud <= 0) return snap_a;

    char a_names[MS_MAX_VARS][64];
    char a_tipos[MS_MAX_VARS][16];
    char a_vals[MS_MAX_VARS][64];
    int na = 0;

    const char* p = snap_a.datos;
    const char* end = snap_a.datos + snap_a.longitud;
    while (p < end && na < MS_MAX_VARS) {
        const char* nl = strchr(p, '\n');
        int line_len = nl ? (int)(nl - p) : (int)(end - p);
        if (line_len > 0) {
            _ms_parse_line(p, line_len,
                          a_names[na], 64, a_tipos[na], 16, a_vals[na], 64);
            if (strlen(a_names[na]) > 0) na++;
        }
        p = nl ? nl + 1 : end;
    }

    char b_names[MS_MAX_VARS][64];
    char b_tipos[MS_MAX_VARS][16];
    char b_vals[MS_MAX_VARS][64];
    int nb = 0;

    p = snap_b.datos;
    end = snap_b.datos + snap_b.longitud;
    while (p < end && nb < MS_MAX_VARS) {
        const char* nl = strchr(p, '\n');
        int line_len = nl ? (int)(nl - p) : (int)(end - p);
        if (line_len > 0) {
            _ms_parse_line(p, line_len,
                          b_names[nb], 64, b_tipos[nb], 16, b_vals[nb], 64);
            if (strlen(b_names[nb]) > 0) nb++;
        }
        p = nl ? nl + 1 : end;
    }

    int cap = (na + nb + na) * 128 + 16;
    char* buf = (char*)pool_alloc((size_t)cap);
    if (!buf) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    int pos = 0;

    for (int i = 0; i < na; i++) {
        int found_in_b = 0;
        for (int j = 0; j < nb; j++) {
            if (strcmp(a_names[i], b_names[j]) == 0) {
                found_in_b = 1;
                if (strcmp(a_tipos[i], b_tipos[j]) != 0 ||
                    strcmp(a_vals[i], b_vals[j]) != 0) {
                    pos += snprintf(buf + pos, (size_t)(cap - pos),
                                    "~%s|%s|%s|%s|%s\n",
                                    a_names[i], a_tipos[i], a_vals[i],
                                    b_tipos[j], b_vals[j]);
                }
                break;
            }
        }
        if (!found_in_b) {
            pos += snprintf(buf + pos, (size_t)(cap - pos),
                            "-%s|%s|%s\n", a_names[i], a_tipos[i], a_vals[i]);
        }
    }

    for (int j = 0; j < nb; j++) {
        int found_in_a = 0;
        for (int i = 0; i < na; i++) {
            if (strcmp(b_names[j], a_names[i]) == 0) { found_in_a = 1; break; }
        }
        if (!found_in_a) {
            pos += snprintf(buf + pos, (size_t)(cap - pos),
                            "+%s|%s|%s\n", b_names[j], b_tipos[j], b_vals[j]);
        }
    }

    if (pos > 0 && buf[pos - 1] == '\n') pos--;
    return (CadenaSegura){ .longitud = pos, .datos = buf };
}

// --- Convenience: diff between two sequence numbers ---
CadenaSegura ms_diff_entre(int seq_a, int seq_b) {
    if (seq_a == seq_b) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    CadenaSegura snap_a = ms_tomar_en(seq_a);
    CadenaSegura snap_b = ms_tomar_en(seq_b);
    if (!snap_a.datos && !snap_b.datos) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    return ms_diferenciar(snap_a, snap_b);
}

// --- Count variables in a snapshot ---
int ms_snapshot_contar_vars(CadenaSegura snapshot) {
    if (!snapshot.datos || snapshot.longitud <= 0) return 0;
    int count = 0;
    const char* p = snapshot.datos;
    const char* end = snapshot.datos + snapshot.longitud;
    while (p < end) {
        const char* nl = strchr(p, '\n');
        if (nl) { if (nl > p) count++; p = nl + 1; }
        else { if (end > p) count++; break; }
    }
    return count;
}

// --- Get byte size of a snapshot string ---
int ms_snapshot_tamano(CadenaSegura snapshot) {
    if (!snapshot.datos) return 0;
    return snapshot.longitud;
}

// --- Check if a variable exists in a snapshot ---
// Returns "tipo:valor" or empty CadenaSegura
CadenaSegura ms_snapshot_contiene(CadenaSegura snapshot, CadenaSegura nombre) {
    if (!snapshot.datos || snapshot.longitud <= 0 ||
        !nombre.datos || nombre.longitud <= 0) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    const char* p = snapshot.datos;
    const char* end = snapshot.datos + snapshot.longitud;
    while (p < end) {
        const char* nl = strchr(p, '\n');
        int line_len = nl ? (int)(nl - p) : (int)(end - p);
        if (line_len > 0) {
            char nb[64], tb[16], vb[64];
            if (_ms_parse_line(p, line_len, nb, 64, tb, 16, vb, 64)) {
                if (strcmp(nb, nombre.datos) == 0) {
                    char result_buf[128];
                    int rlen = snprintf(result_buf, sizeof(result_buf), "%s:%s", tb, vb);
                    if (rlen < 0) return (CadenaSegura){ .longitud = 0, .datos = NULL };
                    char* result = (char*)pool_alloc((size_t)(rlen + 1));
                    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
                    memcpy(result, result_buf, (size_t)(rlen + 1));
                    return (CadenaSegura){ .longitud = rlen, .datos = result };
                }
            }
        }
        p = nl ? nl + 1 : end;
    }
    return (CadenaSegura){ .longitud = 0, .datos = NULL };
}

// ============================================================
// M9.4 — Distributed Multi-Node Debugging
// ============================================================
// Extiende tr_* / rp_* / ms_* para operación en clúster.
// Permite agregación remota de trazas, breakpoints distribuidos
// y correlación cronológica entre nodos del clúster M8.x.
// ============================================================

#define DD_MAX_REMOTE_NODES 16
#define DD_MAX_REMOTE_EVENTS 2048
#define DD_PROTO_MAGIC "SYNDBG"

typedef struct {
    int nodo_id;
    char ip[48];
    int puerto;
    int num_eventos;
    int ultima_sincro_s;
    char eventos[DD_MAX_REMOTE_EVENTS][256]; // serialized event strings
    int activo;
} NodoRemotoDebug;

static int _dd_local_nodo_id = -1;
static int _dd_inicializado = 0;
static int _dd_total_remotos = 0;
static int _dd_ultima_sincro = 0;
static NodoRemotoDebug _dd_nodos_remotos[DD_MAX_REMOTE_NODES];
static pthread_mutex_t _dd_mutex = PTHREAD_MUTEX_INITIALIZER;

// --- Inicializar subsistema de debug distribuido ---
// nodo_id: identificador único de este nodo en el clúster
int dd_inicializar(int nodo_id) {
    pthread_mutex_lock(&_dd_mutex);
    _dd_local_nodo_id = nodo_id;
    _dd_inicializado = 1;
    _dd_total_remotos = 0;
    _dd_ultima_sincro = (int)time(NULL);
    memset(_dd_nodos_remotos, 0, sizeof(_dd_nodos_remotos));
    pthread_mutex_unlock(&_dd_mutex);
    return 0;
}

// --- Registrar un nodo remoto para debug distribuido ---
int dd_registrar_nodo_remoto(int nodo_id, CadenaSegura ip, int puerto) {
    if (!_dd_inicializado || !ip.datos || puerto <= 0) return -1;

    pthread_mutex_lock(&_dd_mutex);

    // Check if already registered
    for (int i = 0; i < _dd_total_remotos; i++) {
        if (_dd_nodos_remotos[i].nodo_id == nodo_id) {
            // Update IP/port
            strncpy(_dd_nodos_remotos[i].ip, ip.datos, sizeof(_dd_nodos_remotos[i].ip) - 1);
            _dd_nodos_remotos[i].puerto = puerto;
            _dd_nodos_remotos[i].activo = 1;
            _dd_nodos_remotos[i].ultima_sincro_s = (int)time(NULL);
            pthread_mutex_unlock(&_dd_mutex);
            return i;
        }
    }

    if (_dd_total_remotos >= DD_MAX_REMOTE_NODES) {
        pthread_mutex_unlock(&_dd_mutex);
        return -2;
    }

    int idx = _dd_total_remotos++;
    _dd_nodos_remotos[idx].nodo_id = nodo_id;
    strncpy(_dd_nodos_remotos[idx].ip, ip.datos, sizeof(_dd_nodos_remotos[idx].ip) - 1);
    _dd_nodos_remotos[idx].ip[sizeof(_dd_nodos_remotos[idx].ip) - 1] = '\0';
    _dd_nodos_remotos[idx].puerto = puerto;
    _dd_nodos_remotos[idx].num_eventos = 0;
    _dd_nodos_remotos[idx].activo = 1;
    _dd_nodos_remotos[idx].ultima_sincro_s = (int)time(NULL);

    pthread_mutex_unlock(&_dd_mutex);
    return idx;
}

// --- Serializar y enviar traza local a nodo remoto ---
// Envía los últimos num_eventos eventos de la traza local al nodo remoto
// Formato: "SYNDBG:TRACE:origen_id:num_eventos:evt1|evt2|..."
int dd_enviar_traza_remota(CadenaSegura ip, int puerto, int num_eventos) {
    if (!_dd_inicializado || !ip.datos || puerto <= 0) return -1;
    if (num_eventos <= 0) num_eventos = tr_total_eventos();
    if (num_eventos > 100) num_eventos = 100; // limit payload size

    // Build trace payload from local tr_* events
    char buf[4096];
    int pos = snprintf(buf, sizeof(buf), "%s:TRACE:%d:%d:",
                       DD_PROTO_MAGIC, _dd_local_nodo_id, num_eventos);

    for (int i = 0; i < num_eventos && pos < (int)sizeof(buf) - 100; i++) {
        int idx = tr_total_eventos() - num_eventos + i;
        if (idx < 0) continue;
        CadenaSegura evt = tr_obtener_evento(idx);
        if (evt.datos && evt.longitud > 0) {
            int n = snprintf(buf + pos, (size_t)(sizeof(buf) - pos),
                             "%s|", evt.datos);
            if (n > 0) pos += n;
        }
    }

    // Send via cluster remote channel
    int rc = cluster_canal_remoto_enviar(ip.datos, puerto, buf, pos, 0);
    return (rc >= 0) ? 0 : -2;
}

// --- Recibir y procesar traza remota ---
// Procesa un paquete SYNDBG:TRACE entrante y lo almacena en el buffer
// de eventos remotos del nodo correspondiente.
// Retorna 0 si se procesó, -1 si no es un paquete debug válido
int dd_recibir_traza_remota(CadenaSegura paquete) {
    if (!_dd_inicializado || !paquete.datos || paquete.longitud <= 0) return -1;

    // Verify magic prefix
    if (strncmp(paquete.datos, DD_PROTO_MAGIC, strlen(DD_PROTO_MAGIC)) != 0)
        return -2;

    // Parse: SYNDBG:TRACE:origen_id:num_eventos:evt1|evt2|...
    const char* p = paquete.datos + strlen(DD_PROTO_MAGIC) + 1;

    // Expect TRACE command
    if (strncmp(p, "TRACE", 5) != 0) return -3;
    p += 6; // skip "TRACE:"

    // Parse origin node ID
    int origen_id = 0;
    while (*p && *p != ':') { origen_id = origen_id * 10 + (*p - '0'); p++; }
    if (!*p) return -4;
    p++; // skip ':'

    // Parse num events
    int num_evt = 0;
    while (*p && *p != ':') { num_evt = num_evt * 10 + (*p - '0'); p++; }
    if (!*p) return -5;
    p++; // skip ':'

    // Find remote node entry or create it
    pthread_mutex_lock(&_dd_mutex);
    int idx = -1;
    for (int i = 0; i < _dd_total_remotos; i++) {
        if (_dd_nodos_remotos[i].nodo_id == origen_id) {
            idx = i;
            break;
        }
    }
    if (idx < 0 && _dd_total_remotos < DD_MAX_REMOTE_NODES) {
        idx = _dd_total_remotos++;
        _dd_nodos_remotos[idx].nodo_id = origen_id;
        strncpy(_dd_nodos_remotos[idx].ip, "", 1);
        _dd_nodos_remotos[idx].puerto = 0;
        _dd_nodos_remotos[idx].num_eventos = 0;
        _dd_nodos_remotos[idx].activo = 1;
    }

    if (idx < 0) {
        pthread_mutex_unlock(&_dd_mutex);
        return -6;
    }

    // Parse event strings into buffer
    int evt_idx = 0;
    const char* evt_start = p;
    while (*p && evt_idx < DD_MAX_REMOTE_EVENTS && evt_idx < num_evt) {
        const char* end = p;
        while (*end && *end != '|') end++;
        int len = (int)(end - p);
        if (len > 0 && len < 255 && evt_idx < DD_MAX_REMOTE_EVENTS) {
            memcpy(_dd_nodos_remotos[idx].eventos[evt_idx], p, (size_t)len);
            _dd_nodos_remotos[idx].eventos[evt_idx][len] = '\0';
            evt_idx++;
        }
        p = (*end == '|') ? end + 1 : end;
    }
    _dd_nodos_remotos[idx].num_eventos = evt_idx;
    _dd_nodos_remotos[idx].ultima_sincro_s = (int)time(NULL);
    _dd_ultima_sincro = (int)time(NULL);

    pthread_mutex_unlock(&_dd_mutex);
    return 0;
}

// --- Sincronizar trazas con todos los nodos remotos registrados ---
// Envía la traza local a cada nodo remoto
int dd_sincronizar_trazas(int num_eventos) {
    if (!_dd_inicializado) return -1;

    pthread_mutex_lock(&_dd_mutex);
    int count = 0;
    for (int i = 0; i < _dd_total_remotos; i++) {
        if (_dd_nodos_remotos[i].activo) {
            CadenaSegura ip = {
                .longitud = (int)strlen(_dd_nodos_remotos[i].ip),
                .datos = _dd_nodos_remotos[i].ip
            };
            pthread_mutex_unlock(&_dd_mutex);
            int rc = dd_enviar_traza_remota(ip, _dd_nodos_remotos[i].puerto, num_eventos);
            pthread_mutex_lock(&_dd_mutex);
            if (rc == 0) count++;
        }
    }
    _dd_ultima_sincro = (int)time(NULL);
    pthread_mutex_unlock(&_dd_mutex);
    return count;
}

// --- Buscar evento en trazas remotas por tag ---
// Busca en todos los buffers remotos el último evento con el tag especificado
// Retorna "nodo_id:evento" o vacío si no se encuentra
CadenaSegura dd_buscar_evento_remoto(int tag, int desde_secuencia) {
    if (!_dd_inicializado)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    pthread_mutex_lock(&_dd_mutex);

    for (int n = _dd_total_remotos - 1; n >= 0; n--) {
        if (!_dd_nodos_remotos[n].activo) continue;
        for (int e = _dd_nodos_remotos[n].num_eventos - 1; e >= 0; e--) {
            const char* evt = _dd_nodos_remotos[n].eventos[e];
            if (!evt || !*evt) continue;
            // Event format: "tag|seq|funcion|linea|variable|valor"
            int evt_tag = 0;
            const char* p = evt;
            while (*p && *p != '|') { evt_tag = evt_tag * 10 + (*p - '0'); p++; }
            if (evt_tag == tag) {
                char result[512];
                int len = snprintf(result, sizeof(result), "%d:%s",
                                   _dd_nodos_remotos[n].nodo_id, evt);
                char* r = (char*)pool_alloc((size_t)(len + 1));
                if (!r) { pthread_mutex_unlock(&_dd_mutex); return (CadenaSegura){0, NULL}; }
                memcpy(r, result, (size_t)(len + 1));
                pthread_mutex_unlock(&_dd_mutex);
                return (CadenaSegura){ .longitud = len, .datos = r };
            }
        }
    }

    pthread_mutex_unlock(&_dd_mutex);
    return (CadenaSegura){ .longitud = 0, .datos = NULL };
}

// --- RPC: Establecer breakpoint remoto ---
// Envía comando SYNDBG:BP a nodo remoto
int dd_breakpoint_remoto(CadenaSegura ip, int puerto, int tipo, CadenaSegura patron, int valor_int) {
    if (!_dd_inicializado || !ip.datos || puerto <= 0) return -1;

    char buf[1024];
    const char* pt = patron.datos ? patron.datos : "";
    int len = snprintf(buf, sizeof(buf), "%s:BP:%d:%s:%d",
                       DD_PROTO_MAGIC, tipo, pt, valor_int);

    return cluster_canal_remoto_enviar(ip.datos, puerto, buf, len, 0);
}

// --- RPC: Inspeccionar variable en nodo remoto ---
// Envía comando SYNDBG:INSPECT y retorna el resultado (simulado)
CadenaSegura dd_inspeccionar_remoto(CadenaSegura ip, int puerto, CadenaSegura nombre_variable) {
    if (!_dd_inicializado || !ip.datos || puerto <= 0 || !nombre_variable.datos)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    // Build remote inspection request
    char buf[1024];
    int len = snprintf(buf, sizeof(buf), "%s:INSPECT:%.*s",
                       DD_PROTO_MAGIC, (int)nombre_variable.longitud, nombre_variable.datos);
    int rc = cluster_canal_remoto_enviar(ip.datos, puerto, buf, len, 0);
    if (rc < 0) return (CadenaSegura){ .longitud = 0, .datos = NULL };

    // For simulation: look up in local remote buffer
    // In real scenario, response comes via dd_recibir_traza_remota
    char result[128];
    int rlen = snprintf(result, sizeof(result), "remote_inspect:%d:%.*s",
                        _dd_local_nodo_id, (int)nombre_variable.longitud, nombre_variable.datos);
    char* r = (char*)pool_alloc((size_t)(rlen + 1));
    if (!r) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(r, result, (size_t)(rlen + 1));
    return (CadenaSegura){ .longitud = rlen, .datos = r };
}

// --- RPC: Obtener pila de llamadas remota ---
CadenaSegura dd_pila_remota(CadenaSegura ip, int puerto) {
    if (!_dd_inicializado || !ip.datos || puerto <= 0)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    char buf[256];
    int len = snprintf(buf, sizeof(buf), "%s:STACK:", DD_PROTO_MAGIC);
    int rc = cluster_canal_remoto_enviar(ip.datos, puerto, buf, len, 0);
    if (rc < 0) return (CadenaSegura){ .longitud = 0, .datos = NULL };

    char result[256];
    int rlen = snprintf(result, sizeof(result), "remote_stack:%d", _dd_local_nodo_id);
    char* r = (char*)pool_alloc((size_t)(rlen + 1));
    if (!r) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(r, result, (size_t)(rlen + 1));
    return (CadenaSegura){ .longitud = rlen, .datos = r };
}

// --- Total de eventos remotos recibidos ---
int dd_total_eventos_remotos(void) {
    if (!_dd_inicializado) return 0;

    pthread_mutex_lock(&_dd_mutex);
    int total = 0;
    for (int i = 0; i < _dd_total_remotos; i++) {
        total += _dd_nodos_remotos[i].num_eventos;
    }
    pthread_mutex_unlock(&_dd_mutex);
    return total;
}

// --- Número de nodos remotos registrados ---
int dd_nodos_remotos_registrados(void) {
    if (!_dd_inicializado) return 0;
    pthread_mutex_lock(&_dd_mutex);
    int n = _dd_total_remotos;
    pthread_mutex_unlock(&_dd_mutex);
    return n;
}

// --- Identificador del nodo local ---
int dd_nodo_local_id(void) {
    return _dd_local_nodo_id;
}

// --- Información del subsistema de debug distribuido ---
// Retorna "local_id:num_remotos:total_eventos_remotos:ultima_sincro"
CadenaSegura dd_info(void) {
    if (!_dd_inicializado)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    char buf[256];
    int total_evt = 0;
    pthread_mutex_lock(&_dd_mutex);
    for (int i = 0; i < _dd_total_remotos; i++) {
        total_evt += _dd_nodos_remotos[i].num_eventos;
    }
    int len = snprintf(buf, sizeof(buf), "%d:%d:%d:%d",
                       _dd_local_nodo_id, _dd_total_remotos,
                       total_evt, _dd_ultima_sincro);
    pthread_mutex_unlock(&_dd_mutex);

    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(result, buf, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = len, .datos = result };
}
