// test_synapse_rag.c — Tests unitarios para Pipeline RAG y negociación n_ctx
// Compilar: gcc -O2 -Wall -Wextra test_synapse_rag.c nucleo/synapse_rag.c nucleo/llama_client.c -o test_synapse_rag.exe -lws2_32 -lwinhttp

#include "nucleo/synapse_rag.h"
#include "nucleo/llama_client.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define ASSERT_OK(expr, msg) do { if (!(expr)) { fprintf(stderr, "[FAIL] %s: %s\n", msg, #expr); exit(1); } else { fprintf(stderr, "[OK] %s\n", msg); } } while(0)

void test_extraer_contexto_basico(void) {
    fprintf(stderr, "\n[TEST] Extracción de contexto básica...\n");

    const char* fuente = 
        "fn main() -> int {\n"
        "    let x = 42;\n"
        "    let y = x + 1;\n"
        "    return y;\n"
        "}\n";

    SynapseRagInput input = {
        .fuente = fuente,
        .linea = 2,  // línea "let y = x + 1;"
        .columna = 8,
        .diagnosticos = "Sin errores",
        .ast_root = NULL,
        .n_ctx_modelo = 4096
    };

    SynapseRagContexto ctx = {0};
    int r = synapse_rag_extraer_contexto(&input, &ctx);
    ASSERT_OK(r == 0, "Extracción exitosa");

    ASSERT_OK(ctx.contexto_archivo != NULL, "Contexto archivo extraído");
    ASSERT_OK(strstr(ctx.contexto_archivo, "let y = x + 1") != NULL, "Línea objetivo en contexto");

    ASSERT_OK(ctx.linea_actual != NULL, "Línea actual extraída");
    ASSERT_OK(strstr(ctx.linea_actual, "let y = x + 1") != NULL, "Línea exacta correcta");

    ASSERT_OK(ctx.diagnosticos != NULL, "Diagnósticos copiados");
    ASSERT_OK(strcmp(ctx.diagnosticos, "Sin errores") == 0, "Diagnósticos correctos");

    ASSERT_OK(ctx.n_ctx_modelo == 4096, "n_ctx leído correctamente");
    ASSERT_OK(ctx.max_tokens_inyectados == 1228, "max_tokens = 4096 * 0.3 = 1228");

    synapse_rag_liberar_contexto(&ctx);
    fprintf(stderr, "[PASS] Extracción básica\n");
}

void test_negociacion_n_ctx(void) {
    fprintf(stderr, "\n[TEST] Negociación dinámica n_ctx...\n");

    // Test ratios
    ASSERT_OK(synapse_rag_calcular_max_tokens(4096, 0.3f) == 1228, "4096 * 0.3 = 1228");
    ASSERT_OK(synapse_rag_calcular_max_tokens(8192, 0.3f) == 2048, "8192 * 0.3 = 2458, clamp a 2048");
    ASSERT_OK(synapse_rag_calcular_max_tokens(1024, 0.3f) == 307, "1024 * 0.3 = 307");
    ASSERT_OK(synapse_rag_calcular_max_tokens(200, 0.3f) == 64, "200 * 0.3 = 60, clamp min 64");

    // Test ratio extremo
    ASSERT_OK(synapse_rag_calcular_max_tokens(4096, 0.0f) == 1228, "ratio 0 usa default 0.3");
    ASSERT_OK(synapse_rag_calcular_max_tokens(4096, 0.5f) == 2048, "ratio 0.5 clamp a 2048");

    // Test leer n_ctx de props JSON
    const char* props = "{\"n_ctx\":4096,\"n_vocab\":32000}";
    int n_ctx = 0;
    ASSERT_OK(synapse_rag_leer_n_ctx_desde_props(props, &n_ctx) == 0, "Leer n_ctx de props");
    ASSERT_OK(n_ctx == 4096, "n_ctx = 4096");

    const char* props2 = "{\"n_ctx\": 8192 }";
    n_ctx = 0;
    ASSERT_OK(synapse_rag_leer_n_ctx_desde_props(props2, &n_ctx) == 0, "Leer n_ctx con espacios");
    ASSERT_OK(n_ctx == 8192, "n_ctx = 8192");

    // Props sin n_ctx
    n_ctx = 0;
    ASSERT_OK(synapse_rag_leer_n_ctx_desde_props("{}", &n_ctx) == -1, "Props vacío retorna error");

    fprintf(stderr, "[PASS] Negociación n_ctx\n");
}

void test_construir_prompt(void) {
    fprintf(stderr, "\n[TEST] Construcción de prompt RAG...\n");

    SynapseRagContexto ctx = {
        .contexto_archivo = "fn main() { let x = 42; }",
        .linea_actual = "let x = 42;",
        .diagnosticos = "Sin errores",
        .nodo_actual_tipo = "AsignacionVariable",
        .n_ctx_modelo = 4096,
        .max_tokens_inyectados = 1228
    };

    char buf[4096];
    int r = synapse_rag_construir_prompt(&ctx, buf, sizeof(buf));
    ASSERT_OK(r == 0, "Prompt construido");

    ASSERT_OK(strstr(buf, "[CONTEXTO_ARCHIVO]") != NULL, "Contiene sección contexto");
    ASSERT_OK(strstr(buf, "[LINEA_ACTUAL]") != NULL, "Contiene sección línea");
    ASSERT_OK(strstr(buf, "[NODO_AST]") != NULL, "Contiene sección nodo AST");
    ASSERT_OK(strstr(buf, "[DIAGNOSTICOS]") != NULL, "Contiene sección diagnósticos");
    ASSERT_OK(strstr(buf, "1228 tokens") != NULL, "Contiene presupuesto de tokens");

    fprintf(stderr, "[PASS] Prompt construido correctamente\n");
}

void test_edge_cases(void) {
    fprintf(stderr, "\n[TEST] Casos frontera...\n");

    // Archivo vacío
    SynapseRagInput input1 = { .fuente = "", .linea = 0, .columna = 0, .diagnosticos = "", .ast_root = NULL, .n_ctx_modelo = 4096 };
    SynapseRagContexto ctx1 = {0};
    int r1 = synapse_rag_extraer_contexto(&input1, &ctx1);
    ASSERT_OK(r1 == 0, "Archivo vacío no crashea");
    ASSERT_OK(strlen(ctx1.contexto_archivo) >= 0, "Contexto vacío manejado");
    synapse_rag_liberar_contexto(&ctx1);

    // Línea fuera de rango
    SynapseRagInput input2 = { .fuente = "linea1\nlinea2", .linea = 100, .columna = 0, .diagnosticos = "", .ast_root = NULL, .n_ctx_modelo = 4096 };
    SynapseRagContexto ctx2 = {0};
    int r2 = synapse_rag_extraer_contexto(&input2, &ctx2);
    ASSERT_OK(r2 == 0, "Línea fuera de rango no crashea");
    synapse_rag_liberar_contexto(&ctx2);

    // n_ctx 0 usa default
    SynapseRagInput input3 = { .fuente = "test", .linea = 0, .columna = 0, .diagnosticos = "", .ast_root = NULL, .n_ctx_modelo = 0 };
    SynapseRagContexto ctx3 = {0};
    int r3 = synapse_rag_extraer_contexto(&input3, &ctx3);
    ASSERT_OK(r3 == 0, "n_ctx=0 usa default");
    ASSERT_OK(ctx3.n_ctx_modelo == RAG_N_CTX_DEFAULT, "Default 4096 aplicado");
    synapse_rag_liberar_contexto(&ctx3);

    fprintf(stderr, "[PASS] Casos frontera\n");
}

void test_integracion_llama_client(void) {
    fprintf(stderr, "\n[TEST] Integración con llama_client (props)...\n");

    // Verificar que llama_obtener_props existe y retorna JSON
    llama_inicializar_red();
    LlamaClient* cli = llama_cliente_crear("127.0.0.1", 9999); // puerto inexistente

    char* props = llama_obtener_props(cli);
    // Sin servidor real, props será NULL, pero la llamada no debe crashear
    if (props) {
        int n_ctx = 0;
        int r = synapse_rag_leer_n_ctx_desde_props(props, &n_ctx);
        if (r == 0 && n_ctx > 0) {
            fprintf(stderr, "  n_ctx leído del servidor: %d\n", n_ctx);
            ASSERT_OK(n_ctx >= 512 && n_ctx <= 32768, "n_ctx en rango válido");
        }
        free(props);
    }

    llama_cliente_destruir(cli);
    llama_cerrar_red();

    fprintf(stderr, "[PASS] Integración llama_client (sin servidor real)\n");
}

int main(void) {
    fprintf(stderr, "============================================================\n");
    fprintf(stderr, "  TESTS: Pipeline RAG + Negociación n_ctx (Fase 3.3)\n");
    fprintf(stderr, "============================================================\n");

    test_extraer_contexto_basico();
    test_negociacion_n_ctx();
    test_construir_prompt();
    test_edge_cases();
    test_integracion_llama_client();

    fprintf(stderr, "\n============================================================\n");
    fprintf(stderr, "  TODOS LOS TESTS PASARON ✓\n");
    fprintf(stderr, "============================================================\n");
    return 0;
}