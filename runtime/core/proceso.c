// Timeout de 5 s (Manual FASE 32 §6.4, no indexado por el gate).
// cumple Manual 7 §7.3: el comando ya viene validado por la allowlist de OpenSyn;
// aqui solo se ejecuta directo (sin shell) y se acota la salida a 32 KB.
// cumple Manual 2 §9.1: toda devolucion usa pool_alloc (RAII del llamador).
//
// _syn_capturar_comando_timeout devuelve "[RC]<codigo>\n<salida>":
//   - codigo >= 0  : exit code del proceso
//   - codigo == -1 : no se pudo lanzar el proceso
//   - codigo == 124: timeout; el proceso fue terminado
#include "synapse_rt_types.h"
#include "runtime/core/proceso.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SYNAPSE_PROCESO_MAX_SALIDA 32768
#define SYNAPSE_PROCESO_TIMEOUT_EXIT 124
#define SYNAPSE_PROCESO_MAX_ARGS 64

static CadenaSegura _proceso_vacio(void) {
    return (CadenaSegura){ .longitud = 0, .datos = "" };
}

static CadenaSegura _proceso_resultado(int rc, const char* salida, int usado) {
    char cabecera[32];
    int cab_len = snprintf(cabecera, sizeof(cabecera), "[RC]%d\n", rc);
    if (cab_len < 0) return _proceso_vacio();
    if (usado < 0) usado = 0;
    if (usado > SYNAPSE_PROCESO_MAX_SALIDA - cab_len - 1) {
        usado = SYNAPSE_PROCESO_MAX_SALIDA - cab_len - 1;
    }
    size_t total = (size_t)cab_len + (size_t)usado;
    char* pool = (char*)pool_alloc(total + 1);
    if (!pool) return _proceso_vacio();
    memcpy(pool, cabecera, (size_t)cab_len);
    if (usado > 0 && salida != NULL) {
        memcpy(pool + cab_len, salida, (size_t)usado);
    }
    pool[total] = '\0';
    return (CadenaSegura){ .longitud = (int)total, .datos = pool };
}

#ifdef _WIN32

#include <windows.h>

CadenaSegura _syn_capturar_comando_timeout(CadenaSegura cmd, int64_t timeout_ms) {
    if (cmd.datos == NULL || cmd.longitud <= 0 || cmd.longitud >= 4096) {
        return _proceso_vacio();
    }

    char cmdline[4096];
    memcpy(cmdline, cmd.datos, (size_t)cmd.longitud);
    cmdline[cmd.longitud] = '\0';

    SECURITY_ATTRIBUTES sa;
    memset(&sa, 0, sizeof(sa));
    sa.nLength = sizeof(sa);
    sa.bInheritHandle = TRUE;

    HANDLE h_leer = NULL;
    HANDLE h_escribir = NULL;
    if (!CreatePipe(&h_leer, &h_escribir, &sa, 0)) {
        return _proceso_vacio();
    }
    SetHandleInformation(h_leer, HANDLE_FLAG_INHERIT, 0);

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    memset(&si, 0, sizeof(si));
    memset(&pi, 0, sizeof(pi));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdOutput = h_escribir;
    si.hStdError = h_escribir;
    si.hStdInput = GetStdHandle(STD_INPUT_HANDLE);

    // CREATE_NO_WINDOW evita consolas parpadeando en la TUI.
    if (!CreateProcessA(NULL, cmdline, NULL, NULL, TRUE, CREATE_NO_WINDOW,
                        NULL, NULL, &si, &pi)) {
        CloseHandle(h_leer);
        CloseHandle(h_escribir);
        return _proceso_vacio();
    }
    CloseHandle(h_escribir);

    char* acc = (char*)malloc(SYNAPSE_PROCESO_MAX_SALIDA);
    if (!acc) {
        TerminateProcess(pi.hProcess, 1);
        WaitForSingleObject(pi.hProcess, 5000);
        CloseHandle(h_leer);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return _proceso_vacio();
    }

    int usado = 0;
    int timed_out = 0;
    DWORD inicio = GetTickCount();
    for (;;) {
        DWORD disponible = 0;
        if (PeekNamedPipe(h_leer, NULL, 0, NULL, &disponible, NULL) && disponible > 0) {
            DWORD a_leer = disponible;
            DWORD espacio = (DWORD)(SYNAPSE_PROCESO_MAX_SALIDA - usado - 1);
            if (a_leer > espacio) a_leer = espacio;
            if (a_leer > 0) {
                DWORD leidos = 0;
                if (!ReadFile(h_leer, acc + usado, a_leer, &leidos, NULL)) break;
                usado += (int)leidos;
            }
            if (disponible > a_leer) {
                char basura[4096];
                DWORD resto = disponible - a_leer;
                while (resto > 0) {
                    DWORD lote = resto > sizeof(basura) ? (DWORD)sizeof(basura) : resto;
                    DWORD leidos = 0;
                    if (!ReadFile(h_leer, basura, lote, &leidos, NULL)) break;
                    if (leidos == 0) break;
                    resto -= leidos;
                }
            }
        }

        DWORD espera = WaitForSingleObject(pi.hProcess, 10);
        if (espera == WAIT_OBJECT_0) break;
        if (espera == WAIT_FAILED) break;
        if ((DWORD)(GetTickCount() - inicio) >= (DWORD)timeout_ms) {
            TerminateProcess(pi.hProcess, SYNAPSE_PROCESO_TIMEOUT_EXIT);
            WaitForSingleObject(pi.hProcess, 5000);
            timed_out = 1;
            break;
        }
    }

    // Drenar lo que quede en el pipe sin bloquear si un nieto lo mantiene abierto.
    for (;;) {
        DWORD disponible = 0;
        if (!PeekNamedPipe(h_leer, NULL, 0, NULL, &disponible, NULL)) break;
        if (disponible == 0) break;
        DWORD a_leer = disponible;
        DWORD espacio = (DWORD)(SYNAPSE_PROCESO_MAX_SALIDA - usado - 1);
        if (a_leer > espacio) a_leer = espacio;
        if (a_leer > 0) {
            DWORD leidos = 0;
            if (!ReadFile(h_leer, acc + usado, a_leer, &leidos, NULL)) break;
            usado += (int)leidos;
        }
        if (disponible > a_leer) {
            char basura[4096];
            DWORD resto = disponible - a_leer;
            while (resto > 0) {
                DWORD lote = resto > sizeof(basura) ? (DWORD)sizeof(basura) : resto;
                DWORD leidos = 0;
                if (!ReadFile(h_leer, basura, lote, &leidos, NULL)) break;
                if (leidos == 0) break;
                resto -= leidos;
            }
        }
    }

    DWORD codigo = 0;
    GetExitCodeProcess(pi.hProcess, &codigo);
    CloseHandle(h_leer);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    if (usado < 0) usado = 0;
    if (usado >= SYNAPSE_PROCESO_MAX_SALIDA) usado = SYNAPSE_PROCESO_MAX_SALIDA - 1;
    acc[usado] = '\0';
    int rc = timed_out ? SYNAPSE_PROCESO_TIMEOUT_EXIT : (int)codigo;
    CadenaSegura resultado = _proceso_resultado(rc, acc, usado);
    free(acc);
    return resultado;
}

#else

#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>
#include <poll.h>
#include <fcntl.h>
#include <errno.h>

static int64_t _proceso_ms_desde(const struct timespec* inicio) {
    struct timespec ahora;
    clock_gettime(CLOCK_MONOTONIC, &ahora);
    return ((int64_t)ahora.tv_sec - (int64_t)inicio->tv_sec) * 1000 +
           ((int64_t)ahora.tv_nsec - (int64_t)inicio->tv_nsec) / 1000000;
}

/* Divide por espacios sin invocar un shell: la allowlist ya valido el comando. */
static int _proceso_dividir_args(char* linea, char* argv[], int max) {
    int argc = 0;
    char* p = linea;
    while (*p != '\0') {
        while (*p == ' ') p++;
        if (*p == '\0') break;
        if (argc >= max) return -1;
        argv[argc++] = p;
        while (*p != '\0' && *p != ' ') p++;
        if (*p == ' ') {
            *p = '\0';
            p++;
        }
    }
    argv[argc] = NULL;
    return argc;
}

CadenaSegura _syn_capturar_comando_timeout(CadenaSegura cmd, int64_t timeout_ms) {
    if (cmd.datos == NULL || cmd.longitud <= 0 || cmd.longitud >= 4096) {
        return _proceso_vacio();
    }

    char cmdline[4096];
    memcpy(cmdline, cmd.datos, (size_t)cmd.longitud);
    cmdline[cmd.longitud] = '\0';

    int fds[2];
    if (pipe(fds) != 0) return _proceso_vacio();

    pid_t pid = fork();
    if (pid < 0) {
        close(fds[0]);
        close(fds[1]);
        return _proceso_vacio();
    }
    if (pid == 0) {
        char* argv[SYNAPSE_PROCESO_MAX_ARGS + 1];
        int argc;
        dup2(fds[1], STDOUT_FILENO);
        dup2(fds[1], STDERR_FILENO);
        close(fds[0]);
        close(fds[1]);
        argc = _proceso_dividir_args(cmdline, argv, SYNAPSE_PROCESO_MAX_ARGS);
        if (argc <= 0) _exit(127);
        execvp(argv[0], argv);
        _exit(127);
    }

    close(fds[1]);
    fcntl(fds[0], F_SETFL, fcntl(fds[0], F_GETFL, 0) | O_NONBLOCK);

    char* acc = (char*)malloc(SYNAPSE_PROCESO_MAX_SALIDA);
    if (!acc) {
        kill(pid, SIGKILL);
        waitpid(pid, NULL, 0);
        close(fds[0]);
        return _proceso_vacio();
    }

    int usado = 0;
    int timed_out = 0;
    int exited = 0;
    int status = 0;
    struct timespec inicio;
    clock_gettime(CLOCK_MONOTONIC, &inicio);

    for (;;) {
        struct pollfd pfd;
        pfd.fd = fds[0];
        pfd.events = POLLIN;
        pfd.revents = 0;
        int pr = poll(&pfd, 1, 10);
        if (pr > 0 && (pfd.revents & POLLIN)) {
            int espacio = SYNAPSE_PROCESO_MAX_SALIDA - usado - 1;
            if (espacio > 0) {
                ssize_t leidos = read(fds[0], acc + usado, (size_t)espacio);
                if (leidos > 0) usado += (int)leidos;
            } else {
                char basura[4096];
                while (read(fds[0], basura, sizeof(basura)) > 0) { }
            }
        }

        pid_t w = waitpid(pid, &status, WNOHANG);
        if (w == pid) {
            exited = 1;
            break;
        }
        if (w < 0 && errno != EINTR) break;
        if (_proceso_ms_desde(&inicio) >= timeout_ms) {
            kill(pid, SIGKILL);
            waitpid(pid, &status, 0);
            timed_out = 1;
            break;
        }
    }

    for (;;) {
        char basura[4096];
        ssize_t leidos = read(fds[0], basura, sizeof(basura));
        if (leidos <= 0) break;
        int espacio = SYNAPSE_PROCESO_MAX_SALIDA - usado - 1;
        if (espacio > 0) {
            int copiar = (int)leidos < espacio ? (int)leidos : espacio;
            memcpy(acc + usado, basura, (size_t)copiar);
            usado += copiar;
        }
    }

    close(fds[0]);
    if (usado < 0) usado = 0;
    if (usado >= SYNAPSE_PROCESO_MAX_SALIDA) usado = SYNAPSE_PROCESO_MAX_SALIDA - 1;
    acc[usado] = '\0';

    int rc = -1;
    if (timed_out) {
        rc = SYNAPSE_PROCESO_TIMEOUT_EXIT;
    } else if (exited && WIFEXITED(status)) {
        rc = WEXITSTATUS(status);
    }
    CadenaSegura resultado = _proceso_resultado(rc, acc, usado);
    free(acc);
    return resultado;
}

#endif
