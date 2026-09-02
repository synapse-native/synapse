// validate_synapse_rag.c — Harness de validación del pipeline RAG para CI
// cumple Manual 9 §1: harness de validación runtime
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "nucleo/synapse_rag.h"

static int tests_passed = 0;
static int tests_failed = 0;

#define ASSERT_OK(expr) do { \
    int _r = (expr); \
    if (_r == 0) { tests_passed++; } \
    else { tests_failed++; fprintf(stderr, "FAIL: %s (line %d)\n", #expr, __LINE__); } \
} while (0)

static void test_coseno_similitud(void) {
    float a[4] = {1.0f, 0.0f, 0.0f, 0.0f};
    float b[4] = {1.0f, 0.0f, 0.0f, 0.0f};
    float c[4] = {0.0f, 1.0f, 0.0f, 0.0f};
    float s_ab = synapse_rag_coseno_similitud(a, b, 4);
    float s_ac = synapse_rag_coseno_similitud(a, c, 4);
    ASSERT_OK(fabsf(s_ab - 1.0f) < 0.0001f);
    ASSERT_OK(fabsf(s_ac - 0.0f) < 0.0001f);
}

static void test_calcular_max_tokens(void) {
    ASSERT_OK(synapse_rag_calcular_max_tokens(4096, 0.3f) == 1228);
    ASSERT_OK(synapse_rag_calcular_max_tokens(2048, 0.5f) == 1024);
    ASSERT_OK(synapse_rag_calcular_max_tokens(0, 0.3f) > 0);
}

static void test_indice_vacio(void) {
    RagIndex idx;
    memset(&idx, 0, sizeof(idx));
    synapse_rag_inicializar_indice(&idx, 768);
    ASSERT_OK(idx.embedding_dim == 768);
    ASSERT_OK(idx.num_chunks == 0);
    RagResultados res;
    int n = synapse_rag_buscar_similares(&idx, NULL, 5, &res);
    ASSERT_OK(n == 0);
    synapse_rag_liberar_indice(&idx);
}

static void test_estadisticas(void) {
    RagEstadisticas est = synapse_rag_obtener_estadisticas();
    ASSERT_OK(est.chunks_indexados >= 0);
    ASSERT_OK(est.busquedas_realizadas >= 0);
}

static void test_n_ctx_props(void) {
    int n_ctx = 0;
    const char* props = "{\"n_ctx\": 4096}";
    ASSERT_OK(synapse_rag_leer_n_ctx_desde_props(props, &n_ctx) == 0);
    ASSERT_OK(n_ctx == 4096);
}

int main(void) {
    printf("=== validate_synapse_rag ===\n");
    test_coseno_similitud();
    test_calcular_max_tokens();
    test_indice_vacio();
    test_estadisticas();
    test_n_ctx_props();
    printf("Pasados: %d / Fallos: %d\n", tests_passed, tests_failed);
    return tests_failed == 0 ? 0 : 1;
}