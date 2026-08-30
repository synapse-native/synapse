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

typedef struct { int longitud; const char* datos; } CadenaSegura;  // cumple Manual 2 §4.1

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

struct GestorDiagnostico;
struct ReporteError;

typedef struct GestorDiagnostico {
    struct ReporteError* reportes;
    int64_t total_reportes;
    int64_t capacidad;
    CadenaSegura idioma;
    CadenaSegura ruta_archivo;
} GestorDiagnostico;

typedef struct ReporteError {
    int64_t codigo;
    int64_t linea;
    int64_t columna;
    CadenaSegura mensaje;
} ReporteError;

static inline int risky_call(void) { return 0; }
int64_t codigo_salida(struct GestorDiagnostico diag);
int64_t contar_errores(struct GestorDiagnostico diag);
CadenaSegura formatear_entrada_error(CadenaSegura ruta, int64_t linea, int64_t columna, CadenaSegura mensaje);
CadenaSegura formatear_ubicacion(CadenaSegura ruta, int64_t linea, int64_t columna);
struct GestorDiagnostico gestor_nuevo(CadenaSegura idioma, CadenaSegura ruta, int64_t capacidad);
int hay_errores(struct GestorDiagnostico diag);
CadenaSegura obtener_linea_contexto(CadenaSegura lineas, int64_t linea_num);
CadenaSegura obtener_plantilla_error(int64_t codigo, CadenaSegura idioma);
void reportar_error(struct GestorDiagnostico diag, int64_t codigo, int64_t linea, int64_t columna, CadenaSegura mensaje);
CadenaSegura resumen_errores(struct GestorDiagnostico diag);

#define ERR_SYNTAX_EXPECTED_TOKEN (1LL)
#define ERR_SYNTAX_UNEXPECTED_TOKEN (2LL)
#define ERR_SYNTAX_UNEXPECTED_EXPR (3LL)
#define ERR_SYNTAX_EXPECTED_NEWLINE (4LL)
#define ERR_LANG_MISSING (5LL)
#define ERR_LANG_UNSUPPORTED (6LL)
#define ERR_INDENT_INVALID (7LL)
#define ERR_INDENT_INCONSISTENT (8LL)
#define ERR_STRING_UNCLOSED (9LL)
#define ERR_LEX_CHAR_UNEXPECTED (10LL)
#define ERR_LEX (11LL)
#define ERR_FILE_NOT_FOUND (12LL)
#define ERR_CANONICAL_FORMAT (13LL)
#define ERR_SEM_VAR_NO_DECLARADA (14LL)
#define ERR_SEM_TIPO_INCOMPATIBLE (15LL)
#define ERR_SEM_TIPO_RETORNO (16LL)
#define ERR_SEM_FUNC_NO_DEFINIDA (17LL)
#define ERR_SEM_REDEFINICION (18LL)
#define ERR_SEM_ARGUMENTOS_INVALIDOS (19LL)
#define ERR_SEM_ESTRUCTURA_NO_DEFINIDA (20LL)
#define ERR_SEM_CAMPO_NO_EXISTE (21LL)
#define ERR_SEM_VAR_MOVIDA (22LL)
#define ERR_MEM_USE_AFTER_MOVE (23LL)
#define ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR (24LL)
#define ERR_MANIFEST_NOT_FOUND (25LL)
#define ERR_MODULE_STD_NOT_FOUND (26LL)
#define ERR_MODULE_AXON_NOT_FOUND (27LL)
#define ERR_DEP_NOT_DECLARED (28LL)
#define ERR_LOCK_HASH_MISMATCH (29LL)
#define ERR_GIT_FAILURE (30LL)
#define ERR_SEM_ASM_FUERA_INSEGURO (31LL)
#define ERR_SEM_CONSTANTE_INMUTABLE (32LL)
#define ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED (33LL)
#define ERR_MEM_LIFETIME_MISMATCH (34LL)
#define ERR_MEM_LIFETIME_CYCLE (35LL)
#define ERR_MEM_BORROW_CONFLICT (39LL)
int64_t codigo_salida(struct GestorDiagnostico diag) {
    if ((hay_errores(diag) == 1)) {
        return 1LL;
          /* [Lifetime Scope: exit depth=1] */
    }
    return 0LL;
      /* [Lifetime Scope: exit depth=0] */
}

int64_t contar_errores(struct GestorDiagnostico diag) {
    return diag.total_reportes;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura formatear_entrada_error(CadenaSegura ruta, int64_t linea, int64_t columna, CadenaSegura mensaje) {
    CadenaSegura r = {0};
    _syn_texto_liberar(r);
    r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        { char _buf[1024]; snprintf(_buf, 1024, "[Synapse] %s:%d:%d - %s", ruta.datos, linea, columna, mensaje.datos); r = (CadenaSegura){ .longitud = (int)strlen(_buf), .datos = strdup(_buf) }; }
          /* [Lifetime Scope: exit depth=1] */
    }
    _syn_texto_liberar(ruta);
    _syn_texto_liberar(mensaje);
    return r;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura formatear_ubicacion(CadenaSegura ruta, int64_t linea, int64_t columna) {
    CadenaSegura r = {0};
    if ((linea > 0LL)) {
        _syn_texto_liberar(r);
        r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        { /* unsafe */
            { char _buf[256]; snprintf(_buf, 256, "%s:%d:%d", ruta.datos, linea, columna); r = (CadenaSegura){ .longitud = (int)strlen(_buf), .datos = strdup(_buf) }; }
              /* [Lifetime Scope: exit depth=2] */
        }
        _syn_texto_liberar(ruta);
        return r;
          /* [Lifetime Scope: exit depth=1] */
    }
    return ruta;
      /* [Lifetime Scope: exit depth=0] */
}

struct GestorDiagnostico gestor_nuevo(CadenaSegura idioma, CadenaSegura ruta, int64_t capacidad) {
    struct GestorDiagnostico g;
    g = (struct GestorDiagnostico){0};
    g.idioma = idioma;
    g.ruta_archivo = ruta;
    g.total_reportes = 0LL;
    g.capacidad = capacidad;
    _syn_texto_liberar(ruta);
    _syn_texto_liberar(idioma);
    return g;
      /* [Lifetime Scope: exit depth=0] */
}

int hay_errores(struct GestorDiagnostico diag) {
    if ((diag.total_reportes > 0LL)) {
        return 1;
          /* [Lifetime Scope: exit depth=1] */
    }
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura obtener_linea_contexto(CadenaSegura lineas, int64_t linea_num) {
    CadenaSegura r = {0};
    _syn_texto_liberar(r);
    r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        // buscar linea_num en buffer de lineas (pendiente);
          /* [Lifetime Scope: exit depth=1] */
    }
    _syn_texto_liberar(lineas);
    return r;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura obtener_plantilla_error(int64_t codigo, CadenaSegura idioma) {
    if ((str_eq(idioma, (CadenaSegura){ .longitud = (int)strlen("es"), .datos = "es" }) == 1)) {
        if ((codigo == ERR_SYNTAX_EXPECTED_TOKEN)) {
            _syn_texto_liberar(idioma);
            return (CadenaSegura){ .longitud = (int)strlen("Se esperaba {esperado}, se encontro '{encontrado}'"), .datos = "Se esperaba {esperado}, se encontro '{encontrado}'" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SYNTAX_UNEXPECTED_TOKEN)) {
            return (CadenaSegura){ .longitud = (int)strlen("Token inesperado '{tok_name}' tras expresion"), .datos = "Token inesperado '{tok_name}' tras expresion" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SYNTAX_UNEXPECTED_EXPR)) {
            return (CadenaSegura){ .longitud = (int)strlen("Expresion inesperada: '{tipo}'"), .datos = "Expresion inesperada: '{tipo}'" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SYNTAX_EXPECTED_NEWLINE)) {
            return (CadenaSegura){ .longitud = (int)strlen("Se esperaba nueva linea despues de '{construccion}'"), .datos = "Se esperaba nueva linea despues de '{construccion}'" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_LANG_MISSING)) {
            return (CadenaSegura){ .longitud = (int)strlen("Falta declaracion de idioma '#lang: <codigo>' en la linea 1"), .datos = "Falta declaracion de idioma '#lang: <codigo>' en la linea 1" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_LANG_UNSUPPORTED)) {
            return (CadenaSegura){ .longitud = (int)strlen("Idioma '{idioma}' no soportado"), .datos = "Idioma '{idioma}' no soportado" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_INDENT_INVALID)) {
            return (CadenaSegura){ .longitud = (int)strlen("La indentacion debe ser multiplo de 4 espacios"), .datos = "La indentacion debe ser multiplo de 4 espacios" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_INDENT_INCONSISTENT)) {
            return (CadenaSegura){ .longitud = (int)strlen("Nivel de indentacion inconsistente"), .datos = "Nivel de indentacion inconsistente" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_STRING_UNCLOSED)) {
            return (CadenaSegura){ .longitud = (int)strlen("Cadena sin cerrar"), .datos = "Cadena sin cerrar" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_LEX)) {
            return (CadenaSegura){ .longitud = (int)strlen("{mensaje}"), .datos = "{mensaje}" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_LEX_CHAR_UNEXPECTED)) {
            return (CadenaSegura){ .longitud = (int)strlen("Caracter inesperado '{char}'"), .datos = "Caracter inesperado '{char}'" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_FILE_NOT_FOUND)) {
            return (CadenaSegura){ .longitud = (int)strlen("Archivo no encontrado: {archivo}"), .datos = "Archivo no encontrado: {archivo}" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_CANONICAL_FORMAT)) {
            return (CadenaSegura){ .longitud = (int)strlen("Formato canonico no reconocido o corrupto"), .datos = "Formato canonico no reconocido o corrupto" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SEM_VAR_NO_DECLARADA)) {
            return (CadenaSegura){ .longitud = (int)strlen("Variable '{nombre}' no declarada en este ambito"), .datos = "Variable '{nombre}' no declarada en este ambito" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SEM_TIPO_INCOMPATIBLE)) {
            return (CadenaSegura){ .longitud = (int)strlen("Tipos incompatibles: no se puede usar '{tipo1}' con '{tipo2}' en '{operacion}'"), .datos = "Tipos incompatibles: no se puede usar '{tipo1}' con '{tipo2}' en '{operacion}'" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SEM_TIPO_RETORNO)) {
            return (CadenaSegura){ .longitud = (int)strlen("Tipo de retorno incorrecto: se esperaba '{esperado}', se obtuvo '{obtenido}'"), .datos = "Tipo de retorno incorrecto: se esperaba '{esperado}', se obtuvo '{obtenido}'" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SEM_FUNC_NO_DEFINIDA)) {
            return (CadenaSegura){ .longitud = (int)strlen("Funcion '{nombre}' no definida"), .datos = "Funcion '{nombre}' no definida" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SEM_REDEFINICION)) {
            return (CadenaSegura){ .longitud = (int)strlen("Redefinicion de '{nombre}' en el mismo ambito"), .datos = "Redefinicion de '{nombre}' en el mismo ambito" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SEM_ARGUMENTOS_INVALIDOS)) {
            return (CadenaSegura){ .longitud = (int)strlen("Cantidad de argumentos invalida para '{nombre}': se esperaban {esperados}"), .datos = "Cantidad de argumentos invalida para '{nombre}': se esperaban {esperados}" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SEM_ESTRUCTURA_NO_DEFINIDA)) {
            return (CadenaSegura){ .longitud = (int)strlen("Estructura '{nombre}' no definida"), .datos = "Estructura '{nombre}' no definida" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SEM_CAMPO_NO_EXISTE)) {
            return (CadenaSegura){ .longitud = (int)strlen("La estructura '{struct}' no tiene un campo '{campo}'"), .datos = "La estructura '{struct}' no tiene un campo '{campo}'" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SEM_VAR_MOVIDA)) {
            return (CadenaSegura){ .longitud = (int)strlen("Uso ilegal de variable ya movida '{nombre}'"), .datos = "Uso ilegal de variable ya movida '{nombre}'" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_MEM_USE_AFTER_MOVE)) {
            return (CadenaSegura){ .longitud = (int)strlen("Acceso prohibido a memoria movida '{nombre}'"), .datos = "Acceso prohibido a memoria movida '{nombre}'" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR)) {
            return (CadenaSegura){ .longitud = (int)strlen("Resultado de canal sin desempaquetar"), .datos = "Resultado de canal sin desempaquetar" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_MANIFEST_NOT_FOUND)) {
            return (CadenaSegura){ .longitud = (int)strlen("Manifiesto axon.toml no encontrado en el directorio actual"), .datos = "Manifiesto axon.toml no encontrado en el directorio actual" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_MODULE_STD_NOT_FOUND)) {
            return (CadenaSegura){ .longitud = (int)strlen("Modulo estandar '{modulo}' no encontrado. Sysroot corrupto"), .datos = "Modulo estandar '{modulo}' no encontrado. Sysroot corrupto" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_MODULE_AXON_NOT_FOUND)) {
            return (CadenaSegura){ .longitud = (int)strlen("Dependencia '{modulo}' no encontrada en axon_modules"), .datos = "Dependencia '{modulo}' no encontrada en axon_modules" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_DEP_NOT_DECLARED)) {
            return (CadenaSegura){ .longitud = (int)strlen("Dependencia '{modulo}' importada en el codigo pero no declarada en axon.toml"), .datos = "Dependencia '{modulo}' importada en el codigo pero no declarada en axon.toml" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_LOCK_HASH_MISMATCH)) {
            return (CadenaSegura){ .longitud = (int)strlen("El hash de la dependencia '{modulo}' no coincide con axon.lock"), .datos = "El hash de la dependencia '{modulo}' no coincide con axon.lock" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_GIT_FAILURE)) {
            return (CadenaSegura){ .longitud = (int)strlen("Error de red o revision Git invalida para la dependencia '{modulo}'"), .datos = "Error de red o revision Git invalida para la dependencia '{modulo}'" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SEM_ASM_FUERA_INSEGURO)) {
            return (CadenaSegura){ .longitud = (int)strlen("asm() solo puede usarse dentro de un bloque 'inseguro:'"), .datos = "asm() solo puede usarse dentro de un bloque 'inseguro:'" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SEM_CONSTANTE_INMUTABLE)) {
            return (CadenaSegura){ .longitud = (int)strlen("No se puede reasignar la constante '{nombre}'"), .datos = "No se puede reasignar la constante '{nombre}'" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED)) {
            return (CadenaSegura){ .longitud = (int)strlen("Sentencia 'coincidir' no exhaustiva: faltan {faltan} variante(s). Use '_' como comodin o anada los casos faltantes"), .datos = "Sentencia 'coincidir' no exhaustiva: faltan {faltan} variante(s). Use '_' como comodin o anada los casos faltantes" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_MEM_LIFETIME_MISMATCH)) {
            return (CadenaSegura){ .longitud = (int)strlen("Violacion de lifetime: la referencia '{nombre}' no vive lo suficiente (alcance {alcance}) vs. requerido {requerido}"), .datos = "Violacion de lifetime: la referencia '{nombre}' no vive lo suficiente (alcance {alcance}) vs. requerido {requerido}" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_MEM_LIFETIME_CYCLE)) {
            return (CadenaSegura){ .longitud = (int)strlen("Ciclo de lifetime detectado: las referencias '{a}' y '{b}' forman un ciclo de dependencia"), .datos = "Ciclo de lifetime detectado: las referencias '{a}' y '{b}' forman un ciclo de dependencia" };
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((codigo == ERR_MEM_BORROW_CONFLICT)) {
            return (CadenaSegura){ .longitud = (int)strlen("Conflicto de prestamo: la variable '{nombre}' tiene prestamos incompatibles (inmutable+mutable o multiples mutables)"), .datos = "Conflicto de prestamo: la variable '{nombre}' tiene prestamos incompatibles (inmutable+mutable o multiples mutables)" };
              /* [Lifetime Scope: exit depth=2] */
        }
        return (CadenaSegura){ .longitud = (int)strlen("Error desconocido"), .datos = "Error desconocido" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SYNTAX_EXPECTED_TOKEN)) {
        return (CadenaSegura){ .longitud = (int)strlen("Expected {esperado}, found '{encontrado}'"), .datos = "Expected {esperado}, found '{encontrado}'" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SYNTAX_UNEXPECTED_TOKEN)) {
        return (CadenaSegura){ .longitud = (int)strlen("Unexpected token '{tok_name}' after expression"), .datos = "Unexpected token '{tok_name}' after expression" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SYNTAX_UNEXPECTED_EXPR)) {
        return (CadenaSegura){ .longitud = (int)strlen("Unexpected expression: '{tipo}'"), .datos = "Unexpected expression: '{tipo}'" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SYNTAX_EXPECTED_NEWLINE)) {
        return (CadenaSegura){ .longitud = (int)strlen("Expected newline after '{construccion}'"), .datos = "Expected newline after '{construccion}'" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_LANG_MISSING)) {
        return (CadenaSegura){ .longitud = (int)strlen("Missing language declaration '#lang: <code>' at line 1"), .datos = "Missing language declaration '#lang: <code>' at line 1" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_LANG_UNSUPPORTED)) {
        return (CadenaSegura){ .longitud = (int)strlen("Language '{idioma}' not supported"), .datos = "Language '{idioma}' not supported" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_INDENT_INVALID)) {
        return (CadenaSegura){ .longitud = (int)strlen("Indentation must be a multiple of 4 spaces"), .datos = "Indentation must be a multiple of 4 spaces" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_INDENT_INCONSISTENT)) {
        return (CadenaSegura){ .longitud = (int)strlen("Inconsistent indentation level"), .datos = "Inconsistent indentation level" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_STRING_UNCLOSED)) {
        return (CadenaSegura){ .longitud = (int)strlen("Unclosed string literal"), .datos = "Unclosed string literal" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_LEX)) {
        return (CadenaSegura){ .longitud = (int)strlen("{mensaje}"), .datos = "{mensaje}" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_LEX_CHAR_UNEXPECTED)) {
        return (CadenaSegura){ .longitud = (int)strlen("Unexpected character '{char}'"), .datos = "Unexpected character '{char}'" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_FILE_NOT_FOUND)) {
        return (CadenaSegura){ .longitud = (int)strlen("File not found: {archivo}"), .datos = "File not found: {archivo}" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_CANONICAL_FORMAT)) {
        return (CadenaSegura){ .longitud = (int)strlen("Unrecognized or corrupted canonical format"), .datos = "Unrecognized or corrupted canonical format" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SEM_VAR_NO_DECLARADA)) {
        return (CadenaSegura){ .longitud = (int)strlen("Variable '{nombre}' not declared in this scope"), .datos = "Variable '{nombre}' not declared in this scope" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SEM_TIPO_INCOMPATIBLE)) {
        return (CadenaSegura){ .longitud = (int)strlen("Incompatible types: cannot use '{tipo1}' with '{tipo2}' in '{operacion}'"), .datos = "Incompatible types: cannot use '{tipo1}' with '{tipo2}' in '{operacion}'" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SEM_TIPO_RETORNO)) {
        return (CadenaSegura){ .longitud = (int)strlen("Incorrect return type: expected '{esperado}', got '{obtenido}'"), .datos = "Incorrect return type: expected '{esperado}', got '{obtenido}'" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SEM_FUNC_NO_DEFINIDA)) {
        return (CadenaSegura){ .longitud = (int)strlen("Function '{nombre}' not defined"), .datos = "Function '{nombre}' not defined" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SEM_REDEFINICION)) {
        return (CadenaSegura){ .longitud = (int)strlen("Redefinition of '{nombre}' in the same scope"), .datos = "Redefinition of '{nombre}' in the same scope" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SEM_ARGUMENTOS_INVALIDOS)) {
        return (CadenaSegura){ .longitud = (int)strlen("Invalid argument count for '{nombre}': expected {esperados}"), .datos = "Invalid argument count for '{nombre}': expected {esperados}" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SEM_ESTRUCTURA_NO_DEFINIDA)) {
        return (CadenaSegura){ .longitud = (int)strlen("Struct '{nombre}' not defined"), .datos = "Struct '{nombre}' not defined" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SEM_CAMPO_NO_EXISTE)) {
        return (CadenaSegura){ .longitud = (int)strlen("Struct '{struct}' has no field '{campo}'"), .datos = "Struct '{struct}' has no field '{campo}'" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SEM_VAR_MOVIDA)) {
        return (CadenaSegura){ .longitud = (int)strlen("Illegal use of already moved variable '{nombre}'"), .datos = "Illegal use of already moved variable '{nombre}'" };
        if ((codigo == ERR_MEM_USE_AFTER_MOVE)) {
            return (CadenaSegura){ .longitud = (int)strlen("Forbidden access to moved memory '{nombre}'"), .datos = "Forbidden access to moved memory '{nombre}'" };
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR)) {
        return (CadenaSegura){ .longitud = (int)strlen("Unpacked channel result"), .datos = "Unpacked channel result" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_MANIFEST_NOT_FOUND)) {
        return (CadenaSegura){ .longitud = (int)strlen("axon.toml manifest not found in current directory"), .datos = "axon.toml manifest not found in current directory" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_MODULE_STD_NOT_FOUND)) {
        return (CadenaSegura){ .longitud = (int)strlen("Standard module '{modulo}' not found. Corrupt Sysroot"), .datos = "Standard module '{modulo}' not found. Corrupt Sysroot" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_MODULE_AXON_NOT_FOUND)) {
        return (CadenaSegura){ .longitud = (int)strlen("Dependency '{modulo}' not found in axon_modules"), .datos = "Dependency '{modulo}' not found in axon_modules" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_DEP_NOT_DECLARED)) {
        return (CadenaSegura){ .longitud = (int)strlen("Dependency '{modulo}' imported in code but not declared in axon.toml"), .datos = "Dependency '{modulo}' imported in code but not declared in axon.toml" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_LOCK_HASH_MISMATCH)) {
        return (CadenaSegura){ .longitud = (int)strlen("Hash of dependency '{modulo}' does not match axon.lock"), .datos = "Hash of dependency '{modulo}' does not match axon.lock" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_GIT_FAILURE)) {
        return (CadenaSegura){ .longitud = (int)strlen("Network error or invalid Git revision for dependency '{modulo}'"), .datos = "Network error or invalid Git revision for dependency '{modulo}'" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SEM_ASM_FUERA_INSEGURO)) {
        return (CadenaSegura){ .longitud = (int)strlen("asm() can only be used inside an 'unsafe:' block"), .datos = "asm() can only be used inside an 'unsafe:' block" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SEM_CONSTANTE_INMUTABLE)) {
        return (CadenaSegura){ .longitud = (int)strlen("Cannot reassign constant '{nombre}'"), .datos = "Cannot reassign constant '{nombre}'" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED)) {
        return (CadenaSegura){ .longitud = (int)strlen("Non-exhaustive 'match' pattern: missing {faltan} variant(s). Add remaining cases or use '_' wildcard"), .datos = "Non-exhaustive 'match' pattern: missing {faltan} variant(s). Add remaining cases or use '_' wildcard" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_MEM_LIFETIME_MISMATCH)) {
        return (CadenaSegura){ .longitud = (int)strlen("Lifetime violation: reference '{nombre}' does not live long enough (scope {alcance}) vs required {requerido}"), .datos = "Lifetime violation: reference '{nombre}' does not live long enough (scope {alcance}) vs required {requerido}" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_MEM_LIFETIME_CYCLE)) {
        return (CadenaSegura){ .longitud = (int)strlen("Lifetime cycle detected: references '{a}' and '{b}' form a dependency cycle"), .datos = "Lifetime cycle detected: references '{a}' and '{b}' form a dependency cycle" };
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((codigo == ERR_MEM_BORROW_CONFLICT)) {
        return (CadenaSegura){ .longitud = (int)strlen("Borrow conflict: variable '{nombre}' has incompatible active borrows (immutable+mutable or multiple mutables)"), .datos = "Borrow conflict: variable '{nombre}' has incompatible active borrows (immutable+mutable or multiple mutables)" };
          /* [Lifetime Scope: exit depth=1] */
    }
    return (CadenaSegura){ .longitud = (int)strlen("Unknown error"), .datos = "Unknown error" };
      /* [Lifetime Scope: exit depth=0] */
}

void reportar_error(struct GestorDiagnostico diag, int64_t codigo, int64_t linea, int64_t columna, CadenaSegura mensaje) {
    { /* unsafe */
        if (diag.total_reportes >= diag.capacidad) return;
        diag.reportes[diag.total_reportes].codigo = codigo;
        diag.reportes[diag.total_reportes].linea = linea;
        diag.reportes[diag.total_reportes].columna = columna;
        diag.total_reportes = diag.total_reportes + 1;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
    _syn_texto_liberar(mensaje);
}

CadenaSegura resumen_errores(struct GestorDiagnostico diag) {
    if ((hay_errores(diag) == 0)) {
        return (CadenaSegura){ .longitud = (int)strlen("0 errores"), .datos = "0 errores" };
          /* [Lifetime Scope: exit depth=1] */
    }
    return concat(entero_a_texto(diag.total_reportes), (CadenaSegura){ .longitud = (int)strlen(" error(es) encontrado(s)"), .datos = " error(es) encontrado(s)" });
      /* [Lifetime Scope: exit depth=0] */
}

int main(int argc, char** argv) {
    (void)argc; (void)argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    synapse_esperar_hilos();
    synapse_esperar_fibras();
    pool_destroy();
    return 0;
}