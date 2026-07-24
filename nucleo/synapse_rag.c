// synapse_rag.c — Pipeline RAG quirúrgico para extracción de contexto AST
// Parte del núcleo Synapse LSP nativo — C99

#include "synapse_rag.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// Helpers internos
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
// Simplificado: busca en el AST el nodo que contiene la posición
static void buscar_nodo_en_posicion(const void* ast_root, int linea, int columna, char* out_tipo, size_t cap) {
    (void)ast_root; (void)linea; (void)columna;
    // Implementación simplificada: en producción recorrería el AST
    // Por ahora retorna tipo genérico
    snprintf(out_tipo, cap, "NodoAST(pos=%d:%d)", linea, columna);
}

// --- API Pública ---

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

    // 5. Negociación n_ctx
    out->n_ctx_modelo = input->n_ctx_modelo > 0 ? input->n_ctx_modelo : RAG_N_CTX_DEFAULT;
    out->max_tokens_inyectados = synapse_rag_calcular_max_tokens(out->n_ctx_modelo, RAG_RATIO_INYECCION_DEFAULT);

    return 0;
}

void synapse_rag_liberar_contexto(SynapseRagContexto* ctx) {
    if (!ctx) return;
    free(ctx->contexto_archivo);
    free(ctx->linea_actual);
    free(ctx->diagnosticos);
    free(ctx->nodo_actual_tipo);
    ctx->contexto_archivo = NULL;
    ctx->linea_actual = NULL;
    ctx->diagnosticos = NULL;
    ctx->nodo_actual_tipo = NULL;
    ctx->n_ctx_modelo = 0;
    ctx->max_tokens_inyectados = 0;
}

int synapse_rag_construir_prompt(const SynapseRagContexto* ctx, char* buf, size_t cap) {
    if (!ctx || !buf || cap < 512) return -1;

    size_t pos = 0;
    buf[0] = '\0';

    rag_append(buf, &pos, cap, "[CONTEXTO_ARCHIVO]:\n");
    rag_append(buf, &pos, cap, ctx->contexto_archivo ? ctx->contexto_archivo : "N/A");
    rag_append(buf, &pos, cap, "\n\n[LINEA_ACTUAL]:\n");
    rag_append(buf, &pos, cap, ctx->linea_actual ? ctx->linea_actual : "N/A");
    rag_append(buf, &pos, cap, "\n\n[NODO_AST]:\n");
    rag_append(buf, &pos, cap, ctx->nodo_actual_tipo ? ctx->nodo_actual_tipo : "N/A");
    rag_append(buf, &pos, cap, "\n\n[DIAGNOSTICOS]:\n");
    rag_append(buf, &pos, cap, ctx->diagnosticos ? ctx->diagnosticos : "N/A");
    rag_append(buf, &pos, cap, "\n\nInstrucción: Explica el código en la línea actual en español, considerando el contexto, el nodo AST y los diagnósticos. Sé conciso y técnico. Respuesta máxima: ");

    char token_buf[32];
    snprintf(token_buf, sizeof(token_buf), "%d tokens.", ctx->max_tokens_inyectados);
    rag_append(buf, &pos, cap, token_buf);

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