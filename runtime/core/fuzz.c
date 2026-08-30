// runtime/core/fuzz.c — Fuzzing Distribuido Multi-Nodo (M10.4):
// coordinador/agentes, envio de casos, procesamiento de paquetes SYNFUZZ,
// reporte de resultados y estadisticas.
// Extracted from synapse_rt.c (D-9(d) corte 6, patron cluster.c R40).
// Texto de las funciones BYTE-IDENTICO al original (CRLF preservado).
// Consumido por std.cluster (externs fz_*, link-time).

#include "synapse_rt_types.h"
#include "synapse_rt_memory.h"
#include "runtime/core/fuzz.h"
#include "runtime/core/cluster.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
#include <time.h>
#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #include <windows.h>
  #include <io.h>
#else
  #include <sys/socket.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
  #include <unistd.h>
  #include <sys/select.h>
  #include <fcntl.h>
#endif

// --- Externs del resto del runtime ---
// D-9(d) corte 6: el bloque FZ usa cluster_canal_remoto_enviar (cluster.h) y
// pool_alloc (synapse_rt_memory.h).

// ============================================================
// FZ — Fuzzing Distribuido Multi-Nodo (M10.4)
// ============================================================
#define FZ_PROTO_MAGIC "SYNFUZZ"
#define FZ_MAX_RESULTS 512
#define FZ_MAX_STDERR 256
#define FZ_MAX_CONTENT 2048

typedef struct {
    int caso_id;
    int exit_code;
    int timestamp;
    char stderr_resumen[FZ_MAX_STDERR];
} ResultadoFuzz;

static int _fz_inicializado = 0;
static int _fz_puerto_coordinador = -1;
static int _fz_total_enviados = 0;
static int _fz_total_recibidos = 0;
static int _fz_total_crashes = 0;
static int _fz_ultimo_caso_id = 0;
static ResultadoFuzz _fz_resultados[FZ_MAX_RESULTS];
static int _fz_num_resultados = 0;
static pthread_mutex_t _fz_mutex = PTHREAD_MUTEX_INITIALIZER;

int fz_iniciar_coordinador(int puerto) {
    if (puerto <= 0) return -1;
    pthread_mutex_lock(&_fz_mutex);
    _fz_inicializado = 1;
    _fz_puerto_coordinador = puerto;
    _fz_total_enviados = 0;
    _fz_total_recibidos = 0;
    _fz_total_crashes = 0;
    _fz_ultimo_caso_id = 0;
    _fz_num_resultados = 0;
    memset(_fz_resultados, 0, sizeof(_fz_resultados));
    pthread_mutex_unlock(&_fz_mutex);
    return 0;
}

int fz_enviar_caso(CadenaSegura ip, int puerto, int caso_id, CadenaSegura contenido) {
    if (!_fz_inicializado || !ip.datos || puerto <= 0 || !contenido.datos) return -1;
    char buf[FZ_MAX_CONTENT + 128];
    int use_len = contenido.longitud;
    if (use_len > FZ_MAX_CONTENT) use_len = FZ_MAX_CONTENT;
    int len = snprintf(buf, sizeof(buf), "%s:CASE:%d:%d:%.*s",
                       FZ_PROTO_MAGIC, caso_id, use_len,
                       use_len, contenido.datos);
    if (len <= 0 || len >= (int)sizeof(buf)) return -2;
    int rc = cluster_canal_remoto_enviar(ip.datos, puerto, buf, len, 0);
    if (rc < 0) return -3;
    pthread_mutex_lock(&_fz_mutex);
    _fz_total_enviados++;
    _fz_ultimo_caso_id = caso_id;
    pthread_mutex_unlock(&_fz_mutex);
    return caso_id;
}

CadenaSegura fz_procesar_mensaje(CadenaSegura paquete) {
    if (!_fz_inicializado || !paquete.datos || paquete.longitud <= 0)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    if (strncmp(paquete.datos, FZ_PROTO_MAGIC, strlen(FZ_PROTO_MAGIC)) != 0)
        return (CadenaSegura){ .longitud = 7, .datos = "IGNORED" };
    const char* p = paquete.datos + strlen(FZ_PROTO_MAGIC) + 1;
    if (strncmp(p, "CASE", 4) == 0) {
        p += 5;
        const char* sep1 = strchr(p, ':');
        if (!sep1) return (CadenaSegura){ .longitud = 0, .datos = NULL };
        const char* sep2 = strchr(sep1 + 1, ':');
        if (!sep2) return (CadenaSegura){ .longitud = 0, .datos = NULL };
        const char* content = sep2 + 1;
        int content_len = (int)(paquete.datos + paquete.longitud - content);
        if (content_len <= 0) return (CadenaSegura){ .longitud = 0, .datos = NULL };
        char* result = (char*)pool_alloc((size_t)(content_len + 16));
        if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
        int rlen = snprintf(result, (size_t)(content_len + 16), "CASE:%.*s", content_len, content);
        return (CadenaSegura){ .longitud = rlen, .datos = result };
    } else if (strncmp(p, "RESULT", 6) == 0) {
        p += 7;
        int caso_id = 0;
        while (*p && *p != ':') { caso_id = caso_id * 10 + (*p - '0'); p++; }
        if (!*p) return (CadenaSegura){ .longitud = 0, .datos = NULL };
        p++;
        int exit_code = 0, sign = 1;
        if (*p == '-') { sign = -1; p++; }
        while (*p && *p != ':') { exit_code = exit_code * 10 + (*p - '0'); p++; }
        exit_code *= sign;
        if (!*p) return (CadenaSegura){ .longitud = 0, .datos = NULL };
        p++;
        pthread_mutex_lock(&_fz_mutex);
        if (_fz_num_resultados < FZ_MAX_RESULTS) {
            _fz_resultados[_fz_num_resultados].caso_id = caso_id;
            _fz_resultados[_fz_num_resultados].exit_code = exit_code;
            _fz_resultados[_fz_num_resultados].timestamp = (int)time(NULL);
            strncpy(_fz_resultados[_fz_num_resultados].stderr_resumen, p, FZ_MAX_STDERR - 1);
            _fz_resultados[_fz_num_resultados].stderr_resumen[FZ_MAX_STDERR - 1] = '\0';
            _fz_num_resultados++;
        }
        _fz_total_recibidos++;
        if (exit_code < 0 || exit_code > 1) _fz_total_crashes++;
        pthread_mutex_unlock(&_fz_mutex);
        char* result = (char*)pool_alloc(64);
        if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
        int rlen = snprintf(result, 64, "RESULT:%d:%d", caso_id, exit_code);
        return (CadenaSegura){ .longitud = rlen, .datos = result };
    }
    return (CadenaSegura){ .longitud = 7, .datos = "IGNORED" };
}

int fz_reportar_resultado(CadenaSegura ip_coord, int puerto_coord,
                          int caso_id, int exit_code, CadenaSegura stderr_resumen) {
    if (!ip_coord.datos || puerto_coord <= 0) return -1;
    char buf[1024];
    const char* stderr_str = stderr_resumen.datos ? stderr_resumen.datos : "";
    int len = snprintf(buf, sizeof(buf), "%s:RESULT:%d:%d:%s",
                       FZ_PROTO_MAGIC, caso_id, exit_code, stderr_str);
    if (len <= 0) return -2;
    return cluster_canal_remoto_enviar(ip_coord.datos, puerto_coord, buf, len, 0);
}

CadenaSegura fz_obtener_resultado(int indice) {
    pthread_mutex_lock(&_fz_mutex);
    if (indice < 0 || indice >= _fz_num_resultados) {
        pthread_mutex_unlock(&_fz_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    char buf[256];
    int len = snprintf(buf, sizeof(buf), "%d:%d:%d",
                       _fz_resultados[indice].caso_id,
                       _fz_resultados[indice].exit_code,
                       _fz_resultados[indice].timestamp);
    pthread_mutex_unlock(&_fz_mutex);
    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(result, buf, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = len, .datos = result };
}

int fz_ultimo_caso_id(void) { return _fz_ultimo_caso_id; }
int fz_total_casos_enviados(void) { return _fz_total_enviados; }
int fz_total_resultados_recibidos(void) { return _fz_total_recibidos; }
int fz_total_crashes(void) { return _fz_total_crashes; }
int fz_num_resultados(void) { return _fz_num_resultados; }

CadenaSegura fz_info(void) {
    if (!_fz_inicializado)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    char buf[256];
    pthread_mutex_lock(&_fz_mutex);
    int len = snprintf(buf, sizeof(buf), "%d:%d:%d:%d:%d",
                       _fz_total_enviados, _fz_total_recibidos,
                       _fz_total_crashes, _fz_ultimo_caso_id,
                       _fz_num_resultados);
    pthread_mutex_unlock(&_fz_mutex);
    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(result, buf, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = len, .datos = result };
}
