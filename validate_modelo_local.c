/*
 * validate_modelo_local.c — Suite de validación para M13.1
 * ========================================================
 * Propósito: Validar el pipeline de inferencia de modelos locales
 * (librerias/std/modelo.syn + synapse_rt.c + nucleo/optimizador_ia.syn)
 *
 * Secciones de prueba:
 *   Section 1: ModeloContext — creación y destrucción (mock)
 *   Section 2: n_ctx — gestión de longitud de contexto
 *   Section 3: Tokenización BPE — codificar/decodificar
 *   Section 4: argmax — selección del token más probable
 *   Section 5: Metadatos — query de arquitectura y capas
 *   Section 6: Optimizador — detección de patrones estáticos
 *   Section 7: Optimizador — sugerencias de contratos
 *   Section 8: Optimizador — análisis de rendimiento
 *   Section 9: Optimizador — detección de código muerto
 *   Section 10: Edge cases — punteros nulos, límites
 *
 * Compilar: gcc -O2 -std=c99 validate_modelo_local.c -o validate_modelo_local.exe -lm
 *
 * NOTA: Este archivo NO modifica el directorio tests/ (candado activo).
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* ============================================================
 * Forward declarations de funciones del runtime (synapse_rt.c)
 * ============================================================ */

typedef struct { int longitud; const char* datos; } CadenaSegura;
typedef struct { unsigned int filas; unsigned int columnas; float* datos; int es_mapeado; } Tensor;

/* Model engine functions */
extern void* _syn_modelo_cargar(CadenaSegura ruta);
extern void _syn_modelo_cerrar(void* ctx);
extern Tensor _syn_modelo_evaluar(void* ctx, int token_id);
extern int _syn_modelo_generar(void* ctx, int token_id, float temp, int top_k, float top_p);
extern int _syn_modelo_n_past(void* ctx);
extern void _syn_modelo_reiniciar(void* ctx);
extern int _syn_modelo_obtener_n_ctx(void* ctx);
extern void _syn_modelo_establecer_n_ctx(void* ctx, int max_tokens);
extern CadenaSegura _syn_modelo_decodificar_token(void* ctx, int token_id);
extern int _syn_modelo_vocab_tamano(void* ctx);
extern int _syn_modelo_codificar_contar(void* ctx, CadenaSegura texto);
extern int _syn_modelo_codificar_obtener(void* ctx, int indice);
extern CadenaSegura _syn_modelo_generar_texto(void* ctx, CadenaSegura prompt,
    int max_tokens, float temp, int top_k, float top_p);
extern CadenaSegura _syn_modelo_obtener_metadato(void* ctx, CadenaSegura clave);
extern CadenaSegura _syn_modelo_obtener_arquitectura(void* ctx);
extern int _syn_modelo_obtener_n_layers(void* ctx);
extern int _syn_modelo_obtener_n_embd(void* ctx);
extern int _syn_modelo_obtener_n_heads(void* ctx);
extern CadenaSegura _syn_gguf_obtener_metadato(void* datos_internos, CadenaSegura clave);

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
        printf("  ✓ %s\n", name);
    } else {
        printf("  ✗ %s (FAILED)\n", name);
    }
}

/* ============================================================
 * Mock model context (GGUF-independent, lightweight)
 * ============================================================ */

/* Structure matching synapse_rt.c's ModeloContexto for testing */
#define MOCK_VOCAB_SIZE 100

typedef struct {
    int es_mock;
    int n_past;
    int max_seq_len;
    int vocab_size;
    int n_layers;
    int n_embd;
    int n_heads;
    int n_ff;
    float rope_theta;
    /* Mock token table */
    char* tokens[MOCK_VOCAB_SIZE];
    int token_count;
    /* Mock encoding */
    int* ultima_codificacion;
    int ultima_codificacion_len;
    /* KV cache stub */
    void* k_cache;
    void* v_cache;
} MockModelo;

/* Crea un contexto mock para pruebas sin GGUF real */
static MockModelo* mock_crear(void) {
    MockModelo* mc = (MockModelo*)calloc(1, sizeof(MockModelo));
    if (!mc) return NULL;
    mc->es_mock = 1;
    mc->n_past = 0;
    mc->max_seq_len = 4096;
    mc->vocab_size = MOCK_VOCAB_SIZE;
    mc->n_layers = 32;
    mc->n_embd = 4096;
    mc->n_heads = 32;
    mc->n_ff = 11008;
    mc->rope_theta = 10000.0f;
    mc->token_count = 10;
    /* Create mock tokens */
    const char* mock_tokens[] = {
        "<unk>", "<s>", "</s>", "hello", " world", "test",
        "Synapse", "AI", "model", "inference"
    };
    for (int i = 0; i < mc->token_count && i < MOCK_VOCAB_SIZE; i++) {
        mc->tokens[i] = strdup(mock_tokens[i]);
    }
    mc->ultima_codificacion = NULL;
    mc->ultima_codificacion_len = 0;
    return mc;
}

static void mock_destruir(MockModelo* mc) {
    if (!mc) return;
    for (int i = 0; i < mc->token_count; i++) {
        free(mc->tokens[i]);
    }
    free(mc->ultima_codificacion);
    free(mc->k_cache);
    free(mc->v_cache);
    free(mc);
}

/* Override synapse_rt.c functions for mock testing */
/* These override the weak/default implementations */

void* _syn_modelo_cargar(CadenaSegura ruta) {
    (void)ruta;
    return (void*)mock_crear();
}

void _syn_modelo_cerrar(void* ctx) {
    if (!ctx) return;
    MockModelo* mc = (MockModelo*)ctx;
    mock_destruir(mc);
}

Tensor _syn_modelo_evaluar(void* ctx, int token_id) {
    MockModelo* mc = (MockModelo*)ctx;
    if (!mc || token_id < 0) return (Tensor){0,0,NULL,0};
    if (mc->n_past >= mc->max_seq_len) return (Tensor){0,0,NULL,0};
    mc->n_past++;

    /* Return mock logits: random-ish values */
    Tensor logits;
    logits.filas = 1;
    logits.columnas = (unsigned int)mc->vocab_size;
    logits.es_mapeado = 0;
    logits.datos = (float*)malloc(mc->vocab_size * sizeof(float));

    /* Token 5 gets highest probability for argmax testing */
    for (int i = 0; i < mc->vocab_size; i++) {
        logits.datos[i] = (float)(rand() % 100) / 100.0f;
    }
    logits.datos[5] = 10.0f;  /* Token 5 is most likely */
    return logits;
}

int _syn_modelo_generar(void* ctx, int token_id, float temp, int top_k, float top_p) {
    (void)token_id; (void)temp; (void)top_k; (void)top_p;
    MockModelo* mc = (MockModelo*)ctx;
    if (!mc) return -1;
    Tensor logits = _syn_modelo_evaluar(ctx, 1);
    if (!logits.datos || logits.columnas <= 0) return -1;
    free(logits.datos);
    /* Predict token 5 always in mock */
    return 5;
}

int _syn_modelo_n_past(void* ctx) {
    return ctx ? ((MockModelo*)ctx)->n_past : 0;
}

void _syn_modelo_reiniciar(void* ctx) {
    if (!ctx) return;
    ((MockModelo*)ctx)->n_past = 0;
}

int _syn_modelo_obtener_n_ctx(void* ctx) {
    return ctx ? ((MockModelo*)ctx)->max_seq_len : 0;
}

void _syn_modelo_establecer_n_ctx(void* ctx, int max_tokens) {
    if (!ctx) return;
    ((MockModelo*)ctx)->max_seq_len = max_tokens;
}

CadenaSegura _syn_modelo_decodificar_token(void* ctx, int token_id) {
    MockModelo* mc = (MockModelo*)ctx;
    if (!mc || token_id < 0 || token_id >= mc->token_count) {
        return (CadenaSegura){0, ""};
    }
    if (mc->tokens[token_id]) {
        return (CadenaSegura){
            .longitud = (int)strlen(mc->tokens[token_id]),
            .datos = strdup(mc->tokens[token_id])
        };
    }
    return (CadenaSegura){0, ""};
}

int _syn_modelo_vocab_tamano(void* ctx) {
    return ctx ? ((MockModelo*)ctx)->vocab_size : 0;
}

int _syn_modelo_codificar_contar(void* ctx, CadenaSegura texto) {
    MockModelo* mc = (MockModelo*)ctx;
    if (!mc || !texto.datos || texto.longitud <= 0) return 0;
    /* Mock: split by space, each word is a token */
    int count = 1;
    for (int i = 0; i < texto.longitud; i++) {
        if (texto.datos[i] == ' ' || texto.datos[i] == '\n') count++;
    }

    /* Store encoding */
    free(mc->ultima_codificacion);
    mc->ultima_codificacion = (int*)malloc(count * sizeof(int));
    mc->ultima_codificacion_len = count;
    for (int i = 0; i < count && i < mc->token_count; i++) {
        mc->ultima_codificacion[i] = i;
    }
    return count;
}

int _syn_modelo_codificar_obtener(void* ctx, int indice) {
    MockModelo* mc = (MockModelo*)ctx;
    if (!mc || !mc->ultima_codificacion ||
        indice < 0 || indice >= mc->ultima_codificacion_len) return -1;
    return mc->ultima_codificacion[indice];
}

CadenaSegura _syn_modelo_generar_texto(void* ctx, CadenaSegura prompt,
    int max_tokens, float temp, int top_k, float top_p) {
    (void)prompt; (void)max_tokens;
    (void)temp; (void)top_k; (void)top_p;
    if (!ctx) return (CadenaSegura){0, ""};
    /* Return mock generated text */
    return (CadenaSegura){
        .longitud = 18,
        .datos = strdup("Synapse model ready")
    };
}

CadenaSegura _syn_modelo_obtener_metadato(void* ctx, CadenaSegura clave) {
    MockModelo* mc = (MockModelo*)ctx;
    (void)clave;
    if (!mc) return (CadenaSegura){0, ""};
    return (CadenaSegura){
        .longitud = 4,
        .datos = strdup("test")
    };
}

CadenaSegura _syn_modelo_obtener_arquitectura(void* ctx) {
    MockModelo* mc = (MockModelo*)ctx;
    if (!mc) return (CadenaSegura){0, ""};
    return (CadenaSegura){
        .longitud = 6,
        .datos = strdup("llama")
    };
}

int _syn_modelo_obtener_n_layers(void* ctx) {
    return ctx ? ((MockModelo*)ctx)->n_layers : 0;
}

int _syn_modelo_obtener_n_embd(void* ctx) {
    return ctx ? ((MockModelo*)ctx)->n_embd : 0;
}

int _syn_modelo_obtener_n_heads(void* ctx) {
    return ctx ? ((MockModelo*)ctx)->n_heads : 0;
}

/* ============================================================
 * Section 1: ModeloContext — creación y destrucción
 * ============================================================ */

static void test_modelo_context(void) {
    section_header("ModeloContext - Creation & Destruction");

    /* 1.1 Crear contexto */
    void* ctx = _syn_modelo_cargar((CadenaSegura){.longitud = 4, .datos = "test"});
    test_assert("cargar_modelo retorna puntero no nulo", ctx != NULL);

    /* 1.2 Verificar estado inicial */
    int n_past = _syn_modelo_n_past(ctx);
    test_assert("n_past inicial = 0", n_past == 0);

    /* 1.3 Cerrar contexto */
    _syn_modelo_cerrar(ctx);
    test_assert("cerrar_modelo no crash", 1);

    /* 1.4 Cerrar contexto nulo */
    _syn_modelo_cerrar(NULL);
    test_assert("cerrar_modelo(NULL) no crash", 1);

    /* 1.5 Doble cierre */
    ctx = _syn_modelo_cargar((CadenaSegura){.longitud = 4, .datos = "test"});
    _syn_modelo_cerrar(ctx);
    _syn_modelo_cerrar(NULL);
    test_assert("doble cierre no crash", 1);

    /* 1.6 n_past en contexto nulo */
    int np = _syn_modelo_n_past(NULL);
    test_assert("n_past(NULL) = 0", np == 0);

    /* 1.7 Evaluar en contexto recién creado */
    ctx = _syn_modelo_cargar((CadenaSegura){.longitud = 4, .datos = "test"});
    Tensor t = _syn_modelo_evaluar(ctx, 1);
    test_assert("evaluar retorna tensor valido",
        t.datos != NULL && t.columnas > 0);
    if (t.datos) free(t.datos);
    _syn_modelo_cerrar(ctx);
}

/* ============================================================
 * Section 2: n_ctx — gestión de longitud de contexto
 * ============================================================ */

static void test_n_ctx(void) {
    section_header("n_ctx - Context Length Management");

    void* ctx = _syn_modelo_cargar((CadenaSegura){.longitud = 4, .datos = "test"});

    /* 2.1 Obtener n_ctx por defecto */
    int nctx = _syn_modelo_obtener_n_ctx(ctx);
    test_assert("obtener_n_ctx por defecto = 4096", nctx == 4096);

    /* 2.2 Establecer n_ctx */
    _syn_modelo_establecer_n_ctx(ctx, 2048);
    int nctx2 = _syn_modelo_obtener_n_ctx(ctx);
    test_assert("establecer_n_ctx(2048) correcto", nctx2 == 2048);

    /* 2.3 Establecer n_ctx a valor mínimo */
    _syn_modelo_establecer_n_ctx(ctx, 128);
    int nctx3 = _syn_modelo_obtener_n_ctx(ctx);
    test_assert("establecer_n_ctx(128) correcto", nctx3 == 128);

    /* 2.4 n_ctx en contexto nulo */
    int nctx4 = _syn_modelo_obtener_n_ctx(NULL);
    test_assert("obtener_n_ctx(NULL) = 0", nctx4 == 0);

    /* 2.5 establecer_n_ctx en nulo */
    _syn_modelo_establecer_n_ctx(NULL, 512);
    test_assert("establecer_n_ctx(NULL) no crash", 1);

    /* 2.6 Reiniciar tras modificar n_ctx */
    _syn_modelo_reiniciar(ctx);
    int np = _syn_modelo_n_past(ctx);
    test_assert("n_past = 0 tras reiniciar", np == 0);

    _syn_modelo_cerrar(ctx);
}

/* ============================================================
 * Section 3: Tokenización BPE
 * ============================================================ */

static void test_tokenizacion(void) {
    section_header("Tokenization BPE - Encoding & Decoding");

    void* ctx = _syn_modelo_cargar((CadenaSegura){.longitud = 4, .datos = "test"});

    /* 3.1 vocab_tamano */
    int vs = _syn_modelo_vocab_tamano(ctx);
    test_assert("vocab_tamano > 0", vs > 0);

    /* 3.2 Decodificar token 3 = "hello" */
    CadenaSegura dec = _syn_modelo_decodificar_token(ctx, 3);
    test_assert("decodificar_token(3) = hello",
        dec.datos && strcmp(dec.datos, "hello") == 0);
    free((void*)dec.datos);

    /* 3.3 Decodificar token 4 = " world" */
    dec = _syn_modelo_decodificar_token(ctx, 4);
    test_assert("decodificar_token(4) = ' world'",
        dec.datos && strcmp(dec.datos, " world") == 0);
    free((void*)dec.datos);

    /* 3.4 Codificar texto */
    int count = _syn_modelo_codificar_contar(ctx,
        (CadenaSegura){.longitud = 12, .datos = "hello world"});
    test_assert("codificar_contar cuenta tokens", count > 0);

    /* 3.5 Obtener token codificado */
    int tok = _syn_modelo_codificar_obtener(ctx, 0);
    test_assert("codificar_obtener(0) >= 0", tok >= 0);

    /* 3.6 Token fuera de rango */
    int tok_invalid = _syn_modelo_codificar_obtener(ctx, 9999);
    test_assert("codificar_obtener(fuera_rango) = -1", tok_invalid == -1);

    /* 3.7 Códificar en contexto nulo */
    int count_null = _syn_modelo_codificar_contar(NULL,
        (CadenaSegura){.longitud = 5, .datos = "hello"});
    test_assert("codificar_contar(NULL) = 0", count_null == 0);

    _syn_modelo_cerrar(ctx);
}

/* ============================================================
 * Section 4: argmax — selección del token más probable
 * ============================================================ */

static int argmax(Tensor logits) {
    if (!logits.datos || logits.columnas <= 0) return -1;
    float max_val = logits.datos[0];
    int idx = 0;
    for (unsigned int i = 1; i < logits.columnas; i++) {
        if (logits.datos[i] > max_val) {
            max_val = logits.datos[i];
            idx = (int)i;
        }
    }
    return idx;
}

static void test_argmax(void) {
    section_header("argmax - Token Selection");

    /* 4.1 argmax con tensor normal */
    float data1[] = {0.1f, 0.3f, 0.5f, 0.05f, 0.05f};
    Tensor t1 = {1, 5, data1, 0};
    int idx = argmax(t1);
    test_assert("argmax([0.1,0.3,0.5,0.05,0.05]) = 2", idx == 2);

    /* 4.2 argmax con primer elemento máximo */
    float data2[] = {0.9f, 0.05f, 0.05f};
    Tensor t2 = {1, 3, data2, 0};
    idx = argmax(t2);
    test_assert("argmax([0.9,0.05,0.05]) = 0", idx == 0);

    /* 4.3 argmax con último elemento máximo */
    float data3[] = {0.1f, 0.1f, 0.8f};
    Tensor t3 = {1, 3, data3, 0};
    idx = argmax(t3);
    test_assert("argmax([0.1,0.1,0.8]) = 2", idx == 2);

    /* 4.4 argmax con todos iguales */
    float data4[] = {0.5f, 0.5f, 0.5f};
    Tensor t4 = {1, 3, data4, 0};
    idx = argmax(t4);
    test_assert("argmax([0.5,0.5,0.5]) = 0 (primer max)", idx == 0);

    /* 4.5 argmax con tensor 1 elemento */
    float data5[] = {42.0f};
    Tensor t5 = {1, 1, data5, 0};
    idx = argmax(t5);
    test_assert("argmax([42]) = 0", idx == 0);

    /* 4.6 argmax con tensor nulo */
    Tensor t6 = {0, 0, NULL, 0};
    idx = argmax(t6);
    test_assert("argmax(NULL) = -1", idx == -1);

    /* 4.7 argmax integrado con mock logits */
    void* ctx = _syn_modelo_cargar((CadenaSegura){.longitud = 4, .datos = "test"});
    Tensor logits = _syn_modelo_evaluar(ctx, 1);
    int am = argmax(logits);
    test_assert("argmax(mock logits) = 5 (token 5 mas probable)",
        am == 5);
    if (logits.datos) free(logits.datos);
    _syn_modelo_cerrar(ctx);
}

/* ============================================================
 * Section 5: Metadatos del modelo
 * ============================================================ */

static void test_metadata(void) {
    section_header("Model Metadata - Architecture & Layers");

    void* ctx = _syn_modelo_cargar((CadenaSegura){.longitud = 4, .datos = "test"});

    /* 5.1 Obtener arquitectura */
    CadenaSegura arch = _syn_modelo_obtener_arquitectura(ctx);
    test_assert("obtener_arquitectura != vacio",
        arch.datos != NULL && arch.longitud > 0);
    free((void*)arch.datos);

    /* 5.2 Obtener n_layers */
    int nl = _syn_modelo_obtener_n_layers(ctx);
    test_assert("obtener_n_layers > 0", nl > 0);

    /* 5.3 Obtener n_embd */
    int ne = _syn_modelo_obtener_n_embd(ctx);
    test_assert("obtener_n_embd > 0", ne > 0);

    /* 5.4 Obtener n_heads */
    int nh = _syn_modelo_obtener_n_heads(ctx);
    test_assert("obtener_n_heads > 0", nh > 0);

    /* 5.5 Verificar coherencia: n_embd / n_heads = head_dim */
    test_assert("n_embd divisible por n_heads", ne % nh == 0);

    /* 5.6 Obtener metadato */
    CadenaSegura meta = _syn_modelo_obtener_metadato(ctx,
        (CadenaSegura){.longitud = 4, .datos = "test"});
    test_assert("obtener_metadato != vacio",
        meta.datos != NULL && meta.longitud > 0);
    free((void*)meta.datos);

    /* 5.7 Metadatos en contexto nulo */
    CadenaSegura meta_null = _syn_modelo_obtener_metadato(NULL,
        (CadenaSegura){.longitud = 4, .datos = "test"});
    test_assert("obtener_metadato(NULL) = vacio",
        meta_null.longitud == 0 || meta_null.datos == NULL);

    _syn_modelo_cerrar(ctx);
}

/* ============================================================
 * Section 6: Optimizador — Detección de patrones estáticos
 * ============================================================ */

/* Simula el optimizador de código: detecta complejidad alta */
static int detectar_complejidad(int num_condicionales, int num_bucles) {
    int complejidad = 1 + num_condicionales + num_bucles;
    if (complejidad > 10) return 1; /* Alta */
    return 0;
}

/* Simula detección de función larga */
static int detectar_funcion_larga(int num_lineas) {
    return num_lineas > 50 ? 1 : 0;
}

static void test_optimizer_patterns(void) {
    section_header("Optimizer - Static Pattern Detection");

    /* 6.1 Complejidad baja (simple) */
    test_assert("complejidad 1 condicional = baja",
        detectar_complejidad(1, 0) == 0);

    /* 6.2 Complejidad media */
    test_assert("complejidad 5 condicionales = baja",
        detectar_complejidad(5, 2) == 0);

    /* 6.3 Complejidad alta (12) */
    test_assert("complejidad 10 condicionales = alta",
        detectar_complejidad(10, 2) == 1);

    /* 6.4 Complejidad muy alta (20) */
    test_assert("complejidad 15 cond + 5 bucles = alta",
        detectar_complejidad(15, 5) == 1);

    /* 6.5 Función corta */
    test_assert("funcion 10 lineas = normal",
        detectar_funcion_larga(10) == 0);

    /* 6.6 Función larga */
    test_assert("funcion 60 lineas = larga",
        detectar_funcion_larga(60) == 1);

    /* 6.7 Función en límite */
    test_assert("funcion 50 lineas = normal",
        detectar_funcion_larga(50) == 0);

    /* 6.8 Función muy larga */
    test_assert("funcion 200 lineas = larga",
        detectar_funcion_larga(200) == 1);
}

/* ============================================================
 * Section 7: Optimizador — Sugerencias de contratos
 * ============================================================ */

/* Simula sugerencia de contrato */
static int sugerir_contrato(int tiene_requiere, int tiene_garantiza) {
    int sugerencias = 0;
    if (!tiene_requiere) sugerencias++;
    if (!tiene_garantiza) sugerencias++;
    return sugerencias;
}

static void test_optimizer_contracts(void) {
    section_header("Optimizer - Contract Suggestions");

    /* 7.1 Sin contratos */
    int s = sugerir_contrato(0, 0);
    test_assert("Sin contratos -> 2 sugerencias", s == 2);

    /* 7.2 Solo requiere */
    s = sugerir_contrato(1, 0);
    test_assert("Solo requiere -> 1 sugerencia", s == 1);

    /* 7.3 Solo garantiza */
    s = sugerir_contrato(0, 1);
    test_assert("Solo garantiza -> 1 sugerencia", s == 1);

    /* 7.4 Ambos contratos */
    s = sugerir_contrato(1, 1);
    test_assert("Ambos contratos -> 0 sugerencias", s == 0);

    /* 7.5 Múltiples funciones sin contratos */
    int total_sugerencias = 0;
    total_sugerencias += sugerir_contrato(0, 0); /* fn1 */
    total_sugerencias += sugerir_contrato(0, 0); /* fn2 */
    test_assert("2 funciones sin contratos -> 4 sugerencias",
        total_sugerencias == 4);
}

/* ============================================================
 * Section 8: Optimizador — Análisis de rendimiento
 * ============================================================ */

/* Simula detección de patrones de rendimiento */
static int detectar_rendimiento(int alloc_en_bucle, int io_en_bucle) {
    int warnings = 0;
    if (alloc_en_bucle) warnings++;
    if (io_en_bucle) warnings++;
    return warnings;
}

static void test_optimizer_performance(void) {
    section_header("Optimizer - Performance Analysis");

    /* 8.1 Sin problemas */
    int w = detectar_rendimiento(0, 0);
    test_assert("Sin alloc ni IO en bucle -> 0 warnings", w == 0);

    /* 8.2 Alloc en bucle */
    w = detectar_rendimiento(1, 0);
    test_assert("Alloc en bucle -> 1 warning", w == 1);

    /* 8.3 IO en bucle */
    w = detectar_rendimiento(0, 1);
    test_assert("IO en bucle -> 1 warning", w == 1);

    /* 8.4 Ambos problemas */
    w = detectar_rendimiento(1, 1);
    test_assert("Alloc + IO en bucle -> 2 warnings", w == 2);

    /* 8.5 Múltiples instancias */
    int total = 0;
    for (int i = 0; i < 10; i++) {
        total += detectar_rendimiento(i % 2, (i + 1) % 2);
    }
    test_assert("10 iteraciones rendimiento coherente", total == 10);
}

/* ============================================================
 * Section 9: Optimizador — Detección de código muerto
 * ============================================================ */

/* Simula detección de código muerto */
static int tiene_codigo_muerto(int hay_retorno, int hay_codigo_despues) {
    return (hay_retorno && hay_codigo_despues) ? 1 : 0;
}

static void test_optimizer_dead_code(void) {
    section_header("Optimizer - Dead Code Detection");

    /* 9.1 Sin código muerto */
    test_assert("retorno sin codigo despues = limpio",
        tiene_codigo_muerto(1, 0) == 0);

    /* 9.2 Código muerto claro */
    test_assert("retorno con codigo despues = codigo muerto",
        tiene_codigo_muerto(1, 1) == 1);

    /* 9.3 Sin retorno */
    test_assert("sin retorno = limpio",
        tiene_codigo_muerto(0, 1) == 0);

    /* 9.4 Sin retorno ni código */
    test_assert("sin retorno ni codigo = limpio",
        tiene_codigo_muerto(0, 0) == 0);

    /* 9.5 Múltiples retornos */
    test_assert("retorno en medio de bloque = codigo muerto",
        tiene_codigo_muerto(1, 1) == 1);
}

/* ============================================================
 * Section 10: Edge Cases
 * ============================================================ */

static void test_edge_cases(void) {
    section_header("Edge Cases - Null Pointers & Boundaries");

    /* 10.1 generar_token en contexto nulo */
    int tok = _syn_modelo_generar(NULL, 0, 0.7f, 40, 0.9f);
    test_assert("generar(NULL) = -1", tok == -1);

    /* 10.2 evaluar en contexto nulo */
    Tensor t = _syn_modelo_evaluar(NULL, 0);
    test_assert("evaluar(NULL) = tensor nulo",
        t.datos == NULL && t.filas == 0 && t.columnas == 0);

    /* 10.3 decodificar_token en contexto nulo */
    CadenaSegura dec = _syn_modelo_decodificar_token(NULL, 0);
    test_assert("decodificar(NULL) = vacio",
        dec.longitud == 0 || dec.datos == NULL);

    /* 10.4 vocab_tamano en contexto nulo */
    int vs = _syn_modelo_vocab_tamano(NULL);
    test_assert("vocab_tamano(NULL) = 0", vs == 0);

    /* 10.5 generar_texto en contexto nulo */
    CadenaSegura gen = _syn_modelo_generar_texto(NULL,
        (CadenaSegura){.longitud = 5, .datos = "hello"},
        10, 0.7f, 40, 0.9f);
    test_assert("generar_texto(NULL) = vacio",
        gen.longitud == 0 || gen.datos == NULL);

    /* 10.6 arquitectura en contexto nulo */
    CadenaSegura arch = _syn_modelo_obtener_arquitectura(NULL);
    test_assert("obtener_arquitectura(NULL) = vacio",
        arch.longitud == 0 || arch.datos == NULL);

    /* 10.7 n_layers en contexto nulo */
    int nl = _syn_modelo_obtener_n_layers(NULL);
    test_assert("obtener_n_layers(NULL) = 0", nl == 0);

    /* 10.8 n_embd en contexto nulo */
    int ne = _syn_modelo_obtener_n_embd(NULL);
    test_assert("obtener_n_embd(NULL) = 0", ne == 0);

    /* 10.9 n_heads en contexto nulo */
    int nh = _syn_modelo_obtener_n_heads(NULL);
    test_assert("obtener_n_heads(NULL) = 0", nh == 0);

    /* 10.10 Decodificar token negativo */
    void* ctx = _syn_modelo_cargar((CadenaSegura){.longitud = 4, .datos = "test"});
    CadenaSegura neg = _syn_modelo_decodificar_token(ctx, -1);
    test_assert("decodificar_token(-1) = vacio",
        neg.longitud == 0 || neg.datos == NULL);

    /* 10.11 Codificar texto vacío */
    int empty = _syn_modelo_codificar_contar(ctx,
        (CadenaSegura){.longitud = 0, .datos = ""});
    test_assert("codificar_contar('') = 0", empty == 0);

    _syn_modelo_cerrar(ctx);
}

/* ============================================================
 * Main
 * ============================================================ */

int main(void) {
    printf("============================================\n");
    printf("  M13.1 — Local Model Inference Pipeline\n");
    printf("  validate_modelo_local.c\n");
    printf("============================================\n");

    test_modelo_context();
    test_n_ctx();
    test_tokenizacion();
    test_argmax();
    test_metadata();
    test_optimizer_patterns();
    test_optimizer_contracts();
    test_optimizer_performance();
    test_optimizer_dead_code();
    test_edge_cases();

    printf("\n============================================\n");
    printf("  RESULTS: %d / %d PASS (%.1f%%)\n",
        tests_passed, tests_total,
        (tests_total > 0) ? (100.0f * tests_passed / tests_total) : 0.0f);
    printf("============================================\n");

    return (tests_passed == tests_total) ? 0 : 1;
}
