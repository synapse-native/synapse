// runtime/core/json.c — std.json: Deterministic JSON Parser + Serializer
// D-9(d) corte 7: extraído de synapse_rt.c (lines 72-461, byte-identical)
// Manual 5 §7: std.json (Deserializador Determinista, arquitectura simdjson-style)
// Manual 3 §12.2: a_texto — serializador determinista NodoJson → CadenaSegura
//
// Arquitectura simdjson-style: arena contigua + strings in-place.
// Sin malloc por clave/nodo. Arena unica liberada al final.

#include "json.h"

#ifndef JSON_MAX_NODES
#define JSON_MAX_NODES 65536
#endif
extern void* pool_alloc(size_t size);
extern void  pool_free(void* p);

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

#define _JSON_INPUT_CAP (16 * 1024 * 1024)
static char _p_input_buf[_JSON_INPUT_CAP];
static CadenaSegura _p_input;
static int _p_pos;

void _json_init(CadenaSegura s) {
    // cumple Manual 4 §2.1: el input se copia a un buffer estatico (_p_input_buf).
    // El llamador (Synapse RAII) puede liberar el buffer original al pasarlo a
    // desde_texto (move semantics), y el pool reusaria esa region durante el
    // parseo (corrompiendo _p_input). Un buffer estatico nunca se libera ni se
    // reusa, asi que el parseo es estable y single-threaded (LSP: 1 mensaje a la vez).
    int n = s.longitud;
    if (n < 0) n = 0;
    if (n > _JSON_INPUT_CAP - 1) n = _JSON_INPUT_CAP - 1;
    memcpy(_p_input_buf, s.datos, (size_t)n);
    _p_input_buf[n] = '\0';
    _p_input.datos = _p_input_buf;
    _p_input.longitud = n;
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
        NodoJson* new = (NodoJson*)malloc((size_t)(a->cap * sizeof(NodoJson)));
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
        ParJson* new = (ParJson*)malloc((size_t)(a->cap * sizeof(ParJson)));
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
#ifdef __AVX2__
static void _skip_ws() {
    while (_p_pos + 32 <= _p_input.longitud) {
        __m256i chunk = _mm256_loadu_si256((const __m256i*)(_p_input.datos + _p_pos));
        __m256i cmp_space = _mm256_cmpeq_epi8(chunk, _mm256_set1_epi8(' '));
        __m256i cmp_tab   = _mm256_cmpeq_epi8(chunk, _mm256_set1_epi8('\t'));
        __m256i cmp_nl    = _mm256_cmpeq_epi8(chunk, _mm256_set1_epi8('\n'));
        __m256i cmp_cr    = _mm256_cmpeq_epi8(chunk, _mm256_set1_epi8('\r'));
        __m256i ws = _mm256_or_si256(_mm256_or_si256(cmp_space, cmp_tab),
                                     _mm256_or_si256(cmp_nl, cmp_cr));
        int mask = _mm256_movemask_epi8(ws);
        if (mask == (int)0xFFFFFFFF) {
            _p_pos += 32;
        } else {
            int ws_count = __builtin_ctz(~(unsigned int)mask);
            _p_pos += ws_count;
            return;
        }
    }
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

// cumple Manual 4 §2.1: las cadenas del parse se COPIAN al pool, desacoplando
// el arbol NodoJson del buffer de entrada (que Synapse RAII libera via pool_free).
// Sin esto, msg.valor_str.datos queda colgado tras liberar `body` (use-after-free).
static CadenaSegura _json_str_copy(const char* p, int len) {
    if (len < 0) len = 0;
    char* dup = (char*)pool_alloc((size_t)(len + 1));
    if (!dup) return (CadenaSegura){0};
    memcpy(dup, p, (size_t)len);
    dup[len] = '\0';
    return (CadenaSegura){ .longitud = len, .datos = dup };
}

// --- String parser ---

#ifdef __AVX2__
static CadenaSegura _parse_string_value() {
    if (_advance() != '"') return (CadenaSegura){0};
    int start = _p_pos;
    __m256i quote = _mm256_set1_epi8('"');
    __m256i bslash = _mm256_set1_epi8('\\');
    while (_p_pos + 32 <= _p_input.longitud) {
        __m256i chunk = _mm256_loadu_si256((const __m256i*)(_p_input.datos + _p_pos));
        __m256i cmp_q = _mm256_cmpeq_epi8(chunk, quote);
        __m256i cmp_b = _mm256_cmpeq_epi8(chunk, bslash);
        __m256i special = _mm256_or_si256(cmp_q, cmp_b);
        int mask = _mm256_movemask_epi8(special);
        if (mask != 0) {
            int pos = __builtin_ctz((unsigned int)mask);
            _p_pos += pos;
            if (_p_input.datos[_p_pos] == '\\') {
                _p_pos += 2;
            } else {
                int len = _p_pos - start;
                _p_pos++;
                return _json_str_copy((char*)_p_input.datos + start, len);
            }
        } else {
            _p_pos += 32;
        }
    }
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
    return _json_str_copy((char*)_p_input.datos + start, len);
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
    return _json_str_copy((char*)_p_input.datos + start, len);
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
    if (len > 63) return 0.0f;
    memcpy(buf, _p_input.datos + start, len);
    buf[len] = '\0';
    float val = (float)strtod(buf, NULL);
    return val;
}

// Forward declaration
static NodoJson _parse_value();

/* cumple Manual 4 §2.1: parse stack para preservar punteros ParArr en recursión. */
/* FIX: parse-stack to preserve ParArr pointers across recursive _parse_value() calls.
 * The local variable `pares` lives on the stack; the compiler may reuse the same
 * stack slot when _parse_value() → _parse_object() recurses, clobbering the parent's
 * pointer. Saving/restoring through this static array avoids the bug.
 * LSP is single-threaded and JSON depth < 64, so this is safe. */
static ParArr* _parse_par_stack[64];
static int _parse_par_sp = 0;

static NodoJson _parse_object() {
    NodoJson n = {0};
    n.tipo = 5;
    _advance();
    _skip_ws();
    if (_peek() == '}') { _advance(); return n; }
    /* cumple Manual 4 §2.1: malloc evita bug de reuso de slabs en pool_alloc. */
    /* FIX: use malloc for ParArr to avoid pool slab reuse bug returning same addr */
    ParArr* pares = (ParArr*)malloc(sizeof(ParArr));
    if (pares) { memset(pares, 0, sizeof(ParArr)); } else { static ParArr _fb; pares = &_fb; }
    int _my_sp = _parse_par_sp;
    _parse_par_stack[_parse_par_sp++] = pares;
    while (1) {
        _skip_ws();
        if (_peek() == '}') break;
        pares = _parse_par_stack[_my_sp];  /* restore after potential recursion */
        if (pares->count > 0) {
            if (_peek() != ',') break;
            _advance();
            _skip_ws();
        }
        CadenaSegura key = _parse_string_value();
        if (key.datos == NULL) {
            _parse_par_sp = _my_sp;
            n.tipo = -1;
            n.valor_str = (CadenaSegura){ .longitud = 27, .datos = "fjson: clave de objeto invalida" };
            return n;
        }
        _skip_ws();
        if (_advance() != ':') {
            _parse_par_sp = _my_sp;
            n.tipo = -1;
            n.valor_str = (CadenaSegura){ .longitud = 25, .datos = "fjson: se esperaba ':'" };
            return n;
        }
        NodoJson val = _parse_value();
        if (val.tipo < 0) {
            _parse_par_sp = _my_sp;
            _json_nodo_liberar(val);
            return val;
        }
        pares = _parse_par_stack[_my_sp];  /* restore after recursion */
        NodoJson* val_ptr = (NodoJson*)pool_alloc(sizeof(NodoJson));
        if (val_ptr) *val_ptr = val;
        par_arr_append(pares, key, val_ptr);
    }
    pares = _parse_par_stack[--_parse_par_sp];  /* restore and pop */
    _skip_ws();
    if (_peek() == '}') _advance();
    n.longitud = pares->count;
    n.objeto_pares = par_arr_detach(pares);
    return n;
}

static NodoJson _parse_array() {
    NodoJson n = {0};
    n.tipo = 4;
    _advance();
    _skip_ws();
    if (_peek() == ']') { _advance(); return n; }
    /* cumple Manual 4 §2.1: malloc evita stack slot reuse en recursión. */
    /* FIX: allocate NodoArr on pool to avoid stack slot reuse during recursion */
    NodoArr* arr = (NodoArr*)malloc(sizeof(NodoArr));
    if (arr) { memset(arr, 0, sizeof(NodoArr)); } else { static NodoArr _fb; arr = &_fb; }
    int _my_sp = _parse_par_sp;
    _parse_par_stack[_parse_par_sp++] = (ParArr*)arr;  /* reuse the same safe stack */
    while (1) {
        _skip_ws();
        if (_peek() == ']') break;
        arr = (NodoArr*)_parse_par_stack[_my_sp];  /* restore after recursion */
        if (arr->count > 0) {
            if (_peek() != ',') break;
            _advance();
            _skip_ws();
        }
        NodoJson val = _parse_value();
        if (val.tipo < 0) {
            _parse_par_sp = _my_sp;
            _json_nodo_liberar(val);
            return val;
        }
        arr = (NodoArr*)_parse_par_stack[_my_sp];  /* restore after recursion */
        nodo_arr_append(arr, val);
    }
    arr = (NodoArr*)_parse_par_stack[--_parse_par_sp];  /* restore and pop */
    _skip_ws();
    if (_peek() == ']') _advance();
    n.longitud = arr->count;
    n.arreglo_hijos = nodo_arr_detach(arr);
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
    if (resultado.tipo < 0) {
        _json_nodo_liberar(resultado); return resultado;
    }
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
// Serializador: NodoJson → CadenaSegura (JSON texto)
// Manual 3 §12.2: a_texto — genera JSON determinista desde un arbol NodoJson
// ============================================================

// Buffer temporal para serializacion (recursivo, sin malloc por nodo).
// Max 64KB — suficiente para JSON de hasta ~16K campos.
#define _SER_BUF_SIZE (64 * 1024)

static char _ser_buf[_SER_BUF_SIZE];
static int _ser_pos;

static void _ser_emit(const char* s, int len) {
    if (_ser_pos + len <= _SER_BUF_SIZE) {
        memcpy(_ser_buf + _ser_pos, s, len);
        _ser_pos += len;
    }
}

static void _ser_char(char c) {
    if (_ser_pos < _SER_BUF_SIZE) {
        _ser_buf[_ser_pos++] = c;
    }
}

// Forward declaration
static void _serializar_nodo(NodoJson nodo);

// Escapa una cadena: copia caracteres especiales con backslash
static void _serializar_cadena(CadenaSegura s) {
    _ser_char('"');
    for (int i = 0; i < s.longitud; i++) {
        char c = s.datos[i];
        switch (c) {
            case '"':  _ser_emit("\\\"", 2); break;
            case '\\': _ser_emit("\\\\", 2); break;
            case '\n': _ser_emit("\\n", 2); break;
            case '\r': _ser_emit("\\r", 2); break;
            case '\t': _ser_emit("\\t", 2); break;
            default:
                if ((unsigned char)c < 0x20) {
                    char hex[8];
                    int n = snprintf(hex, sizeof(hex), "\\u%04x", (unsigned char)c);
                    _ser_emit(hex, n);
                } else {
                    _ser_char(c);
                }
                break;
        }
    }
    _ser_char('"');
}

// Serializa un numero float → string con formato determinista
static void _serializar_numero(float val) {
    char buf[64];
    // Usar %g para formato compacto (sin ceros innecesarios)
    int n = snprintf(buf, sizeof(buf), "%g", (double)val);
    _ser_emit(buf, n);
}

static void _serializar_nodo(NodoJson nodo) {
    switch (nodo.tipo) {
        case -1: // Error → null como fallback
            _ser_emit("null", 4);
            break;
        case 0: // Null
            _ser_emit("null", 4);
            break;
        case 1: // Booleano
            if (nodo.valor_bool)
                _ser_emit("true", 4);
            else
                _ser_emit("false", 5);
            break;
        case 2: // Numero
            _serializar_numero(nodo.valor_num);
            break;
        case 3: // Cadena
            _serializar_cadena(nodo.valor_str);
            break;
        case 4: // Arreglo
            _ser_char('[');
            for (int i = 0; i < nodo.longitud; i++) {
                if (i > 0) _ser_char(',');
                _serializar_nodo(nodo.arreglo_hijos[i]);
            }
            _ser_char(']');
            break;
        case 5: // Objeto
            _ser_char('{');
            for (int i = 0; i < nodo.longitud; i++) {
                if (i > 0) _ser_char(',');
                _serializar_cadena(nodo.objeto_pares[i].clave);
                _ser_char(':');
                _serializar_nodo(*nodo.objeto_pares[i].valor);
            }
            _ser_char('}');
            break;
        default:
            _ser_emit("null", 4);
            break;
    }
}

// cumple Manual 4 §2.1 + H-SEC-1/ME-SEC-1: no devolver el buffer estático
// _ser_buf (compartido, no thread/fiber-safe, use-after-overwrite). Se copia
// a pool_alloc para que el llamador (Synapse RAII) lo libere con pool_free.
CadenaSegura _json_a_texto(NodoJson nodo) {
    _ser_pos = 0;
    _serializar_nodo(nodo);
    // Null-terminate
    if (_ser_pos < _SER_BUF_SIZE) {
        _ser_buf[_ser_pos] = '\0';
    }
    int n = _ser_pos;
    if (n > _SER_BUF_SIZE - 1) n = _SER_BUF_SIZE - 1;
    char* dup = (char*)pool_alloc((size_t)(n + 1));
    if (!dup) return (CadenaSegura){0, ""};
    memcpy(dup, _ser_buf, (size_t)n);
    dup[n] = '\0';
    return (CadenaSegura){ .longitud = n, .datos = dup };
}
