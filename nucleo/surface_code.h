// surface_code.h — Surface Code / Topological Error Correction (M16.3)
// ======================================================================
// Implementa correccion topologica de errores sobre una rejilla 2D LxL
// con estabilizadores tipo X (estrella) y tipo Z (plaqueta).
//
// Zero-telemetry: todo el proceso es local y soberano.
// ======================================================================

#ifndef SURFACE_CODE_H
#define SURFACE_CODE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// Constantes
// ============================================================
#define SC_MAX_L               7   // Maxima dimension de rejilla (7x7 = 49 qubits)
#define SC_MAGIC_HEADER        0x53435243  // "SCRC"
#define SC_VERSION             1
#define SC_MAX_STABILIZERS     100 // Suficiente para 7x7
#define SC_MAX_SYNDROMES       50

// Tipos de estabilizador
#define SC_STAB_X              0   // Estrella (X paridad)
#define SC_STAB_Z              1   // Plaqueta (Z paridad)

// Tipos de error
#define SC_ERROR_X             0
#define SC_ERROR_Z             1
#define SC_ERROR_BOTH          2

// Estados de correccion
#define SC_CORRECTED           0
#define SC_UNCORRECTED         1

// ============================================================
// Tipos
// ============================================================

// Qubit de datos en la rejilla
typedef struct {
    double error_x;          // Probabilidad de error X [0..1]
    double error_z;          // Probabilidad de error Z [0..1]
    int corregido;           // 1 si el error en este qubit fue corregido
    int etiqueta_union;      // Para Union-Find: indice del padre en cluster
} SCDataQubit;

// Estabilizador (X estrella o Z plaqueta)
typedef struct {
    int tipo;                // SC_STAB_X o SC_STAB_Z
    int activo;              // 1 si el estabilizador esta violado (sindrome positivo)
    int qubits[4];           // Indices de los qubits de datos asociados
    int num_qubits;          // Numero de qubits (2 para borde, 4 para interior)
    int fila;                // Posicion fila del estabilizador en la rejilla
    int col;                 // Posicion columna del estabilizador
} SCStabilizer;

// Rejilla completa de Surface Code
typedef struct {
    int L;                    // Dimension LxL
    int num_qubits;           // L*L qubits de datos
    int num_estabilizadores;  // Numero total de estabilizadores
    SCDataQubit* data_qubits; // Arreglo de qubits de datos [L*L]
    SCStabilizer* estabilizadores; // Arreglo de estabilizadores
    int* sindrome_x;          // Indices de estabilizadores X violados
    int* sindrome_z;          // Indices de estabilizadores Z violados
    int num_sindrome_x;       // Cantidad de sindromes X activos
    int num_sindrome_z;       // Cantidad de sindromes Z activos
    double tasa_error;        // Tasa de error actual (fraccion de qubits con error)
    int estado;               // Estado general de la rejilla
} SurfaceCode;

// Resultado de correccion topologica
typedef struct {
    int exito;                // 1 si la correccion fue exitosa
    double fidelidad;         // Fidelidad estimada de la correccion (0..1)
    int errores_detectados;   // Numero de errores detectados
    int errores_corregidos;   // Numero de errores corregidos exitosamente
    int errores_restantes;    // Errores que no pudieron ser corregidos
    char descripcion[128];    // Descripcion textual del resultado
} SCResultado;

// ============================================================
// API publica — 14 funciones
// ============================================================

// --- Ciclo de vida de la rejilla ---
SurfaceCode* sc_crear_rejilla(int L);
void sc_liberar_rejilla(SurfaceCode* rejilla);
void sc_limpiar_rejilla(SurfaceCode* rejilla);

// --- Inicializacion ---
int sc_inicializar_estado_cero(SurfaceCode* rejilla);

// --- Inyeccion de errores ---
int sc_inyectar_error_en(SurfaceCode* rejilla, int fila, int col, int tipo_error);
int sc_inyectar_cadena_error(SurfaceCode* rejilla, int tipo_error,
                              int f_inicio, int c_inicio,
                              int f_fin, int c_fin);

// --- Medicion de estabilizadores ---
int sc_medir_estabilizadores(SurfaceCode* rejilla);

// --- Decodificacion y correccion ---
int sc_decodificar_union_find(SurfaceCode* rejilla);
int sc_corregir_errores(SurfaceCode* rejilla);
SCResultado sc_ciclo_completo(SurfaceCode* rejilla, int num_errores_x, int num_errores_z);

// --- Verificacion ---
int sc_verificar_correccion(SurfaceCode* rejilla);
double sc_calcular_fidelidad(SurfaceCode* rejilla);

// --- Utilidades ---
int sc_obtener_num_errores(SurfaceCode* rejilla);
void sc_imprimir_rejilla(const SurfaceCode* rejilla);

// ============================================================
// Wrappers _syn_sc_* para enlace con std.surface_code
// ============================================================
void* _syn_sc_crear_rejilla(int L);
void _syn_sc_liberar_rejilla(void* rejilla);
int _syn_sc_inicializar_estado_cero(void* rejilla);
int _syn_sc_inyectar_error(void* rejilla, int fila, int col, int tipo);
int _syn_sc_medir_estabilizadores(void* rejilla);
int _syn_sc_corregir_errores(void* rejilla);
int _syn_sc_verificar_correccion(void* rejilla);

#ifdef __cplusplus
}
#endif

#endif // SURFACE_CODE_H
