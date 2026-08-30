// runtime/core/web.c — HTTP server module for Syquex
// Manual 3 §12.1: lib/web.syq
// Servidor HTTP básico con winsock2 (Windows) / sockets (POSIX)
// Compilar: gcc -c runtime/core/web.c -o web.o -lpthread -lws2_32

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
typedef int socklen_t;
#define CLOSESOCKET closesocket
#else
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#define CLOSESOCKET close
typedef int SOCKET;
#define INVALID_SOCKET (-1)
#define SOCKET_ERROR (-1)
#endif

#include "synapse_rt_types.h"
#include "web.h"

// ============================================================
// Internal structures
// ============================================================

#define MAX_ROUTES 64
#define MAX_SERVERS 8
#define MAX_PENDING 16
#define REQ_BUF_SIZE 8192
#define RES_BUF_SIZE 65536
#define METHOD_MAX 8
#define WEB_PATH_MAX 256
#define HEADER_NAME_MAX 64
#define HEADER_VAL_MAX 256

typedef struct {
    char metodo[METHOD_MAX];
    char ruta[WEB_PATH_MAX];
    char contenido[RES_BUF_SIZE];
    int64_t codigo;
    int tiene_codigo; /* 1 = usar codigo, 0 = 200 por defecto */
} Route;

typedef struct {
    Route routes[MAX_ROUTES];
    int route_count;
    int64_t puerto;
    SOCKET listen_fd;
    volatile int running;
    int active; /* 1 = slot in use */

    /* Current request context (set during handle_request) */
    char req_metodo[METHOD_MAX];
    char req_ruta[PATH_MAX];
    char req_body[REQ_BUF_SIZE];
    char req_headers[16][HEADER_NAME_MAX + HEADER_VAL_MAX];
    int req_header_count;
    int64_t req_socket;
} Server;

static Server _servers[MAX_SERVERS];
static int _web_initialized = 0;

static void _web_init(void) {
    if (_web_initialized) return;
    memset(_servers, 0, sizeof(_servers));
#ifdef _WIN32
    WSADATA wsa;
    WSAStartup(MAKEWORD(2, 2), &wsa);
#endif
    _web_initialized = 1;
}

static void _web_cleanup(void) {
#ifdef _WIN32
    WSACleanup();
#endif
}

static int _find_free_server(void) {
    for (int i = 0; i < MAX_SERVERS; i++) {
        if (!_servers[i].active) return i;
    }
    return -1;
}

// ============================================================
// HTTP parsing helpers
// ============================================================

static void _parse_request(SOCKET client_fd, Server* srv) {
    char buf[REQ_BUF_SIZE];
    memset(buf, 0, sizeof(buf));

    int total = 0;
    while (total < REQ_BUF_SIZE - 1) {
        int n = recv(client_fd, buf + total, REQ_BUF_SIZE - 1 - total, 0);
        if (n <= 0) break;
        total += n;
        /* Check for end of headers */
        if (strstr(buf, "\r\n\r\n")) break;
    }
    buf[total] = '\0';

    /* Parse method and path */
    srv->req_metodo[0] = '\0';
    srv->req_ruta[0] = '\0';
    srv->req_body[0] = '\0';
    srv->req_header_count = 0;

    sscanf(buf, "%7s %255s", srv->req_metodo, srv->req_ruta);

    /* Parse headers */
    char* hdr_start = strstr(buf, "\r\n");
    if (hdr_start) {
        hdr_start += 2;
        char* hdr_end = strstr(buf, "\r\n\r\n");
        char* line = hdr_start;
        while (line && line < hdr_end && srv->req_header_count < 16) {
            char* eol = strstr(line, "\r\n");
            if (!eol) break;
            int line_len = (int)(eol - line);
            if (line_len <= 0) break;

            char* colon = memchr(line, ':', line_len);
            if (colon) {
                int name_len = (int)(colon - line);
                int val_start = 1; /* skip ':' */
                while (val_start < line_len && line[val_start] == ' ') val_start++;
                int val_len = line_len - val_start;

                if (name_len < HEADER_NAME_MAX && val_len < HEADER_VAL_MAX) {
                    char* dst = srv->req_headers[srv->req_header_count];
                    memcpy(dst, line, name_len);
                    dst[name_len] = '\0';
                    memcpy(dst + HEADER_NAME_MAX, line + val_start, val_len);
                    dst[HEADER_NAME_MAX + val_len] = '\0';
                    srv->req_header_count++;
                }
            }
            line = eol + 2;
        }

        /* Parse body (after \r\n\r\n) */
        char* body = strstr(buf, "\r\n\r\n");
        if (body) {
            body += 4;
            int body_len = total - (int)(body - buf);
            if (body_len > 0 && body_len < REQ_BUF_SIZE) {
                memcpy(srv->req_body, body, body_len);
                srv->req_body[body_len] = '\0';
            }
        }
    }
}

static void _send_response(SOCKET client_fd, int64_t codigo, const char* content_type, const char* body, int body_len) {
    char header[512];
    int hlen = snprintf(header, sizeof(header),
        "HTTP/1.1 %lld %s\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %d\r\n"
        "Connection: close\r\n"
        "\r\n",
        (long long)codigo,
        (codigo == 200) ? "OK" : (codigo == 404) ? "Not Found" : "Error",
        content_type,
        body_len);

    send(client_fd, header, hlen, 0);
    if (body_len > 0 && body) {
        send(client_fd, body, body_len, 0);
    }
}

// ============================================================
// §12.1 — Crear / Destruir
// ============================================================

int64_t _syn_web_crear(int64_t puerto) {
    _web_init();
    int idx = _find_free_server();
    if (idx < 0) return -1;

    memset(&_servers[idx], 0, sizeof(Server));
    _servers[idx].puerto = puerto;
    _servers[idx].listen_fd = INVALID_SOCKET;
    _servers[idx].active = 1;
    _servers[idx].running = 0;
    return (int64_t)idx;
}

void _syn_web_destruir(int64_t servidor) {
    if (servidor < 0 || servidor >= MAX_SERVERS) return;
    if (!_servers[servidor].active) return;

    _syn_web_detener(servidor);
    _servers[servidor].active = 0;
}

// ============================================================
// §12.1 — Registrar rutas
// ============================================================

static int _find_free_route(Server* srv) {
    for (int i = 0; i < MAX_ROUTES; i++) {
        if (srv->routes[i].metodo[0] == '\0') return i;
    }
    return -1;
}

static int _copy_cadena(char* dst, int dst_size, CadenaSegura src) {
    int len = src.longitud;
    if (len >= dst_size) len = dst_size - 1;
    memcpy(dst, src.datos, len);
    dst[len] = '\0';
    return len;
}

int64_t _syn_web_registrar_ruta(int64_t servidor, CadenaSegura metodo, CadenaSegura ruta, CadenaSegura contenido) {
    return _syn_web_registrar_ruta_codigo(servidor, metodo, ruta, 200, contenido);
}

int64_t _syn_web_registrar_ruta_codigo(int64_t servidor, CadenaSegura metodo, CadenaSegura ruta, int64_t codigo, CadenaSegura contenido) {
    if (servidor < 0 || servidor >= MAX_SERVERS) return -1;
    if (!_servers[servidor].active) return -1;

    int idx = _find_free_route(&_servers[servidor]);
    if (idx < 0) return -1;

    Route* r = &_servers[servidor].routes[idx];
    _copy_cadena(r->metodo, METHOD_MAX, metodo);
    _copy_cadena(r->ruta, PATH_MAX, ruta);
    int clen = _copy_cadena(r->contenido, RES_BUF_SIZE, contenido);
    r->codigo = codigo;
    r->tiene_codigo = 1;

    _servers[servidor].route_count++;
    return 0;
}

// ============================================================
// §12.1 — Iniciar / Detener
// ============================================================

#ifdef _WIN32
static DWORD WINAPI _web_thread(LPVOID param) {
    Server* srv = (Server*)param;
#else
static void* _web_thread(void* param) {
    Server* srv = (Server*)param;
#endif

    while (srv->running) {
        struct sockaddr_in client_addr;
        socklen_t addr_len = sizeof(client_addr);
        SOCKET client = accept(srv->listen_fd, (struct sockaddr*)&client_addr, &addr_len);
        if (client == INVALID_SOCKET) continue;

        _parse_request(client, srv);

        /* Find matching route */
        int found = 0;
        for (int i = 0; i < MAX_ROUTES; i++) {
            Route* r = &srv->routes[i];
            if (r->metodo[0] == '\0') continue;
            if (strcmp(r->metodo, srv->req_metodo) == 0 && strcmp(r->ruta, srv->req_ruta) == 0) {
                int64_t codigo = r->tiene_codigo ? r->codigo : 200;
                _send_response(client, codigo, "text/plain; charset=utf-8", r->contenido, (int)strlen(r->contenido));
                found = 1;
                break;
            }
        }
        if (!found) {
            _send_response(client, 404, "text/plain; charset=utf-8", "Not Found", 9);
        }

        CLOSESOCKET(client);
    }

#ifdef _WIN32
    return 0;
#else
    return NULL;
#endif
}

int64_t _syn_web_iniciar(int64_t servidor) {
    if (servidor < 0 || servidor >= MAX_SERVERS) return -1;
    if (!_servers[servidor].active) return -1;

    Server* srv = &_servers[servidor];

    srv->listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (srv->listen_fd == INVALID_SOCKET) return -2;

    int opt = 1;
    setsockopt(srv->listen_fd, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons((unsigned short)srv->puerto);

    if (bind(srv->listen_fd, (struct sockaddr*)&addr, sizeof(addr)) == SOCKET_ERROR) {
        CLOSESOCKET(srv->listen_fd);
        srv->listen_fd = INVALID_SOCKET;
        return -3;
    }

    if (listen(srv->listen_fd, MAX_PENDING) == SOCKET_ERROR) {
        CLOSESOCKET(srv->listen_fd);
        srv->listen_fd = INVALID_SOCKET;
        return -4;
    }

    srv->running = 1;

#ifdef _WIN32
    HANDLE thread = CreateThread(NULL, 0, _web_thread, srv, 0, NULL);
    if (thread) CloseHandle(thread);
#else
    pthread_t thread;
    pthread_create(&thread, NULL, _web_thread, srv);
    pthread_detach(thread);
#endif

    return 0;
}

void _syn_web_detener(int64_t servidor) {
    if (servidor < 0 || servidor >= MAX_SERVERS) return;
    if (!_servers[servidor].active) return;

    _servers[servidor].running = 0;
    if (_servers[servidor].listen_fd != INVALID_SOCKET) {
        CLOSESOCKET(_servers[servidor].listen_fd);
        _servers[servidor].listen_fd = INVALID_SOCKET;
    }
}

int _syn_web_esta_corriendo(int64_t servidor) {
    if (servidor < 0 || servidor >= MAX_SERVERS) return 0;
    return _servers[servidor].running;
}

// ============================================================
// §12.1 — Petición actual
// ============================================================

CadenaSegura _syn_web_peticion_ruta(int64_t peticion) {
    if (peticion < 0 || peticion >= MAX_SERVERS) return (CadenaSegura){0, ""};
    if (!_servers[peticion].active) return (CadenaSegura){0, ""};
    int len = (int)strlen(_servers[peticion].req_ruta);
    char* dup = (char*)malloc(len + 1);
    if (!dup) return (CadenaSegura){0, ""};
    memcpy(dup, _servers[peticion].req_ruta, len + 1);
    return (CadenaSegura){.longitud = len, .datos = dup};
}

CadenaSegura _syn_web_peticion_metodo(int64_t peticion) {
    if (peticion < 0 || peticion >= MAX_SERVERS) return (CadenaSegura){0, ""};
    if (!_servers[peticion].active) return (CadenaSegura){0, ""};
    int len = (int)strlen(_servers[peticion].req_metodo);
    char* dup = (char*)malloc(len + 1);
    if (!dup) return (CadenaSegura){0, ""};
    memcpy(dup, _servers[peticion].req_metodo, len + 1);
    return (CadenaSegura){.longitud = len, .datos = dup};
}

CadenaSegura _syn_web_peticion_body(int64_t peticion) {
    if (peticion < 0 || peticion >= MAX_SERVERS) return (CadenaSegura){0, ""};
    if (!_servers[peticion].active) return (CadenaSegura){0, ""};
    int len = (int)strlen(_servers[peticion].req_body);
    char* dup = (char*)malloc(len + 1);
    if (!dup) return (CadenaSegura){0, ""};
    memcpy(dup, _servers[peticion].req_body, len + 1);
    return (CadenaSegura){.longitud = len, .datos = dup};
}

CadenaSegura _syn_web_peticion_header(int64_t peticion, CadenaSegura nombre) {
    if (peticion < 0 || peticion >= MAX_SERVERS) return (CadenaSegura){0, ""};
    if (!_servers[peticion].active) return (CadenaSegura){0, ""};

    Server* srv = &_servers[peticion];
    for (int i = 0; i < srv->req_header_count; i++) {
        if (strcmp(srv->req_headers[i], nombre.datos) == 0) {
            char* val = srv->req_headers[i] + HEADER_NAME_MAX;
            int len = (int)strlen(val);
            char* dup = (char*)malloc(len + 1);
            if (!dup) return (CadenaSegura){0, ""};
            memcpy(dup, val, len + 1);
            return (CadenaSegura){.longitud = len, .datos = dup};
        }
    }
    return (CadenaSegura){0, ""};
}

// ============================================================
// §12.1 — Respuesta
// ============================================================

void _syn_web_responder(int64_t peticion, int64_t codigo, CadenaSegura contenido) {
    if (peticion < 0 || peticion >= MAX_SERVERS) return;
    if (!_servers[peticion].active) return;
    SOCKET fd = (SOCKET)_servers[peticion].req_socket;
    _send_response(fd, codigo, "text/plain; charset=utf-8", contenido.datos, contenido.longitud);
}

void _syn_web_responder_texto(int64_t peticion, CadenaSegura contenido) {
    _syn_web_responder(peticion, 200, contenido);
}

void _syn_web_responder_json(int64_t peticion, CadenaSegura contenido) {
    if (peticion < 0 || peticion >= MAX_SERVERS) return;
    if (!_servers[peticion].active) return;
    SOCKET fd = (SOCKET)_servers[peticion].req_socket;
    _send_response(fd, 200, "application/json; charset=utf-8", contenido.datos, contenido.longitud);
}

void _syn_web_responder_html(int64_t peticion, CadenaSegura contenido) {
    if (peticion < 0 || peticion >= MAX_SERVERS) return;
    if (!_servers[peticion].active) return;
    SOCKET fd = (SOCKET)_servers[peticion].req_socket;
    _send_response(fd, 200, "text/html; charset=utf-8", contenido.datos, contenido.longitud);
}

void _syn_web_responder_404(int64_t peticion) {
    _syn_web_responder(peticion, 404, (CadenaSegura){9, "Not Found"});
}
