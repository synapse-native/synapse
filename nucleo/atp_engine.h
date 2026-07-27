// atp_engine.h — Motor de Demostración Automática de Teoremas (ATP Engine)
// ======================================================================
// Implementa un resolvedor SMT ligero integrado para verificar contratos
// requiere/garantiza en tiempo de compilación (--safe) sin requerir
// interacción manual en Coq o Lean.
//
// Capacidades:
//   - Resolución de tautologías aritméticas (x > 0 && x > 0 → válido)
//   - Detección de contradicciones lógicas (x > 0 && x < -5 → imposible)
//   - Propagación de intervalos para aritmética lineal
//   - Resolución proposicional (modus ponens, silogismo, contrapositiva)
//   - Verificación completa de contratos (pre → post)
//
// Zero-telemetry: todo el proceso es local y soberano.
// ======================================================================

#ifndef ATP_ENGINE_H
#define ATP_ENGINE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// Constantes
// ============================================================

#define ATP_MAX_CONSTRAINTS 64            // Máximo de restricciones
#define ATP_MAX_VARS 64                   // Máximo de variables por restricción
#define ATP_MAX_EXPR_LEN 4096             // Longitud máxima de expresión
#define ATP_MAX_VAR_NAME 64               // Longitud máxima de nombre de variable
#define ATP_MAX_ERROR_LEN 1024            // Longitud máxima de mensaje de error
#define ATP_MAGIC_HEADER 0x4154505A       // "ATPZ" — ATP engine magic
#define ATP_VERSION 1                     // Versión del formato

// Resultados de verificación
#define ATP_UNKNOWN 0       // No se pudo determinar
#define ATP_VALID 1         // Teorema válido (demostrado)
#define ATP_INVALID 2       // Teorema inválido (contraejemplo encontrado)
#define ATP_TIMEOUT 3       // Tiempo de resolución agotado
#define ATP_ERROR 4         // Error en el proceso

// Tipos de restricción
#define ATP_CONSTRAINT_REQUIERE 0         // Precondición
#define ATP_CONSTRAINT_GARANTIZA 1        // Postcondición
#define ATP_CONSTRAINT_INVARIANTE 2       // Invariante
#define ATP_CONSTRAINT_ASUNCION 3         // Asunción auxiliar

// Tipos de operador
#define ATP_OP_AND 0
#define ATP_OP_OR 1
#define ATP_OP_NOT 2
#define ATP_OP_IMPLIES 3
#define ATP_OP_EQ 4          // ==
#define ATP_OP_NEQ 5         // !=
#define ATP_OP_LT 6          // <
#define ATP_OP_GT 7          // >
#define ATP_OP_LE 8          // <=
#define ATP_OP_GE 9          // >=
#define ATP_OP_PLUS 10
#define ATP_OP_MINUS 11
#define ATP_OP_MULT 12
#define ATP_OP_DIV 13

// Tipos de átomo
#define ATP_ATOM_VAR 0       // Variable
#define ATP_ATOM_CONST 1     // Constante numérica
#define ATP_ATOM_BOOL 2      // Booleano (true/false)
#define ATP_ATOM_OP 3        // Operación

// ============================================================
// Tipos de datos
// ============================================================

// Átomo de expresión (variable, constante, operación)
typedef struct {
    int tipo;                           // ATP_ATOM_*
    char nombre_var[ATP_MAX_VAR_NAME];  // Nombre (para variables)
    double valor_const;                 // Valor (para constantes)
    int operador;                       // ATP_OP_* (para operaciones)
    int hijo_izq;                       // Índice del hijo izquierdo
    int hijo_der;                       // Índice del hijo derecho
    int negado;                         // 1 = expresión negada
} ATPAtom;

// Restricción lógica
typedef struct {
    char expresion[ATP_MAX_EXPR_LEN];   // Expresión original (Synapse)
    int tipo;                           // ATP_CONSTRAINT_*
    int num_vars;                       // Número de variables
    char vars[ATP_MAX_VARS][ATP_MAX_VAR_NAME];  // Variables
    int num_atomos;                     // Número de átomos en la expresión
    ATPAtom atomos[64];                 // Átomos descompuestos
    int es_lineal;                      // 1 = expresión lineal
    int es_booleana;                    // 1 = expresión booleana
    double cota_inferior;               // Cota inferior inferida (intervalo)
    double cota_superior;               // Cota superior inferida (intervalo)
    int tiene_cota_inf;                 // 1 = tiene cota inferior definida
    int tiene_cota_sup;                 // 1 = tiene cota superior definida
    int evaluable;                      // 1 = se puede evaluar numéricamente
} ATPConstraint;

// Intervalo de variable (para propagación aritmética)
typedef struct {
    char nombre[ATP_MAX_VAR_NAME];
    double inf;                          // Cota inferior (-inf si no definida)
    double sup;                          // Cota superior (+inf si no definida)
    int tiene_inf;                       // 1 si cota inferior definida
    int tiene_sup;                       // 1 si cota superior definida
    int es_entero;                       // 1 si variable de tipo entero
} ATPInterval;

// Estadísticas del motor ATP
typedef struct {
    int num_precondiciones;
    int num_postcondiciones;
    int num_teoremas_demostrados;
    int num_contradicciones_encontradas;
    int num_resolution_steps;
    double tiempo_total_ms;
    int ultimo_resultado;               // ATP_*
} ATPEstadisticas;

// Configuración del motor ATP
typedef struct {
    int max_resolution_depth;           // Máxima profundidad de resolución (default: 100)
    int max_theorem_size;               // Máximo tamaño de teorema en átomos (default: 256)
    int use_arithmetic_solver;          // 1 = resolver aritmética lineal (default: 1)
    int use_propagation;                // 1 = propagar restricciones (default: 1)
    int use_contradiction_check;        // 1 = verificar contradicciones (default: 1)
    int timeout_ms;                     // Timeout de resolución (default: 5000)
    int verify_strict;                  // 1 = estricto (default: 0, permite unknown)
} ATPConfig;

// Motor ATP
typedef struct {
    ATPConfig config;
    ATPConstraint preconditions[ATP_MAX_CONSTRAINTS];
    int num_preconditions;
    ATPConstraint postconditions[ATP_MAX_CONSTRAINTS];
    int num_postconditions;
    ATPConstraint invariants[ATP_MAX_CONSTRAINTS];
    int num_invariants;
    char function_name[256];
    ATPInterval intervalos[ATP_MAX_VARS];
    int num_intervalos;
    int last_result;                    // ATP_*
    char error_message[ATP_MAX_ERROR_LEN];
    int resolution_steps;
    double resolution_time_ms;
    int estado;                         // 0=init, 1=resolviendo, 2=completado
} ATPEngine;

// ============================================================
// API del Motor ATP
// ============================================================

// Inicializa un motor ATP con configuración
// Retorna: puntero a ATPEngine, NULL en error
ATPEngine* atp_iniciar(const ATPConfig* config);

// Agrega una precondición (requiere) al motor
// Retorna: índice de la restricción, -1 en error
int atp_agregar_precondicion(ATPEngine* engine, const char* expresion);

// Agrega una postcondición (garantiza) al motor
// Retorna: índice de la restricción, -1 en error
int atp_agregar_postcondicion(ATPEngine* engine, const char* expresion);

// Agrega un invariante al motor
// Retorna: índice de la restricción, -1 en error
int atp_agregar_invariante(ATPEngine* engine, const char* expresion);

// Establece el nombre de la función a verificar
void atp_establecer_funcion(ATPEngine* engine, const char* nombre);

// Verifica si una expresión individual es una tautología
// Retorna: ATP_VALID si siempre es verdadera, ATP_INVALID si no
int atp_verificar_tautologia(ATPEngine* engine, const char* expresion);

// Verifica si hay contradicciones entre las restricciones actuales
// Retorna: 1 si hay contradicción, 0 si no, -1 en error
int atp_verificar_contradiccion(ATPEngine* engine);

// Propaga restricciones entre precondiciones para inferir nuevas cotas
// Retorna: número de inferencias realizadas
int atp_propagar_restricciones(ATPEngine* engine);

// Demuestra que las postcondiciones se siguen de las precondiciones (pre → post)
// Retorna: ATP_VALID, ATP_INVALID, ATP_UNKNOWN, ATP_TIMEOUT, ATP_ERROR
int atp_demostrar(ATPEngine* engine);

// Verifica un contrato completo: pre → post (con propagación y contradicción)
// Retorna: ATP_VALID, ATP_INVALID, ATP_UNKNOWN
int atp_verificar_contrato(ATPEngine* engine,
                            const char** precondiciones, int num_pre,
                            const char** postcondiciones, int num_post);

// Obtiene las estadísticas actuales del motor
ATPEstadisticas atp_obtener_estadisticas(ATPEngine* engine);

// Guarda el estado del motor a archivo binario
// Formato: [ATP_MAGIC][version][config][restricciones][intervalos]
// Retorna: 0 en éxito, -1 en error
int atp_guardar(const ATPEngine* engine, const char* ruta);

// Carga el estado del motor desde archivo
// Retorna: 0 en éxito, -1 en error
int atp_cargar(ATPEngine* engine, const char* ruta);

// Limpia todas las restricciones del motor
void atp_limpiar(ATPEngine* engine);

// Cierra el motor y libera memoria
void atp_cerrar(ATPEngine* engine);

#ifdef __cplusplus
}
#endif

#endif // ATP_ENGINE_H
