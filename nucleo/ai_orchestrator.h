// cumple Manual 1 §5: orquestador AI nativo
// cumple Manual 8 §4: toolchain
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

#ifdef __cplusplus
}
#endif

#endif // AI_ORCHESTRATOR_H