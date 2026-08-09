// salida_metal.c - Generado por Synapse Compilador
// Lenguaje: Synapse v1.0 (#lang: es)
#pragma GCC diagnostic ignored "-Wint-to-pointer-cast"
#pragma GCC diagnostic ignored "-Wdiscarded-qualifiers"

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <string.h>
#include <assert.h>

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

#define _GEN_TMP_SIZE (4096)
#include "librerias/embedded_libs.h"

// --- Token ID constants (Manual 2 §2.3) ---
#ifndef T_SI
#define T_SI (1)
#endif
#ifndef T_SINO
#define T_SINO (2)
#endif
#ifndef T_FUNCION
#define T_FUNCION (3)
#endif
#ifndef T_RETORNAR
#define T_RETORNAR (4)
#endif
#ifndef T_LANZAR
#define T_LANZAR (5)
#endif
#ifndef T_RECUPERAR
#define T_RECUPERAR (6)
#endif
#ifndef T_ESCUCHAR
#define T_ESCUCHAR (7)
#endif
#ifndef T_MIENTRAS
#define T_MIENTRAS (8)
#endif
#ifndef T_IMPORTAR
#define T_IMPORTAR (9)
#endif
#ifndef T_ESTRUCTURA
#define T_ESTRUCTURA (10)
#endif
#ifndef T_ROMPER
#define T_ROMPER (11)
#endif
#ifndef T_SIGUIENTE
#define T_SIGUIENTE (12)
#endif
#ifndef T_PUNTO
#define T_PUNTO (13)
#endif
#ifndef T_Y
#define T_Y (14)
#endif
#ifndef T_O
#define T_O (15)
#endif
#ifndef T_NO
#define T_NO (16)
#endif
#ifndef T_VERDADERO
#define T_VERDADERO (17)
#endif
#ifndef T_FALSO
#define T_FALSO (18)
#endif
#ifndef T_IDENTIFICADOR
#define T_IDENTIFICADOR (19)
#endif
#ifndef T_NUMERO
#define T_NUMERO (20)
#endif
#ifndef T_FLOTANTE
#define T_FLOTANTE (21)
#endif
#ifndef T_CADENA
#define T_CADENA (22)
#endif
#ifndef T_MAYOR
#define T_MAYOR (23)
#endif
#ifndef T_MENOR
#define T_MENOR (24)
#endif
#ifndef T_IGUAL
#define T_IGUAL (25)
#endif
#ifndef T_DISTINTO
#define T_DISTINTO (26)
#endif
#ifndef T_MENOR_IGUAL
#define T_MENOR_IGUAL (27)
#endif
#ifndef T_MAYOR_IGUAL
#define T_MAYOR_IGUAL (28)
#endif
#ifndef T_ASIGNAR
#define T_ASIGNAR (29)
#endif
#ifndef T_MAS
#define T_MAS (30)
#endif
#ifndef T_MENOS
#define T_MENOS (31)
#endif
#ifndef T_POR
#define T_POR (32)
#endif
#ifndef T_DIV
#define T_DIV (33)
#endif
#ifndef T_MOD
#define T_MOD (34)
#endif
#ifndef T_FLECHA
#define T_FLECHA (35)
#endif
#ifndef T_COINCIDIR
#define T_COINCIDIR (36)
#endif
#ifndef T_FLECHA_DER
#define T_FLECHA_DER (37)
#endif
#ifndef T_PAREN_IZQ
#define T_PAREN_IZQ (38)
#endif
#ifndef T_PAREN_DER
#define T_PAREN_DER (39)
#endif
#ifndef T_DOSPUNTOS
#define T_DOSPUNTOS (40)
#endif
#ifndef T_COMA
#define T_COMA (41)
#endif
#ifndef T_NUEVALINEA
#define T_NUEVALINEA (42)
#endif
#ifndef T_INDENTAR
#define T_INDENTAR (43)
#endif
#ifndef T_DESINDENTAR
#define T_DESINDENTAR (44)
#endif
#ifndef T_AMPERSAND
#define T_AMPERSAND (45)
#endif
#ifndef T_INSEGURO
#define T_INSEGURO (46)
#endif
#ifndef T_IMPORTAR_C
#define T_IMPORTAR_C (47)
#endif
#ifndef T_EXTERNO
#define T_EXTERNO (48)
#endif
#ifndef T_FLECHA_IZQ
#define T_FLECHA_IZQ (49)
#endif
#ifndef T_REQUIERE
#define T_REQUIERE (50)
#endif
#ifndef T_GARANTIZA
#define T_GARANTIZA (51)
#endif
#ifndef T_CANAL
#define T_CANAL (52)
#endif
#ifndef T_ASM
#define T_ASM (53)
#endif
#ifndef T_CONSTANTE
#define T_CONSTANTE (54)
#endif
#ifndef T_PUNTOCOMA
#define T_PUNTOCOMA (55)
#endif
#ifndef T_PARA
#define T_PARA (56)
#endif
#ifndef T_CORCH_IZQ
#define T_CORCH_IZQ (57)
#endif
#ifndef T_CORCH_DER
#define T_CORCH_DER (58)
#endif
#ifndef T_PIPE
#define T_PIPE (59)
#endif
#ifndef T_LET
#define T_LET (60)
#endif
#ifndef T_TIPO
#define T_TIPO (61)
#endif
#ifndef T_TENSOR
#define T_TENSOR (62)
#endif
#ifndef T_NULO
#define T_NULO (63)
#endif
#ifndef T_OK
#define T_OK (64)
#endif
#ifndef T_ERR
#define T_ERR (65)
#endif
#ifndef T_ALGUN
#define T_ALGUN (66)
#endif
#ifndef T_NINGUNO
#define T_NINGUNO (67)
#endif
#ifndef T_MODULO
#define T_MODULO (68)
#endif
#ifndef T_DELEGAR
#define T_DELEGAR (69)
#endif
#ifndef T_EXPORT
#define T_EXPORT (70)
#endif
#ifndef T_RC
#define T_RC (71)
#endif
#ifndef T_ARC
#define T_ARC (72)
#endif
#ifndef T_DEBIL
#define T_DEBIL (73)
#endif
#ifndef T_FIN
#define T_FIN (74)
#endif
#ifndef T_INTERROGACION
#define T_INTERROGACION (75)
#endif

// --- Nodo type constants (AST node types) ---
#ifndef NODO_PROGRAMA
#define NODO_PROGRAMA (1)
#endif
#ifndef NODO_FUNCION
#define NODO_FUNCION (2)
#endif
#ifndef NODO_SI
#define NODO_SI (3)
#endif
#ifndef NODO_MIENTRAS
#define NODO_MIENTRAS (4)
#endif
#ifndef NODO_RETORNAR
#define NODO_RETORNAR (5)
#endif
#ifndef NODO_EXPR
#define NODO_EXPR (6)
#endif
#ifndef NODO_ASIGNACION
#define NODO_ASIGNACION (7)
#endif
#ifndef NODO_IDENTIFICADOR
#define NODO_IDENTIFICADOR (8)
#endif
#ifndef NODO_NUMERO
#define NODO_NUMERO (9)
#endif
#ifndef NODO_DECIMAL
#define NODO_DECIMAL (10)
#endif
#ifndef NODO_CADENA_LIT
#define NODO_CADENA_LIT (11)
#endif
#ifndef NODO_BINARIA
#define NODO_BINARIA (12)
#endif
#ifndef NODO_UNARIA
#define NODO_UNARIA (13)
#endif
#ifndef NODO_LLAMADA
#define NODO_LLAMADA (14)
#endif
#ifndef NODO_PARAMETRO
#define NODO_PARAMETRO (15)
#endif
#ifndef NODO_ESTRUCTURA
#define NODO_ESTRUCTURA (16)
#endif
#ifndef NODO_IMPORTAR
#define NODO_IMPORTAR (17)
#endif
#ifndef NODO_LANZAR
#define NODO_LANZAR (18)
#endif
#ifndef NODO_ESCUCHAR
#define NODO_ESCUCHAR (19)
#endif
#ifndef NODO_ROMPER
#define NODO_ROMPER (20)
#endif
#ifndef NODO_SIGUIENTE
#define NODO_SIGUIENTE (21)
#endif
#ifndef NODO_BOOLEANO
#define NODO_BOOLEANO (22)
#endif
#ifndef NODO_CONSTANTE
#define NODO_CONSTANTE (23)
#endif
#ifndef NODO_INSEGURO
#define NODO_INSEGURO (24)
#endif
#ifndef NODO_IMPORTAR_C
#define NODO_IMPORTAR_C (25)
#endif
#ifndef NODO_EXTERNO
#define NODO_EXTERNO (26)
#endif
#ifndef NODO_RECUPERAR
#define NODO_RECUPERAR (27)
#endif
#ifndef NODO_TENSOR
#define NODO_TENSOR (28)
#endif
#ifndef NODO_INDICE
#define NODO_INDICE (29)
#endif
#ifndef NODO_TRANSFERIDO
#define NODO_TRANSFERIDO (30)
#endif
#ifndef NODO_ACCESO_CAMPO
#define NODO_ACCESO_CAMPO (31)
#endif
#ifndef NODO_ASIGNACION_CAMPO
#define NODO_ASIGNACION_CAMPO (32)
#endif
#ifndef NODO_PARRAFO
#define NODO_PARRAFO (33)
#endif
#ifndef NODO_DECLARACION
#define NODO_DECLARACION (34)
#endif
#ifndef NODO_LOG
#define NODO_LOG (35)
#endif
#ifndef NODO_PUNTERO
#define NODO_PUNTERO (36)
#endif
#ifndef NODO_DEREF
#define NODO_DEREF (37)
#endif
#ifndef NODO_COINCIDIR
#define NODO_COINCIDIR (38)
#endif
#ifndef NODO_CASO
#define NODO_CASO (39)
#endif
#ifndef NODO_ASM
#define NODO_ASM (40)
#endif
#ifndef NODO_CANAL_CREAR
#define NODO_CANAL_CREAR (41)
#endif
#ifndef NODO_ENVIAR_CANAL
#define NODO_ENVIAR_CANAL (42)
#endif
#ifndef NODO_RECIBIR_CANAL
#define NODO_RECIBIR_CANAL (43)
#endif
#ifndef NODO_VACIO
#define NODO_VACIO (44)
#endif
#ifndef NODO_PARA
#define NODO_PARA (45)
#endif
#ifndef NODO_CONTRATO
#define NODO_CONTRATO (46)
#endif
#ifndef NODO_NULO
#define NODO_NULO (47)
#endif
#ifndef NODO_LET
#define NODO_LET (48)
#endif
#ifndef NODO_DELEGAR
#define NODO_DELEGAR (49)
#endif
#ifndef NODO_EXPORT
#define NODO_EXPORT (50)
#endif
#ifndef NODO_DECLARACION_TIPO
#define NODO_DECLARACION_TIPO (51)
#endif
#ifndef NODO_CONSTRUCTOR
#define NODO_CONSTRUCTOR (52)
#endif
#ifndef NODO_PROPAGAR
#define NODO_PROPAGAR (53)
#endif

// --- Error code constants (Manual 3 §3.5) ---
#ifndef ERR_SYNTAX_EXPECTED_TOKEN
#define ERR_SYNTAX_EXPECTED_TOKEN (1)
#endif
#ifndef ERR_SYNTAX_UNEXPECTED_TOKEN
#define ERR_SYNTAX_UNEXPECTED_TOKEN (2)
#endif
#ifndef ERR_SYNTAX_UNEXPECTED_EXPR
#define ERR_SYNTAX_UNEXPECTED_EXPR (3)
#endif
#ifndef ERR_SYNTAX_EXPECTED_NEWLINE
#define ERR_SYNTAX_EXPECTED_NEWLINE (4)
#endif
#ifndef ERR_LANG_MISSING
#define ERR_LANG_MISSING (5)
#endif
#ifndef ERR_LANG_UNSUPPORTED
#define ERR_LANG_UNSUPPORTED (6)
#endif
#ifndef ERR_INDENT_INVALID
#define ERR_INDENT_INVALID (7)
#endif
#ifndef ERR_INDENT_INCONSISTENT
#define ERR_INDENT_INCONSISTENT (8)
#endif
#ifndef ERR_STRING_UNCLOSED
#define ERR_STRING_UNCLOSED (9)
#endif
#ifndef ERR_LEX_CHAR_UNEXPECTED
#define ERR_LEX_CHAR_UNEXPECTED (10)
#endif
#ifndef ERR_LEX
#define ERR_LEX (11)
#endif
#ifndef ERR_FILE_NOT_FOUND
#define ERR_FILE_NOT_FOUND (12)
#endif
#ifndef ERR_CANONICAL_FORMAT
#define ERR_CANONICAL_FORMAT (13)
#endif
#ifndef ERR_SEM_VAR_NO_DECLARADA
#define ERR_SEM_VAR_NO_DECLARADA (14)
#endif
#ifndef ERR_SEM_TIPO_INCOMPATIBLE
#define ERR_SEM_TIPO_INCOMPATIBLE (15)
#endif
#ifndef ERR_SEM_TIPO_RETORNO
#define ERR_SEM_TIPO_RETORNO (16)
#endif
#ifndef ERR_SEM_FUNC_NO_DEFINIDA
#define ERR_SEM_FUNC_NO_DEFINIDA (17)
#endif
#ifndef ERR_SEM_REDEFINICION
#define ERR_SEM_REDEFINICION (18)
#endif
#ifndef ERR_SEM_ARGUMENTOS_INVALIDOS
#define ERR_SEM_ARGUMENTOS_INVALIDOS (19)
#endif
#ifndef ERR_SEM_ESTRUCTURA_NO_DEFINIDA
#define ERR_SEM_ESTRUCTURA_NO_DEFINIDA (20)
#endif
#ifndef ERR_SEM_CAMPO_NO_EXISTE
#define ERR_SEM_CAMPO_NO_EXISTE (21)
#endif
#ifndef ERR_SEM_VAR_MOVIDA
#define ERR_SEM_VAR_MOVIDA (22)
#endif
#ifndef ERR_SEM_ACCESO_MEMORIA_MOVIDA
#define ERR_SEM_ACCESO_MEMORIA_MOVIDA (23)
#endif
#ifndef ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR
#define ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR (24)
#endif
#ifndef ERR_MANIFEST_NOT_FOUND
#define ERR_MANIFEST_NOT_FOUND (25)
#endif
#ifndef ERR_MODULE_STD_NOT_FOUND
#define ERR_MODULE_STD_NOT_FOUND (26)
#endif
#ifndef ERR_MODULE_AXON_NOT_FOUND
#define ERR_MODULE_AXON_NOT_FOUND (27)
#endif
#ifndef ERR_DEP_NOT_DECLARED
#define ERR_DEP_NOT_DECLARED (28)
#endif
#ifndef ERR_LOCK_HASH_MISMATCH
#define ERR_LOCK_HASH_MISMATCH (29)
#endif
#ifndef ERR_GIT_FAILURE
#define ERR_GIT_FAILURE (30)
#endif
#ifndef ERR_SEM_ASM_FUERA_INSEGURO
#define ERR_SEM_ASM_FUERA_INSEGURO (31)
#endif
#ifndef ERR_SEM_CONSTANTE_INMUTABLE
#define ERR_SEM_CONSTANTE_INMUTABLE (32)
#endif
#ifndef ERR_MEM_USE_AFTER_MOVE
#define ERR_MEM_USE_AFTER_MOVE (33)
#endif
#ifndef ERR_VER_WHILE_INACOTADO
#define ERR_VER_WHILE_INACOTADO (34)
#endif
#ifndef ERR_VER_MUTACION_GLOBAL
#define ERR_VER_MUTACION_GLOBAL (35)
#endif
#ifndef ERR_VER_RECURSION_NO_TERMINAL
#define ERR_VER_RECURSION_NO_TERMINAL (36)
#endif
#ifndef ERR_VER_CONTRATO_INVALIDO
#define ERR_VER_CONTRATO_INVALIDO (37)
#endif
#ifndef ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED
#define ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED (38)
#endif
#ifndef ERR_MEM_BORROW_CONFLICT
#define ERR_MEM_BORROW_CONFLICT (39)
#endif
#ifndef ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED
#define ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED (33)
#endif
#ifndef ERR_MEM_LIFETIME_MISMATCH
#define ERR_MEM_LIFETIME_MISMATCH (34)
#endif
#ifndef ERR_MEM_LIFETIME_CYCLE
#define ERR_MEM_LIFETIME_CYCLE (35)
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

// ME-B6: tipos de retorno de funciones definidas (inferencia de tipos nativa)
extern char _G_native_func_returns[512][64];
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
extern char _G_tipo_aliases[128][64];
extern char _G_tipo_aliases_base[128][64];
extern int _G_tipo_aliases_count;

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
extern void cerrar(Canal canal);
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
extern void synapse_lanzar_hilo(void* (*fn)(void*), void* arg);
extern void synapse_esperar_hilos(void);
extern void _syn_texto_liberar(CadenaSegura s);

typedef struct { int es_ok; union {
void* ok_valor; const char* err_mensaje;
} datos; } Resultado_T;
typedef struct CanalConcurrencia CanalConcurrencia;
extern CanalConcurrencia* canal_crear(uint32_t capacidad);
extern void canal_enviar(CanalConcurrencia* canal, void* paquete);
extern void* canal_recibir(CanalConcurrencia* canal);
extern void canal_destruir(CanalConcurrencia* canal);
extern void cerrar_canal(CanalConcurrencia* canal);
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

char _G_native_func_returns[512][64];
int _G_native_func_returns_count;
int _G_native_tipo_retorno(const char* fn, char* out) {
    if (!fn || !out) return 0;
    for (int _i = 0; _i < _G_native_func_returns_count; _i++) {
        if (strcmp(_G_native_func_returns[_i], fn) == 0) {
            strcpy(out, _G_native_func_returns[_i + 256]); return 1;
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
char _G_tipo_aliases[128][64];
char _G_tipo_aliases_base[128][64];
int _G_tipo_aliases_count;


int _g_argc;
char** _g_argv;
int _argc() { return _g_argc; }

CadenaSegura _argv(int i) {
    if (i < 0 || i >= _g_argc) return (CadenaSegura){0, ""};
    return (CadenaSegura){ .longitud = (int)strlen(_g_argv[i]), .datos = _g_argv[i] };
}

void salir(int codigo) { exit(codigo); }

CadenaSegura concat(CadenaSegura a, CadenaSegura b) {
    int _tl = a.longitud + b.longitud;
    char* _buf = (char*)malloc(_tl + 1);
    if (!_buf) { fprintf(stderr,"Error: malloc fallo en concat()\\n"); exit(1); }
    memcpy(_buf, a.datos, a.longitud);
    memcpy(_buf + a.longitud, b.datos, b.longitud);
    _buf[_tl] = 0;
    return (CadenaSegura){_tl, _buf};
}

struct NodoLista;

typedef struct NodoLista {
    int64_t valor;
    void* siguiente;
} NodoLista;

typedef int64_t Edad;

void principal(void);

void principal(void) {
    _simd_detectar();
    int64_t x = 5LL;
    int64_t edad = 10LL;
    CadenaSegura s = (CadenaSegura){ .longitud = (int)strlen("hola"), .datos = "hola" };
    void* ref = nulo;
    Tensor t = crear_tensor(2LL, 3LL);
    escribir_linea(entero_a_texto((x + edad)));
    escribir_linea(s);
    escribir_linea(entero_a_texto(t.filas));
    return;
    if (!t.es_mapeado) { pool_free(t.datos); }
      /* [Lifetime Scope: exit depth=0] */
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    principal();
    synapse_esperar_hilos();
    pool_destroy();
    return 0;
}