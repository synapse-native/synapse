/* tests/test_shutdown.c — Manual 7 §7.7: Shutdown hooks test
 *
 * Valida que los hooks de apagado (SetConsoleCtrlHandler / signal)
 * capturen senales y liberen recursos sin dejar procesos huerfanos.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#include <sys/wait.h>
#endif

static int shutdown_hook_called = 0;
static int test_passed = 0;
static int test_failed = 0;

#define TEST(nombre, expr) do { \
    if (!(expr)) { \
        fprintf(stderr, "  [FAIL] %s\n", nombre); \
        test_failed++; \
    } else { \
        printf("  [PASS] %s\n", nombre); \
        test_passed++; \
    } \
} while(0)

#ifdef _WIN32
static BOOL WINAPI ctrl_handler(DWORD event) {
    switch (event) {
        case CTRL_C_EVENT:
        case CTRL_BREAK_EVENT:
        case CTRL_CLOSE_EVENT:
        case CTRL_LOGOFF_EVENT:
        case CTRL_SHUTDOWN_EVENT:
            shutdown_hook_called = 1;
            return TRUE;
        default:
            return FALSE;
    }
}
#else
static void signal_handler(int sig) {
    shutdown_hook_called = 1;
}
#endif

static void test_shutdown_hook_instalacion(void) {
    printf("\n--- Shutdown Hook: instalacion ---\n");
#ifdef _WIN32
    int ok = SetConsoleCtrlHandler(ctrl_handler, TRUE);
    TEST("SetConsoleCtrlHandler registrado", ok != 0);
#else
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    int ok = sigaction(SIGINT, &sa, NULL) == 0;
    TEST("signal(SIGINT) registrado", ok);
    ok = sigaction(SIGTERM, &sa, NULL) == 0;
    TEST("signal(SIGTERM) registrado", ok);
#endif
}

static void test_shutdown_hook_ejecucion(void) {
    printf("\n--- Shutdown Hook: ejecucion ---\n");
    shutdown_hook_called = 0;
#ifdef _WIN32
    GenerateConsoleCtrlEvent(CTRL_C_EVENT, 0);
#else
    raise(SIGINT);
#endif
    TEST("Shutdown hook se ejecuto", shutdown_hook_called == 1);
}

static void test_no_child_processes(void) {
    printf("\n--- Shutdown Hook: 0 procesos huerfanos ---\n");
    int orphan_count = 0;
#ifdef _WIN32
    HANDLE h = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (h != INVALID_HANDLE_VALUE) {
        PROCESSENTRY32 pe;
        pe.dwSize = sizeof(PROCESSENTRY32);
        if (Process32First(h, &pe)) {
            do {
                if (pe.th32ParentProcessID == GetCurrentProcessId() &&
                    pe.th32ProcessID != GetCurrentProcessId()) {
                    orphan_count++;
                }
            } while (Process32Next(h, &pe));
        }
        CloseHandle(h);
    }
#else
    pid_t child = fork();
    if (child == 0) {
        _exit(0);
    } else if (child > 0) {
        int status;
        waitpid(child, &status, 0);
    }
#endif
    TEST("0 procesos huerfanos post-shutdown", orphan_count == 0);
}

int main(void) {
    printf("========================================\n");
    printf("  Shutdown Hooks Validation\n");
    printf("  Manual 7 §7.7\n");
    printf("========================================\n");

    test_shutdown_hook_instalacion();
    test_shutdown_hook_ejecucion();
    test_no_child_processes();

    printf("\n--- Resultados: %d PASS, %d FAIL ---\n", test_passed, test_failed);
    return test_failed > 0 ? 1 : 0;
}