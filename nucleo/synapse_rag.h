// synapse_rag.h — Pipeline RAG quirúrgico para extracción de contexto AST e indexación semántica
// v2.0: Añadido: AST chunking, embedding storage, cosine similarity search, n_ctx negotiation dinámica
// Implementa: extracción de nodo actual, línea activa, diagnósticos; indexación semántica; búsqueda por similitud

#ifndef SYNAPSE_RAG_H
#define SYNAPSE_RAG_H

#include <stddef.h>
#include <stdint.h>

// Forward declarations
typedef struct Nodo Nodo;
typedef struct ListaNodo ListaNodo;
typedef struct Programa Programa;

// ============================================================
// Constantes de configuración (v1 — herencia existente)
// ============================================================

#define RAG_MAX_CONTEXTO 4096
#define RAG_MAX_LINEA 512
#define RAG_MAX_DIAG 1024
#define RAG_N_CTX_DEFAULT 4096
#define RAG_RATIO_INYECCION_DEFAULT 0.3f
#define RAG_MAX_TOKENS_INYECTADOS 2048

// ============================================================
// Constantes de indexación semántica (v2 — nuevo)
// ============================================================

#define RAG_CHUNK_SIZE_MIN 16       // Mínimo 16 tokens por chunk
#define RAG_CHUNK_SIZE_MAX 512      // Máximo 512 tokens por chunk
#define RAG_CHUNK_OVERLAP 8         // 8 tokens de solapamiento entre chunks
#define RAG_MAX_CHUNKS 1024         // Máximo chunks indexables
#define RAG_EMBEDDING_DIM_DEFAULT 768 // Dimensión por defecto de embeddings
#define RAG_TOP_K_SIMILARES 5       // Top-K resultados de búsqueda semántica

// ============================================================
// Estructuras de datos (v1 — herencia existente)
// ============================================================

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

// ============================================================
// Estructuras de indexación semántica (v2 — nuevo)
// ============================================================

// Un chunk de código con su embedding
typedef struct {
    char* texto;                     // Texto del chunk
    int longitud;                    // Longitud del texto
    int linea_inicio;                // Línea de inicio en el fuente original
    int linea_fin;                   // Línea de fin en el fuente original
    float* embedding;                // Vector de embedding (malloc)
    int embedding_dim;               // Dimensión del embedding
    char tipo_nodo[64];              // Tipo de nodo AST (función, estructura, etc.)
    float puntuacion;                // Puntuación de similitud (resultado de búsqueda)
} RagChunk;

// Índice semántico completo
typedef struct {
    RagChunk chunks[RAG_MAX_CHUNKS]; // Array fijo de chunks
    int num_chunks;                  // Número de chunks actualmente en el índice
    int embedding_dim;               // Dimensión de los embeddings (uniforme)
    float* embedding_cache;          // Caché de embeddings para búsqueda rápida [num_chunks * dim]
} RagIndex;

// Resultado de búsqueda semántica
typedef struct {
    RagChunk* resultados[RAG_TOP_K_SIMILARES]; // Punteros a los chunks más similares
    float puntuaciones[RAG_TOP_K_SIMILARES];   // Puntuaciones de similitud normalizadas [0,1]
    int num_resultados;              // Número de resultados (≤ RAG_TOP_K_SIMILARES)
} RagResultados;

// Estadísticas del pipeline RAG
typedef struct {
    int chunks_indexados;
    int busquedas_realizadas;
    int tokens_inyectados_promedio;
    float tiempo_promedio_busqueda_ms;
} RagEstadisticas;

// ============================================================
// API Principal (v1 — herencia existente)
// ============================================================

// Extrae contexto quirúrgico: nodo actual, línea activa, diagnósticos
int synapse_rag_extraer_contexto(const SynapseRagInput* input, SynapseRagContexto* out);

// Libera memoria del contexto
void synapse_rag_liberar_contexto(SynapseRagContexto* ctx);

// Construye prompt RAG con presupuesto de tokens controlado
int synapse_rag_construir_prompt(const SynapseRagContexto* ctx, char* buf, size_t cap);

// Lee n_ctx del JSON /props del servidor llama.cpp
int synapse_rag_leer_n_ctx_desde_props(const char* props_json, int* out_n_ctx);

// Calcula max_tokens_inyectados = n_ctx * ratio (con límites)
int synapse_rag_calcular_max_tokens(int n_ctx, float ratio);

// ============================================================
// API de Indexación Semántica (v2 — nuevo)
// ============================================================

// Inicializa un índice semántico vacío
void synapse_rag_inicializar_indice(RagIndex* idx, int embedding_dim);

// Libera toda la memoria asociada a un índice
void synapse_rag_liberar_indice(RagIndex* idx);

// Indexa código fuente: chunking por función/estructura/bloque
// Recorre el AST textual y divide en chunks coherentes
// Retorna número de chunks indexados, -1 en error
int synapse_rag_indexar_texto(RagIndex* idx, const char* fuente,
                               const char* nombre_archivo);

// Indexa un chunk individual en el índice
// El chunk debe tener texto y embedding preasignados
// Retorna índice del chunk en el arreglo, -1 en error
int synapse_rag_indexar_chunk(RagIndex* idx, const RagChunk* chunk);

// Busca los K chunks más similares a un texto de consulta
// usando cosine similarity sobre los embeddings
// Retorna número de resultados, -1 en error
int synapse_rag_buscar_similares(const RagIndex* idx,
                                  const float* query_embedding,
                                  int query_dim,
                                  RagResultados* resultados);

// Cosine similarity entre dos vectores
float synapse_rag_coseno_similitud(const float* a, const float* b, int dim);

// Negocia n_ctx dinámicamente: ajusta ratio de inyección según
// el número de chunks relevantes y su tamaño total
// Retorna el max_tokens_inyectados óptimo
int synapse_rag_negociar_n_ctx(int n_ctx_modelo, int num_chunks_relevantes,
                                int tamano_total_chunks,
                                float* out_ratio_usado);

// Obtiene estadísticas del pipeline RAG
RagEstadisticas synapse_rag_obtener_estadisticas(void);

// ============================================================
// Integración con Fine-Tuning (M13.4)
// ============================================================

// Re-rank de resultados RAG usando adaptador LoRA fine-tuned
// Toma los chunks del índice, aplica el modelo fine-tuned para re-rankear
// y retorna los mejores resultados con puntuaciones ajustadas
// Retorna: número de resultados re-rankeados, -1 en error
int synapse_rag_re_rankear_con_ft(void* sesion_ft, const RagIndex* idx,
                                   const char* consulta,
                                   RagResultados* resultados_originales,
                                   RagResultados* resultados_ajustados);

// Genera embeddings contextuales usando el modelo fine-tuned
// El embedding generado refleja el conocimiento especializado del fine-tuning
// Retorna: puntero al embedding (debe liberarse con free()), NULL en error
float* synapse_rag_generar_embedding_ft(void* sesion_ft, const char* texto,
                                         int* out_dim);

#endif // SYNAPSE_RAG_H
