// salida_metal.c - Generado por Synapse Compilador
// Lenguaje: Synapse v1.0 (#lang: es)
#pragma GCC diagnostic ignored "-Wint-to-pointer-cast"
#pragma GCC diagnostic ignored "-Wdiscarded-qualifiers"

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <pthread.h>
#include <string.h>
#include <assert.h>
#ifdef _WIN32
#include <io.h>
#else
#include <dirent.h>
#endif

typedef struct { int longitud; const char* datos; } CadenaSegura;

typedef struct { uint32_t filas; uint32_t columnas; float* datos; int es_mapeado; } Tensor;

typedef struct { FILE* stream; int es_valido; int es_virtual; const char* virtual_data; int virtual_len; } Canal;

#define nulo ((void*)0)
#define verdadero 1
#define falso 0

// --- OO AST node types ---
struct Token;
struct Nodo;
struct ListaNodo;
struct Programa;
struct Identificador;
struct LiteralNumero;
struct LiteralCadena;
struct OpBinaria;
struct OpUnaria;
struct LlamadaFuncion;
struct ExprAccesoCampo;
struct AsignacionVariable;
struct AsignacionCampo;
struct SentenciaSi;
struct SentenciaMientras;
struct SentenciaRetornar;
struct SentenciaExpr;
struct LogLlamada;
struct Parametro;
struct ListaParametro;
struct DefinicionFuncion;
struct DefinicionEstructura;
struct SentenciaRomper;
struct SentenciaSiguiente;
struct SentenciaLanzar;
struct SentenciaRecuperar;
struct SentenciaEscuchar;
struct ExprTensor;
struct ExprIndice;
struct ArgumentoTransferido;
struct SentenciaImportar;
struct ImportarC;
struct DeclaracionExterna;
struct DeclaracionVariable;
struct BloqueInseguro;
struct ExprObtenerDireccion;
struct ExprDereferencia;

typedef struct Token { int tipo; CadenaSegura lexema; int linea; int columna; } Token;
typedef struct Nodo { CadenaSegura tipo; } Nodo;
typedef struct ListaNodo { struct Nodo* cabeza; struct ListaNodo* cola; } ListaNodo;
typedef struct Programa { CadenaSegura tipo; struct ListaNodo* sentencias; } Programa;

#define POOL_BLOQUES 64
#define TAMANO_BLOQUE 4096

#include "librerias/embedded_libs.h"

// --- TokenID + NodoID canonicos (D-9(e), Manual 2 2.3/7.2) ---
// Fuente unica: nucleo/parser_constantes.syn
// Header generado: runtime/core/ast_nodos.h (scripts/gen_ast_nodos_h.py)
#include "runtime/core/ast_nodos.h"

// --- Error code constants (Manual 3 §3.5) ---
#ifndef ERR_CANONICAL_FORMAT
#define ERR_CANONICAL_FORMAT (13LL)
#endif
#ifndef ERR_DEP_NOT_DECLARED
#define ERR_DEP_NOT_DECLARED (28LL)
#endif
#ifndef ERR_FILE_NOT_FOUND
#define ERR_FILE_NOT_FOUND (12LL)
#endif
#ifndef ERR_GIT_FAILURE
#define ERR_GIT_FAILURE (30LL)
#endif
#ifndef ERR_INDENT_INCONSISTENT
#define ERR_INDENT_INCONSISTENT (8LL)
#endif
#ifndef ERR_INDENT_INVALID
#define ERR_INDENT_INVALID (7LL)
#endif
#ifndef ERR_LANG_MISSING
#define ERR_LANG_MISSING (5LL)
#endif
#ifndef ERR_LANG_UNSUPPORTED
#define ERR_LANG_UNSUPPORTED (6LL)
#endif
#ifndef ERR_LEX
#define ERR_LEX (11LL)
#endif
#ifndef ERR_LEX_CHAR_UNEXPECTED
#define ERR_LEX_CHAR_UNEXPECTED (10LL)
#endif
#ifndef ERR_LOCK_HASH_MISMATCH
#define ERR_LOCK_HASH_MISMATCH (29LL)
#endif
#ifndef ERR_MANIFEST_NOT_FOUND
#define ERR_MANIFEST_NOT_FOUND (25LL)
#endif
#ifndef ERR_MEM_BORROW_CONFLICT
#define ERR_MEM_BORROW_CONFLICT (39LL)
#endif
#ifndef ERR_MEM_LIFETIME_CYCLE
#define ERR_MEM_LIFETIME_CYCLE (35LL)
#endif
#ifndef ERR_MEM_LIFETIME_MISMATCH
#define ERR_MEM_LIFETIME_MISMATCH (34LL)
#endif
#ifndef ERR_MODULE_AXON_NOT_FOUND
#define ERR_MODULE_AXON_NOT_FOUND (27LL)
#endif
#ifndef ERR_MODULE_STD_NOT_FOUND
#define ERR_MODULE_STD_NOT_FOUND (26LL)
#endif
#ifndef ERR_SEM_ACCESO_MEMORIA_MOVIDA
#define ERR_SEM_ACCESO_MEMORIA_MOVIDA (23LL)
#endif
#ifndef ERR_SEM_ARGUMENTOS_INVALIDOS
#define ERR_SEM_ARGUMENTOS_INVALIDOS (19LL)
#endif
#ifndef ERR_SEM_ASM_FUERA_INSEGURO
#define ERR_SEM_ASM_FUERA_INSEGURO (31LL)
#endif
#ifndef ERR_SEM_CAMPO_NO_EXISTE
#define ERR_SEM_CAMPO_NO_EXISTE (21LL)
#endif
#ifndef ERR_SEM_CONSTANTE_INMUTABLE
#define ERR_SEM_CONSTANTE_INMUTABLE (32LL)
#endif
#ifndef ERR_SEM_ESTRUCTURA_NO_DEFINIDA
#define ERR_SEM_ESTRUCTURA_NO_DEFINIDA (20LL)
#endif
#ifndef ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED
#define ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED (33LL)
#endif
#ifndef ERR_SEM_FUNC_NO_DEFINIDA
#define ERR_SEM_FUNC_NO_DEFINIDA (17LL)
#endif
#ifndef ERR_SEM_REDEFINICION
#define ERR_SEM_REDEFINICION (18LL)
#endif
#ifndef ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR
#define ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR (24LL)
#endif
#ifndef ERR_SEM_TIPO_INCOMPATIBLE
#define ERR_SEM_TIPO_INCOMPATIBLE (15LL)
#endif
#ifndef ERR_SEM_TIPO_RETORNO
#define ERR_SEM_TIPO_RETORNO (16LL)
#endif
#ifndef ERR_SEM_VAR_MOVIDA
#define ERR_SEM_VAR_MOVIDA (22LL)
#endif
#ifndef ERR_SEM_VAR_NO_DECLARADA
#define ERR_SEM_VAR_NO_DECLARADA (14LL)
#endif
#ifndef ERR_STRING_UNCLOSED
#define ERR_STRING_UNCLOSED (9LL)
#endif
#ifndef ERR_SYNTAX_EXPECTED_NEWLINE
#define ERR_SYNTAX_EXPECTED_NEWLINE (4LL)
#endif
#ifndef ERR_SYNTAX_EXPECTED_TOKEN
#define ERR_SYNTAX_EXPECTED_TOKEN (1LL)
#endif
#ifndef ERR_SYNTAX_UNEXPECTED_EXPR
#define ERR_SYNTAX_UNEXPECTED_EXPR (3LL)
#endif
#ifndef ERR_SYNTAX_UNEXPECTED_TOKEN
#define ERR_SYNTAX_UNEXPECTED_TOKEN (2LL)
#endif

// --- Constantes del programa (fuente de verdad = codigo) ---

extern char _gen_tmp_buf[4096];

extern char _G_emit_buf[1048576];
extern int _G_emit_pos;
extern FILE* _G_fp;

// ME-B4: nombres de estructuras definidas (para constructores en C nativo)
extern char _G_native_structs[256][64];
extern int _G_native_structs_count;
extern int _G_native_es_estructura(const char* n);

extern char _G_native_struct_campos[256][64][64];
extern char _G_native_struct_campos_tipo[256][64][64];
extern int _G_native_struct_campos_count[256];
extern int _G_native_campo_tipo(const char* sn, const char* cn, char* out);

// ME-B6: tipos de retorno de funciones definidas (inferencia de tipos nativa)
extern char _G_native_func_returns[2048][64];
extern int _G_native_func_returns_count;
extern int _G_native_tipo_retorno(const char* fn, char* out);

extern char _G_native_adt_ctrs[256][64];
extern char _G_native_adt_ctrs_adt[256][64];
extern int _G_native_adt_ctrs_tag[256];
extern char _G_native_adt_ctrs_tipo[256][64];
extern int _G_native_adt_ctrs_count;
extern int _G_native_es_adt_ctr(const char* c);
extern int _G_native_adt_ctr_info(const char* c, char* adt_out, int* tag_out, char* tipo_out);
extern int _G_native_adt_unwrap_tipo(const char* adt, char* tipo_out);
extern int _G_native_adt_unwrap_field(const char* adt, char* field_out);
extern char _G_native_adt_gen[64][64];
extern int _G_native_adt_gen_nparams[64];
extern char _G_native_adt_gen_params[64][8][64];
extern int _G_native_adt_gen_count;
extern int _G_native_adt_gen_es(const char* n);
extern char _G_native_adt_inst_type[64][64];
extern char _G_native_adt_inst_c[64][64];
extern char _G_native_adt_inst_base[64][64];
extern char _G_native_adt_inst_fields_c[64][8][64];
extern int _G_native_adt_inst_nfields[64];
extern int _G_native_adt_inst_count;
extern int _G_native_adt_inst_ctr(const char* base, int tag, const char* tipo_c, char* out);

// ME-B7: dedup de funciones emitidas y hoisting de variables (paridad orquestador nativo)
extern char _G_emit_func_names[2048][64];
extern int _G_emit_func_count;
extern char _G_fn_vars[2048][64];
extern int _G_fn_vars_count;
extern void* _G_fn_var_src[2048];
extern int _G_fn_var_auto[2048];
extern char _G_fn_var_tipos[2048][64];  // ME-C4: tipo inferido por hoisting
extern char _G_fn_ptr_vars[64][64];  // ME-B9.x: parametros puntero
extern int _G_fn_ptr_vars_count;
typedef struct { uint32_t ref_count; uint32_t weak_count; uint32_t version; void* data; void (*destructor)(void*); } RcHeader;
typedef struct { RcHeader* header; uint32_t version; } WeakRef;

extern void* rc_alloc(size_t tamano, void (*dtor)(void*));
extern void rc_decrementar(void* ptr);
extern void* arc_alloc(size_t tamano, void (*dtor)(void*));
extern void arc_decrementar(void* ptr);
extern WeakRef rc_weak_ref(void* ptr);
extern void rc_weak_release(WeakRef* w);

extern char _G_native_canal_names[512][64];
extern char _G_native_canal_elem[512][64];
extern int _G_native_canal_count;
extern void _G_native_canal_elem_set(const char* _cname, const char* _celem);
extern int _G_native_canal_elem_tipo(const char* _cname, char* _cout);
extern char _G_listeners[8][16384];
extern int _G_listeners_count;
extern int _G_listener_modo;
extern char _G_lanzar_wrappers[8][4096];
extern int _G_lanzar_wrappers_count;
extern int _G_lanzar_count;
extern char _G_tipo_aliases[128][64];
extern char _G_tipo_aliases_base[128][64];
extern int _G_tipo_aliases_count;
extern int _G_parse_error;

extern int _G_indent;

const char* _G_mt(const char* st);
void _G_vest(struct DefinicionEstructura* n);

#define TAG_OK 0
#define TAG_ERR 1
#define TAG_ALGUNO 0
#define TAG_NINGUNO 1

// --- Helpers de serialización primitiva ---
static inline void* _synapse_box_int(int64_t v) { return (void*)(intptr_t)v; }
static inline int64_t _synapse_unbox_int(void* p) { return (int64_t)(intptr_t)p; }
static inline void* _synapse_box_float(double v) {
    double* _p = (double*)malloc(sizeof(double));
    if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo\\n"); exit(1); }
    *_p = v;
    return (void*)_p;
}
static inline double _synapse_unbox_float(void* p) {
    double _v = *(double*)p;
    free(p);
    return _v;
}

extern void pool_init(uint32_t total_blocks, uint32_t block_size);
extern void pool_free(void* ptr);
extern void* pool_alloc(size_t size);
extern void pool_destroy(void);
extern void escribir(CadenaSegura contenido);
extern void escribir_linea(CadenaSegura contenido);
extern CadenaSegura leer_linea(void);
extern Canal abrir(CadenaSegura ruta, CadenaSegura modo);
extern CadenaSegura leer(Canal canal);
extern void cerrar_archivo(Canal canal);
extern Tensor crear_tensor(int filas, int columnas);
extern Tensor suma_tensor(Tensor a, Tensor b);
extern Tensor producto_punto(Tensor a, Tensor b);
extern Tensor relu(Tensor a);
extern Tensor reserva(int tamano);
extern void libera(Tensor bloque);
extern Tensor suma(Tensor a, Tensor b);
extern Tensor producto(Tensor a, Tensor b);
extern int64_t texto_a_entero(CadenaSegura str);
extern double texto_a_decimal(CadenaSegura str);
extern CadenaSegura decimal_a_texto(double n);
extern CadenaSegura entero_a_texto(int64_t n);
extern int str_eq(CadenaSegura a, CadenaSegura b);
extern CadenaSegura concat(CadenaSegura a, CadenaSegura b);
extern void synapse_lanzar_hilo(void* (*fn)(void*), void* arg);
extern void synapse_esperar_hilos(void);
extern void synapse_esperar_fibras(void);
extern void scheduler_iniciar(int num_hilos_os);
extern void scheduler_detener(void);
extern void fibra_crear(void (*func)(void*), void* arg, size_t stack_size);
extern void fibra_esperar(int fibra_id);
extern void fibra_terminar(void* resultado);
extern void _syn_texto_liberar(CadenaSegura s);

typedef struct { int es_ok; union {
void* ok_valor; const char* err_mensaje;
} datos; } Resultado_T;
typedef struct CanalConcurrencia CanalConcurrencia;
extern CanalConcurrencia* canal_crear(uint32_t capacidad);
extern void canal_enviar(CanalConcurrencia* canal, void* paquete);
extern void* canal_recibir(CanalConcurrencia* canal, bool* cerrado);
extern void canal_destruir(CanalConcurrencia* canal);
extern void cerrar(CanalConcurrencia* canal);
// --- Deteccion SIMD unificada (delegada al runtime synapse_rt.o) ---
extern void _simd_detectar(void);

// --- Contratos (requiere/garantiza) ---
#ifdef SYNAPSE_RELEASE
#define assert_contrato(expr, msg) ((void)0)
#else
#define assert_contrato(expr, msg) \
    do { if (!(expr)) { \
        fprintf(stderr, "CONTRATO: %s en %%s:%%d\\n", \
                msg, __FILE__, __LINE__); \
        exit(1); }} while(0)
#endif

char _gen_tmp_buf[4096];

char _G_emit_buf[1048576];
int _G_emit_pos;
FILE* _G_fp;
int _G_scope_depth;
int _G_scope_vars_depth[256];
char _G_scope_vars_names[256][64];
int _G_scope_vars_total;
int _G_safe_mode;  // M22.5: --safe flag for lifetime assertions
char _G_native_structs[256][64];
int _G_native_structs_count;
int _G_native_es_estructura(const char* n) {
    if (!n) return 0;
    for (int _i = 0; _i < _G_native_structs_count; _i++) {
        if (strcmp(_G_native_structs[_i], n) == 0) return 1;
    }
    return 0;
}

char _G_native_struct_campos[256][64][64];
char _G_native_struct_campos_tipo[256][64][64];
int _G_native_struct_campos_count[256];
int _G_native_campo_tipo(const char* sn, const char* cn, char* out) {
    if (!sn || !cn || !out) return 0;
    for (int _i = 0; _i < _G_native_structs_count; _i++) {
        if (strcmp(_G_native_structs[_i], sn) == 0) {
            for (int _j = 0; _j < _G_native_struct_campos_count[_i]; _j++) {
                if (strcmp(_G_native_struct_campos[_i][_j], cn) == 0) {
                    strcpy(out, _G_native_struct_campos_tipo[_i][_j]); return 1;
                }
            }
        }
    }
    return 0;
}

char _G_native_func_returns[2048][64];
int _G_native_func_returns_count;
int _G_native_tipo_retorno(const char* fn, char* out) {
    if (!fn || !out) return 0;
    for (int _i = 0; _i < _G_native_func_returns_count; _i++) {
        if (strcmp(_G_native_func_returns[_i], fn) == 0) {
            strcpy(out, _G_native_func_returns[_i + 1024]); return 1;
        }
    }
    return 0;
}

char _G_native_adt_ctrs[256][64];
char _G_native_adt_ctrs_adt[256][64];
int _G_native_adt_ctrs_tag[256];
char _G_native_adt_ctrs_tipo[256][64];
int _G_native_adt_ctrs_count;
int _G_native_es_adt_ctr(const char* c) {
    if (!c) return 0;
    for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {
        if (strcmp(_G_native_adt_ctrs[_i], c) == 0) return 1;
    }
    return 0;
}
int _G_native_adt_ctr_info(const char* c, char* adt_out, int* tag_out, char* tipo_out) {
    if (!c) return 0;
    for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {
        if (strcmp(_G_native_adt_ctrs[_i], c) == 0) {
            if (adt_out) strcpy(adt_out, _G_native_adt_ctrs_adt[_i]);
            if (tag_out) *tag_out = _G_native_adt_ctrs_tag[_i];
            if (tipo_out) strcpy(tipo_out, _G_native_adt_ctrs_tipo[_i]);
            return 1;
        }
    }
    return 0;
}
int _G_native_adt_unwrap_tipo(const char* adt, char* tipo_out) {
    if (!adt || !tipo_out) return 0;
    for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {
        if (_G_native_adt_ctrs_tag[_i] == 0 && strcmp(_G_native_adt_ctrs_adt[_i], adt) == 0) {
            strcpy(tipo_out, _G_native_adt_ctrs_tipo[_i]);
            return 1;
        }
    }
    return 0;
}
int _G_native_adt_unwrap_field(const char* adt, char* field_out) {
    if (!adt || !field_out) return 0;
    // D-2: normalizar la base de una instanciacion (Resultado<entero,texto> -> Resultado)
    char _ab[64]; int _ai = 0; for (; adt[_ai] && adt[_ai] != '<' && _ai < 62; _ai++) _ab[_ai] = adt[_ai]; _ab[_ai] = 0;
    for (int _i = 0; _i < _G_native_adt_ctrs_count; _i++) {
        if (_G_native_adt_ctrs_tag[_i] == 0 && strcmp(_G_native_adt_ctrs_adt[_i], _ab) == 0) {
            strcpy(field_out, _G_native_adt_ctrs[_i]);
            return 1;
        }
    }
    return 0;
}

char _G_native_adt_gen[64][64];
int _G_native_adt_gen_nparams[64];
char _G_native_adt_gen_params[64][8][64];
int _G_native_adt_gen_count;
int _G_native_adt_gen_es(const char* n) {
    if (!n) return 0;
    for (int _i = 0; _i < _G_native_adt_gen_count; _i++) { if (strcmp(_G_native_adt_gen[_i], n) == 0) return 1; }
    return 0;
}
char _G_native_adt_inst_type[64][64];
char _G_native_adt_inst_c[64][64];
char _G_native_adt_inst_base[64][64];
char _G_native_adt_inst_fields_c[64][8][64];
int _G_native_adt_inst_nfields[64];
int _G_native_adt_inst_count;
int _G_native_adt_inst_ctr(const char* base, int tag, const char* tipo_c, char* out) {
    if (!base || !out) return 0;
    int _solo = 1; int _ns = 0; for (int _j = 0; _j < _G_native_adt_inst_count; _j++) { if (strcmp(_G_native_adt_inst_base[_j], base) == 0) { _ns++; } }
    if (_ns == 1) _solo = 1; else _solo = 0;
    for (int _i = 0; _i < _G_native_adt_inst_count; _i++) {
        if (strcmp(_G_native_adt_inst_base[_i], base) != 0) continue;
        if (_solo) { strcpy(out, _G_native_adt_inst_c[_i]); return 1; }
        if (tag < _G_native_adt_inst_nfields[_i] && tipo_c && _G_native_adt_inst_fields_c[_i][tag][0] && strcmp(_G_native_adt_inst_fields_c[_i][tag], tipo_c) == 0) { strcpy(out, _G_native_adt_inst_c[_i]); return 1; }
    }
    return 0;
}

char _G_emit_func_names[2048][64];
int _G_emit_func_count;
char _G_fn_vars[2048][64];
int _G_fn_vars_count;
void* _G_fn_var_src[2048];
int _G_fn_var_auto[2048];
char _G_fn_var_tipos[2048][64];  // ME-C4: tipo inferido por hoisting
char _G_fn_ptr_vars[64][64];  // ME-B9.x: parametros puntero
int _G_fn_ptr_vars_count;
char _G_native_canal_names[512][64];
char _G_native_canal_elem[512][64];
int _G_native_canal_count;
void _G_native_canal_elem_set(const char* _cname, const char* _celem) {
    if (!_cname || !_celem) return;
    for (int _ci = 0; _ci < _G_native_canal_count; _ci++) { if (strcmp(_G_native_canal_names[_ci], _cname) == 0) { strncpy(_G_native_canal_elem[_ci], _celem, 63); _G_native_canal_elem[_ci][63] = 0; return; } }
    if (_G_native_canal_count < 512) { strncpy(_G_native_canal_names[_G_native_canal_count], _cname, 63); _G_native_canal_names[_G_native_canal_count][63] = 0; strncpy(_G_native_canal_elem[_G_native_canal_count], _celem, 63); _G_native_canal_elem[_G_native_canal_count][63] = 0; _G_native_canal_count++; }
}
int _G_native_canal_elem_tipo(const char* _cname, char* _cout) {
    if (!_cname || !_cout) return 0;
    for (int _ci = 0; _ci < _G_native_canal_count; _ci++) { if (strcmp(_G_native_canal_names[_ci], _cname) == 0) { strncpy(_cout, _G_native_canal_elem[_ci], 63); _cout[63] = 0; return 1; } }
    return 0;
}
char _G_listeners[8][16384];
int _G_listeners_count;
int _G_listener_modo;
char _G_lanzar_wrappers[8][4096];
int _G_lanzar_wrappers_count;
int _G_lanzar_count;

char _G_tipo_aliases[128][64];
char _G_tipo_aliases_base[128][64];
int _G_tipo_aliases_count;
int _G_parse_error = 0;


int _g_argc;
char** _g_argv;
int _argc() { return _g_argc; }

CadenaSegura _argv(int i) {
    if (i < 0 || i >= _g_argc) return (CadenaSegura){0, ""};
    return (CadenaSegura){ .longitud = (int)strlen(_g_argv[i]), .datos = _g_argv[i] };
}

void salir(int codigo) { exit(codigo); }

struct NodoJson;
struct Opcion;
struct ParJson;
struct Resultado;

typedef struct NodoJson {
    int64_t tipo;
    int64_t valor_bool;
    double valor_num;
    CadenaSegura valor_str;
    struct NodoJson* arreglo_hijos;
    struct ParJson* objeto_pares;
    int64_t longitud;
} NodoJson;

typedef struct Opcion {
    int tag;
    union {
        int64_t valor;
        CadenaSegura valor_str;
        double valor_float;
    } dato;
} Opcion;

typedef struct ParJson {
    CadenaSegura clave;
    struct NodoJson* valor;
} ParJson;

typedef struct Resultado {
    int tag;
    union {
        int64_t valor;
        CadenaSegura valor_str;
        double valor_float;
    } dato;
} Resultado;

static inline int risky_call(void) { return 0; }
CadenaSegura _validar_ruta_segura(CadenaSegura ruta);
CadenaSegura a_texto(int64_t valor);
CadenaSegura a_texto_decimal(double valor);
int64_t atoi_f(CadenaSegura texto);
int64_t cmp_texto(CadenaSegura a, CadenaSegura b);
CadenaSegura construir_error_r(int64_t id, int64_t codigo, CadenaSegura mensaje);
CadenaSegura construir_notificacion_r(CadenaSegura metodo, CadenaSegura params);
CadenaSegura construir_respuesta_r(int64_t id, CadenaSegura resultado);
int64_t contiene(CadenaSegura texto, CadenaSegura subcadena);
struct NodoJson desde_texto(CadenaSegura entrada);
int64_t ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica);
int64_t ejecutar_comando(CadenaSegura cmd);
int64_t eliminar_archivo(CadenaSegura ruta);
void enviar_respuesta_r(CadenaSegura respuesta);
CadenaSegura escapar_json(CadenaSegura texto);
int64_t escribir_archivo(CadenaSegura ruta, CadenaSegura contenido);
int existe_archivo(CadenaSegura ruta);
void handle_code_action_r(int64_t id, CadenaSegura params);
void handle_completion_r(int64_t id, CadenaSegura params);
void handle_definition_r(int64_t id, CadenaSegura uri, CadenaSegura params);
void handle_did_change_configuration_r(CadenaSegura params);
CadenaSegura handle_did_close_r(CadenaSegura uri_ref, CadenaSegura params);
CadenaSegura handle_did_open_r(CadenaSegura uri_ref, CadenaSegura params);
void handle_formatting_r(int64_t id, CadenaSegura params);
void handle_hover_r(int64_t id, CadenaSegura params);
void handle_initialize_r(int64_t id);
void handle_shutdown_r(int64_t id);
void handle_signature_help_r(int64_t id, CadenaSegura params);
void handle_unknown_r(int64_t id);
int64_t indice_de(CadenaSegura texto, CadenaSegura subcadena);
CadenaSegura json_string_r(CadenaSegura valor);
CadenaSegura leer_archivo(CadenaSegura ruta);
CadenaSegura leer_bytes(int64_t cantidad);
void liberar_nodo(struct NodoJson n);
CadenaSegura mayusculas(CadenaSegura texto);
CadenaSegura minusculas(CadenaSegura texto);
struct NodoJson obtener_campo(struct NodoJson nodo, CadenaSegura clave);
struct NodoJson obtener_elemento(struct NodoJson nodo, int64_t indice);
CadenaSegura obtener_env(CadenaSegura nombre);
CadenaSegura recortar(CadenaSegura texto);
CadenaSegura reemplazar(CadenaSegura texto, CadenaSegura buscar, CadenaSegura reemplazar);
CadenaSegura sha256_texto(CadenaSegura datos);
int64_t strchr_f(CadenaSegura texto, int64_t caracter);
CadenaSegura strcpy_f(CadenaSegura texto);
int64_t strlen_s(CadenaSegura a);
CadenaSegura strncpy_f(CadenaSegura texto, int64_t max_len);
int64_t strstr_f(CadenaSegura texto, CadenaSegura patron);
int64_t termina_con(CadenaSegura texto, CadenaSegura sufijo);

extern CadenaSegura _syn_sha256_texto(CadenaSegura datos);
extern int64_t _syn_ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica);
extern CadenaSegura _syn_normalizar_ruta(CadenaSegura ruta);
extern CadenaSegura _syn_obtener_cwd(void);
extern int64_t _syn_ruta_en_directorio(CadenaSegura ruta, CadenaSegura dir);
extern int64_t _syn_ejecutar_comando(CadenaSegura cmd);
extern int64_t _syn_escribir_archivo(CadenaSegura ruta, CadenaSegura contenido);
extern CadenaSegura _syn_leer_archivo(CadenaSegura ruta);
extern CadenaSegura _syn_obtener_env(CadenaSegura nombre);
extern int64_t _syn_existe_archivo(CadenaSegura ruta);
extern int64_t _syn_eliminar_archivo(CadenaSegura ruta);
extern void cerrar_archivo(Canal c);
extern Canal _syn_abrir(CadenaSegura ruta, CadenaSegura modo);
extern CadenaSegura _syn_leer(Canal c);
extern void _syn_escribir(CadenaSegura texto);
extern void _syn_escribir_linea(CadenaSegura texto);
extern CadenaSegura _syn_leer_linea(void);
extern CadenaSegura _syn_leer_bytes(int64_t cantidad);
extern int64_t _syn_fgetc_stdin(void);
extern int64_t _syn_fprintf(int64_t canalm, CadenaSegura formato);
extern int64_t _syn_fprintf_i(int64_t canalm, CadenaSegura formato, int64_t valor);
extern int64_t _syn_fprintf_it(int64_t canalm, CadenaSegura formato, int64_t val1, CadenaSegura val2);
extern void _syn_fflush(int64_t canalm);
extern void _syn_setbuf_null(int64_t canalm);
extern int64_t _syn_texto_contiene(CadenaSegura texto, CadenaSegura subcadena);
extern int64_t _syn_texto_indice_de(CadenaSegura texto, CadenaSegura subcadena);
extern CadenaSegura _syn_texto_reemplazar(CadenaSegura texto, CadenaSegura buscar, CadenaSegura reemplazar);
extern int64_t _syn_texto_termina_con(CadenaSegura texto, CadenaSegura sufijo);
extern CadenaSegura _syn_texto_recortar(CadenaSegura texto);
extern CadenaSegura _syn_texto_mayusculas(CadenaSegura texto);
extern CadenaSegura _syn_texto_minusculas(CadenaSegura texto);
extern CadenaSegura _syn_escapar_json(CadenaSegura texto);
extern CadenaSegura _syn_a_texto_entero(int64_t valor);
extern CadenaSegura _syn_a_texto_decimal(double valor);
extern int64_t _syn_strcmp(CadenaSegura a, CadenaSegura b);
extern int64_t _syn_strlen(CadenaSegura a);
extern int64_t _syn_strstr(CadenaSegura texto, CadenaSegura patron);
extern int64_t _syn_strchr(CadenaSegura texto, int64_t caracter);
extern int64_t _syn_atoi(CadenaSegura texto);
extern CadenaSegura _syn_strcpy(CadenaSegura texto);
extern CadenaSegura _syn_strncpy(CadenaSegura texto, int64_t max_len);
extern struct NodoJson _json_parse(CadenaSegura entrada);
extern struct NodoJson _json_nodo_new(void);
extern void _json_nodo_liberar(struct NodoJson n);
extern struct NodoJson _json_array_get(struct NodoJson nodo, int64_t indice);
extern struct NodoJson _json_object_get(struct NodoJson nodo, CadenaSegura clave);
extern CadenaSegura _json_a_texto(struct NodoJson nodo);
CadenaSegura _validar_ruta_segura(CadenaSegura ruta) {
    CadenaSegura normalizada = {0};
    CadenaSegura cwd = {0};
    _syn_texto_liberar(normalizada);
    normalizada = _syn_normalizar_ruta(ruta);
    _syn_texto_liberar(cwd);
    cwd = _syn_obtener_cwd();
    if ((!_syn_ruta_en_directorio(normalizada, cwd))) {
        _syn_texto_liberar(ruta);
        _syn_texto_liberar(normalizada);
        _syn_texto_liberar(cwd);
        return (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
          /* [Lifetime Scope: exit depth=1] */
    }
    return normalizada;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura a_texto(int64_t valor) {
    return _syn_a_texto_entero(valor);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura a_texto_decimal(double valor) {
    return _syn_a_texto_decimal(valor);
      /* [Lifetime Scope: exit depth=0] */
}

int64_t atoi_f(CadenaSegura texto) {
    _syn_texto_liberar(texto);
    return _syn_atoi(texto);
      /* [Lifetime Scope: exit depth=0] */
}

int64_t cmp_texto(CadenaSegura a, CadenaSegura b) {
    _syn_texto_liberar(b);
    _syn_texto_liberar(a);
    return _syn_strcmp(a, b);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura construir_error_r(int64_t id, int64_t codigo, CadenaSegura mensaje) {
    _syn_texto_liberar(mensaje);
    return concat(concat(concat(concat(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"jsonrpc\":\"2.0\",\"id\":"), .datos = "{\"jsonrpc\":\"2.0\",\"id\":" }, a_texto(id)), (CadenaSegura){ .longitud = (int)strlen(",\"error\":{\"code\":"), .datos = ",\"error\":{\"code\":" }), a_texto(codigo)), (CadenaSegura){ .longitud = (int)strlen(",\"message\":\""), .datos = ",\"message\":\"" }), mensaje), (CadenaSegura){ .longitud = (int)strlen("\"}}"), .datos = "\"}}" });
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura construir_notificacion_r(CadenaSegura metodo, CadenaSegura params) {
    _syn_texto_liberar(params);
    _syn_texto_liberar(metodo);
    return concat(concat(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"jsonrpc\":\"2.0\",\"method\":\""), .datos = "{\"jsonrpc\":\"2.0\",\"method\":\"" }, metodo), (CadenaSegura){ .longitud = (int)strlen("\",\"params\":"), .datos = "\",\"params\":" }), params), (CadenaSegura){ .longitud = (int)strlen("}"), .datos = "}" });
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura construir_respuesta_r(int64_t id, CadenaSegura resultado) {
    _syn_texto_liberar(resultado);
    return concat(concat(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"jsonrpc\":\"2.0\",\"id\":"), .datos = "{\"jsonrpc\":\"2.0\",\"id\":" }, a_texto(id)), (CadenaSegura){ .longitud = (int)strlen(",\"result\":"), .datos = ",\"result\":" }), resultado), (CadenaSegura){ .longitud = (int)strlen("}"), .datos = "}" });
      /* [Lifetime Scope: exit depth=0] */
}

int64_t contiene(CadenaSegura texto, CadenaSegura subcadena) {
    _syn_texto_liberar(texto);
    _syn_texto_liberar(subcadena);
    return _syn_texto_contiene(texto, subcadena);
      /* [Lifetime Scope: exit depth=0] */
}

struct NodoJson desde_texto(CadenaSegura entrada) {
    _syn_texto_liberar(entrada);
    return _json_parse(entrada);
      /* [Lifetime Scope: exit depth=0] */
}

int64_t ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica) {
    _syn_texto_liberar(mensaje);
    _syn_texto_liberar(firma);
    _syn_texto_liberar(clave_publica);
    return _syn_ed25519_verificar(mensaje, firma, clave_publica);
      /* [Lifetime Scope: exit depth=0] */
}

int64_t ejecutar_comando(CadenaSegura cmd) {
    _syn_texto_liberar(cmd);
    return _syn_ejecutar_comando(cmd);
      /* [Lifetime Scope: exit depth=0] */
}

int64_t eliminar_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = {0};
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        _syn_texto_liberar(ruta_segura);
        _syn_texto_liberar(ruta);
        return (-1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    return _syn_eliminar_archivo(ruta_segura);
      /* [Lifetime Scope: exit depth=0] */
}

void enviar_respuesta_r(CadenaSegura respuesta) {
    int64_t len = strlen_s(respuesta);
    CadenaSegura header = concat(concat((CadenaSegura){ .longitud = (int)strlen("Content-Length: "), .datos = "Content-Length: " }, a_texto(len)), (CadenaSegura){ .longitud = (int)strlen("\r\n\r\n"), .datos = "\r\n\r\n" });
    escribir(header);
    escribir(respuesta);
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(respuesta);
    _syn_texto_liberar(header);
}

CadenaSegura escapar_json(CadenaSegura texto) {
    _syn_texto_liberar(texto);
    return _syn_escapar_json(texto);
      /* [Lifetime Scope: exit depth=0] */
}

int64_t escribir_archivo(CadenaSegura ruta, CadenaSegura contenido) {
    CadenaSegura ruta_segura = {0};
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        _syn_texto_liberar(ruta_segura);
        _syn_texto_liberar(ruta);
        _syn_texto_liberar(contenido);
        return (-1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    return _syn_escribir_archivo(ruta_segura, contenido);
      /* [Lifetime Scope: exit depth=0] */
}

int existe_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = {0};
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        _syn_texto_liberar(ruta_segura);
        _syn_texto_liberar(ruta);
        return 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    return (_syn_existe_archivo(ruta_segura) == 1LL);
      /* [Lifetime Scope: exit depth=0] */
}

void handle_code_action_r(int64_t id, CadenaSegura params) {
    enviar_respuesta_r(construir_respuesta_r(id, (CadenaSegura){ .longitud = (int)strlen("[]"), .datos = "[]" }));
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(params);
}

void handle_completion_r(int64_t id, CadenaSegura params) {
    CadenaSegura items = (CadenaSegura){ .longitud = (int)strlen("[{\"label\":\"funcion\",\"kind\":14},{\"label\":\"retorno\",\"kind\":14},{\"label\":\"si\",\"kind\":14},{\"label\":\"mientras\",\"kind\":14}]"), .datos = "[{\"label\":\"funcion\",\"kind\":14},{\"label\":\"retorno\",\"kind\":14},{\"label\":\"si\",\"kind\":14},{\"label\":\"mientras\",\"kind\":14}]" };
    enviar_respuesta_r(construir_respuesta_r(id, concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"isIncomplete\":false,\"items\":"), .datos = "{\"isIncomplete\":false,\"items\":" }, items), (CadenaSegura){ .longitud = (int)strlen("}"), .datos = "}" })));
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(params);
    _syn_texto_liberar(items);
}

void handle_definition_r(int64_t id, CadenaSegura uri, CadenaSegura params) {
    CadenaSegura result = concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"uri\":"), .datos = "{\"uri\":" }, json_string_r(uri)), (CadenaSegura){ .longitud = (int)strlen(",\"range\":{\"start\":{\"line\":0,\"character\":0},\"end\":{\"line\":0,\"character\":10}}}"), .datos = ",\"range\":{\"start\":{\"line\":0,\"character\":0},\"end\":{\"line\":0,\"character\":10}}}" });
    enviar_respuesta_r(construir_respuesta_r(id, result));
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(uri);
    _syn_texto_liberar(result);
    _syn_texto_liberar(params);
}

void handle_did_change_configuration_r(CadenaSegura params) {
    _syn_texto_liberar(params);
    return;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura handle_did_close_r(CadenaSegura uri_ref, CadenaSegura params) {
    CadenaSegura diag = concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"uri\":"), .datos = "{\"uri\":" }, json_string_r(uri_ref)), (CadenaSegura){ .longitud = (int)strlen(",\"diagnostics\":[]}"), .datos = ",\"diagnostics\":[]}" });
    enviar_respuesta_r(construir_notificacion_r((CadenaSegura){ .longitud = (int)strlen("textDocument/publishDiagnostics"), .datos = "textDocument/publishDiagnostics" }, diag));
    _syn_texto_liberar(uri_ref);
    _syn_texto_liberar(params);
    _syn_texto_liberar(diag);
    return (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura handle_did_open_r(CadenaSegura uri_ref, CadenaSegura params) {
    int64_t uri_idx = strstr_f(params, (CadenaSegura){ .longitud = (int)strlen("\"uri\""), .datos = "\"uri\"" });
    if ((uri_idx == (-1LL))) {
        _syn_texto_liberar(params);
        return uri_ref;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura segmento = ((CadenaSegura){.longitud=strlen_s(params), .datos=((char*)memcpy(malloc(strlen_s(params)+1),(params).datos+uri_idx,strlen_s(params)))});
    int64_t comilla1 = strstr_f(segmento, (CadenaSegura){ .longitud = (int)strlen("\""), .datos = "\"" });
    if ((comilla1 == (-1LL))) {
        _syn_texto_liberar(segmento);
        return uri_ref;
          /* [Lifetime Scope: exit depth=1] */
    }
    int64_t uri_abs = ((uri_idx + comilla1) + 1LL);
    CadenaSegura segmento2 = ((CadenaSegura){.longitud=strlen_s(params), .datos=((char*)memcpy(malloc(strlen_s(params)+1),(params).datos+uri_abs,strlen_s(params)))});
    int64_t comilla2 = strstr_f(segmento2, (CadenaSegura){ .longitud = (int)strlen("\""), .datos = "\"" });
    if ((comilla2 == (-1LL))) {
        _syn_texto_liberar(segmento2);
        return uri_ref;
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura nuevo_uri = ((CadenaSegura){.longitud=comilla2, .datos=((char*)memcpy(malloc(comilla2+1),(params).datos+uri_abs,comilla2))});
    CadenaSegura diag = concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"uri\":"), .datos = "{\"uri\":" }, json_string_r(nuevo_uri)), (CadenaSegura){ .longitud = (int)strlen(",\"diagnostics\":[]}"), .datos = ",\"diagnostics\":[]}" });
    enviar_respuesta_r(construir_notificacion_r((CadenaSegura){ .longitud = (int)strlen("textDocument/publishDiagnostics"), .datos = "textDocument/publishDiagnostics" }, diag));
    _syn_texto_liberar(diag);
    return nuevo_uri;
      /* [Lifetime Scope: exit depth=0] */
}

void handle_formatting_r(int64_t id, CadenaSegura params) {
    enviar_respuesta_r(construir_respuesta_r(id, (CadenaSegura){ .longitud = (int)strlen("[]"), .datos = "[]" }));
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(params);
}

void handle_hover_r(int64_t id, CadenaSegura params) {
    CadenaSegura result = (CadenaSegura){ .longitud = (int)strlen("{\"contents\":{\"kind\":\"markdown\",\"value\":\"Tipo: `entero`\"}}"), .datos = "{\"contents\":{\"kind\":\"markdown\",\"value\":\"Tipo: `entero`\"}}" };
    enviar_respuesta_r(construir_respuesta_r(id, result));
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(result);
    _syn_texto_liberar(params);
}

void handle_initialize_r(int64_t id) {
    CadenaSegura caps = (CadenaSegura){ .longitud = (int)strlen("{\"textDocumentSync\":{\"openClose\":true,\"change\":1,\"save\":{\"includeText\":true}},\"hoverProvider\":true,\"completionProvider\":{\"triggerCharacters\":[\".\",\":\",\"(\"]},\"definitionProvider\":true,\"codeActionProvider\":true,\"documentFormattingProvider\":true,\"signatureHelpProvider\":{\"triggerCharacters\":[\"(\",\",\"],\"workspace\":{\"didChangeConfiguration\":{\"supported\":true}}}}"), .datos = "{\"textDocumentSync\":{\"openClose\":true,\"change\":1,\"save\":{\"includeText\":true}},\"hoverProvider\":true,\"completionProvider\":{\"triggerCharacters\":[\".\",\":\",\"(\"]},\"definitionProvider\":true,\"codeActionProvider\":true,\"documentFormattingProvider\":true,\"signatureHelpProvider\":{\"triggerCharacters\":[\"(\",\",\"],\"workspace\":{\"didChangeConfiguration\":{\"supported\":true}}}}" };
    CadenaSegura server_info = (CadenaSegura){ .longitud = (int)strlen("{\"name\":\"synapse-lsp-native\",\"version\":\"0.3.0\"}"), .datos = "{\"name\":\"synapse-lsp-native\",\"version\":\"0.3.0\"}" };
    CadenaSegura result = concat(concat(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"capabilities\":"), .datos = "{\"capabilities\":" }, caps), (CadenaSegura){ .longitud = (int)strlen(",\"serverInfo\":"), .datos = ",\"serverInfo\":" }), server_info), (CadenaSegura){ .longitud = (int)strlen("}"), .datos = "}" });
    enviar_respuesta_r(construir_respuesta_r(id, result));
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(server_info);
    _syn_texto_liberar(result);
    _syn_texto_liberar(caps);
}

void handle_shutdown_r(int64_t id) {
    enviar_respuesta_r(concat(concat((CadenaSegura){ .longitud = (int)strlen("{\"jsonrpc\":\"2.0\",\"id\":"), .datos = "{\"jsonrpc\":\"2.0\",\"id\":" }, a_texto(id)), (CadenaSegura){ .longitud = (int)strlen(",\"result\":null}"), .datos = ",\"result\":null}" }));
      /* [Lifetime Scope: exit depth=0] */
}

void handle_signature_help_r(int64_t id, CadenaSegura params) {
    enviar_respuesta_r(construir_respuesta_r(id, (CadenaSegura){ .longitud = (int)strlen("{\"signatures\":[]}"), .datos = "{\"signatures\":[]}" }));
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(params);
}

void handle_unknown_r(int64_t id) {
    enviar_respuesta_r(construir_error_r(id, (-32601LL), (CadenaSegura){ .longitud = (int)strlen("Method not found"), .datos = "Method not found" }));
      /* [Lifetime Scope: exit depth=0] */
}

int64_t indice_de(CadenaSegura texto, CadenaSegura subcadena) {
    _syn_texto_liberar(texto);
    _syn_texto_liberar(subcadena);
    return _syn_texto_indice_de(texto, subcadena);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura json_string_r(CadenaSegura valor) {
    CadenaSegura escaped = escapar_json(valor);
    _syn_texto_liberar(valor);
    _syn_texto_liberar(escaped);
    return concat(concat((CadenaSegura){ .longitud = (int)strlen("\""), .datos = "\"" }, escaped), (CadenaSegura){ .longitud = (int)strlen("\""), .datos = "\"" });
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura leer_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = {0};
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        _syn_texto_liberar(ruta_segura);
        _syn_texto_liberar(ruta);
        return (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
          /* [Lifetime Scope: exit depth=1] */
    }
    return _syn_leer_archivo(ruta_segura);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura leer_bytes(int64_t cantidad) {
    return _syn_leer_bytes(cantidad);
      /* [Lifetime Scope: exit depth=0] */
}

void liberar_nodo(struct NodoJson n) {
    _json_nodo_liberar(n);
    return;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura mayusculas(CadenaSegura texto) {
    _syn_texto_liberar(texto);
    return _syn_texto_mayusculas(texto);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura minusculas(CadenaSegura texto) {
    _syn_texto_liberar(texto);
    return _syn_texto_minusculas(texto);
      /* [Lifetime Scope: exit depth=0] */
}

struct NodoJson obtener_campo(struct NodoJson nodo, CadenaSegura clave) {
    _json_nodo_liberar(nodo);
    _syn_texto_liberar(clave);
    return _json_object_get(nodo, clave);
      /* [Lifetime Scope: exit depth=0] */
}

struct NodoJson obtener_elemento(struct NodoJson nodo, int64_t indice) {
    _json_nodo_liberar(nodo);
    return _json_array_get(nodo, indice);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura obtener_env(CadenaSegura nombre) {
    _syn_texto_liberar(nombre);
    return _syn_obtener_env(nombre);
      /* [Lifetime Scope: exit depth=0] */
}

int64_t _principal_impl(void) {
    _simd_detectar();
    int64_t tp = 0LL;
    int64_t tf = 0LL;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== test_lsp_methods.syn — 22 Tests LSP ==="), .datos = "=== test_lsp_methods.syn — 22 Tests LSP ===" });
    CadenaSegura r1 = construir_respuesta_r(1LL, (CadenaSegura){ .longitud = (int)strlen("{\"ok\":true}"), .datos = "{\"ok\":true}" });
    if (((contiene(r1, (CadenaSegura){ .longitud = (int)strlen("\"id\":1"), .datos = "\"id\":1" }) != 0LL) && (contiene(r1, (CadenaSegura){ .longitud = (int)strlen("\"jsonrpc\":\"2.0\""), .datos = "\"jsonrpc\":\"2.0\"" }) != 0LL))) {
        tp = (tp + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("  FAIL: construir_respuesta basica"), .datos = "  FAIL: construir_respuesta basica" });
        tf = (tf + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura r2 = construir_respuesta_r(9999LL, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" });
    if ((contiene(r2, (CadenaSegura){ .longitud = (int)strlen("\"id\":9999"), .datos = "\"id\":9999" }) != 0LL)) {
        tp = (tp + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("  FAIL: construir_respuesta id grande"), .datos = "  FAIL: construir_respuesta id grande" });
        tf = (tf + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura e1 = construir_error_r(5LL, (-32600LL), (CadenaSegura){ .longitud = (int)strlen("Invalid Request"), .datos = "Invalid Request" });
    if ((((contiene(e1, (CadenaSegura){ .longitud = (int)strlen("\"id\":5"), .datos = "\"id\":5" }) != 0LL) && (contiene(e1, (CadenaSegura){ .longitud = (int)strlen("\"code\":-32600"), .datos = "\"code\":-32600" }) != 0LL)) && (contiene(e1, (CadenaSegura){ .longitud = (int)strlen("\"error\""), .datos = "\"error\"" }) != 0LL))) {
        tp = (tp + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("  FAIL: construir_error basico"), .datos = "  FAIL: construir_error basico" });
        tf = (tf + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura n1 = construir_notificacion_r((CadenaSegura){ .longitud = (int)strlen("test/method"), .datos = "test/method" }, (CadenaSegura){ .longitud = (int)strlen("{\"data\":1}"), .datos = "{\"data\":1}" });
    if ((((contiene(n1, (CadenaSegura){ .longitud = (int)strlen("\"method\":\"test/method\""), .datos = "\"method\":\"test/method\"" }) != 0LL) && (contiene(n1, (CadenaSegura){ .longitud = (int)strlen("\"params\":{\"data\":1}"), .datos = "\"params\":{\"data\":1}" }) != 0LL)) && (contiene(n1, (CadenaSegura){ .longitud = (int)strlen("\"id\""), .datos = "\"id\"" }) == 0LL))) {
        tp = (tp + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("  FAIL: construir_notificacion basica"), .datos = "  FAIL: construir_notificacion basica" });
        tf = (tf + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura j1 = json_string_r((CadenaSegura){ .longitud = (int)strlen("hola"), .datos = "hola" });
    if ((str_eq(j1, (CadenaSegura){ .longitud = (int)strlen("\"hola\""), .datos = "\"hola\"" }) == 1)) {
        tp = (tp + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("  FAIL: json_string basico"), .datos = "  FAIL: json_string basico" });
        tf = (tf + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura j2 = json_string_r((CadenaSegura){ .longitud = (int)strlen("a\"b"), .datos = "a\"b" });
    if ((contiene(j2, (CadenaSegura){ .longitud = (int)strlen("\\\""), .datos = "\\\"" }) != 0LL)) {
        tp = (tp + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("  FAIL: json_string escape"), .datos = "  FAIL: json_string escape" });
        tf = (tf + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    handle_initialize_r(1LL);
    tp = (tp + 1LL);
    handle_shutdown_r(1LL);
    tp = (tp + 1LL);
    handle_hover_r(1LL, (CadenaSegura){ .longitud = (int)strlen("{}"), .datos = "{}" });
    tp = (tp + 1LL);
    handle_completion_r(1LL, (CadenaSegura){ .longitud = (int)strlen("{}"), .datos = "{}" });
    tp = (tp + 1LL);
    handle_definition_r(1LL, (CadenaSegura){ .longitud = (int)strlen("file:///test.syn"), .datos = "file:///test.syn" }, (CadenaSegura){ .longitud = (int)strlen("{}"), .datos = "{}" });
    tp = (tp + 1LL);
    handle_code_action_r(1LL, (CadenaSegura){ .longitud = (int)strlen("{}"), .datos = "{}" });
    tp = (tp + 1LL);
    handle_formatting_r(1LL, (CadenaSegura){ .longitud = (int)strlen("{}"), .datos = "{}" });
    tp = (tp + 1LL);
    handle_signature_help_r(1LL, (CadenaSegura){ .longitud = (int)strlen("{}"), .datos = "{}" });
    tp = (tp + 1LL);
    handle_unknown_r(1LL);
    tp = (tp + 1LL);
    enviar_respuesta_r((CadenaSegura){ .longitud = (int)strlen("{\"test\":1}"), .datos = "{\"test\":1}" });
    tp = (tp + 1LL);
    CadenaSegura params = (CadenaSegura){ .longitud = (int)strlen("{\"textDocument\":{\"uri\":\"file:///test.syn\"}}"), .datos = "{\"textDocument\":{\"uri\":\"file:///test.syn\"}}" };
    CadenaSegura uri1 = handle_did_open_r((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }, params);
    if ((str_eq(uri1, (CadenaSegura){ .longitud = (int)strlen("file:///test.syn"), .datos = "file:///test.syn" }) == 1)) {
        tp = (tp + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("  FAIL: handle_did_open extrae uri — obtuvo: "), .datos = "  FAIL: handle_did_open extrae uri — obtuvo: " }, uri1));
        tf = (tf + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura uri2 = handle_did_open_r((CadenaSegura){ .longitud = (int)strlen("default.syn"), .datos = "default.syn" }, (CadenaSegura){ .longitud = (int)strlen("{}"), .datos = "{}" });
    if ((str_eq(uri2, (CadenaSegura){ .longitud = (int)strlen("default.syn"), .datos = "default.syn" }) == 1)) {
        tp = (tp + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("  FAIL: handle_did_open default — obtuvo: "), .datos = "  FAIL: handle_did_open default — obtuvo: " }, uri2));
        tf = (tf + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    CadenaSegura uri3 = handle_did_close_r((CadenaSegura){ .longitud = (int)strlen("test.syn"), .datos = "test.syn" }, (CadenaSegura){ .longitud = (int)strlen("{}"), .datos = "{}" });
    if ((str_eq(uri3, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        tp = (tp + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("  FAIL: handle_did_close limpia"), .datos = "  FAIL: handle_did_close limpia" });
        tf = (tf + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    handle_did_change_configuration_r((CadenaSegura){ .longitud = (int)strlen("{}"), .datos = "{}" });
    tp = (tp + 1LL);
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== RESUMEN ==="), .datos = "=== RESUMEN ===" });
    escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("Pasados: "), .datos = "Pasados: " }, a_texto(tp)));
    escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("Fallidos: "), .datos = "Fallidos: " }, a_texto(tf)));
    if ((tf > 0LL)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("RESULTADO: FAIL"), .datos = "RESULTADO: FAIL" });
        _syn_texto_liberar(uri3);
        _syn_texto_liberar(uri2);
        _syn_texto_liberar(uri1);
        _syn_texto_liberar(r2);
        _syn_texto_liberar(r1);
        _syn_texto_liberar(params);
        _syn_texto_liberar(n1);
        _syn_texto_liberar(j2);
        _syn_texto_liberar(j1);
        _syn_texto_liberar(e1);
        return 1LL;
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("RESULTADO: PASS"), .datos = "RESULTADO: PASS" });
        return 0LL;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura recortar(CadenaSegura texto) {
    _syn_texto_liberar(texto);
    return _syn_texto_recortar(texto);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura reemplazar(CadenaSegura texto, CadenaSegura buscar, CadenaSegura reemplazar) {
    _syn_texto_liberar(texto);
    _syn_texto_liberar(reemplazar);
    _syn_texto_liberar(buscar);
    return _syn_texto_reemplazar(texto, buscar, reemplazar);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura sha256_texto(CadenaSegura datos) {
    _syn_texto_liberar(datos);
    return _syn_sha256_texto(datos);
      /* [Lifetime Scope: exit depth=0] */
}

int64_t strchr_f(CadenaSegura texto, int64_t caracter) {
    _syn_texto_liberar(texto);
    return _syn_strchr(texto, caracter);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura strcpy_f(CadenaSegura texto) {
    _syn_texto_liberar(texto);
    return _syn_strcpy(texto);
      /* [Lifetime Scope: exit depth=0] */
}

int64_t strlen_s(CadenaSegura a) {
    _syn_texto_liberar(a);
    return _syn_strlen(a);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura strncpy_f(CadenaSegura texto, int64_t max_len) {
    _syn_texto_liberar(texto);
    return _syn_strncpy(texto, max_len);
      /* [Lifetime Scope: exit depth=0] */
}

int64_t strstr_f(CadenaSegura texto, CadenaSegura patron) {
    _syn_texto_liberar(texto);
    _syn_texto_liberar(patron);
    return _syn_strstr(texto, patron);
      /* [Lifetime Scope: exit depth=0] */
}

int64_t termina_con(CadenaSegura texto, CadenaSegura sufijo) {
    _syn_texto_liberar(texto);
    _syn_texto_liberar(sufijo);
    return _syn_texto_termina_con(texto, sufijo);
      /* [Lifetime Scope: exit depth=0] */
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    _principal_impl();
    synapse_esperar_hilos();
    synapse_esperar_fibras();
    pool_destroy();
    return 0;
}