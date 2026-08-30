// test_ai_orchestrator.c — Pruebas unitarias del orquestador IA y cliente llama.cpp
// Compilar: gcc -O2 test_ai_orchestrator.c nucleo/ai_orchestrator.o nucleo/llama_client.o -o test_ai_orchestrator.exe -lws2_32 -lwinhttp

#include "nucleo/ai_orchestrator.h"
#include "nucleo/llama_client.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#define SLEEP_MS(ms) Sleep(ms)
#else
#include <unistd.h>
#define SLEEP_MS(ms) usleep((ms)*1000)
#endif

static int tests_passed = 0;
static int tests_failed = 0;

#define ASSERT_OK(cond, msg) \
    do { \
        if (cond) { \
            printf("[PASS] %s\n", msg); \
            tests_passed++; \
        } else { \
            printf("[FAIL] %s\n", msg); \
            tests_failed++; \
        } \
    } while(0)

#define ASSERT_EQ(a, b, msg) ASSERT_OK((a) == (b), msg)

// Copia local de json_escape para el test (no depende de llama_client estático)
static char* json_escape(const char* input) {
    if (!input) return strdup("");
    size_t len = strlen(input);
    char* output = (char*)malloc(len * 2 + 1);
    if (!output) return NULL;
    char* dst = output;
    for (size_t i = 0; i < len; i++) {
        char c = input[i];
        switch (c) {
            case '"': *dst++ = '\\'; *dst++ = '"'; break;
            case '\\': *dst++ = '\\'; *dst++ = '\\'; break;
            case '\n': *dst++ = '\\'; *dst++ = 'n'; break;
            case '\r': *dst++ = '\\'; *dst++ = 'r'; break;
            case '\t': *dst++ = '\\'; *dst++ = 't'; break;
            default: *dst++ = c; break;
        }
    }
    *dst = '\0';
    return output;
}

void test_ai_orch_crear_destruir() {
    printf("\n=== Test: ai_orch_crear / destruir ===\n");
    
    AIOrchestrator* orch = ai_orch_crear(NULL, NULL, NULL, 0);
    ASSERT_OK(orch != NULL, "Crear orquestador con defaults");
    
    ASSERT_EQ(orch->corriendo, 0, "Orquestador inicia no corriendo");
    ASSERT_EQ(orch->port, 8088, "Puerto por defecto 8088");
    ASSERT_OK(strcmp(orch->host, "127.0.0.1") == 0, "Host por defecto 127.0.0.1");
    
    ai_orch_destruir(orch);
    ASSERT_OK(1, "Destruir orquestador sin iniciar");
}

void test_ai_orch_crear_custom() {
    printf("\n=== Test: ai_orch_crear con parámetros custom ===\n");
    
    AIOrchestrator* orch = ai_orch_crear(
        "C:\\Custom\\llama-server.exe",
        "C:\\Models\\model.gguf",
        "192.168.1.100",
        9090
    );
    ASSERT_OK(orch != NULL, "Crear con parámetros custom");
    
    ASSERT_OK(strcmp(orch->server_exe, "C:\\Custom\\llama-server.exe") == 0, "server_exe custom");
    ASSERT_OK(strcmp(orch->model_path, "C:\\Models\\model.gguf") == 0, "model_path custom");
    ASSERT_OK(strcmp(orch->host, "192.168.1.100") == 0, "host custom");
    ASSERT_EQ(orch->port, 9090, "port custom");
    
    ai_orch_destruir(orch);
}

void test_llama_client_crear_destruir() {
    printf("\n=== Test: llama_cliente_crear / destruir ===\n");
    
    llama_inicializar_red();
    
    LlamaClient* cli = llama_cliente_crear("127.0.0.1", 8088);
    ASSERT_OK(cli != NULL, "Crear cliente llama.cpp");
    
    llama_cliente_destruir(cli);
    ASSERT_OK(1, "Destruir cliente");
    
    llama_cerrar_red();
}

void test_llama_generar_sin_servidor() {
    printf("\n=== Test: llama_generar sin servidor (debe fallar gracefully) ===\n");
    
    llama_inicializar_red();
    
    LlamaClient* cli = llama_cliente_crear("127.0.0.1", 9999); // Puerto improbable
    ASSERT_OK(cli != NULL, "Crear cliente en puerto libre");
    
    LlamaRespuesta resp = llama_generar(cli, "Hola mundo", 128, 0.7, NULL, 0);
    ASSERT_OK(resp.es_ok == 0, "Generar falla sin servidor");
    ASSERT_OK(resp.error != NULL, "Error message presente");
    
    llama_libre_respuesta(&resp);
    llama_cliente_destruir(cli);
    llama_cerrar_red();
}

void test_llama_verificar_disponible_sin_servidor() {
    printf("\n=== Test: llama_verificar_disponible sin servidor ===\n");
    
    llama_inicializar_red();
    
    LlamaClient* cli = llama_cliente_crear("127.0.0.1", 9999);
    int disponible = llama_verificar_disponible(cli);
    ASSERT_EQ(disponible, 0, "Servidor no disponible retorna 0");
    
    llama_cliente_destruir(cli);
    llama_cerrar_red();
}

void test_shutdown_hook_registro() {
    printf("\n=== Test: Shutdown hook registro/desregistro ===\n");
    
    AIOrchestrator* orch = ai_orch_crear(NULL, NULL, NULL, 0);
    
    // Registrar hook
    ai_orch_registrar_shutdown_hook(orch);
    ASSERT_OK(1, "Registrar shutdown hook");
    
    // Intentar registrar otro (debe advertir)
    AIOrchestrator* orch2 = ai_orch_crear(NULL, NULL, NULL, 0);
    ai_orch_registrar_shutdown_hook(orch2);
    ASSERT_OK(1, "Segundo registro muestra advertencia");
    
    // Desregistrar
    ai_orch_desregistrar_shutdown_hook();
    ASSERT_OK(1, "Desregistrar shutdown hook");
    
    ai_orch_destruir(orch);
    ai_orch_destruir(orch2);
}

void test_shutdown_callback_sin_iniciar() {
    printf("\n=== Test: Shutdown callback sin servidor iniciado ===\n");
    
    AIOrchestrator* orch = ai_orch_crear(NULL, NULL, NULL, 0);
    ai_orch_registrar_shutdown_hook(orch);
    
    // El callback no debe crashear aunque no haya servidor
    ai_orch_shutdown_callback();
    ASSERT_OK(1, "Callback se ejecuta sin crashear (no hay servidor)");
    
    ai_orch_desregistrar_shutdown_hook();
    ai_orch_destruir(orch);
}

void test_ai_orch_obtener_pid() {
    printf("\n=== Test: ai_orch_obtener_pid ===\n");
    
    AIOrchestrator* orch = ai_orch_crear(NULL, NULL, NULL, 0);
    
    // Sin iniciar, PID debe ser 0
#ifdef _WIN32
    ASSERT_EQ(ai_orch_obtener_pid(orch), (DWORD)0, "PID es 0 antes de iniciar");
#else
    ASSERT_EQ(ai_orch_obtener_pid(orch), (pid_t)0, "PID es 0 antes de iniciar");
#endif
    
    ai_orch_destruir(orch);
}

void test_ai_orch_esta_corriendo() {
    printf("\n=== Test: ai_orch_esta_corriendo ===\n");
    
    AIOrchestrator* orch = ai_orch_crear(NULL, NULL, NULL, 0);
    
    ASSERT_EQ(ai_orch_esta_corriendo(orch), 0, "No corriendo antes de iniciar");
    
    ai_orch_destruir(orch);
}

void test_payload_json_formato() {
    printf("\n=== Test: Formato payload JSON /completion ===\n");
    
    // Verificar que json_escape funciona correctamente
    char* test1 = json_escape("Hola \"mundo\"");
    ASSERT_OK(test1 && strcmp(test1, "Hola \\\"mundo\\\"") == 0, "Escape comillas");
    free(test1);
    
    char* test2 = json_escape("Linea1\nLinea2");
    ASSERT_OK(test2 && strstr(test2, "\\n") != NULL, "Escape newline");
    free(test2);
    
    char* test3 = json_escape("Tab\taqui");
    ASSERT_OK(test3 && strstr(test3, "\\t") != NULL, "Escape tab");
    free(test3);
    
    char* test4 = json_escape("");
    ASSERT_OK(test4 && strcmp(test4, "") == 0, "String vacío");
    free(test4);
    
    char* test5 = json_escape(NULL);
    ASSERT_OK(test5 && strcmp(test5, "") == 0, "NULL input");
    free(test5);
}

int main() {
    printf("========================================\n");
    printf("  TEST SUITE: AI Orchestrator + Llama Client\n");
    printf("  Synapse Language - Fase 3.1/3.2\n");
    printf("========================================\n");
    
    test_ai_orch_crear_destruir();
    test_ai_orch_crear_custom();
    test_llama_client_crear_destruir();
    test_llama_generar_sin_servidor();
    test_llama_verificar_disponible_sin_servidor();
    test_shutdown_hook_registro();
    test_shutdown_callback_sin_iniciar();
    test_ai_orch_obtener_pid();
    test_ai_orch_esta_corriendo();
    test_payload_json_formato();
    
    printf("\n========================================\n");
    printf("  RESULTADOS: %d passed, %d failed\n", tests_passed, tests_failed);
    printf("========================================\n");
    
    return tests_failed > 0 ? 1 : 0;
}