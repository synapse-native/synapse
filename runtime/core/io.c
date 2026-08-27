// synapse_rt_io.c — I/O module for Synapse runtime
// Extracted from synapse_rt.c (file I/O, Canal-handle abrir/leer/cerrar) and
// synapse_rt_concurrency.c (thread-safe console I/O). Roadmap Fase 3
// deliverable runtime/core/io.c: funciones de entrada/salida basicas.
// F3-2: define tambien los externs _syn_* que std/io.syn declara
// (antes sin definicion en ningun lado — regla 12, mina latente).
// Compilar: gcc -c synapse_rt_io.c -o synapse_rt_io.o -lpthread

#include "synapse_rt_types.h"
#include "librerias/embedded_libs.h"

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
// std.io externs (F3-2) — std/io.syn los declara como `externo`;
// antes no existian en ningun lado (importar std.io -> link latente).
// ============================================================

void _syn_escribir(CadenaSegura texto) { escribir(texto); }
void _syn_escribir_linea(CadenaSegura texto) { escribir_linea(texto); }
CadenaSegura _syn_leer_linea(void) { return leer_linea(); }

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

// ============================================================
// Canal-as-file-handle (migrado de synapse_rt.c en F3-2)
// Librerias virtuales (embedded_libs.h) + fopen/leer/cerrar
// ============================================================

Canal _syn_abrir(CadenaSegura ruta, CadenaSegura modo) {
    Canal _c = {0};
    _c.es_virtual = 0;
    if (strcmp(ruta.datos, "librerias/compiler/ast_nodes.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_AST; _c.virtual_len = (int)strlen(LIB_AST); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "librerias/compiler/lexer.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_LEXER; _c.virtual_len = (int)strlen(LIB_LEXER); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "librerias/compiler/parser.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_PARSER; _c.virtual_len = (int)strlen(LIB_PARSER); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "librerias/compiler/generator.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_GENERATOR; _c.virtual_len = (int)strlen(LIB_GENERATOR); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "std/io.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_IO; _c.virtual_len = (int)strlen(LIB_IO); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "std/mem.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_MEM; _c.virtual_len = (int)strlen(LIB_MEM); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "std/math.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_MATH; _c.virtual_len = (int)strlen(LIB_MATH); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "std/fs.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_FS; _c.virtual_len = (int)strlen(LIB_FS); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "std/sys.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_SYS; _c.virtual_len = (int)strlen(LIB_SYS); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "std/modelo.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_MODELO; _c.virtual_len = (int)strlen(LIB_MODELO); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "std/oraculo.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_ORACULO; _c.virtual_len = (int)strlen(LIB_ORACULO); _c.es_valido = 1; return _c; }
    _c.stream = fopen(ruta.datos, modo.datos);
    _c.es_valido = (_c.stream != NULL) ? 1 : 0;
    if (!_c.es_valido) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: fopen fallo en abrir()\n");
    }
    return _c;
}

Canal abrir(CadenaSegura ruta, CadenaSegura modo) { return _syn_abrir(ruta, modo); }

CadenaSegura _syn_leer(Canal canal) {
    if (!canal.es_valido) { return (CadenaSegura){ .longitud = 0, .datos = "" }; }
    if (canal.es_virtual) {
        char* _buf = (char*)malloc(canal.virtual_len + 1);
        if (!_buf) { return (CadenaSegura){ .longitud = 0, .datos = "" }; }
        memcpy(_buf, canal.virtual_data, canal.virtual_len);
        _buf[canal.virtual_len] = '\0';
        return (CadenaSegura){ .longitud = canal.virtual_len, .datos = (const char*)_buf };
    }
    fseek(canal.stream, 0, SEEK_END);
    long _tam = ftell(canal.stream);
    rewind(canal.stream);
    char* _buf = (char*)malloc(_tam + 1);
    if (!_buf) { return (CadenaSegura){ .longitud = 0, .datos = "" }; }
    size_t _leido = fread(_buf, 1, _tam, canal.stream);
    _buf[_leido] = '\0';
    return (CadenaSegura){ .longitud = (int)_leido, .datos = (const char*)_buf };
}

CadenaSegura leer(Canal canal) { return _syn_leer(canal); }

void cerrar_archivo(Canal canal) {
    if (canal.es_virtual) { return; }
    if (canal.stream) {
        fclose(canal.stream);
    }
}

// ============================================================
// Extras para lib/io.syq (Fase 24)
// ============================================================

int _syn_existe(const char* ruta) {
    if (!ruta) return 0;
    FILE* f = fopen(ruta, "rb");
    if (f) { fclose(f); return 1; }
    return 0;
}

void _syn_escribir_a(int fd, const char* contenido) {
    // fd se usa como índice de handle global simple
    // Para MVP: escribir a un archivo estático
    // (mejorable con tabla de handles)
    (void)fd;
    (void)contenido;
    // Stub — la escritura real se hace vía _syn_escribir_archivo
}

// ============================================================
// §1.7 — I/O de bajo nivel para LSP
// ============================================================

int _syn_fgetc_stdin(void) {
    return fgetc(stdin);
}

int _syn_fprintf(int canal, CadenaSegura formato) {
    FILE* f = (canal == 1) ? stderr : stdout;
    int r = fwrite(formato.datos, 1, formato.longitud, f);
    fflush(f);
    return r;
}

int _syn_fprintf_i(int canal, CadenaSegura formato, int64_t valor) {
    // Formato simple: reemplaza %lld o %d por el valor
    char buf[8192];
    int f_len = formato.longitud;
    if (f_len > 200) f_len = 200;
    char fmt[256];
    memcpy(fmt, formato.datos, f_len);
    fmt[f_len] = '\0';
    // Buscar %d o %lld y reemplazar
    char* pos = strstr(fmt, "%lld");
    if (pos) {
        *pos = '\0';
        int r = snprintf(buf, sizeof(buf), "%s%lld%s", fmt, valor, pos + 4);
        FILE* f = (canal == 1) ? stderr : stdout;
        fwrite(buf, 1, r, f);
        fflush(f);
        return r;
    }
    pos = strstr(fmt, "%d");
    if (pos) {
        *pos = '\0';
        int r = snprintf(buf, sizeof(buf), "%s%d%s", fmt, (int)valor, pos + 2);
        FILE* f = (canal == 1) ? stderr : stdout;
        fwrite(buf, 1, r, f);
        fflush(f);
        return r;
    }
    // Sin placeholder, escribir tal cual
    FILE* f = (canal == 1) ? stderr : stdout;
    int r = fwrite(formato.datos, 1, formato.longitud, f);
    fflush(f);
    return r;
}

int _syn_fprintf_it(int canal, CadenaSegura formato, int64_t val1, CadenaSegura val2) {
    // Formato con 1 entero y 1 texto: reemplaza %d y %s
    char buf[8192];
    int f_len = formato.longitud;
    if (f_len > 200) f_len = 200;
    char fmt[256];
    memcpy(fmt, formato.datos, f_len);
    fmt[f_len] = '\0';

    // Primero reemplazar %d por el entero
    char temp[4096];
    char* pos = strstr(fmt, "%d");
    if (pos) {
        *pos = '\0';
        snprintf(temp, sizeof(temp), "%s%lld%s", fmt, val1, pos + 2);
    } else {
        strcpy(temp, fmt);
    }

    // Luego reemplazar %s por el texto
    pos = strstr(temp, "%s");
    if (pos) {
        *pos = '\0';
        int r = snprintf(buf, sizeof(buf), "%s%.*s%s", temp, val2.longitud, val2.datos, pos + 2);
        FILE* f = (canal == 1) ? stderr : stdout;
        fwrite(buf, 1, r, f);
        fflush(f);
        return r;
    }

    FILE* f = (canal == 1) ? stderr : stdout;
    int r = fwrite(temp, 1, strlen(temp), f);
    fflush(f);
    return r;
}

void _syn_fflush(int canal) {
    FILE* f = (canal == 1) ? stderr : stdout;
    fflush(f);
}

void _syn_setbuf_null(int canal) {
    FILE* f = (canal == 1) ? stderr : stdout;
    setbuf(f, NULL);
}
