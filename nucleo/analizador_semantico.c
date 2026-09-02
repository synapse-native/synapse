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

typedef struct { int longitud; const char* datos; } CadenaSegura;  // cumple Manual 2 4.1

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
#ifndef PROPIEDAD_VIVO
#define PROPIEDAD_VIVO (1LL)
#endif
#ifndef PROPIEDAD_MOVIDO
#define PROPIEDAD_MOVIDO (2LL)
#endif

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

struct AnalizadorSemanticoEst;
struct SemAdtInfo;
struct SemEstructuraInfo;
struct SemFuncionInfo;
struct SemNodo;
struct SemPrestamo;
struct SemSimbolo;
struct SemTablaSimbolos;

typedef struct AnalizadorSemanticoEst {
    struct SemNodo* nodos;
    int64_t total_nodos;
    struct SemTablaSimbolos* tabla;
    CadenaSegura func_retorno;
    CadenaSegura func_actual;
    int en_coincidir;
    int dentro_de_inseguro;
    int hay_error;
    int hay_error_2_4;
    struct SemEstructuraInfo* info_estructuras;
    int64_t total_estructuras;
    struct SemAdtInfo* info_adts;
    int64_t total_adts;
    struct SemFuncionInfo* info_funciones;
    int64_t total_funciones;
    CadenaSegura asignaciones_retorno_campo;
    CadenaSegura asignaciones_campos_var;
    CadenaSegura asignaciones_campos_campo;
    CadenaSegura asignaciones_campos_tipo;
    int64_t total_asignaciones;
    int64_t proximo_lifetime;
    struct SemPrestamo* prestamos;
    int64_t total_prestamos;
    struct RegionGraph region_graph;
    struct UnionFind uf;
    CadenaSegura lt_kind;
    CadenaSegura lt_ambito;
} AnalizadorSemanticoEst;

typedef struct SemAdtInfo {
    CadenaSegura nombre;
    int64_t num_parametros;
} SemAdtInfo;

typedef struct SemEstructuraInfo {
    CadenaSegura nombre;
    CadenaSegura campos_nombre;
    CadenaSegura campos_tipo;
    int64_t total_campos;
} SemEstructuraInfo;

typedef struct SemFuncionInfo {
    CadenaSegura nombre;
    int64_t nodo;
} SemFuncionInfo;

typedef struct SemNodo {
    int64_t tipo_nodo;
    int64_t linea;
    int64_t columna;
    int64_t valor_int;
    double valor_dec;
    int64_t ptr_str;
    int64_t len_str;
    int64_t hijo_izq;
    int64_t hijo_der;
    int64_t hermano;
    int64_t ptr_extra;
} SemNodo;

typedef struct SemPrestamo {
    int64_t idx_simbolo;
    int es_mutable;
    int64_t nivel_ambito;
} SemPrestamo;

typedef struct SemSimbolo {
    CadenaSegura nombre;
    CadenaSegura tipo;
    int64_t nivel_ambito;
    int64_t propiedad;
    int es_constante;
    int64_t linea;
    int64_t columna;
} SemSimbolo;

typedef struct SemTablaSimbolos {
    struct SemSimbolo* entradas;
    int64_t total_entradas;
    int64_t nivel_actual;
    int64_t max_entradas;
} SemTablaSimbolos;

static inline int risky_call(void) { return 0; }
struct AnalizadorSemanticoEst analizador_nuevo(struct SemNodo nodos, int64_t total);
void analizar(struct AnalizadorSemanticoEst* est);
void analizar_expr(struct AnalizadorSemanticoEst* est, int64_t idx);
void analizar_paso_cuerpos(struct AnalizadorSemanticoEst* est, int64_t idx_programa);
void analizar_paso_estructuras(struct AnalizadorSemanticoEst* est, int64_t idx_programa);
void analizar_paso_funciones(struct AnalizadorSemanticoEst* est, int64_t idx_programa);
void analizar_sentencia(struct AnalizadorSemanticoEst* est, int64_t idx_nodo);
int64_t builtin_cantidad_args(CadenaSegura nombre);
CadenaSegura builtin_tipo_parametro(CadenaSegura nombre, int64_t idx);
CadenaSegura builtin_tipo_retorno(CadenaSegura nombre);
int es_builtin(CadenaSegura nombre);
CadenaSegura nodo_cadena_retorno(struct AnalizadorSemanticoEst* est, int64_t idx);
int64_t nodo_expr(struct AnalizadorSemanticoEst* est, int64_t idx);
int64_t nodo_hermano(struct AnalizadorSemanticoEst* est, int64_t idx);
int64_t nodo_hijo_der(struct AnalizadorSemanticoEst* est, int64_t idx);
int64_t nodo_hijo_izq(struct AnalizadorSemanticoEst* est, int64_t idx);
int64_t nodo_linea(struct AnalizadorSemanticoEst* est, int64_t idx);
int64_t nodo_tipo(struct AnalizadorSemanticoEst* est, int64_t idx);
int64_t nodo_valor_int(struct AnalizadorSemanticoEst* est, int64_t idx);
int64_t parsear_patron_coincidir(CadenaSegura patron, void* tag_buf, void* var_buf);
int prestamo_activo(struct AnalizadorSemanticoEst* est, int64_t idx_simbolo, int es_mutable);
void registrar_adt(struct AnalizadorSemanticoEst* est, CadenaSegura nombre, int64_t num_parametros, int64_t idx_nodo);
void registrar_estructura(struct AnalizadorSemanticoEst* est, CadenaSegura nombre, int64_t idx_nodo);
int registrar_prestamo(struct AnalizadorSemanticoEst* est, int64_t idx_simbolo, int es_mutable);
void sem_error(struct AnalizadorSemanticoEst* est, int64_t codigo, int64_t idx_nodo, CadenaSegura mensaje);
int64_t tabla_buscar(struct AnalizadorSemanticoEst* est, CadenaSegura nombre);
int tabla_declarar(struct AnalizadorSemanticoEst* est, CadenaSegura nombre, CadenaSegura tipo, int64_t idx_nodo, int es_constante);
void tabla_entrar_scope(struct AnalizadorSemanticoEst* est);
int tabla_esta_movido(struct AnalizadorSemanticoEst* est, CadenaSegura nombre);
void tabla_marcar_movido(struct AnalizadorSemanticoEst* est, CadenaSegura nombre);
void tabla_salir_scope(struct AnalizadorSemanticoEst* est);
CadenaSegura tipo_normalizado(CadenaSegura tipo);
void validar_llamada_generica(struct AnalizadorSemanticoEst* est, int64_t idx_llamada);
void validar_tipo_instanciacion(struct AnalizadorSemanticoEst* est, CadenaSegura tipo, int64_t idx_nodo);

#define NODO_PROGRAMA (1LL)
#define NODO_FUNCION (2LL)
#define NODO_SI (3LL)
#define NODO_MIENTRAS (4LL)
#define NODO_RETORNAR (5LL)
#define NODO_EXPR (6LL)
#define NODO_ASIGNACION (7LL)
#define NODO_IDENTIFICADOR (8LL)
#define NODO_NUMERO (9LL)
#define NODO_DECIMAL (10LL)
#define NODO_CADENA_LIT (11LL)
#define NODO_BINARIA (12LL)
#define NODO_UNARIA (13LL)
#define NODO_LLAMADA (14LL)
#define NODO_PARAMETRO (15LL)
#define NODO_ESTRUCTURA (16LL)
#define NODO_DECLARACION_TIPO (51LL)
#define NODO_CONSTRUCTOR (52LL)
#define NODO_IMPORTAR (17LL)
#define NODO_LANZAR (18LL)
#define NODO_ESCUCHAR (19LL)
#define NODO_ROMPER (20LL)
#define NODO_SIGUIENTE (21LL)
#define NODO_BOOLEANO (22LL)
#define NODO_CONSTANTE (23LL)
#define NODO_INSEGURO (24LL)
#define NODO_IMPORTAR_C (25LL)
#define NODO_EXTERNO (26LL)
#define NODO_RECUPERAR (27LL)
#define NODO_TENSOR (28LL)
#define NODO_INDICE (29LL)
#define NODO_TRANSFERIDO (30LL)
#define NODO_ACCESO_CAMPO (31LL)
#define NODO_ASIGNACION_CAMPO (32LL)
#define NODO_PARRAFO (33LL)
#define NODO_DECLARACION (34LL)
#define NODO_LOG (35LL)
#define NODO_PUNTERO (36LL)
#define NODO_DEREF (37LL)
#define NODO_COINCIDIR (38LL)
#define NODO_CASO (39LL)
#define NODO_ASM (40LL)
#define NODO_CANAL_CREAR (41LL)
#define NODO_ENVIAR_CANAL (42LL)
#define NODO_RECIBIR_CANAL (43LL)
#define NODO_VACIO (44LL)
#define NODO_PARA (45LL)
#define NODO_CONTRATO (46LL)
#define ERR_SEM_VAR_NO_DECLARADA (14LL)
#define ERR_SEM_TIPO_INCOMPATIBLE (15LL)
#define ERR_SEM_TIPO_RETORNO (16LL)
#define ERR_SEM_FUNC_NO_DEFINIDA (17LL)
#define ERR_SEM_REDEFINICION (18LL)
#define ERR_SEM_ARGUMENTOS_INVALIDOS (19LL)
#define ERR_SEM_ESTRUCTURA_NO_DEFINIDA (20LL)
#define ERR_SEM_CAMPO_NO_EXISTE (21LL)
#define ERR_SEM_VAR_MOVIDA (22LL)
#define ERR_SEM_ASM_FUERA_INSEGURO (31LL)
#define ERR_SEM_CONSTANTE_INMUTABLE (32LL)
#define ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED (33LL)
#define ERR_MEM_LIFETIME_MISMATCH (34LL)
#define ERR_MEM_LIFETIME_CYCLE (35LL)
#define ERR_SEM_TYPE_AMBIGUOUS (40LL)
#define PROPIEDAD_VIVO (1LL)
#define PROPIEDAD_MOVIDO (2LL)
struct AnalizadorSemanticoEst analizador_nuevo(struct SemNodo nodos, int64_t total) {
    struct AnalizadorSemanticoEst est;
    est = (struct AnalizadorSemanticoEst){0};
    { /* unsafe */
        est.nodos = (struct SemNodo*)&nodos;
        est.total_nodos = total;
        est.tabla->nivel_actual = 0;
        est.tabla->total_entradas = 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    est.func_retorno = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    est.func_actual = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    est.en_coincidir = 0;
    est.dentro_de_inseguro = 0;
    est.hay_error = 0;
    est.total_estructuras = 0LL;
    est.total_asignaciones = 0LL;
    return est;
      /* [Lifetime Scope: exit depth=0] */
}

void analizar(struct AnalizadorSemanticoEst* est) {
    int64_t idx_programa;
    idx_programa = 0LL;
    { /* unsafe */
        idx_programa = 0;
        // Buscar el nodo raiz NODO_PROGRAMA;
        for (int _i = 0; _i < est->total_nodos; _i++) {
            if (est->nodos[_i].tipo_nodo == 1) { idx_programa = _i; break; }
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((idx_programa < 0LL)) {
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    analizar_paso_estructuras(est, idx_programa);
    analizar_paso_funciones(est, idx_programa);
    analizar_paso_cuerpos(est, idx_programa);
      /* [Lifetime Scope: exit depth=0] */
}

void analizar_expr(struct AnalizadorSemanticoEst* est, int64_t idx) {
    int64_t tipo;
    CadenaSegura nombre = {0};
    int64_t es_mut;
    int64_t hijo;
    int64_t h_tipo;
    int64_t arg;
    int64_t r2;
    if ((idx <= 0LL)) {
        _syn_texto_liberar(nombre);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    tipo = nodo_tipo(est, idx);
    if ((tipo == NODO_IDENTIFICADOR)) {
        _syn_texto_liberar(nombre);
        nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        { /* unsafe */
            { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[idx].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[idx])<<32; } const char* _v=(const char*)_bp; if(_v){ CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_v}; nombre=_cs; } };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 0)) {
            if (tabla_esta_movido(est, nombre)) {
                { /* unsafe */
                    { char _mm[256]; snprintf(_mm,256,"Uso ilegal de variable ya movida '%s' (E-504)", nombre.datos); CadenaSegura _msg={.longitud=(int)strlen(_mm),.datos=_mm}; sem_error(est,ERR_MEM_USE_AFTER_MOVE,idx,_msg); }
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        _syn_texto_liberar(nombre);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_TRANSFERIDO)) {
        analizar_expr(est, nodo_hijo_izq(est, idx));
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_PUNTERO)) {
        es_mut = nodo_valor_int(est, idx);
        hijo = nodo_hijo_izq(est, idx);
        if ((hijo > 0LL)) {
            h_tipo = nodo_tipo(est, hijo);
            if ((h_tipo == NODO_IDENTIFICADOR)) {
                { /* unsafe */
                    { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[hijo].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[hijo])<<32; } const char* _v=(const char*)_bp; if(_v){ CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_v}; int _idx=tabla_buscar(est,_cs); if(_idx>=0){ if(!registrar_prestamo(est,_idx,es_mut)){ char _mm[256]; snprintf(_mm,256,"Conflicto de prestamo sobre '%s': prestamo %s incompatible con prestamos activos (Manual 4 S4.2)",_cs.datos,es_mut?"&mut":"&"); CadenaSegura _msg={.longitud=(int)strlen(_mm),.datos=_mm}; sem_error(est,ERR_MEM_BORROW_CONFLICT,idx,_msg); } } } };
                      /* [Lifetime Scope: exit depth=4] */
                }
                { /* unsafe */
                    { int _lt = est->proximo_lifetime;
                        ((int*)est->lt_kind.datos)[0] = LT_LOCAL; ((int*)est->lt_ambito.datos)[0] = 0;
                        ((int*)est->lt_kind.datos)[_lt] = LT_LOCAL; ((int*)est->lt_ambito.datos)[_lt] = est->tabla->nivel_actual;
                        region_agregar_restriccion(est->region_graph, REGION_OUTLIVES, 0, _lt, idx);
                        est->proximo_lifetime = _lt + 1; }
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_BINARIA)) {
        analizar_expr(est, nodo_expr(est, idx));
        analizar_expr(est, nodo_hijo_izq(est, idx));
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_UNARIA)) {
        analizar_expr(est, nodo_expr(est, idx));
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_LLAMADA)) {
        validar_llamada_generica(est, idx);
        { /* unsafe */
                int* _phi27=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp27=(uintptr_t)(unsigned)est->nodos[idx].ptr_str; if(_phi27){ _bp27|=((uintptr_t)(unsigned)_phi27[idx])<<32; } const char* _cal27=(const char*)_bp27;
                if(_cal27 && _cal27[0]){
                    int _se27=0; for(int _i27=0;_i27<est->total_estructuras;_i27++){ if(est->info_estructuras[_i27].nombre.datos&&strcmp(est->info_estructuras[_i27].nombre.datos,_cal27)==0){ _se27=1; break; } };
                    int _fn27=-1; for(int _j27=0;_j27<est->total_funciones;_j27++){ if(est->info_funciones[_j27].nombre.datos&&strcmp(est->info_funciones[_j27].nombre.datos,_cal27)==0){ _fn27=_j27; break; } };
                    if(_se27 && _fn27<0 && ((int*)&est->nodos[idx])[6]!=0){
                        static char _sebuf27[256]; _sebuf27[0]=0;
                        snprintf(_sebuf27,256,"Cantidad de argumentos invalida para '%s': se esperaban 0", _cal27);
                        sem_error(est, ERR_SEM_ARGUMENTOS_INVALIDOS, idx, (CadenaSegura){.longitud=(int)strlen(_sebuf27),.datos=_sebuf27});
                    }
                }
              /* [Lifetime Scope: exit depth=2] */
        }
        arg = nodo_expr(est, idx);
        r2 = 1LL;
        while ((r2 == 1LL)) {
            if ((arg <= 0LL)) {
                r2 = 0LL;
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            analizar_expr(est, arg);
            { /* unsafe */
                arg = est->nodos[arg].hermano;
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_INDICE)) {
        analizar_expr(est, nodo_expr(est, idx));
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    return;
      /* [Lifetime Scope: exit depth=0] */
}

void analizar_paso_cuerpos(struct AnalizadorSemanticoEst* est, int64_t idx_programa) {
    int64_t stmt;
    int64_t r;
    int64_t tipo;
    CadenaSegura nombre = {0};
    int64_t p;
    CadenaSegura pnombre = {0};
    CadenaSegura ptipo = {0};
    int64_t cuerpo;
    int64_t stmt_cuerpo;
    int64_t r2;
    stmt = nodo_hijo_izq(est, idx_programa);
    r = 1LL;
    while ((r == 1LL)) {
        if ((stmt <= 0LL)) {
            r = 0LL;
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        tipo = nodo_tipo(est, stmt);
        if ((tipo == NODO_FUNCION)) {
            _syn_texto_liberar(nombre);
            nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
            { /* unsafe */
                { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[stmt].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[stmt])<<32; } const char* _v=(const char*)_bp; if(_v){ char* _dup=strdup(_v); CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_dup}; nombre=_cs; } };
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((es_builtin(nombre) == 0)) {
                tabla_entrar_scope(est);
                est->func_actual = nombre;
                p = nodo_expr(est, stmt);
                while ((p > 0LL)) {
                    _syn_texto_liberar(pnombre);
                    pnombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
                    { /* unsafe */
                        { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[p].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[p])<<32; } const char* _v=(const char*)_bp; if(_v){ char* _dup=strdup(_v); CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_dup}; pnombre=_cs; } };
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    if ((str_eq(pnombre, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 0)) {
                        _syn_texto_liberar(ptipo);
                        ptipo = nodo_cadena_retorno(est, p);
                        tabla_declarar(est, pnombre, ptipo, p, 0);
                          /* [Lifetime Scope: exit depth=5] */
                        _syn_texto_liberar(ptipo);
                    }
                    { /* unsafe */
                        p = est->nodos[p].hermano;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                    _syn_texto_liberar(pnombre);
                }
                { /* unsafe */
                    est->proximo_lifetime = 1;
                    est->region_graph->total_constraints = 0;
                    for (int _ui = 0; _ui < est->uf->max; _ui++) { ((int*)est->uf->parent.datos)[_ui] = -1; ((int*)est->uf->rank.datos)[_ui] = 0; }
                    ((int*)est->lt_kind.datos)[0] = LT_LOCAL; ((int*)est->lt_ambito.datos)[0] = 0;
                      /* [Lifetime Scope: exit depth=4] */
                }
                cuerpo = nodo_hijo_izq(est, stmt);
                stmt_cuerpo = cuerpo;
                r2 = 1LL;
                while ((r2 == 1LL)) {
                    if ((stmt_cuerpo <= 0LL)) {
                        r2 = 0LL;
                        break;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    analizar_sentencia(est, stmt_cuerpo);
                    { /* unsafe */
                        stmt_cuerpo = est->nodos[stmt_cuerpo].hermano;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                { /* unsafe */
                    if (est->region_graph->total_constraints > 0) {
                        region_resolver(est->region_graph, est->uf, est);
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                tabla_salir_scope(est);
                est->func_actual = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(nombre);
        }
        { /* unsafe */
            stmt = est->nodos[stmt].hermano;
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

void analizar_paso_estructuras(struct AnalizadorSemanticoEst* est, int64_t idx_programa) {
    int64_t stmt;
    int64_t r;
    int64_t tipo;
    CadenaSegura nombre = {0};
    int64_t nparams;
    int64_t tp;
    stmt = nodo_hijo_izq(est, idx_programa);
    r = 1LL;
    while ((r == 1LL)) {
        if ((stmt <= 0LL)) {
            r = 0LL;
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        tipo = nodo_tipo(est, stmt);
        if ((tipo == NODO_ESTRUCTURA)) {
            _syn_texto_liberar(nombre);
            nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
            { /* unsafe */
                { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[stmt].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[stmt])<<32; } const char* _v=(const char*)_bp; if(_v){ char* _dup=strdup(_v); CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_dup}; nombre=_cs; } };
                  /* [Lifetime Scope: exit depth=3] */
            }
            registrar_estructura(est, nombre, stmt);
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(nombre);
        }
        if ((tipo == NODO_DECLARACION_TIPO)) {
            _syn_texto_liberar(nombre);
            nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
            { /* unsafe */
                { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[stmt].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[stmt])<<32; } const char* _v=(const char*)_bp; if(_v){ char* _dup=strdup(_v); CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_dup}; nombre=_cs; } };
                  /* [Lifetime Scope: exit depth=3] */
            }
            nparams = 0LL;
            tp = nodo_expr(est, stmt);
            while ((tp > 0LL)) {
                nparams = (nparams + 1LL);
                { /* unsafe */
                    tp = est->nodos[tp].hermano;
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
            }
            registrar_adt(est, nombre, nparams, stmt);
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(nombre);
        }
        { /* unsafe */
            stmt = est->nodos[stmt].hermano;
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

void analizar_paso_funciones(struct AnalizadorSemanticoEst* est, int64_t idx_programa) {
    CadenaSegura nombre = {0};
    int64_t stmt;
    int64_t r;
    int64_t tipo;
    int ok;
    CadenaSegura retorno = {0};
    int64_t p;
    CadenaSegura tparam = {0};
    int64_t esconst;
    CadenaSegura cnombre = {0};
    int ok_c;
    _syn_texto_liberar(nombre);
    nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        nombre.datos = NULL;
          /* [Lifetime Scope: exit depth=1] */
    }
    stmt = nodo_hijo_izq(est, idx_programa);
    r = 1LL;
    while ((r == 1LL)) {
        if ((stmt <= 0LL)) {
            r = 0LL;
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        tipo = nodo_tipo(est, stmt);
        if ((tipo == NODO_FUNCION)) {
            _syn_texto_liberar(nombre);
            nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
            { /* unsafe */
                { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[stmt].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[stmt])<<32; } const char* _v=(const char*)_bp; if(_v){ char* _dup=strdup(_v); CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_dup}; nombre=_cs; } };
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((es_builtin(nombre) == 0)) {
                ok = tabla_declarar(est, nombre, (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" }, stmt, 0);
                if ((ok == 0)) {
                    sem_error(est, ERR_SEM_REDEFINICION, stmt, nombre);
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
            }
            _syn_texto_liberar(retorno);
            retorno = nodo_cadena_retorno(est, stmt);
            validar_tipo_instanciacion(est, retorno, stmt);
            p = nodo_expr(est, stmt);
            while ((p > 0LL)) {
                _syn_texto_liberar(tparam);
                tparam = nodo_cadena_retorno(est, p);
                validar_tipo_instanciacion(est, tparam, p);
                { /* unsafe */
                    p = est->nodos[p].hermano;
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
                _syn_texto_liberar(tparam);
            }
            { /* unsafe */
                if (est->total_funciones < 256 && nombre.datos) {
                    char* _nmost = strdup(nombre.datos); // R1: copia propia (el nombre local se libera en la siguiente iteracion; paridad S1 registrar_funcion);
                    est->info_funciones[est->total_funciones].nombre = (CadenaSegura){.longitud = (int)strlen(_nmost), .datos = _nmost};
                    est->info_funciones[est->total_funciones].nodo = stmt;
                    est->total_funciones = est->total_funciones + 1;
                }
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(retorno);
            _syn_texto_liberar(nombre);
        }
        if ((tipo == NODO_EXTERNO)) {
            _syn_texto_liberar(nombre);
            nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
            { /* unsafe */
                { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[stmt].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[stmt])<<32; } const char* _v=(const char*)_bp; if(_v){ char* _dup=strdup(_v); CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_dup}; nombre=_cs; } };
                  /* [Lifetime Scope: exit depth=3] */
            }
            ok = tabla_declarar(est, nombre, (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" }, stmt, 0);
            if ((ok == 0)) {
                sem_error(est, ERR_SEM_REDEFINICION, stmt, nombre);
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(nombre);
        }
        if ((tipo == NODO_ASIGNACION)) {
            esconst = nodo_hijo_der(est, stmt);
            if ((esconst == 1LL)) {
                _syn_texto_liberar(cnombre);
                cnombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
                { /* unsafe */
                    { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[stmt].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[stmt])<<32; } const char* _v=(const char*)_bp; if(_v){ char* _dup=strdup(_v); CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_dup}; cnombre=_cs; } };
                      /* [Lifetime Scope: exit depth=4] */
                }
                if ((str_eq(cnombre, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 0)) {
                    ok_c = tabla_declarar(est, cnombre, (CadenaSegura){ .longitud = (int)strlen("entero"), .datos = "entero" }, stmt, 1);
                    if ((ok_c == 0)) {
                        sem_error(est, ERR_SEM_REDEFINICION, stmt, cnombre);
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
                _syn_texto_liberar(cnombre);
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        { /* unsafe */
            stmt = est->nodos[stmt].hermano;
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

void analizar_sentencia(struct AnalizadorSemanticoEst* est, int64_t idx_nodo) {
    int64_t tipo;
    int64_t linea;
    int64_t esconstdecl;
    CadenaSegura cnom = {0};
    int ok_c;
    CadenaSegura varnombre = {0};
    int64_t idx_sim;
    int64_t esconst;
    int ok_decl;
    int64_t cuerpo;
    int64_t stmt;
    int64_t r;
    int ok_para;
    int64_t cond_para;
    int64_t canal_expr;
    int64_t prev;
    int64_t casos;
    int64_t idx_caso;
    int64_t tiene_wildcard;
    int64_t tiene_ok;
    int64_t tiene_err;
    int64_t tiene_algun;
    int64_t tiene_ninguno;
    CadenaSegura tag_nombre = {0};
    CadenaSegura var_nombre = {0};
    int64_t res;
    int64_t cuerpo_caso;
    int64_t stmt_c;
    int64_t r2;
    int64_t v;
    int64_t vt;
    CadenaSegura vnombre = {0};
    int64_t llamada_t;
    int64_t arg_t;
    int64_t r3_t;
    int64_t hijo_t;
    int64_t ht;
    CadenaSegura t_nombre = {0};
    if ((idx_nodo < 0LL)) {
        _syn_texto_liberar(vnombre);
        _syn_texto_liberar(varnombre);
        _syn_texto_liberar(var_nombre);
        _syn_texto_liberar(tag_nombre);
        _syn_texto_liberar(t_nombre);
        _syn_texto_liberar(cnom);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    tipo = nodo_tipo(est, idx_nodo);
    linea = nodo_linea(est, idx_nodo);
    if ((tipo == NODO_ASIGNACION)) {
        esconstdecl = nodo_hijo_der(est, idx_nodo);
        if ((esconstdecl == 1LL)) {
            _syn_texto_liberar(cnom);
            cnom = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
            { /* unsafe */
                { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[idx_nodo].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[idx_nodo])<<32; } const char* _v=(const char*)_bp; if(_v){ CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_v}; cnom=_cs; } };
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((str_eq(cnom, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 0)) {
                ok_c = tabla_declarar(est, cnom, (CadenaSegura){ .longitud = (int)strlen("entero"), .datos = "entero" }, idx_nodo, 1);
                if ((ok_c == 0)) {
                    sem_error(est, ERR_SEM_REDEFINICION, idx_nodo, cnom);
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
            }
            analizar_expr(est, nodo_expr(est, idx_nodo));
            _syn_texto_liberar(cnom);
            return;
              /* [Lifetime Scope: exit depth=2] */
        }
        _syn_texto_liberar(varnombre);
        varnombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        { /* unsafe */
            { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[idx_nodo].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[idx_nodo])<<32; } const char* _v=(const char*)_bp; if(_v){ CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_v}; varnombre=_cs; } };
              /* [Lifetime Scope: exit depth=2] */
        }
        idx_sim = tabla_buscar(est, varnombre);
        if ((idx_sim < 0LL)) {
            if ((str_eq(varnombre, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 0)) {
                tabla_declarar(est, varnombre, (CadenaSegura){ .longitud = (int)strlen("entero"), .datos = "entero" }, idx_nodo, 0);
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        else {
            esconst = 0;
            { /* unsafe */
                if (est->tabla->entradas[idx_sim].es_constante) { esconst = verdadero; }
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((esconst == 1)) {
                { /* unsafe */
                        fprintf(stderr, "[Synapse] Error semantico (linea %d, columna %d): No se puede reasignar la constante '%s'\n", (idx_nodo>=0&&idx_nodo<est->total_nodos)?est->nodos[idx_nodo].linea:0, (idx_nodo>=0&&idx_nodo<est->total_nodos)?est->nodos[idx_nodo].columna:0, varnombre.datos);
                      /* [Lifetime Scope: exit depth=4] */
                }
                sem_error(est, ERR_SEM_CONSTANTE_INMUTABLE, idx_nodo, varnombre);
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        analizar_expr(est, nodo_expr(est, idx_nodo));
        _syn_texto_liberar(varnombre);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_DECLARACION)) {
        _syn_texto_liberar(varnombre);
        varnombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        { /* unsafe */
            { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[idx_nodo].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[idx_nodo])<<32; } const char* _v=(const char*)_bp; if(_v){ CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_v}; varnombre=_cs; } };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((str_eq(varnombre, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 0)) {
            ok_decl = tabla_declarar(est, varnombre, (CadenaSegura){ .longitud = (int)strlen("entero"), .datos = "entero" }, idx_nodo, 0);
            if ((ok_decl == 0)) {
                sem_error(est, ERR_SEM_REDEFINICION, idx_nodo, varnombre);
                  /* [Lifetime Scope: exit depth=3] */
            }
            else {
                { /* unsafe */
                    est->proximo_lifetime = est->proximo_lifetime + 1;
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        analizar_expr(est, nodo_expr(est, idx_nodo));
        _syn_texto_liberar(varnombre);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_SI)) {
        analizar_expr(est, nodo_expr(est, idx_nodo));
        tabla_entrar_scope(est);
        cuerpo = nodo_hijo_izq(est, idx_nodo);
        stmt = cuerpo;
        r = 1LL;
        while ((r == 1LL)) {
            if ((stmt <= 0LL)) {
                r = 0LL;
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            analizar_sentencia(est, stmt);
            { /* unsafe */
                stmt = est->nodos[stmt].hermano;
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        tabla_salir_scope(est);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_MIENTRAS)) {
        analizar_expr(est, nodo_expr(est, idx_nodo));
        tabla_entrar_scope(est);
        cuerpo = nodo_hijo_izq(est, idx_nodo);
        stmt = cuerpo;
        r = 1LL;
        while ((r == 1LL)) {
            if ((stmt <= 0LL)) {
                r = 0LL;
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            analizar_sentencia(est, stmt);
            { /* unsafe */
                stmt = est->nodos[stmt].hermano;
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        tabla_salir_scope(est);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_PARA)) {
        tabla_entrar_scope(est);
        _syn_texto_liberar(varnombre);
        varnombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        { /* unsafe */
            { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[idx_nodo].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[idx_nodo])<<32; } const char* _v=(const char*)_bp; if(_v){ CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_v}; varnombre=_cs; } };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((str_eq(varnombre, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 0)) {
            ok_para = tabla_declarar(est, varnombre, (CadenaSegura){ .longitud = (int)strlen("entero"), .datos = "entero" }, idx_nodo, 0);
            if ((ok_para == 0)) {
                sem_error(est, ERR_SEM_REDEFINICION, idx_nodo, varnombre);
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        analizar_expr(est, nodo_expr(est, idx_nodo));
        cond_para = nodo_hijo_der(est, idx_nodo);
        if ((cond_para > 0LL)) {
            analizar_expr(est, cond_para);
              /* [Lifetime Scope: exit depth=2] */
        }
        cuerpo = nodo_hijo_izq(est, idx_nodo);
        stmt = cuerpo;
        r = 1LL;
        while ((r == 1LL)) {
            if ((stmt <= 0LL)) {
                r = 0LL;
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            analizar_sentencia(est, stmt);
            { /* unsafe */
                stmt = est->nodos[stmt].hermano;
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        tabla_salir_scope(est);
        _syn_texto_liberar(varnombre);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_ESCUCHAR)) {
        canal_expr = nodo_expr(est, idx_nodo);
        if ((canal_expr > 0LL)) {
            analizar_expr(est, canal_expr);
              /* [Lifetime Scope: exit depth=2] */
        }
        tabla_entrar_scope(est);
        cuerpo = nodo_hijo_izq(est, idx_nodo);
        stmt = cuerpo;
        r = 1LL;
        while ((r == 1LL)) {
            if ((stmt <= 0LL)) {
                r = 0LL;
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            analizar_sentencia(est, stmt);
            { /* unsafe */
                stmt = est->nodos[stmt].hermano;
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        tabla_salir_scope(est);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_INSEGURO)) {
        tabla_entrar_scope(est);
        prev = est->dentro_de_inseguro;
        est->dentro_de_inseguro = 1;
        cuerpo = nodo_hijo_izq(est, idx_nodo);
        stmt = cuerpo;
        r = 1LL;
        while ((r == 1LL)) {
            if ((stmt <= 0LL)) {
                r = 0LL;
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            analizar_sentencia(est, stmt);
            { /* unsafe */
                stmt = est->nodos[stmt].hermano;
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        est->dentro_de_inseguro = prev;
        tabla_salir_scope(est);
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_COINCIDIR)) {
        est->en_coincidir = 1;
        casos = nodo_hijo_izq(est, idx_nodo);
        idx_caso = casos;
        tiene_wildcard = 0;
        tiene_ok = 0;
        tiene_err = 0;
        tiene_algun = 0;
        tiene_ninguno = 0;
        r = 1LL;
        while ((r == 1LL)) {
            if ((idx_caso <= 0LL)) {
                r = 0LL;
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            _syn_texto_liberar(tag_nombre);
            tag_nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
            _syn_texto_liberar(var_nombre);
            var_nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
            res = 0LL;
            { /* unsafe */
                int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[idx_caso].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[idx_caso])<<32; } CadenaSegura _patron_s = { .longitud = 255, .datos = (const char*)_bp };
                static char _tb_r11[64]; static char _vb_r11[64]; _tb_r11[0]=0; _vb_r11[0]=0;
                res = parsear_patron_coincidir(_patron_s, _tb_r11, _vb_r11);
                if (res == 1) { tag_nombre = (CadenaSegura){ .longitud = (int)strlen(_tb_r11), .datos = _tb_r11 }; var_nombre = (CadenaSegura){ .longitud = (int)strlen(_vb_r11), .datos = _vb_r11 }; }
                // Manual 2 S2.4: marcar variantes para validacion de exhaustividad;
                if(res==1){ if(tag_nombre.datos){ if(strcmp(tag_nombre.datos,"ok")==0) tiene_ok=1; if(strcmp(tag_nombre.datos,"err")==0) tiene_err=1; if(strcmp(tag_nombre.datos,"algun")==0) tiene_algun=1; if(strcmp(tag_nombre.datos,"ninguno")==0) tiene_ninguno=1; } };
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((res == 0LL)) {
                tiene_wildcard = 1;
                tabla_entrar_scope(est);
                cuerpo_caso = nodo_hijo_izq(est, idx_caso);
                stmt_c = cuerpo_caso;
                r2 = 1LL;
                while ((r2 == 1LL)) {
                    if ((stmt_c <= 0LL)) {
                        r2 = 0LL;
                        break;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    analizar_sentencia(est, stmt_c);
                    { /* unsafe */
                        stmt_c = est->nodos[stmt_c].hermano;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                tabla_salir_scope(est);
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((res == 1LL)) {
                if ((str_eq(var_nombre, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 0)) {
                    tabla_declarar(est, var_nombre, (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" }, idx_caso, 0);
                      /* [Lifetime Scope: exit depth=4] */
                }
                tabla_entrar_scope(est);
                cuerpo_caso = nodo_hijo_izq(est, idx_caso);
                stmt_c = cuerpo_caso;
                r2 = 1LL;
                while ((r2 == 1LL)) {
                    if ((stmt_c <= 0LL)) {
                        r2 = 0LL;
                        break;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    analizar_sentencia(est, stmt_c);
                    { /* unsafe */
                        stmt_c = est->nodos[stmt_c].hermano;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                tabla_salir_scope(est);
                  /* [Lifetime Scope: exit depth=3] */
            }
            { /* unsafe */
                idx_caso = est->nodos[idx_caso].hermano;
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
            _syn_texto_liberar(var_nombre);
            _syn_texto_liberar(tag_nombre);
        }
        if ((tiene_wildcard == 0)) {
            if ((((tiene_ok == 1) && (tiene_err == 0)) || ((tiene_ok == 0) && (tiene_err == 1)))) {
                sem_error(est, ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED, idx_nodo, (CadenaSegura){ .longitud = (int)strlen("coincidir no exhaustivo: faltan variantes ok/err"), .datos = "coincidir no exhaustivo: faltan variantes ok/err" });
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((((tiene_algun == 1) && (tiene_ninguno == 0)) || ((tiene_algun == 0) && (tiene_ninguno == 1)))) {
                sem_error(est, ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED, idx_nodo, (CadenaSegura){ .longitud = (int)strlen("coincidir no exhaustivo: faltan variantes algun/ninguno"), .datos = "coincidir no exhaustivo: faltan variantes algun/ninguno" });
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        est->en_coincidir = 0;
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_EXPR)) {
        analizar_expr(est, nodo_expr(est, idx_nodo));
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_LOG)) {
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_ENVIAR_CANAL)) {
        analizar_expr(est, nodo_expr(est, idx_nodo));
        v = nodo_expr(est, idx_nodo);
        if ((v > 0LL)) {
            vt = nodo_tipo(est, v);
            if ((vt == NODO_IDENTIFICADOR)) {
                _syn_texto_liberar(vnombre);
                vnombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
                { /* unsafe */
                    { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[v].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[v])<<32; } const char* _v=(const char*)_bp; if(_v){ CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_v}; vnombre=_cs; } };
                      /* [Lifetime Scope: exit depth=4] */
                }
                if ((str_eq(vnombre, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 0)) {
                    tabla_marcar_movido(est, vnombre);
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
                _syn_texto_liberar(vnombre);
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_LANZAR)) {
        analizar_expr(est, nodo_expr(est, idx_nodo));
        llamada_t = nodo_expr(est, idx_nodo);
        if ((llamada_t > 0LL)) {
            arg_t = nodo_expr(est, llamada_t);
            r3_t = 1LL;
            while ((r3_t == 1LL)) {
                if ((arg_t <= 0LL)) {
                    r3_t = 0LL;
                    break;
                      /* [Lifetime Scope: exit depth=4] */
                }
                if ((nodo_tipo(est, arg_t) == NODO_TRANSFERIDO)) {
                    hijo_t = nodo_hijo_izq(est, arg_t);
                    if ((hijo_t > 0LL)) {
                        ht = nodo_tipo(est, hijo_t);
                        if ((ht == NODO_IDENTIFICADOR)) {
                            _syn_texto_liberar(t_nombre);
                            t_nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
                            { /* unsafe */
                                { int* _phi=(int*)est->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[hijo_t].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[hijo_t])<<32; } const char* _v=(const char*)_bp; if(_v){ CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_v}; t_nombre=_cs; } };
                                  /* [Lifetime Scope: exit depth=7] */
                            }
                            if ((str_eq(t_nombre, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 0)) {
                                tabla_marcar_movido(est, t_nombre);
                                  /* [Lifetime Scope: exit depth=7] */
                            }
                              /* [Lifetime Scope: exit depth=6] */
                            _syn_texto_liberar(t_nombre);
                        }
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                { /* unsafe */
                    arg_t = est->nodos[arg_t].hermano;
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((tipo == NODO_RETORNAR)) {
        analizar_expr(est, nodo_expr(est, idx_nodo));
        return;
          /* [Lifetime Scope: exit depth=1] */
    }
    return;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t builtin_cantidad_args(CadenaSegura nombre) {
    { /* unsafe */
        if (strcmp(nombre.datos, "reserva") == 0) { return 1; }
        if (strcmp(nombre.datos, "libera") == 0) { return 1; }
        if (strcmp(nombre.datos, "crear_tensor") == 0) { return 2; }
        if (strcmp(nombre.datos, "suma_tensor") == 0) { return 2; }
        if (strcmp(nombre.datos, "producto_punto") == 0) { return 2; }
        if (strcmp(nombre.datos, "abrir") == 0) { return 2; }
        if (strcmp(nombre.datos, "leer") == 0) { return 1; }
        if (strcmp(nombre.datos, "escribir") == 0) { return 1; }
        if (strcmp(nombre.datos, "escribir_linea") == 0) { return 1; }
        if (strcmp(nombre.datos, "leer_linea") == 0) { return 0; }
        if (strcmp(nombre.datos, "cerrar_archivo") == 0) { return 1; }
        if (strcmp(nombre.datos, "suma") == 0) { return 2; }
        if (strcmp(nombre.datos, "producto") == 0) { return 2; }
        if (strcmp(nombre.datos, "relu") == 0) { return 1; }
        if (strcmp(nombre.datos, "tokenizar") == 0) { return 1; }
        if (strcmp(nombre.datos, "parsear") == 0) { return 1; }
        if (strcmp(nombre.datos, "generar") == 0) { return 2; }
        if (strcmp(nombre.datos, "_argc") == 0) { return 0; }
        if (strcmp(nombre.datos, "_argv") == 0) { return 1; }
        if (strcmp(nombre.datos, "salir") == 0) { return 1; }
        if (strcmp(nombre.datos, "concat") == 0) { return 2; }
        if (strcmp(nombre.datos, "texto_a_entero") == 0) { return 1; }
        if (strcmp(nombre.datos, "texto_a_decimal") == 0) { return 1; }
        if (strcmp(nombre.datos, "entero_a_texto") == 0) { return 1; }
        if (strcmp(nombre.datos, "decimal_a_texto") == 0) { return 1; }
        if (strcmp(nombre.datos, "volcar_ast") == 0) { return 2; }
        if (strcmp(nombre.datos, "canal_crear") == 0) { return 1; }
        if (strcmp(nombre.datos, "canal_enviar") == 0) { return 2; }
        if (strcmp(nombre.datos, "canal_recibir") == 0) { return 1; }
        if (strcmp(nombre.datos, "cerrar") == 0) { return 1; }
        if (strcmp(nombre.datos, "len") == 0) { return 1; }
        if (strcmp(nombre.datos, "subcadena") == 0) { return 3; }
        if (strcmp(nombre.datos, "empieza_con") == 0) { return 2; }
          /* [Lifetime Scope: exit depth=1] */
    }
    _syn_texto_liberar(nombre);
    return 0LL;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura builtin_tipo_parametro(CadenaSegura nombre, int64_t idx) {
    if ((((((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("reserva"), .datos = "reserva" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("libera"), .datos = "libera" }) == 1)) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("crear_tensor"), .datos = "crear_tensor" }) == 1)) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("suma_tensor"), .datos = "suma_tensor" }) == 1)) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("producto_punto"), .datos = "producto_punto" }) == 1))) {
        if ((idx == 0LL)) {
            _syn_texto_liberar(nombre);
            return (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((((idx == 1LL) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("reserva"), .datos = "reserva" }) == 1)) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("libera"), .datos = "libera" }) == 1))) {
            return (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("abrir"), .datos = "abrir" }) == 1)) {
        if (((idx == 0LL) || (idx == 1LL))) {
            return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if (((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("leer"), .datos = "leer" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("cerrar_archivo"), .datos = "cerrar_archivo" }) == 1))) {
        if ((idx == 0LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("Canal"), .datos = "Canal" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if (((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("escribir"), .datos = "escribir" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("escribir_linea"), .datos = "escribir_linea" }) == 1))) {
        if ((idx == 0LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if (((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("suma"), .datos = "suma" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("producto"), .datos = "producto" }) == 1))) {
        if (((idx == 0LL) || (idx == 1LL))) {
            return (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("relu"), .datos = "relu" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("tokenizar"), .datos = "tokenizar" }) == 1)) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("parsear"), .datos = "parsear" }) == 1))) {
        if ((idx == 0LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("generar"), .datos = "generar" }) == 1)) {
        if ((idx == 0LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("Programa"), .datos = "Programa" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((idx == 1LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("_argv"), .datos = "_argv" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("salir"), .datos = "salir" }) == 1)) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("texto_a_entero"), .datos = "texto_a_entero" }) == 1))) {
        if ((idx == 0LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("concat"), .datos = "concat" }) == 1)) {
        if (((idx == 0LL) || (idx == 1LL))) {
            return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if (((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("texto_a_decimal"), .datos = "texto_a_decimal" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("decimal_a_texto"), .datos = "decimal_a_texto" }) == 1))) {
        if ((idx == 0LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("entero_a_texto"), .datos = "entero_a_texto" }) == 1)) {
        if ((idx == 0LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("volcar_ast"), .datos = "volcar_ast" }) == 1)) {
        if ((idx == 0LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("Programa"), .datos = "Programa" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("canal_crear"), .datos = "canal_crear" }) == 1)) {
        if ((idx == 0LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("canal_enviar"), .datos = "canal_enviar" }) == 1)) {
        if ((idx == 0LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("CanalConcurrencia*"), .datos = "CanalConcurrencia*" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((idx == 1LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("void*"), .datos = "void*" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if (((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("canal_recibir"), .datos = "canal_recibir" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("cerrar"), .datos = "cerrar" }) == 1))) {
        if ((idx == 0LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("CanalConcurrencia*"), .datos = "CanalConcurrencia*" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if (((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("len"), .datos = "len" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("empieza_con"), .datos = "empieza_con" }) == 1))) {
        if ((idx == 0LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("subcadena"), .datos = "subcadena" }) == 1)) {
        if ((idx == 0LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if (((idx == 1LL) || (idx == 2LL))) {
            return (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("empieza_con"), .datos = "empieza_con" }) == 1)) {
        if ((idx == 1LL)) {
            return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    return (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura builtin_tipo_retorno(CadenaSegura nombre) {
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("reserva"), .datos = "reserva" }) == 1)) {
        _syn_texto_liberar(nombre);
        return (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("libera"), .datos = "libera" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("crear_tensor"), .datos = "crear_tensor" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("suma_tensor"), .datos = "suma_tensor" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("producto_punto"), .datos = "producto_punto" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("abrir"), .datos = "abrir" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("Canal"), .datos = "Canal" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("leer"), .datos = "leer" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("escribir"), .datos = "escribir" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("escribir_linea"), .datos = "escribir_linea" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("leer_linea"), .datos = "leer_linea" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("cerrar_archivo"), .datos = "cerrar_archivo" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("suma"), .datos = "suma" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("producto"), .datos = "producto" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("relu"), .datos = "relu" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("tokenizar"), .datos = "tokenizar" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("parsear"), .datos = "parsear" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("Programa"), .datos = "Programa" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("generar"), .datos = "generar" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("_argc"), .datos = "_argc" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("_argv"), .datos = "_argv" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("salir"), .datos = "salir" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("concat"), .datos = "concat" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("texto_a_entero"), .datos = "texto_a_entero" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("texto_a_decimal"), .datos = "texto_a_decimal" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("decimal"), .datos = "decimal" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("entero_a_texto"), .datos = "entero_a_texto" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("decimal_a_texto"), .datos = "decimal_a_texto" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("volcar_ast"), .datos = "volcar_ast" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("canal_crear"), .datos = "canal_crear" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("CanalConcurrencia*"), .datos = "CanalConcurrencia*" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("canal_enviar"), .datos = "canal_enviar" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("canal_recibir"), .datos = "canal_recibir" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("void*"), .datos = "void*" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("cerrar"), .datos = "cerrar" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("len"), .datos = "len" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("subcadena"), .datos = "subcadena" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("empieza_con"), .datos = "empieza_con" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
          /* [Lifetime Scope: exit depth=1] */
    }
    return (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
      /* [Lifetime Scope: exit depth=0] */
}

int es_builtin(CadenaSegura nombre) {
    { /* unsafe */
        if (strcmp(nombre.datos, "reserva") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "libera") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "crear_tensor") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "suma_tensor") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "producto_punto") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "abrir") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "leer") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "escribir") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "escribir_linea") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "leer_linea") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "cerrar_archivo") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "suma") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "producto") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "relu") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "tokenizar") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "parsear") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "generar") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "_argc") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "_argv") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "salir") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "concat") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "texto_a_entero") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "texto_a_decimal") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "entero_a_texto") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "decimal_a_texto") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "volcar_ast") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "canal_crear") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "canal_enviar") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "canal_recibir") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "cerrar") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "len") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "subcadena") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "empieza_con") == 0) { return verdadero; }
          /* [Lifetime Scope: exit depth=1] */
    }
    _syn_texto_liberar(nombre);
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura nodo_cadena_retorno(struct AnalizadorSemanticoEst* est, int64_t idx) {
    CadenaSegura r = {0};
    _syn_texto_liberar(r);
    r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        { int* _phi=(int*)est->asignaciones_retorno_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est->nodos[idx].ptr_extra; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[idx])<<32; } const char* _v=(const char*)_bp; if(_v){ char* _dup=strdup(_v); CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_dup}; r=_cs; } };
          /* [Lifetime Scope: exit depth=1] */
    }
    return r;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t nodo_expr(struct AnalizadorSemanticoEst* est, int64_t idx) {
    int64_t r;
    r = 0LL;
    { /* unsafe */
        r = (idx >= 0 && idx < est->total_nodos) ? ((int*)&est->nodos[idx])[6] : 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    return r;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t nodo_hermano(struct AnalizadorSemanticoEst* est, int64_t idx) {
    int64_t r;
    r = 0LL;
    { /* unsafe */
        r = (idx >= 0 && idx < est->total_nodos) ? est->nodos[idx].hermano : 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    return r;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t nodo_hijo_der(struct AnalizadorSemanticoEst* est, int64_t idx) {
    int64_t r;
    r = 0LL;
    { /* unsafe */
        r = (idx >= 0 && idx < est->total_nodos) ? est->nodos[idx].hijo_der : 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    return r;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t nodo_hijo_izq(struct AnalizadorSemanticoEst* est, int64_t idx) {
    int64_t r;
    r = 0LL;
    { /* unsafe */
        r = (idx >= 0 && idx < est->total_nodos) ? est->nodos[idx].hijo_izq : 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    return r;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t nodo_linea(struct AnalizadorSemanticoEst* est, int64_t idx) {
    int64_t r;
    r = 0LL;
    { /* unsafe */
        r = (idx >= 0 && idx < est->total_nodos) ? est->nodos[idx].linea : 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    return r;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t nodo_tipo(struct AnalizadorSemanticoEst* est, int64_t idx) {
    int64_t r;
    r = 0LL;
    { /* unsafe */
        r = (idx >= 0 && idx < est->total_nodos) ? est->nodos[idx].tipo_nodo : 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    return r;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t nodo_valor_int(struct AnalizadorSemanticoEst* est, int64_t idx) {
    int64_t r;
    r = 0LL;
    { /* unsafe */
        r = (idx >= 0 && idx < est->total_nodos) ? est->nodos[idx].valor_int : 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    return r;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t parsear_patron_coincidir(CadenaSegura patron, void* tag_buf, void* var_buf) {
    { /* unsafe */
        if (patron.datos[0] == '_' && patron.datos[1] == 0) { return 0; }
        char* _tbo = (char*)tag_buf; char* _vbo = (char*)var_buf;
        if (!_tbo || !_vbo) return -1;
        // Extract tag name before '(';
        int _i = 0;
        char _tag[64]; int _tp = 0;
        // R11-h: bound _tp < 63 (revision code-reviewer): un tag de >63 chars;
        // no debe desbordar el buffer de stack del compilador (trunca, no crashea).;
        while (patron.datos[_i] != 0 && patron.datos[_i] != '(' && _tp < 63) { _tag[_tp++] = patron.datos[_i]; _i++; }
        _tag[_tp] = 0;
        if (patron.datos[_i] != '(') {
            // R11: tag sin payload (ej. 'ninguno') -> var vacia, res=1;
            strcpy(_tbo, _tag); _vbo[0] = 0;
            return 1;
        }
        _i++; // skip '(';
        char _var[64]; int _vp = 0;
        while (patron.datos[_i] != 0 && patron.datos[_i] != ')' && _vp < 63) { _var[_vp++] = patron.datos[_i]; _i++; }
        _var[_vp] = 0;
        if (patron.datos[_i] != ')') { return -1; }
        // Copy results into caller buffers (strcpy, no strdup: buffers estaticos;
        // del caller, vida de proceso; RAII pool_free no-op con R10);
        strcpy(_tbo, _tag); strcpy(_vbo, _var);
          /* [Lifetime Scope: exit depth=1] */
    }
    _syn_texto_liberar(patron);
    return 1LL;
      /* [Lifetime Scope: exit depth=0] */
}

int prestamo_activo(struct AnalizadorSemanticoEst* est, int64_t idx_simbolo, int es_mutable) {
    int64_t r;
    int64_t i;
    r = 0LL;
    i = 0LL;
    while ((i < est->total_prestamos)) {
        { /* unsafe */
            if (est->prestamos[i].idx_simbolo == idx_simbolo) {
                if (es_mutable) { r = 1; }
                else if (est->prestamos[i].es_mutable) { r = 1; }
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((r == 1LL)) {
            break;
              /* [Lifetime Scope: exit depth=2] */
        }
        i = (i + 1LL);
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((r == 1LL)) {
        return 1;
          /* [Lifetime Scope: exit depth=1] */
    }
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

void registrar_adt(struct AnalizadorSemanticoEst* est, CadenaSegura nombre, int64_t num_parametros, int64_t idx_nodo) {
    int64_t i;
    int64_t r;
    i = 0LL;
    r = 1LL;
    while ((r == 1LL)) {
        { /* unsafe */
            r = (i < est->total_adts) ? 1 : 0;
            if ((r == 0LL)) {
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            { int _eq = 1; const char* _a = est->info_adts[i].nombre.datos; const char* _b = nombre.datos; for (int _si = 0; _si < 256; _si++) { if (_a[_si] != _b[_si]) { _eq = 0; break; } if (_a[_si] == 0) break; } if (_eq) { sem_error(est, ERR_SEM_REDEFINICION, idx_nodo, nombre); return; } };
            i = i + 1;
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    { /* unsafe */
        char* _nmost = nombre.datos ? strdup(nombre.datos) : (char*)"";
        est->info_adts[est->total_adts].nombre = (CadenaSegura){.longitud = (int)strlen(_nmost), .datos = _nmost};
        est->info_adts[est->total_adts].num_parametros = num_parametros;
        est->total_adts = est->total_adts + 1;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(nombre);
}

void registrar_estructura(struct AnalizadorSemanticoEst* est, CadenaSegura nombre, int64_t idx_nodo) {
    int64_t i;
    int64_t r;
    i = 0LL;
    r = 1LL;
    while ((r == 1LL)) {
        { /* unsafe */
            r = (i < est->total_estructuras) ? 1 : 0;
            if ((r == 0LL)) {
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            int _eq = 1;
            for (int _si = 0; _si < 256; _si++) { if (nombre.datos[_si] != est->info_estructuras[i].nombre.datos[_si]) { _eq = 0; break; } if (nombre.datos[_si] == 0) break; }
            if (_eq) {
                sem_error(est, ERR_SEM_REDEFINICION, idx_nodo, nombre);
                return;
            }
            i = i + 1;
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    { /* unsafe */
        char* _nmost = nombre.datos ? strdup(nombre.datos) : (char*)"";
        est->info_estructuras[est->total_estructuras].nombre = (CadenaSegura){.longitud = (int)strlen(_nmost), .datos = _nmost};
        est->info_estructuras[est->total_estructuras].total_campos = 0;
        est->total_estructuras = est->total_estructuras + 1;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(nombre);
}

int registrar_prestamo(struct AnalizadorSemanticoEst* est, int64_t idx_simbolo, int es_mutable) {
    if (prestamo_activo(est, idx_simbolo, es_mutable)) {
        return 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    { /* unsafe */
        if (est->total_prestamos < 4096) {
            est->prestamos[est->total_prestamos].idx_simbolo = idx_simbolo;
            est->prestamos[est->total_prestamos].es_mutable = es_mutable;
            est->prestamos[est->total_prestamos].nivel_ambito = est->tabla->nivel_actual;
            est->total_prestamos++;
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    return 1;
      /* [Lifetime Scope: exit depth=0] */
}

void sem_error(struct AnalizadorSemanticoEst* est, int64_t codigo, int64_t idx_nodo, CadenaSegura mensaje) {
    int64_t linea;
    int64_t columna;
    linea = 0LL;
    columna = 0LL;
    { /* unsafe */
        linea = (idx_nodo >= 0 && idx_nodo < est->total_nodos) ? est->nodos[idx_nodo].linea : 0;
        columna = (idx_nodo >= 0 && idx_nodo < est->total_nodos) ? est->nodos[idx_nodo].columna : 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    est->hay_error = 1;
    if ((codigo == ERR_SEM_REDEFINICION)) {
        { /* unsafe */
                static char _mre_buf[256]; _mre_buf[0]=0;
                if (mensaje.datos) snprintf(_mre_buf, 256, "Redefinicion de '%s' en el mismo ambito", mensaje.datos);
                if (mensaje.datos) fprintf(stderr, "[Synapse] Error semantico (linea %d, columna %d): %s\n", linea, columna, _mre_buf);
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        if ((codigo != ERR_SEM_CONSTANTE_INMUTABLE)) {
            { /* unsafe */
                    if (mensaje.datos) fprintf(stderr, "[Synapse] Error semantico (linea %d, columna %d): %s\n", linea, columna, mensaje.datos);
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(mensaje);
}

int64_t tabla_buscar(struct AnalizadorSemanticoEst* est, CadenaSegura nombre) {
    int64_t i;
    int64_t r;
    i = 0LL;
    r = 1LL;
    while ((r == 1LL)) {
        { /* unsafe */
            r = (i < est->tabla->total_entradas) ? 1 : 0;
            if ((r == 0LL)) {
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            int _eq = 1;
            int _idx = est->tabla->total_entradas - 1 - i;
            for (int _si = 0; _si < 256; _si++) {
                char _a = nombre.datos[_si];
                char _b = est->tabla->entradas[_idx].nombre.datos[_si];
                if (_a != _b) { _eq = 0; break; }
                if (_a == 0) break;
            }
            if (_eq) { return _idx; }
            i = i + 1;
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    _syn_texto_liberar(nombre);
    return (-1LL);
      /* [Lifetime Scope: exit depth=0] */
}

int tabla_declarar(struct AnalizadorSemanticoEst* est, CadenaSegura nombre, CadenaSegura tipo, int64_t idx_nodo, int es_constante) {
    int64_t linea;
    int64_t columna;
    int64_t i;
    int64_t encontrado;
    int64_t r;
    linea = 0LL;
    columna = 0LL;
    { /* unsafe */
        linea = (idx_nodo >= 0) ? est->nodos[idx_nodo].linea : 0;
        columna = (idx_nodo >= 0) ? est->nodos[idx_nodo].columna : 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    i = 0LL;
    encontrado = 0;
    r = 1LL;
    while ((r == 1LL)) {
        { /* unsafe */
            r = (i < est->tabla->total_entradas) ? 1 : 0;
            if ((r == 0LL)) {
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if (est->tabla->entradas[i].nivel_ambito == est->tabla->nivel_actual) {
                int _eq = 1;
                for (int _si = 0; _si < 256; _si++) { if (((const char*)nombre.datos)[_si] != ((const char*)est->tabla->entradas[i].nombre.datos)[_si]) { _eq = 0; break; } if (((const char*)nombre.datos)[_si] == 0) break; }
                if (_eq) { encontrado = verdadero; }
            }
            i = i + 1;
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((encontrado == 1)) {
        _syn_texto_liberar(tipo);
        _syn_texto_liberar(nombre);
        return 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    { /* unsafe */
        if (est->tabla->total_entradas >= est->tabla->max_entradas) { return 0; }
          /* [Lifetime Scope: exit depth=1] */
    }
    { /* unsafe */
        // Propiedad del nombre: copia propia (evita use-after-free si el llamador libera su buffer);
        char* _nmown = nombre.datos ? strdup(nombre.datos) : (char*)"";
        est->tabla->entradas[est->tabla->total_entradas].nombre = (CadenaSegura){.longitud = (int)strlen(_nmown), .datos = _nmown};
        est->tabla->entradas[est->tabla->total_entradas].tipo = tipo;
        est->tabla->entradas[est->tabla->total_entradas].nivel_ambito = est->tabla->nivel_actual;
        est->tabla->entradas[est->tabla->total_entradas].propiedad = 1;
        est->tabla->entradas[est->tabla->total_entradas].es_constante = es_constante;
        est->tabla->entradas[est->tabla->total_entradas].linea = linea;
        est->tabla->entradas[est->tabla->total_entradas].columna = columna;
        est->tabla->total_entradas = est->tabla->total_entradas + 1;
          /* [Lifetime Scope: exit depth=1] */
    }
    return 1;
      /* [Lifetime Scope: exit depth=0] */
}

void tabla_entrar_scope(struct AnalizadorSemanticoEst* est) {
    { /* unsafe */
        est->tabla->nivel_actual = est->tabla->nivel_actual + 1;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

int tabla_esta_movido(struct AnalizadorSemanticoEst* est, CadenaSegura nombre) {
    int64_t idx;
    int64_t r;
    idx = tabla_buscar(est, nombre);
    if ((idx >= 0LL)) {
        r = 0LL;
        { /* unsafe */
            r = (est->tabla->entradas[idx].propiedad == 2) ? 1 : 0;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((r == 1LL)) {
            _syn_texto_liberar(nombre);
            return 1;
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

void tabla_marcar_movido(struct AnalizadorSemanticoEst* est, CadenaSegura nombre) {
    int64_t idx;
    idx = tabla_buscar(est, nombre);
    if ((idx >= 0LL)) {
        { /* unsafe */
            est->tabla->entradas[idx].propiedad = 2;
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(nombre);
}

void tabla_salir_scope(struct AnalizadorSemanticoEst* est) {
    { /* unsafe */
        while (est->tabla->total_entradas > 0) {
            if (est->tabla->entradas[est->tabla->total_entradas - 1].nivel_ambito < est->tabla->nivel_actual) break;
            est->tabla->total_entradas = est->tabla->total_entradas - 1;
        }
        while (est->total_prestamos > 0) {
            if (est->prestamos[est->total_prestamos - 1].nivel_ambito < est->tabla->nivel_actual) break;
            est->total_prestamos = est->total_prestamos - 1;
        }
        est->tabla->nivel_actual = est->tabla->nivel_actual - 1;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura tipo_normalizado(CadenaSegura tipo) {
    if (((str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("entero"), .datos = "entero" }) == 1) || (str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" }) == 1))) {
        _syn_texto_liberar(tipo);
        return (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((((str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("decimal"), .datos = "decimal" }) == 1) || (str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("real"), .datos = "real" }) == 1)) || (str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("flotante"), .datos = "flotante" }) == 1))) {
        return (CadenaSegura){ .longitud = (int)strlen("decimal"), .datos = "decimal" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if (((str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("booleano"), .datos = "booleano" }) == 1) || (str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("logico"), .datos = "logico" }) == 1))) {
        return (CadenaSegura){ .longitud = (int)strlen("booleano"), .datos = "booleano" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if (((str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" }) == 1) || (str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("cadena"), .datos = "cadena" }) == 1))) {
        return (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if (((str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" }) == 1) || (str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("vacio"), .datos = "vacio" }) == 1))) {
        return (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("CanalConcurrencia*"), .datos = "CanalConcurrencia*" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen("CanalConcurrencia*"), .datos = "CanalConcurrencia*" };
          /* [Lifetime Scope: exit depth=1] */
    }
    return tipo;
      /* [Lifetime Scope: exit depth=0] */
}

void validar_llamada_generica(struct AnalizadorSemanticoEst* est, int64_t idx_llamada) {
    { /* unsafe */
        void _f8_r1_llamada_generica(struct AnalizadorSemanticoEst* e, int idx) {
            int* _phi=(int*)e->asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)e->nodos[idx].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[idx])<<32; } const char* _callee=(const char*)_bp;
            if(!_callee||!_callee[0]) return;
            int _fn=-1; for(int _i=0;_i<e->total_funciones;_i++){ if(e->info_funciones[_i].nombre.datos && strcmp(e->info_funciones[_i].nombre.datos,_callee)==0){ _fn=_i; break; } };
            if(_fn<0) return; int _fnod=e->info_funciones[_fn].nodo;
            char _ret[256]; _ret[0]=0;
            { int* _phr=(int*)e->asignaciones_retorno_campo.datos; uintptr_t _br=(uintptr_t)(unsigned)e->nodos[_fnod].ptr_extra; if(_phr){ _br|=((uintptr_t)(unsigned)_phr[_fnod])<<32; } const char* _vr=(const char*)_br; if(_vr){ int _l=(int)strlen(_vr); if(_l>255)_l=255; memcpy(_ret,_vr,_l); _ret[_l]=0; } };
            char _pars[8][256]; int _np=0; int _pr=((int*)&e->nodos[_fnod])[6];
            while(_pr>0 && _np<8){
                char _pt[256]; _pt[0]=0;
                { int* _php=(int*)e->asignaciones_retorno_campo.datos; uintptr_t _bpr=(uintptr_t)(unsigned)e->nodos[_pr].ptr_extra; if(_php){ _bpr|=((uintptr_t)(unsigned)_php[_pr])<<32; } const char* _vp=(const char*)_bpr; if(_vp){ int _l=(int)strlen(_vp); if(_l>255)_l=255; memcpy(_pt,_vp,_l); _pt[_l]=0; } };
                memcpy(_pars[_np],_pt,256); _np++; _pr=e->nodos[_pr].hermano;
            }
            // TVars: tipo desnudo en mayuscula y desconocido (paridad S1 _recolectar_tvars_firma);
            char _tvn[8][64]; int _ntv=0;
            { const char* _srcs[9]; int _ns=0; if(_ret[0]){ _srcs[_ns++]=_ret; } for(int _i=0;_i<_np;_i++){ if(_pars[_i][0]){ _srcs[_ns++]=_pars[_i]; } };
                for(int _s=0;_s<_ns;_s++){ const char* _c=_srcs[_s]; while(*_c==' '){ _c++; }
                    while(*_c=='&'){ if(strncmp(_c,"&mut ",5)==0){ _c+=5; } else { _c++; } while(*_c==' '){ _c++; } };
                    int _len=(int)strlen(_c); while(_len>0 && (_c[_len-1]=='*'||_c[_len-1]==' ')){ _len--; }
                    if(_len==0) continue; if(!(_c[0]>='A'&&_c[0]<='Z')) continue;
                    int _ok=1; for(int _j=0;_j<_len;_j++){ char _ch=_c[_j]; if(_ch=='<'||_ch=='>'||_ch=='('||_ch==')'||_ch=='['||_ch==']'||_ch==','||_ch==' '||_ch=='&'||_ch=='*'){ _ok=0; break; } } if(!_ok) continue;
                    char _nm[64]; int _nl=_len; if(_nl>63){ _nl=63; } memcpy(_nm,_c,_nl); _nm[_nl]=0;
                    if(strcmp(_nm,"entero")==0||strcmp(_nm,"decimal")==0||strcmp(_nm,"texto")==0||strcmp(_nm,"booleano")==0||strcmp(_nm,"nulo")==0||strcmp(_nm,"void")==0) continue;
                    int _con=0; for(int _i=0;_i<e->total_estructuras;_i++){ if(e->info_estructuras[_i].nombre.datos&&strcmp(e->info_estructuras[_i].nombre.datos,_nm)==0){ _con=1; break; } } if(_con) continue;
                    for(int _i=0;_i<e->total_adts;_i++){ if(e->info_adts[_i].nombre.datos&&strcmp(e->info_adts[_i].nombre.datos,_nm)==0){ _con=1; break; } } if(_con) continue;
                    int _dup=0; for(int _i=0;_i<_ntv;_i++){ if(strcmp(_tvn[_i],_nm)==0){ _dup=1; break; } } if(_dup) continue;
                    if(_ntv<8){ memcpy(_tvn[_ntv],_nm,64); _ntv++; }
                }
            }
            if(_ntv==0) return;
            char _sub[8][256]; int _sb[8]; for(int _i=0;_i<8;_i++){ _sb[_i]=0; _sub[_i][0]=0; }
            // tipos de argumentos (inferencia minima de expresion);
            char _args[8][256]; int _na=0; int _argn=((int*)&e->nodos[idx])[6];
            while(_argn>0 && _na<8){
                char _ab[256]; _ab[0]=0; int _at=e->nodos[_argn].tipo_nodo;
                int _her=e->nodos[_argn].hermano;
                int _g=0; while(_at==30 && _g<8){ int _hx=e->nodos[_argn].hijo_izq; if(_hx<=0){ _at=0; break; } _argn=_hx; _at=e->nodos[_argn].tipo_nodo; _g++; }
                if(_at==9){ strcpy(_ab,"entero"); }
                else if(_at==10){ strcpy(_ab,"decimal"); }
                else if(_at==11){ strcpy(_ab,"texto"); }
                else if(_at==22){ strcpy(_ab,"booleano"); }
                else if(_at==8){
                    int* _pa=(int*)e->asignaciones_campos_campo.datos; uintptr_t _ba=(uintptr_t)(unsigned)e->nodos[_argn].ptr_str; if(_pa){ _ba|=((uintptr_t)(unsigned)_pa[_argn])<<32; } const char* _va=(const char*)_ba;
                    if(_va&&_va[0]){ int _ti=-1; for(int _s=e->tabla->total_entradas-1;_s>=0;_s--){ if(!e->tabla->entradas[_s].nombre.datos) continue; int _eq=1; for(int _k=0;_k<256;_k++){ if(_va[_k]!=e->tabla->entradas[_s].nombre.datos[_k]){ _eq=0; break; } if(_va[_k]==0) break; } if(_eq){ _ti=_s; break; } };
                        if(_ti>=0&&e->tabla->entradas[_ti].tipo.datos){ int _l=(int)strlen(e->tabla->entradas[_ti].tipo.datos); if(_l>255)_l=255; memcpy(_ab,e->tabla->entradas[_ti].tipo.datos,_l); _ab[_l]=0; } };
                }
                else if(_at==14){
                    int* _pa=(int*)e->asignaciones_campos_campo.datos; uintptr_t _ba=(uintptr_t)(unsigned)e->nodos[_argn].ptr_str; if(_pa){ _ba|=((uintptr_t)(unsigned)_pa[_argn])<<32; } const char* _va=(const char*)_ba;
                    if(_va&&_va[0]){ int _ci=-1; for(int _i=0;_i<e->total_funciones;_i++){ if(e->info_funciones[_i].nombre.datos&&strcmp(e->info_funciones[_i].nombre.datos,_va)==0){ _ci=_i; break; } };
                        if(_ci>=0){ int _no=e->info_funciones[_ci].nodo; int* _phr=(int*)e->asignaciones_retorno_campo.datos; uintptr_t _br=(uintptr_t)(unsigned)e->nodos[_no].ptr_extra; if(_phr){ _br|=((uintptr_t)(unsigned)_phr[_no])<<32; } const char* _vr=(const char*)_br; if(_vr){ int _l=(int)strlen(_vr); if(_l>255)_l=255; memcpy(_ab,_vr,_l); _ab[_l]=0; } };
                        if(_ci<0){ int _sc=0; for(int _i=0;_i<e->total_estructuras;_i++){ if(e->info_estructuras[_i].nombre.datos&&strcmp(e->info_estructuras[_i].nombre.datos,_va)==0){ _sc=1; break; } } if(_sc){ strcpy(_ab,_va); } } };
                }
                memcpy(_args[_na],_ab,256); _na++; _argn=_her;
            }
            if(_na!=_np){ char _mm[256]; snprintf(_mm,256,"Cantidad de argumentos invalida para '%s': se esperaban %d (Manual 2 seccion 8.2)",_callee,_np);
                fprintf(stderr,"[Synapse] Error semantico (linea %lld, columna %lld): %s\n",(long long)(idx>=0&&idx<e->total_nodos?e->nodos[idx].linea:0),(long long)(idx>=0&&idx<e->total_nodos?e->nodos[idx].columna:0),_mm); e->hay_error=1; return; }
            // unificador iterativo (worklist de pares) con sustitucion de TVars y occurs check;
            for(int _pari=0;_pari<_np;_pari++){
                char _a[256]; char _b[256]; strcpy(_a,_pars[_pari]); strcpy(_b,_args[_pari]); if(!_b[0]) continue;
                char _q1[8][256]; char _q2[8][256]; int _qh=0; int _fails=0; if(_qh<8){ strcpy(_q1[_qh],_a); strcpy(_q2[_qh],_b); _qh++; }
                while(_qh>0 && !_fails){
                    _qh--; strcpy(_a,_q1[_qh]); strcpy(_b,_q2[_qh]);
                    char _ta[256]; char _tb[256]; strcpy(_ta,_a); strcpy(_tb,_b);
                    for(int _it=0;_it<8;_it++){ int _changed=0; for(int _t=0;_t<_ntv;_t++){ if(_sb[_t] && strcmp(_ta,_tvn[_t])==0){ strcpy(_ta,_sub[_t]); _changed=1; } if(_sb[_t] && strcmp(_tb,_tvn[_t])==0){ strcpy(_tb,_sub[_t]); _changed=1; } } if(!_changed) break; }
                    if(strcmp(_ta,_tb)==0) continue;
                    int _ia=-1,_ib=-1; for(int _t=0;_t<_ntv;_t++){ if(strcmp(_ta,_tvn[_t])==0){ _ia=_t; } if(strcmp(_tb,_tvn[_t])==0){ _ib=_t; } };
                    if(_ia>=0 && !_sb[_ia]){
                        if(_ib>=0){ strcpy(_sub[_ia],_tb); _sb[_ia]=1; }
                        else { int _occ=0; for(int _k=0;_k<(int)strlen(_tb);_k++){ if((_tb[_k]>='A'&&_tb[_k]<='Z')||(_tb[_k]>='a'&&_tb[_k]<='z')||(_tb[_k]>='0'&&_tb[_k]<='9')||_tb[_k]=='_'){ int _k2=_k; while(_k2<(int)strlen(_tb)&&((_tb[_k2]>='A'&&_tb[_k2]<='Z')||(_tb[_k2]>='a'&&_tb[_k2]<='z')||(_tb[_k2]>='0'&&_tb[_k2]<='9')||_tb[_k2]=='_')){ _k2++; } char _tok[64]; int _tl=_k2-_k; if(_tl>63)_tl=63; memcpy(_tok,_tb+_k,_tl); _tok[_tl]=0; if(strcmp(_tok,_tvn[_ia])==0){ _occ=1; } _k=_k2-1; } };
                            if(_occ){ _fails=1; } else { strcpy(_sub[_ia],_tb); _sb[_ia]=1; } };
                        continue;
                    }
                    if(_ib>=0 && !_sb[_ib]){
                        int _occ=0; for(int _k=0;_k<(int)strlen(_ta);_k++){ if((_ta[_k]>='A'&&_ta[_k]<='Z')||(_ta[_k]>='a'&&_ta[_k]<='z')||(_ta[_k]>='0'&&_ta[_k]<='9')||_ta[_k]=='_'){ int _k2=_k; while(_k2<(int)strlen(_ta)&&((_ta[_k2]>='A'&&_ta[_k2]<='Z')||(_ta[_k2]>='a'&&_ta[_k2]<='z')||(_ta[_k2]>='0'&&_ta[_k2]<='9')||_ta[_k2]=='_')){ _k2++; } char _tok[64]; int _tl=_k2-_k; if(_tl>63)_tl=63; memcpy(_tok,_ta+_k,_tl); _tok[_tl]=0; if(strcmp(_tok,_tvn[_ib])==0){ _occ=1; } _k=_k2-1; } };
                        if(_occ){ _fails=1; } else { strcpy(_sub[_ib],_ta); _sb[_ib]=1; } continue;
                    }
                    { int _la=(int)strlen(_ta); int _lb=(int)strlen(_tb); int _a1=-1,_b1=-1;
                        for(int _k=0;_k<_la;_k++){ if(_ta[_k]=='<'){ _a1=_k; break; } } for(int _k=0;_k<_lb;_k++){ if(_tb[_k]=='<'){ _b1=_k; break; } };
                        if(_a1>=0&&_b1>=0&&_ta[_la-1]=='>'&&_tb[_lb-1]=='>'){
                            char _ba0[64]; char _bb0[64]; int _la0=_a1; if(_la0>63)_la0=63; memcpy(_ba0,_ta,_la0); _ba0[_la0]=0; int _lb0=_b1; if(_lb0>63)_lb0=63; memcpy(_bb0,_tb,_lb0); _bb0[_lb0]=0;
                            if(strcmp(_ba0,_bb0)==0){
                                char _aa[4][256]; char _bb[4][256]; int _ana=0,_bna=0;
                                { int _prof=0; int _in=0; for(int _k=_a1+1;_k<_la-1;_k++){ char _ch=_ta[_k]; if(_ch=='<'||_ch=='('){ _prof++; } if(_ch=='>'||_ch==')'){ _prof--; } if(_ch==','&&_prof==0){ if(_ana<4){ _aa[_ana][_in]=0; _ana++; _in=0; } } else if(_ch!=' '){ if(_ana<4&&_in<255){ _aa[_ana][_in++]=_ch; } } } if(_ana<4){ _aa[_ana][_in]=0; _ana++; } };
                                { int _prof=0; int _in=0; for(int _k=_b1+1;_k<_lb-1;_k++){ char _ch=_tb[_k]; if(_ch=='<'||_ch=='('){ _prof++; } if(_ch=='>'||_ch==')'){ _prof--; } if(_ch==','&&_prof==0){ if(_bna<4){ _bb[_bna][_in]=0; _bna++; _in=0; } } else if(_ch!=' '){ if(_bna<4&&_in<255){ _bb[_bna][_in++]=_ch; } } } if(_bna<4){ _bb[_bna][_in]=0; _bna++; } };
                                if(_ana==_bna){ for(int _k=0;_k<_ana;_k++){ if(_qh<8){ strcpy(_q1[_qh],_aa[_k]); strcpy(_q2[_qh],_bb[_k]); _qh++; } } } else { _fails=1; }
                            } else { _fails=1; }
                        } else { _fails=1; }
                    }
                }
                if(_fails){ char _mm[256]; snprintf(_mm,256,"Tipos incompatibles: no se puede usar '%s' con '%s' al instanciar '%s' (Manual 2 seccion 8.2)",_a,_b,_callee);
                    fprintf(stderr,"[Synapse] Error semantico (linea %lld, columna %lld): %s\n",(long long)(idx>=0&&idx<e->total_nodos?e->nodos[idx].linea:0),(long long)(idx>=0&&idx<e->total_nodos?e->nodos[idx].columna:0),_mm); e->hay_error=1; break; }
            }
            // retorno: resolver y chequear TVar libre -> ERR_SEM_TYPE_AMBIGUOUS;
            { char _rr[256]; strcpy(_rr,_ret);
                for(int _it=0;_it<8;_it++){ int _changed=0; for(int _t=0;_t<_ntv;_t++){ if(_sb[_t]&&strcmp(_rr,_tvn[_t])==0){ strcpy(_rr,_sub[_t]); _changed=1; } } if(!_changed) break; }
                int _libre=0; for(int _t=0;_t<_ntv && !_libre;_t++){ if(_sb[_t]) continue; for(int _k=0;_k<(int)strlen(_rr);_k++){ if((_rr[_k]>='A'&&_rr[_k]<='Z')||(_rr[_k]>='a'&&_rr[_k]<='z')||(_rr[_k]>='0'&&_rr[_k]<='9')||_rr[_k]=='_'){ int _k2=_k; while(_k2<(int)strlen(_rr)&&((_rr[_k2]>='A'&&_rr[_k2]<='Z')||(_rr[_k2]>='a'&&_rr[_k2]<='z')||(_rr[_k2]>='0'&&_rr[_k2]<='9')||_rr[_k2]=='_')){ _k2++; } char _tok[64]; int _tl=_k2-_k; if(_tl>63)_tl=63; memcpy(_tok,_rr+_k,_tl); _tok[_tl]=0; if(strcmp(_tok,_tvn[_t])==0){ _libre=1; } _k=_k2-1; } } };
                if(_libre){ char _mm[256]; snprintf(_mm,256,"Expresion con tipo ambiguo: no se puede inferir '%s' (Manual 2 seccion 8.2)",_rr);
                    fprintf(stderr,"[Synapse] Error semantico (linea %lld, columna %lld): %s\n",(long long)(idx>=0&&idx<e->total_nodos?e->nodos[idx].linea:0),(long long)(idx>=0&&idx<e->total_nodos?e->nodos[idx].columna:0),_mm); e->hay_error=1; }
            }
        }
        _f8_r1_llamada_generica(est, idx_llamada);
          /* [Lifetime Scope: exit depth=1] */
    }
    return;
      /* [Lifetime Scope: exit depth=0] */
}

void validar_tipo_instanciacion(struct AnalizadorSemanticoEst* est, CadenaSegura tipo, int64_t idx_nodo) {
    { /* unsafe */

        void _f8_tipo_instanciacion_2_4(struct AnalizadorSemanticoEst* e, const char* s0, int idx) {
            char base[512]; const char* s; char* lt;
            if (!s0 || !s0[0]) return;
            s = s0;
            if (strncmp(s, "&mut ", 5) == 0) s += 5; else if (s[0] == '&') s += 1;
            if (strlen(s) >= 512) return;
            strcpy(base, s);
            while (base[0] && base[strlen(base)-1] == '*') base[strlen(base)-1] = 0;
            lt = strchr(base, '<');
            if (!(lt && base[strlen(base)-1] == '>')) return; /* tipo simple: lenient Etapa 1 */;
            {
                char nom[128]; int nl, profundidad, nargs, i, es_adt, es_estructura, base_conocida, adt_np; const char* p;
                nl = (int)(lt - base); if (nl > 127) nl = 127;
                memcpy(nom, base, nl); nom[nl] = 0;
                profundidad = 0; nargs = 1; p = lt + 1;
                // R13: contar argumentos con profundidad (solo el '>' de nivel 0 cierra);
                // antes el bucle se detenia en el PRIMER '>' y un ADT anidado;
                // (Resultado<Resultado<entero,texto>,texto>) contaba 1 argumento.;
                for (; *p; p++) { if (*p == '<') profundidad++; else if (*p == '>') { if (profundidad == 0) break; profundidad--; } else if (*p == ',' && profundidad == 0) nargs++; }
                        es_adt = 0; adt_np = 0;
                base_conocida = 0; { static const char* const _prim[] = {"int","entero","int64_t","long","float","decimal","double","real","flotante","texto","cadena","CadenaSegura","string","booleano","logico","bool","nulo","vacio","void","puntero","void*","rc","arc","debil","débil","weak","faible","fraco","tensor","CanalConcurrencia","Canal",0}; int _pi; for (_pi = 0; _prim[_pi]; _pi++) if (strcmp(nom, _prim[_pi]) == 0) { base_conocida = 1; break; } };
                        for (i = 0; i < e->total_adts; i++) if (e->info_adts[i].nombre.datos && strcmp(e->info_adts[i].nombre.datos, nom) == 0) { es_adt = 1; adt_np = e->info_adts[i].num_parametros; break; }
                es_estructura = 0;
                for (i = 0; i < e->total_estructuras; i++) if (e->info_estructuras[i].nombre.datos && strcmp(e->info_estructuras[i].nombre.datos, nom) == 0) { es_estructura = 1; break; }
                base_conocida = es_adt || es_estructura || base_conocida; /* base conocida ya calculada arriba */;
                if (es_adt && nargs != adt_np) { char _ma[256]; snprintf(_ma, 256, "[Synapse] Error semantico (linea %lld, columna %lld): ADT '%s' instanciado con %d argumento(s); se esperaban %d (Manual 2 seccion 8.2)", (long long)(idx>=0&&idx<e->total_nodos?e->nodos[idx].linea:0), (long long)(idx>=0&&idx<e->total_nodos?e->nodos[idx].columna:0), nom, nargs, adt_np); fprintf(stderr, "%s\n", _ma); e->hay_error_2_4 = 1; }
                        else if (!es_adt && !base_conocida) { char _mb[256]; snprintf(_mb, 256, "[Synapse] Error semantico (linea %lld, columna %lld): tipo base '%s' no definido en este programa (instanciacion '%s')", (long long)(idx>=0&&idx<e->total_nodos?e->nodos[idx].linea:0), (long long)(idx>=0&&idx<e->total_nodos?e->nodos[idx].columna:0), nom, s0); fprintf(stderr, "%s\n", _mb); e->hay_error_2_4 = 1; }
                p = lt + 1; profundidad = 0;
                // R13: dividir argumentos con profundidad (solo '>' de nivel 0 separa);
                // antes el bucle se detenia en el primer '>' y los argumentos tras un;
                // ADT anidado no se validaban recursivamente.;
                while (*p && !(*p == '>' && profundidad == 0)) {
                    const char* ini = p;
                    while (*p && !(*p == '>' && profundidad == 0) && !(*p == ',' && profundidad == 0)) { if (*p == '<') profundidad++; else if (*p == '>') profundidad--; p++; }
                    { char arg[256]; int al = (int)(p - ini); if (al > 255) al = 255; memcpy(arg, ini, al); arg[al] = 0;
                      while (arg[0] == ' ') memmove(arg, arg+1, strlen(arg)); while (arg[0] && arg[strlen(arg)-1] == ' ') arg[strlen(arg)-1] = 0;
                      _f8_tipo_instanciacion_2_4(e, arg, idx); }
                    if (*p == ',') p++; else break;
                }
            }
        }
        if (tipo.datos != NULL && tipo.datos[0] != 0) { _f8_tipo_instanciacion_2_4(est, tipo.datos, idx_nodo); }
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(tipo);
}

int main(int argc, char** argv) {
    (void)argc; (void)argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    synapse_esperar_hilos();
    synapse_esperar_fibras();
    pool_destroy();
    return 0;
}