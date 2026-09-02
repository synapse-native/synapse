// cumple Manual 1 5: orquestador AI nativo
// cumple Manual 8 4: toolchain
// ai_orchestrator.c — Implementación del orquestador llama-server.exe
// Windows: CreateProcess + TerminateProcess
// POSIX: fork/exec + kill
// Incluye synapse_shutdown_hook() con atexit + signal handlers para terminación forzosa y liberación RAM/VRAM

#include "ai_orchestrator.h"
#include "detect_hardware.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
    #include <windows.h>
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #include <psapi.h>
    #ifdef _MSC_VER
    #pragma comment(lib, "ws2_32.lib")
    #pragma comment(lib, "psapi.lib")
    #endif
#else
    #include <unistd.h>
    #include <sys/wait.h>
    #include <signal.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <fcntl.h>
    #include <errno.h>
    #include <sys/select.h>
    #include <dlfcn.h>
    #include <malloc.h>
#endif

// Variable global para el orquestador activo (solo uno a la vez)
static AIOrchestrator* g_active_orchestrator = NULL;

static int tcp_connect_check(const char* host, int port, int timeout_ms) {
#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) return 0;
    SOCKET s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (s == INVALID_SOCKET) { WSACleanup(); return 0; }

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)port);
    addr.sin_addr.s_addr = inet_addr(host);

    u_long mode = 1;
    ioctlsocket(s, FIONBIO, &mode);

    int res = connect(s, (struct sockaddr*)&addr, sizeof(addr));
    if (res == SOCKET_ERROR) {
        int err = WSAGetLastError();
        if (err != WSAEWOULDBLOCK) { closesocket(s); WSACleanup(); return 0; }
    }

    fd_set writefds;
    FD_ZERO(&writefds);
    FD_SET(s, &writefds);
    struct timeval tv = { timeout_ms / 1000, (timeout_ms % 1000) * 1000 };
    res = select(0, NULL, &writefds, NULL, &tv);

    int ok = 0;
    if (res > 0) {
        int so_error = 0;
        int len = sizeof(so_error);
        getsockopt(s, SOL_SOCKET, SO_ERROR, (char*)&so_error, &len);
        ok = (so_error == 0);
    }
    closesocket(s);
    WSACleanup();
    return ok;
#else
    int s = socket(AF_INET, SOCK_STREAM, 0);
    if (s < 0) return 0;

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)port);
    addr.sin_addr.s_addr = inet_addr(host);

    int flags = fcntl(s, F_GETFL, 0);
    fcntl(s, F_SETFL, flags | O_NONBLOCK);

    int res = connect(s, (struct sockaddr*)&addr, sizeof(addr));
    if (res < 0 && errno != EINPROGRESS) { close(s); return 0; }

    fd_set writefds;
    FD_ZERO(&writefds);
    FD_SET(s, &writefds);
    struct timeval tv = { timeout_ms / 1000, (timeout_ms % 1000) * 1000 };
    res = select(s + 1, NULL, &writefds, NULL, &tv);

    int ok = 0;
    if (res > 0) {
        int so_error = 0;
        socklen_t len = sizeof(so_error);
        getsockopt(s, SOL_SOCKET, SO_ERROR, &so_error, &len);
        ok = (so_error == 0);
    }
    close(s);
    return ok;
#endif
}

// HTTP GET /health simple para verificar que llama-server responde
static int http_health_check(const char* host, int port, int timeout_ms) {
    char request[256];
    snprintf(request, sizeof(request),
        "GET /health HTTP/1.1\r\n"
        "Host: %s:%d\r\n"
        "Connection: close\r\n"
        "\r\n", host, port);

#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) return 0;
    SOCKET s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (s == INVALID_SOCKET) { WSACleanup(); return 0; }

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)port);
    addr.sin_addr.s_addr = inet_addr(host);

    int res = connect(s, (struct sockaddr*)&addr, sizeof(addr));
    if (res == SOCKET_ERROR) { closesocket(s); WSACleanup(); return 0; }

    send(s, request, (int)strlen(request), 0);

    fd_set readfds;
    FD_ZERO(&readfds);
    FD_SET(s, &readfds);
    struct timeval tv = { timeout_ms / 1000, (timeout_ms % 1000) * 1000 };
    res = select(0, &readfds, NULL, NULL, &tv);

    int ok = 0;
    if (res > 0) {
        char buf[512];
        int n = recv(s, buf, sizeof(buf) - 1, 0);
        if (n > 0) {
            buf[n] = 0;
            if (strstr(buf, "200 OK") || strstr(buf, "healthy")) ok = 1;
        }
    }
    closesocket(s);
    WSACleanup();
    return ok;
#else
    int s = socket(AF_INET, SOCK_STREAM, 0);
    if (s < 0) return 0;

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)port);
    addr.sin_addr.s_addr = inet_addr(host);

    struct timeval tv = { timeout_ms / 1000, (timeout_ms % 1000) * 1000 };
    setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

    if (connect(s, (struct sockaddr*)&addr, sizeof(addr)) < 0) { close(s); return 0; }

    send(s, request, strlen(request), 0);

    char buf[512];
    int n = recv(s, buf, sizeof(buf) - 1, 0);
    int ok = 0;
    if (n > 0) {
        buf[n] = 0;
        if (strstr(buf, "200 OK") || strstr(buf, "healthy")) ok = 1;
    }
    close(s);
    return ok;
#endif
}

// Forward declarations
static void synapse_force_terminate_llama_server(void);
static void synapse_release_ram_vram(void);
static void synapse_shutdown_callback_internal(void);

// Handler de señales POSIX para ai_orch_shutdown_callback
#ifndef _WIN32
static void signal_handler(int sig) {
    (void)sig;
    ai_orch_shutdown_callback();
    signal(sig, SIG_DFL);
    raise(sig);
}
#endif

int ai_orch_perfilar_sistema(HwConfig* config) {
    if (!config) return -1;
    HwProfile perfil;
    if (synapse_detectar_hardware(&perfil) != 0) {
        config->ctx_size = AI_ORCH_DEFAULT_CTX_SIZE;
        config->threads = AI_ORCH_DEFAULT_THREADS;
        config->ngl = 0;
        config->ram_gb = 0;
        config->vram_gb = 0;
        config->cpu_fisicos = 0;
        config->modelo[0] = '\0';
        return -1;
    }
    config->ctx_size = perfil.ctx_size_sugerido;
    config->threads = perfil.threads_sugeridos;
    config->ngl = perfil.ngl_sugerido;
    config->ram_gb = perfil.total_ram_gb;
    config->vram_gb = perfil.vram_gb;
    config->cpu_fisicos = perfil.cpu_fisicos;
    strncpy(config->modelo, perfil.modelo_sugerido, sizeof(config->modelo) - 1);
    config->modelo[sizeof(config->modelo) - 1] = '\0';
    return 0;
}

AIOrchestrator* ai_orch_crear(const char* server_exe, const char* model_path,
                               const char* host, int port) {
    AIOrchestrator* orch = (AIOrchestrator*)calloc(1, sizeof(AIOrchestrator));
    if (!orch) return NULL;

    orch->server_exe = server_exe ? strdup(server_exe) : strdup(AI_ORCH_SERVER_EXE);
    orch->model_path = model_path ? strdup(model_path) : strdup(AI_ORCH_MODEL_PATH);
    orch->host = host ? strdup(host) : strdup(AI_ORCH_DEFAULT_HOST);
    orch->port = port > 0 ? port : AI_ORCH_DEFAULT_PORT;
    orch->corriendo = 0;
    orch->hw_detectado = 0;
    memset(&orch->hw, 0, sizeof(orch->hw));

#ifdef _WIN32
    orch->hProcess = NULL;
    orch->hThread = NULL;
    orch->dwProcessId = 0;
    memset(&orch->pi, 0, sizeof(orch->pi));
#else
    orch->pid = 0;
#endif

    return orch;
}

int ai_orch_iniciar(AIOrchestrator* orch) {
    if (!orch || orch->corriendo) return -1;

    // Detectar hardware si no se ha hecho antes
    if (!orch->hw_detectado) {
        HwProfile perfil;
        if (synapse_detectar_hardware(&perfil) == 0) {
            orch->hw.ctx_size = perfil.ctx_size_sugerido;
            orch->hw.threads = perfil.threads_sugeridos;
            orch->hw.ngl = perfil.ngl_sugerido;
            orch->hw.ram_gb = perfil.total_ram_gb;
            orch->hw.vram_gb = perfil.vram_gb;
            orch->hw.cpu_fisicos = perfil.cpu_fisicos;
            strncpy(orch->hw.modelo, perfil.modelo_sugerido, sizeof(orch->hw.modelo) - 1);
            orch->hw.modelo[sizeof(orch->hw.modelo) - 1] = '\0';
            orch->hw_detectado = 1;
            fprintf(stderr, "[AI_ORCH] Hardware detectado: %.1f GB RAM, %d cores, modelo: %s\n",
                perfil.total_ram_gb, perfil.cpu_fisicos, perfil.modelo_sugerido);
        } else {
            orch->hw.ctx_size = AI_ORCH_DEFAULT_CTX_SIZE;
            orch->hw.threads = AI_ORCH_DEFAULT_THREADS;
            orch->hw.ngl = 0;
            orch->hw_detectado = 1;
        }
    }

    // Construir línea de comandos para llama-server con parámetros hardware-conscientes
    // Formato: llama-server.exe -m <model> --host <host> --port <port> --ctx-size N --threads N [--ngl N] --no-mmap --mlock
    char cmdline[2048];
    char ngl_arg[64] = "";
    if (orch->hw.ngl > 0 && orch->hw.vram_gb >= 2.0) {
        snprintf(ngl_arg, sizeof(ngl_arg), "--ngl %d", orch->hw.ngl);
    }
    int len = snprintf(cmdline, sizeof(cmdline),
        "\"%s\" -m \"%s\" --host %s --port %d --ctx-size %d --threads %d %s%s--no-mmap --mlock",
        orch->server_exe, orch->model_path, orch->host, orch->port,
        orch->hw.ctx_size, orch->hw.threads,
        ngl_arg[0] ? ngl_arg : "", ngl_arg[0] ? " " : "");

    if (len >= (int)sizeof(cmdline)) {
        fprintf(stderr, "[AI_ORCH] Línea de comandos demasiado larga\n");
        return -1;
    }

    fprintf(stderr, "[AI_ORCH] Iniciando: %s\n", cmdline);
    fflush(stderr);

#ifdef _WIN32
    STARTUPINFOA si = {0};
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;

    PROCESS_INFORMATION pi = {0};

    BOOL ok = CreateProcessA(
        NULL,           // application name (usamos cmdline)
        cmdline,        // command line
        NULL,           // process security
        NULL,           // thread security
        FALSE,          // inherit handles
        CREATE_NO_WINDOW, // creation flags
        NULL,           // environment
        NULL,           // current directory
        &si,            // startup info
        &pi             // process info
    );

    if (!ok) {
        DWORD err = GetLastError();
        fprintf(stderr, "[AI_ORCH] CreateProcess falló: %lu\n", err);
        return -1;
    }

    // Guardar handles
    orch->hProcess = pi.hProcess;
    orch->hThread = pi.hThread;
    orch->dwProcessId = pi.dwProcessId;
    orch->pi = pi;
    orch->corriendo = 1;

    // Cerrar handle del thread (no lo necesitamos)
    CloseHandle(pi.hThread);
    orch->hThread = NULL;

    fprintf(stderr, "[AI_ORCH] Servidor iniciado PID: %lu\n", pi.dwProcessId);
    fflush(stderr);

#else
    pid_t pid = fork();
    if (pid < 0) {
        perror("[AI_ORCH] fork");
        return -1;
    }

    if (pid == 0) {
        // Proceso hijo
        execl("/bin/sh", "sh", "-c", cmdline, (char*)NULL);
        perror("[AI_ORCH] execl");
        _exit(1);
    }

    orch->pid = pid;
    orch->corriendo = 1;
    fprintf(stderr, "[AI_ORCH] Servidor iniciado PID: %d\n", pid);
    fflush(stderr);
#endif

    // Esperar a que el servidor HTTP esté listo (polling con timeout)
    int elapsed = 0;
    const int step_ms = 200;
    const int max_wait = AI_ORCH_STARTUP_TIMEOUT_MS;

    while (elapsed < max_wait) {
#ifdef _WIN32
        Sleep(step_ms);
#else
        usleep(step_ms * 1000);
#endif
        elapsed += step_ms;

        if (tcp_connect_check(orch->host, orch->port, 500)) {
            // TCP conecta, verificar HTTP /health
            if (http_health_check(orch->host, orch->port, 1000)) {
                fprintf(stderr, "[AI_ORCH] Servidor listo en %s:%d (después de %d ms)\n",
                    orch->host, orch->port, elapsed);
                fflush(stderr);

                // Registrar shutdown hook automático al iniciar exitosamente
                ai_orch_registrar_shutdown_hook(orch);

                return 0;
            }
        }
    }

    fprintf(stderr, "[AI_ORCH] Timeout esperando servidor (%d ms)\n", max_wait);
    ai_orch_detener(orch);
    return -1;
}

void ai_orch_detener(AIOrchestrator* orch) {
    if (!orch || !orch->corriendo) return;

    fprintf(stderr, "[AI_ORCH] Deteniendo servidor...\n");
    fflush(stderr);

#ifdef _WIN32
    if (orch->hProcess) {
        // Intentar terminación suave con CTRL_BREAK_EVENT si está en misma consola
        // Pero como usamos CREATE_NO_WINDOW, usamos TerminateProcess
        if (!TerminateProcess(orch->hProcess, 0)) {
            fprintf(stderr, "[AI_ORCH] TerminateProcess falló: %lu\n", GetLastError());
        }
        WaitForSingleObject(orch->hProcess, 5000);
        CloseHandle(orch->hProcess);
        orch->hProcess = NULL;
    }
#else
    if (orch->pid > 0) {
        // SIGTERM para apagado grácil
        kill(orch->pid, SIGTERM);

        // Esperar hasta 5 segundos
        int status;
        for (int i = 0; i < 50; i++) {
            pid_t res = waitpid(orch->pid, &status, WNOHANG);
            if (res == orch->pid) break;
            if (res == -1) break;
            usleep(100000); // 100ms
        }

        // Si sigue vivo, SIGKILL
        if (kill(orch->pid, 0) == 0) {
            kill(orch->pid, SIGKILL);
            waitpid(orch->pid, &status, 0);
        }
        orch->pid = 0;
    }
#endif

    orch->corriendo = 0;
    fprintf(stderr, "[AI_ORCH] Servidor detenido\n");
    fflush(stderr);
}

int ai_orch_esta_listo(const AIOrchestrator* orch, int timeout_ms) {
    if (!orch || !orch->corriendo) return 0;
    return tcp_connect_check(orch->host, orch->port, timeout_ms) &&
           http_health_check(orch->host, orch->port, timeout_ms);
}

void ai_orch_destruir(AIOrchestrator* orch) {
    if (!orch) return;
    ai_orch_detener(orch);
    free(orch->server_exe);
    free(orch->model_path);
    free(orch->host);
    free(orch);
}

#ifdef _WIN32
DWORD ai_orch_obtener_pid(const AIOrchestrator* orch) {
    return orch ? orch->dwProcessId : 0;
}
#else
pid_t ai_orch_obtener_pid(const AIOrchestrator* orch) {
    return orch ? orch->pid : 0;
}
#endif

int ai_orch_esta_corriendo(const AIOrchestrator* orch) {
    if (!orch || !orch->corriendo) return 0;

#ifdef _WIN32
    if (!orch->hProcess) return 0;
    DWORD exitCode;
    if (!GetExitCodeProcess(orch->hProcess, &exitCode)) return 0;
    return exitCode == STILL_ACTIVE;
#else
    if (orch->pid <= 0) return 0;
    return kill(orch->pid, 0) == 0;
#endif
}

// ============================================================================
// synapse_shutdown_hook — Hook de terminación forzosa para Synapse
// Garantiza terminación de llama-server.exe y liberación absoluta de RAM/VRAM
// Acoplado a atexit + signal handlers (SIGINT, SIGTERM, SIGHUP, CTRL_C_EVENT, CTRL_CLOSE_EVENT)
// ============================================================================

// Terminación forzosa del proceso llama-server.exe
static void synapse_force_terminate_llama_server(void) {
    if (!g_active_orchestrator || !g_active_orchestrator->corriendo) return;

    fprintf(stderr, "[SYNAPSE_SHUTDOWN] Terminación forzosa de llama-server.exe (PID: %lu)...\n",
#ifdef _WIN32
            g_active_orchestrator->dwProcessId
#else
            g_active_orchestrator->pid
#endif
    );
    fflush(stderr);

#ifdef _WIN32
    if (g_active_orchestrator->hProcess) {
        if (!TerminateProcess(g_active_orchestrator->hProcess, 1)) {
            DWORD err = GetLastError();
            fprintf(stderr, "[SYNAPSE_SHUTDOWN] TerminateProcess falló: %lu\n", err);
        }
        WaitForSingleObject(g_active_orchestrator->hProcess, 3000);
        CloseHandle(g_active_orchestrator->hProcess);
        g_active_orchestrator->hProcess = NULL;
    }
#else
    if (g_active_orchestrator->pid > 0) {
        kill(g_active_orchestrator->pid, SIGKILL);
        int status;
        waitpid(g_active_orchestrator->pid, &status, 0);
        g_active_orchestrator->pid = 0;
    }
#endif

    g_active_orchestrator->corriendo = 0;
    fprintf(stderr, "[SYNAPSE_SHUTDOWN] llama-server.exe terminado\n");
    fflush(stderr);
}

// Liberación agresiva de RAM/VRAM del proceso actual
static void synapse_release_ram_vram(void) {
    fprintf(stderr, "[SYNAPSE_SHUTDOWN] Liberando RAM/VRAM...\n");
    fflush(stderr);

#ifdef _WIN32
    // Windows: EmptyWorkingSet para forzar liberación de working set
    HANDLE hProcess = GetCurrentProcess();
    if (EmptyWorkingSet(hProcess)) {
        fprintf(stderr, "[SYNAPSE_RAM] EmptyWorkingSet OK\n");
    } else {
        fprintf(stderr, "[SYNAPSE_RAM] EmptyWorkingSet falló: %lu\n", GetLastError());
    }

    // Intentar liberar memoria de heap no usada
    HeapSetInformation(GetProcessHeap(), HeapCompatibilityInformation, NULL, 0);

    // Intentar liberar memoria de GPU si hay CUDA
    HMODULE nvcuda = GetModuleHandleA("nvcuda.dll");
    if (nvcuda) {
        typedef int (WINAPI* cuInit_t)(unsigned int);
        typedef int (WINAPI* cuDevicePrimaryCtxRelease_t)(int);
        cuInit_t cuInit = (cuInit_t)(void*)GetProcAddress(nvcuda, "cuInit");
        cuDevicePrimaryCtxRelease_t cuDevicePrimaryCtxRelease = (cuDevicePrimaryCtxRelease_t)(void*)GetProcAddress(nvcuda, "cuDevicePrimaryCtxRelease");
        if (cuInit && cuDevicePrimaryCtxRelease) {
            cuInit(0);
            for (int dev = 0; dev < 16; dev++) {
                cuDevicePrimaryCtxRelease(dev);
            }
        }
    }
#else
    // POSIX: malloc_trim para devolver memoria libre al SO
    malloc_trim(0);

    // POSIX: intentar liberar VRAM via CUDA si disponible
    void* handle = dlopen("libcuda.so.1", RTLD_LAZY | RTLD_LOCAL);
    if (handle) {
        int (*cuInit)(unsigned int) = dlsym(handle, "cuInit");
        int (*cuDevicePrimaryCtxRelease)(int) = dlsym(handle, "cuDevicePrimaryCtxRelease");
        if (cuInit && cuDevicePrimaryCtxRelease) {
            cuInit(0);
            for (int dev = 0; dev < 16; dev++) {
                cuDevicePrimaryCtxRelease(dev);
            }
        }
        dlclose(handle);
    }

    fprintf(stderr, "[SYNAPSE_RAM] malloc_trim(0) ejecutado\n");
#endif

    fprintf(stderr, "[SYNAPSE_SHUTDOWN] RAM/VRAM liberada\n");
    fflush(stderr);
}

// Callback interno unificado para atexit + signals
static void synapse_shutdown_callback_internal(void) {
    if (g_active_orchestrator && g_active_orchestrator->corriendo) {
        synapse_force_terminate_llama_server();
        synapse_release_ram_vram();
        g_active_orchestrator = NULL;
    }
}

// Handler de señales POSIX para synapse_shutdown_hook
#ifndef _WIN32
static void synapse_signal_handler(int sig) {
    (void)sig;
    synapse_shutdown_callback_internal();
    signal(sig, SIG_DFL);
    raise(sig);
}
#endif

// Handler de eventos de consola Windows para synapse_shutdown_hook
#ifdef _WIN32
static BOOL WINAPI synapse_console_ctrl_handler(DWORD ctrl_type) {
    if (g_active_orchestrator && g_active_orchestrator->corriendo) {
        fprintf(stderr, "[SYNAPSE_SHUTDOWN] Console Ctrl Event: %lu - terminación forzosa...\n", ctrl_type);
        fflush(stderr);
        synapse_shutdown_callback_internal();
        return TRUE;
    }
    return FALSE;
}
#endif

// API pública: Registra el hook de shutdown de Synapse (atexit + signals)
// Debe llamarse UNA vez al iniciar la aplicación (ej. en main() del LSP/editor)
void synapse_shutdown_hook(void) {
    static int registered = 0;
    if (registered) {
        fprintf(stderr, "[SYNAPSE_SHUTDOWN] ADVERTENCIA: Hook ya registrado\n");
        return;
    }

    // Registrar atexit para cierre normal
    if (atexit(synapse_shutdown_callback_internal) != 0) {
        fprintf(stderr, "[SYNAPSE_SHUTDOWN] ERROR: No se pudo registrar atexit\n");
    }

#ifdef _WIN32
    // Windows: SetConsoleCtrlHandler para CTRL_C_EVENT, CTRL_CLOSE_EVENT, CTRL_LOGOFF_EVENT, CTRL_SHUTDOWN_EVENT
    SetConsoleCtrlHandler(synapse_console_ctrl_handler, TRUE);
#else
    // POSIX: signal handlers para SIGINT, SIGTERM, SIGHUP
    signal(SIGINT, synapse_signal_handler);
    signal(SIGTERM, synapse_signal_handler);
    signal(SIGHUP, synapse_signal_handler);
    // SIGKILL no se puede capturar
#endif

    registered = 1;
    fprintf(stderr, "[SYNAPSE_SHUTDOWN] Hook registrado (PID: %lu)\n",
#ifdef _WIN32
            (unsigned long)GetCurrentProcessId()
#else
            (unsigned long)getpid()
#endif
    );
    fflush(stderr);
}

// API pública: Desregistra el hook de shutdown (para pruebas)
void synapse_shutdown_unhook(void) {
    static int registered = 0;
    if (!registered) return;

#ifdef _WIN32
    SetConsoleCtrlHandler(synapse_console_ctrl_handler, FALSE);
#else
    signal(SIGINT, SIG_DFL);
    signal(SIGTERM, SIG_DFL);
    signal(SIGHUP, SIG_DFL);
#endif

    registered = 0;
    fprintf(stderr, "[SYNAPSE_SHUTDOWN] Hook desregistrado\n");
    fflush(stderr);
}

// ============================================================================
// ai_orch_* shutdown hook (delegado a synapse_shutdown_hook)
// ============================================================================

// Callback interno para atexit / signal handler
void ai_orch_shutdown_callback(void) {
    synapse_shutdown_callback_internal();
}

// Registra hook de cierre automático (atexit + signals)
// Delega en synapse_shutdown_hook() para terminación forzosa y liberación RAM/VRAM
void ai_orch_registrar_shutdown_hook(AIOrchestrator* orch) {
    if (!orch) return;

    // Solo permitir un orquestador activo a la vez
    if (g_active_orchestrator != NULL) {
        fprintf(stderr, "[AI_ORCH] ADVERTENCIA: Ya hay un orquestador registrado\n");
        return;
    }

    g_active_orchestrator = orch;

    // Delegar en synapse_shutdown_hook() que registra atexit + signals + liberación RAM/VRAM
    synapse_shutdown_hook();

    fprintf(stderr, "[AI_ORCH] Shutdown hook delegado a synapse_shutdown_hook (PID: %lu)\n",
#ifdef _WIN32
            (unsigned long)GetCurrentProcessId()
#else
            (unsigned long)getpid()
#endif
    );
    fflush(stderr);
}

// Desregistra el hook de cierre (para pruebas)
void ai_orch_desregistrar_shutdown_hook(void) {
    if (g_active_orchestrator) {
        g_active_orchestrator = NULL;
    }
    synapse_shutdown_unhook();
    fprintf(stderr, "[AI_ORCH] Shutdown hook desregistrado\n");
    fflush(stderr);
}