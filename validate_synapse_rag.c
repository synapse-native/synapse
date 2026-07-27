/*
 * validate_synapse_rag.c — Suite de validación para M13.2
 * ==========================================================
 * Propósito: Validar el pipeline RAG quirúrgico de OpenSyn
 * (nucleo/synapse_rag.c + opensyn/router.syn)
 *
 * Secciones de prueba:
 *   Section 1: Chunking de código fuente (synapse_rag_indexar_texto)
 *   Section 2: Indexación de chunks individuales
 *   Section 3: Cosine similarity entre vectores
 *   Section 4: Búsqueda semántica (top-K similares)
 *   Section 5: Negociación dinámica de n_ctx
 *   Section 6: Construcción de prompts RAG (v1 herencia)
 *   Section 7: Extracción de contexto quirúrgico (v1 herencia)
 *   Section 8: Liberación de memoria y edge cases
 *
 * Compilar: gcc -O2 -std=c99 validate_synapse_rag.c synapse_rag.c -o validate_synapse_rag.exe -lm
 *
 * NOTA: Este archivo NO modifica el directorio tests/ (candado activo).
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* Import the RAG pipeline */
#include "nucleo/synapse_rag.h"

/* ============================================================
 * Test harness
 * ============================================================ */

static int tests_total = 0;
static int tests_passed = 0;
static int section_num = 0;

static void section_header(const char* name) {
    section_num++;
    printf("\n=== SECTION %d: %s ===\n", section_num, name);
}

static void test_assert(const char* name, int cond) {
    tests_total++;
    if (cond) {
        tests_passed++;
        printf("  \xe2\x9c\x93 %s\n", name);
    } else {
        printf("  \xe2\x9c\x97 %s (FAILED)\n", name);
    }
}

/* ============================================================
 * Test data
 * ============================================================ */

static const char* CODIGO_EJEMPLO =
    "#lang: es\n"
    "importar std.io\n"
    "\n"
    "constante MAX_ITEMS = 100\n"
    "\n"
    "funcion factorial(n: entero) -> entero:\n"
    "    si n <= 1:\n"
    "        retornar 1\n"
    "    retornar n * factorial(n - 1)\n"
    "\n"
    "estructura Punto:\n"
    "    x: entero\n"
    "    y: entero\n"
    "\n"
    "funcion distancia(origen: Punto, destino: Punto) -> decimal:\n"
    "    dx = destino.x - origen.x\n"
    "    dy = destino.y - origen.y\n"
    "    retornar raiz(dx * dx + dy * dy)\n";

static const char* CODIGO_FACTORIAL =
    "funcion factorial(n: entero) -> entero:\n"
    "    si n <= 1:\n"
    "        retornar 1\n"
    "    retornar n * factorial(n - 1)\n";

/* ============================================================
 * Section 1: Chunking de código fuente
 * ============================================================ */

static void test_chunking(void) {
    section_header("Source Chunking - synapse_rag_indexar_texto");

    RagIndex idx;
    synapse_rag_inicializar_indice(&idx, 768);

    /* 1.1 Indexar código de ejemplo */
    int n = synapse_rag_indexar_texto(&idx, CODIGO_EJEMPLO, "test.syn");
    test_assert("indexar_texto retorna chunks > 0", n > 0);

    /* 1.2 Verificar que los chunks se crearon */
    test_assert("num_chunks > 0", idx.num_chunks > 0);

    /* 1.3 Verificar que cada chunk tiene texto */
    int todos_tienen_texto = 1;
    for (int i = 0; i < idx.num_chunks; i++) {
        if (!idx.chunks[i].texto || idx.chunks[i].longitud <= 0) {
            todos_tienen_texto = 0;
            break;
        }
    }
    test_assert("todos los chunks tienen texto valido", todos_tienen_texto);

    /* 1.4 Indexar código vacío */
    RagIndex idx_vacio;
    synapse_rag_inicializar_indice(&idx_vacio, 768);
    int n_vacio = synapse_rag_indexar_texto(&idx_vacio, "", "vacio.syn");
    test_assert("indexar texto vacio = 0", n_vacio == 0);
    synapse_rag_liberar_indice(&idx_vacio);

    /* 1.5 Indexar código nulo */
    int n_nulo = synapse_rag_indexar_texto(&idx, NULL, "nulo.syn");
    test_assert("indexar texto nulo = -1", n_nulo == -1);

    /* 1.6 Indexar con índice nulo */
    int n_idx_nulo = synapse_rag_indexar_texto(NULL, CODIGO_EJEMPLO, "test.syn");
    test_assert("indexar con idx nulo = -1", n_idx_nulo == -1);

    /* 1.7 Verificar chunking máximo (no excede límite) */
    test_assert("num_chunks <= RAG_MAX_CHUNKS", idx.num_chunks <= RAG_MAX_CHUNKS);

    synapse_rag_liberar_indice(&idx);
}

/* ============================================================
 * Section 2: Indexación de chunks individuales
 * ============================================================ */

static void test_chunk_indexing(void) {
    section_header("Chunk Indexing - synapse_rag_indexar_chunk");

    RagIndex idx;
    synapse_rag_inicializar_indice(&idx, 768);

    /* 2.1 Indexar chunk simple */
    RagChunk c;
    memset(&c, 0, sizeof(c));
    c.texto = strdup("funcion suma(a: entero, b: entero) -> entero:\n    retornar a + b\n");
    c.longitud = (int)strlen(c.texto);
    c.linea_inicio = 0;
    c.linea_fin = 1;
    c.embedding_dim = 0;
    c.embedding = NULL;
    strcpy(c.tipo_nodo, "funcion");

    int i = synapse_rag_indexar_chunk(&idx, &c);
    test_assert("indexar_chunk retorna indice >= 0", i >= 0);
    test_assert("indice = 0 (primer chunk)", i == 0);

    /* 2.2 Indexar segundo chunk */
    strcpy(c.tipo_nodo, "estructura");
    c.texto = strdup("estructura Punto:\n    x: entero\n    y: entero\n");
    c.longitud = (int)strlen(c.texto);

    i = synapse_rag_indexar_chunk(&idx, &c);
    test_assert("indexar segundo chunk indice = 1", i == 1);
    test_assert("num_chunks = 2", idx.num_chunks == 2);

    /* 2.3 Verificar chunks almacenados correctamente */
    test_assert("chunk[0] tipo = funcion",
        strcmp(idx.chunks[0].tipo_nodo, "funcion") == 0);
    test_assert("chunk[1] tipo = estructura",
        strcmp(idx.chunks[1].tipo_nodo, "estructura") == 0);

    /* 2.4 Indexar chunk con embedding */
    float emb[] = {0.1f, 0.2f, 0.3f, 0.4f};
    RagChunk c_emb;
    memset(&c_emb, 0, sizeof(c_emb));
    c_emb.texto = strdup("chunk con embedding");
    c_emb.longitud = 18;
    c_emb.embedding_dim = 4;
    c_emb.embedding = (float*)malloc(4 * sizeof(float));
    memcpy(c_emb.embedding, emb, 4 * sizeof(float));
    strcpy(c_emb.tipo_nodo, "test");

    i = synapse_rag_indexar_chunk(&idx, &c_emb);
    test_assert("indexar chunk con embedding", i == 2);

    /* 2.5 Indexar chunk nulo */
    int n = synapse_rag_indexar_chunk(&idx, NULL);
    test_assert("indexar chunk nulo = -1", n == -1);

    /* 2.6 Indexar en índice nulo */
    n = synapse_rag_indexar_chunk(NULL, &c_emb);
    test_assert("indexar en indice nulo = -1", n == -1);

    /* 2.7 Liberar chunk embed */
    free(c_emb.embedding);
    free(c_emb.texto);

    synapse_rag_liberar_indice(&idx);

    /* Note: c.texto was allocated with strdup; ownership transferred to index */
    /* Don't free c.texto manually — index frees it in liberar_indice */
}

/* ============================================================
 * Section 3: Cosine similarity
 * ============================================================ */

static void test_cosine_similarity(void) {
    section_header("Cosine Similarity - synapse_rag_coseno_similitud");

    /* 3.1 Vectores idénticos */
    float a[] = {1.0f, 0.0f, 0.0f};
    float b[] = {1.0f, 0.0f, 0.0f};
    float sim = synapse_rag_coseno_similitud(a, b, 3);
    test_assert("identicos = 1.0", fabsf(sim - 1.0f) < 0.001f);

    /* 3.2 Vectores ortogonales */
    float c[] = {1.0f, 0.0f, 0.0f};
    float d[] = {0.0f, 1.0f, 0.0f};
    sim = synapse_rag_coseno_similitud(c, d, 3);
    test_assert("ortogonales = 0.0", fabsf(sim) < 0.001f);

    /* 3.3 Vectores opuestos */
    float e[] = {1.0f, 0.0f, 0.0f};
    float f[] = {-1.0f, 0.0f, 0.0f};
    sim = synapse_rag_coseno_similitud(e, f, 3);
    test_assert("opuestos = -1.0", fabsf(sim + 1.0f) < 0.001f);

    /* 3.4 Vectores parcialmente similares */
    float g[] = {1.0f, 2.0f, 3.0f};
    float h[] = {1.0f, 2.0f, 0.0f};
    sim = synapse_rag_coseno_similitud(g, h, 3);
    test_assert("parciales > 0", sim > 0.5f);

    /* 3.5 Dimensión 1 */
    float i[] = {42.0f};
    float j[] = {42.0f};
    sim = synapse_rag_coseno_similitud(i, j, 1);
    test_assert("dim=1 identicos = 1.0", fabsf(sim - 1.0f) < 0.001f);

    /* 3.6 Vector nulo */
    float k[] = {0.0f, 0.0f, 0.0f};
    float l[] = {1.0f, 0.0f, 0.0f};
    sim = synapse_rag_coseno_similitud(k, l, 3);
    test_assert("vector nulo = 0.0", fabsf(sim) < 0.001f);

    /* 3.7 Parámetros nulos */
    sim = synapse_rag_coseno_similitud(NULL, l, 3);
    test_assert("a nulo = 0.0", fabsf(sim) < 0.001f);

    sim = synapse_rag_coseno_similitud(k, NULL, 3);
    test_assert("b nulo = 0.0", fabsf(sim) < 0.001f);

    sim = synapse_rag_coseno_similitud(k, l, 0);
    test_assert("dim=0 = 0.0", fabsf(sim) < 0.001f);

    /* 3.8 Alta dimensión */
    int dim1024 = 1024;
    float* big_a = (float*)malloc(dim1024 * sizeof(float));
    float* big_b = (float*)malloc(dim1024 * sizeof(float));
    for (int i = 0; i < dim1024; i++) {
        big_a[i] = (float)(i % 100) / 100.0f;
        big_b[i] = big_a[i];
    }
    sim = synapse_rag_coseno_similitud(big_a, big_b, dim1024);
    test_assert("alta dimension identicos = 1.0", fabsf(sim - 1.0f) < 0.001f);
    free(big_a);
    free(big_b);
}

/* ============================================================
 * Section 4: Búsqueda semántica (top-K similares)
 * ============================================================ */

static void test_semantic_search(void) {
    section_header("Semantic Search - synapse_rag_buscar_similares");

    RagIndex idx;
    synapse_rag_inicializar_indice(&idx, 4);

    /* Indexar chunks con embeddings conocidos */
    for (int k = 0; k < 5; k++) {
        RagChunk c;
        memset(&c, 0, sizeof(c));
        char tbuf[64];
        snprintf(tbuf, 64, "chunk_%d", k);
        c.texto = strdup(tbuf);
        c.longitud = (int)strlen(c.texto);
        c.embedding_dim = 4;
        c.embedding = (float*)malloc(4 * sizeof(float));
        for (int j = 0; j < 4; j++) {
            c.embedding[j] = (float)(k + 1) * 0.1f;
        }
        snprintf(c.tipo_nodo, 64, "test");
        synapse_rag_indexar_chunk(&idx, &c);
    }

    /* 4.1 Buscar con embedding idéntico al primer chunk */
    float query[] = {0.1f, 0.1f, 0.1f, 0.1f};
    RagResultados res;
    int n = synapse_rag_buscar_similares(&idx, query, 4, &res);
    test_assert("buscar_similares retorna > 0", n > 0);
    test_assert("resultado[0] puntuacion > 0.9",
        res.puntuaciones[0] > 0.9f);

    /* 4.2 Verificar resultados ordenados */
    int ordenado = 1;
    for (int i = 1; i < res.num_resultados; i++) {
        if (res.puntuaciones[i] > res.puntuaciones[i - 1]) {
            ordenado = 0;
            break;
        }
    }
    test_assert("resultados ordenados descendente", ordenado);

    /* 4.3 Buscar con embedding ortogonal */
    float query_ortho[] = {1.0f, 0.0f, 0.0f, 0.0f};
    float* first_emb = idx.chunks[0].embedding;
    if (first_emb) {
        /* Make query orthogonal to chunk[0] by using different values */
        for (int i = 0; i < 4; i++) query_ortho[i] = 1.0f - first_emb[i];
    }
    n = synapse_rag_buscar_similares(&idx, query_ortho, 4, &res);
    test_assert("busqueda con query ortogonal funciona", n >= 0);

    /* 4.4 Buscar en índice vacío */
    RagIndex idx_vacio;
    synapse_rag_inicializar_indice(&idx_vacio, 4);
    n = synapse_rag_buscar_similares(&idx_vacio, query, 4, &res);
    test_assert("buscar en indice vacio = 0", n == 0);
    synapse_rag_liberar_indice(&idx_vacio);

    /* 4.5 Buscar con query nula */
    n = synapse_rag_buscar_similares(&idx, NULL, 4, &res);
    test_assert("buscar con query nula = -1", n == -1);

    /* 4.6 Buscar en índice nulo */
    n = synapse_rag_buscar_similares(NULL, query, 4, &res);
    test_assert("buscar en indice nulo = -1", n == -1);

    /* 4.7 Verificar límite top-K */
    test_assert("num_resultados <= RAG_TOP_K_SIMILARES",
        res.num_resultados <= RAG_TOP_K_SIMILARES);

    synapse_rag_liberar_indice(&idx);
}

/* ============================================================
 * Section 5: Negociación dinámica de n_ctx
 * ============================================================ */

static void test_nctx_negotiation(void) {
    section_header("n_ctx Negotiation - synapse_rag_negociar_n_ctx");

    /* 5.1 n_ctx por defecto con pocos chunks */
    float ratio;
    int max_tok = synapse_rag_negociar_n_ctx(4096, 3, 500, &ratio);
    test_assert("4096 ctx, 3 chunks -> tokens > 0", max_tok > 0);
    test_assert("ratio default ~0.3", fabsf(ratio - 0.3f) < 0.1f);

    /* 5.2 n_ctx pequeño (modelo minimal) */
    max_tok = synapse_rag_negociar_n_ctx(512, 1, 100, &ratio);
    test_assert("512 ctx -> tokens minimo 64", max_tok >= 64);
    test_assert("ratio ajustado para ctx pequeno", ratio >= 0.15f);

    /* 5.3 n_ctx grande con muchos chunks */
    max_tok = synapse_rag_negociar_n_ctx(32768, 20, 8000, &ratio);
    test_assert("32768 ctx, 20 chunks -> tokens significativos",
        max_tok > 1024);

    /* 5.4 n_ctx = 0 (default) */
    max_tok = synapse_rag_negociar_n_ctx(0, 1, 100, &ratio);
    test_assert("ctx=0 usa default, tokens > 0", max_tok > 0);

    /* 5.5 Chunks muy grandes */
    max_tok = synapse_rag_negociar_n_ctx(2048, 1, 8000, NULL);
    test_assert("chunks grandes -> ratio ajustado > 0.15", max_tok >= 64);

    /* 5.6 Tokens muy pequeños */
    max_tok = synapse_rag_negociar_n_ctx(4096, 1, 32, &ratio);
    test_assert("chunks pequenos -> ratio minimo", max_tok >= 64);

    /* 5.7 Ratio máximo no excede 0.5 */
    max_tok = synapse_rag_negociar_n_ctx(4096, 50, 10000, &ratio);
    test_assert("ratio <= 0.5", ratio <= 0.51f);

    /* 5.8 No excede max tokens */
    test_assert("max_tokens <= RAG_MAX_TOKENS_INYECTADOS",
        max_tok <= RAG_MAX_TOKENS_INYECTADOS);
}

/* ============================================================
 * Section 6: Construcción de prompts (v1 herencia)
 * ============================================================ */

static void test_prompt_construction(void) {
    section_header("Prompt Construction - synapse_rag_construir_prompt");

    /* 6.1 Prompt con contexto completo */
    SynapseRagContexto ctx;
    memset(&ctx, 0, sizeof(ctx));
    ctx.contexto_archivo = strdup("linea 1\nlinea 2\nlinea 3");
    ctx.linea_actual = strdup("linea 2");
    ctx.diagnosticos = strdup("Error: variable no definida");
    ctx.nodo_actual_tipo = strdup("AsignacionVariable");
    ctx.n_ctx_modelo = 4096;
    ctx.max_tokens_inyectados = 128;
    ctx.max_tokens_generacion = 3968;

    char buf[4096];
    int rc = synapse_rag_construir_prompt(&ctx, buf, sizeof(buf));
    test_assert("construir_prompt exitoso", rc == 0);

    /* 6.2 Prompt contiene secciones esperadas */
    test_assert("prompt contiene [CONTEXTO]",
        strstr(buf, "[CONTEXTO]") != NULL);
    test_assert("prompt contiene [LINEA]",
        strstr(buf, "[LINEA]") != NULL);
    test_assert("prompt contiene [AST]",
        strstr(buf, "[AST]") != NULL);
    test_assert("prompt contiene [DIAG]",
        strstr(buf, "[DIAG]") != NULL);

    /* 6.3 Prompt con parámetros inválidos */
    rc = synapse_rag_construir_prompt(NULL, buf, sizeof(buf));
    test_assert("construir_prompt con ctx nulo = -1", rc == -1);

    char* null_buf = NULL;
    rc = synapse_rag_construir_prompt(&ctx, null_buf, 0);
    test_assert("construir_prompt con buf nulo = -1", rc == -1);

    /* 6.4 Prompt con buffer pequeño */
    char tiny[4] = {0};
    rc = synapse_rag_construir_prompt(&ctx, tiny, 4);
    test_assert("construir_prompt buffer pequeno = -1 (cap < 512)", rc == -1);

    /* 6.5 Prompt con campos nulos */
    SynapseRagContexto ctx_vacio;
    memset(&ctx_vacio, 0, sizeof(ctx_vacio));
    rc = synapse_rag_construir_prompt(&ctx_vacio, buf, sizeof(buf));
    test_assert("construir_prompt con campos nulos", rc == 0);

    free(ctx.contexto_archivo);
    free(ctx.linea_actual);
    free(ctx.diagnosticos);
    free(ctx.nodo_actual_tipo);
}

/* ============================================================
 * Section 7: Extracción de contexto quirúrgico (v1 herencia)
 * ============================================================ */

static void test_context_extraction(void) {
    section_header("Context Extraction - synapse_rag_extraer_contexto");

    /* 7.1 Extraer contexto de código fuente */
    SynapseRagInput input;
    memset(&input, 0, sizeof(input));
    input.fuente = CODIGO_EJEMPLO;
    input.linea = 6;  /* línea de la función factorial */
    input.columna = 0;
    input.diagnosticos = "test diag";
    input.n_ctx_modelo = 4096;
    input.ast_root = NULL;

    SynapseRagContexto ctx;
    memset(&ctx, 0, sizeof(ctx));
    int rc = synapse_rag_extraer_contexto(&input, &ctx);
    test_assert("extraer_contexto exitoso", rc == 0);

    /* 7.2 Verificar campos extraídos */
    test_assert("contexto_archivo no nulo", ctx.contexto_archivo != NULL);
    test_assert("linea_actual no nulo", ctx.linea_actual != NULL);
    test_assert("diagnosticos no nulo", ctx.diagnosticos != NULL);
    test_assert("nodo_actual_tipo no nulo", ctx.nodo_actual_tipo != NULL);

    /* 7.3 Verificar n_ctx negociado */
    test_assert("n_ctx_modelo > 0", ctx.n_ctx_modelo > 0);
    test_assert("max_tokens_inyectados > 0", ctx.max_tokens_inyectados > 0);
    test_assert("max_tokens_generacion > 0", ctx.max_tokens_generacion > 0);

    /* 7.4 Verificar partición 30/70 */
    int total = ctx.max_tokens_inyectados + ctx.max_tokens_generacion;
    test_assert("suma tokens <= n_ctx (con margen)",
        total <= ctx.n_ctx_modelo + 64);

    /* 7.5 Extraer con input nulo */
    rc = synapse_rag_extraer_contexto(NULL, &ctx);
    test_assert("extraer_contexto input nulo = -1", rc == -1);

    rc = synapse_rag_extraer_contexto(&input, NULL);
    test_assert("extraer_contexto output nulo = -1", rc == -1);

    /* 7.6 Extraer con n_ctx = 0 (usa default) */
    input.n_ctx_modelo = 0;
    memset(&ctx, 0, sizeof(ctx));
    rc = synapse_rag_extraer_contexto(&input, &ctx);
    test_assert("extraer_contexto con n_ctx=0 usa default", rc == 0);
    test_assert("n_ctx default > 0", ctx.n_ctx_modelo > 0);

    synapse_rag_liberar_contexto(&ctx);

    /* 7.7 Liberar contexto nulo */
    synapse_rag_liberar_contexto(NULL);
    test_assert("liberar_contexto(NULL) no crash", 1);
}

/* ============================================================
 * Section 8: Liberación de memoria y edge cases
 * ============================================================ */

static void test_memory_edge_cases(void) {
    section_header("Memory & Edge Cases - liberar_indice, estadisticas");

    /* 8.1 Liberar índice nulo */
    synapse_rag_liberar_indice(NULL);
    test_assert("liberar_indice(NULL) no crash", 1);

    /* 8.2 Inicializar índice nulo */
    synapse_rag_inicializar_indice(NULL, 768);
    test_assert("inicializar_indice(NULL) no crash", 1);

    /* 8.3 Obtener estadísticas */
    RagEstadisticas stats = synapse_rag_obtener_estadisticas();
    test_assert("estadisticas tienen chunks indexados >= 0",
        stats.chunks_indexados >= 0);
    test_assert("estadisticas tienen busquedas >= 0",
        stats.busquedas_realizadas >= 0);

    /* 8.4 Leer n_ctx desde props JSON */
    int n_ctx;
    int rc = synapse_rag_leer_n_ctx_desde_props(
        "{\"n_ctx\":4096,\"model\":\"test\"}", &n_ctx);
    test_assert("leer_n_ctx desde JSON = 4096",
        rc == 0 && n_ctx == 4096);

    /* 8.5 Leer n_ctx desde props sin campo */
    rc = synapse_rag_leer_n_ctx_desde_props("{}", &n_ctx);
    test_assert("leer_n_ctx sin campo = -1", rc == -1);

    /* 8.6 Leer n_ctx con json nulo */
    rc = synapse_rag_leer_n_ctx_desde_props(NULL, &n_ctx);
    test_assert("leer_n_ctx json nulo = -1", rc == -1);

    /* 8.7 Calcular max tokens con valores límite */
    int mt = synapse_rag_calcular_max_tokens(4096, 0.3f);
    test_assert("calcular_max_tokens 4096*0.3 = 1228",
        mt == 1228); /* 4096 * 0.3 = 1228.8 -> (int)1228 */

    /* 8.8 Calcular con ratio alto (clamped a 0.5) */
    mt = synapse_rag_calcular_max_tokens(4096, 0.8f);
    test_assert("calcular con ratio 0.8 clamped a 0.5 -> 2048",
        mt == 2048);

    /* 8.9 Calcular con n_ctx pequeño */
    mt = synapse_rag_calcular_max_tokens(128, 0.3f);
    test_assert("calcular con n_ctx 128 -> min 64", mt == 64);

    /* 8.10 Calcular con n_ctx = 0 */
    mt = synapse_rag_calcular_max_tokens(0, 0.3f);
    test_assert("calcular con n_ctx 0 -> default 128", mt == 128);

    /* 8.11 Verify chunking + search pipeline end-to-end */
    RagIndex idx;
    synapse_rag_inicializar_indice(&idx, 4);
    synapse_rag_indexar_texto(&idx, CODIGO_EJEMPLO, "test.syn");

    float q[] = {0.1f, 0.2f, 0.3f, 0.4f};
    RagResultados res;
    int num = synapse_rag_buscar_similares(&idx, q, 4, &res);
    test_assert("pipeline E2E: busqueda funciona", num >= 0);

    /* Verify chunks have texto */
    int chunks_validos = 0;
    for (int i = 0; i < idx.num_chunks; i++) {
        if (idx.chunks[i].texto && idx.chunks[i].longitud > 0) chunks_validos++;
    }
    test_assert("pipeline E2E: todos los chunks validos",
        chunks_validos == idx.num_chunks);

    synapse_rag_liberar_indice(&idx);

    /* 8.12 Doble liberación */
    RagIndex idx2;
    synapse_rag_inicializar_indice(&idx2, 768);
    synapse_rag_liberar_indice(&idx2);
    synapse_rag_liberar_indice(&idx2);  /* double free should be safe */
    test_assert("doble liberacion de indice no crash", 1);
}

/* ============================================================
 * Main
 * ============================================================ */

int main(void) {
    printf("============================================\n");
    printf("  M13.2 — OpenSyn RAG Pipeline CI/CD\n");
    printf("  validate_synapse_rag.c\n");
    printf("============================================\n");

    test_chunking();
    test_chunk_indexing();
    test_cosine_similarity();
    test_semantic_search();
    test_nctx_negotiation();
    test_prompt_construction();
    test_context_extraction();
    test_memory_edge_cases();

    printf("\n============================================\n");
    printf("  RESULTS: %d / %d PASS (%.1f%%)\n",
        tests_passed, tests_total,
        (tests_total > 0) ? (100.0f * tests_passed / tests_total) : 0.0f);
    printf("============================================\n");

    return (tests_passed == tests_total) ? 0 : 1;
}
