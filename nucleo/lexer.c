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

typedef struct { uint32_t filas; uint32_t columnas; float* datos; } Tensor;

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
#include "runtime/core/ast_nodos.h"

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
#ifndef IDIOMA_ES
#define IDIOMA_ES (0)
#endif
#ifndef IDIOMA_EN
#define IDIOMA_EN (1)
#endif
#ifndef IDIOMA_FR
#define IDIOMA_FR (2)
#endif
#ifndef IDIOMA_PT
#define IDIOMA_PT (3)
#endif
#ifndef MAX_TOKENS
#define MAX_TOKENS (16384)
#endif
#ifndef MAX_INDENT
#define MAX_INDENT (64)
#endif

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

// PGO variables (defined in self-hosted parser module)
extern int _P_ntks, _P_tpos, _P_p_err;

extern int _G_indent;

const char* _G_mt(const char* st);
void _G_vest(struct DefinicionEstructura* n);

#define TAG_OK 0
#define TAG_ERR 1
#define TAG_ALGUNO 0
#define TAG_NINGUNO 1

// --- Helpers de serialización primitiva ---
static inline void* _synapse_box_int(int v) { return (void*)(intptr_t)v; }
static inline int _synapse_unbox_int(void* p) { return (int)(intptr_t)p; }
static inline void* _synapse_box_float(float v) {
    float* _p = (float*)malloc(sizeof(float));
    if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo\\n"); exit(1); }
    *_p = v;
    return (void*)_p;
}
static inline float _synapse_unbox_float(void* p) {
    float _v = *(float*)p;
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
extern int texto_a_entero(CadenaSegura str);
extern float texto_a_decimal(CadenaSegura str);
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

struct LexerBuffers;
struct TokenLex;

typedef struct LexerBuffers {
    void* tokens;
    void* sbuf;
    void* indent_stack;
    int str_pos;
    int ntks;
    int total_tokens;
    int hay_error;
    int idioma;
    int linea_actual;
    int nivel_pila;
} LexerBuffers;

typedef struct TokenLex {
    int tipo;
    int linea;
    int columna;
    CadenaSegura valor;
} TokenLex;

int es_alnum(int c);
int es_digito(int c);
int es_letra(int c);
int keyword_token(CadenaSegura palabra, int idioma);
int keyword_token_en(CadenaSegura palabra);
int keyword_token_es(CadenaSegura palabra);
int keyword_token_fr(CadenaSegura palabra);
int keyword_token_pt(CadenaSegura palabra);
void* lexer_buffers(void);
CadenaSegura lexer_decodificar_cadena(void* ptr, int ini, int len);
int lexer_detectar_idioma(void* ptr, int len);
void lexer_error(CadenaSegura mensaje, int linea, int columna);
void lexer_fijar_linea(int n);
int lexer_hay_error(void);
int lexer_idioma_actual(void);
int lexer_linea_actual(void);
int lexer_obtener_total(void);
void lexer_procesar_indentacion(void* ptr_linea, int len_linea);
void lexer_push_token(int tipo, int linea, int columna);
void lexer_push_token_valor(int tipo, int linea, int columna, CadenaSegura valor);
void lexer_reset_buffers(void);
void lexer_tokenizar_linea(void* ptr_texto, int len_texto);
int str_char(CadenaSegura s, int i);
int str_char_at(void* ptr, int i);
int str_len(CadenaSegura s);
int str_len_ptr(void* ptr);
int tokenizar(CadenaSegura fuente);

#define T_SI (1)
#define T_SINO (2)
#define T_FUNCION (3)
#define T_RETORNAR (4)
#define T_LANZAR (5)
#define T_RECUPERAR (6)
#define T_ESCUCHAR (7)
#define T_MIENTRAS (8)
#define T_IMPORTAR (9)
#define T_ESTRUCTURA (10)
#define T_ROMPER (11)
#define T_SIGUIENTE (12)
#define T_PUNTO (13)
#define T_Y (14)
#define T_O (15)
#define T_NO (16)
#define T_VERDADERO (17)
#define T_FALSO (18)
#define T_IDENTIFICADOR (19)
#define T_NUMERO (20)
#define T_FLOTANTE (21)
#define T_CADENA (22)
#define T_MAYOR (23)
#define T_MENOR (24)
#define T_IGUAL (25)
#define T_DISTINTO (26)
#define T_MENOR_IGUAL (27)
#define T_MAYOR_IGUAL (28)
#define T_ASIGNAR (29)
#define T_MAS (30)
#define T_MENOS (31)
#define T_POR (32)
#define T_DIV (33)
#define T_MOD (34)
#define T_FLECHA (35)
#define T_COINCIDIR (36)
#define T_FLECHA_DER (37)
#define T_PAREN_IZQ (38)
#define T_PAREN_DER (39)
#define T_DOSPUNTOS (40)
#define T_COMA (41)
#define T_NUEVALINEA (42)
#define T_INDENTAR (43)
#define T_DESINDENTAR (44)
#define T_AMPERSAND (45)
#define T_INSEGURO (46)
#define T_IMPORTAR_C (47)
#define T_EXTERNO (48)
#define T_FLECHA_IZQ (49)
#define T_REQUIERE (50)
#define T_GARANTIZA (51)
#define T_CANAL (52)
#define T_ASM (53)
#define T_CONSTANTE (54)
#define T_PUNTOCOMA (55)
#define T_PARA (56)
#define T_FIN (57)
#define T_ERROR (58)
#define T_LET (59)
#define T_TIPO (60)
#define T_TENSOR (61)
#define T_NULO (62)
#define T_OK (63)
#define T_ERR (64)
#define T_ALGUN (65)
#define T_NINGUNO (66)
#define T_MODULO (67)
#define T_DELEGAR (68)
#define T_EXPORT (69)
#define T_RC (70)
#define T_ARC (71)
#define T_DEBIL (72)
#define T_PIPE (73)
#define IDIOMA_ES (0)
#define IDIOMA_EN (1)
#define IDIOMA_FR (2)
#define IDIOMA_PT (3)
#define MAX_TOKENS (16384)
#define MAX_INDENT (64)
int es_alnum(int c) {
    if ((es_digito(c) == 1)) {
        return 1;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((es_letra(c) == 1)) {
        return 1;
          /* [Lifetime Scope: exit depth=1] */
    }
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

int es_digito(int c) {
    if ((c >= 48)) {
        if ((c <= 57)) {
            return 1;
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

int es_letra(int c) {
    if ((c >= 128)) {
        return 1;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((c >= 65)) {
        if ((c <= 90)) {
            return 1;
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((c >= 97)) {
        if ((c <= 122)) {
            return 1;
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((c == 95)) {
        return 1;
          /* [Lifetime Scope: exit depth=1] */
    }
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

int keyword_token(CadenaSegura palabra, int idioma) {
    if ((idioma == IDIOMA_EN)) {
        return keyword_token_en(palabra);
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((idioma == IDIOMA_FR)) {
        return keyword_token_fr(palabra);
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((idioma == IDIOMA_PT)) {
        return keyword_token_pt(palabra);
          /* [Lifetime Scope: exit depth=1] */
    }
    return keyword_token_es(palabra);
      /* [Lifetime Scope: exit depth=0] */
}

int keyword_token_en(CadenaSegura palabra) {
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("if"), .datos = "if" }) == 1)) {
        return T_SI;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("else"), .datos = "else" }) == 1)) {
        return T_SINO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("function"), .datos = "function" }) == 1)) {
        return T_FUNCION;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("return"), .datos = "return" }) == 1)) {
        return T_RETORNAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("spawn"), .datos = "spawn" }) == 1)) {
        return T_LANZAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("recover"), .datos = "recover" }) == 1)) {
        return T_RECUPERAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("listen"), .datos = "listen" }) == 1)) {
        return T_ESCUCHAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("while"), .datos = "while" }) == 1)) {
        return T_MIENTRAS;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("break"), .datos = "break" }) == 1)) {
        return T_ROMPER;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("continue"), .datos = "continue" }) == 1)) {
        return T_SIGUIENTE;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("import"), .datos = "import" }) == 1)) {
        return T_IMPORTAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("struct"), .datos = "struct" }) == 1)) {
        return T_ESTRUCTURA;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("and"), .datos = "and" }) == 1)) {
        return T_Y;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("or"), .datos = "or" }) == 1)) {
        return T_O;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("not"), .datos = "not" }) == 1)) {
        return T_NO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("true"), .datos = "true" }) == 1)) {
        return T_VERDADERO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("false"), .datos = "false" }) == 1)) {
        return T_FALSO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("unsafe"), .datos = "unsafe" }) == 1)) {
        return T_INSEGURO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("import_c"), .datos = "import_c" }) == 1)) {
        return T_IMPORTAR_C;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("extern"), .datos = "extern" }) == 1)) {
        return T_EXTERNO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("match"), .datos = "match" }) == 1)) {
        return T_COINCIDIR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("requires"), .datos = "requires" }) == 1)) {
        return T_REQUIERE;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("ensures"), .datos = "ensures" }) == 1)) {
        return T_GARANTIZA;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("asm"), .datos = "asm" }) == 1)) {
        return T_ASM;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("constant"), .datos = "constant" }) == 1)) {
        return T_CONSTANTE;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("const"), .datos = "const" }) == 1)) {
        return T_CONSTANTE;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("for"), .datos = "for" }) == 1)) {
        return T_PARA;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("type"), .datos = "type" }) == 1)) {
        return T_TIPO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" }) == 1)) {
        return T_TENSOR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("null"), .datos = "null" }) == 1)) {
        return T_NULO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("ok"), .datos = "ok" }) == 1)) {
        return T_OK;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("err"), .datos = "err" }) == 1)) {
        return T_ERR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("some"), .datos = "some" }) == 1)) {
        return T_ALGUN;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("none"), .datos = "none" }) == 1)) {
        return T_NINGUNO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("let"), .datos = "let" }) == 1)) {
        return T_LET;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("delegate"), .datos = "delegate" }) == 1)) {
        return T_DELEGAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("rc"), .datos = "rc" }) == 1)) {
        return T_RC;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("arc"), .datos = "arc" }) == 1)) {
        return T_ARC;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("weak"), .datos = "weak" }) == 1)) {
        return T_DEBIL;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("module"), .datos = "module" }) == 1)) {
        return T_MODULO;
          /* [Lifetime Scope: exit depth=1] */
    }
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

int keyword_token_es(CadenaSegura palabra) {
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("si"), .datos = "si" }) == 1)) {
        return T_SI;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("sino"), .datos = "sino" }) == 1)) {
        return T_SINO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("funcion"), .datos = "funcion" }) == 1)) {
        return T_FUNCION;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("retornar"), .datos = "retornar" }) == 1)) {
        return T_RETORNAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("lanzar"), .datos = "lanzar" }) == 1)) {
        return T_LANZAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("recuperar"), .datos = "recuperar" }) == 1)) {
        return T_RECUPERAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("escuchar"), .datos = "escuchar" }) == 1)) {
        return T_ESCUCHAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("mientras"), .datos = "mientras" }) == 1)) {
        return T_MIENTRAS;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("importar"), .datos = "importar" }) == 1)) {
        return T_IMPORTAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("romper"), .datos = "romper" }) == 1)) {
        return T_ROMPER;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("siguiente"), .datos = "siguiente" }) == 1)) {
        return T_SIGUIENTE;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("estructura"), .datos = "estructura" }) == 1)) {
        return T_ESTRUCTURA;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("y"), .datos = "y" }) == 1)) {
        return T_Y;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("o"), .datos = "o" }) == 1)) {
        return T_O;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("no"), .datos = "no" }) == 1)) {
        return T_NO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("verdadero"), .datos = "verdadero" }) == 1)) {
        return T_VERDADERO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("falso"), .datos = "falso" }) == 1)) {
        return T_FALSO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("inseguro"), .datos = "inseguro" }) == 1)) {
        return T_INSEGURO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("importar_c"), .datos = "importar_c" }) == 1)) {
        return T_IMPORTAR_C;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("externo"), .datos = "externo" }) == 1)) {
        return T_EXTERNO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("coincidir"), .datos = "coincidir" }) == 1)) {
        return T_COINCIDIR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("requiere"), .datos = "requiere" }) == 1)) {
        return T_REQUIERE;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("garantiza"), .datos = "garantiza" }) == 1)) {
        return T_GARANTIZA;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("canal"), .datos = "canal" }) == 1)) {
        return T_CANAL;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("asm"), .datos = "asm" }) == 1)) {
        return T_ASM;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("constante"), .datos = "constante" }) == 1)) {
        return T_CONSTANTE;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("para"), .datos = "para" }) == 1)) {
        return T_PARA;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("tipo"), .datos = "tipo" }) == 1)) {
        return T_TIPO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" }) == 1)) {
        return T_TENSOR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" }) == 1)) {
        return T_NULO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("ok"), .datos = "ok" }) == 1)) {
        return T_OK;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("err"), .datos = "err" }) == 1)) {
        return T_ERR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("algun"), .datos = "algun" }) == 1)) {
        return T_ALGUN;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("ninguno"), .datos = "ninguno" }) == 1)) {
        return T_NINGUNO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("let"), .datos = "let" }) == 1)) {
        return T_LET;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("delegar"), .datos = "delegar" }) == 1)) {
        return T_DELEGAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("rc"), .datos = "rc" }) == 1)) {
        return T_RC;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("arc"), .datos = "arc" }) == 1)) {
        return T_ARC;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("débil"), .datos = "débil" }) == 1)) {
        return T_DEBIL;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("modulo"), .datos = "modulo" }) == 1)) {
        return T_MODULO;
          /* [Lifetime Scope: exit depth=1] */
    }
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

int keyword_token_fr(CadenaSegura palabra) {
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("si"), .datos = "si" }) == 1)) {
        return T_SI;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("sinon"), .datos = "sinon" }) == 1)) {
        return T_SINO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("fonction"), .datos = "fonction" }) == 1)) {
        return T_FUNCION;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("retourner"), .datos = "retourner" }) == 1)) {
        return T_RETORNAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("lancer"), .datos = "lancer" }) == 1)) {
        return T_LANZAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("recuperer"), .datos = "recuperer" }) == 1)) {
        return T_RECUPERAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("ecouter"), .datos = "ecouter" }) == 1)) {
        return T_ESCUCHAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("tantque"), .datos = "tantque" }) == 1)) {
        return T_MIENTRAS;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("rompre"), .datos = "rompre" }) == 1)) {
        return T_ROMPER;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("continuer"), .datos = "continuer" }) == 1)) {
        return T_SIGUIENTE;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("importer"), .datos = "importer" }) == 1)) {
        return T_IMPORTAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("structure"), .datos = "structure" }) == 1)) {
        return T_ESTRUCTURA;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("et"), .datos = "et" }) == 1)) {
        return T_Y;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("ou"), .datos = "ou" }) == 1)) {
        return T_O;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("non"), .datos = "non" }) == 1)) {
        return T_NO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("vrai"), .datos = "vrai" }) == 1)) {
        return T_VERDADERO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("faux"), .datos = "faux" }) == 1)) {
        return T_FALSO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("dangereux"), .datos = "dangereux" }) == 1)) {
        return T_INSEGURO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("importer_c"), .datos = "importer_c" }) == 1)) {
        return T_IMPORTAR_C;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("externe"), .datos = "externe" }) == 1)) {
        return T_EXTERNO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("correspondre"), .datos = "correspondre" }) == 1)) {
        return T_COINCIDIR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("exige"), .datos = "exige" }) == 1)) {
        return T_REQUIERE;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("garantit"), .datos = "garantit" }) == 1)) {
        return T_GARANTIZA;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("asm"), .datos = "asm" }) == 1)) {
        return T_ASM;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("constante"), .datos = "constante" }) == 1)) {
        return T_CONSTANTE;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("pour"), .datos = "pour" }) == 1)) {
        return T_PARA;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("type"), .datos = "type" }) == 1)) {
        return T_TIPO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("tenseur"), .datos = "tenseur" }) == 1)) {
        return T_TENSOR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("nul"), .datos = "nul" }) == 1)) {
        return T_NULO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("ok"), .datos = "ok" }) == 1)) {
        return T_OK;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("err"), .datos = "err" }) == 1)) {
        return T_ERR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("some"), .datos = "some" }) == 1)) {
        return T_ALGUN;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("aucun"), .datos = "aucun" }) == 1)) {
        return T_NINGUNO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("let"), .datos = "let" }) == 1)) {
        return T_LET;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("déléguer"), .datos = "déléguer" }) == 1)) {
        return T_DELEGAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("rc"), .datos = "rc" }) == 1)) {
        return T_RC;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("arc"), .datos = "arc" }) == 1)) {
        return T_ARC;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("faible"), .datos = "faible" }) == 1)) {
        return T_DEBIL;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("module"), .datos = "module" }) == 1)) {
        return T_MODULO;
          /* [Lifetime Scope: exit depth=1] */
    }
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

int keyword_token_pt(CadenaSegura palabra) {
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("se"), .datos = "se" }) == 1)) {
        return T_SI;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("senao"), .datos = "senao" }) == 1)) {
        return T_SINO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("funcao"), .datos = "funcao" }) == 1)) {
        return T_FUNCION;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("retornar"), .datos = "retornar" }) == 1)) {
        return T_RETORNAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("lancar"), .datos = "lancar" }) == 1)) {
        return T_LANZAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("recuperar"), .datos = "recuperar" }) == 1)) {
        return T_RECUPERAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("escutar"), .datos = "escutar" }) == 1)) {
        return T_ESCUCHAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("enquanto"), .datos = "enquanto" }) == 1)) {
        return T_MIENTRAS;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("parar"), .datos = "parar" }) == 1)) {
        return T_ROMPER;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("continuar"), .datos = "continuar" }) == 1)) {
        return T_SIGUIENTE;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("importar"), .datos = "importar" }) == 1)) {
        return T_IMPORTAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("estrutura"), .datos = "estrutura" }) == 1)) {
        return T_ESTRUCTURA;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("e"), .datos = "e" }) == 1)) {
        return T_Y;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("ou"), .datos = "ou" }) == 1)) {
        return T_O;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("nao"), .datos = "nao" }) == 1)) {
        return T_NO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("verdadeiro"), .datos = "verdadeiro" }) == 1)) {
        return T_VERDADERO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("falso"), .datos = "falso" }) == 1)) {
        return T_FALSO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("inseguro"), .datos = "inseguro" }) == 1)) {
        return T_INSEGURO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("importar_c"), .datos = "importar_c" }) == 1)) {
        return T_IMPORTAR_C;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("externo"), .datos = "externo" }) == 1)) {
        return T_EXTERNO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("coincidir"), .datos = "coincidir" }) == 1)) {
        return T_COINCIDIR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("requer"), .datos = "requer" }) == 1)) {
        return T_REQUIERE;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("garante"), .datos = "garante" }) == 1)) {
        return T_GARANTIZA;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("asm"), .datos = "asm" }) == 1)) {
        return T_ASM;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("constante"), .datos = "constante" }) == 1)) {
        return T_CONSTANTE;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("para"), .datos = "para" }) == 1)) {
        return T_PARA;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("tipo"), .datos = "tipo" }) == 1)) {
        return T_TIPO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" }) == 1)) {
        return T_TENSOR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" }) == 1)) {
        return T_NULO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("ok"), .datos = "ok" }) == 1)) {
        return T_OK;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("err"), .datos = "err" }) == 1)) {
        return T_ERR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("algum"), .datos = "algum" }) == 1)) {
        return T_ALGUN;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("nenhum"), .datos = "nenhum" }) == 1)) {
        return T_NINGUNO;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("let"), .datos = "let" }) == 1)) {
        return T_LET;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("delegar"), .datos = "delegar" }) == 1)) {
        return T_DELEGAR;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("rc"), .datos = "rc" }) == 1)) {
        return T_RC;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("arc"), .datos = "arc" }) == 1)) {
        return T_ARC;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("fraco"), .datos = "fraco" }) == 1)) {
        return T_DEBIL;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("modulo"), .datos = "modulo" }) == 1)) {
        return T_MODULO;
          /* [Lifetime Scope: exit depth=1] */
    }
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

void* lexer_buffers(void) {
    { /* unsafe */
        void* r = nulo;
        static struct LexerBuffers _N_bufs = {0,0,0,0,0,0,0,0,0,0};
        static struct TokenLex _N_tks[65536];
        static char _N_sbuf[65536];
        static int _N_indents[64];
        if (_N_bufs.tokens == 0) { _N_bufs.tokens = (void*)_N_tks; _N_bufs.sbuf = (void*)_N_sbuf; _N_bufs.indent_stack = (void*)_N_indents; }
        r = (void*)&_N_bufs;
        return r;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura lexer_decodificar_cadena(void* ptr, int ini, int len) {
    CadenaSegura r = {0};
    { /* unsafe */
        _syn_texto_liberar(r);
        r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        struct LexerBuffers* _b = (struct LexerBuffers*)lexer_buffers();
        const char* _p = (const char*)ptr + ini;
        char* _out = (char*)_b->sbuf + _b->str_pos; int _n = 0;
        for (int _k = 0; _k < len && _n < 65535 - _b->str_pos; _k++) {
            if (_p[_k] == 92 && _k + 1 < len) {
                switch (_p[_k + 1]) {
                    case 34: _out[_n++] = 34; _k++; break;
                    case 39: _out[_n++] = 39; _k++; break;
                    case 92: _out[_n++] = 92; _k++; break;
                    case 110: _out[_n++] = 10; _k++; break;
                    case 116: _out[_n++] = 9; _k++; break;
                    case 114: _out[_n++] = 13; _k++; break;
                    case 48: _out[_n++] = 0; _k++; break;
                    default: _out[_n++] = _p[_k]; break;
                }
            } else { _out[_n++] = _p[_k]; }
        }
        r = (CadenaSegura){_n, _out};
        _b->str_pos += _n;
        return r;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

int lexer_detectar_idioma(void* ptr, int len) {
    int r;
    int ini;
    int fin;
    CadenaSegura lang = {0};
    { /* unsafe */
        r = 0;
        r = (len >= 7 && ((const char*)ptr)[0] == '#' && ((const char*)ptr)[1] == 'l' && ((const char*)ptr)[2] == 'a' && ((const char*)ptr)[3] == 'n' && ((const char*)ptr)[4] == 'g' && ((const char*)ptr)[5] == ':') ? 1 : 0;
        if ((r == 0)) {
            return (-1);
              /* [Lifetime Scope: exit depth=2] */
        }
        ini = 6;
        fin = 6;
        while (ini < len && ((const char*)ptr)[ini] == ' ') { ini = ini + 1; }
        fin = ini;
        while (fin < len && ((const char*)ptr)[fin] != ' ' && ((const char*)ptr)[fin] != 10 && ((const char*)ptr)[fin] != 13) { fin = fin + 1; }
        _syn_texto_liberar(lang);
        lang = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        lang = (CadenaSegura){.longitud = (fin - ini), .datos = (char*)ptr + ini};
        if ((str_eq(lang, (CadenaSegura){ .longitud = (int)strlen("es"), .datos = "es" }) == 1)) {
            return IDIOMA_ES;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((str_eq(lang, (CadenaSegura){ .longitud = (int)strlen("en"), .datos = "en" }) == 1)) {
            return IDIOMA_EN;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((str_eq(lang, (CadenaSegura){ .longitud = (int)strlen("fr"), .datos = "fr" }) == 1)) {
            return IDIOMA_FR;
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((str_eq(lang, (CadenaSegura){ .longitud = (int)strlen("pt"), .datos = "pt" }) == 1)) {
            return IDIOMA_PT;
              /* [Lifetime Scope: exit depth=2] */
        }
        return (-2);
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

void lexer_error(CadenaSegura mensaje, int linea, int columna) {
    { /* unsafe */
        struct LexerBuffers* _b = (struct LexerBuffers*)lexer_buffers();
        _b->hay_error = 1;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

void lexer_fijar_linea(int n) {
    { /* unsafe */
        ((struct LexerBuffers*)lexer_buffers())->linea_actual = n;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

int lexer_hay_error(void) {
    int r;
    { /* unsafe */
        r = 0;
        r = ((struct LexerBuffers*)lexer_buffers())->hay_error;
        return r;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

int lexer_idioma_actual(void) {
    int r;
    { /* unsafe */
        r = 0;
        r = ((struct LexerBuffers*)lexer_buffers())->idioma;
        return r;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

int lexer_linea_actual(void) {
    int r;
    { /* unsafe */
        r = 0;
        r = ((struct LexerBuffers*)lexer_buffers())->linea_actual;
        return r;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

int lexer_obtener_total(void) {
    int r;
    { /* unsafe */
        r = 0;
        r = ((struct LexerBuffers*)lexer_buffers())->ntks;
        return r;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

void lexer_procesar_indentacion(void* ptr_linea, int len_linea) {
    int espacios;
    int r;
    int nivel;
    int tope;
    { /* unsafe */
        struct LexerBuffers* _b = (struct LexerBuffers*)lexer_buffers();
        espacios = 0;
        while (espacios < len_linea && ((const char*)ptr_linea)[espacios] == ' ') { espacios = espacios + 1; }
        if ((espacios < len_linea)) {
            r = 0;
            r = (((const char*)ptr_linea)[espacios] == '	') ? 1 : 0;
            if ((r == 1)) {
                lexer_error((CadenaSegura){ .longitud = (int)strlen("Tabulador prohibido E-101"), .datos = "Tabulador prohibido E-101" }, lexer_linea_actual(), (espacios + 1));
                return;
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        if (((espacios % 4) != 0)) {
            lexer_error((CadenaSegura){ .longitud = (int)strlen("Indentacion debe ser multiplo de 4 espacios"), .datos = "Indentacion debe ser multiplo de 4 espacios" }, lexer_linea_actual(), 0);
            return;
              /* [Lifetime Scope: exit depth=2] */
        }
        nivel = (espacios / 4);
        tope = 0;
        tope = (_b->nivel_pila > 0) ? ((int*)_b->indent_stack)[_b->nivel_pila - 1] : 0;
        if ((nivel > tope)) {
            ((int*)_b->indent_stack)[_b->nivel_pila] = nivel;
            _b->nivel_pila = _b->nivel_pila + 1;
            tope = nivel;
            lexer_push_token(T_INDENTAR, lexer_linea_actual(), 0);
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((nivel < tope)) {
            while ((nivel < tope)) {
                _b->nivel_pila = _b->nivel_pila - 1;
                tope = (_b->nivel_pila > 0) ? ((int*)_b->indent_stack)[_b->nivel_pila - 1] : 0;
                lexer_push_token(T_DESINDENTAR, lexer_linea_actual(), 0);
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

void lexer_push_token(int tipo, int linea, int columna) {
    lexer_push_token_valor(tipo, linea, columna, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
      /* [Lifetime Scope: exit depth=0] */
}

void lexer_push_token_valor(int tipo, int linea, int columna, CadenaSegura valor) {
    { /* unsafe */
        struct LexerBuffers* _b = (struct LexerBuffers*)lexer_buffers();
        if (_b->ntks >= 65536) return;
        struct TokenLex* _t = (struct TokenLex*)_b->tokens;
        _t[_b->ntks].tipo = tipo;
        _t[_b->ntks].linea = linea;
        _t[_b->ntks].columna = columna;
        _t[_b->ntks].valor = valor;
        _b->ntks = _b->ntks + 1;
        _b->total_tokens = _b->ntks;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

void lexer_reset_buffers(void) {
    { /* unsafe */
        struct LexerBuffers* _b = (struct LexerBuffers*)lexer_buffers();
        _b->ntks = 0; _b->str_pos = 0; _b->hay_error = 0; _b->total_tokens = 0; _b->nivel_pila = 0;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

void lexer_tokenizar_linea(void* ptr_texto, int len_texto) {
    int i;
    int r;
    int c;
    int c2;
    int q;
    int inicio_str;
    int cerrada;
    CadenaSegura contenido = {0};
    int inicio_num;
    int es_float;
    CadenaSegura lexema_num = {0};
    int inicio_ar;
    CadenaSegura arroba = {0};
    int inicio;
    CadenaSegura palabra = {0};
    int tok;
    i = 0;
    r = 1;
    while ((r == 1)) {
        { /* unsafe */
            struct LexerBuffers* _b = (struct LexerBuffers*)lexer_buffers();
            r = (i < len_texto) ? 1 : 0;
            if ((r == 0)) {
                break;
                  /* [Lifetime Scope: exit depth=3] */
            }
            c = 0;
            c = (unsigned char)((const char*)ptr_texto)[i];
            if ((c == 32)) {
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 47)) {
                if (((i + 1) < len_texto)) {
                    c2 = 0;
                    c2 = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c2 == 47)) {
                        return;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 35)) {
                return;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if (((c == 34) || (c == 39))) {
                q = c;
                inicio_str = i;
                cerrada = 0;
                i = i + 1;
                while ((i < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i];
                    if ((c == 92)) {
                        i = i + 1;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    else {
                        if ((c == q)) {
                            cerrada = 1;
                            break;
                              /* [Lifetime Scope: exit depth=6] */
                        }
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    i = i + 1;
                      /* [Lifetime Scope: exit depth=4] */
                }
                if ((cerrada == 1)) {
                    _syn_texto_liberar(contenido);
                    contenido = lexer_decodificar_cadena(ptr_texto, (inicio_str + 1), ((i - inicio_str) - 1));
                    lexer_push_token_valor(T_CADENA, lexer_linea_actual(), (inicio_str + 1), contenido);
                      /* [Lifetime Scope: exit depth=4] */
                }
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c >= 48)) {
                if ((c <= 57)) {
                    inicio_num = i;
                    while ((i < len_texto)) {
                        c = (unsigned char)((const char*)ptr_texto)[i];
                        if ((c < 48)) {
                            break;
                              /* [Lifetime Scope: exit depth=6] */
                        }
                        if ((c > 57)) {
                            break;
                              /* [Lifetime Scope: exit depth=6] */
                        }
                        i = i + 1;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    es_float = 0;
                    if ((i < len_texto)) {
                        c = (unsigned char)((const char*)ptr_texto)[i];
                        if ((c == 46)) {
                            es_float = 1;
                            i = i + 1;
                            while ((i < len_texto)) {
                                c = (unsigned char)((const char*)ptr_texto)[i];
                                if ((c < 48)) {
                                    break;
                                      /* [Lifetime Scope: exit depth=8] */
                                }
                                if ((c > 57)) {
                                    break;
                                      /* [Lifetime Scope: exit depth=8] */
                                }
                                i = i + 1;
                                  /* [Lifetime Scope: exit depth=7] */
                            }
                              /* [Lifetime Scope: exit depth=6] */
                        }
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    _syn_texto_liberar(lexema_num);
                    lexema_num = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
                    { /* unsafe */
                        lexema_num = (CadenaSegura){.longitud = (i - inicio_num), .datos = (char*)ptr_texto + inicio_num};
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    if ((es_float == 1)) {
                        lexer_push_token_valor(T_FLOTANTE, lexer_linea_actual(), (inicio_num + 1), lexema_num);
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    else {
                        lexer_push_token_valor(T_NUMERO, lexer_linea_actual(), (inicio_num + 1), lexema_num);
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    continue;
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 64)) {
                inicio_ar = i;
                i = i + 1;
                while ((i < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i];
                    if ((es_alnum(c) == 0)) {
                        if ((c != 95)) {
                            break;
                              /* [Lifetime Scope: exit depth=6] */
                        }
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    i = i + 1;
                      /* [Lifetime Scope: exit depth=4] */
                }
                _syn_texto_liberar(arroba);
                arroba = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
                { /* unsafe */
                    arroba = (CadenaSegura){.longitud = (i - inicio_ar), .datos = (char*)ptr_texto + inicio_ar};
                      /* [Lifetime Scope: exit depth=4] */
                }
                if ((str_eq(arroba, (CadenaSegura){ .longitud = (int)strlen("@export"), .datos = "@export" }) == 1)) {
                    lexer_push_token_valor(T_EXPORT, lexer_linea_actual(), (inicio_ar + 1), arroba);
                      /* [Lifetime Scope: exit depth=4] */
                }
                else {
                    lexer_error((CadenaSegura){ .longitud = (int)strlen("Caracter inesperado '@'"), .datos = "Caracter inesperado '@'" }, lexer_linea_actual(), (inicio_ar + 1));
                      /* [Lifetime Scope: exit depth=4] */
                }
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((es_letra(c) == 1)) {
                inicio = i;
                while ((i < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i];
                    if ((es_alnum(c) == 0)) {
                        if ((c != 95)) {
                            break;
                              /* [Lifetime Scope: exit depth=6] */
                        }
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    i = i + 1;
                      /* [Lifetime Scope: exit depth=4] */
                }
                _syn_texto_liberar(palabra);
                palabra = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
                { /* unsafe */
                    palabra = (CadenaSegura){.longitud = (i - inicio), .datos = (char*)ptr_texto + inicio};
                      /* [Lifetime Scope: exit depth=4] */
                }
                tok = keyword_token(palabra, lexer_idioma_actual());
                if ((tok == 0)) {
                    tok = T_IDENTIFICADOR;
                      /* [Lifetime Scope: exit depth=4] */
                }
                if ((tok == T_IDENTIFICADOR)) {
                    lexer_push_token_valor(tok, lexer_linea_actual(), (inicio + 1), palabra);
                      /* [Lifetime Scope: exit depth=4] */
                }
                else {
                    if ((((((((((((((tok == T_TIPO) || (tok == T_TENSOR)) || (tok == T_NULO)) || (tok == T_OK)) || (tok == T_ERR)) || (tok == T_ALGUN)) || (tok == T_NINGUNO)) || (tok == T_LET)) || (tok == T_DELEGAR)) || (tok == T_RC)) || (tok == T_ARC)) || (tok == T_DEBIL)) || (tok == T_MODULO))) {
                        lexer_push_token_valor(tok, lexer_linea_actual(), (inicio + 1), palabra);
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    else {
                        lexer_push_token(tok, lexer_linea_actual(), (inicio + 1));
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 43)) {
                lexer_push_token(T_MAS, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 45)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 62)) {
                        lexer_push_token(T_FLECHA, lexer_linea_actual(), (i + 1));
                        i = i + 2;
                        continue;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    if ((c == 60)) {
                        lexer_push_token(T_FLECHA_IZQ, lexer_linea_actual(), (i + 1));
                        i = i + 2;
                        continue;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                lexer_push_token(T_MENOS, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 61)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 62)) {
                        lexer_push_token(T_FLECHA_DER, lexer_linea_actual(), (i + 1));
                        i = i + 2;
                        continue;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    if ((c == 61)) {
                        lexer_push_token(T_IGUAL, lexer_linea_actual(), (i + 1));
                        i = i + 2;
                        continue;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                lexer_push_token(T_ASIGNAR, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 33)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 61)) {
                        lexer_push_token(T_DISTINTO, lexer_linea_actual(), (i + 1));
                        i = i + 2;
                        continue;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 60)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 61)) {
                        lexer_push_token(T_MENOR_IGUAL, lexer_linea_actual(), (i + 1));
                        i = i + 2;
                        continue;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                lexer_push_token(T_MENOR, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 62)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 61)) {
                        lexer_push_token(T_MAYOR_IGUAL, lexer_linea_actual(), (i + 1));
                        i = i + 2;
                        continue;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                lexer_push_token(T_MAYOR, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 42)) {
                lexer_push_token(T_POR, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 47)) {
                lexer_push_token(T_DIV, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 37)) {
                lexer_push_token(T_MOD, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 40)) {
                lexer_push_token(T_PAREN_IZQ, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 41)) {
                lexer_push_token(T_PAREN_DER, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 58)) {
                lexer_push_token(T_DOSPUNTOS, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 44)) {
                lexer_push_token(T_COMA, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 46)) {
                lexer_push_token(T_PUNTO, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 38)) {
                lexer_push_token(T_AMPERSAND, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 59)) {
                lexer_push_token(T_PUNTOCOMA, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 124)) {
                lexer_push_token(T_PIPE, lexer_linea_actual(), (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            lexer_error((CadenaSegura){ .longitud = (int)strlen("Caracter inesperado"), .datos = "Caracter inesperado" }, lexer_linea_actual(), (i + 1));
            i = i + 1;
              /* [Lifetime Scope: exit depth=2] */
        }
        continue;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

int str_char(CadenaSegura s, int i) {
    int r;
    { /* unsafe */
        r = 0;
        r = (i >= 0 && i < s.longitud) ? (unsigned char)s.datos[i] : 0;
        return r;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

int str_char_at(void* ptr, int i) {
    int r;
    { /* unsafe */
        r = 0;
        r = (unsigned char)((const char*)ptr)[i];
        return r;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

int str_len(CadenaSegura s) {
    int r;
    { /* unsafe */
        r = 0;
        r = s.longitud;
        return r;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

int str_len_ptr(void* ptr) {
    int r;
    { /* unsafe */
        r = 0;
        r = (int)strlen((const char*)ptr);
        return r;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

int tokenizar(CadenaSegura fuente) {
    int _i=0, _linea=1, _columna=1, _token_count=0;
    while (_i < fuente.longitud) {
        char _c = fuente.datos[_i];
        if (_c==' '||_c=='\t'){_i++;_columna++;continue;}
        if (_c=='\r'){_i++;continue;}
        if (_c=='\n'){_i++;_linea++;_columna=1;continue;}
        if (_c=='/'&&_i+1<fuente.longitud&&fuente.datos[_i+1]=='/'){
            while(_i<fuente.longitud&&fuente.datos[_i]!='\n')_i++;continue;
        }
        if(_c=='\"'||_c=='\''){char _q=_c;int _st=_i;_i++;_columna++;while(_i<fuente.longitud&&fuente.datos[_i]!=_q){_i++;_columna++;}if(_i>=fuente.longitud){break;}_i++;_columna++;_token_count++;}
        else if(_c>='0'&&_c<='9'){int _st=_i;while(_i<fuente.longitud&&fuente.datos[_i]>='0'&&fuente.datos[_i]<='9')_i++;_columna+=_i-_st;_token_count++;}
        else if((_c>='a'&&_c<='z')||(_c>='A'&&_c<='Z')||_c=='_'){int _st=_i;while(_i<fuente.longitud&&((fuente.datos[_i]>='a'&&fuente.datos[_i]<='z')||(fuente.datos[_i]>='A'&&fuente.datos[_i]<='Z')||(fuente.datos[_i]>='0'&&fuente.datos[_i]<='9')||fuente.datos[_i]=='_'))_i++;_columna+=_i-_st;_token_count++;}
        else{_i++;_columna++;_token_count++;}
    }
    return _token_count;
}
