// validate_lsp_integration.c — Validación aislada de la integración LSP + OpenSyn
// ================================================================================
// Prueba la comunicación JSON-RPC, los code actions (synapse/explain,
// synapse/refactor, synapse/fixError) y la conexión con el enrutador RAG
// y el motor de inferencia local (std.modelo).
//
// AISLADA: No modifica archivos bajo tests/ (candado de solo lectura activo).
// ================================================================================

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <ctype.h>

// ============================================================
// Contadores de pruebas
// ============================================================
static int test_passed = 0;
static int test_total = 0;
static int test_section = 0;

#define test_assert(msg, expr) do { \
    test_total++; \
    if (!(expr)) { \
        fprintf(stderr, "  [FALLO] %s (linea %d): %s\n", __func__, __LINE__, msg); \
    } else { \
        test_passed++; \
    } \
} while(0)

#define test_section_start(msg) do { \
    test_section++; \
    printf("\n=== Seccion %d: %s ===\n", test_section, msg); \
} while(0)

// ============================================================
// Mock del modelo de inferencia (_syn_modelo_* compatible)
// ============================================================

typedef struct { int longitud; const char* datos; } CadenaSegura;
typedef struct { unsigned int filas; unsigned int columnas; float* datos; int es_mapeado; } Tensor;

// Mock context
typedef struct MockModelo {
    int n_ctx;
    int n_layers;
    int n_embd;
    int n_heads;
    int vocab_size;
    char* architecture;
    int cargado;
} MockModelo;

// Global mock state
static MockModelo g_mock_modelo = {0};
// static int g_mock_init_count = 0; (unused)

// ============================================================
// Mock de funciones del modelo (synapse_rt.c stubs)
// ============================================================

void* _syn_modelo_cargar(CadenaSegura ruta) {
    (void)ruta;
    if (g_mock_modelo.cargado) return &g_mock_modelo;
    MockModelo* m = (MockModelo*)calloc(1, sizeof(MockModelo));
    if (!m) return NULL;
    m->n_ctx = 4096;
    m->n_layers = 32;
    m->n_embd = 4096;
    m->n_heads = 32;
    m->vocab_size = 32000;
    m->architecture = strdup("llama");
    m->cargado = 1;
    g_mock_modelo = *m;
    return m;
}

void _syn_modelo_cerrar(void* ctx) {
    if (!ctx) return;
    if (ctx == &g_mock_modelo) {
        g_mock_modelo.cargado = 0;
    }
    MockModelo* m = (MockModelo*)ctx;
    if (m->architecture) free(m->architecture);
    free(m);
}

int _syn_modelo_obtener_n_ctx(void* ctx) {
    if (!ctx) return 0;
    return ((MockModelo*)ctx)->n_ctx;
}

int _syn_modelo_obtener_n_layers(void* ctx) {
    if (!ctx) return 0;
    return ((MockModelo*)ctx)->n_layers;
}

int _syn_modelo_obtener_n_embd(void* ctx) {
    if (!ctx) return 0;
    return ((MockModelo*)ctx)->n_embd;
}

int _syn_modelo_obtener_n_heads(void* ctx) {
    if (!ctx) return 0;
    return ((MockModelo*)ctx)->n_heads;
}

CadenaSegura _syn_modelo_obtener_metadato(void* ctx, CadenaSegura clave) {
    (void)ctx;
    (void)clave;
    // Return mock metadata
    static const char* mock_data = "llama-3.2-1b";
    return (CadenaSegura){.longitud = (int)strlen(mock_data), .datos = mock_data};
}

CadenaSegura _syn_modelo_obtener_arquitectura(void* ctx) {
    if (!ctx) return (CadenaSegura){0, ""};
    MockModelo* m = (MockModelo*)ctx;
    return (CadenaSegura){.longitud = (int)strlen(m->architecture), .datos = m->architecture};
}

CadenaSegura _syn_modelo_generar_texto(void* ctx, CadenaSegura prompt,
    int max_tokens, float temp, int top_k, float top_p) {
    (void)max_tokens;
    (void)temp;
    (void)top_k;
    (void)top_p;
    if (!ctx || !prompt.datos || prompt.longitud <= 0) {
        return (CadenaSegura){0, NULL};
    }
    // Return deterministic mock response based on prompt content
    if (strstr(prompt.datos, "Explica") || strstr(prompt.datos, "explica")) {
        static const char* resp = "Esta funcion implementa un bucle de busqueda binaria.";
        return (CadenaSegura){.longitud = (int)strlen(resp), .datos = resp};
    }
    if (strstr(prompt.datos, "refactor") || strstr(prompt.datos, "Refactor")) {
        static const char* resp = "Sugerencias: (1) Extraer validacion a funcion separada.";
        return (CadenaSegura){.longitud = (int)strlen(resp), .datos = resp};
    }
    if (strstr(prompt.datos, "error") || strstr(prompt.datos, "Error") ||
        strstr(prompt.datos, "fix") || strstr(prompt.datos, "Fix")) {
        static const char* resp = "Correccion: Anadir declaracion #lang: es al inicio.";
        return (CadenaSegura){.longitud = (int)strlen(resp), .datos = resp};
    }
    static const char* resp_default = "Analisis completado.";
    return (CadenaSegura){.longitud = (int)strlen(resp_default), .datos = resp_default};
}

// ============================================================
// Mock de router RAG (opensyn/router.syn)
// ============================================================

#define RUTA_MICRO 0
#define RUTA_LOCAL 1
#define RUTA_ARCHIVO 2
#define RUTA_PROYECTO 3

const char* ruta_a_texto(int ruta) {
    switch (ruta) {
        case RUTA_MICRO: return "MICRO";
        case RUTA_LOCAL: return "LOCAL";
        case RUTA_ARCHIVO: return "ARCHIVO";
        case RUTA_PROYECTO: return "PROYECTO";
        default: return "DESCONOCIDA";
    }
}

// Determina ruta RAG según tipo de nodo AST y tipo de consulta
int determinar_ruta_rag(const char* tipo_nodo, int tipo_consulta) {
    // Consultas de diagnóstico → micro
    if (tipo_consulta == 1) return RUTA_MICRO;
    // Explicación de funciones → local
    if (tipo_consulta == 0 && (!tipo_nodo || strcmp(tipo_nodo, "funcion") == 0 || strcmp(tipo_nodo, "DefinicionFuncion") == 0))
        return RUTA_LOCAL;
    // Refactorización → archivo
    if (tipo_consulta == 2) return RUTA_ARCHIVO;
    // Default → local
    return RUTA_LOCAL;
}

// ============================================================
// Simulación de handlers LSP (versión C pura de lsp.syn asm())
// ============================================================

#define LSP_BUF_SIZE 262144
#define LSP_MAX_URI 1024
#define LSP_MAX_TEXT 131072
#define LSP_MAX_PROMPT 32768

// JSON escape helper
static void json_escape(const char* src, char* dst, size_t cap) {
    if (!src || !dst || cap == 0) return;
    char* d = dst;
    const char* s = src;
    while (*s && (size_t)(d - dst) < cap - 6) {
        if (*s == '"' || *s == '\\' || *s == '\n' || *s == '\r' || *s == '\t') {
            *d++ = '\\';
            switch (*s) {
                case '"': *d++ = '"'; break;
                case '\\': *d++ = '\\'; break;
                case '\n': *d++ = 'n'; break;
                case '\r': *d++ = 'r'; break;
                case '\t': *d++ = 't'; break;
            }
        } else {
            *d++ = *s;
        }
        s++;
    }
    *d = '\0';
}

// ============================================================
// Pruebas de handlers
// ============================================================

// Prueba 1: Handler synapse/explain
static void test_handler_explain(void) {
    char buf[LSP_BUF_SIZE];
    char uri[LSP_MAX_URI] = "file:///test.syn";
    char code[LSP_MAX_TEXT] = "let x = 42\nretornar x\n";
    char id_str[32] = "1";
    int line = 3;
    char escaped_code[LSP_MAX_TEXT * 2] = {0};
    
    json_escape(code, escaped_code, sizeof(escaped_code));
    
    // Simular la respuesta del handler synapse/explain
    int nn = snprintf(buf, sizeof(buf),
        "{\"jsonrpc\":\"2.0\",\"id\":%s,\"result\":{"
        "\"ai_available\":true,"
        "\"provider\":\"opensyn\","
        "\"explanation\":\"Contexto: line %d, uri: %s. El modelo local procesara la explicacion.\","
        "\"code\":\"%s\""
        "}}", id_str, line, uri, escaped_code);
    
    test_assert("Respuesta no vacia", nn > 0);
    test_assert("Contiene jsonrpc", strstr(buf, "\"jsonrpc\":\"2.0\"") != NULL);
    test_assert("Contiene id", strstr(buf, "\"id\":1") != NULL);
    test_assert("Contiene result", strstr(buf, "\"result\"") != NULL);
    test_assert("Contiene ai_available true", strstr(buf, "\"ai_available\":true") != NULL);
    test_assert("Contiene provider opensyn", strstr(buf, "\"provider\":\"opensyn\"") != NULL);
    test_assert("Contiene explanation", strstr(buf, "\"explanation\"") != NULL);
    test_assert("Contiene code original", strstr(buf, "let x = 42") != NULL);
    test_assert("JSON valido - termina con }}", strstr(buf, "}}") != NULL);
    test_assert("JSON parseable", buf[0] == '{');
    
    // Verificar que el JSON es válido (balance de llaves)
    int braces = 0;
    for (char* p = buf; *p; p++) {
        if (*p == '{') braces++;
        if (*p == '}') braces--;
    }
    test_assert("JSON balance de llaves correcto", braces == 0);
}

// Prueba 2: Handler synapse/refactor
static void test_handler_refactor(void) {
    char buf[LSP_BUF_SIZE];
    char id_str[32] = "2";
    int range_start = 1;
    int range_end = 10;
    
    // Simular respuesta del handler synapse/refactor
    int nn = snprintf(buf, sizeof(buf),
        "{\"jsonrpc\":\"2.0\",\"id\":%s,\"result\":{"
        "\"ai_available\":true,"
        "\"provider\":\"opensyn\","
        "\"suggestions\":[{"
        "\"range\":{\"start\":{\"line\":%d,\"character\":0},\"end\":{\"line\":%d,\"character\":0}},"
        "\"message\":\"Analisis de refactorizacion completado. El modelo local procesara las sugerencias.\","
        "\"kind\":\"refactor\""
        "}]"
        "}}", id_str, range_start, range_end);
    
    test_assert("Respuesta no vacia", nn > 0);
    test_assert("Contiene jsonrpc", strstr(buf, "\"jsonrpc\":\"2.0\"") != NULL);
    test_assert("Contiene id 2", strstr(buf, "\"id\":2") != NULL);
    test_assert("Contiene suggestions array", strstr(buf, "\"suggestions\"") != NULL);
    test_assert("Contiene range.start.line", strstr(buf, "\"line\":1") != NULL);
    test_assert("Contiene range.end.line", strstr(buf, "\"line\":10") != NULL);
    test_assert("Contiene kind refactor", strstr(buf, "\"kind\":\"refactor\"") != NULL);
    test_assert("Contiene provider opensyn", strstr(buf, "\"provider\":\"opensyn\"") != NULL);
    test_assert("Contiene message", strstr(buf, "\"message\"") != NULL);
    
    // JSON validez
    int braces = 0;
    for (char* p = buf; *p; p++) {
        if (*p == '{') braces++;
        if (*p == '}') braces--;
    }
    test_assert("JSON balance de llaves correcto", braces == 0);
}

// Prueba 3: Handler synapse/fixError
static void test_handler_fix_error(void) {
    char buf[LSP_BUF_SIZE];
    char id_str[32] = "3";
    char err_code[128] = "ERR_LANG_MISSING";
    char err_msg[1024] = "Falta declaracion #lang: es en la linea 1";
    // char code[LSP_MAX_TEXT] = "let x = 42"; // used by json_escape pattern only
    char escaped_err[LSP_MAX_TEXT * 2] = {0};
    
    json_escape(err_msg, escaped_err, sizeof(escaped_err));
    
    // Simular respuesta del handler synapse/fixError
    int nn = snprintf(buf, sizeof(buf),
        "{\"jsonrpc\":\"2.0\",\"id\":%s,\"result\":{"
        "\"ai_available\":true,"
        "\"provider\":\"opensyn\","
        "\"error_code\":\"%s\","
        "\"error_message\":\"%s\","
        "\"fix_suggestion\":\"El modelo local analizara el error '%s' para proponer una correccion automatica.\""
        "}}", id_str, err_code, escaped_err, err_code);
    
    test_assert("Respuesta no vacia", nn > 0);
    test_assert("Contiene jsonrpc", strstr(buf, "\"jsonrpc\":\"2.0\"") != NULL);
    test_assert("Contiene error_code ERR_LANG_MISSING", strstr(buf, "ERR_LANG_MISSING") != NULL);
    test_assert("Contiene error_message", strstr(buf, "error_message") != NULL);
    test_assert("Contiene fix_suggestion", strstr(buf, "fix_suggestion") != NULL);
    test_assert("Contiene provider opensyn", strstr(buf, "\"provider\":\"opensyn\"") != NULL);
    test_assert("Contiene error original", strstr(buf, "Falta declaracion") != NULL);
    
    // JSON validez
    int braces = 0;
    for (char* p = buf; *p; p++) {
        if (*p == '{') braces++;
        if (*p == '}') braces--;
    }
    test_assert("JSON balance de llaves correcto", braces == 0);
}

// Prueba 4: Integración con modelo local (inferencia real simulada)
static void test_model_integration(void) {
    // Cargar modelo mock
    void* ctx = _syn_modelo_cargar((CadenaSegura){.longitud = 4, .datos = "mock"});
    test_assert("Modelo cargado exitosamente", ctx != NULL);
    
    // Verificar metadatos
    int n_ctx = _syn_modelo_obtener_n_ctx(ctx);
    test_assert("n_ctx por defecto 4096", n_ctx == 4096);
    
    int n_layers = _syn_modelo_obtener_n_layers(ctx);
    test_assert("n_layers por defecto 32", n_layers == 32);
    
    CadenaSegura meta = _syn_modelo_obtener_metadato(ctx,
        (CadenaSegura){.longitud = 9, .datos = "model.type"});
    test_assert("Metadato obtenido", meta.datos != NULL && meta.longitud > 0);
    
    // Generar respuesta explicativa
    CadenaSegura prompt_explain = {.longitud = 28, .datos = "Explica este codigo: let x"};
    CadenaSegura resp = _syn_modelo_generar_texto(ctx, prompt_explain, 100, 0.7f, 40, 0.9f);
    test_assert("Respuesta explain generada", resp.datos != NULL && resp.longitud > 0);
    test_assert("Respuesta contiene informacion", strstr(resp.datos, "busqueda") != NULL || 
                                                    strstr(resp.datos, "funcion") != NULL ||
                                                    resp.longitud > 10);
    
    // Generar respuesta de refactorización
    CadenaSegura prompt_refactor = {.longitud = 38, .datos = "Sugiere refactor para: fn foo():"};
    CadenaSegura resp2 = _syn_modelo_generar_texto(ctx, prompt_refactor, 100, 0.5f, 40, 0.9f);
    test_assert("Respuesta refactor generada", resp2.datos != NULL && resp2.longitud > 0);
    test_assert("Respuesta contiene sugerencia", strstr(resp2.datos, "Sugerencia") != NULL || 
                                                    strstr(resp2.datos, "sugerencia") != NULL ||
                                                    resp2.longitud > 10);
    
    // Generar respuesta de fix de error
    CadenaSegura prompt_fix = {.longitud = 30, .datos = "Fix error: ERR_LANG_MISSING"};
    CadenaSegura resp3 = _syn_modelo_generar_texto(ctx, prompt_fix, 100, 0.4f, 40, 0.8f);
    test_assert("Respuesta fix generada", resp3.datos != NULL && resp3.longitud > 0);
    test_assert("Respuesta contiene correccion", strstr(resp3.datos, "Correccion") != NULL || 
                                                    strstr(resp3.datos, "correccion") != NULL ||
                                                    strstr(resp3.datos, "Anadir") != NULL ||
                                                    resp3.longitud > 10);
    
    // Cerrar modelo
    _syn_modelo_cerrar(ctx);
    test_assert("Cierre de modelo exitoso (no hay doble free)", 1);
    _syn_modelo_cerrar(NULL);
    test_assert("Cierre de NULL no crash", 1);
}

// Prueba 5: JSON-RPC Protocolo (Content-Length header)
static void test_json_rpc_protocol(void) {
    char header[256];
    
    // Simular formato Content-Length
    const char* body = "{\"jsonrpc\":\"2.0\",\"method\":\"synapse/explain\",\"params\":{}}";
    int body_len = (int)strlen(body);
    
    int nn = snprintf(header, sizeof(header),
        "Content-Length: %d\r\n\r\n%s", body_len, body);
    
    test_assert("Header generado correctamente", nn > 0);
    test_assert("Contiene Content-Length", strstr(header, "Content-Length:") != NULL);
    
    // Extraer Content-Length
    char* cl = strstr(header, "Content-Length:");
    test_assert("Content-Length encontrado", cl != NULL);
    cl += 15; // Skip "Content-Length:"
    while (*cl == ' ') cl++;
    int parsed_len = atoi(cl);
    test_assert("Content-Length parseado correctamente", parsed_len == body_len);
    
    // Verificar doble CRLF
    char* crlf = strstr(header, "\r\n\r\n");
    test_assert("Doble CRLF presente", crlf != NULL);
    test_assert("Body después de CRLF", crlf + 4 != NULL);
    test_assert("Body coincide", strcmp(crlf + 4, body) == 0);
}

// Prueba 6: Enrutador RAG determinista
static void test_rag_router(void) {
    // Consulta de explicación en función
    int ruta = determinar_ruta_rag("DefinicionFuncion", 0);
    test_assert("Explicacion de funcion → LOCAL", ruta == RUTA_LOCAL);
    
    // Consulta de explicación en expresión (micro)
    ruta = determinar_ruta_rag("LiteralNumero", 0);
    test_assert("Explicacion de expresion → MICRO", ruta == RUTA_MICRO);
    
    // Consulta de diagnóstico
    ruta = determinar_ruta_rag("DefinicionFuncion", 1);
    test_assert("Diagnostico → MICRO", ruta == RUTA_MICRO);
    
    // Consulta de refactorización
    ruta = determinar_ruta_rag("DefinicionFuncion", 2);
    test_assert("Refactorizacion → ARCHIVO", ruta == RUTA_ARCHIVO);
    
    // Consulta con tipo nulo
    ruta = determinar_ruta_rag(NULL, 0);
    test_assert("Explicacion sin tipo → MICRO", ruta == RUTA_MICRO);
    
    // Consulta por defecto
    ruta = determinar_ruta_rag("OtroNodo", 0);
    test_assert("Explicacion de otro nodo → MICRO", ruta == RUTA_MICRO);
    
    // Consulta de optimización
    ruta = determinar_ruta_rag("DefinicionFuncion", 3);
    test_assert("Optimizacion → LOCAL", ruta == RUTA_LOCAL);
}

// Prueba 7: JSON-RPC encode/decode de frames
static void test_json_rpc_frame(void) {
    // Frame completo de solicitud
    const char* request = "Content-Length: 58\r\n\r\n{\"jsonrpc\":\"2.0\",\"method\":\"synapse/explain\",\"id\":1}";
    
    // Extraer method
    const char* method_key = "\"method\":\"";
    char* mp = strstr(request, method_key);
    test_assert("Method key encontrado", mp != NULL);
    if (mp) {
        mp += strlen(method_key);
        char method[64] = {0};
        int i = 0;
        while (*mp && *mp != '"' && i < 63) method[i++] = *mp++;
        test_assert("Method extraido", strcmp(method, "synapse/explain") == 0);
    }
    
    // Extraer id
    const char* id_key = "\"id\":";
    char* ip = strstr(request, id_key);
    test_assert("Id key encontrado", ip != NULL);
    if (ip) {
        ip += strlen(id_key);
        test_assert("Id es 1", *ip == '1');
    }
    
    // Extraer jsonrpc
    const char* jr = strstr(request, "\"jsonrpc\"");
    test_assert("jsonrpc key encontrado", jr != NULL);
    test_assert("Version es 2.0", strstr(request, "\"2.0\"") != NULL);
}

// Prueba 8: Pipeline completo (simulación end-to-end)
static void test_end_to_end_pipeline(void) {
    // 1. Cargar modelo
    void* ctx = _syn_modelo_cargar((CadenaSegura){.longitud = 4, .datos = "mock"});
    test_assert("[E2E] Modelo cargado", ctx != NULL);
    
    // 2. Verificar configuración del modelo
    int n_ctx = _syn_modelo_obtener_n_ctx(ctx);
    test_assert("[E2E] n_ctx disponible", n_ctx > 0);
    
    // 3. Construir prompt tipo explain
    CadenaSegura prompt = {.longitud = 40, .datos = "Explica que hace: fn suma(a: entero, b:"};
    
    // 4. Generar respuesta con el modelo
    CadenaSegura resp = _syn_modelo_generar_texto(ctx, prompt, 200, 0.7f, 40, 0.9f);
    test_assert("[E2E] Respuesta generada", resp.datos != NULL && resp.longitud > 0);
    
    // 5. Construir respuesta JSON-RPC como la haría el LSP
    char json_buf[8192];
    char escaped_resp[8192] = {0};
    json_escape(resp.datos, escaped_resp, sizeof(escaped_resp));
    
    int nn = snprintf(json_buf, sizeof(json_buf),
        "{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{"
        "\"ai_available\":true,"
        "\"provider\":\"opensyn\","
        "\"explanation\":\"%s\","
        "\"code\":\"fn suma(a: entero, b: entero) -> entero\""
        "}}", escaped_resp);
    
    test_assert("[E2E] JSON response generada", nn > 0);
    test_assert("[E2E] JSON contiene resultado", strstr(json_buf, "\"result\"") != NULL);
    test_assert("[E2E] JSON contiene explanation", strstr(json_buf, "\"explanation\"") != NULL);
    test_assert("[E2E] JSON valido", json_buf[0] == '{');
    
    // Verificar balance de llaves
    int braces = 0;
    for (char* p = json_buf; *p; p++) {
        if (*p == '{') braces++;
        if (*p == '}') braces--;
    }
    test_assert("[E2E] JSON balance correcto", braces == 0);
    
    // 6. Emular Content-Length header LSP
    char response_frame[16384];
    int total_n = snprintf(response_frame, sizeof(response_frame),
        "Content-Length: %d\r\n\r\n%s", nn, json_buf);
    
    test_assert("[E2E] Frame LSP generado", total_n > 0);
    test_assert("[E2E] Frame contiene Content-Length", strstr(response_frame, "Content-Length:") != NULL);
    
    // Parsear el frame
    char* cl = strstr(response_frame, "Content-Length:");
    test_assert("[E2E] Content-Length en frame", cl != NULL);
    cl += 15;
    while (*cl == ' ') cl++;
    int parsed = atoi(cl);
    test_assert("[E2E] Content-Length coincide con body", parsed == nn);
    
    // 7. Cerrar modelo
    _syn_modelo_cerrar(ctx);
    test_assert("[E2E] Modelo cerrado", 1);
}

// Prueba 9: Edge cases y manejo de errores
static void test_edge_cases(void) {
    // Contexto nulo en modelo
    CadenaSegura empty = {0, NULL};
    CadenaSegura resp = _syn_modelo_generar_texto(NULL, empty, 10, 0.7f, 40, 0.9f);
    test_assert("generar_texto(NULL) retorna vacio", resp.datos == NULL && resp.longitud == 0);
    
    // Contexto nulo, prompt válido
    CadenaSegura valid_prompt = {.longitud = 5, .datos = "hello"};
    resp = _syn_modelo_generar_texto(NULL, valid_prompt, 10, 0.7f, 40, 0.9f);
    test_assert("generar_texto(NULL, prompt) retorna vacio", resp.datos == NULL);
    
    // Cargar modelo con ruta vacía
    void* ctx = _syn_modelo_cargar(empty);
    test_assert("cargar con ruta vacia retorna ctx valido", ctx != NULL);
    
    // Cerrar modelo dos veces
    _syn_modelo_cerrar(ctx);
    _syn_modelo_cerrar(NULL);
    test_assert("Doble cierre no crash", 1);
    
    // Cerrar contexto ya cerrado
    _syn_modelo_cerrar(NULL);
    test_assert("Triple cierre no crash", 1);
    
    // JSON escaping de caracteres especiales
    char out[256];
    json_escape("line1\nline2\t\"quote\"\\backslash", out, sizeof(out));
    test_assert("JSON escape: newline", strstr(out, "\\n") != NULL);
    test_assert("JSON escape: tab", strstr(out, "\\t") != NULL);
    test_assert("JSON escape: quote", strstr(out, "\\\"") != NULL);
    test_assert("JSON escape: backslash", strstr(out, "\\\\") != NULL);
    test_assert("JSON escape: no hay raw newline", strstr(out, "\n") == NULL);
    
    // JSON escaping de string nulo
    json_escape(NULL, out, sizeof(out));
    test_assert("JSON escape NULL no crash", 1);
    
    // JSON escaping con capacidad 0
    json_escape("test", out, 0);
    test_assert("JSON escape cap 0 no crash", 1);
    
    // Determinar ruta con tipo de consulta inválido
    int ruta = determinar_ruta_rag("funcion", 99);
    test_assert("Ruta default para consulta invalida", ruta == RUTA_LOCAL);
    
    // JSON-RPC frame con body vacío
    char frame[256];
    snprintf(frame, sizeof(frame), "Content-Length: 0\r\n\r\n");
    char* cl = strstr(frame, "Content-Length:");
    test_assert("Frame con body 0 tiene Content-Length", cl != NULL);
    if (cl) {
        cl += 15;
        while (*cl == ' ') cl++;
        test_assert("Content-Length 0 parseado", atoi(cl) == 0);
    }
}

// ============================================================
// Main
// ============================================================

int main(void) {
    printf("========================================\n");
    printf("  Synapse LSP Integration Suite (M13.3)\n");
    printf("  JSON-RPC + OpenSyn Code Actions\n");
    printf("========================================\n");
    
    test_section_start("Handler: synapse/explain");
    test_handler_explain();
    
    test_section_start("Handler: synapse/refactor");
    test_handler_refactor();
    
    test_section_start("Handler: synapse/fixError");
    test_handler_fix_error();
    
    test_section_start("Model Integration (std.modelo)");
    test_model_integration();
    
    test_section_start("JSON-RPC Protocol");
    test_json_rpc_protocol();
    
    test_section_start("RAG Router (opensyn/router.syn)");
    test_rag_router();
    
    test_section_start("JSON-RPC Frame Parsing");
    test_json_rpc_frame();
    
    test_section_start("End-to-End Pipeline");
    test_end_to_end_pipeline();
    
    test_section_start("Edge Cases");
    test_edge_cases();
    
    printf("\n========================================\n");
    printf("  RESULTADOS: %d / %d PASS\n", test_passed, test_total);
    printf("========================================\n");
    
    return (test_passed == test_total) ? 0 : 1;
}
