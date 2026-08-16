// synapse_rt_debug.h — Public API of runtime/core/debug.c
// Extraido de synapse_rt.c (deuda D-9(d), corte 5 tras cluster.c R40).
#ifndef SYNAPSE_RT_DEBUG_H
#define SYNAPSE_RT_DEBUG_H

#include "synapse_rt_types.h"

#ifdef __cplusplus
extern "C" {
#endif

// --- Tipos compartidos del sistema de traza (movidos aqui en D-9(d) corte 5:
//     debug.h debe declarar los tipos que usan sus prototipos) ---
#define TRACE_MAX_EVENTS 50000
#define TRACE_DIR ".synapse/traces"

typedef enum {
    EVENT_ASSIGNMENT = 0,
    EVENT_FN_CALL = 1,
    EVENT_FN_RETURN = 2,
    EVENT_ERROR = 3,
    EVENT_BRANCH_TAKEN = 4,
    EVENT_LOOP_ITERATION = 5,
    EVENT_VARIABLE_CHANGE = 6,
    EVENT_CONTRACT_CHECK = 7,
    EVENT_USER_TRACE = 8
} TraceEventTag;

typedef struct {
    int tag;
    long long timestamp;
    const char* funcion;
    const char* archivo;
    int linea;
    long long valor_entero;
    double valor_decimal;
    const char* valor_texto;
    const char* variable;
} TraceEvent;

typedef struct {
    char id[64];
    char programa[256];
    TraceEvent* eventos;
    int total_eventos;
    int capacidad;
    int cabeza;
    int estado;  // 0=ACTIVA, 1=FINALIZADA, 2=PERSISTIDA
} TraceSession;

long long _get_timestamp_ns(void);
CadenaSegura _syn_debug_iniciar_sesion(CadenaSegura programa);
int _syn_debug_registrar_evento(int tag, const char* funcion, const char* archivo, int linea, const char* variable, long long valor_entero, double valor_decimal, const char* valor_texto);
int _syn_debug_trace(const char* expresion_texto, void* valor, const char* tipo);
CadenaSegura _syn_debug_finalizar_sesion(void);
TraceSession _syn_debug_obtener_sesion(void);
int tr_inicializar_recording(void);
int tr_grabar_bifurcacion(int linea, int rama, CadenaSegura id_funcion);
int tr_grabar_snapshot(CadenaSegura nombre_variable, int valor_entero, CadenaSegura valor_texto, int linea);
int tr_grabar_llamada(CadenaSegura funcion, int linea, int num_args);
int tr_grabar_retorno(CadenaSegura funcion, int linea);
int tr_grabar_error(CadenaSegura mensaje, int linea);
int tr_buscar_evento(int tag, int desde_secuencia);
CadenaSegura tr_obtener_evento(int indice);
int tr_reproducir_hasta(int secuencia_objetivo);
int tr_indice_ultimo_error(void);
int tr_total_eventos(void);
int rp_inicializar(void);
int rp_establecer_breakpoint(int tipo, CadenaSegura patron, int valor_int);
int rp_eliminar_breakpoint(int id);
int rp_limpiar_breakpoints(void);
int rp_buscar_breakpoint(int id);
int rp_retroceder(int pasos, int desde_evento);
int rp_posicion_actual(void);
int rp_ir_a_pre_error(void);
CadenaSegura rp_inspeccionar_variable(int indice_evento, CadenaSegura nombre);
CadenaSegura rp_pila_llamadas(int indice_evento);
int rp_buscar_cambio_variable(CadenaSegura nombre, int valor);
CadenaSegura ms_tomar_en(int secuencia);
CadenaSegura ms_diferenciar(CadenaSegura snap_a, CadenaSegura snap_b);
CadenaSegura ms_diff_entre(int seq_a, int seq_b);
int ms_snapshot_contar_vars(CadenaSegura snapshot);
int ms_snapshot_tamano(CadenaSegura snapshot);
CadenaSegura ms_snapshot_contiene(CadenaSegura snapshot, CadenaSegura nombre);
int dd_inicializar(int nodo_id);
int dd_registrar_nodo_remoto(int nodo_id, CadenaSegura ip, int puerto);
int dd_enviar_traza_remota(CadenaSegura ip, int puerto, int num_eventos);
int dd_recibir_traza_remota(CadenaSegura paquete);
int dd_sincronizar_trazas(int num_eventos);
CadenaSegura dd_buscar_evento_remoto(int tag, int desde_secuencia);
int dd_breakpoint_remoto(CadenaSegura ip, int puerto, int tipo, CadenaSegura patron, int valor_int);
CadenaSegura dd_inspeccionar_remoto(CadenaSegura ip, int puerto, CadenaSegura nombre_variable);
CadenaSegura dd_pila_remota(CadenaSegura ip, int puerto);
int dd_total_eventos_remotos(void);
int dd_nodos_remotos_registrados(void);
int dd_nodo_local_id(void);
CadenaSegura dd_info(void);

#ifdef __cplusplus
}
#endif

#endif /* SYNAPSE_RT_DEBUG_H */