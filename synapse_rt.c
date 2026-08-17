// synapse_rt.c — Synapse runtime (modular: types, memory, concurrency)
// Compilar: gcc -c synapse_rt.c -o synapse_rt.o
// Linkear con: synapse_rt_memory.o synapse_rt_concurrency.o

#include "synapse_rt_types.h"
#include "runtime/core/tensor.h"  // D-9(d): std.math/std.tensor/std.simd extraidos a tensor.c
#include "runtime/core/cluster.h"  // D-9(d): std.cluster (M8.1-M8.6) extraido a cluster.c
#include "runtime/core/debug.h"  // D-9(d): debug (M9.0-M9.4) extraido a debug.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <pthread.h>
#include <time.h>
#include "librerias/embedded_libs.h"
#include "axon/tweetnacl.h"

#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #include <windows.h>
  #include <direct.h>
  #include <wincrypt.h>
#else
  #include <sys/socket.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
  #include <unistd.h>
  #include <sys/mman.h>
  #include <sys/stat.h>
  #include <fcntl.h>
#endif

// -----------------------------------------------------------
// (Canal abrir/leer/cerrar + librerias virtuales movidos a runtime/core/io.c en F3-2;
//  externs _syn_abrir/_syn_leer/_syn_escribir/_syn_escribir_linea/_syn_leer_linea
//  definidos alli tambien — std/io.syn ya enlaza)

// --- std.conv ---
int64_t texto_a_entero(CadenaSegura str) {
    if (str.datos == NULL || str.longitud == 0) return 0;
    return (int64_t)strtoll(str.datos, NULL, 10);
}

double texto_a_decimal(CadenaSegura str) {
    if (str.datos == NULL || str.longitud == 0) return 0.0;
    return strtod(str.datos, NULL);
}

CadenaSegura decimal_a_texto(double n) {
    char buf[64];
    int len = snprintf(buf, sizeof(buf), "%f", n);
    char* data = (char*)malloc(len + 1);
    if (!data) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en decimal_a_texto\n"); exit(1); }
    memcpy(data, buf, len + 1);
    return (CadenaSegura){ .longitud = len, .datos = data };
}

// A5.1 (D-7): entero -> int64_t (Manual 2 S4.1 L267-268). Ensayo de runtime:
// %lld con cast (long long) para portabilidad; salida identica para valores
// pequenos, sin truncar en rangos 32->64 bits. Los mapeos se migran en A5.2.
CadenaSegura entero_a_texto(int64_t n) {
    char buf[64];
    int len = snprintf(buf, sizeof(buf), "%lld", (long long)n);
    char* data = (char*)malloc(len + 1);
    if (!data) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en entero_a_texto\n"); exit(1); }
    memcpy(data, buf, len + 1);
    return (CadenaSegura){ .longitud = len, .datos = data };
}

// ============================================================
// std.net — Socket helpers (TCP client)
// ============================================================

int _syn_iniciar_red(void) {
#ifdef _WIN32
    WSADATA wsa;
    return WSAStartup(MAKEWORD(2,2), &wsa);
#else
    return 0;
#endif
}

int _syn_cerrar_red(void) {
#ifdef _WIN32
    return WSACleanup();
#else
    return 0;
#endif
}

int _syn_socket(void) {
    return (int)socket(AF_INET, SOCK_STREAM, 0);
}

int _syn_conectar(int fd, const char* ip, int puerto) {
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)puerto);
    addr.sin_addr.s_addr = inet_addr(ip);
    if (addr.sin_addr.s_addr == INADDR_NONE)
        return -1;
    return connect(fd, (struct sockaddr*)&addr, sizeof(addr));
}

int _syn_enviar(int fd, const char* datos, int lon) {
    return (int)send(fd, datos, (size_t)lon, 0);
}

int _syn_recibir(int fd, char* buf, int lon) {
    return (int)recv(fd, buf, (size_t)lon, 0);
}

int _syn_cerrar_socket(int fd) {
#ifdef _WIN32
    return closesocket(fd);
#else
    return close(fd);
#endif
}

// ============================================================
// std.json — JSON Parser (Deserializador Determinista)
// Arquitectura simdjson-style: arena contigua + strings in-place.
// Sin malloc por clave/nodo. Arena unica liberada al final.
// ============================================================

// --- Arena (contiguous bump allocator) ---

static NodoJson* _json_arena = NULL;
static int _json_arena_pos = 0;

static NodoJson* _json_arena_alloc(void) {
    if (_json_arena_pos >= JSON_MAX_NODES) return NULL;
    return &_json_arena[_json_arena_pos++];
}

// --- Parser state ---

static CadenaSegura _p_input;
static int _p_pos;

void _json_init(CadenaSegura s) {
    _p_input = s;
    _p_pos = 0;
    if (!_json_arena) {
        _json_arena = (NodoJson*)pool_alloc(JSON_MAX_NODES * sizeof(NodoJson));
    }
    _json_arena_pos = 0;
}

NodoJson _json_nodo_new() {
    NodoJson n = {0};
    return n;
}

// Arena liberada en _json_parse(). No-op para compatibilidad.
void _json_nodo_liberar(NodoJson n) {
    (void)n;
}

// --- Dynamic array helpers (arena-based, pool_alloc en vez de malloc) ---

static void nodo_arr_init(NodoArr* a) { a->items = NULL; a->count = 0; a->cap = 0; }

static void nodo_arr_append(NodoArr* a, NodoJson item) {
    if (a->count >= a->cap) {
        a->cap = a->cap ? a->cap * 2 : 8;
        NodoJson* new = (NodoJson*)pool_alloc((size_t)(a->cap * sizeof(NodoJson)));
        if (a->items) { memcpy(new, a->items, (size_t)(a->count * sizeof(NodoJson))); }
        a->items = new;
    }
    a->items[a->count++] = item;
}

static NodoJson* nodo_arr_detach(NodoArr* a) {
    NodoJson* p = a->items;
    a->items = NULL;
    a->count = 0;
    a->cap = 0;
    return p;
}

static void par_arr_init(ParArr* a) { a->items = NULL; a->count = 0; a->cap = 0; }

static void par_arr_append(ParArr* a, CadenaSegura clave, NodoJson* valor) {
    if (a->count >= a->cap) {
        a->cap = a->cap ? a->cap * 2 : 8;
        ParJson* new = (ParJson*)pool_alloc((size_t)(a->cap * sizeof(ParJson)));
        if (a->items) { memcpy(new, a->items, (size_t)(a->count * sizeof(ParJson))); }
        a->items = new;
    }
    a->items[a->count].clave = clave;
    a->items[a->count].valor = valor;
    a->count++;
}

static ParJson* par_arr_detach(ParArr* a) {
    ParJson* p = a->items;
    a->items = NULL;
    a->count = 0;
    a->cap = 0;
    return p;
}

// --- Lexer helpers (con aceleracion SIMD para parseo masivo) ---

static int _peek() {
    if (_p_pos < 0 || _p_pos >= _p_input.longitud) return -1;
    return (unsigned char)_p_input.datos[_p_pos];
}

static int _advance() {
    if (_p_pos < 0 || _p_pos >= _p_input.longitud) return -1;
    return (unsigned char)_p_input.datos[_p_pos++];
}

// Skip whitespace using AVX2 when available (32 bytes/ciclo)
// (immintrin.h already included above under __AVX2__ guard)
#ifdef __AVX2__
static void _skip_ws() {
    while (_p_pos + 32 <= _p_input.longitud) {
        __m256i chunk = _mm256_loadu_si256((const __m256i*)(_p_input.datos + _p_pos));
        // Compare each byte with space (0x20), tab (0x09), newline (0x0A), CR (0x0D)
        __m256i ws_chars = _mm256_set1_epi8(' ');
        __m256i cmp_space = _mm256_cmpeq_epi8(chunk, _mm256_set1_epi8(' '));
        __m256i cmp_tab   = _mm256_cmpeq_epi8(chunk, _mm256_set1_epi8('\t'));
        __m256i cmp_nl    = _mm256_cmpeq_epi8(chunk, _mm256_set1_epi8('\n'));
        __m256i cmp_cr    = _mm256_cmpeq_epi8(chunk, _mm256_set1_epi8('\r'));
        __m256i ws = _mm256_or_si256(_mm256_or_si256(cmp_space, cmp_tab),
                                     _mm256_or_si256(cmp_nl, cmp_cr));
        int mask = _mm256_movemask_epi8(ws);
        if (mask == 0xFFFFFFFF) {
            // All 32 bytes are whitespace
            _p_pos += 32;
        } else {
            // Found at least one non-whitespace byte
            int ws_count = __builtin_ctz(~(unsigned int)mask);
            _p_pos += ws_count;
            return;
        }
    }
    // Fallback to scalar for remaining < 32 bytes
    while (_p_pos < _p_input.longitud) {
        char c = _p_input.datos[_p_pos];
        if (c == ' ' || c == '\t' || c == '\n' || c == '\r') _p_pos++;
        else break;
    }
}
#else
static void _skip_ws() {
    while (_p_pos < _p_input.longitud) {
        char c = _p_input.datos[_p_pos];
        if (c == ' ' || c == '\t' || c == '\n' || c == '\r') _p_pos++;
        else break;
    }
}
#endif

// AVX2-accelerated string value scanning: find closing quote in 32-byte chunks
#ifdef __AVX2__
static CadenaSegura _parse_string_value() {
    if (_advance() != '"') return (CadenaSegura){0};
    int start = _p_pos;
    // AVX2: search for quote or backslash in 32-byte chunks
    __m256i quote = _mm256_set1_epi8('"');
    __m256i bslash = _mm256_set1_epi8('\\');
    while (_p_pos + 32 <= _p_input.longitud) {
        __m256i chunk = _mm256_loadu_si256((const __m256i*)(_p_input.datos + _p_pos));
        __m256i cmp_q = _mm256_cmpeq_epi8(chunk, quote);
        __m256i cmp_b = _mm256_cmpeq_epi8(chunk, bslash);
        __m256i special = _mm256_or_si256(cmp_q, cmp_b);
        int mask = _mm256_movemask_epi8(special);
        if (mask != 0) {
            // Found quote or backslash; find first position
            int pos = __builtin_ctz((unsigned int)mask);
            _p_pos += pos;
            if (_p_input.datos[_p_pos] == '\\') {
                // Escaped character: skip it and continue
                _p_pos += 2;
            } else {
                // Found closing quote: in-place string (sin malloc)
                int len = _p_pos - start;
                char* p = (char*)_p_input.datos + start;
                p[len] = '\0';  // null-terminate in buffer (writable)
                _p_pos++;  // consume closing quote
                return (CadenaSegura){ .longitud = len, .datos = p };
            }
        } else {
            _p_pos += 32;  // No special chars in this chunk
        }
    }
    // Fallback to scalar for remaining characters
    while (_p_pos < _p_input.longitud) {
        char c = _p_input.datos[_p_pos];
        if (c == '"') break;
        if (c == '\\') _p_pos++;
        _p_pos++;
    }
    if (_p_pos >= _p_input.longitud) return (CadenaSegura){0};
    int end = _p_pos;
    _p_pos++;
    int len = end - start;
    char* p = (char*)_p_input.datos + start;
    p[len] = '\0';  // null-terminate in buffer (writable)
    return (CadenaSegura){ .longitud = len, .datos = p };
}
#else
static CadenaSegura _parse_string_value() {
    if (_advance() != '"') return (CadenaSegura){0};
    int start = _p_pos;
    while (_p_pos < _p_input.longitud) {
        char c = _p_input.datos[_p_pos];
        if (c == '"') break;
        if (c == '\\') _p_pos++;
        _p_pos++;
    }
    if (_p_pos >= _p_input.longitud) return (CadenaSegura){0};
    int end = _p_pos;
    _p_pos++;
    int len = end - start;
    char* p = (char*)_p_input.datos + start;
    p[len] = '\0';  // null-terminate in buffer (in-place, sin malloc)
    return (CadenaSegura){ .longitud = len, .datos = p };
}
#endif

static int _match_str(const char* expected) {
    int len = (int)strlen(expected);
    if (_p_pos + len > _p_input.longitud) return 0;
    if (strncmp(_p_input.datos + _p_pos, expected, len) == 0) {
        _p_pos += len;
        return 1;
    }
    return 0;
}

static float _parse_number_value() {
    int start = _p_pos;
    if (_p_pos < _p_input.longitud && _p_input.datos[_p_pos] == '-') _p_pos++;
    while (_p_pos < _p_input.longitud && _p_input.datos[_p_pos] >= '0' && _p_input.datos[_p_pos] <= '9') _p_pos++;
    if (_p_pos < _p_input.longitud && _p_input.datos[_p_pos] == '.') {
        _p_pos++;
        while (_p_pos < _p_input.longitud && _p_input.datos[_p_pos] >= '0' && _p_input.datos[_p_pos] <= '9') _p_pos++;
    }
    if (_p_pos < _p_input.longitud && (_p_input.datos[_p_pos] == 'e' || _p_input.datos[_p_pos] == 'E')) {
        _p_pos++;
        if (_p_pos < _p_input.longitud && (_p_input.datos[_p_pos] == '+' || _p_input.datos[_p_pos] == '-')) _p_pos++;
        while (_p_pos < _p_input.longitud && _p_input.datos[_p_pos] >= '0' && _p_input.datos[_p_pos] <= '9') _p_pos++;
    }
    int len = _p_pos - start;
    char buf[64];
    if (len > 63) return 0.0f;  // safety guard
    memcpy(buf, _p_input.datos + start, len);
    buf[len] = '\0';
    float val = (float)strtod(buf, NULL);
    return val;
}

// Forward declaration
static NodoJson _parse_value();

static NodoJson _parse_object() {
    NodoJson n = {0};
    n.tipo = 5;
    _advance();
    _skip_ws();
    if (_peek() == '}') { _advance(); return n; }
    ParArr pares;
    par_arr_init(&pares);
    while (1) {
        _skip_ws();
        if (_peek() == '}') break;
        if (pares.count > 0) {
            if (_peek() != ',') break;
            _advance();
            _skip_ws();
        }
        CadenaSegura key = _parse_string_value();
        if (key.datos == NULL) {
            n.tipo = -1;
            n.valor_str = (CadenaSegura){ .longitud = 27, .datos = "fjson: clave de objeto invalida" };
            return n;
        }
        _skip_ws();
        if (_advance() != ':') {
            n.tipo = -1;
            n.valor_str = (CadenaSegura){ .longitud = 25, .datos = "fjson: se esperaba ':'" };
            return n;
        }
        NodoJson val = _parse_value();
        if (val.tipo < 0) {
            _json_nodo_liberar(val);
            return val; // propagate error
        }
        NodoJson* val_ptr = (NodoJson*)pool_alloc(sizeof(NodoJson));
        if (val_ptr) *val_ptr = val;
        par_arr_append(&pares, key, val_ptr);
    }
    _skip_ws();
    if (_peek() == '}') _advance();
    n.longitud = pares.count;
    n.objeto_pares = par_arr_detach(&pares);
    return n;
}

static NodoJson _parse_array() {
    NodoJson n = {0};
    n.tipo = 4;
    _advance();
    _skip_ws();
    if (_peek() == ']') { _advance(); return n; }
    NodoArr arr;
    nodo_arr_init(&arr);
    while (1) {
        _skip_ws();
        if (_peek() == ']') break;
        if (arr.count > 0) {
            if (_peek() != ',') break;
            _advance();
            _skip_ws();
        }
        NodoJson val = _parse_value();
        if (val.tipo < 0) {
            _json_nodo_liberar(val);
            return val; // propagate error
        }
        nodo_arr_append(&arr, val);
    }
    _skip_ws();
    if (_peek() == ']') _advance();
    n.longitud = arr.count;
    n.arreglo_hijos = nodo_arr_detach(&arr);
    return n;
}

static NodoJson _parse_value() {
    NodoJson n = {0};
    _skip_ws();
    int c = _peek();
    if (c == '{') return _parse_object();
    if (c == '[') return _parse_array();
    if (c == '"') {
        CadenaSegura s = _parse_string_value();
        if (s.datos == NULL) { n.tipo = -1; n.valor_str = (CadenaSegura){ .longitud = 25, .datos = "fjson: cadena sin cerrar" }; return n; }
        n.tipo = 3;
        n.valor_str = s;
        return n;
    }
    if (c == 't') { if (_match_str("true")) { n.tipo = 1; n.valor_bool = 1; return n; } }
    if (c == 'f') { if (_match_str("false")) { n.tipo = 1; n.valor_bool = 0; return n; } }
    if (c == 'n') { if (_match_str("null")) { n.tipo = 0; return n; } }
    if (c == '-' || (c >= '0' && c <= '9')) {
        n.tipo = 2;
        n.valor_num = _parse_number_value();
        return n;
    }
    n.tipo = -1;
    n.valor_str = (CadenaSegura){ .longitud = 22, .datos = "fjson: valor inesperado" };
    return n;
}

NodoJson _json_parse(CadenaSegura entrada) {
    _json_init(entrada);
    NodoJson resultado = _parse_value();
    if (resultado.tipo < 0) { _json_nodo_liberar(resultado); return resultado; }
    _skip_ws();
    if (_peek() != -1) {
        _json_nodo_liberar(resultado);
        NodoJson e = {0};
        e.tipo = -1;
        e.valor_str = (CadenaSegura){ .longitud = 39, .datos = "fjson: contenido extra despues del valor" };
        return e;
    }
    return resultado;
}

// --- Deep clone for safe getter returns ---

NodoJson _json_nodo_clonar(NodoJson src) {
    NodoJson n = src;
    if (n.tipo == 3 && n.valor_str.datos) {
        char* dup = (char*)malloc(n.valor_str.longitud + 1);
        if (dup) memcpy(dup, n.valor_str.datos, n.valor_str.longitud + 1);
        n.valor_str.datos = dup;
    } else if (n.tipo == 4 && n.arreglo_hijos) {
        n.arreglo_hijos = (NodoJson*)malloc(n.longitud * sizeof(NodoJson));
        for (int i = 0; i < n.longitud; i++)
            n.arreglo_hijos[i] = _json_nodo_clonar(src.arreglo_hijos[i]);
    } else if (n.tipo == 5 && n.objeto_pares) {
        n.objeto_pares = (ParJson*)malloc(n.longitud * sizeof(ParJson));
        for (int i = 0; i < n.longitud; i++) {
            n.objeto_pares[i].clave = src.objeto_pares[i].clave;
            if (n.objeto_pares[i].clave.datos) {
                char* dup = (char*)malloc(n.objeto_pares[i].clave.longitud + 1);
                if (dup) memcpy(dup, n.objeto_pares[i].clave.datos, n.objeto_pares[i].clave.longitud + 1);
                n.objeto_pares[i].clave.datos = dup;
            }
            n.objeto_pares[i].valor = (NodoJson*)malloc(sizeof(NodoJson));
            if (n.objeto_pares[i].valor)
                *n.objeto_pares[i].valor = _json_nodo_clonar(*src.objeto_pares[i].valor);
        }
    }
    return n;
}

NodoJson _json_array_get(NodoJson nodo, int indice) {
    if (nodo.tipo != 4 || indice < 0 || indice >= nodo.longitud)
        return (NodoJson){0};
    return _json_nodo_clonar(nodo.arreglo_hijos[indice]);
}

NodoJson _json_object_get(NodoJson nodo, CadenaSegura clave) {
    if (nodo.tipo != 5)
        return (NodoJson){0};
    for (int i = 0; i < nodo.longitud; i++) {
        ParJson* p = &nodo.objeto_pares[i];
        if (p->clave.longitud == clave.longitud &&
            (clave.longitud == 0 || strncmp(p->clave.datos, clave.datos, clave.longitud) == 0))
            return _json_nodo_clonar(*p->valor);
    }
    return (NodoJson){0};
}

// ============================================================
// std.toml — TOML Parser (Subset para Axon)
// ============================================================

typedef struct ParToml ParToml;
typedef struct NodoToml NodoToml;

struct ParToml {
    CadenaSegura clave;
    NodoToml* valor;
};

struct NodoToml {
    int tipo;           // -1=Error, 0=Nulo, 1=Tabla, 2=Cadena, 3=TablaEnLinea
    CadenaSegura valor_str;
    ParToml* pares;
    int longitud;
};

// --- Cache types (matching _synapse_shared.h for linker) ---

typedef struct CacheEntry {
    CadenaSegura clave;
    CadenaSegura archivo_fuente;
    CadenaSegura archivo_objeto;
    CadenaSegura hash_fuente;
    CadenaSegura hashes_deps;
    CadenaSegura flags_compilacion;
    CadenaSegura version_compilador;
    int timestamp;
    int tamano_bytes;
} CacheEntry;

typedef struct CacheStats {
    int total_entradas;
    int hits;
    int misses;
    int tamano_total_bytes;
    int hits_ultima_ejecucion;
    int misses_ultima_ejecucion;
} CacheStats;

typedef struct CampoToml {
    int tipo;
    CadenaSegura valor_str;
    int valor_ent;
} CampoToml;

// --- Ed25519 Verification (via TweetNaCl) ---
// Verifica una firma Ed25519 sobre un mensaje.
// Parametros:
//   mensaje: texto plano original
//   firma: firma de 64 bytes (R || S)
//   clave_publica: clave publica de 32 bytes
// Retorna: 0 si la firma es valida, -1 si es invalida

// randombytes stub for TweetNaCl (only needed if crypto_sign_keypair is linked)
// Uses OS-provided CSPRNG instead of rand() for cryptographic security.
void randombytes(unsigned char* x, unsigned long long xlen) ;
void randombytes(unsigned char* x, unsigned long long xlen) {
    if (xlen == 0) return;
#ifdef _WIN32
    HCRYPTPROV hProv = 0;
    if (CryptAcquireContextA(&hProv, NULL, NULL, PROV_RSA_FULL,
                             CRYPT_VERIFYCONTEXT)) {
        CryptGenRandom(hProv, (DWORD)xlen, x);
        CryptReleaseContext(hProv, 0);
    } else {
        for (unsigned long long i = 0; i < xlen; i++) x[i] = 0;
    }
#else
    FILE* f = fopen("/dev/urandom", "rb");
    if (f) {
        size_t n = fread(x, 1, (size_t)xlen, f);
        fclose(f);
        for (unsigned long long i = n; i < xlen; i++) x[i] = 0;
    } else {
        #ifdef __linux__
        ssize_t ret = getrandom(x, (size_t)xlen, 0);
        if (ret < 0) {
            for (unsigned long long i = 0; i < xlen; i++) x[i] = 0;
        }
        #else
        for (unsigned long long i = 0; i < xlen; i++) x[i] = 0;
        #endif
    }
#endif
}

int _syn_ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica) {
    if (firma.longitud < 64 || clave_publica.longitud < 32) {
        return -1;
    }
    unsigned long long mlen = 0;
    unsigned char* sm = (unsigned char*)malloc((size_t)(mensaje.longitud + 64));
    if (!sm) return -1;
    memcpy(sm, firma.datos, 64);
    memcpy(sm + 64, mensaje.datos, (size_t)mensaje.longitud);
    unsigned long long smlen = (unsigned long long)(mensaje.longitud + 64);
    unsigned char* pk = (unsigned char*)clave_publica.datos;
    // Use separate buffer for output (TweetNaCl requires m != sm)
    // crypto_sign_open writes smlen (mensaje.longitud+64) bytes into m, so allocate that.
    unsigned char* m_buf = (unsigned char*)malloc((size_t)(mensaje.longitud + 64));
    if (!m_buf) { free(sm); return -1; }
    int rc = crypto_sign_open(m_buf, &mlen, sm, smlen, pk);
    free(sm);
    free(m_buf);
    return rc;
}

// --- TOML parser state ---
static CadenaSegura _t_input;
static int _t_pos;
static int _t_linea;
static int _t_error;

static int _t_peek(void) {
    if (_t_pos >= _t_input.longitud) return -1;
    return (unsigned char)_t_input.datos[_t_pos];
}

static void _t_advance(void) {
    if (_t_pos < _t_input.longitud) _t_pos++;
}

static void _t_skip_ws(void) {
    while (_t_pos < _t_input.longitud) {
        char c = _t_input.datos[_t_pos];
        if (c == ' ' || c == '\t') { _t_pos++; continue; }
        break;
    }
}

static void _t_skip_line(void) {
    while (_t_pos < _t_input.longitud && _t_input.datos[_t_pos] != '\n') _t_pos++;
    if (_t_pos < _t_input.longitud) _t_pos++;
    _t_linea++;
}

static int _t_skip_newline(void) {
    if (_t_peek() == '\r') { _t_advance(); }
    if (_t_peek() == '\n') { _t_advance(); _t_linea++; return 1; }
    return 0;
}

static NodoToml _t_parse_inline_table(void);

static CadenaSegura _t_strdup_c(const char* src, int len) {
    if (len <= 0) return (CadenaSegura){0};
    char* buf = (char*)malloc(len + 1);
    if (!buf) return (CadenaSegura){0};
    memcpy(buf, src, len);
    buf[len] = '\0';
    return (CadenaSegura){ .longitud = len, .datos = buf };
}

static CadenaSegura _t_parse_bare_key(void) {
    int start = _t_pos;
    while (_t_pos < _t_input.longitud) {
        char c = _t_input.datos[_t_pos];
        if (c == '=' || c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '#' || c == '}' || c == ',' || c == ']')
            break;
        _t_pos++;
    }
    int len = _t_pos - start;
    if (len == 0) return (CadenaSegura){0};
    return _t_strdup_c(_t_input.datos + start, len);
}

static CadenaSegura _t_parse_string(void) {
    if (_t_peek() != '"') {
        _t_error = 1;
        return (CadenaSegura){0};
    }
    _t_advance();
    int start = _t_pos;
    while (_t_pos < _t_input.longitud && _t_input.datos[_t_pos] != '"') {
        if (_t_input.datos[_t_pos] == '\\') _t_pos++;
        _t_pos++;
    }
    if (_t_pos >= _t_input.longitud) {
        _t_error = 1;
        return (CadenaSegura){0};
    }
    int raw_len = _t_pos - start;
    char* buf = (char*)malloc(raw_len + 1);
    int wi = 0;
    for (int i = 0; i < raw_len; i++) {
        if (_t_input.datos[start + i] == '\\' && i + 1 < raw_len) {
            i++;
            switch (_t_input.datos[start + i]) {
                case '"': buf[wi++] = '"'; break;
                case '\\': buf[wi++] = '\\'; break;
                case 'n': buf[wi++] = '\n'; break;
                case 't': buf[wi++] = '\t'; break;
                default: buf[wi++] = _t_input.datos[start + i]; break;
            }
        } else {
            buf[wi++] = _t_input.datos[start + i];
        }
    }
    buf[wi] = '\0';
    _t_advance();
    return (CadenaSegura){ .longitud = wi, .datos = buf };
}

static NodoToml _t_parse_value(void) {
    _t_skip_ws();
    int c = _t_peek();
    if (c == '"') {
        CadenaSegura s = _t_parse_string();
        return (NodoToml){ .tipo = 2, .valor_str = s };
    }
    if (c == '{') {
        return _t_parse_inline_table();
    }
    // Bare value (treat as string for now)
    CadenaSegura s = _t_parse_bare_key();
    if (_t_error || s.longitud == 0) {
        if (s.datos) free((void*)s.datos);
        _t_error = 1;
        return (NodoToml){ .tipo = -1 };
    }
    return (NodoToml){ .tipo = 2, .valor_str = s };
}

static void _t_nodo_liberar_internal(NodoToml n);

static NodoToml _t_parse_inline_table(void) {
    _t_advance();
    NodoToml tbl = { .tipo = 3 };
    int cap = 0;
    while (_t_pos < _t_input.longitud && !_t_error) {
        _t_skip_ws();
        int c = _t_peek();
        if (c == '}') { _t_advance(); break; }
        if (c == ',' || c == '\n' || c == '\r') { _t_advance(); continue; }

        CadenaSegura key = _t_parse_bare_key();
        if (_t_error || key.longitud == 0) { free((void*)key.datos); break; }
        _t_skip_ws();
        if (_t_peek() != '=') { _t_error = 1; free((void*)key.datos); break; }
        _t_advance();

        NodoToml val = _t_parse_value();
        if (_t_error) { free((void*)key.datos); _t_nodo_liberar_internal(val); break; }

        if (tbl.longitud >= cap) {
            cap = cap == 0 ? 4 : cap * 2;
            tbl.pares = (ParToml*)realloc(tbl.pares, cap * sizeof(ParToml));
        }
        ParToml* p = &tbl.pares[tbl.longitud++];
        p->clave = key;
        p->valor = (NodoToml*)malloc(sizeof(NodoToml));
        *p->valor = val;

        _t_skip_ws();
        if (_t_peek() == '}') { _t_advance(); break; }
        if (_t_peek() == ',') _t_advance();
    }
    return tbl;
}

static CadenaSegura _t_parse_section_key(void) {
    _t_skip_ws();
    int start = _t_pos;
    while (_t_pos < _t_input.longitud) {
        char c = _t_input.datos[_t_pos];
        if (c == ']' || c == '\n' || c == '\r') break;
        _t_pos++;
    }
    int end = _t_pos;
    while (end > start && (_t_input.datos[end-1] == ' ' || _t_input.datos[end-1] == '\t')) end--;
    if (_t_peek() != ']') return (CadenaSegura){0};
    return _t_strdup_c(_t_input.datos + start, end - start);
}

static NodoToml* _t_find_or_create_table(NodoToml* root, CadenaSegura name) {
    for (int i = 0; i < root->longitud; i++) {
        ParToml* p = &root->pares[i];
        if (p->clave.longitud == name.longitud &&
            (name.longitud == 0 || strncmp(p->clave.datos, name.datos, name.longitud) == 0)) {
            return p->valor;
        }
    }
    NodoToml* tbl = (NodoToml*)calloc(1, sizeof(NodoToml));
    tbl->tipo = 1;
    if (root->longitud >= 0) {
        root->pares = (ParToml*)realloc(root->pares, (root->longitud + 1) * sizeof(ParToml));
        root->pares[root->longitud].clave = _t_strdup_c(name.datos, name.longitud);
        root->pares[root->longitud].valor = tbl;
        root->longitud++;
    }
    return tbl;
}

static void _t_nodo_liberar_internal(NodoToml n) {
    if (n.tipo == 2 || n.tipo == -1) {
        // NOTA: NO liberamos n.valor_str.datos aquí porque la propiedad
        // se transfiere al llamante cuando accede a campo.valor_str.
    } else if (n.tipo == 1 || n.tipo == 3) {
        if (n.pares) {
            for (int i = 0; i < n.longitud; i++) {
                if (n.pares[i].clave.datos) free((void*)n.pares[i].clave.datos);
                if (n.pares[i].valor) {
                    _t_nodo_liberar_internal(*n.pares[i].valor);
                    free(n.pares[i].valor);
                    n.pares[i].valor = NULL;
                }
            }
            free(n.pares);
            n.pares = NULL;
        }
    }
}

NodoToml _toml_nodo_new(void) {
    return (NodoToml){0};
}

void _toml_nodo_liberar(NodoToml n) {
    _t_nodo_liberar_internal(n);
}

static NodoToml _t_nodo_clonar(NodoToml src) {
    NodoToml n = { .tipo = src.tipo, .longitud = 0 };
    if (src.tipo == 2 || src.tipo == -1) {
        n.valor_str = _t_strdup_c(src.valor_str.datos, src.valor_str.longitud);
    } else if (src.tipo == 1 || src.tipo == 3) {
        if (src.pares && src.longitud > 0) {
            n.pares = (ParToml*)malloc(src.longitud * sizeof(ParToml));
            n.longitud = src.longitud;
            for (int i = 0; i < src.longitud; i++) {
                n.pares[i].clave = _t_strdup_c(src.pares[i].clave.datos, src.pares[i].clave.longitud);
                n.pares[i].valor = (NodoToml*)malloc(sizeof(NodoToml));
                *n.pares[i].valor = _t_nodo_clonar(*src.pares[i].valor);
            }
        }
    }
    return n;
}

NodoToml _toml_object_get(NodoToml nodo, CadenaSegura clave) {
    if (nodo.tipo != 1 && nodo.tipo != 3)
        return (NodoToml){0};
    for (int i = 0; i < nodo.longitud; i++) {
        ParToml* p = &nodo.pares[i];
        if (p->clave.longitud == clave.longitud &&
            (clave.longitud == 0 || strncmp(p->clave.datos, clave.datos, clave.longitud) == 0))
            return _t_nodo_clonar(*p->valor);
    }
    return (NodoToml){0};
}

NodoToml _toml_parse(CadenaSegura entrada) {
    _t_input = entrada;
    _t_pos = 0;
    _t_linea = 1;
    _t_error = 0;

    NodoToml root = { .tipo = 1 };
    NodoToml* current = &root;

    while (_t_pos < _t_input.longitud && !_t_error) {
        _t_skip_ws();
        int c = _t_peek();
        if (c < 0) break;
        if (c == '\n' || c == '\r') { _t_skip_newline(); continue; }
        if (c == '#') { _t_skip_line(); continue; }

        if (c == '[') {
            _t_advance();
            CadenaSegura sec_name = _t_parse_section_key();
            if (_t_error || sec_name.longitud == 0) {
                _t_error = 1;
                break;
            }
            _t_advance();
            NodoToml* tbl = _t_find_or_create_table(&root, sec_name);
            free((void*)sec_name.datos);
            current = tbl ? tbl : &root;
            _t_skip_line();
            continue;
        }

        // Key-value pair
        CadenaSegura key = _t_parse_bare_key();
        _t_skip_ws();
        if (_t_peek() != '=') { _t_error = 1; free((void*)key.datos); break; }
        _t_advance();
        NodoToml val = _t_parse_value();
        if (_t_error) {
            free((void*)key.datos);
            _t_nodo_liberar_internal(val);
            break;
        }

        if (current->longitud >= 0) {
            current->pares = (ParToml*)realloc(current->pares, (current->longitud + 1) * sizeof(ParToml));
            current->pares[current->longitud].clave = key;
            current->pares[current->longitud].valor = (NodoToml*)malloc(sizeof(NodoToml));
            *current->pares[current->longitud].valor = val;
            current->longitud++;
        }
        _t_skip_line();
    }

    if (_t_error) {
        _t_nodo_liberar_internal(root);
        char err_buf[128];
        int err_len = snprintf(err_buf, sizeof(err_buf),
            "Error TOML linea %d", _t_linea);
        NodoToml err = { .tipo = -1 };
        err.valor_str = _t_strdup_c(err_buf, err_len);
        return err;
    }

    return root;
}

// ============================================================
// std.tiempo — Time & Profiling
// ============================================================

int64_t _syn_ahora_ms(void) {
#ifdef _WIN32
    FILETIME ft;
    GetSystemTimeAsFileTime(&ft);
    uint64_t t = ((uint64_t)ft.dwHighDateTime << 32) | ft.dwLowDateTime;
    // Convert from 100-ns intervals since 1601-01-01 to ms since 1970-01-01
    return (int64_t)((t - 116444736000000000ULL) / 10000);
#else
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (int64_t)ts.tv_sec * 1000 + (int64_t)ts.tv_nsec / 1000000;
#endif
}

void _syn_dormir_ms(int ms) {
#ifdef _WIN32
    Sleep((DWORD)ms);
#else
    struct timespec ts;
    ts.tv_sec = ms / 1000;
    ts.tv_nsec = (long)(ms % 1000) * 1000000L;
    nanosleep(&ts, NULL);
#endif
}

// ============================================================
// std.cripto — SHA-256 (FIPS 180-4) + Ed25519 (TweetNaCl)
#include "axon/tweetnacl.h"// --- SHA-256 (sin cambios) ---
// ============================================================
// (typedef SHA256_CTX movido a synapse_rt_types.h en D-9(d) corte 4:
//  lo comparten synapse_rt.c y runtime/core/cluster.c.)

static const uint32_t K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

#define ROTR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))
#define CH(x, y, z) (((x) & (y)) ^ (~(x) & (z)))
#define MAJ(x, y, z) (((x) & (y)) ^ ((x) & (z)) ^ ((y) & (z)))
#define SIG0(x) (ROTR(x, 2) ^ ROTR(x, 13) ^ ROTR(x, 22))
#define SIG1(x) (ROTR(x, 6) ^ ROTR(x, 11) ^ ROTR(x, 25))
#define sig0(x) (ROTR(x, 7) ^ ROTR(x, 18) ^ ((x) >> 3))
#define sig1(x) (ROTR(x, 17) ^ ROTR(x, 19) ^ ((x) >> 10))

static void sha256_transform(SHA256_CTX* ctx, const uint8_t* block) {
    uint32_t W[64];
    for (int i = 0; i < 16; i++) {
        W[i] = ((uint32_t)block[i*4] << 24) | ((uint32_t)block[i*4+1] << 16)
             | ((uint32_t)block[i*4+2] << 8)  | (uint32_t)block[i*4+3];
    }
    for (int i = 16; i < 64; i++) {
        W[i] = sig1(W[i-2]) + W[i-7] + sig0(W[i-15]) + W[i-16];
    }

    uint32_t a = ctx->state[0], b = ctx->state[1];
    uint32_t c = ctx->state[2], d = ctx->state[3];
    uint32_t e = ctx->state[4], f = ctx->state[5];
    uint32_t g = ctx->state[6], h = ctx->state[7];

    for (int i = 0; i < 64; i++) {
        uint32_t T1 = h + SIG1(e) + CH(e, f, g) + K[i] + W[i];
        uint32_t T2 = SIG0(a) + MAJ(a, b, c);
        h = g; g = f; f = e; e = d + T1;
        d = c; c = b; b = a; a = T1 + T2;
    }

    ctx->state[0] += a; ctx->state[1] += b;
    ctx->state[2] += c; ctx->state[3] += d;
    ctx->state[4] += e; ctx->state[5] += f;
    ctx->state[6] += g; ctx->state[7] += h;
}

void sha256_init(SHA256_CTX* ctx) {
    ctx->state[0] = 0x6a09e667; ctx->state[1] = 0xbb67ae85;
    ctx->state[2] = 0x3c6ef372; ctx->state[3] = 0xa54ff53a;
    ctx->state[4] = 0x510e527f; ctx->state[5] = 0x9b05688c;
    ctx->state[6] = 0x1f83d9ab; ctx->state[7] = 0x5be0cd19;
    ctx->bitcount = 0;
    ctx->buffer_len = 0;
}

void sha256_update(SHA256_CTX* ctx, const uint8_t* data, size_t len) {
    for (size_t i = 0; i < len; i++) {
        ctx->buffer[ctx->buffer_len++] = data[i];
        ctx->bitcount += 8;
        if (ctx->buffer_len == SHA256_BLOCK_SIZE) {
            sha256_transform(ctx, ctx->buffer);
            ctx->buffer_len = 0;
        }
    }
}

void sha256_final(SHA256_CTX* ctx, uint8_t* digest) {
    uint64_t bitcount = ctx->bitcount;
    ctx->buffer[ctx->buffer_len++] = 0x80;
    if (ctx->buffer_len > 56) {
        while (ctx->buffer_len < SHA256_BLOCK_SIZE)
            ctx->buffer[ctx->buffer_len++] = 0;
        sha256_transform(ctx, ctx->buffer);
        ctx->buffer_len = 0;
    }
    while (ctx->buffer_len < 56)
        ctx->buffer[ctx->buffer_len++] = 0;
    for (int i = 7; i >= 0; i--) {
        ctx->buffer[56 + i] = (uint8_t)(bitcount >> ((7 - i) * 8));
    }
    sha256_transform(ctx, ctx->buffer);
    for (int i = 0; i < 8; i++) {
        digest[i*4]   = (ctx->state[i] >> 24) & 0xFF;
        digest[i*4+1] = (ctx->state[i] >> 16) & 0xFF;
        digest[i*4+2] = (ctx->state[i] >> 8) & 0xFF;
        digest[i*4+3] = ctx->state[i] & 0xFF;
    }
}

CadenaSegura _syn_sha256_texto(CadenaSegura datos) {
    SHA256_CTX ctx;
    uint8_t digest[SHA256_DIGEST_SIZE];
    char hex[65];

    sha256_init(&ctx);
    sha256_update(&ctx, (const uint8_t*)datos.datos, (size_t)datos.longitud);
    sha256_final(&ctx, digest);

    for (int i = 0; i < SHA256_DIGEST_SIZE; i++) {
        sprintf(hex + i * 2, "%02x", digest[i]);
    }
    hex[64] = '\0';

    char* data = (char*)malloc(65);
    if (!data) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(data, hex, 65);
    return (CadenaSegura){ .longitud = 64, .datos = data };
}

// ============================================================
// std.http — HTTP Server (Minimalista, sincrono, single-thread)
// ============================================================

int _syn_servidor_escuchar(int puerto) {
    int fd = (int)socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return -1;

    int opt = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons((unsigned short)puerto);

    if (bind(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        _syn_cerrar_socket(fd);
        return -1;
    }
    if (listen(fd, 5) < 0) {
        _syn_cerrar_socket(fd);
        return -1;
    }
    return fd;
}

int _syn_servidor_aceptar(int fd_servidor) {
    struct sockaddr_in cliente;
    socklen_t tam = sizeof(cliente);
    return (int)accept(fd_servidor, (struct sockaddr*)&cliente, &tam);
}

// Lee una peticion HTTP completa (hasta \r\n\r\n + contenido opcional)
CadenaSegura _syn_http_leer_peticion(int fd_cliente) {
    char buf[4096];
    int total = 0;
    int n;

    while (total < (int)sizeof(buf) - 1) {
        n = (int)recv(fd_cliente, buf + total, (size_t)(sizeof(buf) - 1 - total), 0);
        if (n <= 0) break;
        total += n;
        buf[total] = '\0';
        // Check for end of headers
        if (total >= 4 && memcmp(buf + total - 4, "\r\n\r\n", 4) == 0)
            break;
    }
    if (total <= 0) return (CadenaSegura){ .longitud = 0, .datos = "" };

    char* data = (char*)malloc((size_t)(total + 1));
    if (!data) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(data, buf, (size_t)total);
    data[total] = '\0';
    return (CadenaSegura){ .longitud = total, .datos = data };
}

int _syn_http_enviar_respuesta(int fd_cliente, CadenaSegura respuesta) {
    int total = (int)send(fd_cliente, respuesta.datos, (size_t)respuesta.longitud, 0);
    return total;
}

void _syn_http_cerrar_cliente(int fd_cliente) {
    _syn_cerrar_socket(fd_cliente);
}

CadenaSegura _syn_http_respuesta_ok(int codigo, const char* tipo, const char* cuerpo, int lon) {
    char header[512];
    int hlen = snprintf(header, sizeof(header),
        "HTTP/1.1 %d OK\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %d\r\n"
        "Connection: close\r\n\r\n",
        codigo, tipo, lon);
    if (hlen < 0 || hlen >= (int)sizeof(header)) {
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
    int total = hlen + lon;
    char* buf = (char*)malloc((size_t)(total + 1));
    if (!buf) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(buf, header, (size_t)hlen);
    memcpy(buf + hlen, cuerpo, (size_t)lon);
    buf[total] = '\0';
    return (CadenaSegura){ .longitud = total, .datos = buf };
}

// --- std.ai (GGUF Reader / Memory Mapping) ---
// D-9(d) corte 3: bloque std.ai (GGUF/BPE/ModeloContexto/inferencia/oraculos)
// extraido a runtime/core/modelo.c (texto byte-identico, patron tensor.c R35).

// --- Cache-to-TOML helpers (externo stubs from cache.syn) ---
// (NO parte del corte std.ai: pertenece a nucleo/cache.syn, tipos en este archivo.)

struct NodoToml toml_desde_entrada(struct CacheEntry entry) {
    (void)entry;
    struct NodoToml doc = {0};
    doc.tipo = 1; doc.pares = NULL; doc.longitud = 0; doc.valor_str = (CadenaSegura){0, ""};
    return doc;
}

struct NodoToml toml_desde_stats(struct CacheStats entry) {
    (void)entry;
    struct NodoToml doc = {0};
    doc.tipo = 1; doc.pares = NULL; doc.longitud = 0; doc.valor_str = (CadenaSegura){0, ""};
    return doc;
}

CadenaSegura a_texto(struct NodoToml doc) {
    // Convert NodoToml to TOML text string
    // Minimal stub: returns empty string
    (void)doc;
    return (CadenaSegura){0, ""};
}

struct NodoToml actualizar_indice(struct NodoToml doc, struct CacheEntry entry) {
    // Update TOML index document with a new entry
    // Minimal stub: returns doc unchanged
    (void)entry;
    return doc;
}

// ============================================================================
// ============================================================
// Axon — HTTP download + TAR extraction + SHA-256 Lock
// ============================================================

// --- SHA-256 raw (binary digest to hex string) ---
// Returns hex string (heap-allocated), caller must free.
CadenaSegura _syn_sha256_hex(CadenaSegura datos) {
    SHA256_CTX ctx;
    uint8_t digest[SHA256_DIGEST_SIZE];
    sha256_init(&ctx);
    sha256_update(&ctx, (const uint8_t*)datos.datos, (size_t)datos.longitud);
    sha256_final(&ctx, digest);
    char hex[65];
    for (int i = 0; i < SHA256_DIGEST_SIZE; i++) {
        snprintf(hex + i * 2, 3, "%02x", digest[i]);
    }
    hex[64] = 0;
    char* data = (char*)malloc(65);
    if (!data) return (CadenaSegura){0, ""};
    memcpy(data, hex, 65);
    return (CadenaSegura){ .longitud = 64, .datos = data };
}

// --- Reusable: SHA-256 hash of a file on disk ---
// Returns hex string (heap-allocated), or empty string on failure.
CadenaSegura _syn_sha256_archivo(const char* ruta) {
    FILE* f = fopen(ruta, "rb");
    if (!f) return (CadenaSegura){0, ""};
    SHA256_CTX ctx;
    sha256_init(&ctx);
    uint8_t buf[8192];
    size_t n;
    while ((n = fread(buf, 1, sizeof(buf), f)) > 0) {
        sha256_update(&ctx, buf, n);
    }
    fclose(f);
    uint8_t digest[SHA256_DIGEST_SIZE];
    sha256_final(&ctx, digest);
    char hex[65];
    for (int i = 0; i < SHA256_DIGEST_SIZE; i++) {
        snprintf(hex + i * 2, 3, "%02x", digest[i]);
    }
    hex[64] = 0;
    char* data = (char*)malloc(65);
    if (!data) return (CadenaSegura){0, ""};
    memcpy(data, hex, 65);
    return (CadenaSegura){ .longitud = 64, .datos = data };
}

// --- HTTP GET: download URL content into a file on disk ---
// Returns 0 on success, -1 on failure.
// Writes response body to the specified output path.
int _syn_http_get_archivo(CadenaSegura host, int puerto, CadenaSegura ruta, const char* salida_ruta) {
    int fd = _syn_socket();
    if (fd < 0) return -1;
    if (_syn_conectar(fd, host.datos, puerto) < 0) {
        _syn_cerrar_socket(fd);
        return -1;
    }
    char req[4096];
    snprintf(req, sizeof(req),
        "GET %s HTTP/1.0\r\n"
        "Host: %s\r\n"
        "User-Agent: Synapse-Axon/2.0\r\n"
        "Connection: close\r\n"
        "\r\n",
        ruta.datos, host.datos);
    _syn_enviar(fd, req, (int)strlen(req));

    // Read response: skip headers, write body to file
    char buf[4096];
    int total = 0;
    int header_done = 0;
    FILE* out = fopen(salida_ruta, "wb");
    if (!out) { _syn_cerrar_socket(fd); return -1; }

    while (1) {
        int n = _syn_recibir(fd, buf, sizeof(buf) - 1);
        if (n <= 0) break;
        buf[n] = 0;
        total += n;

        if (!header_done) {
            char* body = strstr(buf, "\r\n\r\n");
            if (body) {
                header_done = 1;
                body += 4;
                int body_len = n - (int)(body - buf);
                if (body_len > 0) fwrite(body, 1, (size_t)body_len, out);
            }
        } else {
            fwrite(buf, 1, (size_t)n, out);
        }
    }
    fclose(out);
    _syn_cerrar_socket(fd);
    return header_done ? 0 : -1;
}

// --- POSIX TAR extraction (header-only, no compression) ---
// Extracts files from a .tar archive into the output directory.
// Returns 0 on success, -1 on failure.
// TAR format: 512-byte blocks, headers in ASCII octal.
int _syn_tar_extraer(const char* tar_ruta, const char* salida_dir) {
    FILE* f = fopen(tar_ruta, "rb");
    if (!f) return -1;

    // Create output directory
    char mkdir_cmd[1024];
#ifdef _WIN32
    snprintf(mkdir_cmd, sizeof(mkdir_cmd), "mkdir \"%s\" 2>nul", salida_dir);
#else
    snprintf(mkdir_cmd, sizeof(mkdir_cmd), "mkdir -p \"%s\" 2>/dev/null", salida_dir);
#endif
    system(mkdir_cmd);

    uint8_t block[512];
    int result = 0;

    while (1) {
        size_t n = fread(block, 1, 512, f);
        if (n < 512) break;  // EOF or partial block

        // Check for end-of-archive (two zero blocks)
        if (block[0] == 0) {
            // Skip second zero block
            fread(block, 1, 512, f);
            break;
        }

        // Parse header fields from octal ASCII
        char name[256];
        char size_str[13];
        char typeflag;
        char prefix[156];

        memcpy(name, block, 100); name[100] = 0;
        memcpy(size_str, block + 124, 12); size_str[12] = 0;
        typeflag = block[156];
        memcpy(prefix, block + 345, 155); prefix[155] = 0;

        // --- Path traversal protection (Manual 6 §6.1) ---
        // Reject absolute paths and directory escapes ("../" or "/.." components)
        int _pt_traversal = 0;
        if (name[0] == '/' || prefix[0] == '/') { _pt_traversal = 1; }
        // Check for ".." as a PATH COMPONENT (not substring - avoids foo..bar false positives)
        if (!_pt_traversal) {
            const char* _checks[] = {name, prefix, NULL};
            for (int _ci = 0; _checks[_ci] && !_pt_traversal; _ci++) {
                const char* _p = _checks[_ci];
                int _len = (int)strlen(_p);
                // Check start: "../"
                if (_len >= 3 && _p[0] == '.' && _p[1] == '.' && _p[2] == '/') { _pt_traversal = 1; }
                // Check middle: "/../"
                if (!_pt_traversal) {
                    for (int _si = 1; _si < _len - 3; _si++) {
                        if (_p[_si] == '/' && _p[_si+1] == '.' && _p[_si+2] == '.' && _p[_si+3] == '/') {
                            _pt_traversal = 1; break;
                        }
                    }
                }
                // Check end: "/.."
                if (!_pt_traversal && _len >= 3 && _p[_len-3] == '/' && _p[_len-2] == '.' && _p[_len-1] == '.') {
                    _pt_traversal = 1;
                }
                // Check exact: ".."
                if (!_pt_traversal && _len == 2 && _p[0] == '.' && _p[1] == '.') { _pt_traversal = 1; }
            }
        }
        if (_pt_traversal) {
            fprintf(stderr, "[Axon] ERR_AXON_COMPROMISED: path traversal detectado en TAR: %s/%s\n", prefix, name);
            fclose(f);
            return -1;
        }

        // Build full path (prefix + "/" + name)
        char full_path[512];
        if (prefix[0]) {
            snprintf(full_path, sizeof(full_path), "%s/%s", salida_dir, prefix);
            // Ensure subdirectory exists
#ifdef _WIN32
            snprintf(mkdir_cmd, sizeof(mkdir_cmd), "mkdir \"%s\" 2>nul", full_path);
#else
            snprintf(mkdir_cmd, sizeof(mkdir_cmd), "mkdir -p \"%s\" 2>/dev/null", full_path);
#endif
            system(mkdir_cmd);
            snprintf(full_path, sizeof(full_path), "%s/%s/%s", salida_dir, prefix, name);
        } else {
            snprintf(full_path, sizeof(full_path), "%s/%s", salida_dir, name);
        }

        // Parse file size (octal string to long)
        unsigned long file_size = 0;
        for (int i = 0; size_str[i] && i < 12; i++) {
            if (size_str[i] >= '0' && size_str[i] <= '7') {
                file_size = file_size * 8 + (unsigned long)(size_str[i] - '0');
            } else break;
        }

        // Calculate data blocks (rounded up to 512)
        unsigned long data_blocks = (file_size + 511) / 512;

        if (typeflag == '0' || typeflag == '\0') {  // Regular file
            FILE* out = fopen(full_path, "wb");
            if (out) {
                unsigned long remaining = file_size;
                for (unsigned long bi = 0; bi < data_blocks; bi++) {
                    uint8_t data_block[512];
                    size_t dn = fread(data_block, 1, 512, f);
                    if (dn < 512) break;
                    size_t to_write = remaining > 512 ? 512 : remaining;
                    fwrite(data_block, 1, to_write, out);
                    remaining -= to_write;
                }
                fclose(out);
            } else {
                // Skip data blocks if can't open output
                fseek(f, (long)(data_blocks * 512), SEEK_CUR);
            }
        } else if (typeflag == '5') {  // Directory
#ifdef _WIN32
            snprintf(mkdir_cmd, sizeof(mkdir_cmd), "mkdir \"%s\" 2>nul", full_path);
#else
            snprintf(mkdir_cmd, sizeof(mkdir_cmd), "mkdir -p \"%s\" 2>/dev/null", full_path);
#endif
            system(mkdir_cmd);
        } else {
            // Unknown type, skip data blocks
            fseek(f, (long)(data_blocks * 512), SEEK_CUR);
        }
    }

    fclose(f);
    return result;
}

// --- Axon Lock: verify downloaded package against axon.lock ---
// axon.lock format (TOML):
//   [lock]
//   "paquete" = { version = "1.0.0", hash = "sha256:9f86d..." }
//
// Returns 0 on match, -1 on mismatch (caller should abort with ERR_AXON_COMPROMISED).
int _syn_axon_verificar_lock(const char* paquete, const char* version, const char* archivo_ruta, const char* lock_ruta) {
    // 1. Read existing axon.lock
    FILE* f = fopen(lock_ruta, "rb");
    if (!f) {
        // No lock file exists: create one
        CadenaSegura hash = _syn_sha256_archivo(archivo_ruta);
        if (hash.longitud == 0) return -1;
        f = fopen(lock_ruta, "wb");
        if (!f) { free((void*)hash.datos); return -1; }
        fprintf(f, "[lock]\n\"%s\" = { version = \"%s\", hash = \"sha256:%s\" }\n", paquete, version, hash.datos);
        fclose(f);
        fprintf(stderr, "[Axon] Lock creado: %s\n", lock_ruta);
        free((void*)hash.datos);
        return 0;
    }

    // 2. Lock exists: read and parse it
    fseek(f, 0, SEEK_END);
    long fsz = ftell(f);
    fseek(f, 0, SEEK_SET);
    char* content = (char*)malloc((size_t)fsz + 1);
    if (!content) { fclose(f); return -1; }
    fread(content, 1, (size_t)fsz, f);
    fclose(f);
    content[fsz] = 0;

    // Simple TOML parsing: find sha256:... hash for this package
    char search_key[256];
    snprintf(search_key, sizeof(search_key), "\"%s\"", paquete);
    char* pkg_start = strstr(content, search_key);
    if (!pkg_start) {
        // Package not in lock: append it
        free(content);
        CadenaSegura hash = _syn_sha256_archivo(archivo_ruta);
        if (hash.longitud == 0) return -1;
        f = fopen(lock_ruta, "ab");
        if (!f) { free((void*)hash.datos); return -1; }
        fprintf(f, "\"%s\" = { version = \"%s\", hash = \"sha256:%s\" }\n", paquete, version, hash.datos);
        fclose(f);
        free((void*)hash.datos);
        return 0;
    }

    // Find hash field
    char* hash_field = strstr(pkg_start, "sha256:");
    if (!hash_field) { free(content); return -1; }
    hash_field += 7;  // skip "sha256:"
    char expected_hash[65];
    int hi = 0;
    while (hi < 64 && hash_field[hi] && hash_field[hi] != '"' && hash_field[hi] != '}' && hash_field[hi] != ' ' && hash_field[hi] != '\n') {
        expected_hash[hi] = hash_field[hi];
        hi++;
    }
    expected_hash[hi] = 0;
    free(content);

    // 3. Compute actual hash of downloaded file
    CadenaSegura actual_hash = _syn_sha256_archivo(archivo_ruta);
    if (actual_hash.longitud == 0) return -1;

    // 4. Compare (save hash string BEFORE free)
    int match = (strcmp(expected_hash, actual_hash.datos) == 0);

    if (!match) {
        char _actual_hex[65];
        strncpy(_actual_hex, actual_hash.datos, 64);
        _actual_hex[64] = 0;
        free((void*)actual_hash.datos);
        fprintf(stderr, "[Axon] ERR_AXON_COMPROMISED: hash mismatch for '%s'\n", paquete);
        fprintf(stderr, "  Esperado: sha256:%s\n", expected_hash);
        fprintf(stderr, "  Obtenido: sha256:%s\n", _actual_hex);
        remove(archivo_ruta);
        return -1;
    }

    free((void*)actual_hash.datos);
    fprintf(stderr, "[Axon] Hash verificado: sha256:%s\n", expected_hash);
    return 0;
}

// --- Axon: Ed25519 signature verification ---
int _syn_axon_verificar_firma(const char* tar_ruta, const char* sig_ruta, const char* clave_publica_hex) {
    // 1. Read tar file (mensaje)
    FILE* f = fopen(tar_ruta, "rb");
    if (!f) return -1;
    fseek(f, 0, SEEK_END);
    long tar_sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (tar_sz < 0) { fclose(f); return -1; }
    size_t alloc_sz = (size_t)(tar_sz > 0 ? tar_sz : 1);
    unsigned char* buf = (unsigned char*)malloc(alloc_sz);
    if (!buf) { fclose(f); return -1; }
    if (tar_sz > 0) fread(buf, 1, (size_t)tar_sz, f);
    fclose(f);
    CadenaSegura mensaje = { .longitud = (int)tar_sz, .datos = (char*)buf };

    // 2. Read sig file (expect 64 bytes binary Ed25519 signature)
    f = fopen(sig_ruta, "rb");
    if (!f) { free(buf); return -1; }
    fseek(f, 0, SEEK_END);
    long sig_sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (sig_sz < 64) { fclose(f); free(buf); return -1; }
    unsigned char sig[64];
    size_t sig_rd = fread(sig, 1, 64, f);
    fclose(f);
    if (sig_rd < 64) { free(buf); return -1; }
    CadenaSegura firma = { .longitud = 64, .datos = (char*)sig };

    // 3. Convert hex public key (64 hex chars) to 32 bytes
    int pk_hex_len = (int)strlen(clave_publica_hex);
    if (pk_hex_len < 64) { free(buf); return -1; }
    unsigned char pk[32];
    for (int i = 0; i < 32; i++) {
        unsigned int byte_val;
        char hex_pair[3] = { clave_publica_hex[i*2], clave_publica_hex[i*2+1], 0 };
        if (sscanf(hex_pair, "%x", &byte_val) != 1) { free(buf); return -1; }
        pk[i] = (unsigned char)byte_val;
    }
    CadenaSegura clave_publica = { .longitud = 32, .datos = (char*)pk };

    // 4. Verify Ed25519 signature (calls _syn_ed25519_verificar defined above)
    int rc = _syn_ed25519_verificar(mensaje, firma, clave_publica);

    free(buf);  // sig and pk are stack-allocated
    return rc;  // 0 = signature valid, -1 = invalid
}

// Axon TOML cleanup wrapper (takes pointer, calls _toml_nodo_liberar by value)
void _syn_axon_limpiar_toml(void* n) {
    if (!n) return;
    _toml_nodo_liberar(*(NodoToml*)n);
}

// --- Axon: busqueda local (offline-first resolution) ---
// Returns:
//  0 = package already installed (extract_dir/principal.syn exists)
//  1 = package tar available in .axon_cache/
//  2 = package tar available in paquetes_oficiales/<ver>/
//  3+ = package found via AXON_PATH environment variable
// -1 = not found locally
int _syn_axon_buscar_local(const char* paquete, const char* version,
                           char* tar_path, int tar_sz,
                           char* extract_dir, int ext_sz) {
    // 0. Pre-set extract_dir regardless (needed by caller)
    snprintf(extract_dir, ext_sz, "axon_modules/%s", paquete);

    // 1. Check installed: axon_modules/<pkg>/principal.syn
    char chk[1024];
    snprintf(chk, sizeof(chk), "%s/principal.syn", extract_dir);
    FILE* f = fopen(chk, "rb");
    if (f) { fclose(f); fprintf(stderr, "[Axon] Local: ya instalado en %s\n", extract_dir); return 0; }

    // 2. Check .axon_cache/<pkg>.tar
    snprintf(tar_path, tar_sz, ".axon_cache/%s.tar", paquete);
    f = fopen(tar_path, "rb");
    if (f) { fclose(f); fprintf(stderr, "[Axon] Local: cache encontrado %s\n", tar_path); return 1; }

    // 3. Check paquetes_oficiales/<pkg>/<ver>.tar
    snprintf(tar_path, tar_sz, "paquetes_oficiales/%s/%s.tar", paquete, version);
    f = fopen(tar_path, "rb");
    if (f) { fclose(f); fprintf(stderr, "[Axon] Local: oficial %s\n", tar_path); return 2; }

    // 4. Check AXON_PATH env var directories (semicolon-separated)
    const char* axon_path = getenv("AXON_PATH");
    if (axon_path && axon_path[0]) {
        char path_copy[4096];
        strncpy(path_copy, axon_path, sizeof(path_copy)-1);
        path_copy[sizeof(path_copy)-1] = '\0';
        char* save;
        char* tok = strtok_r(path_copy, ";", &save);
        int origin = 3;
        while (tok) {
            snprintf(tar_path, tar_sz, "%s/%s/%s.tar", tok, paquete, version);
            f = fopen(tar_path, "rb");
            if (f) { fclose(f); fprintf(stderr, "[Axon] Local: AXON_PATH %s\n", tar_path); return origin; }
            tok = strtok_r(NULL, ";", &save);
            origin++;
        }
    }

    return -1; // not found
}

// --- Axon: escribir lock (append mode, crea entrada en axon.lock) ---
int _syn_axon_escribir_lock(const char* paquete, const char* version, const char* hash_sha256) {
    if (!hash_sha256 || !*hash_sha256) { fprintf(stderr,"[Axon] WARNING: hash vacio para lock\n"); return -1; }
    FILE* f = fopen("axon.lock", "ab");
    if (!f) { fprintf(stderr,"[Axon] WARNING: no se pudo abrir axon.lock\n"); return -1; }
    fseek(f, 0, SEEK_END);
    if (ftell(f) == 0) { fprintf(f, "[lock]\n"); }
    fprintf(f, "\"%s\" = { version = \"%s\", hash = \"sha256:%s\" }\n", paquete, version, hash_sha256);
    fclose(f);
    fprintf(stderr, "[Axon] Lock actualizado: %s v%s\n", paquete, version);
    return 0;
}

// ============================================================
// M9.0 — Debug/Trace System (time-travel debug, traza persistente)
// extraido a runtime/core/debug.c (D-9(d) corte 5, patron cluster.c R40).
// ============================================================

// ============================================================
// M8.1-M8.4 — std.cluster (transporte UDP/Ed25519, work-stealing,
// raft, checkpoint/live-migration) extraido a runtime/core/cluster.c
// (D-9(d) corte 4, patron modelo.c R39; texto byte-identico).
// El bloque M9.1-M9.3 (debug time-travel) permanece aqui (corte 5).
// ============================================================

// ============================================================
// M9.1-M9.3 — Deterministic Recording / Reversible Breakpoints /
// Memory Snapshots extraido a runtime/core/debug.c (corte 5).
// ============================================================

// ============================================================
// M8.5-M8.6 — std.cluster (auto-discovery & membership, UDP multicast)
// extraido a runtime/core/cluster.c (D-9(d) corte 4, patron modelo.c R39).
// ============================================================

// ============================================================
// M9.4 — Distributed Multi-Node Debugging extraido a
// runtime/core/debug.c (D-9(d) corte 5).
// ============================================================

// ============================================================
// FZ — Fuzzing Distribuido Multi-Nodo (M10.4) extraido a
// runtime/core/fuzz.c (D-9(d) corte 6, patron cluster.c R40).
// ============================================================

// ============================================================
// PATH TRAVERSAL PROTECTION — std.sistema helpers
// ============================================================

int str_eq(CadenaSegura a, CadenaSegura b) {
    if (a.longitud != b.longitud) return 0;
    return memcmp(a.datos, b.datos, (size_t)a.longitud) == 0;
}

CadenaSegura _syn_normalizar_ruta(CadenaSegura ruta) {
    char buf[4096];
    int len = ruta.longitud < 4095 ? ruta.longitud : 4095;
    memcpy(buf, ruta.datos, (size_t)len);
    buf[len] = '\0';
    // Resolve . and ..
    char normalized[4096];
    int nlen = 0;
    int i = 0;
    while (i < len) {
        if (buf[i] == '/' || buf[i] == '\\') {
            // Skip double separators
            while (i < len && (buf[i] == '/' || buf[i] == '\\')) i++;
            continue;
        }
        // Check for ..
        if (buf[i] == '.' && i + 1 < len && buf[i+1] == '.') {
            if (i + 2 >= len || buf[i+2] == '/' || buf[i+2] == '\\') {
                // Go back one component
                while (nlen > 0 && normalized[nlen-1] != '/' && normalized[nlen-1] != '\\') nlen--;
                if (nlen > 0) nlen--; // remove separator
                i += 2;
                if (i < len && (buf[i] == '/' || buf[i] == '\\')) i++;
                continue;
            }
        }
        // Copy component
        while (i < len && buf[i] != '/' && buf[i] != '\\') {
            if (nlen < 4095) normalized[nlen++] = buf[i];
            i++;
        }
        if (i < len && nlen < 4095) normalized[nlen++] = '/';
    }
    if (nlen > 0 && normalized[nlen-1] == '/') nlen--;
    if (nlen == 0) { normalized[nlen++] = '.'; }
    normalized[nlen] = '\0';
    char* result = (char*)pool_alloc((size_t)(nlen + 1));
    if (!result) return ruta;
    memcpy(result, normalized, (size_t)(nlen + 1));
    return (CadenaSegura){ .longitud = nlen, .datos = result };
}

CadenaSegura _syn_obtener_cwd(void) {
    char buf[4096];
#ifdef _WIN32
    DWORD len = GetCurrentDirectoryA(4096, buf);
#else
    char* _cwd = getcwd(buf, 4096);
    int len = _cwd ? (int)strlen(buf) : 0;
#endif
    if (len == 0 || len >= 4096) {
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(result, buf, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = (int)len, .datos = result };
}

int _syn_ruta_en_directorio(CadenaSegura ruta, CadenaSegura dir) {
    if (ruta.longitud < dir.longitud) return 0;
    return memcmp(ruta.datos, dir.datos, (size_t)dir.longitud) == 0;
}


