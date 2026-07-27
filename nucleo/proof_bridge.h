// proof_bridge.h — Puente de Verificación Formal (Coq/Lean Bridge)
// =================================================================
// Conecta el módulo de contratos lógicos de Synapse (--safe) con
// asistentes de demostración de teoremas interactivos (Coq o Lean),
// exportando el AST canónico y las especificaciones de pre/postcondiciones
// (requiere/garantiza) a términos lógicos verificables matemáticamente.
//
// Formatos soportados:
//   - Coq (.v): Términos del Cálculo de Construcciones Inductivas (CIC)
//   - Lean (.lean): Términos del Cálculo de Construcciones con universos
//
// Zero-telemetry: todo el proceso es local y soberano.
// =================================================================

#ifndef PROOF_BRIDGE_H
#define PROOF_BRIDGE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// Constantes
// ============================================================

#define PB_MAX_CONTRACTS 64            // Máximo de contratos por función
#define PB_MAX_FUNCTIONS 1024          // Máximo de funciones verificables
#define PB_MAX_EXPR_LEN 4096           // Longitud máxima de expresión lógica
#define PB_MAX_FILE_LEN 65536          // Longitud máxima de archivo .v/.lean
#define PB_MAGIC_HEADER 0x50524F46     // "PROF" — Proof bridge magic
#define PB_VERSION 1                   // Versión del formato
#define PB_MAX_CERT_LEN 8192           // Longitud máxima de certificado

// Formatos de asistente de pruebas
#define PB_FORMAT_COQ 0                // Coq (.v)
#define PB_FORMAT_LEAN 1               // Lean (.lean)

// Tipos de contrato
#define PB_CONTRACT_REQUIERE 0         // Precondición
#define PB_CONTRACT_GARANTIZA 1        // Postcondición
#define PB_CONTRACT_INVARIANTE 2       // Invariante de bucle

// Estados de verificación
#define PB_VERIFY_UNCHECKED 0          // No verificado
#define PB_VERIFY_VALID 1              // Verificado correcto
#define PB_VERIFY_INVALID 2            // Verificado incorrecto
#define PB_VERIFY_ERROR 3              // Error en verificación

// ============================================================
// Tipos de datos
// ============================================================

// Expresión de contrato exportable a lógica formal
typedef struct {
    char expresion[PB_MAX_EXPR_LEN];    // Expresión original (Synapse)
    char termino_coq[PB_MAX_EXPR_LEN];  // Término Coq equivalente
    char termino_lean[PB_MAX_EXPR_LEN]; // Término Lean equivalente
    int tipo_contrato;                  // PB_CONTRACT_*
    int es_valido;                      // 0 = inválido, 1 = válido
    char dependencias[PB_MAX_EXPR_LEN]; // Dependencias para el teorema
} PBContractExpr;

// Función verificable con sus contratos
typedef struct {
    char nombre_funcion[PB_MAX_EXPR_LEN];
    PBContractExpr requiere[PB_MAX_CONTRACTS];
    int num_requiere;
    PBContractExpr garantiza[PB_MAX_CONTRACTS];
    int num_garantiza;
    char tipo_retorno[64];
    int num_parametros;
    char parametros[PB_MAX_EXPR_LEN];    // Lista de parámetros tipados
    int verificada;                      // PB_VERIFY_*
    char certificado[PB_MAX_CERT_LEN];   // Certificado de prueba (hash)
} PBFunctionSpec;

// Configuración del puente de verificación
typedef struct {
    int formato_destino;              // PB_FORMAT_COQ o PB_FORMAT_LEAN
    int generar_esqueleto;            // 1 = generar esqueleto de proof
    int verificar_automatico;         // 1 = verificar automáticamente
    char ruta_salida[256];            // Directorio de salida para archivos
    char nombre_teoria[64];           // Nombre de la teoría/módulo
    int incluir_axiomas;              // 1 = incluir axiomas de apoyo
} PBConfig;

// Certificado de verificación
typedef struct {
    uint32_t magic;                   // PB_MAGIC_HEADER
    uint32_t version;                 // PB_VERSION
    char hash_funcion[64];            // SHA-256 de la especificación
    char resultado[16];               // "VALID" o "INVALID"
    char proof_hash[64];              // Hash del proof term
    int64_t timestamp;                // Timestamp de verificación
} PBCertificate;

// Estadísticas del puente
typedef struct {
    int num_funciones_exportadas;
    int num_contratos_exportados;
    int num_funciones_verificadas;
    int num_certificados_generados;
    int formato_usado;                // PB_FORMAT_COQ o PB_FORMAT_LEAN
    int errores_traduccion;
    int archivos_generados;
} PBEstadisticas;

// Sesión del puente de verificación
typedef struct {
    PBConfig config;
    PBFunctionSpec funciones[PB_MAX_FUNCTIONS];
    int num_funciones;
    int estado;                       // 0=init, 1=exportando, 2=verificado
    char buffer_salida[PB_MAX_FILE_LEN];  // Buffer para archivo generado
    int num_archivos_generados;
    char archivos_generados[64][256]; // Lista de archivos generados
} PBSession;

// ============================================================
// API del Puente de Verificación Formal
// ============================================================

// Inicializa una sesión del puente con configuración
// Retorna: puntero a PBSession, NULL en error
PBSession* pb_iniciar(const PBConfig* config);

// Agrega una función con sus contratos para verificación formal
// Retorna: índice de la función, -1 en error
int pb_agregar_funcion(PBSession* sesion, const char* nombre,
                        const char* tipo_retorno, const char* parametros);

// Agrega un contrato (requiere/garantiza) a la última función agregada
// Retorna: 0 en éxito, -1 en error
int pb_agregar_contrato(PBSession* sesion, const char* expresion,
                         int tipo_contrato);

// Traduce una expresión Synapse a término Coq
// Retorna: puntero a string con término Coq, NULL en error
const char* pb_traducir_a_coq(const char* expr_synapse);

// Traduce una expresión Synapse a término Lean
// Retorna: puntero a string con término Lean, NULL en error
const char* pb_traducir_a_lean(const char* expr_synapse);

// Genera archivo de teoría Coq (.v) con todas las funciones y contratos
// Retorna: número de caracteres escritos, -1 en error
int pb_generar_archivo_coq(PBSession* sesion);

// Genera archivo de teoría Lean (.lean) con todas las funciones y contratos
// Retorna: número de caracteres escritos, -1 en error
int pb_generar_archivo_lean(PBSession* sesion);

// Genera certificado de verificación para una función
// Retorna: 0 en éxito, -1 en error
int pb_generar_certificado(PBSession* sesion, const char* nombre_funcion);

// Verifica un certificado contra una especificación de función
// Retorna: PB_VERIFY_VALID, PB_VERIFY_INVALID, o PB_VERIFY_ERROR
int pb_verificar_certificado(const PBCertificate* cert,
                              const PBFunctionSpec* spec);

// Exporta todas las funciones a archivos en el directorio configurado
// Retorna: número de archivos generados, -1 en error
int pb_exportar(PBSession* sesion);

// Obtiene estadísticas del puente
PBEstadisticas pb_obtener_estadisticas(PBSession* sesion);

// Guarda el estado de la sesión a archivo binario
// Formato: [PB_MAGIC][version][config][funciones][contratos][certificados]
// Retorna: 0 en éxito, -1 en error
int pb_guardar(const PBSession* sesion, const char* ruta);

// Carga el estado de la sesión desde archivo
// Retorna: 0 en éxito, -1 en error
int pb_cargar(PBSession* sesion, const char* ruta);

// Cierra la sesión y libera memoria
void pb_cerrar(PBSession* sesion);

#ifdef __cplusplus
}
#endif

#endif // PROOF_BRIDGE_H
