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

// --- Token ID constants (Manual 2 §2.3) ---
#ifndef T_IF
#define T_IF (1)
#endif
#ifndef T_ELSE
#define T_ELSE (2)
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
#ifndef T_FIN
#define T_FIN (57)
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
extern void cerrar(Canal canal);
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
extern CadenaSegura decimal_a_texto(float n);
extern CadenaSegura entero_a_texto(int n);
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

struct LexerEstado;
struct TokenLex;

typedef struct LexerEstado {
    int ptr_fuente;
    int len_fuente;
    int posicion;
    int linea_actual;
    int columna_actual;
    struct TokenLex* tokens;
    int total_tokens;
    int pila_indent[64];
    int nivel_pila;
    int idioma;
    int hay_error;
    CadenaSegura error_mensaje;
    int error_linea;
    int error_columna;
} LexerEstado;

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
int lexer_detectar_idioma(struct LexerEstado lex);
void lexer_error(struct LexerEstado lex, CadenaSegura mensaje, int linea, int columna);
void lexer_procesar_indentacion(struct LexerEstado lex, int ptr_linea, int len_linea);
void lexer_push_token(struct LexerEstado lex, int tipo, int linea, int columna);
void lexer_push_token_valor(struct LexerEstado lex, int tipo, int linea, int columna, CadenaSegura valor);
void lexer_tokenizar_linea(struct LexerEstado lex, int ptr_texto, int len_texto);
int str_char(CadenaSegura s, int i);
int str_char_at(int ptr, int i);
int str_len(CadenaSegura s);
int str_len_ptr(int ptr);
int tokenizar(CadenaSegura fuente);

#define T_IF (1)
#define T_ELSE (2)
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
        return T_IF;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("else"), .datos = "else" }) == 1)) {
        return T_ELSE;
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
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

int keyword_token_es(CadenaSegura palabra) {
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("si"), .datos = "si" }) == 1)) {
        return T_IF;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("sino"), .datos = "sino" }) == 1)) {
        return T_ELSE;
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
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

int keyword_token_fr(CadenaSegura palabra) {
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("si"), .datos = "si" }) == 1)) {
        return T_IF;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("sinon"), .datos = "sinon" }) == 1)) {
        return T_ELSE;
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
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

int keyword_token_pt(CadenaSegura palabra) {
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("se"), .datos = "se" }) == 1)) {
        return T_IF;
          /* [Lifetime Scope: exit depth=1] */
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("senao"), .datos = "senao" }) == 1)) {
        return T_ELSE;
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
    return 0;
      /* [Lifetime Scope: exit depth=0] */
}

int lexer_detectar_idioma(struct LexerEstado lex) {
    int r;
    int ini;
    int fin;
    CadenaSegura lang = {0};
    { /* unsafe */
        r = 0;
        r = (lex.len_fuente >= 7 && ((const char*)lex.ptr_fuente)[0] == '#' && ((const char*)lex.ptr_fuente)[1] == 'l' && ((const char*)lex.ptr_fuente)[2] == 'a' && ((const char*)lex.ptr_fuente)[3] == 'n' && ((const char*)lex.ptr_fuente)[4] == 'g' && ((const char*)lex.ptr_fuente)[5] == ':') ? 1 : 0;
        if ((r == 0)) {
            return (-1);
              /* [Lifetime Scope: exit depth=2] */
        }
        ini = 6;
        fin = 6;
        while (ini < lex.len_fuente && ((const char*)lex.ptr_fuente)[ini] == ' ') { ini = ini + 1; }
        fin = ini;
        while (fin < lex.len_fuente && ((const char*)lex.ptr_fuente)[fin] != ' ' && ((const char*)lex.ptr_fuente)[fin] != 10 && ((const char*)lex.ptr_fuente)[fin] != 13) { fin = fin + 1; }
        _syn_texto_liberar(lang);
        lang = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        lang = (CadenaSegura){.longitud = (fin - ini), .datos = (char*)lex.ptr_fuente + ini};
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

void lexer_error(struct LexerEstado lex, CadenaSegura mensaje, int linea, int columna) {
    lex.hay_error = 1;
    lex.error_mensaje = mensaje;
    lex.error_linea = linea;
    lex.error_columna = columna;
      /* [Lifetime Scope: exit depth=0] */
}

void lexer_procesar_indentacion(struct LexerEstado lex, int ptr_linea, int len_linea) {
    int espacios;
    int r;
    int nivel;
    int tope;
    { /* unsafe */
        espacios = 0;
        while (espacios < len_linea && ((const char*)ptr_linea)[espacios] == ' ') { espacios = espacios + 1; }
        if ((espacios < len_linea)) {
            r = 0;
            r = (((const char*)ptr_linea)[espacios] == '	') ? 1 : 0;
            if ((r == 1)) {
                lexer_error(lex, (CadenaSegura){ .longitud = (int)strlen("Tabulador prohibido E-101"), .datos = "Tabulador prohibido E-101" }, lex.linea_actual, (espacios + 1));
                return;
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
        if (((espacios % 4) != 0)) {
            lexer_error(lex, (CadenaSegura){ .longitud = (int)strlen("Indentacion debe ser multiplo de 4 espacios"), .datos = "Indentacion debe ser multiplo de 4 espacios" }, lex.linea_actual, 0);
            return;
              /* [Lifetime Scope: exit depth=2] */
        }
        nivel = (espacios / 4);
        tope = 0;
        tope = (lex.nivel_pila > 0) ? lex.pila_indent[lex.nivel_pila - 1] : 0;
        if ((nivel > tope)) {
            lex.pila_indent[lex.nivel_pila] = nivel;
            lex.nivel_pila = lex.nivel_pila + 1;
            lexer_push_token(lex, T_INDENTAR, lex.linea_actual, 0);
              /* [Lifetime Scope: exit depth=2] */
        }
        if ((nivel < tope)) {
            while ((nivel < tope)) {
                lex.nivel_pila = lex.nivel_pila - 1;
                tope = (lex.nivel_pila > 0) ? lex.pila_indent[lex.nivel_pila - 1] : 0;
                lexer_push_token(lex, T_DESINDENTAR, lex.linea_actual, 0);
                  /* [Lifetime Scope: exit depth=3] */
            }
              /* [Lifetime Scope: exit depth=2] */
        }
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

void lexer_push_token(struct LexerEstado lex, int tipo, int linea, int columna) {
    lexer_push_token_valor(lex, tipo, linea, columna, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
      /* [Lifetime Scope: exit depth=0] */
}

void lexer_push_token_valor(struct LexerEstado lex, int tipo, int linea, int columna, CadenaSegura valor) {
    { /* unsafe */
        if (lex.total_tokens >= 16384) return;
        lex.tokens[lex.total_tokens].tipo = tipo;
        lex.tokens[lex.total_tokens].linea = linea;
        lex.tokens[lex.total_tokens].columna = columna;
        lex.tokens[lex.total_tokens].valor = valor;
        lex.total_tokens = lex.total_tokens + 1;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

void lexer_tokenizar_linea(struct LexerEstado lex, int ptr_texto, int len_texto) {
    int i;
    int r;
    int c;
    int inicio;
    CadenaSegura palabra = {0};
    int tok;
    i = 0;
    r = 1;
    while ((r == 1)) {
        { /* unsafe */
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
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 47)) {
                        return;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 34)) {
                i = i + 1;
                while ((i < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i];
                    if ((c == 92)) {
                        i = i + 1;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    else {
                        if ((c == 34)) {
                            break;
                              /* [Lifetime Scope: exit depth=6] */
                        }
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    i = i + 1;
                      /* [Lifetime Scope: exit depth=4] */
                }
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 39)) {
                i = i + 1;
                while ((i < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i];
                    if ((c == 92)) {
                        i = i + 1;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    else {
                        if ((c == 39)) {
                            break;
                              /* [Lifetime Scope: exit depth=6] */
                        }
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    i = i + 1;
                      /* [Lifetime Scope: exit depth=4] */
                }
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c >= 48)) {
                if ((c <= 57)) {
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
                    continue;
                      /* [Lifetime Scope: exit depth=4] */
                }
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
                tok = keyword_token(palabra, lex.idioma);
                if ((tok == 0)) {
                    tok = T_IDENTIFICADOR;
                      /* [Lifetime Scope: exit depth=4] */
                }
                if ((tok == T_IDENTIFICADOR)) {
                    lexer_push_token_valor(lex, tok, lex.linea_actual, (inicio + 1), palabra);
                      /* [Lifetime Scope: exit depth=4] */
                }
                else {
                    lexer_push_token(lex, tok, lex.linea_actual, (inicio + 1));
                      /* [Lifetime Scope: exit depth=4] */
                }
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 43)) {
                lexer_push_token(lex, T_MAS, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 45)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 62)) {
                        lexer_push_token(lex, T_FLECHA, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    if ((c == 60)) {
                        lexer_push_token(lex, T_FLECHA_IZQ, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                lexer_push_token(lex, T_MENOS, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 61)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 62)) {
                        lexer_push_token(lex, T_FLECHA_DER, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                    if ((c == 61)) {
                        lexer_push_token(lex, T_IGUAL, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                lexer_push_token(lex, T_ASIGNAR, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 33)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 61)) {
                        lexer_push_token(lex, T_DISTINTO, lex.linea_actual, (i + 1));
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
                        lexer_push_token(lex, T_MENOR_IGUAL, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                lexer_push_token(lex, T_MENOR, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 62)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 61)) {
                        lexer_push_token(lex, T_MAYOR_IGUAL, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                          /* [Lifetime Scope: exit depth=5] */
                    }
                      /* [Lifetime Scope: exit depth=4] */
                }
                lexer_push_token(lex, T_MAYOR, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 42)) {
                lexer_push_token(lex, T_POR, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 47)) {
                lexer_push_token(lex, T_DIV, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 37)) {
                lexer_push_token(lex, T_MOD, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 40)) {
                lexer_push_token(lex, T_PAREN_IZQ, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 41)) {
                lexer_push_token(lex, T_PAREN_DER, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 58)) {
                lexer_push_token(lex, T_DOSPUNTOS, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 44)) {
                lexer_push_token(lex, T_COMA, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 46)) {
                lexer_push_token(lex, T_PUNTO, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 38)) {
                lexer_push_token(lex, T_AMPERSAND, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            if ((c == 59)) {
                lexer_push_token(lex, T_PUNTOCOMA, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
                  /* [Lifetime Scope: exit depth=3] */
            }
            lexer_error(lex, (CadenaSegura){ .longitud = (int)strlen("Caracter inesperado"), .datos = "Caracter inesperado" }, lex.linea_actual, (i + 1));
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

int str_char_at(int ptr, int i) {
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

int str_len_ptr(int ptr) {
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
