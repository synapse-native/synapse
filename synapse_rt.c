// synapse_rt.c — Synapse runtime (modular: types, memory, concurrency)
// Compilar: gcc -c synapse_rt.c -o synapse_rt.o
// Linkear con: synapse_rt_memory.o synapse_rt_concurrency.o

#include "synapse_rt_types.h"
#include "runtime/core/tensor.h"  // D-9(d): std.math/std.tensor/std.simd extraidos a tensor.c
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
#include "axon/tweetnacl.h"

// --- SHA-256 (sin cambios) ---
// ============================================================

#define SHA256_BLOCK_SIZE 64
#define SHA256_DIGEST_SIZE 32

typedef struct {
    uint32_t state[8];
    uint64_t bitcount;
    uint8_t buffer[SHA256_BLOCK_SIZE];
    uint32_t buffer_len;
} SHA256_CTX;

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

static void sha256_init(SHA256_CTX* ctx) {
    ctx->state[0] = 0x6a09e667; ctx->state[1] = 0xbb67ae85;
    ctx->state[2] = 0x3c6ef372; ctx->state[3] = 0xa54ff53a;
    ctx->state[4] = 0x510e527f; ctx->state[5] = 0x9b05688c;
    ctx->state[6] = 0x1f83d9ab; ctx->state[7] = 0x5be0cd19;
    ctx->bitcount = 0;
    ctx->buffer_len = 0;
}

static void sha256_update(SHA256_CTX* ctx, const uint8_t* data, size_t len) {
    for (size_t i = 0; i < len; i++) {
        ctx->buffer[ctx->buffer_len++] = data[i];
        ctx->bitcount += 8;
        if (ctx->buffer_len == SHA256_BLOCK_SIZE) {
            sha256_transform(ctx, ctx->buffer);
            ctx->buffer_len = 0;
        }
    }
}

static void sha256_final(SHA256_CTX* ctx, uint8_t* digest) {
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
// Debug / Trace System — Time-Travel Debugging Support
// ============================================================

#define TRACE_MAX_EVENTS 50000
#define TRACE_DIR ".synapse/traces"

typedef enum {
    EVENT_ASSIGNMENT = 0,
    EVENT_FN_CALL = 1,
    EVENT_FN_RETURN = 2,
    EVENT_ERROR = 3,
    EVENT_BRANCH_TAKEN = 4,
    EVENT_LOOP_ITERATION = 5,
    EVENT_VARIABLE_CHANGE = 6,
    EVENT_CONTRACT_CHECK = 7,
    EVENT_USER_TRACE = 8
} TraceEventTag;

typedef struct {
    int tag;
    long long timestamp;
    const char* funcion;
    const char* archivo;
    int linea;
    long long valor_entero;
    double valor_decimal;
    const char* valor_texto;
    const char* variable;
} TraceEvent;

typedef struct {
    char id[64];
    char programa[256];
    TraceEvent* eventos;
    int total_eventos;
    int capacidad;
    int cabeza;
    int estado;  // 0=ACTIVA, 1=FINALIZADA, 2=PERSISTIDA
} TraceSession;

static TraceSession g_trace_session = {0};
static int g_trace_initialized = 0;

long long _get_timestamp_ns(void) {
#ifdef _WIN32
    FILETIME ft;
    GetSystemTimeAsFileTime(&ft);
    ULARGE_INTEGER ul;
    ul.LowPart = ft.dwLowDateTime;
    ul.HighPart = ft.dwHighDateTime;
    return (long long)(ul.QuadPart / 10) - 116444736000000000LL;
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
#endif
}

static const char* _syn_home_dir(void) {
    const char* h = getenv("HOME");
#ifdef _WIN32
    if (h == NULL || h[0] == '\0') h = getenv("USERPROFILE");
#endif
    return (h != NULL && h[0] != '\0') ? h : ".";
}

static void _ensure_trace_dir(void) {
    // ME-R2: la traza se persiste en ~/.synapse/traces (API documentada en
    // std.debug y verificada por tests/unit/test_debug.py); antes se usaba
    // ".synapse/traces" relativo al CWD -> el archivo nunca aparecia en el
    // home del usuario y el test nunca encontraba el .trace.
    char buf[1024];
    const char* home = _syn_home_dir();
    snprintf(buf, sizeof(buf), "%s/.synapse", home);
#ifdef _WIN32
    _mkdir(buf);
#else
    mkdir(buf, 0755);
#endif
    snprintf(buf, sizeof(buf), "%s/%s", home, TRACE_DIR);
#ifdef _WIN32
    _mkdir(buf);
#else
    mkdir(buf, 0755);
#endif
}

static char* _generate_trace_id(void) {
    static char id[64];
    long long ts = _get_timestamp_ns();
    snprintf(id, sizeof(id), "trace_%lld_%d", ts, rand() % 10000);
    return id;
}

static void _init_trace_session(const char* programa) {
    if (g_trace_initialized) return;
    
    _ensure_trace_dir();
    
    g_trace_session.eventos = (TraceEvent*)calloc(TRACE_MAX_EVENTS, sizeof(TraceEvent));
    if (!g_trace_session.eventos) {
        fprintf(stderr, "[Debug] ERROR: No se pudo asignar buffer de traza\n");
        return;
    }
    g_trace_session.capacidad = TRACE_MAX_EVENTS;
    g_trace_session.cabeza = 0;
    g_trace_session.total_eventos = 0;
    g_trace_session.estado = 0;
    
    strncpy(g_trace_session.id, _generate_trace_id(), sizeof(g_trace_session.id)-1);
    strncpy(g_trace_session.programa, programa ? programa : "desconocido", sizeof(g_trace_session.programa)-1);
    
    g_trace_initialized = 1;
    fprintf(stderr, "[Debug] Sesion iniciada: %s (%s)\n", g_trace_session.id, g_trace_session.programa);
}

CadenaSegura _syn_debug_iniciar_sesion(CadenaSegura programa) {
    _init_trace_session(programa.datos ? programa.datos : "");
    
    CadenaSegura id;
    id.longitud = (int)strlen(g_trace_session.id);
    id.datos = g_trace_session.id;
    return id;
}

int _syn_debug_registrar_evento(int tag, const char* funcion, const char* archivo, int linea, 
                                 const char* variable, long long valor_entero, double valor_decimal, const char* valor_texto) {
    if (!g_trace_initialized) {
        _init_trace_session("desconocido");
    }
    if (!g_trace_session.eventos) return -1;
    
    int idx = g_trace_session.cabeza % TRACE_MAX_EVENTS;
    TraceEvent* e = &g_trace_session.eventos[idx];
    
    e->tag = tag;
    e->timestamp = _get_timestamp_ns();
    e->funcion = funcion ? funcion : "";
    e->archivo = archivo ? archivo : "";
    e->linea = linea;
    e->valor_entero = valor_entero;
    e->valor_decimal = valor_decimal;
    e->valor_texto = valor_texto ? valor_texto : "";
    e->variable = variable ? variable : "";
    
    g_trace_session.cabeza = (g_trace_session.cabeza + 1) % TRACE_MAX_EVENTS;
    if (g_trace_session.total_eventos < TRACE_MAX_EVENTS) {
        g_trace_session.total_eventos++;
    }
    
    return 0;
}

int _syn_debug_trace(const char* expresion_texto, void* valor, const char* tipo) {
    // Registrar evento de traza de usuario
    if (!g_trace_initialized) {
        _init_trace_session("desconocido");
    }
    return _syn_debug_registrar_evento(EVENT_USER_TRACE, "trace", "", 0, 
                                        expresion_texto ? expresion_texto : "expr", 
                                        0, 0.0, "");
}

CadenaSegura _syn_debug_finalizar_sesion(void) {
    if (!g_trace_initialized) {
        CadenaSegura vacia = {0, ""};
        return vacia;
    }
    
    if (g_trace_session.estado != 0) {
        CadenaSegura id = {(int)strlen(g_trace_session.id), g_trace_session.id};
        return id;
    }
    
    _ensure_trace_dir();
    
    char filepath[512];
    snprintf(filepath, sizeof(filepath), "%s/%s/%s.trace", _syn_home_dir(), TRACE_DIR, g_trace_session.id);
    
    FILE* f = fopen(filepath, "wb");
    if (!f) {
        fprintf(stderr, "[Debug] ERROR: No se pudo escribir traza: %s\n", filepath);
        CadenaSegura id = {(int)strlen(g_trace_session.id), g_trace_session.id};
        return id;
    }
    
    // Escribir header
    fprintf(f, "TRACE v1\n");
    fprintf(f, "id=%s\n", g_trace_session.id);
    fprintf(f, "programa=%s\n", g_trace_session.programa);
    fprintf(f, "eventos=%d\n", g_trace_session.total_eventos);
    fprintf(f, "capacidad=%d\n", TRACE_MAX_EVENTS);
    fprintf(f, "---\n");
    
    // Escribir eventos en orden cronologico (desde el mas antiguo)
    int inicio = (g_trace_session.total_eventos < TRACE_MAX_EVENTS) ? 0 : 
                 (g_trace_session.cabeza % TRACE_MAX_EVENTS);
    int count = g_trace_session.total_eventos;
    
    for (int i = 0; i < count; i++) {
        int idx = (inicio + i) % TRACE_MAX_EVENTS;
        TraceEvent* e = &g_trace_session.eventos[idx];
        
        fprintf(f, "%d|%lld|%s|%s|%d|%lld|%f|%s|%s\n",
            e->tag,
            e->timestamp,
            e->funcion,
            e->archivo,
            e->linea,
            e->valor_entero,
            e->valor_decimal,
            e->valor_texto ? e->valor_texto : "",
            e->variable ? e->variable : "");
    }
    
    fclose(f);
    
    g_trace_session.estado = 2;  // PERSISTIDA
    
    fprintf(stderr, "[Debug] Traza guardada: %s (%d eventos)\n", filepath, count);
    
    CadenaSegura id;
    id.longitud = (int)strlen(g_trace_session.id);
    id.datos = g_trace_session.id;
    return id;
}

TraceSession _syn_debug_obtener_sesion(void) {
    return g_trace_session;
}

// ============================================================
// M8.1 — std.cluster — Transport Layer for Distributed Nodes
// UDP-based messaging with Ed25519 authentication
// ============================================================

// --- Ed25519 Key Generation (via TweetNaCl) ---
// Generates a new Ed25519 key pair.
// Returns colon-separated "public_key_hex:private_key_hex"
CadenaSegura cluster_generar_par_claves(void) {
    unsigned char pk[32], sk[64];
    if (crypto_sign_keypair(pk, sk) != 0) {
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
    char hex_pk[65], hex_sk[129];
    for (int i = 0; i < 32; i++)
        sprintf(hex_pk + i * 2, "%02x", pk[i]);
    hex_pk[64] = '\0';
    for (int i = 0; i < 64; i++)
        sprintf(hex_sk + i * 2, "%02x", sk[i]);
    hex_sk[128] = '\0';
    int total_len = 64 + 1 + 128;
    char* result = (char*)pool_alloc((size_t)(total_len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = "" };
    sprintf(result, "%s:%s", hex_pk, hex_sk);
    return (CadenaSegura){ .longitud = total_len, .datos = result };
}

// --- Ed25519 Signing ---
// clave_privada_hex can be the full "pubkey:privkey" string or just "privkey" (128 chars)
CadenaSegura cluster_firmar_mensaje(CadenaSegura mensaje, CadenaSegura clave_privada_hex) {
    const char* key_start = clave_privada_hex.datos;
    int key_len = clave_privada_hex.longitud;
    // If full par string "pubkey:privkey", skip past pubkey and ':'
    if (key_len == 193) { // 64 + 1 + 128
        key_start += 65;
        key_len = 128;
    }
    if (key_len < 128)
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    unsigned char sk[64];
    for (int i = 0; i < 64; i++) {
        unsigned int byte;
        sscanf(key_start + i * 2, "%02x", &byte);
        sk[i] = (unsigned char)byte;
    }
    unsigned char sm[2048];
    unsigned long long smlen;
    if (crypto_sign(sm, &smlen, (const unsigned char*)mensaje.datos,
                    (unsigned long long)mensaje.longitud, sk) != 0)
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    char hex_sig[129];
    for (int i = 0; i < 64; i++)
        sprintf(hex_sig + i * 2, "%02x", sm[i]);
    hex_sig[128] = '\0';
    char* result = (char*)pool_alloc(129);
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(result, hex_sig, 129);
    return (CadenaSegura){ .longitud = 128, .datos = result };
}

// --- Ed25519 Signature Verification ---
int cluster_verificar_firma(CadenaSegura mensaje, CadenaSegura firma_hex,
                             CadenaSegura clave_publica_hex) {
    const char* pk_start = clave_publica_hex.datos;
    int pk_len = clave_publica_hex.longitud;
    // If full par string "pubkey:privkey", only use pubkey part
    if (pk_len == 193) pk_len = 64;
    if (firma_hex.longitud < 128 || pk_len < 64) return -1;
    unsigned char firma[64], pk[32];
    for (int i = 0; i < 64; i++) {
        unsigned int byte;
        sscanf(firma_hex.datos + i * 2, "%02x", &byte);
        firma[i] = (unsigned char)byte;
    }
    for (int i = 0; i < 32; i++) {
        unsigned int byte;
        sscanf(pk_start + i * 2, "%02x", &byte);
        pk[i] = (unsigned char)byte;
    }
    unsigned long long mlen = 0;
    unsigned char* sm = (unsigned char*)malloc((size_t)(mensaje.longitud + 64));
    if (!sm) return -1;
    memcpy(sm, firma, 64);
    memcpy(sm + 64, mensaje.datos, (size_t)mensaje.longitud);
    unsigned char* m_buf = (unsigned char*)malloc((size_t)(mensaje.longitud + 64));
    if (!m_buf) { free(sm); return -1; }
    int rc = crypto_sign_open(m_buf, &mlen, sm, (unsigned long long)(mensaje.longitud + 64), pk);
    free(sm);
    free(m_buf);
    return rc;
}

// --- UDP Socket Helpers ---
static int _cluster_udp_socket(int puerto) {
    int fd = (int)socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) return -1;
    int opt = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)puerto);
    addr.sin_addr.s_addr = INADDR_ANY;
    if (bind(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
#ifdef _WIN32
        closesocket(fd);
#else
        close(fd);
#endif
        return -1;
    }
    return fd;
}

static int _cluster_udp_enviar(int fd, const char* ip, int puerto,
                                const char* datos, int lon) {
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)puerto);
    addr.sin_addr.s_addr = inet_addr(ip);
    if (addr.sin_addr.s_addr == INADDR_NONE) return -1;
    return (int)sendto(fd, datos, (size_t)lon, 0,
                       (struct sockaddr*)&addr, sizeof(addr));
}

// --- Cluster Initialization ---
static int _cluster_sock_global = -1;

int cluster_iniciar_nodo(int puerto) {
    _syn_iniciar_red();
    int fd = _cluster_udp_socket(puerto);
    if (fd < 0) return -1;
    _cluster_sock_global = fd;
    return 0;
}

int cluster_detener_nodo(void) {
    if (_cluster_sock_global >= 0) {
#ifdef _WIN32
        closesocket(_cluster_sock_global);
#else
        close(_cluster_sock_global);
#endif
    }
    _cluster_sock_global = -1;
    return 0;
}

// --- Send HELLO handshake message ---
int cluster_enviar_hello(const char* ip, int puerto,
                          CadenaSegura id_origen, CadenaSegura pubkey_hex) {
    if (_cluster_sock_global < 0) return -1;
    char buf[1024];
    int len = snprintf(buf, sizeof(buf), "HELLO:%.*s:%.*s",
                       (int)id_origen.longitud, id_origen.datos,
                       (int)pubkey_hex.longitud, pubkey_hex.datos);
    return _cluster_udp_enviar(_cluster_sock_global, ip, puerto, buf, len);
}

// --- Remote Channel: send data ---
int cluster_canal_remoto_enviar(const char* ip, int puerto,
                                const char* datos, int lon,
                                int chan_id) {
    if (_cluster_sock_global < 0) return -1;
    char header[64];
    static int seq_counter = 0;
    int hdr_len = snprintf(header, sizeof(header), "DATA:%d:%d:", chan_id, seq_counter++);
    char* paquete = (char*)pool_alloc((size_t)(hdr_len + lon));
    if (!paquete) return -1;
    memcpy(paquete, header, (size_t)hdr_len);
    memcpy(paquete + hdr_len, datos, (size_t)lon);
    int n = _cluster_udp_enviar(_cluster_sock_global, ip, puerto,
                                 paquete, hdr_len + lon);
    pool_free(paquete);
    return n;
}

// --- Receive a datagram (non-blocking) ---
CadenaSegura cluster_recibir_paquete(int timeout_ms) {
    if (_cluster_sock_global < 0) return (CadenaSegura){ .longitud = 0, .datos = "" };
#ifdef _WIN32
    u_long mode = 1;
    ioctlsocket(_cluster_sock_global, FIONBIO, &mode);
#else
    int flags = fcntl(_cluster_sock_global, F_GETFL, 0);
    fcntl(_cluster_sock_global, F_SETFL, flags | O_NONBLOCK);
#endif
    char buf[65536];
    struct sockaddr_in from;
    socklen_t fromlen = sizeof(from);
    int n = (int)recvfrom(_cluster_sock_global, buf, sizeof(buf) - 1, 0,
                           (struct sockaddr*)&from, &fromlen);
    if (n <= 0) return (CadenaSegura){ .longitud = 0, .datos = "" };
    buf[n] = '\0';
    char* result = (char*)pool_alloc((size_t)(n + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(result, buf, (size_t)(n + 1));
    return (CadenaSegura){ .longitud = n, .datos = result };
}

// ============================================================
// M8.2 — Distributed Work-Stealing Scheduler
// Lock-free-ish distributed task scheduler using local queues
// and UDP-based stealing protocol (STEAL/STOLEN messages).
// Each node maintains a local deque protected by a pthread mutex.
// ============================================================

// --- Work queue entry ---
typedef struct {
    int id;
    char* datos;
    int len;
} WsTarea;

// --- Work queue state ---
static WsTarea* _ws_cola = NULL;
static int _ws_capacidad = 0;
static int _ws_cabeza = 0;  // pop from front (stealing)
static int _ws_cola_idx = 0; // push to back (local)
static int _ws_contador = 0;
static pthread_mutex_t _ws_mutex = PTHREAD_MUTEX_INITIALIZER;
static int _ws_robo_seq = 0;
static int _ws_ultimo_robo_seq = -1;

// --- Stolen task buffer (for receiving stolen tasks) ---
static WsTarea _ws_robada = {0, NULL, 0};
static int _ws_robada_valida = 0;

int ws_inicializar(int capacidad) {
    if (capacidad <= 0) capacidad = 1024;
    if (_ws_cola) {
        free(_ws_cola);
        _ws_cola = NULL;
    }
    _ws_cola = (WsTarea*)malloc((size_t)capacidad * sizeof(WsTarea));
    if (!_ws_cola) return -1;
    memset(_ws_cola, 0, (size_t)capacidad * sizeof(WsTarea));
    _ws_capacidad = capacidad;
    _ws_cabeza = 0;
    _ws_cola_idx = 0;
    _ws_contador = 0;
    _ws_robo_seq = 0;
    _ws_ultimo_robo_seq = -1;
    _ws_robada_valida = 0;
    return 0;
}

int ws_encolar(int id, CadenaSegura datos) {
    pthread_mutex_lock(&_ws_mutex);
    if (_ws_contador >= _ws_capacidad) {
        pthread_mutex_unlock(&_ws_mutex);
        return -1;
    }
    char* copia = (char*)malloc((size_t)(datos.longitud + 1));
    if (!copia) { pthread_mutex_unlock(&_ws_mutex); return -1; }
    memcpy(copia, datos.datos, (size_t)datos.longitud);
    copia[datos.longitud] = '\0';
    _ws_cola[_ws_cola_idx].id = id;
    _ws_cola[_ws_cola_idx].datos = copia;
    _ws_cola[_ws_cola_idx].len = datos.longitud;
    _ws_cola_idx = (_ws_cola_idx + 1) % _ws_capacidad;
    _ws_contador++;
    pthread_mutex_unlock(&_ws_mutex);
    return 0;
}

CadenaSegura ws_desencolar(void) {
    pthread_mutex_lock(&_ws_mutex);
    if (_ws_contador <= 0) {
        pthread_mutex_unlock(&_ws_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
    // Pop from back (LIFO) for local worker — better cache locality
    int idx = (_ws_cola_idx - 1 + _ws_capacidad) % _ws_capacidad;
    // But if only 1 item, pop from front
    if (_ws_contador == 1) idx = _ws_cabeza;
    WsTarea t = _ws_cola[idx];
    _ws_cola[idx].datos = NULL;
    // Recalculate indices
    if (_ws_contador == 1) {
        _ws_cabeza = 0;
        _ws_cola_idx = 0;
    } else if (idx == _ws_cabeza) {
        _ws_cabeza = (_ws_cabeza + 1) % _ws_capacidad;
    } else {
        _ws_cola_idx = (_ws_cola_idx - 1 + _ws_capacidad) % _ws_capacidad;
    }
    _ws_contador--;
    pthread_mutex_unlock(&_ws_mutex);
    // Build result string "id:datos"
    char id_str[32];
    int id_len = snprintf(id_str, sizeof(id_str), "%d:", t.id);
    int total_len = id_len + t.len;
    char* buf = (char*)pool_alloc((size_t)(total_len + 1));
    if (!buf) { free(t.datos); return (CadenaSegura){ .longitud = 0, .datos = "" }; }
    memcpy(buf, id_str, (size_t)id_len);
    memcpy(buf + id_len, t.datos, (size_t)t.len);
    buf[total_len] = '\0';
    free(t.datos);
    return (CadenaSegura){ .longitud = total_len, .datos = buf };
}

int ws_profundidad(void) {
    pthread_mutex_lock(&_ws_mutex);
    int n = _ws_contador;
    pthread_mutex_unlock(&_ws_mutex);
    return n;
}

int ws_carga_estimada(void) {
    pthread_mutex_lock(&_ws_mutex);
    int pct = (_ws_capacidad > 0) ? (_ws_contador * 100 / _ws_capacidad) : 0;
    if (pct > 100) pct = 100;
    pthread_mutex_unlock(&_ws_mutex);
    return pct;
}

// --- Steal from front (for stealing by remote nodes) ---
// Called by the responder: removes task from front and returns it.
// The caller must format the response message.
static int _ws_robar_frontal(int* out_id, char** out_data, int* out_len) {
    pthread_mutex_lock(&_ws_mutex);
    if (_ws_contador <= 0) {
        pthread_mutex_unlock(&_ws_mutex);
        return -1;
    }
    WsTarea t = _ws_cola[_ws_cabeza];
    _ws_cola[_ws_cabeza].datos = NULL;
    _ws_cabeza = (_ws_cabeza + 1) % _ws_capacidad;
    _ws_contador--;
    pthread_mutex_unlock(&_ws_mutex);
    *out_id = t.id;
    *out_data = t.datos;
    *out_len = t.len;
    return 0;
}

// --- Send steal request to a remote node ---
// Format: "WSTEAL:<seq>"
int ws_enviar_solicitud_robo(CadenaSegura ip, int puerto) {
    if (_cluster_sock_global < 0) return -1;
    int seq = __atomic_fetch_add(&_ws_robo_seq, 1, __ATOMIC_SEQ_CST);
    _ws_ultimo_robo_seq = seq;
    char buf[64];
    int len = snprintf(buf, sizeof(buf), "WSTEAL:%d", seq);
    const char* ip_str = ip.datos;
    int puerto_int = puerto;
    return _cluster_udp_enviar(_cluster_sock_global, ip_str, puerto_int, buf, len);
}

// --- Process incoming message for work-stealing protocol ---
// Returns structured text:
//   "ROBADA:id:data" — a stolen task was received (the caller's steal was answered)
//   "ATENDIDO" — a WSTEAL request was handled (stolen task sent back)
//   "VACIA" — a WSTEAL request came but local queue was empty
//   original data — pass-through for non-steal messages
CadenaSegura ws_procesar_mensaje(CadenaSegura paquete) {
    if (paquete.longitud < 7) return paquete;
    const char* p = paquete.datos;
    int plen = paquete.longitud;

    // Check for "WSTEAL:" prefix (incoming steal request)
    if (plen >= 7 && memcmp(p, "WSTEAL:", 7) == 0) {
        // Responder: dequeue from front and send back as "WSTOLEN:<seq>:<id>:<data>"
        int seq = 0;
        sscanf(p + 7, "%d", &seq);
        int task_id;
        char* task_data;
        int task_len;
        if (_ws_robar_frontal(&task_id, &task_data, &task_len) != 0) {
            // Queue empty — send "WNONE:<seq>"
            char resp[64];
            int rlen = snprintf(resp, sizeof(resp), "WNONE:%d", seq);
            (void)rlen;
            // We need to know who sent it. Since we don't track sender addr,
            // we can't respond. The requester will timeout.
            // For now, just store that we were empty.
            return (CadenaSegura){ .longitud = 5, .datos = "VACIA" };
        }
        // Build response: "WSTOLEN:<seq>:<id>:<data>"
        char hdr[64];
        int hdr_len = snprintf(hdr, sizeof(hdr), "WSTOLEN:%d:%d:", seq, task_id);
        int total = hdr_len + task_len;
        char* resp = (char*)pool_alloc((size_t)(total + 1));
        if (!resp) { free(task_data); return (CadenaSegura){ .longitud = 0, .datos = "" }; }
        memcpy(resp, hdr, (size_t)hdr_len);
        memcpy(resp + hdr_len, task_data, (size_t)task_len);
        resp[total] = '\0';
        free(task_data);
        // In a real scenario, we'd send this back to the requester.
        // For the simulation test, we return it as "ATENDIDO" + the response data
        // to allow the test harness to route it.
        char* result = (char*)pool_alloc((size_t)(total + 10));
        if (!result) return (CadenaSegura){ .longitud = 0, .datos = "" };
        memcpy(result, "ATENDIDO:", 9);
        memcpy(result + 9, resp, (size_t)total);
        result[total + 9] = '\0';
        pool_free(resp);
        return (CadenaSegura){ .longitud = total + 9, .datos = result };
    }

    // Check for "WSTOLEN:" prefix (incoming steal response)
    if (plen >= 8 && memcmp(p, "WSTOLEN:", 8) == 0) {
        // Parse: "WSTOLEN:<seq>:<id>:<data>"
        int seq, task_id;
        int consumed = 0;
        if (sscanf(p + 8, "%d:%d%n", &seq, &task_id, &consumed) >= 2) {
            int data_start = 8 + consumed + 1; // skip past ":<data>"
            if (data_start < plen) {
                int data_len = plen - data_start;
                char* copia = (char*)malloc((size_t)(data_len + 1));
                if (copia) {
                    memcpy(copia, p + data_start, (size_t)data_len);
                    copia[data_len] = '\0';
                    // Store in stolen buffer
                    pthread_mutex_lock(&_ws_mutex);
                    if (_ws_robada.datos) free(_ws_robada.datos);
                    _ws_robada.id = task_id;
                    _ws_robada.datos = copia;
                    _ws_robada.len = data_len;
                    _ws_robada_valida = 1;
                    pthread_mutex_unlock(&_ws_mutex);
                    // Return "ROBADA:id:data"
                    char id_str[32];
                    int id_len = snprintf(id_str, sizeof(id_str), "%d:", task_id);
                    int total = 7 + id_len + data_len; // "ROBADA:" + "id:" + data
                    char* buf = (char*)pool_alloc((size_t)(total + 1));
                    if (buf) {
                        memcpy(buf, "ROBADA:", 7);
                        memcpy(buf + 7, id_str, (size_t)id_len);
                        memcpy(buf + 7 + id_len, copia, (size_t)data_len);
                        buf[total] = '\0';
                        return (CadenaSegura){ .longitud = total, .datos = buf };
                    }
                }
            }
        }
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }

    // Check for "WNONE:" prefix (steal response with no tasks)
    if (plen >= 6 && memcmp(p, "WNONE:", 6) == 0) {
        return (CadenaSegura){ .longitud = 5, .datos = "VACIA" };
    }

    // Not a steal message — pass through
    return paquete;
}

// --- Retrieve the last stolen task ---
// Returns "id:data" or "" if none
CadenaSegura ws_ultima_robada(void) {
    pthread_mutex_lock(&_ws_mutex);
    if (!_ws_robada_valida || !_ws_robada.datos) {
        pthread_mutex_unlock(&_ws_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
    char id_str[32];
    int id_len = snprintf(id_str, sizeof(id_str), "%d:", _ws_robada.id);
    int total = id_len + _ws_robada.len;
    char* buf = (char*)pool_alloc((size_t)(total + 1));
    if (!buf) {
        pthread_mutex_unlock(&_ws_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
    memcpy(buf, id_str, (size_t)id_len);
    memcpy(buf + id_len, _ws_robada.datos, (size_t)_ws_robada.len);
    buf[total] = '\0';
    pthread_mutex_unlock(&_ws_mutex);
    return (CadenaSegura){ .longitud = total, .datos = buf };
}

// --- Manually forward a WSTEAL response to the requester ---
// Used in simulation: the test harness routes ATENDIDO responses back.
int ws_reenviar_respuesta(CadenaSegura ip, int puerto, CadenaSegura respuesta) {
    if (_cluster_sock_global < 0 || respuesta.longitud <= 0) return -1;
    return _cluster_udp_enviar(_cluster_sock_global, ip.datos, puerto,
                                respuesta.datos, respuesta.longitud);
}

// ============================================================
// M8.3 — Raft Consensus Algorithm for Shared State
// Simplified Raft implementation:
//   - Leader election with randomized timeouts
//   - Term-based voting
//   - Heartbeat mechanism (AppendEntries)
//   - Log replication tracking
// Supports multi-node simulation via node_id-indexed state array.
// ============================================================

#define RAFT_FOLLOWER  0
#define RAFT_CANDIDATE 1
#define RAFT_LEADER    2

#define MAX_RAFT_NODES 8
#define RAFT_HEARTBEAT_MS 50
#define RAFT_ELECTION_MIN_MS 150
#define RAFT_ELECTION_MAX_MS 300

typedef struct {
    int current_term;
    int voted_for;
    int state;
    int node_id;
    int num_nodes;
    long long election_deadline_ns;
    long long next_heartbeat_ns;
    int leader_id;
    int log_count;
    int last_log_index;   // Raft: index of last log entry
    int last_log_term;    // Raft: term of last log entry
    int commit_index;
    int last_applied;
    int votes_granted;
    int votes_needed;
    unsigned int seed;
    // Ed25519 signing keypair for Raft RPC authentication
    char clave_publica_hex[65];   // 32 bytes -> 64 hex chars + null
    char clave_privada_hex[65];   // 32 bytes -> 64 hex chars + null
} RaftNode;

static RaftNode _raft_nodes[MAX_RAFT_NODES];
static int _raft_inicializado = 0;
// static int _raft_simulation_mode = 0;

static long long _raft_now_ns(void) {
    return _get_timestamp_ns();
}

static int _raft_rand_range(RaftNode* n, int min, int max) {
    n->seed = n->seed * 1103515245u + 12345u;
    return min + (int)((n->seed >> 16) % (unsigned int)(max - min + 1));
}

static RaftNode* _raft_get(int node_id) {
    if (node_id < 0 || node_id >= MAX_RAFT_NODES) return NULL;
    return &_raft_nodes[node_id];
}

int raft_inicializar(int node_id, int num_nodes, int seed) {
    if (node_id < 0 || node_id >= MAX_RAFT_NODES) return -1;
    if (num_nodes < 1 || num_nodes > MAX_RAFT_NODES) return -1;
    RaftNode* n = &_raft_nodes[node_id];
    n->current_term = 0;
    n->voted_for = -1;
    n->state = RAFT_FOLLOWER;
    n->node_id = node_id;
    n->num_nodes = num_nodes;
    n->election_deadline_ns = 0;
    n->next_heartbeat_ns = 0;
    n->leader_id = -1;
    n->log_count = 0;
    n->last_log_index = 0;
    n->last_log_term = 0;
    n->commit_index = 0;
    n->last_applied = 0;
    n->votes_granted = 0;
    n->votes_needed = num_nodes / 2 + 1;
    n->seed = (unsigned int)(seed ^ node_id);
    // Generate Ed25519 keypair for Raft RPC authentication
    {
        unsigned char pk[32], sk[64];
        crypto_sign_keypair(pk, sk);
        for (int i = 0; i < 32; i++) {
            snprintf(n->clave_publica_hex + i * 2, 3, "%02x", pk[i]);
            snprintf(n->clave_privada_hex + i * 2, 3, "%02x", sk[i]);
        }
        n->clave_publica_hex[64] = '\0';
        n->clave_privada_hex[64] = '\0';
    }
    _raft_inicializado = 1;
    return 0;
}

int raft_iniciar(long long tiempo_actual_ns, int node_id) {
    RaftNode* n = _raft_get(node_id);
    if (!n) return -1;
    n->state = RAFT_FOLLOWER;
    n->leader_id = -1;
    n->voted_for = -1;
    int timeout = _raft_rand_range(n, RAFT_ELECTION_MIN_MS, RAFT_ELECTION_MAX_MS);
    n->election_deadline_ns = tiempo_actual_ns + (long long)timeout * 1000000LL;
    n->next_heartbeat_ns = 0;
    return 0;
}

int raft_estado(int node_id) {
    RaftNode* n = _raft_get(node_id);
    return n ? n->state : -1;
}

int raft_term_actual(int node_id) {
    RaftNode* n = _raft_get(node_id);
    return n ? n->current_term : -1;
}

int raft_lider_actual(int node_id) {
    RaftNode* n = _raft_get(node_id);
    return n ? n->leader_id : -1;
}

int raft_log_entradas(int node_id) {
    RaftNode* n = _raft_get(node_id);
    return n ? n->log_count : -1;
}

int raft_commit_index(int node_id) {
    RaftNode* n = _raft_get(node_id);
    return n ? n->commit_index : -1;
}

// --- Start election (called by follower/candidate on timeout) ---
static void _raft_iniciar_eleccion(RaftNode* n, long long now_ns) {
    n->current_term++;
    n->state = RAFT_CANDIDATE;
    n->voted_for = n->node_id;
    n->votes_granted = 1;  // vote for self
    n->leader_id = -1;

    // Reset election timeout for this node
    int timeout = _raft_rand_range(n, RAFT_ELECTION_MIN_MS, RAFT_ELECTION_MAX_MS);
    n->election_deadline_ns = now_ns + (long long)timeout * 1000000LL;

    // In simulation mode: send RequestVote to all other nodes
    // (handled by the test harness calling raft_procesar_solicitud_voto)
}

// --- Ed25519 signing for Raft RPC messages ---
// Signs a Raft message with the node's Ed25519 private key.
// msg: the raw message bytes (e.g., "RVOTE:<term>:<id>:<log_idx>:<log_term>")
// firma_out: output buffer for 64-byte hex signature (128 chars + null)
// Returns: 0 on success, -1 on error
int raft_firmar_mensaje(int node_id, const char* msg, int msg_len,
                         char* firma_out) {
    RaftNode* n = _raft_get(node_id);
    if (!n || !msg || !firma_out || msg_len <= 0) return -1;

    // Decode private key from hex
    unsigned char sk[64];
    for (int i = 0; i < 64; i++) {
        unsigned int byte;
        sscanf(n->clave_privada_hex + i * 2, "%02x", &byte);
        sk[i] = (unsigned char)byte;
    }

    // Sign: crypto_sign returns signature || message
    unsigned long long smlen = 0;
    unsigned char* sm = (unsigned char*)malloc((size_t)(msg_len + 64));
    if (!sm) return -1;
    crypto_sign(sm, &smlen, (const unsigned char*)msg,
                (unsigned long long)msg_len, sk);

    // Extract first 64 bytes (signature) and encode to hex
    for (int i = 0; i < 64; i++) {
        snprintf(firma_out + i * 2, 3, "%02x", sm[i]);
    }
    firma_out[128] = '\0';
    free(sm);
    return 0;
}

// Verifies an Ed25519 signature on a Raft message.
// msg: the raw message bytes
// firma_hex: 128-char hex signature
// pk_hex: 64-char hex public key
// Returns: 0 if valid, -1 if invalid
int raft_verificar_firma_rpc(const char* msg, int msg_len,
                              const char* firma_hex, const char* pk_hex) {
    if (!msg || !firma_hex || !pk_hex || msg_len <= 0) return -1;
    if (strlen(firma_hex) < 128 || strlen(pk_hex) < 64) return -1;

    // Decode signature and public key
    unsigned char sig[64], pk[32];
    for (int i = 0; i < 64; i++) {
        unsigned int byte;
        sscanf(firma_hex + i * 2, "%02x", &byte);
        sig[i] = (unsigned char)byte;
    }
    for (int i = 0; i < 32; i++) {
        unsigned int byte;
        sscanf(pk_hex + i * 2, "%02x", &byte);
        pk[i] = (unsigned char)byte;
    }

    // Build signed message: signature || original message
    unsigned long long smlen = (unsigned long long)(msg_len + 64);
    unsigned char* sm = (unsigned char*)malloc(smlen);
    if (!sm) return -1;
    memcpy(sm, sig, 64);
    memcpy(sm + 64, msg, (size_t)msg_len);

    // Verify
    unsigned char* mout = (unsigned char*)malloc(smlen);
    if (!mout) { free(sm); return -1; }
    unsigned long long mlen = 0;
    int rc = crypto_sign_open(mout, &mlen, sm, smlen, pk);
    free(sm);
    free(mout);
    return rc;  // 0 = valid, -1 = invalid
}

// --- Process a RequestVote message ---
// msg format: "RVOTE:<term>:<candidate_id>:<last_log_idx>:<last_log_term>"
// Returns: 1=voted, 0=denied, -1=error
int raft_procesar_solicitud_voto(int voter_id, int candidate_term,
                                  int candidate_id, int candidate_last_log,
                                  int candidate_last_log_term) {
    RaftNode* n = _raft_get(voter_id);
    if (!n) return -1;

    // If candidate term < current term, deny
    if (candidate_term < n->current_term) return 0;

    // If candidate term > current term, step down and update
    if (candidate_term > n->current_term) {
        n->current_term = candidate_term;
        n->state = RAFT_FOLLOWER;
        n->voted_for = -1;
        n->leader_id = -1;
    }

    // If already voted in this term, deny
    if (n->voted_for != -1 && n->voted_for != candidate_id) return 0;

    // Raft safety: Log Comparison
    // A candidate must have a log at least as up-to-date as the voter's log.
    // Compare last_log_term first; if equal, compare last_log_index.
    if (candidate_last_log_term < n->last_log_term) return 0;
    if (candidate_last_log_term == n->last_log_term &&
        candidate_last_log < n->last_log_index) return 0;

    // Grant vote
    n->voted_for = candidate_id;
    long long now = _raft_now_ns();
    int timeout = _raft_rand_range(n, RAFT_ELECTION_MIN_MS, RAFT_ELECTION_MAX_MS);
    n->election_deadline_ns = now + (long long)timeout * 1000000LL;
    return 1;
}

// --- Process a RequestVote response ---
// msg format: "RVOTED:<term>:<voter_id>:<granted>"
// Returns: 1=leader elected, 0=still candidate, -1=error
int raft_procesar_respuesta_voto(int candidate_id, int responder_term,
                                  int responder_id, int granted) {
    RaftNode* n = _raft_get(candidate_id);
    if (!n || n->state != RAFT_CANDIDATE) return -1;

    // Ignore stale responses
    if (responder_term != n->current_term) return 0;

    if (granted) {
        n->votes_granted++;
        if (n->votes_granted >= n->votes_needed) {
            // Become leader
            n->state = RAFT_LEADER;
            n->leader_id = n->node_id;
            long long now = _raft_now_ns();
            n->next_heartbeat_ns = now;
            return 1;  // leader elected
        }
    }
    return 0;
}

// --- Process a heartbeat / AppendEntries from leader ---
// msg format: "RHB:<term>:<leader_id>:<leader_commit>"
// Returns: 1=accepted, 0=rejected (stale term), -1=error
int raft_procesar_heartbeat(int follower_id, int leader_term,
                             int leader_id, int leader_commit) {
    RaftNode* n = _raft_get(follower_id);
    if (!n) return -1;

    // Reject stale term
    if (leader_term < n->current_term) return 0;

    // Leader term >= current term: acknowledge
    if (leader_term > n->current_term) {
        n->current_term = leader_term;
        n->state = RAFT_FOLLOWER;
        n->voted_for = -1;
    }

    n->leader_id = leader_id;
    n->state = RAFT_FOLLOWER;

    // Update commit index
    if (leader_commit > n->commit_index) {
        n->commit_index = leader_commit;
        if (n->commit_index > n->log_count)
            n->commit_index = n->log_count;
    }

    // Reset election timeout (we have a valid leader)
    long long now = _raft_now_ns();
    int timeout = _raft_rand_range(n, RAFT_ELECTION_MIN_MS, RAFT_ELECTION_MAX_MS);
    n->election_deadline_ns = now + (long long)timeout * 1000000LL;

    return 1;
}

// --- Tick: advance Raft time. Call periodically ---
// Handles election timeouts and heartbeat scheduling.
// Returns: event code — 0=no event, 1=election started, 2=heartbeat sent
int raft_tick(long long tiempo_actual_ns, int node_id) {
    RaftNode* n = _raft_get(node_id);
    if (!n) return -1;

    if (n->state == RAFT_LEADER) {
        // Send heartbeats periodically
        if (tiempo_actual_ns >= n->next_heartbeat_ns) {
            n->next_heartbeat_ns = tiempo_actual_ns + (long long)RAFT_HEARTBEAT_MS * 1000000LL;
            return 2;  // heartbeat due
        }
        return 0;
    }

    // Follower or candidate: check election timeout
    if (tiempo_actual_ns >= n->election_deadline_ns) {
        if (n->state == RAFT_FOLLOWER) {
            _raft_iniciar_eleccion(n, tiempo_actual_ns);
            return 1;  // election started
        } else if (n->state == RAFT_CANDIDATE) {
            // Election timeout: start new election
            _raft_iniciar_eleccion(n, tiempo_actual_ns);
            return 1;  // new election started
        }
    }

    return 0;
}

// --- Force leader to step down (for testing) ---
int raft_forzar_abdicacion(int node_id) {
    RaftNode* n = _raft_get(node_id);
    if (!n || n->state != RAFT_LEADER) return -1;
    n->state = RAFT_FOLLOWER;
    n->leader_id = -1;
    n->voted_for = -1;
    long long now = _raft_now_ns();
    int timeout = _raft_rand_range(n, RAFT_ELECTION_MIN_MS, RAFT_ELECTION_MAX_MS);
    n->election_deadline_ns = now + (long long)timeout * 1000000LL;
    return 0;
}

// --- Append a log entry to the leader (for testing) ---
int raft_agregar_entrada(int node_id) {
    RaftNode* n = _raft_get(node_id);
    if (!n || n->state != RAFT_LEADER) return -1;
    n->log_count++;
    n->last_log_index = n->log_count;
    n->last_log_term = n->current_term;
    return n->log_count;
}

// --- Reset state for a node (for testing) ---
int raft_reiniciar_nodo(int node_id) {
    RaftNode* n = _raft_get(node_id);
    if (!n) return -1;
    return raft_inicializar(node_id, n->num_nodes, (int)(_raft_now_ns() & 0x7FFFFFFF));
}

// --- Get node info string for diagnostics ---
// Returns comma-separated "term,state,leader,log,commit"
CadenaSegura raft_info(int node_id) {
    RaftNode* n = _raft_get(node_id);
    if (!n) return (CadenaSegura){ .longitud = 0, .datos = "" };
    char buf[128];
    int len = snprintf(buf, sizeof(buf), "%d,%d,%d,%d,%d",
                       n->current_term, n->state, n->leader_id,
                       n->log_count, n->commit_index);
    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(result, buf, (size_t)len);
    result[len] = '\0';
    return (CadenaSegura){ .longitud = len, .datos = result };
}

// =========================================================================
// M8.4 — Checkpoint/Restore (Migración de Tareas Live)
// =========================================================================
// Serialización de estado de tareas para migración en caliente entre nodos.
// Formato checkpoint: CKPT:<task_id>:<seq>:<sha256_hex>:<data_len>:<data>
// Checksum: SHA-256 (64-char hex) for cryptographic integrity verification
// =========================================================================

static int _cm_seq = 0;
static int _cm_completadas = 0;
static int _cm_fallidas = 0;
static char _cm_ultimo_resultado[256];

static pthread_mutex_t _cm_mutex = PTHREAD_MUTEX_INITIALIZER;

// --- Compute SHA-256 checksum for checkpoint integrity ---
// Uses the SHA-256 implementation already present in this file.
// Returns first 4 bytes of SHA-256 digest as a 32-bit truncated hash.
static unsigned int _cm_checksum(const char* data, int len) {
    SHA256_CTX ctx;
    uint8_t digest[32];
    sha256_init(&ctx);
    sha256_update(&ctx, (const uint8_t*)data, (size_t)len);
    sha256_final(&ctx, digest);
    // Truncate to 32 bits for checkpoint format compatibility
    return ((unsigned int)digest[0] << 24) | ((unsigned int)digest[1] << 16) |
           ((unsigned int)digest[2] << 8)  | ((unsigned int)digest[3]);
}

// --- Compute full SHA-256 hex hash for checkpoint integrity ---
// Returns 64-char hex string (caller must free if pool_alloc'd).
static void _cm_sha256_hex(const char* data, int len, char* hex_out) {
    SHA256_CTX ctx;
    uint8_t digest[32];
    sha256_init(&ctx);
    sha256_update(&ctx, (const uint8_t*)data, (size_t)len);
    sha256_final(&ctx, digest);
    for (int i = 0; i < 32; i++) {
        snprintf(hex_out + i * 2, 3, "%02x", digest[i]);
    }
    hex_out[64] = '\0';
}

// --- Initialize checkpoint subsystem ---
int cm_inicializar(void) {
    pthread_mutex_lock(&_cm_mutex);
    _cm_seq = 0;
    _cm_completadas = 0;
    _cm_fallidas = 0;
    _cm_ultimo_resultado[0] = '\0';
    pthread_mutex_unlock(&_cm_mutex);
    return 0;
}

// --- Serialize a task into a CKPT checkpoint string ---
// Returns: "CKPT:<id>:<seq>:<sha256_hex>:<data_len>:<data>"
CadenaSegura cm_serializar_checkpoint(int task_id, CadenaSegura datos) {
    if (datos.longitud <= 0 || !datos.datos)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    pthread_mutex_lock(&_cm_mutex);
    int seq = _cm_seq++;
    pthread_mutex_unlock(&_cm_mutex);

    // Full SHA-256 hash for cryptographic integrity
    char sha256_hex[65];
    _cm_sha256_hex(datos.datos, datos.longitud, sha256_hex);

    char header[128];
    int hdr_len = snprintf(header, sizeof(header), "CKPT:%d:%d:%s:%d:",
                           task_id, seq, sha256_hex, datos.longitud);

    int total_len = hdr_len + datos.longitud;
    char* buf = (char*)pool_alloc((size_t)(total_len + 1));
    if (!buf) return (CadenaSegura){ .longitud = 0, .datos = NULL };

    memcpy(buf, header, (size_t)hdr_len);
    memcpy(buf + hdr_len, datos.datos, (size_t)datos.longitud);
    buf[total_len] = '\0';

    return (CadenaSegura){ .longitud = total_len, .datos = buf };
}

// --- Deserialize a CKPT checkpoint string ---
// Parses "CKPT:<id>:<seq>:<sha256_hex>:<len>:<data>"
// Returns: { task_id via out pointer, datos as CadenaSegura }
// On error returns CadenaSegura with longitud=0 and datos=NULL
CadenaSegura cm_deserializar_checkpoint(CadenaSegura checkpoint_str,
                                         int* out_task_id, int* out_seq) {
    if (checkpoint_str.longitud < 5 || !checkpoint_str.datos
        || memcmp(checkpoint_str.datos, "CKPT:", 5) != 0)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    const char* p = checkpoint_str.datos + 5;
    const char* end = checkpoint_str.datos + checkpoint_str.longitud;

    // Parse task_id
    char* endp = NULL;
    long task_id = strtol(p, &endp, 10);
    if (endp == p || *endp != ':' || endp >= end)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    p = endp + 1;

    // Parse seq
    long seq = strtol(p, &endp, 10);
    if (endp == p || *endp != ':' || endp >= end)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    p = endp + 1;

    // Parse SHA-256 hex checksum (64 chars)
    char cksum_str[65];
    if (end - p < 64) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(cksum_str, p, 64);
    cksum_str[64] = '\0';
    p += 64;

    if (*p != ':') return (CadenaSegura){ .longitud = 0, .datos = NULL };
    p++;

    // Parse data length
    long data_len = strtol(p, &endp, 10);
    if (endp == p || *endp != ':' || endp >= end)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    p = endp + 1;

    // Verify remaining data matches claimed length
    int remaining = (int)(end - p);
    if (remaining != (int)data_len)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    // Verify SHA-256 checksum
    char computed_hex[65];
    _cm_sha256_hex(p, (int)data_len, computed_hex);
    if (memcmp(computed_hex, cksum_str, 64) != 0)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    // Copy data into pool-allocated buffer
    char* data_buf = (char*)pool_alloc((size_t)(data_len + 1));
    if (!data_buf) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(data_buf, p, (size_t)data_len);
    data_buf[data_len] = '\0';

    if (out_task_id) *out_task_id = (int)task_id;
    if (out_seq) *out_seq = (int)seq;

    return (CadenaSegura){ .longitud = (int)data_len, .datos = data_buf };
}

// --- Verify checkpoint integrity (re-compute checksum) ---
// Returns: 0 = valid, -1 = corrupted
int cm_verificar_integridad(CadenaSegura checkpoint_str) {
    int task_id_dummy, seq_dummy;
    CadenaSegura data = cm_deserializar_checkpoint(checkpoint_str,
                                                    &task_id_dummy, &seq_dummy);
    if (data.longitud <= 0 || !data.datos) return -1;
    pool_free((void*)data.datos);
    return 0;
}

// --- Restore a task from a checkpoint string into the WS queue ---
// Returns: 0 = ok, -1 = error
int cm_restaurar_checkpoint(CadenaSegura checkpoint_str) {
    int task_id;
    int seq;
    CadenaSegura task_data = cm_deserializar_checkpoint(checkpoint_str,
                                                         &task_id, &seq);
    if (task_data.longitud <= 0 || !task_data.datos) return -1;

    int rc = ws_encolar(task_id, task_data);
    pool_free((void*)task_data.datos);
    return rc;
}

// --- Full migration: checkpoint + remove from WS queue ---
// This simulates the migration of a task:
//   1. Create checkpoint from task data
//   2. Remove task from local WS queue (ownership transfer)
//   3. Return checkpoint string for transport to remote node
// Returns: checkpoint string, or empty on failure
CadenaSegura cm_migrar_tarea(CadenaSegura datos_debug) {
    pthread_mutex_lock(&_cm_mutex);

    // Dequeue a task from the WS queue
    CadenaSegura tarea = ws_desencolar();
    if (tarea.longitud <= 0) {
        _cm_fallidas++;
        snprintf(_cm_ultimo_resultado, sizeof(_cm_ultimo_resultado),
                 "MIGRACION_FALLIDA:cola_vacia");
        pthread_mutex_unlock(&_cm_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    // Parse task_id from "id:data" format returned by ws_desencolar
    const char* p = tarea.datos;
    const char* colon = memchr(p, ':', (size_t)tarea.longitud);
    int task_id = 0;
    int data_offset = 0;
    int data_len = 0;
    if (colon) {
        char id_str[32];
        int id_len = (int)(colon - p);
        if (id_len >= 32) id_len = 31;
        memcpy(id_str, p, (size_t)id_len);
        id_str[id_len] = '\0';
        task_id = atoi(id_str);
        data_offset = id_len + 1;
        data_len = tarea.longitud - data_offset;
    } else {
        pool_free((void*)tarea.datos);
        _cm_fallidas++;
        snprintf(_cm_ultimo_resultado, sizeof(_cm_ultimo_resultado),
                 "MIGRACION_FALLIDA:formato_invalido");
        pthread_mutex_unlock(&_cm_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    // Build CadenaSegura for just the payload
    CadenaSegura payload = { .longitud = data_len,
                             .datos = tarea.datos + data_offset };

    // Create checkpoint with SHA-256 integrity
    int seq = _cm_seq++;
    char sha256_hex[65];
    _cm_sha256_hex(payload.datos, payload.longitud, sha256_hex);

    char header[128];
    int hdr_len = snprintf(header, sizeof(header), "CKPT:%d:%d:%s:%d:",
                           task_id, seq, sha256_hex, payload.longitud);

    int ckpt_total = hdr_len + payload.longitud;
    char* ckpt_buf = (char*)pool_alloc((size_t)(ckpt_total + 1));
    if (!ckpt_buf) {
        pool_free((void*)tarea.datos);
        _cm_fallidas++;
        snprintf(_cm_ultimo_resultado, sizeof(_cm_ultimo_resultado),
                 "MIGRACION_FALLIDA:pool_alloc_ckpt");
        pthread_mutex_unlock(&_cm_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    memcpy(ckpt_buf, header, (size_t)hdr_len);
    memcpy(ckpt_buf + hdr_len, payload.datos, (size_t)payload.longitud);
    ckpt_buf[ckpt_total] = '\0';

    _cm_completadas++;
    snprintf(_cm_ultimo_resultado, sizeof(_cm_ultimo_resultado),
             "MIGRACION_OK:%d:seq=%d", task_id, seq);

    pool_free((void*)tarea.datos);
    pthread_mutex_unlock(&_cm_mutex);

    return (CadenaSegura){ .longitud = ckpt_total, .datos = ckpt_buf };
}

// --- Simulate full migration lifecycle between two nodes ---
int cm_migrar_entre_nodos(CadenaSegura ip_destino, int puerto_destino) {
    (void)ip_destino;
    (void)puerto_destino;

    CadenaSegura ckpt = cm_migrar_tarea((CadenaSegura){ .longitud = 0, .datos = NULL });
    if (ckpt.longitud <= 0 || !ckpt.datos) return -1;

    int rc = cm_restaurar_checkpoint(ckpt);
    pool_free((void*)ckpt.datos);

    pthread_mutex_lock(&_cm_mutex);
    if (rc == 0)
        _cm_completadas++;
    else
        _cm_fallidas++;
    pthread_mutex_unlock(&_cm_mutex);

    return rc;
}

// --- Get last migration result string ---
CadenaSegura cm_ultima_migracion(void) {
    pthread_mutex_lock(&_cm_mutex);
    int len = (int)strlen(_cm_ultimo_resultado);
    char* buf = (char*)pool_alloc((size_t)(len + 1));
    if (!buf) {
        pthread_mutex_unlock(&_cm_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    memcpy(buf, _cm_ultimo_resultado, (size_t)(len + 1));
    pthread_mutex_unlock(&_cm_mutex);
    return (CadenaSegura){ .longitud = len, .datos = buf };
}

// --- Get completed migration count ---
int cm_migraciones_completadas(void) {
    pthread_mutex_lock(&_cm_mutex);
    int n = _cm_completadas;
    pthread_mutex_unlock(&_cm_mutex);
    return n;
}

// --- Get failed migration count ---
int cm_migraciones_fallidas(void) {
    pthread_mutex_lock(&_cm_mutex);
    int n = _cm_fallidas;
    pthread_mutex_unlock(&_cm_mutex);
    return n;
}

// =========================================================================
// M9.1 — Deterministic Execution Recording (rr-style Time-Travel Debug)
// =========================================================================
// Integrates with existing M9.0 circular buffer. Adds sequential event
// numbering, snapshot mechanism, backward search, and replay simulation.
// =========================================================================

static int _tr_secuencia = 0;
static int _tr_initialized = 0;
static int _tr_ultimo_error_idx = -1;

static pthread_mutex_t _tr_mutex = PTHREAD_MUTEX_INITIALIZER;

// --- Initialize recording with sequence numbering ---
// Resets sequence counter and prepares the trace buffer for deterministic recording.
// Must be called after iniciar_sesion().
int tr_inicializar_recording(void) {
    if (!g_trace_initialized) {
        _init_trace_session("recording");
    }
    if (!g_trace_session.eventos) return -1;

    // Reset buffer for deterministic recording
    pthread_mutex_lock(&_tr_mutex);
    _tr_secuencia = 0;
    _tr_ultimo_error_idx = -1;
    _tr_initialized = 1;
    g_trace_session.total_eventos = 0;
    g_trace_session.cabeza = 0;
    pthread_mutex_unlock(&_tr_mutex);

    return 0;
}

// --- Helper: get next sequence number (thread-safe) ---
static int _tr_next_seq(void) {
    pthread_mutex_lock(&_tr_mutex);
    int s = _tr_secuencia++;
    pthread_mutex_unlock(&_tr_mutex);
    return s;
}

// --- Record a branch decision (which path was taken) ---
// linea: source line of the branch
// rama: 0 = false/else, 1 = true/if
// id_funcion: function name context
int tr_grabar_bifurcacion(int linea, int rama, CadenaSegura id_funcion) {
    if (!_tr_initialized) return -1;
    int seq = _tr_next_seq();
    int rc = _syn_debug_registrar_evento(
        EVENT_BRANCH_TAKEN,
        id_funcion.datos ? id_funcion.datos : "",
        "", linea,
        "branch",
        (long long)seq,
        (double)rama,
        rama ? "true" : "false");
    if (rc != 0) return -1;
    return seq;
}

// --- Record a variable snapshot at current execution point ---
// nombre_variable: name of the variable being snapshotted
// valor_entero: integer value (or 0 if using texto)
// valor_texto: string value (or empty if using entero)
// linea: source line number
int tr_grabar_snapshot(CadenaSegura nombre_variable, int valor_entero,
                       CadenaSegura valor_texto, int linea) {
    if (!_tr_initialized) return -1;
    int seq = _tr_next_seq();
    int rc = _syn_debug_registrar_evento(
        EVENT_VARIABLE_CHANGE,
        "", "", linea,
        nombre_variable.datos ? nombre_variable.datos : "",
        (long long)seq,
        (double)valor_entero,
        valor_texto.datos ? valor_texto.datos : "");
    if (rc != 0) return -1;
    return seq;
}

// --- Record a function call entry ---
// funcion: function name
// linea: source line of the call
// num_args: number of arguments passed
int tr_grabar_llamada(CadenaSegura funcion, int linea, int num_args) {
    if (!_tr_initialized) return -1;
    int seq = _tr_next_seq();
    int rc = _syn_debug_registrar_evento(
        EVENT_FN_CALL,
        funcion.datos ? funcion.datos : "",
        "", linea,
        "args",
        (long long)seq,
        (double)num_args,
        "");
    if (rc != 0) return -1;
    return seq;
}

// --- Record a function return ---
// funcion: function name
// linea: source line of the return
int tr_grabar_retorno(CadenaSegura funcion, int linea) {
    if (!_tr_initialized) return -1;
    int seq = _tr_next_seq();
    int rc = _syn_debug_registrar_evento(
        EVENT_FN_RETURN,
        funcion.datos ? funcion.datos : "",
        "", linea,
        "return",
        (long long)seq,
        0.0, "");
    if (rc != 0) return -1;
    return seq;
}

// --- Record an error event (for fault induction testing) ---
// mensaje: description of the error
// linea: source line where the error occurred
int tr_grabar_error(CadenaSegura mensaje, int linea) {
    if (!_tr_initialized) return -1;
    int seq = _tr_next_seq();
    int idx = g_trace_session.cabeza > 0 ? g_trace_session.cabeza - 1 : 0;
    _tr_ultimo_error_idx = idx;
    int rc = _syn_debug_registrar_evento(
        EVENT_ERROR,
        "", "", linea,
        "error",
        (long long)seq,
        0.0,
        mensaje.datos ? mensaje.datos : "unknown_error");
    if (rc != 0) return -1;
    return seq;
}

// --- Search backwards through recorded events for a specific tag ---
// Returns sequence number of the found event, or -1 if not found.
// Starts from the most recent event and searches backwards.
int tr_buscar_evento(int tag, int desde_secuencia) {
    if (!_tr_initialized || !g_trace_session.eventos) return -1;

    int total = g_trace_session.total_eventos;
    if (total <= 0) return -1;

    int inicio = (g_trace_session.total_eventos < TRACE_MAX_EVENTS) ? 0 :
                 (g_trace_session.cabeza % TRACE_MAX_EVENTS);

    // Search backwards from the end
    for (int i = total - 1; i >= 0; i--) {
        int idx = (inicio + i) % TRACE_MAX_EVENTS;
        TraceEvent* e = &g_trace_session.eventos[idx];
        if (e->tag == tag) {
            // Found an event with matching tag
            // If desde_secuencia >= 0, only return if seq <= desde_secuencia
            long long ev_seq = e->valor_entero;
            if (desde_secuencia < 0 || ev_seq <= (long long)desde_secuencia) {
                return (int)ev_seq;
            }
        }
    }
    return -1;
}

// --- Get recorded event at index as string for inspection ---
// Returns "tag|seq|funcion|linea|variable|valor" or empty if not found
CadenaSegura tr_obtener_evento(int indice) {
    if (!_tr_initialized || !g_trace_session.eventos) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    int total = g_trace_session.total_eventos;
    if (indice < 0 || indice >= total) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    int inicio = (total < TRACE_MAX_EVENTS) ? 0 :
                 (g_trace_session.cabeza % TRACE_MAX_EVENTS);
    int idx = (inicio + indice) % TRACE_MAX_EVENTS;
    TraceEvent* e = &g_trace_session.eventos[idx];

    char buf[256];
    int len = snprintf(buf, sizeof(buf), "%d|%lld|%s|%d|%s|%lld",
                       e->tag, e->valor_entero,
                       e->funcion ? e->funcion : "",
                       e->linea,
                       e->variable ? e->variable : "",
                       (long long)e->valor_decimal);

    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(result, buf, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = len, .datos = result };
}

// --- Simulate replay up to a target event sequence number ---
// In a full rr implementation this would re-execute the program.
// Here, we validate that events exist up to the target seq and return
// the count of events that would be replayed.
int tr_reproducir_hasta(int secuencia_objetivo) {
    if (!_tr_initialized || !g_trace_session.eventos) return -1;
    if (secuencia_objetivo < 0) return -1;

    int total = g_trace_session.total_eventos;
    int inicio = (total < TRACE_MAX_EVENTS) ? 0 :
                 (g_trace_session.cabeza % TRACE_MAX_EVENTS);

    int replayed = 0;
    for (int i = 0; i < total; i++) {
        int idx = (inicio + i) % TRACE_MAX_EVENTS;
        TraceEvent* e = &g_trace_session.eventos[idx];
        if (e->valor_entero <= (long long)secuencia_objetivo) {
            replayed++;
        } else {
            break;
        }
    }
    return replayed;
}

// --- Get the sequence number of the last error event ---
// Returns sequence number, or -1 if no error recorded
int tr_indice_ultimo_error(void) {
    if (!_tr_initialized) return -1;
    return _tr_ultimo_error_idx;
}

// --- Get total number of recorded events (sequence count) ---
int tr_total_eventos(void) {
    if (!_tr_initialized) return 0;
    return _tr_secuencia;
}

// =========================================================================
// M9.2 — Reversible Breakpoints & Historical Snapshot Inspection
// =========================================================================
// Engine for reverse execution replay: set breakpoints on line/variable/tag,
// step backwards through the event trace, inspect call stacks and variable
// values at any recorded point, and jump to the event just before a fault.
// =========================================================================

#define RP_MAX_BREAKPOINTS 16
#define RP_POR_LINEA    0
#define RP_POR_VARIABLE 1
#define RP_POR_TAG      2

typedef struct {
    int activo;
    int tipo;     // 0=linea, 1=variable, 2=tag
    char patron[64];
    int valor_int;
} RpBreakpoint;

static RpBreakpoint _rp_breakpoints[RP_MAX_BREAKPOINTS];
static int _rp_total_bps = 0;
static int _rp_posicion = -1;  // current replay cursor (event index)
static int _rp_initialized = 0;

// --- Helper: get event at logical index (handles circular buffer) ---
static TraceEvent* _rp_get_event(int indice_logico) {
    if (!g_trace_session.eventos) return NULL;
    int total = g_trace_session.total_eventos;
    if (indice_logico < 0 || indice_logico >= total) return NULL;
    int inicio = (total < TRACE_MAX_EVENTS) ? 0 :
                 (g_trace_session.cabeza % TRACE_MAX_EVENTS);
    int idx = (inicio + indice_logico) % TRACE_MAX_EVENTS;
    return &g_trace_session.eventos[idx];
}

// --- Initialize the reversible debug engine ---
int rp_inicializar(void) {
    for (int i = 0; i < RP_MAX_BREAKPOINTS; i++) {
        _rp_breakpoints[i].activo = 0;
    }
    _rp_total_bps = 0;
    _rp_posicion = -1;
    _rp_initialized = 1;
    return 0;
}

// --- Set a reversible breakpoint ---
// tipo: 0=linea, 1=variable, 2=tag
// patron: line number as string for linea, variable name for variable, tag name for tag
// valor_int: for tipo=2 the tag integer, for tipo=0 the line number, for tipo=1 ignored
// Returns breakpoint ID (0-based), or -1 if full
int rp_establecer_breakpoint(int tipo, CadenaSegura patron, int valor_int) {
    if (!_rp_initialized) return -1;
    if (_rp_total_bps >= RP_MAX_BREAKPOINTS) return -1;
    if (tipo < 0 || tipo > 2) return -1;

    int id = _rp_total_bps;
    _rp_breakpoints[id].activo = 1;
    _rp_breakpoints[id].tipo = tipo;
    _rp_breakpoints[id].valor_int = valor_int;
    if (patron.datos) {
        int plen = patron.longitud < 63 ? patron.longitud : 63;
        memcpy(_rp_breakpoints[id].patron, patron.datos, (size_t)plen);
        _rp_breakpoints[id].patron[plen] = '\0';
    } else {
        _rp_breakpoints[id].patron[0] = '\0';
    }
    _rp_total_bps++;
    return id;
}

// --- Remove a breakpoint by ID ---
int rp_eliminar_breakpoint(int id) {
    if (!_rp_initialized) return -1;
    if (id < 0 || id >= _rp_total_bps) return -1;
    _rp_breakpoints[id].activo = 0;
    // Compact: shift remaining breakpoints down
    for (int i = id; i < _rp_total_bps - 1; i++) {
        _rp_breakpoints[i] = _rp_breakpoints[i + 1];
    }
    _rp_total_bps--;
    return 0;
}

// --- Clear all breakpoints ---
int rp_limpiar_breakpoints(void) {
    if (!_rp_initialized) return -1;
    for (int i = 0; i < RP_MAX_BREAKPOINTS; i++) {
        _rp_breakpoints[i].activo = 0;
    }
    _rp_total_bps = 0;
    return 0;
}

// --- Find event index matching a breakpoint, searching backwards ---
// Returns logical event index, or -1 if not found
int rp_buscar_breakpoint(int id) {
    if (!_rp_initialized || !g_trace_session.eventos) return -1;
    if (id < 0 || id >= _rp_total_bps) return -1;
    if (!_rp_breakpoints[id].activo) return -1;

    int total = g_trace_session.total_eventos;
    if (total <= 0) return -1;

    RpBreakpoint* bp = &_rp_breakpoints[id];

    // Search backwards from end
    for (int i = total - 1; i >= 0; i--) {
        TraceEvent* e = _rp_get_event(i);
        if (!e) continue;

        int match = 0;
        switch (bp->tipo) {
            case RP_POR_LINEA:
                match = (e->linea == bp->valor_int);
                break;
            case RP_POR_VARIABLE:
                match = (e->variable && bp->patron[0] &&
                         strcmp(e->variable, bp->patron) == 0);
                break;
            case RP_POR_TAG:
                match = (e->tag == bp->valor_int);
                break;
        }
        if (match) return i;
    }
    return -1;
}

// --- Step backwards N events from a given position ---
// Returns the new position (event index), or -1 if at start
int rp_retroceder(int pasos, int desde_evento) {
    if (!_rp_initialized) return -1;
    int total = g_trace_session.total_eventos;
    if (total <= 0) return -1;

    int inicio = desde_evento >= 0 ? desde_evento : (total - 1);
    if (inicio >= total) inicio = total - 1;
    if (pasos <= 0) {
        _rp_posicion = inicio;
        return _rp_posicion;
    }

    int nueva_pos = inicio - pasos;
    if (nueva_pos < 0) nueva_pos = -1;

    _rp_posicion = nueva_pos;
    return _rp_posicion;
}

// --- Get the current replay cursor position ---
int rp_posicion_actual(void) {
    if (!_rp_initialized) return -1;
    return _rp_posicion;
}

// --- Jump to the event index just before the last error ---
// Returns the event index of the last non-error event before the error, or -1
int rp_ir_a_pre_error(void) {
    if (!_rp_initialized || !g_trace_session.eventos) return -1;
    int total = g_trace_session.total_eventos;
    if (total <= 0) return -1;

    // Find the last ERROR event
    int error_idx = -1;
    for (int i = total - 1; i >= 0; i--) {
        TraceEvent* e = _rp_get_event(i);
        if (e && e->tag == EVENT_ERROR) {
            error_idx = i;
            break;
        }
    }
    if (error_idx < 0) return -1;

    // Return event just before the error
    int pre = error_idx - 1;
    if (pre < 0) return -1;

    _rp_posicion = pre;
    return pre;
}

// --- Inspect a variable's value at a specific event index ---
// Searches backwards from indice_evento (inclusive) for the most recent
// occurrence of the named variable. Returns "entero:<val>" or "texto:<val>",
// or empty CadenaSegura if the variable was never recorded.
CadenaSegura rp_inspeccionar_variable(int indice_evento, CadenaSegura nombre) {
    if (!_rp_initialized || !g_trace_session.eventos) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    if (!nombre.datos || nombre.longitud <= 0) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    int total = g_trace_session.total_eventos;
    if (indice_evento < 0 || indice_evento >= total) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    // Search backwards from indice_evento for the named variable
    for (int i = indice_evento; i >= 0; i--) {
        TraceEvent* e = _rp_get_event(i);
        if (!e) continue;
        if ((e->tag == EVENT_VARIABLE_CHANGE || e->tag == EVENT_ASSIGNMENT)
            && e->variable && strcmp(e->variable, nombre.datos) == 0) {
            // Found the most recent occurrence
            char buf[64];
            int len = 0;
            if (e->valor_texto && strlen(e->valor_texto) > 0) {
                len = snprintf(buf, sizeof(buf), "texto:%s", e->valor_texto);
            } else {
                len = snprintf(buf, sizeof(buf), "entero:%lld", (long long)e->valor_decimal);
            }
            char* result = (char*)pool_alloc((size_t)(len + 1));
            if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
            memcpy(result, buf, (size_t)(len + 1));
            return (CadenaSegura){ .longitud = len, .datos = result };
        }
    }
    return (CadenaSegura){ .longitud = 0, .datos = NULL };
}

// --- Build call stack string at a specific event index ---
// Returns "funcion:linea|funcion:linea|..." (innermost first), or empty
CadenaSegura rp_pila_llamadas(int indice_evento) {
    if (!_rp_initialized || !g_trace_session.eventos) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    int total = g_trace_session.total_eventos;
    if (indice_evento < 0 || indice_evento >= total) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    // Walk backwards from indice_evento, tracking call/return pairs
    // Use a simple stack: push on EVENT_FN_CALL, pop on EVENT_FN_RETURN
    char stack_buf[1024];
    int stack_len = 0;
    int depth = 0;
    // Track unmatched calls
    int call_lineas[64];
    const char* call_funcs[64];

    for (int i = indice_evento; i >= 0; i--) {
        TraceEvent* e = _rp_get_event(i);
        if (!e) break;

        if (e->tag == EVENT_FN_RETURN) {
            depth++;
        } else if (e->tag == EVENT_FN_CALL) {
            if (depth > 0) {
                depth--;  // matched a return
            } else {
                // Unmatched call: add to stack
                int idx = stack_len / 2; // placeholder
                (void)idx;
                // Build "funcion:linea|" segment
                const char* fname = e->funcion ? e->funcion : "?";
                int seg_len = snprintf(stack_buf + stack_len,
                                       sizeof(stack_buf) - (size_t)stack_len,
                                       "%s:%d|", fname, e->linea);
                if (seg_len > 0 && stack_len + seg_len < (int)sizeof(stack_buf)) {
                    stack_len += seg_len;
                }
            }
        }
    }

    // Remove trailing '|'
    if (stack_len > 0 && stack_buf[stack_len - 1] == '|') {
        stack_len--;
    }

    if (stack_len <= 0) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    char* result = (char*)pool_alloc((size_t)(stack_len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(result, stack_buf, (size_t)(stack_len + 1));
    return (CadenaSegura){ .longitud = stack_len, .datos = result };
}

// --- Search backwards for a variable change to a specific value ---
// Returns event index, or -1 if not found
int rp_buscar_cambio_variable(CadenaSegura nombre, int valor) {
    if (!_rp_initialized || !g_trace_session.eventos) return -1;
    if (!nombre.datos || nombre.longitud <= 0) return -1;

    int total = g_trace_session.total_eventos;
    if (total <= 0) return -1;

    for (int i = total - 1; i >= 0; i--) {
        TraceEvent* e = _rp_get_event(i);
        if (!e) continue;
        if ((e->tag == EVENT_VARIABLE_CHANGE || e->tag == EVENT_ASSIGNMENT)
            && e->variable && strcmp(e->variable, nombre.datos) == 0
            && (int)e->valor_decimal == valor) {
            return i;
        }
    }
    return -1;
}

// =========================================================================
// M9.3 — Memory Snapshots & Historical State Diff
// =========================================================================
// Engine for capturing compressed variable-state snapshots from the event
// trace and computing structural diffs between two execution points.
//
// Snapshot format (newline-separated entries):
//     var1|entero|42
//     var2|texto|hello
//
// Diff format (prefix identifies change type):
//     +name|tipo|val          — added in B
//     -name|tipo|val          — removed in B
//     ~name|tipo_a|val_a|tipo_b|val_b  — changed
// =========================================================================

#define MS_MAX_VARS 256
#define MS_LINE_MAX 128

// --- Helper: find event index for a given sequence number ---
// Seq numbers are assigned monotonically by _tr_next_seq. Since events
// are stored consecutively (1:1 with seq), we derive index = seq - 1.
// Returns -1 if out of range.
static int _ms_seq_a_indice(int seq) {
    if (!g_trace_session.eventos) return -1;
    int total = g_trace_session.total_eventos;
    if (total <= 0 || seq < 1) return -1;
    int idx = seq - 1;
    if (idx >= total) idx = total - 1;  // clamp to last event
    return idx;
}

// --- Helper: append one line to a snapshot buffer ---
static int _ms_append_line(char* buf, int offset, int cap,
                           const char* name, const char* tipo,
                           const char* valor) {
    if (!name) name = "?";
    if (!tipo) tipo = "?";
    if (!valor) valor = "";
    int needed = snprintf(buf + offset, (size_t)(cap - offset),
                          "%s|%s|%s\n", name, tipo, valor);
    if (needed < 0) return offset;
    if (offset + needed >= cap) return offset;
    return offset + needed;
}

// --- Helper: parse a snapshot line into name / tipo / valor ---
// Returns 1 if parsed OK, 0 on error
static int _ms_parse_line(const char* line, int line_len,
                          char* name_out, int name_cap,
                          char* tipo_out, int tipo_cap,
                          char* val_out, int val_cap) {
    if (!line || line_len <= 0) return 0;
    const char* p1 = strchr(line, '|');
    if (!p1 || p1 >= line + line_len) return 0;
    int name_len = (int)(p1 - line);
    if (name_len >= name_cap) name_len = name_cap - 1;
    memcpy(name_out, line, (size_t)name_len);
    name_out[name_len] = '\0';

    const char* p2 = strchr(p1 + 1, '|');
    if (!p2 || p2 >= line + line_len) return 0;
    int tipo_len = (int)(p2 - (p1 + 1));
    if (tipo_len >= tipo_cap) tipo_len = tipo_cap - 1;
    memcpy(tipo_out, p1 + 1, (size_t)tipo_len);
    tipo_out[tipo_len] = '\0';

    int val_len = line_len - (int)(p2 + 1 - line);
    if (val_len >= val_cap) val_len = val_cap - 1;
    memcpy(val_out, p2 + 1, (size_t)val_len);
    val_out[val_len] = '\0';
    return 1;
}

// --- Capture a compressed variable-state snapshot at a given sequence ---
// Walks backward from the event matching seq, collecting the most recent
// value of each unique variable.
// Returns serialized snapshot string, or empty CadenaSegura on error.
CadenaSegura ms_tomar_en(int secuencia) {
    if (!g_trace_session.eventos) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    int idx = _ms_seq_a_indice(secuencia);
    if (idx < 0) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    char names[MS_MAX_VARS][64];
    char tipos[MS_MAX_VARS][16];
    char vals[MS_MAX_VARS][64];
    int nvars = 0;

    for (int i = idx; i >= 0 && nvars < MS_MAX_VARS; i--) {
        TraceEvent* e = _rp_get_event(i);
        if (!e) continue;
        if (e->tag != EVENT_VARIABLE_CHANGE && e->tag != EVENT_ASSIGNMENT) continue;
        if (!e->variable || strlen(e->variable) == 0) continue;

        int found = 0;
        for (int j = 0; j < nvars; j++) {
            if (strcmp(names[j], e->variable) == 0) { found = 1; break; }
        }
        if (found) continue;

        int nlen = (int)strlen(e->variable);
        if (nlen >= 64) nlen = 63;
        memcpy(names[nvars], e->variable, (size_t)nlen);
        names[nvars][nlen] = '\0';

        if (e->valor_texto && strlen(e->valor_texto) > 0) {
            memcpy(tipos[nvars], "texto", 6);
            int vlen = (int)strlen(e->valor_texto);
            if (vlen >= 64) vlen = 63;
            memcpy(vals[nvars], e->valor_texto, (size_t)vlen);
            vals[nvars][vlen] = '\0';
        } else {
            memcpy(tipos[nvars], "entero", 7);
            snprintf(vals[nvars], 64, "%lld", (long long)e->valor_decimal);
        }
        nvars++;
    }

    int cap = nvars * 128 + 16;
    char* buf = (char*)pool_alloc((size_t)cap);
    if (!buf) return (CadenaSegura){ .longitud = 0, .datos = NULL };

    int pos = 0;
    for (int i = nvars - 1; i >= 0; i--) {
        pos = _ms_append_line(buf, pos, cap, names[i], tipos[i], vals[i]);
    }

    return (CadenaSegura){ .longitud = pos, .datos = buf };
}

// --- Compare two snapshots and produce a structural diff ---
// Returns diff string, or empty on error.
CadenaSegura ms_diferenciar(CadenaSegura snap_a, CadenaSegura snap_b) {
    if (!snap_a.datos || snap_a.longitud <= 0) return snap_b;
    if (!snap_b.datos || snap_b.longitud <= 0) return snap_a;

    char a_names[MS_MAX_VARS][64];
    char a_tipos[MS_MAX_VARS][16];
    char a_vals[MS_MAX_VARS][64];
    int na = 0;

    const char* p = snap_a.datos;
    const char* end = snap_a.datos + snap_a.longitud;
    while (p < end && na < MS_MAX_VARS) {
        const char* nl = strchr(p, '\n');
        int line_len = nl ? (int)(nl - p) : (int)(end - p);
        if (line_len > 0) {
            _ms_parse_line(p, line_len,
                          a_names[na], 64, a_tipos[na], 16, a_vals[na], 64);
            if (strlen(a_names[na]) > 0) na++;
        }
        p = nl ? nl + 1 : end;
    }

    char b_names[MS_MAX_VARS][64];
    char b_tipos[MS_MAX_VARS][16];
    char b_vals[MS_MAX_VARS][64];
    int nb = 0;

    p = snap_b.datos;
    end = snap_b.datos + snap_b.longitud;
    while (p < end && nb < MS_MAX_VARS) {
        const char* nl = strchr(p, '\n');
        int line_len = nl ? (int)(nl - p) : (int)(end - p);
        if (line_len > 0) {
            _ms_parse_line(p, line_len,
                          b_names[nb], 64, b_tipos[nb], 16, b_vals[nb], 64);
            if (strlen(b_names[nb]) > 0) nb++;
        }
        p = nl ? nl + 1 : end;
    }

    int cap = (na + nb + na) * 128 + 16;
    char* buf = (char*)pool_alloc((size_t)cap);
    if (!buf) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    int pos = 0;

    for (int i = 0; i < na; i++) {
        int found_in_b = 0;
        for (int j = 0; j < nb; j++) {
            if (strcmp(a_names[i], b_names[j]) == 0) {
                found_in_b = 1;
                if (strcmp(a_tipos[i], b_tipos[j]) != 0 ||
                    strcmp(a_vals[i], b_vals[j]) != 0) {
                    pos += snprintf(buf + pos, (size_t)(cap - pos),
                                    "~%s|%s|%s|%s|%s\n",
                                    a_names[i], a_tipos[i], a_vals[i],
                                    b_tipos[j], b_vals[j]);
                }
                break;
            }
        }
        if (!found_in_b) {
            pos += snprintf(buf + pos, (size_t)(cap - pos),
                            "-%s|%s|%s\n", a_names[i], a_tipos[i], a_vals[i]);
        }
    }

    for (int j = 0; j < nb; j++) {
        int found_in_a = 0;
        for (int i = 0; i < na; i++) {
            if (strcmp(b_names[j], a_names[i]) == 0) { found_in_a = 1; break; }
        }
        if (!found_in_a) {
            pos += snprintf(buf + pos, (size_t)(cap - pos),
                            "+%s|%s|%s\n", b_names[j], b_tipos[j], b_vals[j]);
        }
    }

    if (pos > 0 && buf[pos - 1] == '\n') pos--;
    return (CadenaSegura){ .longitud = pos, .datos = buf };
}

// --- Convenience: diff between two sequence numbers ---
CadenaSegura ms_diff_entre(int seq_a, int seq_b) {
    if (seq_a == seq_b) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    CadenaSegura snap_a = ms_tomar_en(seq_a);
    CadenaSegura snap_b = ms_tomar_en(seq_b);
    if (!snap_a.datos && !snap_b.datos) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    return ms_diferenciar(snap_a, snap_b);
}

// --- Count variables in a snapshot ---
int ms_snapshot_contar_vars(CadenaSegura snapshot) {
    if (!snapshot.datos || snapshot.longitud <= 0) return 0;
    int count = 0;
    const char* p = snapshot.datos;
    const char* end = snapshot.datos + snapshot.longitud;
    while (p < end) {
        const char* nl = strchr(p, '\n');
        if (nl) { if (nl > p) count++; p = nl + 1; }
        else { if (end > p) count++; break; }
    }
    return count;
}

// --- Get byte size of a snapshot string ---
int ms_snapshot_tamano(CadenaSegura snapshot) {
    if (!snapshot.datos) return 0;
    return snapshot.longitud;
}

// --- Check if a variable exists in a snapshot ---
// Returns "tipo:valor" or empty CadenaSegura
CadenaSegura ms_snapshot_contiene(CadenaSegura snapshot, CadenaSegura nombre) {
    if (!snapshot.datos || snapshot.longitud <= 0 ||
        !nombre.datos || nombre.longitud <= 0) {
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    const char* p = snapshot.datos;
    const char* end = snapshot.datos + snapshot.longitud;
    while (p < end) {
        const char* nl = strchr(p, '\n');
        int line_len = nl ? (int)(nl - p) : (int)(end - p);
        if (line_len > 0) {
            char nb[64], tb[16], vb[64];
            if (_ms_parse_line(p, line_len, nb, 64, tb, 16, vb, 64)) {
                if (strcmp(nb, nombre.datos) == 0) {
                    char result_buf[128];
                    int rlen = snprintf(result_buf, sizeof(result_buf), "%s:%s", tb, vb);
                    if (rlen < 0) return (CadenaSegura){ .longitud = 0, .datos = NULL };
                    char* result = (char*)pool_alloc((size_t)(rlen + 1));
                    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
                    memcpy(result, result_buf, (size_t)(rlen + 1));
                    return (CadenaSegura){ .longitud = rlen, .datos = result };
                }
            }
        }
        p = nl ? nl + 1 : end;
    }
    return (CadenaSegura){ .longitud = 0, .datos = NULL };
}

// ============================================================
// M8.5 — Cluster Auto-Discovery & Membership
// ============================================================
// UDP multicast discovery, heartbeat-based health tracking,
// and dynamic node table management.
// ============================================================

#define MAX_NODOS_CLUSTER 64
#define MAX_ID_LEN 64
#define MAX_IP_LEN 48
#define MAX_PUBKEY_LEN 128
#define DESCUBRIMIENTO_MAGIC "SYNCLUSTER"

// --- Node table entry ---
typedef struct {
    char id[MAX_ID_LEN];
    char ip[MAX_IP_LEN];
    int puerto;
    char pubkey[MAX_PUBKEY_LEN];
    int estado;         // 0=DESCONOCIDO, 1=VIVO, 2=SOSPECHOSO, 3=MUERTO
    int ultimo_latido_s; // timestamp (unix epoch seconds) of last heartbeat
    int primer_visto_s;   // timestamp when first discovered
    int num_heartbeats;   // total heartbeats received
} NodoClusterMembresia;

static NodoClusterMembresia _tabla_membresia[MAX_NODOS_CLUSTER];
static int _num_nodos_membresia = 0;
static int _max_nodos_membresia = MAX_NODOS_CLUSTER;
static int _heartbeat_intervalo_s = 5;   // default: 5 seconds
static int _heartbeat_timeout_s = 15;     // default: 15 seconds without = dead
static int _ultimo_tick_heartbeat_s = 0;
static pthread_mutex_t _membresia_mutex = PTHREAD_MUTEX_INITIALIZER;
static int _descubrimiento_inicializado = 0;

// --- Inicializa la tabla de membresía ---
int cluster_descubrimiento_inicializar(int max_nodos) {
    pthread_mutex_lock(&_membresia_mutex);
    if (max_nodos > MAX_NODOS_CLUSTER || max_nodos <= 0)
        max_nodos = MAX_NODOS_CLUSTER;
    _max_nodos_membresia = max_nodos;
    _num_nodos_membresia = 0;
    memset(_tabla_membresia, 0, sizeof(_tabla_membresia));
    _descubrimiento_inicializado = 1;
    _ultimo_tick_heartbeat_s = 0;
    pthread_mutex_unlock(&_membresia_mutex);
    return 0;
}

// --- Detiene el subsistema de descubrimiento ---
int cluster_descubrimiento_detener(void) {
    pthread_mutex_lock(&_membresia_mutex);
    _num_nodos_membresia = 0;
    memset(_tabla_membresia, 0, sizeof(_tabla_membresia));
    _descubrimiento_inicializado = 0;
    pthread_mutex_unlock(&_membresia_mutex);
    return 0;
}

// --- Encuentra índice de nodo por ID, o -1 si no existe ---
static int _buscar_nodo_por_id(const char* id) {
    for (int i = 0; i < _num_nodos_membresia; i++) {
        if (strcmp(_tabla_membresia[i].id, id) == 0)
            return i;
    }
    return -1;
}

// --- Encuentra índice de nodo por IP+puerto, o -1 ---
static int _buscar_nodo_por_direccion(const char* ip, int puerto) {
    for (int i = 0; i < _num_nodos_membresia; i++) {
        if (strcmp(_tabla_membresia[i].ip, ip) == 0 &&
            _tabla_membresia[i].puerto == puerto)
            return i;
    }
    return -1;
}

// --- Registrar o actualizar un nodo en la tabla de membresía ---
// Retorna índice del nodo (0+), o -1 si tabla llena
int cluster_registrar_nodo(CadenaSegura id, CadenaSegura ip, int puerto, CadenaSegura pubkey) {
    if (!_descubrimiento_inicializado) return -2;
    if (!id.datos || !ip.datos || puerto <= 0) return -3;

    pthread_mutex_lock(&_membresia_mutex);

    // Check if already exists
    int idx = _buscar_nodo_por_id(id.datos);
    if (idx < 0)
        idx = _buscar_nodo_por_direccion(ip.datos, puerto);

    if (idx >= 0) {
        // Update existing entry
        _tabla_membresia[idx].estado = 1; // VIVO
        _tabla_membresia[idx].ultimo_latido_s = (int)time(NULL);
        _tabla_membresia[idx].num_heartbeats++;
        strncpy(_tabla_membresia[idx].ip, ip.datos, MAX_IP_LEN - 1);
        _tabla_membresia[idx].puerto = puerto;
        if (pubkey.datos)
            strncpy(_tabla_membresia[idx].pubkey, pubkey.datos, MAX_PUBKEY_LEN - 1);
        pthread_mutex_unlock(&_membresia_mutex);
        return idx;
    }

    // New node: add if space available
    if (_num_nodos_membresia >= _max_nodos_membresia) {
        pthread_mutex_unlock(&_membresia_mutex);
        return -1;
    }

    int nuevo = _num_nodos_membresia++;
    strncpy(_tabla_membresia[nuevo].id, id.datos, MAX_ID_LEN - 1);
    _tabla_membresia[nuevo].id[MAX_ID_LEN - 1] = '\0';
    strncpy(_tabla_membresia[nuevo].ip, ip.datos, MAX_IP_LEN - 1);
    _tabla_membresia[nuevo].ip[MAX_IP_LEN - 1] = '\0';
    _tabla_membresia[nuevo].puerto = puerto;
    if (pubkey.datos) {
        strncpy(_tabla_membresia[nuevo].pubkey, pubkey.datos, MAX_PUBKEY_LEN - 1);
        _tabla_membresia[nuevo].pubkey[MAX_PUBKEY_LEN - 1] = '\0';
    } else {
        _tabla_membresia[nuevo].pubkey[0] = '\0';
    }
    _tabla_membresia[nuevo].estado = 1; // VIVO
    _tabla_membresia[nuevo].ultimo_latido_s = (int)time(NULL);
    _tabla_membresia[nuevo].primer_visto_s = (int)time(NULL);
    _tabla_membresia[nuevo].num_heartbeats = 1;

    pthread_mutex_unlock(&_membresia_mutex);
    return nuevo;
}

// --- Eliminar un nodo de la tabla por ID ---
// Retorna 0 si se eliminó, -1 si no se encontró
int cluster_eliminar_nodo(CadenaSegura id) {
    if (!_descubrimiento_inicializado || !id.datos) return -1;

    pthread_mutex_lock(&_membresia_mutex);
    int idx = _buscar_nodo_por_id(id.datos);
    if (idx < 0) {
        pthread_mutex_unlock(&_membresia_mutex);
        return -1;
    }
    // Shift remaining nodes
    for (int i = idx; i < _num_nodos_membresia - 1; i++) {
        _tabla_membresia[i] = _tabla_membresia[i + 1];
    }
    _num_nodos_membresia--;
    memset(&_tabla_membresia[_num_nodos_membresia], 0, sizeof(NodoClusterMembresia));
    pthread_mutex_unlock(&_membresia_mutex);
    return 0;
}

// --- Retorna número de nodos activos (estado VIVO) ---
int cluster_nodos_activos(void) {
    if (!_descubrimiento_inicializado) return 0;
    pthread_mutex_lock(&_membresia_mutex);
    int count = 0;
    for (int i = 0; i < _num_nodos_membresia; i++) {
        if (_tabla_membresia[i].estado == 1) count++;
    }
    pthread_mutex_unlock(&_membresia_mutex);
    return count;
}

// --- Retorna número total de nodos en tabla ---
int cluster_total_nodos(void) {
    if (!_descubrimiento_inicializado) return 0;
    pthread_mutex_lock(&_membresia_mutex);
    int n = _num_nodos_membresia;
    pthread_mutex_unlock(&_membresia_mutex);
    return n;
}

// --- Obtener información de un nodo por índice ---
// Retorna "id:ip:puerto:pubkey:estado:heartbeats"
CadenaSegura cluster_obtener_nodo(int idx) {
    if (!_descubrimiento_inicializado || idx < 0)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    pthread_mutex_lock(&_membresia_mutex);
    if (idx >= _num_nodos_membresia) {
        pthread_mutex_unlock(&_membresia_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    NodoClusterMembresia* n = &_tabla_membresia[idx];
    char buf[512];
    int len = snprintf(buf, sizeof(buf), "%s:%s:%d:%s:%d:%d",
                       n->id, n->ip, n->puerto, n->pubkey,
                       n->estado, n->num_heartbeats);
    if (len < 0 || len >= (int)sizeof(buf)) {
        pthread_mutex_unlock(&_membresia_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) {
        pthread_mutex_unlock(&_membresia_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }
    memcpy(result, buf, (size_t)(len + 1));
    pthread_mutex_unlock(&_membresia_mutex);
    return (CadenaSegura){ .longitud = len, .datos = result };
}

// --- Inicializar subsistema de heartbeat ---
// intervalo_s: segundos entre ticks de heartbeat
// timeout_s: segundos sin heartbeat para marcar nodo como caído
int cluster_heartbeat_inicializar(int intervalo_s, int timeout_s) {
    if (intervalo_s <= 0) intervalo_s = 5;
    if (timeout_s <= 0) timeout_s = 15;
    if (timeout_s < intervalo_s * 2) timeout_s = intervalo_s * 3; // timeout >= 3*interval

    pthread_mutex_lock(&_membresia_mutex);
    _heartbeat_intervalo_s = intervalo_s;
    _heartbeat_timeout_s = timeout_s;
    _ultimo_tick_heartbeat_s = (int)time(NULL);
    pthread_mutex_unlock(&_membresia_mutex);
    return 0;
}

// --- Tick del heartbeat: verifica latidos y purga nodos caídos ---
// tiempo_actual_s: timestamp UNIX actual en segundos
// Retorna cantidad de nodos purgados
int cluster_tick_heartbeat(int tiempo_actual_s) {
    if (!_descubrimiento_inicializado) return -1;
    if (tiempo_actual_s <= 0) tiempo_actual_s = (int)time(NULL);

    pthread_mutex_lock(&_membresia_mutex);

    int purgados = 0;
    for (int i = 0; i < _num_nodos_membresia; i++) {
        if (_tabla_membresia[i].estado == 1) { // VIVO
            int edad = tiempo_actual_s - _tabla_membresia[i].ultimo_latido_s;
            if (edad >= _heartbeat_timeout_s) {
                _tabla_membresia[i].estado = 3; // MUERTO
                purgados++;
            } else if (edad >= _heartbeat_timeout_s / 2) {
                _tabla_membresia[i].estado = 2; // SOSPECHOSO
            }
        }
    }

    _ultimo_tick_heartbeat_s = tiempo_actual_s;
    pthread_mutex_unlock(&_membresia_mutex);
    return purgados;
}

// --- Registrar un heartbeat recibido de un nodo ---
// Retorna 0 si ok, -1 si nodo no encontrado
int cluster_recibir_heartbeat(CadenaSegura id) {
    if (!_descubrimiento_inicializado || !id.datos) return -1;

    pthread_mutex_lock(&_membresia_mutex);
    int idx = _buscar_nodo_por_id(id.datos);
    if (idx < 0) {
        pthread_mutex_unlock(&_membresia_mutex);
        return -1;
    }
    _tabla_membresia[idx].estado = 1; // VIVO
    _tabla_membresia[idx].ultimo_latido_s = (int)time(NULL);
    _tabla_membresia[idx].num_heartbeats++;
    pthread_mutex_unlock(&_membresia_mutex);
    return 0;
}

// --- Generar paquete de descubrimiento (SYNCLUSTER announcement) ---
// Formato: "SYNCLUSTER:id:ip:puerto:pubkey_hex"
// Retorna el paquete como CadenaSegura (heap-allocated, caller debe liberar)
CadenaSegura cluster_generar_anuncio(CadenaSegura id, CadenaSegura ip, int puerto, CadenaSegura pubkey) {
    if (!id.datos || !ip.datos || puerto <= 0)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    char buf[512];
    const char* pk = pubkey.datos ? pubkey.datos : "";
    int len = snprintf(buf, sizeof(buf), "%s:%s:%s:%d:%s",
                       DESCUBRIMIENTO_MAGIC, id.datos, ip.datos, puerto, pk);
    if (len < 0 || len >= (int)sizeof(buf))
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(result, buf, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = len, .datos = result };
}

// --- Procesar paquete de descubrimiento entrante ---
// Formato esperado: "SYNCLUSTER:id:ip:puerto:pubkey_hex"
// Retorna 0 si se procesó correctamente, -1 si es inválido
int cluster_procesar_anuncio(CadenaSegura paquete) {
    if (!paquete.datos || paquete.longitud <= (int)strlen(DESCUBRIMIENTO_MAGIC))
        return -1;

    // Verify magic prefix
    if (strncmp(paquete.datos, DESCUBRIMIENTO_MAGIC, strlen(DESCUBRIMIENTO_MAGIC)) != 0)
        return -2;

    // Parse: SYNCLUSTER:id:ip:puerto:pubkey
    const char* p = paquete.datos + strlen(DESCUBRIMIENTO_MAGIC) + 1;

    // Extract id (up to next ':')
    const char* id_start = p;
    while (*p && *p != ':') p++;
    if (!*p) return -3;
    int id_len = (int)(p - id_start);
    if (id_len <= 0 || id_len >= MAX_ID_LEN) return -3;

    // Extract ip (up to next ':')
    p++; // skip ':'
    const char* ip_start = p;
    while (*p && *p != ':') p++;
    if (!*p) return -4;
    int ip_len = (int)(p - ip_start);
    if (ip_len <= 0 || ip_len >= MAX_IP_LEN) return -4;

    // Extract puerto (up to next ':')
    p++; // skip ':'
    int puerto = 0;
    while (*p && *p != ':') {
        puerto = puerto * 10 + (*p - '0');
        p++;
    }
    if (puerto <= 0 || puerto > 65535) return -5;

    // Extract pubkey (rest of string)
    const char* pubkey_start = p + 1; // skip ':' or end of string
    int pubkey_len = (int)(paquete.datos + paquete.longitud - pubkey_start);
    if (pubkey_len < 0) pubkey_len = 0;

    // Build temporary strings for registration
    char id_buf[MAX_ID_LEN];
    char ip_buf[MAX_IP_LEN];
    char pk_buf[MAX_PUBKEY_LEN];

    memcpy(id_buf, id_start, (size_t)id_len);
    id_buf[id_len] = '\0';

    memcpy(ip_buf, ip_start, (size_t)ip_len);
    ip_buf[ip_len] = '\0';

    if (pubkey_len > 0 && pubkey_len < MAX_PUBKEY_LEN) {
        memcpy(pk_buf, pubkey_start, (size_t)pubkey_len);
        pk_buf[pubkey_len] = '\0';
    } else {
        pk_buf[0] = '\0';
    }

    CadenaSegura cid = { .longitud = id_len, .datos = id_buf };
    CadenaSegura cip = { .longitud = ip_len, .datos = ip_buf };
    CadenaSegura cpk = { .longitud = pubkey_len, .datos = pk_buf };

    int rc = cluster_registrar_nodo(cid, cip, puerto, cpk);
    return (rc >= 0) ? 0 : -6;
}

// --- Generar representación textual de la tabla de membresía ---
// Formato: "nodo1|nodo2|..." donde cada nodo es "id:ip:puerto:estado"
CadenaSegura cluster_info_membresia_como_texto(void) {
    if (!_descubrimiento_inicializado)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    pthread_mutex_lock(&_membresia_mutex);

    // Calculate total size needed
    int total = 0;
    for (int i = 0; i < _num_nodos_membresia; i++) {
        total += (int)strlen(_tabla_membresia[i].id) + 1 +
                 (int)strlen(_tabla_membresia[i].ip) + 1 + 6 + 1 + 1; // :ip:puerto:estado|
    }
    if (total <= 0) {
        pthread_mutex_unlock(&_membresia_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    char* result = (char*)pool_alloc((size_t)(total + 1));
    if (!result) {
        pthread_mutex_unlock(&_membresia_mutex);
        return (CadenaSegura){ .longitud = 0, .datos = NULL };
    }

    int pos = 0;
    for (int i = 0; i < _num_nodos_membresia; i++) {
        NodoClusterMembresia* n = &_tabla_membresia[i];
        int nlen = snprintf(result + pos, (size_t)(total - pos + 1),
                            "%s:%s:%d:%d|",
                            n->id, n->ip, n->puerto, n->estado);
        if (nlen > 0) pos += nlen;
    }
    result[pos] = '\0';

    pthread_mutex_unlock(&_membresia_mutex);
    return (CadenaSegura){ .longitud = pos, .datos = result };
}

// --- Verificar salud de un nodo específico ---
// Retorna: 1=VIVO, 2=SOSPECHOSO, 3=MUERTO, -1=desconocido
int cluster_verificar_salud_nodo(CadenaSegura id) {
    if (!_descubrimiento_inicializado || !id.datos) return -1;

    pthread_mutex_lock(&_membresia_mutex);
    int idx = _buscar_nodo_por_id(id.datos);
    if (idx < 0) {
        pthread_mutex_unlock(&_membresia_mutex);
        return -1;
    }
    int estado = _tabla_membresia[idx].estado;
    pthread_mutex_unlock(&_membresia_mutex);
    return estado;
}

// --- Obtener timestamp del último tick de heartbeat ---
int cluster_ultimo_tick_heartbeat(void) {
    return _ultimo_tick_heartbeat_s;
}

// --- Obtener configuración de heartbeat ---
// Retorna "intervalo:timeout"
CadenaSegura cluster_info_heartbeat(void) {
    char buf[64];
    int len = snprintf(buf, sizeof(buf), "%d:%d", _heartbeat_intervalo_s, _heartbeat_timeout_s);
    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(result, buf, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = len, .datos = result };
}

// ============================================================
// M8.6 — UDP Multicast Real para Auto-Descubrimiento en Red
// ============================================================
// Conecta cluster_generar_anuncio / cluster_procesar_anuncio
// con sockets UDP reales mediante multicast.
// Grupo por defecto: 239.255.0.1:9700
// ============================================================

#define SYNAPSE_MC_GRUPO "239.255.0.1"
#define SYNAPSE_MC_PUERTO 9700

static int _cluster_mc_sock = -1;
static char _cluster_mc_grupo[32];
static int _cluster_mc_puerto = SYNAPSE_MC_PUERTO;
static volatile int _hilo_descubrimiento_activo = 0;
static pthread_t _hilo_descubrimiento_tid;

// --- Inicializar socket multicast y unirse al grupo ---
// grupo: "239.255.0.1" por defecto
// Retorna fd del socket, o -1 si error
int cluster_multicast_iniciar(const char* grupo, int puerto) {
    if (!grupo) grupo = SYNAPSE_MC_GRUPO;
    if (puerto <= 0) puerto = SYNAPSE_MC_PUERTO;

    strncpy(_cluster_mc_grupo, grupo, sizeof(_cluster_mc_grupo) - 1);
    _cluster_mc_grupo[sizeof(_cluster_mc_grupo) - 1] = '\0';
    _cluster_mc_puerto = puerto;

    if (_cluster_mc_sock >= 0) {
        return _cluster_mc_sock;
    }

    _syn_iniciar_red();

    int fd = (int)socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) return -1;

    int opt = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));

#ifdef SO_REUSEPORT
    setsockopt(fd, SOL_SOCKET, SO_REUSEPORT, (const char*)&opt, sizeof(opt));
#endif

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)puerto);
    addr.sin_addr.s_addr = htonl(INADDR_ANY);

    if (bind(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
#ifdef _WIN32
        closesocket(fd);
#else
        close(fd);
#endif
        return -2;
    }

    struct ip_mreq mreq;
    memset(&mreq, 0, sizeof(mreq));
    mreq.imr_multiaddr.s_addr = inet_addr(grupo);
    mreq.imr_interface.s_addr = htonl(INADDR_ANY);

    if (setsockopt(fd, IPPROTO_IP, IP_ADD_MEMBERSHIP,
                   (const char*)&mreq, sizeof(mreq)) < 0) {
#ifdef _WIN32
        closesocket(fd);
#else
        close(fd);
#endif
        return -3;
    }

#ifdef _WIN32
    u_long mode = 1;
    ioctlsocket(fd, FIONBIO, &mode);
#else
    int flags = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);
#endif

    _cluster_mc_sock = fd;
    return fd;
}

// --- Salir del grupo multicast y cerrar socket ---
int cluster_multicast_detener(void) {
    if (_cluster_mc_sock < 0) return 0;

    struct ip_mreq mreq;
    memset(&mreq, 0, sizeof(mreq));
    mreq.imr_multiaddr.s_addr = inet_addr(_cluster_mc_grupo);
    mreq.imr_interface.s_addr = htonl(INADDR_ANY);
    setsockopt(_cluster_mc_sock, IPPROTO_IP, IP_DROP_MEMBERSHIP,
               (const char*)&mreq, sizeof(mreq));

#ifdef _WIN32
    closesocket(_cluster_mc_sock);
#else
    close(_cluster_mc_sock);
#endif
    _cluster_mc_sock = -1;
    return 0;
}

// --- Enviar anuncio SYNCLUSTER al grupo multicast ---
int cluster_anunciar_por_multicast(CadenaSegura id, CadenaSegura ip_host,
                                    int puerto_host, CadenaSegura pubkey) {
    if (_cluster_mc_sock < 0) return -1;
    if (!id.datos || !ip_host.datos || puerto_host <= 0) return -2;

    CadenaSegura anuncio = cluster_generar_anuncio(id, ip_host, puerto_host, pubkey);
    if (!anuncio.datos || anuncio.longitud <= 0) return -3;

    struct sockaddr_in dest;
    memset(&dest, 0, sizeof(dest));
    dest.sin_family = AF_INET;
    dest.sin_port = htons((unsigned short)_cluster_mc_puerto);
    dest.sin_addr.s_addr = inet_addr(_cluster_mc_grupo);

    int n = (int)sendto(_cluster_mc_sock, anuncio.datos, (size_t)anuncio.longitud, 0,
                        (struct sockaddr*)&dest, sizeof(dest));

    return (n > 0) ? 0 : -4;
}

// --- Recibir y procesar un paquete multicast ---
// timeout_ms: tiempo máximo de espera en ms (0 = no bloqueante)
// Retorna: 0 si se procesó un anuncio, 1 si no hay datos, -1 si error
int cluster_escuchar_multicast(int timeout_ms) {
    if (_cluster_mc_sock < 0) return -1;

    if (timeout_ms > 0) {
#ifdef _WIN32
        u_long mode = 0;
        ioctlsocket(_cluster_mc_sock, FIONBIO, &mode);
        struct timeval tv;
        tv.tv_sec = timeout_ms / 1000;
        tv.tv_usec = (timeout_ms % 1000) * 1000;
        fd_set fds;
        FD_ZERO(&fds);
        FD_SET(_cluster_mc_sock, &fds);
        int sr = select(0, &fds, NULL, NULL, &tv);
        if (sr <= 0) {
            u_long nb = 1;
            ioctlsocket(_cluster_mc_sock, FIONBIO, &nb);
            return (sr == 0) ? 1 : -2;
        }
#else
        struct timeval tv;
        tv.tv_sec = timeout_ms / 1000;
        tv.tv_usec = (timeout_ms % 1000) * 1000;
        fd_set fds;
        FD_ZERO(&fds);
        FD_SET(_cluster_mc_sock, &fds);
        int sr = select(_cluster_mc_sock + 1, &fds, NULL, NULL, &tv);
        if (sr <= 0) return (sr == 0) ? 1 : -2;
#endif
    }

    char buf[65536];
    struct sockaddr_in from;
    socklen_t fromlen = sizeof(from);
    int n = (int)recvfrom(_cluster_mc_sock, buf, sizeof(buf) - 1, 0,
                          (struct sockaddr*)&from, &fromlen);

    if (n <= 0) {
#ifdef _WIN32
        u_long mode = 1;
        ioctlsocket(_cluster_mc_sock, FIONBIO, &mode);
#endif
        return 1;
    }

    buf[n] = '\0';
    CadenaSegura paquete = { .longitud = n, .datos = buf };
    int rc = cluster_procesar_anuncio(paquete);

#ifdef _WIN32
    u_long mode = 1;
    ioctlsocket(_cluster_mc_sock, FIONBIO, &mode);
#endif

    return (rc == 0) ? 0 : -3;
}

// --- Argumentos para el hilo de descubrimiento ---
typedef struct {
    char id[MAX_ID_LEN];
    char ip[MAX_IP_LEN];
    int puerto;
    char pubkey[MAX_PUBKEY_LEN];
    int intervalo_s;
} HiloDescubrimientoArgs;

// --- Función del hilo de descubrimiento en segundo plano ---
static void* _hilo_descubrimiento_func(void* arg) {
    HiloDescubrimientoArgs* args = (HiloDescubrimientoArgs*)arg;

    CadenaSegura id = { .longitud = (int)strlen(args->id), .datos = args->id };
    CadenaSegura ip = { .longitud = (int)strlen(args->ip), .datos = args->ip };
    CadenaSegura pk = { .longitud = (int)strlen(args->pubkey), .datos = args->pubkey };

    while (_hilo_descubrimiento_activo) {
        cluster_anunciar_por_multicast(id, ip, args->puerto, pk);

        for (int i = 0; i < 5; i++) {
            int rc = cluster_escuchar_multicast(200);
            if (rc != 0 && rc != -3) break;
        }

        for (int s = 0; s < args->intervalo_s && _hilo_descubrimiento_activo; s++) {
#ifdef _WIN32
            Sleep(1000);
#else
            sleep(1);
#endif
        }
    }

    free(args);
    return NULL;
}

// --- Iniciar hilo de descubrimiento activo en segundo plano ---
int cluster_iniciar_hilo_descubrimiento(CadenaSegura id, CadenaSegura ip_host,
                                         int puerto_host, CadenaSegura pubkey,
                                         int intervalo_s) {
    if (_hilo_descubrimiento_activo) return -1;
    if (!id.datos || !ip_host.datos || puerto_host <= 0) return -2;
    if (intervalo_s < 1) intervalo_s = 5;

    _hilo_descubrimiento_activo = 1;

    HiloDescubrimientoArgs* args = (HiloDescubrimientoArgs*)malloc(sizeof(HiloDescubrimientoArgs));
    if (!args) { _hilo_descubrimiento_activo = 0; return -3; }

    strncpy(args->id, id.datos, MAX_ID_LEN - 1);
    args->id[MAX_ID_LEN - 1] = '\0';
    strncpy(args->ip, ip_host.datos, MAX_IP_LEN - 1);
    args->ip[MAX_IP_LEN - 1] = '\0';
    args->puerto = puerto_host;
    if (pubkey.datos) {
        strncpy(args->pubkey, pubkey.datos, MAX_PUBKEY_LEN - 1);
        args->pubkey[MAX_PUBKEY_LEN - 1] = '\0';
    } else {
        args->pubkey[0] = '\0';
    }
    args->intervalo_s = intervalo_s;

    pthread_create(&_hilo_descubrimiento_tid, NULL,
                   _hilo_descubrimiento_func, args);
    pthread_detach(_hilo_descubrimiento_tid);

    return 0;
}

// --- Detener hilo de descubrimiento activo ---
int cluster_detener_hilo_descubrimiento(void) {
    _hilo_descubrimiento_activo = 0;
    return 0;
}

// --- Verificar si el hilo de descubrimiento está activo ---
int cluster_hilo_descubrimiento_activo(void) {
    return _hilo_descubrimiento_activo ? 1 : 0;
}

// --- Consultar grupo multicast configurado ---
CadenaSegura cluster_multicast_info(void) {
    char buf[128];
    int len = snprintf(buf, sizeof(buf), "%s:%d:%d",
                       _cluster_mc_grupo, _cluster_mc_puerto, _cluster_mc_sock);
    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(result, buf, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = len, .datos = result };
}

// ============================================================
// M9.4 — Distributed Multi-Node Debugging
// ============================================================
// Extiende tr_* / rp_* / ms_* para operación en clúster.
// Permite agregación remota de trazas, breakpoints distribuidos
// y correlación cronológica entre nodos del clúster M8.x.
// ============================================================

#define DD_MAX_REMOTE_NODES 16
#define DD_MAX_REMOTE_EVENTS 2048
#define DD_PROTO_MAGIC "SYNDBG"

typedef struct {
    int nodo_id;
    char ip[48];
    int puerto;
    int num_eventos;
    int ultima_sincro_s;
    char eventos[DD_MAX_REMOTE_EVENTS][256]; // serialized event strings
    int activo;
} NodoRemotoDebug;

static int _dd_local_nodo_id = -1;
static int _dd_inicializado = 0;
static int _dd_total_remotos = 0;
static int _dd_ultima_sincro = 0;
static NodoRemotoDebug _dd_nodos_remotos[DD_MAX_REMOTE_NODES];
static pthread_mutex_t _dd_mutex = PTHREAD_MUTEX_INITIALIZER;

// --- Inicializar subsistema de debug distribuido ---
// nodo_id: identificador único de este nodo en el clúster
int dd_inicializar(int nodo_id) {
    pthread_mutex_lock(&_dd_mutex);
    _dd_local_nodo_id = nodo_id;
    _dd_inicializado = 1;
    _dd_total_remotos = 0;
    _dd_ultima_sincro = (int)time(NULL);
    memset(_dd_nodos_remotos, 0, sizeof(_dd_nodos_remotos));
    pthread_mutex_unlock(&_dd_mutex);
    return 0;
}

// --- Registrar un nodo remoto para debug distribuido ---
int dd_registrar_nodo_remoto(int nodo_id, CadenaSegura ip, int puerto) {
    if (!_dd_inicializado || !ip.datos || puerto <= 0) return -1;

    pthread_mutex_lock(&_dd_mutex);

    // Check if already registered
    for (int i = 0; i < _dd_total_remotos; i++) {
        if (_dd_nodos_remotos[i].nodo_id == nodo_id) {
            // Update IP/port
            strncpy(_dd_nodos_remotos[i].ip, ip.datos, sizeof(_dd_nodos_remotos[i].ip) - 1);
            _dd_nodos_remotos[i].puerto = puerto;
            _dd_nodos_remotos[i].activo = 1;
            _dd_nodos_remotos[i].ultima_sincro_s = (int)time(NULL);
            pthread_mutex_unlock(&_dd_mutex);
            return i;
        }
    }

    if (_dd_total_remotos >= DD_MAX_REMOTE_NODES) {
        pthread_mutex_unlock(&_dd_mutex);
        return -2;
    }

    int idx = _dd_total_remotos++;
    _dd_nodos_remotos[idx].nodo_id = nodo_id;
    strncpy(_dd_nodos_remotos[idx].ip, ip.datos, sizeof(_dd_nodos_remotos[idx].ip) - 1);
    _dd_nodos_remotos[idx].ip[sizeof(_dd_nodos_remotos[idx].ip) - 1] = '\0';
    _dd_nodos_remotos[idx].puerto = puerto;
    _dd_nodos_remotos[idx].num_eventos = 0;
    _dd_nodos_remotos[idx].activo = 1;
    _dd_nodos_remotos[idx].ultima_sincro_s = (int)time(NULL);

    pthread_mutex_unlock(&_dd_mutex);
    return idx;
}

// --- Serializar y enviar traza local a nodo remoto ---
// Envía los últimos num_eventos eventos de la traza local al nodo remoto
// Formato: "SYNDBG:TRACE:origen_id:num_eventos:evt1|evt2|..."
int dd_enviar_traza_remota(CadenaSegura ip, int puerto, int num_eventos) {
    if (!_dd_inicializado || !ip.datos || puerto <= 0) return -1;
    if (num_eventos <= 0) num_eventos = tr_total_eventos();
    if (num_eventos > 100) num_eventos = 100; // limit payload size

    // Build trace payload from local tr_* events
    char buf[4096];
    int pos = snprintf(buf, sizeof(buf), "%s:TRACE:%d:%d:",
                       DD_PROTO_MAGIC, _dd_local_nodo_id, num_eventos);

    for (int i = 0; i < num_eventos && pos < (int)sizeof(buf) - 100; i++) {
        int idx = tr_total_eventos() - num_eventos + i;
        if (idx < 0) continue;
        CadenaSegura evt = tr_obtener_evento(idx);
        if (evt.datos && evt.longitud > 0) {
            int n = snprintf(buf + pos, (size_t)(sizeof(buf) - pos),
                             "%s|", evt.datos);
            if (n > 0) pos += n;
        }
    }

    // Send via cluster remote channel
    int rc = cluster_canal_remoto_enviar(ip.datos, puerto, buf, pos, 0);
    return (rc >= 0) ? 0 : -2;
}

// --- Recibir y procesar traza remota ---
// Procesa un paquete SYNDBG:TRACE entrante y lo almacena en el buffer
// de eventos remotos del nodo correspondiente.
// Retorna 0 si se procesó, -1 si no es un paquete debug válido
int dd_recibir_traza_remota(CadenaSegura paquete) {
    if (!_dd_inicializado || !paquete.datos || paquete.longitud <= 0) return -1;

    // Verify magic prefix
    if (strncmp(paquete.datos, DD_PROTO_MAGIC, strlen(DD_PROTO_MAGIC)) != 0)
        return -2;

    // Parse: SYNDBG:TRACE:origen_id:num_eventos:evt1|evt2|...
    const char* p = paquete.datos + strlen(DD_PROTO_MAGIC) + 1;

    // Expect TRACE command
    if (strncmp(p, "TRACE", 5) != 0) return -3;
    p += 6; // skip "TRACE:"

    // Parse origin node ID
    int origen_id = 0;
    while (*p && *p != ':') { origen_id = origen_id * 10 + (*p - '0'); p++; }
    if (!*p) return -4;
    p++; // skip ':'

    // Parse num events
    int num_evt = 0;
    while (*p && *p != ':') { num_evt = num_evt * 10 + (*p - '0'); p++; }
    if (!*p) return -5;
    p++; // skip ':'

    // Find remote node entry or create it
    pthread_mutex_lock(&_dd_mutex);
    int idx = -1;
    for (int i = 0; i < _dd_total_remotos; i++) {
        if (_dd_nodos_remotos[i].nodo_id == origen_id) {
            idx = i;
            break;
        }
    }
    if (idx < 0 && _dd_total_remotos < DD_MAX_REMOTE_NODES) {
        idx = _dd_total_remotos++;
        _dd_nodos_remotos[idx].nodo_id = origen_id;
        strncpy(_dd_nodos_remotos[idx].ip, "", 1);
        _dd_nodos_remotos[idx].puerto = 0;
        _dd_nodos_remotos[idx].num_eventos = 0;
        _dd_nodos_remotos[idx].activo = 1;
    }

    if (idx < 0) {
        pthread_mutex_unlock(&_dd_mutex);
        return -6;
    }

    // Parse event strings into buffer
    int evt_idx = 0;
    const char* evt_start = p;
    while (*p && evt_idx < DD_MAX_REMOTE_EVENTS && evt_idx < num_evt) {
        const char* end = p;
        while (*end && *end != '|') end++;
        int len = (int)(end - p);
        if (len > 0 && len < 255 && evt_idx < DD_MAX_REMOTE_EVENTS) {
            memcpy(_dd_nodos_remotos[idx].eventos[evt_idx], p, (size_t)len);
            _dd_nodos_remotos[idx].eventos[evt_idx][len] = '\0';
            evt_idx++;
        }
        p = (*end == '|') ? end + 1 : end;
    }
    _dd_nodos_remotos[idx].num_eventos = evt_idx;
    _dd_nodos_remotos[idx].ultima_sincro_s = (int)time(NULL);
    _dd_ultima_sincro = (int)time(NULL);

    pthread_mutex_unlock(&_dd_mutex);
    return 0;
}

// --- Sincronizar trazas con todos los nodos remotos registrados ---
// Envía la traza local a cada nodo remoto
int dd_sincronizar_trazas(int num_eventos) {
    if (!_dd_inicializado) return -1;

    pthread_mutex_lock(&_dd_mutex);
    int count = 0;
    for (int i = 0; i < _dd_total_remotos; i++) {
        if (_dd_nodos_remotos[i].activo) {
            CadenaSegura ip = {
                .longitud = (int)strlen(_dd_nodos_remotos[i].ip),
                .datos = _dd_nodos_remotos[i].ip
            };
            pthread_mutex_unlock(&_dd_mutex);
            int rc = dd_enviar_traza_remota(ip, _dd_nodos_remotos[i].puerto, num_eventos);
            pthread_mutex_lock(&_dd_mutex);
            if (rc == 0) count++;
        }
    }
    _dd_ultima_sincro = (int)time(NULL);
    pthread_mutex_unlock(&_dd_mutex);
    return count;
}

// --- Buscar evento en trazas remotas por tag ---
// Busca en todos los buffers remotos el último evento con el tag especificado
// Retorna "nodo_id:evento" o vacío si no se encuentra
CadenaSegura dd_buscar_evento_remoto(int tag, int desde_secuencia) {
    if (!_dd_inicializado)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    pthread_mutex_lock(&_dd_mutex);

    for (int n = _dd_total_remotos - 1; n >= 0; n--) {
        if (!_dd_nodos_remotos[n].activo) continue;
        for (int e = _dd_nodos_remotos[n].num_eventos - 1; e >= 0; e--) {
            const char* evt = _dd_nodos_remotos[n].eventos[e];
            if (!evt || !*evt) continue;
            // Event format: "tag|seq|funcion|linea|variable|valor"
            int evt_tag = 0;
            const char* p = evt;
            while (*p && *p != '|') { evt_tag = evt_tag * 10 + (*p - '0'); p++; }
            if (evt_tag == tag) {
                char result[512];
                int len = snprintf(result, sizeof(result), "%d:%s",
                                   _dd_nodos_remotos[n].nodo_id, evt);
                char* r = (char*)pool_alloc((size_t)(len + 1));
                if (!r) { pthread_mutex_unlock(&_dd_mutex); return (CadenaSegura){0, NULL}; }
                memcpy(r, result, (size_t)(len + 1));
                pthread_mutex_unlock(&_dd_mutex);
                return (CadenaSegura){ .longitud = len, .datos = r };
            }
        }
    }

    pthread_mutex_unlock(&_dd_mutex);
    return (CadenaSegura){ .longitud = 0, .datos = NULL };
}

// --- RPC: Establecer breakpoint remoto ---
// Envía comando SYNDBG:BP a nodo remoto
int dd_breakpoint_remoto(CadenaSegura ip, int puerto, int tipo, CadenaSegura patron, int valor_int) {
    if (!_dd_inicializado || !ip.datos || puerto <= 0) return -1;

    char buf[1024];
    const char* pt = patron.datos ? patron.datos : "";
    int len = snprintf(buf, sizeof(buf), "%s:BP:%d:%s:%d",
                       DD_PROTO_MAGIC, tipo, pt, valor_int);

    return cluster_canal_remoto_enviar(ip.datos, puerto, buf, len, 0);
}

// --- RPC: Inspeccionar variable en nodo remoto ---
// Envía comando SYNDBG:INSPECT y retorna el resultado (simulado)
CadenaSegura dd_inspeccionar_remoto(CadenaSegura ip, int puerto, CadenaSegura nombre_variable) {
    if (!_dd_inicializado || !ip.datos || puerto <= 0 || !nombre_variable.datos)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    // Build remote inspection request
    char buf[1024];
    int len = snprintf(buf, sizeof(buf), "%s:INSPECT:%.*s",
                       DD_PROTO_MAGIC, (int)nombre_variable.longitud, nombre_variable.datos);
    int rc = cluster_canal_remoto_enviar(ip.datos, puerto, buf, len, 0);
    if (rc < 0) return (CadenaSegura){ .longitud = 0, .datos = NULL };

    // For simulation: look up in local remote buffer
    // In real scenario, response comes via dd_recibir_traza_remota
    char result[128];
    int rlen = snprintf(result, sizeof(result), "remote_inspect:%d:%.*s",
                        _dd_local_nodo_id, (int)nombre_variable.longitud, nombre_variable.datos);
    char* r = (char*)pool_alloc((size_t)(rlen + 1));
    if (!r) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(r, result, (size_t)(rlen + 1));
    return (CadenaSegura){ .longitud = rlen, .datos = r };
}

// --- RPC: Obtener pila de llamadas remota ---
CadenaSegura dd_pila_remota(CadenaSegura ip, int puerto) {
    if (!_dd_inicializado || !ip.datos || puerto <= 0)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    char buf[256];
    int len = snprintf(buf, sizeof(buf), "%s:STACK:", DD_PROTO_MAGIC);
    int rc = cluster_canal_remoto_enviar(ip.datos, puerto, buf, len, 0);
    if (rc < 0) return (CadenaSegura){ .longitud = 0, .datos = NULL };

    char result[256];
    int rlen = snprintf(result, sizeof(result), "remote_stack:%d", _dd_local_nodo_id);
    char* r = (char*)pool_alloc((size_t)(rlen + 1));
    if (!r) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(r, result, (size_t)(rlen + 1));
    return (CadenaSegura){ .longitud = rlen, .datos = r };
}

// --- Total de eventos remotos recibidos ---
int dd_total_eventos_remotos(void) {
    if (!_dd_inicializado) return 0;

    pthread_mutex_lock(&_dd_mutex);
    int total = 0;
    for (int i = 0; i < _dd_total_remotos; i++) {
        total += _dd_nodos_remotos[i].num_eventos;
    }
    pthread_mutex_unlock(&_dd_mutex);
    return total;
}

// --- Número de nodos remotos registrados ---
int dd_nodos_remotos_registrados(void) {
    if (!_dd_inicializado) return 0;
    pthread_mutex_lock(&_dd_mutex);
    int n = _dd_total_remotos;
    pthread_mutex_unlock(&_dd_mutex);
    return n;
}

// --- Identificador del nodo local ---
int dd_nodo_local_id(void) {
    return _dd_local_nodo_id;
}

// --- Información del subsistema de debug distribuido ---
// Retorna "local_id:num_remotos:total_eventos_remotos:ultima_sincro"
CadenaSegura dd_info(void) {
    if (!_dd_inicializado)
        return (CadenaSegura){ .longitud = 0, .datos = NULL };

    char buf[256];
    int total_evt = 0;
    pthread_mutex_lock(&_dd_mutex);
    for (int i = 0; i < _dd_total_remotos; i++) {
        total_evt += _dd_nodos_remotos[i].num_eventos;
    }
    int len = snprintf(buf, sizeof(buf), "%d:%d:%d:%d",
                       _dd_local_nodo_id, _dd_total_remotos,
                       total_evt, _dd_ultima_sincro);
    pthread_mutex_unlock(&_dd_mutex);

    char* result = (char*)pool_alloc((size_t)(len + 1));
    if (!result) return (CadenaSegura){ .longitud = 0, .datos = NULL };
    memcpy(result, buf, (size_t)(len + 1));
    return (CadenaSegura){ .longitud = len, .datos = result };
}
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
