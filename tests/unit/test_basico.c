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

static inline int risky_call(void) { return 0; }

int64_t _principal_impl(void) {
    _simd_detectar();
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("Hola"), .datos = "Hola" });
    return 0LL;
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