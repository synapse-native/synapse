// symbolic_exec.h — Motor de Ejecución Simbólica (M15.3)
// ======================================================================
// Implementa un motor que ejecuta rutas del AST sobre valores simbólicos,
// integrando el motor ATP (atp_engine.h), el puente de demostración
// (proof_bridge.h) y el verificador de contratos (verificador_formal.syn).
//
// Capacidades:
//   - Creación y gestión de variables simbólicas (α, β, γ)
//   - Rastreo de condiciones de ruta (Path Conditions)
//   - Exploración de bifurcaciones de control (si/sino, coincidir)
//   - Detección de caminos imposibles (contradicciones simbólicas)
//   - Verificación de alcanzabilidad de estados de error
//   - Detección de violaciones de contratos (división por cero,
//     desbordamiento aritmético, fuera de límites)
//
// Integración:
//   - ATP Engine: resolución de restricciones por intervalos
//   - Proof Bridge: exportación de condiciones de ruta a Coq/Lean
//
// Zero-telemetry: todo el proceso es local y soberano.
// ======================================================================

#ifndef SYMBOLIC_EXEC_H
#define SYMBOLIC_EXEC_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// Constantes
// ============================================================

#define SE_MAX_VARS 64                   // Máximo de variables simbólicas
#define SE_MAX_CONSTRAINTS 256           // Máximo de restricciones por ruta
#define SE_MAX_PATHS 256                 // Máximo de rutas exploradas
#define SE_MAX_VAR_NAME 64               // Longitud máxima de nombre de variable
#define SE_MAX_EXPR_LEN 4096             // Longitud máxima de expresión
#define SE_MAX_ERROR_LEN 1024            // Longitud máxima de mensaje de error
#define SE_MAGIC_HEADER 0x53454E47       // "SENG" — Symbolic engine magic
#define SE_VERSION 1                     // Versión del formato

// Estados de ruta
#define SE_PATH_ACTIVE 0                 // Ruta activa (explorando)
#define SE_PATH_FEASIBLE 1               // Ruta factible
#define SE_PATH_INFEASIBLE 2             // Ruta imposible (contradicción)
#define SE_PATH_VIOLATION 3              // Ruta con violación detectada
#define SE_PATH_EXPLORED 4               // Ruta completamente explorada

// Tipos de restricción simbólica
#define SE_CONSTRAINT_EQ 0               // ==
#define SE_CONSTRAINT_NEQ 1              // !=
#define SE_CONSTRAINT_LT 2               // <
#define SE_CONSTRAINT_GT 3               // >
#define SE_CONSTRAINT_LE 4               // <=
#define SE_CONSTRAINT_GE 5               // >=

// Tipos de violación
#define SE_VIOLATION_NONE 0              // Sin violación
#define SE_VIOLATION_DIV_BY_ZERO 1       // División por cero
#define SE_VIOLATION_OVERFLOW 2          // Desbordamiento aritmético
#define SE_VIOLATION_BOUNDS 3            // Fuera de límites (array)
#define SE_VIOLATION_CONTRACT 4          // Violación de contrato

// Modos de exploración
#define SE_EXPLORE_ALL 0                 // Explorar todas las rutas
#define SE_EXPLORE_FEASIBLE 1            // Solo rutas factibles
#define SE_EXPLORE_VIOLATIONS 2          // Solo rutas con violaciones

// ============================================================
// Tipos de datos
// ============================================================

// Variable simbólica
typedef struct {
    char nombre[SE_MAX_VAR_NAME];        // Nombre único (α, β, x, n, etc.)
    int tipo_hint;                       // 0=entero, 1=decimal, 2=booleano
    double cota_inf;                     // Cota inferior simbólica
    double cota_sup;                     // Cota superior simbólica
    int tiene_cota_inf;                  // 1 si cota inferior definida
    int tiene_cota_sup;                  // 1 si cota superior definida
    int es_simbolica;                    // 1 si es variable simbólica (no concreta)
} SEVariable;

// Restricción de condición de ruta
typedef struct {
    char expresion[SE_MAX_EXPR_LEN];     // Expresión textual (ej. "x > 5")
    int tipo;                            // SE_CONSTRAINT_*
    char variable[SE_MAX_VAR_NAME];      // Variable involucrada
    double valor;                        // Valor de comparación
    int es_simbolica;                    // 1 si involucra variables simbólicas
    int es_activa;                       // 1 si la restricción está activa
} SEConstraint;

// Ruta de ejecución simbólica
typedef struct {
    int estado;                          // SE_PATH_*
    SEConstraint constraints[SE_MAX_CONSTRAINTS];
    int num_constraints;
    int violation_type;                  // SE_VIOLATION_*
    char violation_msg[SE_MAX_ERROR_LEN];
    int profundidad;                     // Profundidad de exploración
    int num_bifurcaciones;               // Número de bifurcaciones en esta ruta
    double coste_estimado;               // Coste estimado de la ruta
    int idx_inicio;                      // Índice de inicio en el AST
} SEPath;

// Configuración del motor de ejecución simbólica
typedef struct {
    int explore_mode;                    // SE_EXPLORE_*
    int max_path_depth;                  // Máxima profundidad de exploración (default: 100)
    int detect_div_by_zero;              // 1 = detectar división por cero
    int detect_overflow;                 // 1 = detectar desbordamiento
    int detect_bounds;                   // 1 = detectar fuera de límites
    int detect_contract_violations;      // 1 = detectar violaciones de contrato
    int use_atp_engine;                  // 1 = usar ATP engine para restricciones
    int timeout_ms;                      // Timeout de exploración (default: 5000)
} SEConfig;

// Estadísticas del motor simbólico
typedef struct {
    int num_variables;
    int num_rutas_exploradas;
    int num_rutas_factibles;
    int num_rutas_infactibles;
    int num_violaciones_detectadas;
    int num_bifurcaciones;
    int num_restricciones;
    double tiempo_total_ms;
} SEEstadisticas;

// Motor de ejecución simbólica
typedef struct {
    SEConfig config;
    SEVariable variables[SE_MAX_VARS];
    int num_variables;
    SEPath paths[SE_MAX_PATHS];
    int num_paths;
    int active_path_idx;                 // Índice de la ruta activa actual
    char error_message[SE_MAX_ERROR_LEN];
    int estado;                          // 0=init, 1=explorando, 2=completado
    double tiempo_total_ms;
    void* atp_engine;                    // Puntero al ATPEngine (opcional)
} SEEngine;

// ============================================================
// API del Motor de Ejecución Simbólica
// ============================================================

// Inicializa un motor de ejecución simbólica
// Si atp_engine no es NULL, lo usa para resolver restricciones
// Retorna: puntero a SEEngine, NULL en error
SEEngine* se_iniciar(const SEConfig* config, void* atp_engine);

// Crea una variable simbólica con nombre y cotas opcionales
// Retorna: índice de la variable, -1 en error
int se_agregar_variable(SEEngine* engine, const char* nombre,
                         double cota_inf, double cota_sup,
                         int tipo_hint);

// Agrega una restricción a la ruta activa
// Retorna: índice de la restricción, -1 en error
int se_agregar_restriccion(SEEngine* engine, const char* expresion, int tipo);

// Bifurca la ruta activa en dos: una con la condición y otra con su negación
// Retorna: 0 en éxito, -1 en error
int se_bifurcar(SEEngine* engine, const char* condicion);

// Verifica si la ruta activa es alcanzable (no contradictoria)
// Retorna: 1 si alcanzable, 0 si no, -1 en error
int se_verificar_alcanzabilidad(SEEngine* engine);

// Detecta si una expresión aritmética puede causar división por cero
// bajo las restricciones actuales
// Retorna: SE_VIOLATION_DIV_BY_ZERO si hay riesgo, SE_VIOLATION_NONE si no
int se_detectar_division_por_cero(SEEngine* engine, const char* divisor_expr);

// Detecta si una operación aritmética puede causar desbordamiento
// bajo las restricciones actuales
// Retorna: SE_VIOLATION_OVERFLOW si hay riesgo, SE_VIOLATION_NONE si no
int se_detectar_desbordamiento(SEEngine* engine, const char* op_expr,
                                double limite_inf, double limite_sup);

// Detecta si un acceso a array puede estar fuera de límites
// Retorna: SE_VIOLATION_BOUNDS si hay riesgo, SE_VIOLATION_NONE si no
int se_detectar_fuera_limites(SEEngine* engine, const char* idx_expr,
                               int tamano_array);

// Detecta violaciones de contrato (requiere/garantiza) en la ruta activa
// Retorna: SE_VIOLATION_CONTRACT si hay violación, SE_VIOLATION_NONE si no
int se_detectar_violacion_contrato(SEEngine* engine,
                                    const char* precondiciones[], int num_pre,
                                    const char* postcondiciones[], int num_post);

// Explora todas las rutas factibles desde el estado actual
// Retorna: número de rutas exploradas, -1 en error
int se_explorar(SEEngine* engine);

// Cambia la ruta activa a un índice específico
// Retorna: 0 en éxito, -1 en error
int se_activar_ruta(SEEngine* engine, int idx);

// Obtiene las estadísticas actuales del motor
SEEstadisticas se_obtener_estadisticas(SEEngine* engine);

// Guarda el estado del motor a archivo binario
// Formato: [SE_MAGIC][version][config][variables][paths][restricciones]
// Retorna: 0 en éxito, -1 en error
int se_guardar(const SEEngine* engine, const char* ruta);

// Carga el estado del motor desde archivo
// Retorna: 0 en éxito, -1 en error
int se_cargar(SEEngine* engine, const char* ruta);

// Limpia todas las variables, rutas y restricciones del motor
void se_limpiar(SEEngine* engine);

// Cierra el motor y libera memoria
void se_cerrar(SEEngine* engine);

#ifdef __cplusplus
}
#endif

#endif // SYMBOLIC_EXEC_H
