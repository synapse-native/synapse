// FASE 24 — Test de Web/HTTP (Manual 3 §12.1)
// TDD: este test ES la especificación. Si las funciones _syn_web_*
// no existen, el test NO compila — eso es correcto.
//
// Manual 3 §12.1: lib/web.syq — Servidor HTTP básico
// Comando: pytest tests/syquex/test_web.py -v
// Criterio: crear, registrar rutas, iniciar, hacer request, detener

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
typedef int socklen_t;
#define CLOSESOCKET closesocket
#else
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#define CLOSESOCKET close
#endif

#include "synapse_rt_types.h"
#include "runtime/core/web.h"

static int passed = 0;
static int failed = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { printf("  [FAIL] %s\n", msg); failed++; } \
    else { printf("  [PASS] %s\n", msg); passed++; } \
} while(0)

#define CS(s) ((CadenaSegura){ .longitud = (int)strlen(s), .datos = (s) })

/* Helper: send raw HTTP request and read response */
static int _http_get(const char* host, int port, const char* path, char* resp, int resp_size) {
    SOCKET fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return -1;

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)port);
    addr.sin_addr.s_addr = inet_addr(host);

    if (connect(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        CLOSESOCKET(fd);
        return -2;
    }

    char req[512];
    int rlen = snprintf(req, sizeof(req), "GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n", path, host);
    send(fd, req, rlen, 0);

    int total = 0;
    while (total < resp_size - 1) {
        int n = recv(fd, resp + total, resp_size - 1 - total, 0);
        if (n <= 0) break;
        total += n;
    }
    resp[total] = '\0';
    CLOSESOCKET(fd);
    return total;
}

int main(void) {
    setbuf(stdout, NULL);

    // === 1. Crear / Destruir ===
    printf("=== 1. Crear / Destruir ===\n");
    int64_t s = _syn_web_crear(0); /* puerto 0 = test */
    CHECK(s >= 0, "crear retorna servidor >= 0");

    // === 2. Registrar rutas ===
    printf("=== 2. Registrar rutas ===\n");
    int64_t r = _syn_web_registrar_ruta(s, CS("GET"), CS("/"), CS("Hola mundo"));
    CHECK(r == 0, "registrar_ruta rc=0");

    r = _syn_web_registrar_ruta_codigo(s, CS("GET"), CS("/api/status"), 200, CS("{\"ok\":true}"));
    CHECK(r == 0, "registrar_ruta_codigo rc=0");

    // === 3. Iniciar ===
    printf("=== 3. Iniciar ===\n");
    r = _syn_web_iniciar(s);
    CHECK(r == 0, "iniciar rc=0");
    CHECK(_syn_web_esta_corriendo(s) == 1, "esta_corriendo == 1");

    /* Get the actual port (from the listen socket) */
    /* We use a known port for testing */
    _syn_web_detener(s);
    _syn_web_destruir(s);

    /* Re-crear with a fixed port */
    s = _syn_web_crear(18765);
    _syn_web_registrar_ruta(s, CS("GET"), CS("/"), CS("Hola mundo"));
    _syn_web_registrar_ruta_codigo(s, CS("GET"), CS("/api/status"), 200, CS("{\"ok\":true}"));
    _syn_web_registrar_ruta(s, CS("GET"), CS("/texto"), CS("Contenido plano"));

    r = _syn_web_iniciar(s);
    CHECK(r == 0, "iniciar en puerto 18765 rc=0");

    /* Small delay for the server to start */
#ifdef _WIN32
    Sleep(200);
#else
    usleep(200000);
#endif

    // === 4. GET / ===
    printf("=== 4. GET / ===\n");
    char resp[4096];
    int n = _http_get("127.0.0.1", 18765, "/", resp, sizeof(resp));
    CHECK(n > 0, "GET / retorna datos");
    CHECK(strstr(resp, "200 OK") != NULL, "GET / status 200");
    CHECK(strstr(resp, "Hola mundo") != NULL, "GET / body == 'Hola mundo'");

    // === 5. GET /api/status ===
    printf("=== 5. GET /api/status ===\n");
    n = _http_get("127.0.0.1", 18765, "/api/status", resp, sizeof(resp));
    CHECK(n > 0, "GET /api/status retorna datos");
    CHECK(strstr(resp, "{\"ok\":true}") != NULL, "GET /api/status body JSON");

    // === 6. GET /texto ===
    printf("=== 6. GET /texto ===\n");
    n = _http_get("127.0.0.1", 18765, "/texto", resp, sizeof(resp));
    CHECK(n > 0, "GET /texto retorna datos");
    CHECK(strstr(resp, "Contenido plano") != NULL, "GET /texto body");

    // === 7. GET /noexiste → 404 ===
    printf("=== 7. GET /noexiste (404) ===\n");
    n = _http_get("127.0.0.1", 18765, "/noexiste", resp, sizeof(resp));
    CHECK(n > 0, "GET /noexiste retorna datos");
    CHECK(strstr(resp, "404") != NULL, "GET /noexiste status 404");

    // === 8. Detener ===
    printf("=== 8. Detener ===\n");
    _syn_web_detener(s);
    CHECK(_syn_web_esta_corriendo(s) == 0, "esta_corriendo == 0 tras detener");

    // === 9. Destruir ===
    printf("=== 9. Destruir ===\n");
    _syn_web_destruir(s);
    CHECK(1, "destruir no crashea");

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
