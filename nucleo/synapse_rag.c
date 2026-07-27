// synapse_rag.c — Pipeline RAG quirúrgico para extracción de contexto AST e indexación semántica
// v2.0: Añadido: AST chunking, embedding storage, cosine similarity search, n_ctx negotiation dinámica
// Parte del núcleo Synapse LSP nativo — C99

#include "synapse_rag.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>
#include <time.h>

// ============================================================
// Helpers internos (v1 — herencia existente)
// ============================================================

static char* rag_strdup(const char* s) {
    return s ? strdup(s) : NULL;
}

static void rag_append(char* buf, size_t* pos, size_t cap, const char* s) {
    if (!s) return;
    size_t len = strlen(s);
    if (*pos + len + 1 >= cap) return;
    memcpy(buf + *pos, s, len);
    *pos += len;
    buf[*pos] = '\0';
}

// Extrae una ventana de contexto alrededor de una línea (5 líneas antes/después)
static void extraer_ventana_contexto(const char* fuente, int linea, char* buf, size_t cap) {
    if (!fuente || linea < 0) { buf[0] = '\0'; return; }

    const char* inicio = fuente;
    int inicio_ventana = linea > 5 ? linea - 5 : 0;
    for (int i = 0; i < inicio_ventana && *inicio; i++) {
        inicio = strchr(inicio, '\n');
        if (!inicio) { inicio = fuente + strlen(fuente); break; }
        inicio++;
    }

    // Copiar hasta línea objetivo + 5
    const char* fin = inicio;
    int lineas = 0;
    while (*fin && lineas < 11) { // 5 antes + actual + 5 después
        if (*fin == '\n') lineas++;
        fin++;
    }

    size_t len = fin - inicio;
    if (len >= cap) len = cap - 1;
    memcpy(buf, inicio, len);
    buf[len] = '\0';
}

// Extrae la línea exacta
static void extraer_linea_exacta(const char* fuente, int linea, char* buf, size_t cap) {
    if (!fuente || linea < 0) { buf[0] = '\0'; return; }

    const char* inicio = fuente;
    for (int i = 0; i < linea && *inicio; i++) {
        inicio = strchr(inicio, '\n');
        if (!inicio) { buf[0] = '\0'; return; }
        inicio++;
    }

    const char* fin = inicio;
    while (*fin && *fin != '\n') fin++;

    size_t len = fin - inicio;
    if (len >= cap) len = cap - 1;
    memcpy(buf, inicio, len);
    buf[len] = '\0';
}

// Busca el nodo AST en la posición dada (línea, columna)
static void buscar_nodo_en_posicion(const void* ast_root, int linea, int columna, char* out_tipo, size_t cap) {
    (void)ast_root; (void)linea; (void)columna;
    snprintf(out_tipo, cap, "NodoAST(pos=%d:%d)", linea, columna);
}

// ============================================================
// API principal (v1 — herencia existente)
// ============================================================

int synapse_rag_extraer_contexto(const SynapseRagInput* input, SynapseRagContexto* out) {
    if (!input || !out) return -1;

    memset(out, 0, sizeof(SynapseRagContexto));

    // 1. Extraer ventana de contexto (11 líneas centradas en la actual)
    out->contexto_archivo = (char*)malloc(2048);
    if (out->contexto_archivo) {
        extraer_ventana_contexto(input->fuente, input->linea, out->contexto_archivo, 2048);
    }

    // 2. Extraer línea exacta
    out->linea_actual = (char*)malloc(512);
    if (out->linea_actual) {
        extraer_linea_exacta(input->fuente, input->linea, out->linea_actual, 512);
    }

    // 3. Copiar diagnósticos
    out->diagnosticos = rag_strdup(input->diagnosticos ? input->diagnosticos : "Sin diagnósticos");

    // 4. Buscar nodo AST en posición
    out->nodo_actual_tipo = (char*)malloc(128);
    if (out->nodo_actual_tipo) {
        buscar_nodo_en_posicion(input->ast_root, input->linea, input->columna, out->nodo_actual_tipo, 128);
    }

    // 5. Negociación n_ctx — partición 30/70 estricta
    out->n_ctx_modelo = input->n_ctx_modelo > 0 ? input->n_ctx_modelo : RAG_N_CTX_DEFAULT;
    out->max_tokens_inyectados = synapse_rag_calcular_max_tokens(out->n_ctx_modelo, RAG_RATIO_INYECCION_DEFAULT);
    out->max_tokens_generacion = out->n_ctx_modelo - out->max_tokens_inyectados;
    if (out->max_tokens_generacion < 64) out->max_tokens_generacion = 64;

    return 0;
}

void synapse_rag_liberar_contexto(SynapseRagContexto* ctx) {
    if (!ctx) return;
    free(ctx->contexto_archivo);
    free(ctx->linea_actual);
    free(ctx->diagnosticos);
    free(ctx->nodo_actual_tipo);
    memset(ctx, 0, sizeof(SynapseRagContexto));
}

int synapse_rag_construir_prompt(const SynapseRagContexto* ctx, char* buf, size_t cap) {
    if (!ctx || !buf || cap < 512) return -1;

    size_t pos = 0;
    buf[0] = '\0';

    rag_append(buf, &pos, cap, "[CONTEXTO]:\n");
    rag_append(buf, &pos, cap, ctx->contexto_archivo ? ctx->contexto_archivo : "N/A");
    rag_append(buf, &pos, cap, "\n[LINEA]: ");
    rag_append(buf, &pos, cap, ctx->linea_actual ? ctx->linea_actual : "N/A");
    rag_append(buf, &pos, cap, "\n[AST]: ");
    rag_append(buf, &pos, cap, ctx->nodo_actual_tipo ? ctx->nodo_actual_tipo : "N/A");
    rag_append(buf, &pos, cap, "\n[DIAG]: ");
    rag_append(buf, &pos, cap, ctx->diagnosticos ? ctx->diagnosticos : "N/A");

    rag_append(buf, &pos, cap, "\n\nExplica la linea en espanol. Max: ");
    char tb[32];
    snprintf(tb, sizeof(tb), "%d tokens.", ctx->max_tokens_inyectados);
    rag_append(buf, &pos, cap, tb);

    return 0;
}

int synapse_rag_leer_n_ctx_desde_props(const char* props_json, int* out_n_ctx) {
    if (!props_json || !out_n_ctx) return -1;

    const char* p = strstr(props_json, "\"n_ctx\"");
    if (!p) return -1;

    p = strchr(p, ':');
    if (!p) return -1;
    p++;
    while (*p == ' ' || *p == '\t') p++;

    *out_n_ctx = atoi(p);
    return (*out_n_ctx > 0) ? 0 : -1;
}

int synapse_rag_calcular_max_tokens(int n_ctx, float ratio) {
    if (n_ctx <= 0) return 128;
    if (ratio <= 0.0f) ratio = RAG_RATIO_INYECCION_DEFAULT;
    if (ratio > 0.5f) ratio = 0.5f;
    int max = (int)(n_ctx * ratio);
    if (max < 64) max = 64;
    if (max > RAG_MAX_TOKENS_INYECTADOS) max = RAG_MAX_TOKENS_INYECTADOS;
    return max;
}

// ============================================================
// API de Indexación Semántica (v2 — nuevo)
// ============================================================

// Estadísticas globales del pipeline
static RagEstadisticas _rag_stats = {0};

void synapse_rag_inicializar_indice(RagIndex* idx, int embedding_dim) {
    if (!idx) return;
    memset(idx, 0, sizeof(RagIndex));
    idx->num_chunks = 0;
    idx->embedding_dim = (embedding_dim > 0) ? embedding_dim : RAG_EMBEDDING_DIM_DEFAULT;
    idx->embedding_cache = NULL;
}

void synapse_rag_liberar_indice(RagIndex* idx) {
    if (!idx) return;
    for (int i = 0; i < idx->num_chunks; i++) {
        free(idx->chunks[i].texto);
        free(idx->chunks[i].embedding);
    }
    free(idx->embedding_cache);
    memset(idx, 0, sizeof(RagIndex));
}

int synapse_rag_indexar_chunk(RagIndex* idx, const RagChunk* chunk) {
    if (!idx || !chunk) return -1;
    if (idx->num_chunks >= RAG_MAX_CHUNKS) return -1;

    RagChunk* dst = &idx->chunks[idx->num_chunks];
    dst->texto = rag_strdup(chunk->texto);
    dst->longitud = chunk->longitud;
    dst->linea_inicio = chunk->linea_inicio;
    dst->linea_fin = chunk->linea_fin;
    dst->embedding_dim = chunk->embedding_dim;
    dst->puntuacion = 0.0f;
    strncpy(dst->tipo_nodo, chunk->tipo_nodo, 63);
    dst->tipo_nodo[63] = '\0';

    // Copy embedding if present
    if (chunk->embedding && chunk->embedding_dim > 0) {
        dst->embedding = (float*)malloc(chunk->embedding_dim * sizeof(float));
        if (dst->embedding) {
            memcpy(dst->embedding, chunk->embedding, chunk->embedding_dim * sizeof(float));
        }
    } else {
        dst->embedding = NULL;
    }

    // Rebuild embedding cache
    int dim = idx->embedding_dim;
    free(idx->embedding_cache);
    idx->embedding_cache = (float*)calloc(idx->num_chunks + 1, dim * sizeof(float));
    if (idx->embedding_cache) {
        for (int i = 0; i <= idx->num_chunks; i++) {
            if (idx->chunks[i].embedding) {
                memcpy(&idx->embedding_cache[i * dim], idx->chunks[i].embedding, dim * sizeof(float));
            }
        }
    }

    int index = idx->num_chunks;
    idx->num_chunks++;
    _rag_stats.chunks_indexados++;
    return index;
}

// Divide un texto fuente en chunks coherentes (por línea)
int synapse_rag_indexar_texto(RagIndex* idx, const char* fuente,
                               const char* nombre_archivo) {
    (void)nombre_archivo;
    if (!idx || !fuente) return -1;

    const char* p = fuente;
    int num_chunks_creados = 0;

    while (*p && idx->num_chunks < RAG_MAX_CHUNKS) {
        // Skip blank lines
        while (*p == '\n' || *p == '\r') p++;
        if (!*p) break;

        // Record start of chunk
        const char* chunk_start = p;
        int linea_inicio = 0;
        { const char* l = fuente; while (l < chunk_start) { if (*l == '\n') linea_inicio++; l++; } }

        // Read up to CHUNK_SIZE_MAX chars or until next function/struct definition
        const char* chunk_end = chunk_start;
        int chars = 0;
        int last_newline = 0;

        while (*chunk_end && chars < RAG_CHUNK_SIZE_MAX) {
            if (*chunk_end == '\n') { last_newline = chars; }
            chars++;
            // Break at function/struct boundaries
            if (chars > RAG_CHUNK_SIZE_MIN &&
                ((strncmp(chunk_end, "\nfn ", 4) == 0) ||
                 (strncmp(chunk_end, "\nestructura ", 12) == 0))) {
                break;
            }
            chunk_end++;
        }

        // If we hit max size, cut at last newline
        if (chars >= RAG_CHUNK_SIZE_MAX && last_newline > RAG_CHUNK_SIZE_MIN) {
            chunk_end = chunk_start + last_newline;
        }

        size_t len = chunk_end - chunk_start;
        if (len > 0) {
            char* chunk_text = (char*)malloc(len + 1);
            if (chunk_text) {
                memcpy(chunk_text, chunk_start, len);
                chunk_text[len] = '\0';

                // Detect node type from first line
                char tipo_nodo[64] = "bloque";
                const char* first_line = chunk_text;
                if (strncmp(first_line, "fn ", 3) == 0) {
                    snprintf(tipo_nodo, 64, "funcion");
                } else if (strncmp(first_line, "estructura ", 11) == 0) {
                    snprintf(tipo_nodo, 64, "estructura");
                } else if (strncmp(first_line, "importar ", 9) == 0) {
                    snprintf(tipo_nodo, 64, "importacion");
                } else if (strncmp(first_line, "constante ", 10) == 0) {
                    snprintf(tipo_nodo, 64, "constante");
                }

                // Prepare chunk (embedding will be computed by caller)
                RagChunk c;
                memset(&c, 0, sizeof(c));
                c.texto = chunk_text;     // ownership transferred to RagChunk
                c.longitud = (int)len;
                c.linea_inicio = linea_inicio;
                c.linea_fin = linea_inicio; // approximate
                c.embedding_dim = 0;
                c.embedding = NULL;
                strncpy(c.tipo_nodo, tipo_nodo, 63);
                c.tipo_nodo[63] = '\0';

                int rc = synapse_rag_indexar_chunk(idx, &c);
                if (rc >= 0) num_chunks_creados++;
                else free(chunk_text);  // ownership not taken
            }
        }

        p = chunk_end;
    }

    return num_chunks_creados;
}

int synapse_rag_buscar_similares(const RagIndex* idx,
                                  const float* query_embedding,
                                  int query_dim,
                                  RagResultados* resultados) {
    if (!idx || !query_embedding || !resultados) return -1;
    if (idx->num_chunks <= 0 || query_dim <= 0) return 0;

    memset(resultados, 0, sizeof(RagResultados));

    int dim = (query_dim < idx->embedding_dim) ? query_dim : idx->embedding_dim;

    // For each chunk, compute cosine similarity
    for (int i = 0; i < idx->num_chunks; i++) {
        RagChunk* chunk = &idx->chunks[i];
        if (!chunk->embedding) continue;

        float sim = synapse_rag_coseno_similitud(query_embedding, chunk->embedding, dim);
        chunk->puntuacion = sim;

        // Insert into top-K results
        int insert_at = resultados->num_resultados;
        for (int j = 0; j < resultados->num_resultados; j++) {
            if (sim > resultados->puntuaciones[j]) {
                insert_at = j;
                break;
            }
        }

        if (insert_at < RAG_TOP_K_SIMILARES) {
            // Shift elements right
            if (resultados->num_resultados < RAG_TOP_K_SIMILARES) {
                resultados->num_resultados++;
            }
            for (int j = resultados->num_resultados - 1; j > insert_at; j--) {
                resultados->resultados[j] = resultados->resultados[j - 1];
                resultados->puntuaciones[j] = resultados->puntuaciones[j - 1];
            }
            resultados->resultados[insert_at] = chunk;
            resultados->puntuaciones[insert_at] = sim;
        }
    }

    _rag_stats.busquedas_realizadas++;
    return resultados->num_resultados;
}

float synapse_rag_coseno_similitud(const float* a, const float* b, int dim) {
    if (!a || !b || dim <= 0) return 0.0f;

    double dot = 0.0, norm_a = 0.0, norm_b = 0.0;
    for (int i = 0; i < dim; i++) {
        dot += (double)a[i] * (double)b[i];
        norm_a += (double)a[i] * (double)a[i];
        norm_b += (double)b[i] * (double)b[i];
    }

    if (norm_a < 1e-10 || norm_b < 1e-10) return 0.0f;
    return (float)(dot / (sqrt(norm_a) * sqrt(norm_b)));
}

int synapse_rag_negociar_n_ctx(int n_ctx_modelo, int num_chunks_relevantes,
                                int tamano_total_chunks,
                                float* out_ratio_usado) {
    if (n_ctx_modelo <= 0) n_ctx_modelo = RAG_N_CTX_DEFAULT;

    // Estimate token count: ~4 chars per token
    int tokens_chunks = tamano_total_chunks / 4;
    if (tokens_chunks < 32) tokens_chunks = 32;

    // Base ratio: 30%
    float ratio = RAG_RATIO_INYECCION_DEFAULT;

    // Adjust ratio based on chunk count and size
    if (num_chunks_relevantes > 5) {
        ratio += 0.05f;  // More chunks need more context
    }
    if (tokens_chunks > n_ctx_modelo / 2) {
        ratio = (float)tokens_chunks / (float)n_ctx_modelo;
    }

    // Clamp ratio
    if (ratio < 0.15f) ratio = 0.15f;
    if (ratio > 0.5f) ratio = 0.5f;

    int max_tokens = (int)(n_ctx_modelo * ratio);
    if (max_tokens < 64) max_tokens = 64;
    if (max_tokens > RAG_MAX_TOKENS_INYECTADOS) max_tokens = RAG_MAX_TOKENS_INYECTADOS;

    if (out_ratio_usado) *out_ratio_usado = ratio;

    _rag_stats.tokens_inyectados_promedio =
        (_rag_stats.tokens_inyectados_promedio + max_tokens) / 2;

    return max_tokens;
}

RagEstadisticas synapse_rag_obtener_estadisticas(void) {
    return _rag_stats;
}

// ============================================================
// Integración con Fine-Tuning (M13.4)
// ============================================================

// Re-rank de resultados RAG usando puntuación ajustada por fine-tuning
int synapse_rag_re_rankear_con_ft(void* sesion_ft, const RagIndex* idx,
                                   const char* consulta,
                                   RagResultados* resultados_originales,
                                   RagResultados* resultados_ajustados) {
    (void)sesion_ft;
    (void)idx;
    (void)consulta;
    if (!resultados_originales || !resultados_ajustados) return -1;

    // Copiar resultados originales como base
    memcpy(resultados_ajustados, resultados_originales, sizeof(RagResultados));

    // Aplicar ajuste: las puntuaciones se modifican según el conocimiento
    // del fine-tuning (en implementación real, se usaría el modelo fine-tuned
    // para re-rankear). Por ahora, aplicamos un factor de corrección
    // basado en el tipo de nodo.
    for (int i = 0; i < resultados_ajustados->num_resultados; i++) {
        float ajuste = 1.0f;
        RagChunk* chunk = resultados_ajustados->resultados[i];
        if (chunk) {
            // Los chunks de tipo función reciben un boost (más relevantes)
            if (strcmp(chunk->tipo_nodo, "funcion") == 0) {
                ajuste = 1.15f;
            } else if (strcmp(chunk->tipo_nodo, "estructura") == 0) {
                ajuste = 1.10f;
            }
        }
        resultados_ajustados->puntuaciones[i] *= ajuste;
        if (resultados_ajustados->puntuaciones[i] > 1.0f) {
            resultados_ajustados->puntuaciones[i] = 1.0f;
        }
    }

    return resultados_ajustados->num_resultados;
}

// Genera embedding contextual para RAG (con sesgo de fine-tuning)
float* synapse_rag_generar_embedding_ft(void* sesion_ft, const char* texto,
                                         int* out_dim) {
    (void)sesion_ft;
    if (!texto || !out_dim) return NULL;

    int len = (int)strlen(texto);
    int dim = 64;  // Dimensión reducida para embedding contextual
    *out_dim = dim;

    float* emb = (float*)calloc((size_t)dim, sizeof(float));
    if (!emb) return NULL;

    // Generar embedding basado en contenido (simplificado)
    // En producción, esto usaría el encoder del modelo fine-tuned
    for (int i = 0; i < dim && i < len; i++) {
        emb[i % dim] += (float)(unsigned char)texto[i] / 256.0f;
    }

    // Normalizar
    float norm = 0.0f;
    for (int i = 0; i < dim; i++) norm += emb[i] * emb[i];
    if (norm > 0.0f) {
        norm = sqrtf(norm);
        for (int i = 0; i < dim; i++) emb[i] /= norm;
    }

    return emb;
}
