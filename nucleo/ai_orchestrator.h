// cumple Manual 1 5: orquestador AI nativo
// cumple Manual 8 4: toolchain
// ai_orchestrator.h — Orquestador del motor IA local (llama-server.exe)
// Parte del núcleo Synapse LSP nativo — C99, Windows (CreateProcess) / POSIX

#ifndef AI_ORCHESTRATOR_H
#define AI_ORCHESTRATOR_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// Configuración por defecto (sobrescribible por axon.toml en el futuro)
#define AI_ORCH_DEFAULT_HOST "127.0.0.1"
#define AI_ORCH_DEFAULT_PORT 8088
#define AI_ORCH_SERVER_EXE "C:\\Synapse\\ia\\llama-server.exe"
#define AI_ORCH_MODEL_PATH "C:\\Synapse\\ia\\model.gguf"
#define AI_ORCH_STARTUP_TIMEOUT_MS 15000
#define AI_ORCH_REQUEST_TIMEOUT_MS 30000
#define AI_ORCH_DEFAULT_CTX_SIZE 4096
#define AI_ORCH_DEFAULT_THREADS 4

// Include platform-specific headers for type definitions
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <sys/types.h>
#endif

// Configuración hardware-consciente
typedef struct {
    int ctx_size;
    int threads;
    int ngl;
    double ram_gb;
    double vram_gb;
    int cpu_fisicos;
    char modelo[128];
} HwConfig;

// Contexto opaco del orquestador
typedef struct AIOrchestrator {
    char* server_exe;
    char* model_path;
    char* host;
    int port;
    HwConfig hw;

#ifdef _WIN32
    HANDLE hProcess;
    HANDLE hThread;
    DWORD dwProcessId;
    PROCESS_INFORMATION pi;
#else
    pid_t pid;
#endif

    int corriendo;
    int hw_detectado;
} AIOrchestrator;

// Inicializa el orquestador (no inicia el servidor todavía)
AIOrchestrator* ai_orch_crear(const char* server_exe, const char* model_path,
                               const char* host, int port);

// Inicia llama-server.exe como proceso hijo con parámetros hardware-conscientes
// Retorna 0 en éxito, -1 en error
int ai_orch_iniciar(AIOrchestrator* orch);

// Ejecuta detección de hardware y devuelve configuración óptima
// Retorna 0 en éxito, -1 en error
int ai_orch_perfilar_sistema(HwConfig* config);

// Detiene el proceso hijo (SIGTERM / TerminateProcess)
void ai_orch_detener(AIOrchestrator* orch);

// Verifica si el servidor HTTP está respondiendo (TCP connect + HTTP GET /health)
int ai_orch_esta_listo(const AIOrchestrator* orch, int timeout_ms);

// Libera recursos del orquestador
void ai_orch_destruir(AIOrchestrator* orch);

// Obtiene el PID del proceso hijo (para depuración)
#ifdef _WIN32
DWORD ai_orch_obtener_pid(const AIOrchestrator* orch);
#else
pid_t ai_orch_obtener_pid(const AIOrchestrator* orch);
#endif

// Verifica si el proceso hijo sigue vivo
int ai_orch_esta_corriendo(const AIOrchestrator* orch);

// Registra hook de cierre automático (atexit + signals)
// Debe llamarse UNA vez al iniciar la aplicación
void ai_orch_registrar_shutdown_hook(AIOrchestrator* orch);

// Desregistra el hook de cierre (para pruebas)
void ai_orch_desregistrar_shutdown_hook(void);

// Callback interno para atexit / signal handler
void ai_orch_shutdown_callback(void);

// ============================================================================
// synapse_shutdown_hook — Hook de terminación forzosa para Synapse
// Garantiza terminación de llama-server.exe y liberación absoluta de RAM/VRAM
// Acoplado a atexit + signal handlers (SIGINT, SIGTERM, SIGHUP, CTRL_C_EVENT, CTRL_CLOSE_EVENT)
// ============================================================================

// Registra el hook de shutdown de Synapse (atexit + signals)
// Debe llamarse UNA vez al iniciar la aplicación (ej. en main() del LSP/editor)
void synapse_shutdown_hook(void);

// Desregistra el hook de shutdown (para pruebas)
void synapse_shutdown_unhook(void);

// ============================================================================
// Agent Skills Integration — soporte nativo para habilidades de agente
// Adaptado de addyosmani/agent-skills (MIT License)
// ============================================================================

// Inicia el proceso de generación con una habilidad específica
// skill_name: "tdd", "code_review", "planificacion", "context_pack", "doubt_driven"
// instruccion: texto con la tarea o código a procesar
// Retorna 0 en éxito, -1 en error
int ai_orch_skill_generar(AIOrchestrator* orch, const char* skill_name, const char* instruccion, char* output_buf, size_t output_buf_size);

// Envía un prompt al servidor llama con la habilidad especificada
// prompt_base: el SYSTEM_PROMPT de la habilidad
// query: la instrucción o código del usuario
// Retorna 0 en éxito, -1 en error
int ai_orch_enviar_skill_prompt(AIOrchestrator* orch, const char* prompt_base, const char* query, char* output_buf, size_t output_buf_size);

// Genera texto usando un modelo GGUF local (runtime nativo Synapse)
// A diferencia de ai_orch_enviar_skill_prompt, usa el modelo cargado directamente
// por _syn_modelo_cargar, sin necesidad de llama-server.exe externo
// skill_prompt: el SYSTEM_PROMPT de la habilidad (de std/agent_skills.syn)
// query: la instrucción o código del usuario
// model_path: ruta al archivo .gguf
// output_buf: buffer para el resultado
// output_buf_size: tamaño del buffer
// Retorna 0 en éxito, -1 en error
// cumple Manual 7 §6: integracion de agent-skills con runtime nativo
int ai_orch_skill_modelo_local(const char* skill_prompt, const char* query,
                                const char* model_path,
                                char* output_buf, size_t output_buf_size);

#ifdef __cplusplus
}
#endif

#endif // AI_ORCHESTRATOR_H