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

struct Opcion;
struct Resultado;

typedef struct Opcion {
    int tag;
    union {
        int valor;
        CadenaSegura valor_str;
        float valor_float;
    } dato;
} Opcion;

typedef struct Resultado {
    int tag;
    union {
        int valor;
        CadenaSegura valor_str;
        float valor_float;
    } dato;
} Resultado;

CadenaSegura _validar_ruta_segura(CadenaSegura ruta);
int ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica);
int ejecutar_comando(CadenaSegura cmd);
int eliminar_archivo(CadenaSegura ruta);
int escribir_archivo(CadenaSegura ruta, CadenaSegura contenido);
int existe_archivo(CadenaSegura ruta);
CadenaSegura leer_archivo(CadenaSegura ruta);
CadenaSegura obtener_env(CadenaSegura nombre);
int principal(void);
int prueba_clave_incorrecta(void);
int prueba_enviar_datos_canal(void);
int prueba_enviar_hello(void);
int prueba_firma_corrupta(void);
int prueba_firmar_verificar(void);
int prueba_generar_par(void);
int prueba_handshake_bidireccional(void);
int prueba_iniciar_detener_nodo(void);
int prueba_resultado_algebraico(void);
CadenaSegura sha256_texto(CadenaSegura datos);

extern CadenaSegura _syn_sha256_texto(CadenaSegura datos);
extern int _syn_ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica);
extern CadenaSegura _syn_normalizar_ruta(CadenaSegura ruta);
extern CadenaSegura _syn_obtener_cwd(void);
extern int _syn_ruta_en_directorio(CadenaSegura ruta, CadenaSegura dir);
extern int _syn_ejecutar_comando(CadenaSegura cmd);
extern int _syn_escribir_archivo(CadenaSegura ruta, CadenaSegura contenido);
extern CadenaSegura _syn_leer_archivo(CadenaSegura ruta);
extern CadenaSegura _syn_obtener_env(CadenaSegura nombre);
extern int _syn_existe_archivo(CadenaSegura ruta);
extern int _syn_eliminar_archivo(CadenaSegura ruta);
extern Canal _syn_abrir(CadenaSegura ruta, CadenaSegura modo);
extern CadenaSegura _syn_leer(Canal c);
extern void _syn_escribir(CadenaSegura texto);
extern void _syn_escribir_linea(CadenaSegura texto);
extern CadenaSegura _syn_leer_linea(void);
extern CadenaSegura cluster_generar_par_claves(void);
extern CadenaSegura cluster_firmar_mensaje(CadenaSegura mensaje, CadenaSegura clave_privada_hex);
extern int cluster_verificar_firma(CadenaSegura mensaje, CadenaSegura firma_hex, CadenaSegura clave_publica_hex);
extern int cluster_iniciar_nodo(int puerto);
extern int cluster_detener_nodo(void);
extern int cluster_enviar_hello(CadenaSegura ip, int puerto, CadenaSegura id_origen, CadenaSegura pubkey_hex);
extern int cluster_canal_remoto_enviar(CadenaSegura ip, int puerto, CadenaSegura datos, int lon, int chan_id);
CadenaSegura _validar_ruta_segura(CadenaSegura ruta) {
    CadenaSegura normalizada = {0};
    CadenaSegura cwd = {0};
    _syn_texto_liberar(normalizada);
    normalizada = _syn_normalizar_ruta(ruta);
    _syn_texto_liberar(cwd);
    cwd = _syn_obtener_cwd();
    if ((!_syn_ruta_en_directorio(normalizada, cwd))) {
        return (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
          /* [Lifetime Scope: exit depth=1] */
    }
    return normalizada;
      /* [Lifetime Scope: exit depth=0] */
}

int ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica) {
    return _syn_ed25519_verificar(mensaje, firma, clave_publica);
      /* [Lifetime Scope: exit depth=0] */
}

int ejecutar_comando(CadenaSegura cmd) {
    return _syn_ejecutar_comando(cmd);
      /* [Lifetime Scope: exit depth=0] */
}

int eliminar_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = {0};
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        return (-1);
          /* [Lifetime Scope: exit depth=1] */
    }
    return _syn_eliminar_archivo(ruta_segura);
      /* [Lifetime Scope: exit depth=0] */
}

int escribir_archivo(CadenaSegura ruta, CadenaSegura contenido) {
    CadenaSegura ruta_segura = {0};
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        return (-1);
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
        return 0;
          /* [Lifetime Scope: exit depth=1] */
    }
    return (_syn_existe_archivo(ruta_segura) == 1);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura leer_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = {0};
    _syn_texto_liberar(ruta_segura);
    ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        return (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
          /* [Lifetime Scope: exit depth=1] */
    }
    return _syn_leer_archivo(ruta_segura);
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura obtener_env(CadenaSegura nombre) {
    return _syn_obtener_env(nombre);
      /* [Lifetime Scope: exit depth=0] */
}

int principal(void) {
    int total_fallos;
    _simd_detectar();
    total_fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("========================================"), .datos = "========================================" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("  M18.3: Handshake Ed25519 Zero-Trust"), .datos = "  M18.3: Handshake Ed25519 Zero-Trust" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("========================================"), .datos = "========================================" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    total_fallos = (total_fallos + prueba_generar_par());
    total_fallos = (total_fallos + prueba_firmar_verificar());
    total_fallos = (total_fallos + prueba_firma_corrupta());
    total_fallos = (total_fallos + prueba_clave_incorrecta());
    total_fallos = (total_fallos + prueba_handshake_bidireccional());
    total_fallos = (total_fallos + prueba_iniciar_detener_nodo());
    total_fallos = (total_fallos + prueba_enviar_hello());
    total_fallos = (total_fallos + prueba_enviar_datos_canal());
    total_fallos = (total_fallos + prueba_resultado_algebraico());
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("========================================"), .datos = "========================================" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("  RESULTADOS"), .datos = "  RESULTADOS" });
    escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("  Total fallos: "), .datos = "  Total fallos: " }, entero_a_texto(total_fallos)));
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("========================================"), .datos = "========================================" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    if ((total_fallos > 0)) {
        return 1;
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        return 0;
          /* [Lifetime Scope: exit depth=1] */
    }
      /* [Lifetime Scope: exit depth=0] */
}

int prueba_clave_incorrecta(void) {
    int fallos;
    CadenaSegura par_a = {0};
    CadenaSegura par_b = {0};
    CadenaSegura firma = {0};
    int resultado;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 4: Rechazo de clave publica incorrecta ==="), .datos = "=== Prueba 4: Rechazo de clave publica incorrecta ===" });
    _syn_texto_liberar(par_a);
    par_a = cluster_generar_par_claves();
    _syn_texto_liberar(par_b);
    par_b = cluster_generar_par_claves();
    _syn_texto_liberar(firma);
    firma = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test"), .datos = "synapse-handshake:test" }, par_a);
    resultado = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test"), .datos = "synapse-handshake:test" }, firma, par_b);
    if ((resultado != 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] verificar_firma() rechaza clave publica incorrecta"), .datos = "[OK] verificar_firma() rechaza clave publica incorrecta" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] verificar_firma() debio rechazar clave incorrecta"), .datos = "[FALLO] verificar_firma() debio rechazar clave incorrecta" });
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int prueba_enviar_datos_canal(void) {
    int fallos;
    int rc;
    int rc2;
    int rc3;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 8: Envio de datos por canal remoto ==="), .datos = "=== Prueba 8: Envio de datos por canal remoto ===" });
    rc = cluster_iniciar_nodo(0);
    if ((rc >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] nodo iniciado para canal"), .datos = "[OK] nodo iniciado para canal" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] no pudo iniciar nodo rc="), .datos = "[FALLO] no pudo iniciar nodo rc=" }, entero_a_texto(rc)));
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    rc2 = cluster_canal_remoto_enviar((CadenaSegura){ .longitud = (int)strlen("127.0.0.1"), .datos = "127.0.0.1" }, 19098, (CadenaSegura){ .longitud = (int)strlen("datos transmitidos"), .datos = "datos transmitidos" }, 18, 1);
    if ((rc2 >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] canal_remoto_enviar retorna >= 0"), .datos = "[OK] canal_remoto_enviar retorna >= 0" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] canal_remoto_enviar() fallo rc="), .datos = "[FALLO] canal_remoto_enviar() fallo rc=" }, entero_a_texto(rc2)));
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    rc3 = cluster_detener_nodo();
    if ((rc3 >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] nodo detenido tras canal"), .datos = "[OK] nodo detenido tras canal" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] detener nodo fallo rc="), .datos = "[FALLO] detener nodo fallo rc=" }, entero_a_texto(rc3)));
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int prueba_enviar_hello(void) {
    int fallos;
    CadenaSegura par = {0};
    int rc;
    int rc2;
    int rc3;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 7: Envio HELLO ==="), .datos = "=== Prueba 7: Envio HELLO ===" });
    _syn_texto_liberar(par);
    par = cluster_generar_par_claves();
    rc = cluster_iniciar_nodo(0);
    if ((rc >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] nodo iniciado"), .datos = "[OK] nodo iniciado" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] no pudo iniciar nodo rc="), .datos = "[FALLO] no pudo iniciar nodo rc=" }, entero_a_texto(rc)));
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    rc2 = cluster_enviar_hello((CadenaSegura){ .longitud = (int)strlen("127.0.0.1"), .datos = "127.0.0.1" }, 19099, (CadenaSegura){ .longitud = (int)strlen("nodo-test"), .datos = "nodo-test" }, par);
    if ((rc2 >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] enviar_hello a 127.0.0.1:19099 retorna >= 0"), .datos = "[OK] enviar_hello a 127.0.0.1:19099 retorna >= 0" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] enviar_hello() fallo rc="), .datos = "[FALLO] enviar_hello() fallo rc=" }, entero_a_texto(rc2)));
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    rc3 = cluster_detener_nodo();
    if ((rc3 >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] nodo detenido"), .datos = "[OK] nodo detenido" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] detener nodo fallo rc="), .datos = "[FALLO] detener nodo fallo rc=" }, entero_a_texto(rc3)));
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int prueba_firma_corrupta(void) {
    int fallos;
    CadenaSegura par = {0};
    CadenaSegura firma = {0};
    int resultado;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 3: Rechazo de firma corrupta (Zero-Trust) ==="), .datos = "=== Prueba 3: Rechazo de firma corrupta (Zero-Trust) ===" });
    _syn_texto_liberar(par);
    par = cluster_generar_par_claves();
    _syn_texto_liberar(firma);
    firma = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test"), .datos = "synapse-handshake:test" }, par);
    resultado = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test-DIFFERENT"), .datos = "synapse-handshake:test-DIFFERENT" }, firma, par);
    if ((resultado != 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] verificar_firma() rechaza mensaje incorrecto"), .datos = "[OK] verificar_firma() rechaza mensaje incorrecto" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] verificar_firma() debio rechazar mensaje incorrecto"), .datos = "[FALLO] verificar_firma() debio rechazar mensaje incorrecto" });
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int prueba_firmar_verificar(void) {
    int fallos;
    CadenaSegura par = {0};
    CadenaSegura firma = {0};
    int resultado;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 2: Firma y verificacion Ed25519 ==="), .datos = "=== Prueba 2: Firma y verificacion Ed25519 ===" });
    _syn_texto_liberar(par);
    par = cluster_generar_par_claves();
    _syn_texto_liberar(firma);
    firma = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test-message"), .datos = "synapse-handshake:test-message" }, par);
    if ((str_eq(firma, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] firmar_mensaje() retorna firma vacia"), .datos = "[FALLO] firmar_mensaje() retorna firma vacia" });
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] firmar_mensaje() retorna firma no vacia"), .datos = "[OK] firmar_mensaje() retorna firma no vacia" });
          /* [Lifetime Scope: exit depth=1] */
    }
    resultado = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:test-message"), .datos = "synapse-handshake:test-message" }, firma, par);
    if ((resultado == 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] verificar_firma() retorna 0 para firma valida"), .datos = "[OK] verificar_firma() retorna 0 para firma valida" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] verificar_firma() debio retornar 0, obtuvo "), .datos = "[FALLO] verificar_firma() debio retornar 0, obtuvo " }, entero_a_texto(resultado)));
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int prueba_generar_par(void) {
    int fallos;
    CadenaSegura par = {0};
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 1: Generar par Ed25519 ==="), .datos = "=== Prueba 1: Generar par Ed25519 ===" });
    _syn_texto_liberar(par);
    par = cluster_generar_par_claves();
    if ((str_eq(par, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] generar_par() retorna vacio"), .datos = "[FALLO] generar_par() retorna vacio" });
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] generar_par() no retorna vacio"), .datos = "[OK] generar_par() no retorna vacio" });
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int prueba_handshake_bidireccional(void) {
    int fallos;
    CadenaSegura par_a = {0};
    CadenaSegura par_b = {0};
    CadenaSegura firma_a = {0};
    int v1;
    CadenaSegura firma_b = {0};
    int v2;
    int v3;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 5: Handshake bidireccional A <-> B ==="), .datos = "=== Prueba 5: Handshake bidireccional A <-> B ===" });
    _syn_texto_liberar(par_a);
    par_a = cluster_generar_par_claves();
    _syn_texto_liberar(par_b);
    par_b = cluster_generar_par_claves();
    _syn_texto_liberar(firma_a);
    firma_a = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:pubkey-B"), .datos = "synapse-handshake:pubkey-B" }, par_a);
    if ((str_eq(firma_a, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] A no genera firma de handshake"), .datos = "[FALLO] A no genera firma de handshake" });
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] A genera firma de handshake"), .datos = "[OK] A genera firma de handshake" });
          /* [Lifetime Scope: exit depth=1] */
    }
    v1 = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:pubkey-B"), .datos = "synapse-handshake:pubkey-B" }, firma_a, par_a);
    if ((v1 == 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] B verifica firma de A correctamente"), .datos = "[OK] B verifica firma de A correctamente" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] B debio verificar firma de A, obtuvo "), .datos = "[FALLO] B debio verificar firma de A, obtuvo " }, entero_a_texto(v1)));
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    _syn_texto_liberar(firma_b);
    firma_b = cluster_firmar_mensaje((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:pubkey-A"), .datos = "synapse-handshake:pubkey-A" }, par_b);
    if ((str_eq(firma_b, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] B no genera firma de respuesta"), .datos = "[FALLO] B no genera firma de respuesta" });
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] B genera firma de respuesta"), .datos = "[OK] B genera firma de respuesta" });
          /* [Lifetime Scope: exit depth=1] */
    }
    v2 = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("synapse-handshake:pubkey-A"), .datos = "synapse-handshake:pubkey-A" }, firma_b, par_b);
    if ((v2 == 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] A verifica firma de B correctamente"), .datos = "[OK] A verifica firma de B correctamente" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] A debio verificar firma de B, obtuvo "), .datos = "[FALLO] A debio verificar firma de B, obtuvo " }, entero_a_texto(v2)));
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    v3 = cluster_verificar_firma((CadenaSegura){ .longitud = (int)strlen("mensaje-alterado"), .datos = "mensaje-alterado" }, firma_b, par_b);
    if ((v3 != 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] A rechaza firma de B con mensaje alterado"), .datos = "[OK] A rechaza firma de B con mensaje alterado" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] A debio rechazar mensaje alterado"), .datos = "[FALLO] A debio rechazar mensaje alterado" });
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int prueba_iniciar_detener_nodo(void) {
    int fallos;
    int rc;
    int rc2;
    int rc3;
    int rc4;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 6: Iniciar/Detener nodo UDP ==="), .datos = "=== Prueba 6: Iniciar/Detener nodo UDP ===" });
    rc = cluster_iniciar_nodo(0);
    if ((rc >= 0)) {
        escribir_linea(concat(concat((CadenaSegura){ .longitud = (int)strlen("[OK] iniciar_nodo(0) retorna >= 0 (rc="), .datos = "[OK] iniciar_nodo(0) retorna >= 0 (rc=" }, entero_a_texto(rc)), (CadenaSegura){ .longitud = (int)strlen(")"), .datos = ")" }));
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] iniciar_nodo(0) fallo rc="), .datos = "[FALLO] iniciar_nodo(0) fallo rc=" }, entero_a_texto(rc)));
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    rc2 = cluster_detener_nodo();
    if ((rc2 >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] detener_nodo() retorna >= 0"), .datos = "[OK] detener_nodo() retorna >= 0" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] detener_nodo() fallo rc="), .datos = "[FALLO] detener_nodo() fallo rc=" }, entero_a_texto(rc2)));
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    rc3 = cluster_iniciar_nodo(9701);
    if ((rc3 >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] reiniciar_nodo(9701) retorna >= 0"), .datos = "[OK] reiniciar_nodo(9701) retorna >= 0" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] reiniciar_nodo(9701) fallo rc="), .datos = "[FALLO] reiniciar_nodo(9701) fallo rc=" }, entero_a_texto(rc3)));
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    rc4 = cluster_detener_nodo();
    if ((rc4 >= 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] redetener_nodo() retorna >= 0"), .datos = "[OK] redetener_nodo() retorna >= 0" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("[FALLO] redetener_nodo() fallo rc="), .datos = "[FALLO] redetener_nodo() fallo rc=" }, entero_a_texto(rc4)));
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

int prueba_resultado_algebraico(void) {
    int fallos;
    struct Resultado r_ok;
    struct Resultado r_err;
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("=== Prueba 9: Tipo algebraico Resultado ==="), .datos = "=== Prueba 9: Tipo algebraico Resultado ===" });
    r_ok = (struct Resultado){0};
    r_ok.tag = 0;
    r_ok.valor_str = (CadenaSegura){ .longitud = (int)strlen("operacion exitosa"), .datos = "operacion exitosa" };
    if ((r_ok.tag == 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] Resultado.ok tiene tag=0"), .datos = "[OK] Resultado.ok tiene tag=0" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] Resultado.ok tag debio ser 0"), .datos = "[FALLO] Resultado.ok tag debio ser 0" });
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    r_err = (struct Resultado){0};
    r_err.tag = 1;
    r_err.valor_str = (CadenaSegura){ .longitud = (int)strlen("error de autenticacion"), .datos = "error de autenticacion" };
    if ((r_err.tag == 1)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] Resultado.err tiene tag=1"), .datos = "[OK] Resultado.err tiene tag=1" });
          /* [Lifetime Scope: exit depth=1] */
    }
    else {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("[FALLO] Resultado.err tag debio ser 1"), .datos = "[FALLO] Resultado.err tag debio ser 1" });
        fallos = (fallos + 1);
          /* [Lifetime Scope: exit depth=1] */
    }
    return fallos;
      /* [Lifetime Scope: exit depth=0] */
}

CadenaSegura sha256_texto(CadenaSegura datos) {
    return _syn_sha256_texto(datos);
      /* [Lifetime Scope: exit depth=0] */
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    return principal();
    synapse_esperar_hilos();
    pool_destroy();
    return 0;
}