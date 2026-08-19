// runtime/core/json.c — std.json: Deterministic JSON Parser
// D-9(d) corte 7: extraído de synapse_rt.c (lines 72-461, byte-identical)
// Manual 5 §7: std.json (Deserializador Determinista, arquitectura simdjson-style)
//
// Arquitectura simdjson-style: arena contigua + strings in-place.
// Sin malloc por clave/nodo. Arena unica liberada al final.

#include "runtime/core/json.h"

// SIMD intrinsics (only needed when __AVX2__ is active)
#ifdef __AVX2__
#include <immintrin.h>
#endif

// ============================================================
// std.json — JSON Parser (Deserializador Determinista)
// ============================================================

// --- Arena (contiguous bump allocator) ---

static NodoJson* _json_arena = NULL;
static int _json_arena_pos = 0;

__attribute__((unused))
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