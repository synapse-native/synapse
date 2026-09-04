// synapse_rt_io.c — I/O module for Synapse runtime
// Extracted from synapse_rt.c (file I/O, Canal-handle abrir/leer/cerrar) and
// synapse_rt_concurrency.c (thread-safe console I/O). Roadmap Fase 3
// deliverable runtime/core/io.c: funciones de entrada/salida basicas.
// F3-2: define tambien los externs _syn_* que std/io.syn declara
// (antes sin definicion en ningun lado — regla 12, mina latente).
// Compilar: gcc -c synapse_rt_io.c -o synapse_rt_io.o -lpthread

#include "synapse_rt_types.h"
#include "librerias/embedded_libs.h"
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#include <windows.h>
#else
#include <unistd.h>
#endif

// ============================================================
// Thread-safe console I/O
// ============================================================

// cumple Manual 5 3: pthread_once para inicialización thread-safe
static pthread_once_t _syn_stdout_binary_once = PTHREAD_ONCE_INIT;
static pthread_once_t _syn_stdin_binary_once = PTHREAD_ONCE_INIT;

#ifdef _WIN32
// Detecta si un HANDLE es consola real (GetConsoleMode falla en pipes/archivos).
// Los textos Synapse/OpenSyn son UTF-8; la consola Windows usa CP850/CP437 por
// defecto y muestra mojibake (┬┐/├®). Se alinea la consola a CP_UTF8 SOLO cuando
// hay consola real: con pipes (LSP) GetConsoleMode falla y no se toca nada.
static int _syn_es_consola_handle(HANDLE h) {
    DWORD modo = 0;
    return h != NULL && h != INVALID_HANDLE_VALUE && GetConsoleMode(h, &modo) != 0;
}
#endif

static void _syn_ensure_stdout_binary_init(void) {
#ifdef _WIN32
    _setmode(_fileno(stdout), _O_BINARY);
    HANDLE h = GetStdHandle(STD_OUTPUT_HANDLE);
    if (_syn_es_consola_handle(h)) {
        SetConsoleOutputCP(65001);  // cumple Manual 9 2.5: UTF-8 en consola
        // cumple Manual 9 2.5: habilita secuencias ANSI (banner/colores estilo
        // OpenCode/Freebuff) SOLO en consola real; los pipes quedan sin escapes.
        DWORD modo = 0;
        if (GetConsoleMode(h, &modo)) {
            SetConsoleMode(h, modo | 0x0004 /* ENABLE_VIRTUAL_TERMINAL_PROCESSING */);
        }
    }
#else
    // POSIX: hereda el TTY; no hace falta nada (ANSI nativo).
#endif
}

// ============================================================
// Consola real + colores ANSI (estilo OpenCode/Freebuff)
// cumple Manual 7 8: banner y prompt del chat interactivo local.
// cumple Manual 7 2.3: el System Prompt del agente se presenta en consola
// real con ANSI (banner/prompt ❯) y sin escapes en pipes; _syn_es_consola y
// _syn_ansi son las guardas de presentación del prompt del agente (R2).
// ============================================================

// cumple Manual 9 2.5: _syn_es_consola devuelve 1 si stdout es consola real
// (no pipe/archivo). El chat solo emite escapes ANSI en consola real para no
// ensuciar pipes (LSP/tests) — mismas guardas que el CP65001.
int64_t _syn_es_consola(void) {
#ifdef _WIN32
    HANDLE h = GetStdHandle(STD_OUTPUT_HANDLE);
    return _syn_es_consola_handle(h) ? 1 : 0;
#else
    return isatty(fileno(stdout)) ? 1 : 0;
#endif
}

// cumple Manual 9 2.5: _syn_ansi(sgr) devuelve "\x1b[<sgr>m". sgr=0 resetea;
// 31..37 colores (rojo..blanco); +100 = negrita (ej. 136 -> "\x1b[1;36m").
// Retorna pool_alloc (RAII, Manual 2 9.1). Vacía si sgr inválido.
CadenaSegura _syn_ansi(int64_t sgr) {
    CadenaSegura vacio = { .longitud = 0, .datos = "" };
    int code = (int)sgr;
    int bold = 0;
    if (code > 100) { bold = 1; code -= 100; }
    if (code != 0 && (code < 30 || code > 37)) return vacio;
    char buf[16];
    int largo;
    if (bold) {
        largo = snprintf(buf, sizeof(buf), "\x1b[1;%dm", code);
    } else {
        largo = snprintf(buf, sizeof(buf), "\x1b[%dm", code);
    }
    if (largo <= 0) return vacio;
    char* pool = (char*)pool_alloc((size_t)largo + 1);
    if (!pool) return vacio;
    memcpy(pool, buf, (size_t)largo + 1);
    return (CadenaSegura){ .longitud = largo, .datos = pool };
}

// cumple Manual 8 1.2: stdin en modo binario para LSP (evita traducción \r\n)
static void _syn_ensure_stdin_binary_init(void) {
#ifdef _WIN32
    _setmode(_fileno(stdin), _O_BINARY);
#endif
}

#ifdef _WIN32
// Consola interactiva (chat OpenSyn, menus): modo TEXTO del CRT (traduce CRLF y
// devuelve la linea al pulsar Enter con echo/edicion) + codepage UTF-8 de entrada.
// No aplica a pipes: el LSP usa ReadFile directo (Manual 8 1.2).
static pthread_once_t _syn_stdin_consola_once = PTHREAD_ONCE_INIT;
static void _syn_ensure_stdin_consola_init(void) {
    _setmode(_fileno(stdin), _O_TEXT);
    SetConsoleCP(65001);  // cumple Manual 9 2.5: entrada UTF-8
}
#endif

static void _syn_ensure_stdout_binary(void) {
    pthread_once(&_syn_stdout_binary_once, _syn_ensure_stdout_binary_init);
}

static void _syn_ensure_stdin_binary(void) {
    pthread_once(&_syn_stdin_binary_once, _syn_ensure_stdin_binary_init);
}


pthread_mutex_t io_mutex = PTHREAD_MUTEX_INITIALIZER;

#ifdef _WIN32
// Cache stdin handle at process start — GetStdHandle can return
// INVALID_HANDLE_VALUE after CRT initialization corrupts it.
// Use _get_osfhandle(0) which is more reliable with pipes.
static HANDLE _syn_stdin_handle = NULL;
static pthread_once_t _syn_stdin_handle_once = PTHREAD_ONCE_INIT;
static void _syn_cache_stdin_handle(void) {
    _syn_stdin_handle = (HANDLE)_get_osfhandle(0);
    if (_syn_stdin_handle == INVALID_HANDLE_VALUE || _syn_stdin_handle == NULL) {
        _syn_stdin_handle = GetStdHandle(STD_INPUT_HANDLE);
    }
}
static HANDLE _syn_get_stdin_handle(void) {
    pthread_once(&_syn_stdin_handle_once, _syn_cache_stdin_handle);
    return _syn_stdin_handle;
}
#endif

void escribir(CadenaSegura contenido) {
    _syn_ensure_stdout_binary();
    pthread_mutex_lock(&io_mutex);
    fwrite(contenido.datos, 1, contenido.longitud, stdout);
    fflush(stdout);
    pthread_mutex_unlock(&io_mutex);
}

void escribir_linea(CadenaSegura contenido) {
    _syn_ensure_stdout_binary();  // cumple Manual 9 2.5: CP65001 también al imprimir por línea
    pthread_mutex_lock(&io_mutex);
    fwrite(contenido.datos, 1, contenido.longitud, stdout);
    fwrite("\n", 1, 1, stdout);
    fflush(stdout);
    pthread_mutex_unlock(&io_mutex);
}

// cumple Manual 5 3: mutex protege _buf estático contra data races
static pthread_mutex_t _leer_linea_mutex = PTHREAD_MUTEX_INITIALIZER;

// Forward declaration — implementación real en _syn_leer_linea (ReadFile Windows)
CadenaSegura _syn_leer_linea(void);

// leer_linea() — wrapper público que delega a _syn_leer_linea (la implementación real).
// lsp_v3.c también define leer_linea() como wrapper que llama a _syn_leer_linea.
// Con --allow-multiple-definition el linker toma la primera definición,
// pero ambas llegan a _syn_leer_linea → ReadFile (Windows) o fgets (otros).
CadenaSegura leer_linea(void) {
    return _syn_leer_linea();
}

// ============================================================
// std.io externs (F3-2) — std/io.syn los declara como `externo`;
// antes no existian en ningun lado (importar std.io -> link latente).
// ============================================================

void _syn_escribir(CadenaSegura texto) { escribir(texto); }
void _syn_escribir_linea(CadenaSegura texto) { escribir_linea(texto); }

#ifdef _WIN32
// Export cached stdin handle for use by string_utils.c _syn_leer_bytes
HANDLE _syn_get_cached_stdin(void) { return _syn_get_stdin_handle(); }
#endif

// _syn_leer_linea contiene la implementación real.
// lsp_v3.c define su propio `leer_linea` wrapper que llama a _syn_leer_linea.
// io.c también define `leer_linea` que llama a _syn_leer_linea.
// El linker con --allow-multiple-definition toma la primera definición de
// `leer_linea` (la del LSP wrapper). Ambas llegan a _syn_leer_linea.
CadenaSegura _syn_leer_linea(void) {
    static char _buf[4096];
    pthread_mutex_lock(&_leer_linea_mutex);
#ifdef _WIN32
    {
        HANDLE hstdin = _syn_get_stdin_handle();
        if (_syn_es_consola_handle(hstdin)) {
            // Consola interactiva (chat/OpenSyn, menus): CRT en modo texto con
            // codepage UTF-8. El ReadFile byte-a-byte es solo para pipes (LSP).
            pthread_once(&_syn_stdin_consola_once, _syn_ensure_stdin_consola_init);
            if (fgets(_buf, 4096, stdin)) {
                int _len = (int)strlen(_buf);
                if (_len > 0 && _buf[_len - 1] == '\n') { _buf[_len - 1] = '\0'; _len--; }
                if (_len > 0 && _buf[_len - 1] == '\r') { _buf[_len - 1] = '\0'; _len--; }
                if (_len == 0) {
                    pthread_mutex_unlock(&_leer_linea_mutex);
                    return (CadenaSegura){ .longitud = 0, .datos = "" };
                }
                // cumple Manual 2 9.1: pool_alloc (RAII libera con pool_free)
                char* _dup = (char*)pool_alloc((size_t)(_len + 1));
                if (!_dup) { pthread_mutex_unlock(&_leer_linea_mutex); return (CadenaSegura){ .longitud = 0, .datos = "" }; }
                memcpy(_dup, _buf, _len + 1);
                pthread_mutex_unlock(&_leer_linea_mutex);
                return (CadenaSegura){ .longitud = _len, .datos = _dup };
            }
            pthread_mutex_unlock(&_leer_linea_mutex);
            return (CadenaSegura){ .longitud = 0, .datos = "" };
        }
        // cumple Manual 8 1.2: ReadFile directo para pipes de subprocess en Windows
        // fgets() falla con pipes de Python porque _setmode+_get_osfhandle corrompe
        // el handle. GetStdHandle(STD_INPUT_HANDLE) bypassa el CRT completamente.
        if (hstdin == NULL || hstdin == INVALID_HANDLE_VALUE) {
            pthread_mutex_unlock(&_leer_linea_mutex);
            return (CadenaSegura){ .longitud = 0, .datos = "" };
        }
        int _pos = 0;
        while (_pos < 4095) {
            DWORD _leidos = 0;
            BOOL ok = ReadFile(hstdin, _buf + _pos, 1, &_leidos, NULL);
            if (!ok || _leidos == 0) {
                if (_pos == 0) {
                    pthread_mutex_unlock(&_leer_linea_mutex);
                    return (CadenaSegura){ .longitud = 0, .datos = "" };
                }
                break;
            }
            if (_buf[_pos] == '\n') {
                _pos++;
                break;
            }
            _pos++;
        }
        _buf[_pos] = '\0';
        int _len = _pos;
        if (_len > 0 && _buf[_len - 1] == '\n') { _buf[_len - 1] = '\0'; _len--; }
        if (_len > 0 && _buf[_len - 1] == '\r') { _buf[_len - 1] = '\0'; _len--; }
        if (_len == 0) {
            // cumple Manual 2 9.1: pool_alloc, no literal ni malloc ajeno
            char* _empty = (char*)pool_alloc(1);
            if (_empty) _empty[0] = '\0';
            pthread_mutex_unlock(&_leer_linea_mutex);
            return (CadenaSegura){ .longitud = 0, .datos = _empty ? _empty : "" };
        }
        char* _dup = (char*)pool_alloc((size_t)(_len + 1));
        if (!_dup) { pthread_mutex_unlock(&_leer_linea_mutex); return (CadenaSegura){ .longitud = 0, .datos = "" }; }
        memcpy(_dup, _buf, _len + 1);
        pthread_mutex_unlock(&_leer_linea_mutex);
        return (CadenaSegura){ .longitud = _len, .datos = _dup };
    }
#else
    if (fgets(_buf, 4096, stdin)) {
        int _len = (int)strlen(_buf);
        if (_len > 0 && _buf[_len - 1] == '\n') { _buf[_len - 1] = '\0'; _len--; }
        if (_len > 0 && _buf[_len - 1] == '\r') { _buf[_len - 1] = '\0'; _len--; }
        if (_len == 0) {
            pthread_mutex_unlock(&_leer_linea_mutex);
            return (CadenaSegura){ .longitud = 0, .datos = "" };
        }
        // cumple Manual 2 9.1: pool_alloc (RAII libera con pool_free)
        char* _dup = (char*)pool_alloc((size_t)(_len + 1));
        if (!_dup) { pthread_mutex_unlock(&_leer_linea_mutex); return (CadenaSegura){ .longitud = 0, .datos = "" }; }
        memcpy(_dup, _buf, _len + 1);
        pthread_mutex_unlock(&_leer_linea_mutex);
        return (CadenaSegura){ .longitud = _len, .datos = _dup };
    }
    pthread_mutex_unlock(&_leer_linea_mutex);
    return (CadenaSegura){ .longitud = 0, .datos = "" };
#endif
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
