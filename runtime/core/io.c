// synapse_rt_io.c — I/O module for Synapse runtime
// Extracted from synapse_rt.c (file I/O) and synapse_rt_concurrency.c
// (thread-safe console I/O). Roadmap Fase 3 deliverable runtime/core/io.c:
// funciones de entrada/salida basicas (log, lectura/escritura de archivos).
// Compilar: gcc -c synapse_rt_io.c -o synapse_rt_io.o -lpthread

#include "synapse_rt_types.h"

// ============================================================
// Thread-safe console I/O
// ============================================================

pthread_mutex_t io_mutex = PTHREAD_MUTEX_INITIALIZER;

void escribir(CadenaSegura contenido) {
    pthread_mutex_lock(&io_mutex);
    fwrite(contenido.datos, 1, contenido.longitud, stdout);
    fflush(stdout);
    pthread_mutex_unlock(&io_mutex);
}

void escribir_linea(CadenaSegura contenido) {
    pthread_mutex_lock(&io_mutex);
    fwrite(contenido.datos, 1, contenido.longitud, stdout);
    fwrite("\n", 1, 1, stdout);
    fflush(stdout);
    pthread_mutex_unlock(&io_mutex);
}

CadenaSegura leer_linea(void) {
    static char _buf[4096];
    if (fgets(_buf, 4096, stdin)) {
        int _len = (int)strlen(_buf);
        if (_len > 0 && _buf[_len - 1] == '\n') { _buf[_len - 1] = '\0'; _len--; }
        char* _dup = (char*)malloc(_len + 1);
        if (!_dup) { return (CadenaSegura){ .longitud = 0, .datos = "" }; }
        memcpy(_dup, _buf, _len + 1);
        return (CadenaSegura){ .longitud = _len, .datos = _dup };
    }
    return (CadenaSegura){ .longitud = 0, .datos = "" };
}

// ============================================================
// File I/O (lectura/escritura de archivos)
// ============================================================

static char* _syn_leer_archivo_como_texto(const char* ruta) {
    FILE* f = fopen(ruta, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    rewind(f);
    if (sz <= 0) { fclose(f); return NULL; }
    char* buf = (char*)malloc((size_t)(sz + 1));
    if (!buf) { fclose(f); return NULL; }
    size_t n = fread(buf, 1, (size_t)sz, f);
    fclose(f);
    buf[n] = '\0';
    return buf;
}

int _syn_escribir_archivo(CadenaSegura ruta, CadenaSegura contenido) {
    if (ruta.datos == NULL || ruta.longitud <= 0) return -1;
    char* ruta_c = (char*)malloc((size_t)(ruta.longitud + 1));
    if (!ruta_c) return -1;
    memcpy(ruta_c, ruta.datos, (size_t)ruta.longitud);
    ruta_c[ruta.longitud] = '\0';
    FILE* f = fopen(ruta_c, "wb");
    if (!f) { free(ruta_c); return -1; }
    if (contenido.datos && contenido.longitud > 0) {
        fwrite(contenido.datos, 1, (size_t)contenido.longitud, f);
    }
    fclose(f);
    free(ruta_c);
    return 0;
}

CadenaSegura _syn_leer_archivo(CadenaSegura ruta) {
    if (ruta.datos == NULL || ruta.longitud <= 0) return (CadenaSegura){0, ""};
    char* ruta_c = (char*)malloc((size_t)(ruta.longitud + 1));
    if (!ruta_c) return (CadenaSegura){0, ""};
    memcpy(ruta_c, ruta.datos, (size_t)ruta.longitud);
    ruta_c[ruta.longitud] = '\0';
    char* contenido = _syn_leer_archivo_como_texto(ruta_c);
    free(ruta_c);
    if (!contenido) return (CadenaSegura){0, ""};
    CadenaSegura res = {.longitud = (int)strlen(contenido), .datos = contenido};
    return res;
}
