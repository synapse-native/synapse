// salida_metal.c - Generado por Synapse Compilador
// Lenguaje: Synapse v1.0 (#lang: es)
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

// --- OO AST node types (correct, from hola.c) ---
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
struct BloqueInseguro;
struct ExprObtenerDireccion;
struct ExprDereferencia;

typedef struct Token { int tipo; CadenaSegura lexema; int linea; int columna; } Token;
typedef struct Nodo { CadenaSegura tipo; } Nodo;
typedef struct ListaNodo { struct Nodo* cabeza; struct ListaNodo* cola; } ListaNodo;
typedef struct Programa { CadenaSegura tipo; struct ListaNodo* sentencias; } Programa;
typedef struct Identificador { CadenaSegura tipo; CadenaSegura nombre; } Identificador;
typedef struct LiteralNumero { CadenaSegura tipo; int valor; } LiteralNumero;
typedef struct LiteralCadena { CadenaSegura tipo; CadenaSegura valor; } LiteralCadena;
typedef struct OpBinaria { CadenaSegura tipo; struct Nodo* izquierdo; struct Token* operador; struct Nodo* derecho; } OpBinaria;
typedef struct OpUnaria { CadenaSegura tipo; struct Token* operador; struct Nodo* expr; } OpUnaria;
typedef struct LlamadaFuncion { CadenaSegura tipo; CadenaSegura nombre; struct ListaNodo* argumentos; } LlamadaFuncion;
typedef struct ExprAccesoCampo { CadenaSegura tipo; struct Nodo* objeto; CadenaSegura nombre_campo; } ExprAccesoCampo;
typedef struct AsignacionVariable { CadenaSegura tipo; CadenaSegura nombre; struct Nodo* expresion; } AsignacionVariable;
typedef struct AsignacionCampo { CadenaSegura tipo; struct Nodo* objeto; CadenaSegura nombre_campo; struct Nodo* expresion; } AsignacionCampo;
typedef struct SentenciaSi { CadenaSegura tipo; struct Nodo* condicion; struct ListaNodo* cuerpo; struct ListaNodo* cuerpo_sino; } SentenciaSi;
typedef struct SentenciaMientras { CadenaSegura tipo; struct Nodo* condicion; struct ListaNodo* cuerpo; } SentenciaMientras;
typedef struct SentenciaRetornar { CadenaSegura tipo; struct Nodo* expr; } SentenciaRetornar;
typedef struct SentenciaExpr { CadenaSegura tipo; struct Nodo* expr; } SentenciaExpr;
typedef struct LogLlamada { CadenaSegura tipo; struct ListaNodo* argumentos; } LogLlamada;
typedef struct Parametro { CadenaSegura tipo; CadenaSegura nombre; CadenaSegura tipo_param; int es_transferencia; } Parametro;
typedef struct ListaParametro { struct Parametro* cabeza; struct ListaParametro* cola; } ListaParametro;
typedef struct DefinicionFuncion { CadenaSegura tipo; CadenaSegura nombre; struct ListaParametro* parametros; CadenaSegura tipo_retorno; struct ListaNodo* cuerpo; } DefinicionFuncion;
typedef struct DefinicionEstructura { CadenaSegura tipo; CadenaSegura nombre; struct ListaParametro* campos; } DefinicionEstructura;
typedef struct SentenciaRomper { CadenaSegura tipo; } SentenciaRomper;
typedef struct SentenciaSiguiente { CadenaSegura tipo; } SentenciaSiguiente;
typedef struct SentenciaLanzar { CadenaSegura tipo; struct Nodo* llamada; } SentenciaLanzar;
typedef struct SentenciaRecuperar { CadenaSegura tipo; struct Nodo* accion_critica; struct Nodo* plan_b; } SentenciaRecuperar;
typedef struct SentenciaEscuchar { CadenaSegura tipo; struct Nodo* canal; struct Nodo* respuesta; } SentenciaEscuchar;
typedef struct ExprTensor { CadenaSegura tipo; struct Nodo* filas; struct Nodo* columnas; } ExprTensor;
typedef struct ExprIndice { CadenaSegura tipo; struct Nodo* expr; struct Nodo* indice; } ExprIndice;
typedef struct ArgumentoTransferido { CadenaSegura tipo; struct Nodo* expr; } ArgumentoTransferido;
typedef struct SentenciaImportar { CadenaSegura tipo; CadenaSegura ruta; } SentenciaImportar;
typedef struct ImportarC { CadenaSegura tipo; CadenaSegura ruta; int es_sistema; } ImportarC;
typedef struct DeclaracionExterna { CadenaSegura tipo; CadenaSegura nombre; struct Parametro* parametros; CadenaSegura tipo_retorno; } DeclaracionExterna;
typedef struct BloqueInseguro { CadenaSegura tipo; struct Nodo* cuerpo; } BloqueInseguro;
typedef struct ExprObtenerDireccion { CadenaSegura tipo; struct Nodo* expr; } ExprObtenerDireccion;
typedef struct ExprDereferencia { CadenaSegura tipo; struct Nodo* expr; } ExprDereferencia;

// Constantes del pool de memoria (definidas en synapse_rt.c)
#define POOL_BLOQUES 64
#define TAMANO_BLOQUE 4096

// Constantes de tags para uniones etiquetadas (ADTs)
#define TAG_OK 0
#define TAG_ERR 1
#define TAG_ALGUNO 0
#define TAG_NINGUNO 1

// --- Helpers de serialización primitiva para canales (Zero-Copy) ---
static inline void* _synapse_box_int(int v) { return (void*)(intptr_t)v; }
static inline int _synapse_unbox_int(void* p) { return (int)(intptr_t)p; }
static inline void* _synapse_box_float(float v) {
    float* _p = (float*)malloc(sizeof(float));
    if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en _synapse_box_float\n"); exit(1); }
    *_p = v;
    return (void*)_p;
}
static inline float _synapse_unbox_float(void* p) {
    float _v = *(float*)p;
    free(p);
    return _v;
}

// --- Declaraciones extern del runtime precompilado (synapse_rt.o) ---
extern void pool_init(uint32_t total_blocks, uint32_t block_size);
extern void pool_free(void* ptr);
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
extern void synapse_lanzar_hilo(void* (*fn)(void*), void* arg);
extern void synapse_esperar_hilos(void);
extern void _syn_texto_liberar(CadenaSegura s);

// --- Declaraciones extern de canales (CanalConcurrencia) ---
typedef struct { int es_ok; union { void* ok_valor; const char* err_mensaje; } datos; } Resultado_T;
typedef struct CanalConcurrencia CanalConcurrencia;
extern CanalConcurrencia* canal_crear(uint32_t capacidad);
extern void canal_enviar(CanalConcurrencia* canal, void* paquete);
extern void* canal_recibir(CanalConcurrencia* canal);
extern void canal_destruir(CanalConcurrencia* canal);
extern void cerrar_canal(CanalConcurrencia* canal);
static int _g_argc;
static char** _g_argv;
int _argc() { return _g_argc; }

CadenaSegura _argv(int i) {
    if (i < 0 || i >= _g_argc) return (CadenaSegura){0, ""};
    return (CadenaSegura){ .longitud = (int)strlen(_g_argv[i]), .datos = _g_argv[i] };
}

void salir(int codigo) { exit(codigo); }

CadenaSegura concat(CadenaSegura a, CadenaSegura b) {
    int _tl = a.longitud + b.longitud;
    char* _buf = (char*)malloc(_tl + 1);
    if (!_buf) { fprintf(stderr,"Error: Asignación de memoria falló en concat()\n"); exit(1); }
    memcpy(_buf, a.datos, a.longitud);
    memcpy(_buf + a.longitud, b.datos, b.longitud);
    _buf[_tl] = 0;
    CadenaSegura _r = { .longitud = _tl, .datos = _buf };
    return _r;
}

#define IF (1)
#define ELSE (2)
#define FUNCTION (3)
#define RETURN (4)
#define SPAWN (5)
#define RECOVER (6)
#define LISTEN (7)
#define WHILE (8)
#define IMPORT (9)
#define STRUCT (10)
#define BREAK (11)
#define CONTINUE (12)
#define DOT (13)
#define AND (14)
#define OR (15)
#define NOT (16)
#define TRUE (17)
#define FALSE (18)
#define IDENTIFIER (19)
#define NUMBER (20)
#define FLOAT (21)
#define STRING (22)
#define GREATER (23)
#define LESS (24)
#define EQUALS (25)
#define NOT_EQUALS (26)
#define LESS_EQUALS (27)
#define GREATER_EQUALS (28)
#define ASSIGN (29)
#define PLUS (30)
#define MINUS (31)
#define STAR (32)
#define SLASH (33)
#define MODULO (34)
#define ARROW (35)
#define MATCH (36)
#define ARROW_RIGHT (37)
#define LPAREN (38)
#define RPAREN (39)
#define COLON (40)
#define COMMA (41)
#define NEWLINE (42)
#define INDENT (43)
#define DEDENT (44)
#define AMPERSAND (45)
#define INSEGURO (46)
#define IMPORTAR_C (47)
#define EXTERNO (48)
#define ARROW_LEFT (49)
#define REQUIERE (50)
#define GARANTIZA (51)
#define CANAL (52)
#define ASM (53)
#define CONSTANTE (54)
#define SEMICOLON (55)
#define PARA (56)
#define EOF (57)
int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    synapse_esperar_hilos();
    return 0;
}