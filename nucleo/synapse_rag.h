// synapse_rag.h — Pipeline RAG quirúrgico para extracción de contexto AST
// Implementa: extracción de nodo actual, línea activa, diagnósticos; negociación dinámica n_ctx

#ifndef SYNAPSE_RAG_H
#define SYNAPSE_RAG_H

#include <stddef.h>
#include <stdint.h>

// Forward declarations
typedef struct Nodo Nodo;
typedef struct ListaNodo ListaNodo;
typedef struct Programa Programa;

// Constantes de configuración
#define RAG_MAX_CONTEXTO 4096
#define RAG_MAX_LINEA 512
#define RAG_MAX_DIAG 1024
#define RAG_N_CTX_DEFAULT 4096
#define RAG_RATIO_INYECCION_DEFAULT 0.3f
#define RAG_MAX_TOKENS_INYECTADOS 2048

// Entrada para extracción de contexto RAG
typedef struct {
    const char* fuente;              // Texto completo del archivo
    int linea;                       // Línea objetivo (0-indexed)
    int columna;                     // Columna objetivo (0-indexed)
    const char* diagnosticos;        // Diagnósticos formateados (JSON o texto)
    const Programa* ast_root;        // Raíz del AST parseado
    int n_ctx_modelo;                // n_ctx del modelo cargado (0 = usar default)
} SynapseRagInput;

// Contexto extraído para inyección en prompt
typedef struct {
    char* contexto_archivo;          // Ventana de ~11 líneas alrededor de la línea actual
    char* linea_actual;              // Línea exacta en posición cursor
    char* diagnosticos;              // Diagnósticos recientes
    char* nodo_actual_tipo;          // Tipo del nodo AST en posición cursor
    int n_ctx_modelo;                // n_ctx del modelo (leído de /props)
    int max_tokens_inyectados;       // n_ctx * 0.3 (30% para contexto)
    int max_tokens_generacion;       // n_ctx * 0.7 (70% para respuesta)
} SynapseRagContexto;

// API Principal

// Extrae contexto quirúrgico: nodo actual, línea activa, diagnósticos
// Retorna 0 en éxito, -1 en error
int synapse_rag_extraer_contexto(const SynapseRagInput* input, SynapseRagContexto* out);

// Libera memoria del contexto
void synapse_rag_liberar_contexto(SynapseRagContexto* ctx);

// Construye prompt RAG con presupuesto de tokens controlado
// Retorna 0 en éxito, -1 en error
int synapse_rag_construir_prompt(const SynapseRagContexto* ctx, char* buf, size_t cap);

// Lee n_ctx del JSON /props del servidor llama.cpp
// Retorna 0 en éxito, -1 si no se encuentra
int synapse_rag_leer_n_ctx_desde_props(const char* props_json, int* out_n_ctx);

// Calcula max_tokens_inyectados = n_ctx * ratio (con límites)
// ratio default 0.3, max 0.5, min tokens 64
int synapse_rag_calcular_max_tokens(int n_ctx, float ratio);

#endif // SYNAPSE_RAG_H