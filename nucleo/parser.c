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
extern void cerrar(CanalConcurrencia* canal);
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

struct TokenExt;
struct NodoAST;
struct ParserEst;

int parser_nuevo_nodo(struct ParserEst est, int tipo, int linea, int columna);
void parser_error(struct ParserEst est, CadenaSegura mensaje, int linea, int columna);
int token_tipo(struct ParserEst est, int pos);
int token_linea(struct ParserEst est, int pos);
int token_columna(struct ParserEst est, int pos);
void token_avanzar(struct ParserEst est);
int token_mirar(struct ParserEst est);
int token_esperar(struct ParserEst est, int esperado);
int token_esperar_texto(struct ParserEst est, int esperado);
int parsear_expresion(struct ParserEst est);
int parsear_logica(struct ParserEst est);
int parsear_comparacion(struct ParserEst est);
int parsear_adicion(struct ParserEst est);
int parsear_multiplicacion(struct ParserEst est);
int parsear_unario(struct ParserEst est);
int parsear_primario(struct ParserEst est);
int parsear_sentencia(struct ParserEst est);
int parsear_funcion(struct ParserEst est);
int parsear_si(struct ParserEst est);
int parsear_mientras(struct ParserEst est);
int parsear_para(struct ParserEst est);
int parsear_retornar(struct ParserEst est);
int parsear_lanzar(struct ParserEst est);
int parsear_escuchar(struct ParserEst est);
int parsear_asignacion(struct ParserEst est);
int parsear_estructura_def(struct ParserEst est);
int parsear_constante(struct ParserEst est);
int parsear_asm(struct ParserEst est);
int parsear_inseguro(struct ParserEst est);
int parsear_importar_c(struct ParserEst est);
int parsear_externo(struct ParserEst est);
int parsear_coincidir(struct ParserEst est);
int parsear_enviar_canal(struct ParserEst est);
struct Programa parsear(CadenaSegura fuente);

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
#define NODO_PROGRAMA (1)
#define NODO_FUNCION (2)
#define NODO_SI (3)
#define NODO_MIENTRAS (4)
#define NODO_RETORNAR (5)
#define NODO_EXPR (6)
#define NODO_ASIGNACION (7)
#define NODO_IDENTIFICADOR (8)
#define NODO_NUMERO (9)
#define NODO_DECIMAL (10)
#define NODO_CADENA_LIT (11)
#define NODO_BINARIA (12)
#define NODO_UNARIA (13)
#define NODO_LLAMADA (14)
#define NODO_PARAMETRO (15)
#define NODO_ESTRUCTURA (16)
#define NODO_IMPORTAR (17)
#define NODO_LANZAR (18)
#define NODO_ESCUCHAR (19)
#define NODO_ROMPER (20)
#define NODO_SIGUIENTE (21)
#define NODO_BOOLEANO (22)
#define NODO_CONSTANTE (23)
#define NODO_INSEGURO (24)
#define NODO_IMPORTAR_C (25)
#define NODO_EXTERNO (26)
#define NODO_RECUPERAR (27)
#define NODO_TENSOR (28)
#define NODO_INDICE (29)
#define NODO_TRANSFERIDO (30)
#define NODO_ACCESO_CAMPO (31)
#define NODO_ASIGNACION_CAMPO (32)
#define NODO_PARRAFO (33)
#define NODO_DECLARACION (34)
#define NODO_LOG (35)
#define NODO_PUNTERO (36)
#define NODO_DEREF (37)
#define NODO_COINCIDIR (38)
#define NODO_CASO (39)
#define NODO_ASM (40)
#define NODO_CANAL_CREAR (41)
#define NODO_ENVIAR_CANAL (42)
#define NODO_RECIBIR_CANAL (43)
#define NODO_VACIO (44)
typedef struct TokenExt {
    int tipo;
    int linea;
    int columna;
    int ptr_valor;
    int len_valor;
} TokenExt;

static inline struct TokenExt TokenExt_nuevo() {
    struct TokenExt _r = {0};
    return _r;
}

typedef struct NodoAST {
    int tipo_nodo;
    int linea;
    int columna;
    int valor_int;
    float valor_dec;
    int ptr_str;
    int len_str;
    int hijo_izq;
    int hijo_der;
    int hermano;
    int ptr_extra;
} NodoAST;

static inline struct NodoAST NodoAST_nuevo() {
    struct NodoAST _r = {0};
    return _r;
}

typedef struct ParserEst {
    struct TokenExt* tokens;
    int total_tokens;
    int posicion;
    struct NodoAST* nodos;
    int total_nodos;
    int hay_error;
    CadenaSegura error_mensaje;
    int error_linea;
    int error_columna;
    int es_sin_std;
} ParserEst;

static inline struct ParserEst ParserEst_nuevo() {
    struct ParserEst _r = {0};
    return _r;
}

int parser_nuevo_nodo(struct ParserEst est, int tipo, int linea, int columna) {
    { /* unsafe */
        int idx = 0;
        idx = est.total_nodos;
        est.nodos[idx].tipo_nodo = tipo;
        est.nodos[idx].linea = linea;
        est.nodos[idx].columna = columna;
        est.nodos[idx].valor_int = 0;
        est.nodos[idx].hijo_izq = 0;
        est.nodos[idx].hijo_der = 0;
        est.nodos[idx].hermano = 0;
        est.total_nodos = idx + 1;
        int _ret_156 = idx;
        return _ret_156;
    }
}

void parser_error(struct ParserEst est, CadenaSegura mensaje, int linea, int columna) {
    est.hay_error = 1;
    est.error_mensaje = mensaje;
    est.error_linea = linea;
    est.error_columna = columna;
}

int token_tipo(struct ParserEst est, int pos) {
    { /* unsafe */
        int r = 0;
        r = (pos < est.total_tokens) ? est.tokens[pos].tipo : 57;
        int _ret_170 = r;
        return _ret_170;
    }
}

int token_linea(struct ParserEst est, int pos) {
    { /* unsafe */
        int r = 0;
        r = (pos < est.total_tokens) ? est.tokens[pos].linea : 0;
        int _ret_176 = r;
        return _ret_176;
    }
}

int token_columna(struct ParserEst est, int pos) {
    { /* unsafe */
        int r = 0;
        r = (pos < est.total_tokens) ? est.tokens[pos].columna : 0;
        int _ret_182 = r;
        return _ret_182;
    }
}

void token_avanzar(struct ParserEst est) {
    { /* unsafe */
        est.posicion = est.posicion + 1;
    }
}

int token_mirar(struct ParserEst est) {
    { /* unsafe */
        int r = 0;
        r = (est.posicion < est.total_tokens) ? est.tokens[est.posicion].tipo : 57;
        int _ret_192 = r;
        return _ret_192;
    }
}

int token_esperar(struct ParserEst est, int esperado) {
    int t = token_mirar(est);
    if ((t == esperado)) {
        { /* unsafe */
            est.posicion = est.posicion + 1;
        }
        int _ret_199 = 1;
        return _ret_199;
    }
    est.hay_error = 1;
    int _ret_201 = 0;
    return _ret_201;
}

int token_esperar_texto(struct ParserEst est, int esperado) {
    int t = token_mirar(est);
    if ((t == esperado)) {
        int linea = token_linea(est, est.posicion);
        int col = token_columna(est, est.posicion);
        { /* unsafe */
            est.posicion = est.posicion + 1;
        }
        int _ret_210 = parser_nuevo_nodo(est, NODO_IDENTIFICADOR, linea, col);
        return _ret_210;
    }
    est.hay_error = 1;
    int _ret_212 = 0;
    return _ret_212;
}

int parsear_expresion(struct ParserEst est) {
    int _ret_216 = parsear_logica(est);
    return _ret_216;
}

int parsear_logica(struct ParserEst est) {
    int linea = 0;
    int col = 0;
    int der = 0;
    int nodo = 0;
    int izq = parsear_comparacion(est);
    int r = 1;
    while ((r == 1)) {
        int t = token_mirar(est);
        if ((t == T_Y)) {
            linea = token_linea(est, est.posicion);
            col = token_columna(est, est.posicion);
            token_avanzar(est);
            der = parsear_comparacion(est);
            nodo = parser_nuevo_nodo(est, NODO_BINARIA, linea, col);
            { /* unsafe */
                est.nodos[nodo].valor_int = 100;
                est.nodos[nodo].hijo_izq = izq;
                est.nodos[nodo].hijo_der = der;
            }
            izq = nodo;
            continue;
        }
        if ((t == T_O)) {
            linea = token_linea(est, est.posicion);
            col = token_columna(est, est.posicion);
            token_avanzar(est);
            der = parsear_comparacion(est);
            nodo = parser_nuevo_nodo(est, NODO_BINARIA, linea, col);
            { /* unsafe */
                est.nodos[nodo].valor_int = 101;
                est.nodos[nodo].hijo_izq = izq;
                est.nodos[nodo].hijo_der = der;
            }
            izq = nodo;
            continue;
        }
        r = 0;
    }
    int _ret_252 = izq;
    return _ret_252;
}

int parsear_comparacion(struct ParserEst est) {
    int linea = 0;
    int col = 0;
    int der = 0;
    int nodo = 0;
    int izq = parsear_adicion(est);
    int r = 1;
    while ((r == 1)) {
        int t = token_mirar(est);
        if ((t == T_MAYOR)) {
            linea = token_linea(est, est.posicion);
            col = token_columna(est, est.posicion);
            token_avanzar(est);
            der = parsear_adicion(est);
            nodo = parser_nuevo_nodo(est, NODO_BINARIA, linea, col);
            { /* unsafe */
                est.nodos[nodo].valor_int = 200;
                est.nodos[nodo].hijo_izq = izq;
                est.nodos[nodo].hijo_der = der;
            }
            izq = nodo;
            continue;
        }
        if ((t == T_MENOR)) {
            linea = token_linea(est, est.posicion);
            col = token_columna(est, est.posicion);
            token_avanzar(est);
            der = parsear_adicion(est);
            nodo = parser_nuevo_nodo(est, NODO_BINARIA, linea, col);
            { /* unsafe */
                est.nodos[nodo].valor_int = 201;
                est.nodos[nodo].hijo_izq = izq;
                est.nodos[nodo].hijo_der = der;
            }
            izq = nodo;
            continue;
        }
        if ((t == T_IGUAL)) {
            linea = token_linea(est, est.posicion);
            col = token_columna(est, est.posicion);
            token_avanzar(est);
            der = parsear_adicion(est);
            nodo = parser_nuevo_nodo(est, NODO_BINARIA, linea, col);
            { /* unsafe */
                est.nodos[nodo].valor_int = 202;
                est.nodos[nodo].hijo_izq = izq;
                est.nodos[nodo].hijo_der = der;
            }
            izq = nodo;
            continue;
        }
        if ((t == T_DISTINTO)) {
            linea = token_linea(est, est.posicion);
            col = token_columna(est, est.posicion);
            token_avanzar(est);
            der = parsear_adicion(est);
            nodo = parser_nuevo_nodo(est, NODO_BINARIA, linea, col);
            { /* unsafe */
                est.nodos[nodo].valor_int = 203;
                est.nodos[nodo].hijo_izq = izq;
                est.nodos[nodo].hijo_der = der;
            }
            izq = nodo;
            continue;
        }
        if ((t == T_MENOR_IGUAL)) {
            linea = token_linea(est, est.posicion);
            col = token_columna(est, est.posicion);
            token_avanzar(est);
            der = parsear_adicion(est);
            nodo = parser_nuevo_nodo(est, NODO_BINARIA, linea, col);
            { /* unsafe */
                est.nodos[nodo].valor_int = 204;
                est.nodos[nodo].hijo_izq = izq;
                est.nodos[nodo].hijo_der = der;
            }
            izq = nodo;
            continue;
        }
        if ((t == T_MAYOR_IGUAL)) {
            linea = token_linea(est, est.posicion);
            col = token_columna(est, est.posicion);
            token_avanzar(est);
            der = parsear_adicion(est);
            nodo = parser_nuevo_nodo(est, NODO_BINARIA, linea, col);
            { /* unsafe */
                est.nodos[nodo].valor_int = 205;
                est.nodos[nodo].hijo_izq = izq;
                est.nodos[nodo].hijo_der = der;
            }
            izq = nodo;
            continue;
        }
        r = 0;
    }
    int _ret_336 = izq;
    return _ret_336;
}

int parsear_adicion(struct ParserEst est) {
    int linea = 0;
    int col = 0;
    int der = 0;
    int nodo = 0;
    int izq = parsear_multiplicacion(est);
    int r = 1;
    while ((r == 1)) {
        int t = token_mirar(est);
        if ((t == T_MAS)) {
            linea = token_linea(est, est.posicion);
            col = token_columna(est, est.posicion);
            token_avanzar(est);
            der = parsear_multiplicacion(est);
            nodo = parser_nuevo_nodo(est, NODO_BINARIA, linea, col);
            { /* unsafe */
                est.nodos[nodo].valor_int = 300;
                est.nodos[nodo].hijo_izq = izq;
                est.nodos[nodo].hijo_der = der;
            }
            izq = nodo;
            continue;
        }
        if ((t == T_MENOS)) {
            linea = token_linea(est, est.posicion);
            col = token_columna(est, est.posicion);
            token_avanzar(est);
            der = parsear_multiplicacion(est);
            nodo = parser_nuevo_nodo(est, NODO_BINARIA, linea, col);
            { /* unsafe */
                est.nodos[nodo].valor_int = 301;
                est.nodos[nodo].hijo_izq = izq;
                est.nodos[nodo].hijo_der = der;
            }
            izq = nodo;
            continue;
        }
        r = 0;
    }
    int _ret_372 = izq;
    return _ret_372;
}

int parsear_multiplicacion(struct ParserEst est) {
    int linea = 0;
    int col = 0;
    int der = 0;
    int nodo = 0;
    int izq = parsear_unario(est);
    int r = 1;
    while ((r == 1)) {
        int t = token_mirar(est);
        if ((t == T_POR)) {
            linea = token_linea(est, est.posicion);
            col = token_columna(est, est.posicion);
            token_avanzar(est);
            der = parsear_unario(est);
            nodo = parser_nuevo_nodo(est, NODO_BINARIA, linea, col);
            { /* unsafe */
                est.nodos[nodo].valor_int = 400;
                est.nodos[nodo].hijo_izq = izq;
                est.nodos[nodo].hijo_der = der;
            }
            izq = nodo;
            continue;
        }
        if ((t == T_DIV)) {
            linea = token_linea(est, est.posicion);
            col = token_columna(est, est.posicion);
            token_avanzar(est);
            der = parsear_unario(est);
            nodo = parser_nuevo_nodo(est, NODO_BINARIA, linea, col);
            { /* unsafe */
                est.nodos[nodo].valor_int = 401;
                est.nodos[nodo].hijo_izq = izq;
                est.nodos[nodo].hijo_der = der;
            }
            izq = nodo;
            continue;
        }
        if ((t == T_MOD)) {
            linea = token_linea(est, est.posicion);
            col = token_columna(est, est.posicion);
            token_avanzar(est);
            der = parsear_unario(est);
            nodo = parser_nuevo_nodo(est, NODO_BINARIA, linea, col);
            { /* unsafe */
                est.nodos[nodo].valor_int = 402;
                est.nodos[nodo].hijo_izq = izq;
                est.nodos[nodo].hijo_der = der;
            }
            izq = nodo;
            continue;
        }
        r = 0;
    }
    int _ret_420 = izq;
    return _ret_420;
}

int parsear_unario(struct ParserEst est) {
    int linea = 0;
    int col = 0;
    int expr = 0;
    int nodo = 0;
    int t = token_mirar(est);
    if ((t == T_MENOS)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        expr = parsear_unario(est);
        nodo = parser_nuevo_nodo(est, NODO_UNARIA, linea, col);
        { /* unsafe */
            est.nodos[nodo].valor_int = 500;
            est.nodos[nodo].hijo_izq = expr;
        }
        int _ret_437 = nodo;
        return _ret_437;
    }
    if ((t == T_NO)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        expr = parsear_unario(est);
        nodo = parser_nuevo_nodo(est, NODO_UNARIA, linea, col);
        { /* unsafe */
            est.nodos[nodo].valor_int = 501;
            est.nodos[nodo].hijo_izq = expr;
        }
        int _ret_447 = nodo;
        return _ret_447;
    }
    if ((t == T_AMPERSAND)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        expr = parsear_unario(est);
        nodo = parser_nuevo_nodo(est, NODO_PUNTERO, linea, col);
        { /* unsafe */
            est.nodos[nodo].hijo_izq = expr;
        }
        int _ret_456 = nodo;
        return _ret_456;
    }
    if ((t == T_POR)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        expr = parsear_unario(est);
        nodo = parser_nuevo_nodo(est, NODO_DEREF, linea, col);
        { /* unsafe */
            est.nodos[nodo].hijo_izq = expr;
        }
        int _ret_465 = nodo;
        return _ret_465;
    }
    int _ret_466 = parsear_primario(est);
    return _ret_466;
}

int parsear_primario(struct ParserEst est) {
    int linea = 0;
    int col = 0;
    int nodo = 0;
    int t = token_mirar(est);
    if ((t == T_NUMERO)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        nodo = parser_nuevo_nodo(est, NODO_NUMERO, linea, col);
        int _ret_478 = nodo;
        return _ret_478;
    }
    if ((t == T_FLOTANTE)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        nodo = parser_nuevo_nodo(est, NODO_DECIMAL, linea, col);
        int _ret_484 = nodo;
        return _ret_484;
    }
    if ((t == T_CADENA)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        nodo = parser_nuevo_nodo(est, NODO_CADENA_LIT, linea, col);
        int _ret_490 = nodo;
        return _ret_490;
    }
    if ((t == T_VERDADERO)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        nodo = parser_nuevo_nodo(est, NODO_BOOLEANO, linea, col);
        { /* unsafe */
            est.nodos[nodo].valor_int = 1;
        }
        int _ret_498 = nodo;
        return _ret_498;
    }
    if ((t == T_FALSO)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        nodo = parser_nuevo_nodo(est, NODO_BOOLEANO, linea, col);
        { /* unsafe */
            est.nodos[nodo].valor_int = 0;
        }
        int _ret_506 = nodo;
        return _ret_506;
    }
    if ((t == T_IDENTIFICADOR)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        nodo = parser_nuevo_nodo(est, NODO_IDENTIFICADOR, linea, col);
        int t2 = token_mirar(est);
        if ((t2 == T_PAREN_IZQ)) {
            { /* unsafe */
                est.nodos[nodo].tipo_nodo = 14;
            }
            token_esperar(est, T_PAREN_IZQ);
            int r = 1;
            while ((r == 1)) {
                if ((token_mirar(est) == T_PAREN_DER)) {
                    break;
                }
                int arg = parsear_expresion(est);
                if ((token_mirar(est) == T_COMA)) {
                    token_avanzar(est);
                    continue;
                }
                r = 1;
            }
            token_esperar(est, T_PAREN_DER);
        }
        if ((t2 == T_PUNTO)) {
            if ((token_mirar(est) == T_PUNTO)) {
                token_avanzar(est);
                int tok_campo = token_mirar(est);
                int linea2 = token_linea(est, est.posicion);
                int col2 = token_columna(est, est.posicion);
                if ((tok_campo == T_IDENTIFICADOR)) {
                    token_avanzar(est);
                    int nodo2 = parser_nuevo_nodo(est, NODO_ACCESO_CAMPO, linea2, col2);
                    { /* unsafe */
                        est.nodos[nodo2].hijo_izq = nodo;
                    }
                    nodo = nodo2;
                }
            }
        }
        int _ret_539 = nodo;
        return _ret_539;
    }
    if ((t == T_PAREN_IZQ)) {
        token_avanzar(est);
        int expr = parsear_expresion(est);
        token_esperar(est, T_PAREN_DER);
        int _ret_544 = expr;
        return _ret_544;
    }
    parser_error(est, (CadenaSegura){ .longitud = 20, .datos = "Expresion inesperada" }, token_linea(est, est.posicion), token_columna(est, est.posicion));
    int _ret_546 = 0;
    return _ret_546;
}

int parsear_sentencia(struct ParserEst est) {
    int linea = 0;
    int col = 0;
    int nodo = 0;
    int t = token_mirar(est);
    if ((t == T_FUNCION)) {
        int _ret_555 = parsear_funcion(est);
        return _ret_555;
    }
    if ((t == T_ESTRUCTURA)) {
        int _ret_557 = parsear_estructura_def(est);
        return _ret_557;
    }
    if ((t == T_IF)) {
        int _ret_559 = parsear_si(est);
        return _ret_559;
    }
    if ((t == T_MIENTRAS)) {
        int _ret_561 = parsear_mientras(est);
        return _ret_561;
    }
    if ((t == T_PARA)) {
        int _ret_563 = parsear_para(est);
        return _ret_563;
    }
    if ((t == T_RETORNAR)) {
        int _ret_565 = parsear_retornar(est);
        return _ret_565;
    }
    if ((t == T_LANZAR)) {
        int _ret_567 = parsear_lanzar(est);
        return _ret_567;
    }
    if ((t == T_ESCUCHAR)) {
        int _ret_569 = parsear_escuchar(est);
        return _ret_569;
    }
    if ((t == T_ROMPER)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        int _ret_574 = parser_nuevo_nodo(est, NODO_ROMPER, linea, col);
        return _ret_574;
    }
    if ((t == T_SIGUIENTE)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        int _ret_579 = parser_nuevo_nodo(est, NODO_SIGUIENTE, linea, col);
        return _ret_579;
    }
    if ((t == T_IMPORTAR)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        nodo = parser_nuevo_nodo(est, NODO_IMPORTAR, linea, col);
        int _ret_585 = nodo;
        return _ret_585;
    }
    if ((t == T_ESTRUCTURA)) {
        int _ret_587 = parsear_estructura_def(est);
        return _ret_587;
    }
    if ((t == T_CONSTANTE)) {
        int _ret_589 = parsear_constante(est);
        return _ret_589;
    }
    if ((t == T_ASM)) {
        int _ret_591 = parsear_asm(est);
        return _ret_591;
    }
    if ((t == T_INSEGURO)) {
        int _ret_593 = parsear_inseguro(est);
        return _ret_593;
    }
    if ((t == T_IMPORTAR_C)) {
        int _ret_595 = parsear_importar_c(est);
        return _ret_595;
    }
    if ((t == T_EXTERNO)) {
        int _ret_597 = parsear_externo(est);
        return _ret_597;
    }
    if ((t == T_COINCIDIR)) {
        int _ret_599 = parsear_coincidir(est);
        return _ret_599;
    }
    if ((t == T_INDENTAR)) {
        int _ret_601 = 0;
        return _ret_601;
    }
    if ((t == T_DESINDENTAR)) {
        int _ret_603 = 0;
        return _ret_603;
    }
    if ((t == T_NUEVALINEA)) {
        int _ret_605 = 0;
        return _ret_605;
    }
    if ((t == T_FIN)) {
        int _ret_607 = 0;
        return _ret_607;
    }
    if ((t == T_IDENTIFICADOR)) {
        int t2 = token_mirar(est);
        if ((t2 == T_ASIGNAR)) {
            int _ret_611 = parsear_asignacion(est);
            return _ret_611;
        }
        if ((t2 == T_FLECHA_IZQ)) {
            int _ret_613 = parsear_enviar_canal(est);
            return _ret_613;
        }
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        int expr = parsear_expresion(est);
        int t3 = token_mirar(est);
        if ((t3 == T_RECUPERAR)) {
            token_avanzar(est);
            token_esperar(est, T_DOSPUNTOS);
            int plan_b = parsear_expresion(est);
            int _ret_623 = expr;
            return _ret_623;
        }
        nodo = parser_nuevo_nodo(est, NODO_EXPR, linea, col);
        { /* unsafe */
            est.nodos[nodo].hijo_izq = expr;
        }
        int _ret_627 = nodo;
        return _ret_627;
    }
    int _ret_628 = 0;
    return _ret_628;
}

int parsear_funcion(struct ParserEst est) {
    int r2 = 0;
    int expr = 0;
    int r = 0;
    if ((token_esperar(est, T_FUNCION) == 0)) {
        int _ret_636 = 0;
        return _ret_636;
    }
    int t = token_mirar(est);
    if ((t != T_IDENTIFICADOR)) {
        parser_error(est, (CadenaSegura){ .longitud = 29, .datos = "Se esperaba nombre de funcion" }, token_linea(est, est.posicion), token_columna(est, est.posicion));
        int _ret_640 = 0;
        return _ret_640;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    token_avanzar(est);
    int nodo_func = parser_nuevo_nodo(est, NODO_FUNCION, linea, col);
    if ((token_esperar(est, T_PAREN_IZQ) == 0)) {
        int _ret_646 = 0;
        return _ret_646;
    }
    int ultimo_param = 0;
    if ((token_mirar(est) != T_PAREN_DER)) {
        r = 1;
        while ((r == 1)) {
            int linea_p = token_linea(est, est.posicion);
            int col_p = token_columna(est, est.posicion);
            if ((token_mirar(est) == T_IDENTIFICADOR)) {
                token_avanzar(est);
                if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
                    int _ret_657 = 0;
                    return _ret_657;
                }
                if ((token_mirar(est) == T_IDENTIFICADOR)) {
                    token_avanzar(est);
                    int nodo_p = parser_nuevo_nodo(est, NODO_PARAMETRO, linea_p, col_p);
                    if ((token_mirar(est) == T_COMA)) {
                        token_avanzar(est);
                        continue;
                    } else {
                        r = 0;
                    }
                } else {
                    r = 0;
                }
            } else {
                r = 0;
            }
        }
    }
    if ((token_esperar(est, T_PAREN_DER) == 0)) {
        int _ret_671 = 0;
        return _ret_671;
    }
    if ((token_esperar(est, T_FLECHA) == 0)) {
        int _ret_673 = 0;
        return _ret_673;
    }
    if ((token_mirar(est) == T_IDENTIFICADOR)) {
        token_avanzar(est);
    }
    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
        int _ret_678 = 0;
        return _ret_678;
    }
    r = 1;
    while ((r == 1)) {
        t = token_mirar(est);
        if ((t == T_NUEVALINEA)) {
            token_avanzar(est);
            continue;
        }
        if ((t == T_INDENTAR)) {
            token_avanzar(est);
            while ((r == 1)) {
                t = token_mirar(est);
                if ((t == T_REQUIERE)) {
                    token_avanzar(est);
                    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
                        int _ret_693 = 0;
                        return _ret_693;
                    }
                    r2 = 1;
                    while ((r2 == 1)) {
                        t = token_mirar(est);
                        if ((t == T_NUEVALINEA)) {
                            token_avanzar(est);
                            continue;
                        }
                        if ((t == T_INDENTAR)) {
                            token_avanzar(est);
                            while ((r2 == 1)) {
                                t = token_mirar(est);
                                if ((t == T_NUEVALINEA)) {
                                    token_avanzar(est);
                                    continue;
                                }
                                if ((t == T_DESINDENTAR)) {
                                    token_avanzar(est);
                                    r2 = 0;
                                    break;
                                }
                                expr = parsear_expresion(est);
                                continue;
                            }
                        } else {
                            r2 = 0;
                        }
                    }
                    continue;
                }
                if ((t == T_GARANTIZA)) {
                    token_avanzar(est);
                    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
                        int _ret_719 = 0;
                        return _ret_719;
                    }
                    r2 = 1;
                    while ((r2 == 1)) {
                        t = token_mirar(est);
                        if ((t == T_NUEVALINEA)) {
                            token_avanzar(est);
                            continue;
                        }
                        if ((t == T_INDENTAR)) {
                            token_avanzar(est);
                            while ((r2 == 1)) {
                                t = token_mirar(est);
                                if ((t == T_NUEVALINEA)) {
                                    token_avanzar(est);
                                    continue;
                                }
                                if ((t == T_DESINDENTAR)) {
                                    token_avanzar(est);
                                    r2 = 0;
                                    break;
                                }
                                expr = parsear_expresion(est);
                                continue;
                            }
                        } else {
                            r2 = 0;
                        }
                    }
                    continue;
                }
                if ((t == T_DESINDENTAR)) {
                    token_avanzar(est);
                    r = 0;
                    break;
                }
                r = 0;
            }
        } else {
            r = 0;
        }
    }
    if ((token_mirar(est) == T_INDENTAR)) {
        token_avanzar(est);
        while ((r == 1)) {
            t = token_mirar(est);
            if ((t == T_DESINDENTAR)) {
                token_avanzar(est);
                r = 0;
                break;
            }
            if ((t == T_FIN)) {
                r = 0;
                break;
            }
            int stmt = parsear_sentencia(est);
            continue;
        }
    }
    int _ret_763 = nodo_func;
    return _ret_763;
}

int parsear_si(struct ParserEst est) {
    int t = 0;
    int stmt = 0;
    int r = 1;
    if ((token_esperar(est, T_IF) == 0)) {
        int _ret_771 = 0;
        return _ret_771;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    int nodo = parser_nuevo_nodo(est, NODO_SI, linea, col);
    int cond = parsear_expresion(est);
    { /* unsafe */
        est.nodos[nodo].hijo_izq = cond;
    }
    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
        int _ret_779 = 0;
        return _ret_779;
    }
    if ((token_mirar(est) == T_NUEVALINEA)) {
        token_avanzar(est);
        if ((token_mirar(est) == T_INDENTAR)) {
            token_avanzar(est);
            while ((r == 1)) {
                t = token_mirar(est);
                if ((t == T_DESINDENTAR)) {
                    token_avanzar(est);
                    r = 0;
                    break;
                }
                if ((t == T_FIN)) {
                    r = 0;
                    break;
                }
                stmt = parsear_sentencia(est);
                continue;
            }
        }
    }
    r = 1;
    if ((token_mirar(est) == T_ELSE)) {
        token_avanzar(est);
        if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
            int _ret_799 = 0;
            return _ret_799;
        }
        if ((token_mirar(est) == T_NUEVALINEA)) {
            token_avanzar(est);
            if ((token_mirar(est) == T_INDENTAR)) {
                token_avanzar(est);
                while ((r == 1)) {
                    t = token_mirar(est);
                    if ((t == T_DESINDENTAR)) {
                        token_avanzar(est);
                        r = 0;
                        break;
                    }
                    if ((t == T_FIN)) {
                        r = 0;
                        break;
                    }
                    stmt = parsear_sentencia(est);
                    continue;
                }
            }
        }
    }
    int _ret_815 = nodo;
    return _ret_815;
}

int parsear_mientras(struct ParserEst est) {
    if ((token_esperar(est, T_MIENTRAS) == 0)) {
        int _ret_819 = 0;
        return _ret_819;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    int nodo = parser_nuevo_nodo(est, NODO_MIENTRAS, linea, col);
    int cond = parsear_expresion(est);
    { /* unsafe */
        est.nodos[nodo].hijo_izq = cond;
    }
    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
        int _ret_827 = 0;
        return _ret_827;
    }
    if ((token_mirar(est) == T_NUEVALINEA)) {
        token_avanzar(est);
        if ((token_mirar(est) == T_INDENTAR)) {
            token_avanzar(est);
            int r = 1;
            while ((r == 1)) {
                int t = token_mirar(est);
                if ((t == T_DESINDENTAR)) {
                    token_avanzar(est);
                    r = 0;
                    break;
                }
                if ((t == T_FIN)) {
                    r = 0;
                    break;
                }
                int stmt = parsear_sentencia(est);
                continue;
            }
        }
    }
    int _ret_844 = nodo;
    return _ret_844;
}

int parsear_para(struct ParserEst est) {
    if ((token_esperar(est, T_PARA) == 0)) {
        int _ret_848 = 0;
        return _ret_848;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    int nodo = parser_nuevo_nodo(est, NODO_VACIO, linea, col);
    parsear_asignacion(est);
    if ((token_esperar(est, T_PUNTOCOMA) == 0)) {
        int _ret_854 = 0;
        return _ret_854;
    }
    parsear_expresion(est);
    if ((token_esperar(est, T_PUNTOCOMA) == 0)) {
        int _ret_857 = 0;
        return _ret_857;
    }
    parsear_asignacion(est);
    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
        int _ret_860 = 0;
        return _ret_860;
    }
    if ((token_mirar(est) == T_NUEVALINEA)) {
        token_avanzar(est);
        if ((token_mirar(est) == T_INDENTAR)) {
            token_avanzar(est);
            int r = 1;
            while ((r == 1)) {
                int t = token_mirar(est);
                if ((t == T_DESINDENTAR)) {
                    token_avanzar(est);
                    r = 0;
                    break;
                }
                if ((t == T_FIN)) {
                    r = 0;
                    break;
                }
                int stmt = parsear_sentencia(est);
                continue;
            }
        }
    }
    int _ret_877 = nodo;
    return _ret_877;
}

int parsear_retornar(struct ParserEst est) {
    if ((token_esperar(est, T_RETORNAR) == 0)) {
        int _ret_881 = 0;
        return _ret_881;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    int nodo = parser_nuevo_nodo(est, NODO_RETORNAR, linea, col);
    int t = token_mirar(est);
    if ((t != T_NUEVALINEA)) {
        if ((t != T_DESINDENTAR)) {
            if ((t != T_FIN)) {
                int expr = parsear_expresion(est);
                { /* unsafe */
                    est.nodos[nodo].hijo_izq = expr;
                }
            }
        }
    }
    int _ret_892 = nodo;
    return _ret_892;
}

int parsear_lanzar(struct ParserEst est) {
    if ((token_esperar(est, T_LANZAR) == 0)) {
        int _ret_896 = 0;
        return _ret_896;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    int nodo = parser_nuevo_nodo(est, NODO_LANZAR, linea, col);
    int expr = parsear_expresion(est);
    { /* unsafe */
        est.nodos[nodo].hijo_izq = expr;
    }
    int _ret_903 = nodo;
    return _ret_903;
}

int parsear_escuchar(struct ParserEst est) {
    if ((token_esperar(est, T_ESCUCHAR) == 0)) {
        int _ret_907 = 0;
        return _ret_907;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    int nodo = parser_nuevo_nodo(est, NODO_ESCUCHAR, linea, col);
    parsear_expresion(est);
    if ((token_esperar(est, T_FLECHA) == 0)) {
        int _ret_913 = 0;
        return _ret_913;
    }
    int expr = parsear_expresion(est);
    int _ret_915 = nodo;
    return _ret_915;
}

int parsear_asignacion(struct ParserEst est) {
    int t = token_mirar(est);
    if ((t != T_IDENTIFICADOR)) {
        int _ret_920 = 0;
        return _ret_920;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    token_avanzar(est);
    if ((token_esperar(est, T_ASIGNAR) == 0)) {
        int _ret_925 = 0;
        return _ret_925;
    }
    int nodo = parser_nuevo_nodo(est, NODO_ASIGNACION, linea, col);
    int expr = parsear_expresion(est);
    { /* unsafe */
        est.nodos[nodo].hijo_der = expr;
    }
    int _ret_930 = nodo;
    return _ret_930;
}

int parsear_estructura_def(struct ParserEst est) {
    if ((token_esperar(est, T_ESTRUCTURA) == 0)) {
        int _ret_934 = 0;
        return _ret_934;
    }
    int t = token_mirar(est);
    if ((t != T_IDENTIFICADOR)) {
        int _ret_937 = 0;
        return _ret_937;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    token_avanzar(est);
    int nodo = parser_nuevo_nodo(est, NODO_ESTRUCTURA, linea, col);
    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
        int _ret_943 = 0;
        return _ret_943;
    }
    if ((token_mirar(est) == T_NUEVALINEA)) {
        token_avanzar(est);
        if ((token_mirar(est) == T_INDENTAR)) {
            token_avanzar(est);
            int r = 1;
            while ((r == 1)) {
                t = token_mirar(est);
                if ((t == T_NUEVALINEA)) {
                    token_avanzar(est);
                    continue;
                }
                if ((t == T_DESINDENTAR)) {
                    token_avanzar(est);
                    r = 0;
                    break;
                }
                if ((t == T_FIN)) {
                    r = 0;
                    break;
                }
                if ((t == T_IDENTIFICADOR)) {
                    token_avanzar(est);
                    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
                        int _ret_964 = 0;
                        return _ret_964;
                    }
                    if ((token_mirar(est) == T_IDENTIFICADOR)) {
                        token_avanzar(est);
                    }
                }
                continue;
            }
            int _ret_968 = nodo;
            return _ret_968;
        }
    }
    int _ret_969 = nodo;
    return _ret_969;
}

int parsear_constante(struct ParserEst est) {
    if ((token_esperar(est, T_CONSTANTE) == 0)) {
        int _ret_973 = 0;
        return _ret_973;
    }
    int t = token_mirar(est);
    if ((t != T_IDENTIFICADOR)) {
        int _ret_976 = 0;
        return _ret_976;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    token_avanzar(est);
    int nodo = parser_nuevo_nodo(est, NODO_CONSTANTE, linea, col);
    if ((token_mirar(est) == T_DOSPUNTOS)) {
        token_avanzar(est);
        if ((token_mirar(est) == T_IDENTIFICADOR)) {
            token_avanzar(est);
        }
    }
    if ((token_esperar(est, T_ASIGNAR) == 0)) {
        int _ret_986 = 0;
        return _ret_986;
    }
    int expr = parsear_expresion(est);
    { /* unsafe */
        est.nodos[nodo].hijo_izq = expr;
    }
    int _ret_990 = nodo;
    return _ret_990;
}

int parsear_asm(struct ParserEst est) {
    if ((token_esperar(est, T_ASM) == 0)) {
        int _ret_994 = 0;
        return _ret_994;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    int nodo = parser_nuevo_nodo(est, NODO_ASM, linea, col);
    if ((token_esperar(est, T_PAREN_IZQ) == 0)) {
        int _ret_999 = 0;
        return _ret_999;
    }
    if ((token_mirar(est) == T_CADENA)) {
        { /* unsafe */
            est.nodos[nodo].ptr_str = est.tokens[est.posicion].ptr_valor;
            est.nodos[nodo].len_str = est.tokens[est.posicion].len_valor;
        }
        token_avanzar(est);
    }
    if ((token_esperar(est, T_PAREN_DER) == 0)) {
        int _ret_1006 = 0;
        return _ret_1006;
    }
    int _ret_1007 = nodo;
    return _ret_1007;
}

int parsear_inseguro(struct ParserEst est) {
    if ((token_esperar(est, T_INSEGURO) == 0)) {
        int _ret_1011 = 0;
        return _ret_1011;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    int nodo = parser_nuevo_nodo(est, NODO_INSEGURO, linea, col);
    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
        int _ret_1016 = 0;
        return _ret_1016;
    }
    if ((token_mirar(est) == T_NUEVALINEA)) {
        token_avanzar(est);
        if ((token_mirar(est) == T_INDENTAR)) {
            token_avanzar(est);
            int r = 1;
            while ((r == 1)) {
                int t = token_mirar(est);
                if ((t == T_DESINDENTAR)) {
                    token_avanzar(est);
                    r = 0;
                    break;
                }
                if ((t == T_FIN)) {
                    r = 0;
                    break;
                }
                int stmt = parsear_sentencia(est);
                continue;
            }
        }
    }
    int _ret_1033 = nodo;
    return _ret_1033;
}

int parsear_importar_c(struct ParserEst est) {
    if ((token_esperar(est, T_IMPORTAR_C) == 0)) {
        int _ret_1037 = 0;
        return _ret_1037;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    int nodo = parser_nuevo_nodo(est, NODO_IMPORTAR_C, linea, col);
    if ((token_mirar(est) == T_CADENA)) {
        token_avanzar(est);
    }
    int _ret_1043 = nodo;
    return _ret_1043;
}

int parsear_externo(struct ParserEst est) {
    if ((token_esperar(est, T_EXTERNO) == 0)) {
        int _ret_1047 = 0;
        return _ret_1047;
    }
    if ((token_esperar(est, T_FUNCION) == 0)) {
        int _ret_1049 = 0;
        return _ret_1049;
    }
    int t = token_mirar(est);
    if ((t != T_IDENTIFICADOR)) {
        int _ret_1052 = 0;
        return _ret_1052;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    token_avanzar(est);
    int nodo = parser_nuevo_nodo(est, NODO_EXTERNO, linea, col);
    if ((token_esperar(est, T_PAREN_IZQ) == 0)) {
        int _ret_1058 = 0;
        return _ret_1058;
    }
    int r = 1;
    while ((r == 1)) {
        t = token_mirar(est);
        if ((t == T_PAREN_DER)) {
            r = 0;
            break;
        }
        if ((t == T_IDENTIFICADOR)) {
            token_avanzar(est);
            if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
                int _ret_1068 = 0;
                return _ret_1068;
            }
            if ((token_mirar(est) == T_IDENTIFICADOR)) {
                token_avanzar(est);
            }
            if ((token_mirar(est) == T_POR)) {
                token_avanzar(est);
            }
            if ((token_mirar(est) == T_COMA)) {
                token_avanzar(est);
                continue;
            }
        }
    }
    if ((token_esperar(est, T_PAREN_DER) == 0)) {
        int _ret_1077 = 0;
        return _ret_1077;
    }
    if ((token_esperar(est, T_FLECHA) == 0)) {
        int _ret_1079 = 0;
        return _ret_1079;
    }
    if ((token_mirar(est) == T_IDENTIFICADOR)) {
        token_avanzar(est);
    }
    int _ret_1082 = nodo;
    return _ret_1082;
}

int parsear_coincidir(struct ParserEst est) {
    if ((token_esperar(est, T_COINCIDIR) == 0)) {
        int _ret_1086 = 0;
        return _ret_1086;
    }
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    int nodo = parser_nuevo_nodo(est, NODO_COINCIDIR, linea, col);
    int expr = parsear_expresion(est);
    { /* unsafe */
        est.nodos[nodo].hijo_izq = expr;
    }
    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
        int _ret_1094 = 0;
        return _ret_1094;
    }
    if ((token_mirar(est) == T_NUEVALINEA)) {
        token_avanzar(est);
        if ((token_mirar(est) == T_INDENTAR)) {
            token_avanzar(est);
            int r = 1;
            while ((r == 1)) {
                int t = token_mirar(est);
                if ((t == T_NUEVALINEA)) {
                    token_avanzar(est);
                    continue;
                }
                if ((t == T_DESINDENTAR)) {
                    token_avanzar(est);
                    r = 0;
                    break;
                }
                if ((t == T_FIN)) {
                    r = 0;
                    break;
                }
                if ((t == T_IDENTIFICADOR)) {
                    int linea_c = token_linea(est, est.posicion);
                    int col_c = token_columna(est, est.posicion);
                    token_avanzar(est);
                    int nodo_caso = parser_nuevo_nodo(est, NODO_CASO, linea_c, col_c);
                    if ((token_mirar(est) == T_PAREN_IZQ)) {
                        token_avanzar(est);
                        if ((token_mirar(est) == T_IDENTIFICADOR)) {
                            token_avanzar(est);
                        }
                        if ((token_esperar(est, T_PAREN_DER) == 0)) {
                            int _ret_1122 = 0;
                            return _ret_1122;
                        }
                    }
                    if ((token_esperar(est, T_FLECHA_DER) == 0)) {
                        int _ret_1124 = 0;
                        return _ret_1124;
                    }
                    int r2 = 1;
                    while ((r2 == 1)) {
                        t = token_mirar(est);
                        if ((t == T_NUEVALINEA)) {
                            r2 = 0;
                            break;
                        }
                        if ((t == T_DESINDENTAR)) {
                            r2 = 0;
                            break;
                        }
                        if ((t == T_FIN)) {
                            r2 = 0;
                            break;
                        }
                        int stmt = parsear_sentencia(est);
                        continue;
                    }
                }
                continue;
            }
        }
    }
    int _ret_1140 = nodo;
    return _ret_1140;
}

int parsear_enviar_canal(struct ParserEst est) {
    int linea = token_linea(est, est.posicion);
    int col = token_columna(est, est.posicion);
    int nodo = parser_nuevo_nodo(est, NODO_ENVIAR_CANAL, linea, col);
    if ((token_mirar(est) == T_IDENTIFICADOR)) {
        token_avanzar(est);
    }
    if ((token_esperar(est, T_FLECHA_IZQ) == 0)) {
        int _ret_1149 = 0;
        return _ret_1149;
    }
    int expr = parsear_expresion(est);
    int _ret_1151 = nodo;
    return _ret_1151;
}

// --- Token IDs ---
#define T_IF 1
#define T_ELSE 2
#define T_FUNC 3
#define T_RET 4
#define T_SPAWN 5
#define T_RECOVER 6
#define T_LISTEN 7
#define T_WHILE 8
#define T_IMPORT 9
#define T_BREAK 10
#define T_CONTINUE 11
#define T_DOT 12
#define T_IDENT 13
#define T_NUM 14
#define T_STR 15
#define T_GT 16
#define T_LT 17
#define T_EQ 18
#define T_NE 19
#define T_LE 20
#define T_GE 21
#define T_ASSIGN 22
#define T_PLUS 23
#define T_MINUS 24
#define T_MUL 25
#define T_DIV 26
#define T_MOD 27
#define T_ARROW 28
#define T_LPAREN 29
#define T_RPAREN 30
#define T_COLON 31
#define T_COMMA 32
#define T_NL 33
#define T_INDENT 34
#define T_DEDENT 35
#define T_EOF 36
#define T_STRUCT 37
#define T_AND 38
#define T_OR 39
#define T_NOT 40
#define T_TRUE 41
#define T_FALSE 42
#define T_INSEGURO 43
#define T_IMPORTAR_C 44
#define T_AMPERSAND 45
#define T_EXTERNO 46

#define MAX_TOKS 16384
typedef struct { int tipo; int linea; int col; char val[256]; } _P_Token;
_P_Token _P_tks[MAX_TOKS];
int _P_ntks = 0, _P_tpos = 0, _P_p_err = 0;
int _P_pila_indent[64], _P_nivel_pila = 0;

static void _P_tokenizar(const char* s, int len) {
    int i = 0, li = 1, co = 1;
    while (i < len && _P_ntks < MAX_TOKS - 1) {
        char c = s[i];
        if (c == ' ' || c == '\t') { i++; co++; continue; }
        if (c == '\r') { i++; continue; }
        if (c == '\n') {
            _P_tks[_P_ntks].tipo = T_NL; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = 0;
            _P_ntks++; i++; li++; co = 1;
            while (i < len && (s[i]==' '||s[i]=='\t')) { if(s[i]==' ')co++; else co+=4; i++; }
            if (i < len && s[i]=='\n') continue;
            if (i < len && s[i]=='#') { while(i<len&&s[i]!='\n')i++; continue; }
            if (i < len && s[i]=='/' && i+1<len && s[i+1]=='/') { while(i<len&&s[i]!='\n')i++; continue; }
            { int _sp = co-1;
            if (_sp > _P_pila_indent[_P_nivel_pila]) {
                _P_nivel_pila++; _P_pila_indent[_P_nivel_pila] = _sp;
                _P_tks[_P_ntks].tipo = T_INDENT; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = 0;
                _P_ntks++;
            } else if (_sp < _P_pila_indent[_P_nivel_pila]) {
                while (_P_nivel_pila > 0 && _sp < _P_pila_indent[_P_nivel_pila]) {
                    _P_tks[_P_ntks].tipo = T_DEDENT; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = 0;
                    _P_ntks++; _P_nivel_pila--;
                }
            } }
            continue;
        }
        if (c == '/' && i+1 < len && s[i+1] == '/') {
            while (i < len && s[i] != '\n') i++; continue;
        }
        if (c == '#') {
            while (i < len && s[i] != '\n') i++; continue;
        }
        if (c == '"' || c == '\'') {
            char q = c; int st = i; int scol = co; i++; co++;
            while (i < len && s[i] != q) { i++; co++; }
            if (i >= len) break;
            i++; co++;
            int vl = (i - st - 2) < 255 ? (i - st - 2) : 255;
            strncpy(_P_tks[_P_ntks].val, s + st + 1, vl); _P_tks[_P_ntks].val[vl] = 0;
            _P_tks[_P_ntks].tipo = T_STR; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = scol;
            _P_ntks++; continue;
        }
        if (c >= '0' && c <= '9') {
            int st = i; int scol = co; while (i < len && s[i] >= '0' && s[i] <= '9') i++;
            if (i < len && s[i] == '.') { i++; while (i < len && s[i] >= '0' && s[i] <= '9') i++; }
            int vl = (i - st) < 255 ? (i - st) : 255;
            strncpy(_P_tks[_P_ntks].val, s + st, vl); _P_tks[_P_ntks].val[vl] = 0;
            _P_tks[_P_ntks].tipo = T_NUM; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = scol;
            _P_ntks++; co += (i - st); continue;
        }
        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_') {
            int st = i; int scol = co;
            while (i < len && ((s[i] >= 'a' && s[i] <= 'z') || (s[i] >= 'A' && s[i] <= 'Z') || (s[i] >= '0' && s[i] <= '9') || s[i] == '_')) i++;
            int vl = (i - st) < 255 ? (i - st) : 255;
            strncpy(_P_tks[_P_ntks].val, s + st, vl); _P_tks[_P_ntks].val[vl] = 0;
            _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = scol;
            typedef struct { const char* p; int t; } _KW;
            static const _KW _ks[] = {
                {"si",T_IF},{"if",T_IF},{"se",T_IF},{"wenn",T_IF},
                {"sino",T_ELSE},{"else",T_ELSE},{"sinon",T_ELSE},{"senao",T_ELSE},{"sonst",T_ELSE},{"altrimenti",T_ELSE},
                {"funcion",T_FUNC},{"function",T_FUNC},{"fonction",T_FUNC},{"funcao",T_FUNC},{"funktion",T_FUNC},{"funzione",T_FUNC},
                {"retornar",T_RET},{"return",T_RET},{"retourner",T_RET},{"retornar",T_RET},{"rueckgabe",T_RET},{"restituisci",T_RET},
                {"lanzar",T_SPAWN},{"spawn",T_SPAWN},{"lancer",T_SPAWN},{"lancar",T_SPAWN},{"starten",T_SPAWN},{"lancia",T_SPAWN},
                {"recuperar",T_RECOVER},{"recover",T_RECOVER},{"recuperer",T_RECOVER},{"recuperar",T_RECOVER},{"wiederherstellen",T_RECOVER},{"recupera",T_RECOVER},
                {"escuchar",T_LISTEN},{"listen",T_LISTEN},{"ecouter",T_LISTEN},{"escutar",T_LISTEN},{"hoeren",T_LISTEN},{"ascolta",T_LISTEN},
                {"mientras",T_WHILE},{"while",T_WHILE},{"tantque",T_WHILE},{"enquanto",T_WHILE},{"waehrend",T_WHILE},{"mentre",T_WHILE},
                {"importar",T_IMPORT},{"import",T_IMPORT},{"importer",T_IMPORT},{"importar",T_IMPORT},{"importieren",T_IMPORT},{"importa",T_IMPORT},
                {"romper",T_BREAK},{"break",T_BREAK},{"rompre",T_BREAK},{"parar",T_BREAK},{"abbrechen",T_BREAK},{"interrompi",T_BREAK},
                {"siguiente",T_CONTINUE},{"continue",T_CONTINUE},{"continuer",T_CONTINUE},{"continuar",T_CONTINUE},{"fortsetzen",T_CONTINUE},{"continua",T_CONTINUE},
                {"estructura",T_STRUCT},{"struct",T_STRUCT},{"structure",T_STRUCT},{"estrutura",T_STRUCT},{"struktur",T_STRUCT},{"struttura",T_STRUCT},
                {"y",T_AND},{"and",T_AND},{"et",T_AND},{"e",T_AND},{"und",T_AND},
                {"o",T_OR},{"or",T_OR},{"ou",T_OR},{"oder",T_OR},
                {"no",T_NOT},{"not",T_NOT},{"non",T_NOT},{"nao",T_NOT},{"nicht",T_NOT},
                {"verdadero",T_TRUE},{"true",T_TRUE},{"vrai",T_TRUE},{"verdadeiro",T_TRUE},{"wahr",T_TRUE},{"vero",T_TRUE},
                {"falso",T_FALSE},{"false",T_FALSE},{"faux",T_FALSE},{"falsch",T_FALSE},
                {"inseguro",T_INSEGURO},{"unsafe",T_INSEGURO},
                {"importar_c",T_IMPORTAR_C},{"import_c",T_IMPORTAR_C},{"importer_c",T_IMPORTAR_C},{"importa_c",T_IMPORTAR_C},
                {"externo",T_EXTERNO},{"extern",T_EXTERNO},{"externe",T_EXTERNO},{"esterno",T_EXTERNO},
                {NULL,0}
            };
            int _kt = T_IDENT;
            for (int _ki = 0; _ks[_ki].p; _ki++) {
                if (strcmp(_P_tks[_P_ntks].val, _ks[_ki].p) == 0) { _kt = _ks[_ki].t; break; }
            }
            _P_tks[_P_ntks].tipo = _kt;
            _P_ntks++; co += (i - st); continue;
        }
        if ((unsigned char)c >= 0x80) { i++; continue; }
        if (i+1 < len) {
            if (c == '-' && s[i+1] == '>') {
                _P_tks[_P_ntks].tipo = T_ARROW; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = co;
                _P_ntks++; i+=2; co+=2; continue;
            }
            if (c == '=' && s[i+1] == '=') {
                _P_tks[_P_ntks].tipo = T_EQ; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = co;
                _P_ntks++; i+=2; co+=2; continue;
            }
            if (c == '!' && s[i+1] == '=') {
                _P_tks[_P_ntks].tipo = T_NE; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = co;
                _P_ntks++; i+=2; co+=2; continue;
            }
            if (c == '<' && s[i+1] == '=') {
                _P_tks[_P_ntks].tipo = T_LE; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = co;
                _P_ntks++; i+=2; co+=2; continue;
            }
            if (c == '>' && s[i+1] == '=') {
                _P_tks[_P_ntks].tipo = T_GE; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = co;
                _P_ntks++; i+=2; co+=2; continue;
            }
        }
        {
            int tt = T_EOF;
            if (c == '=') tt = T_ASSIGN;
            else if (c == '+') tt = T_PLUS;
            else if (c == '-') tt = T_MINUS;
            else if (c == '*') tt = T_MUL;
            else if (c == '/') tt = T_DIV;
            else if (c == '%') tt = T_MOD;
            else if (c == '(') tt = T_LPAREN;
            else if (c == ')') tt = T_RPAREN;
            else if (c == ':') tt = T_COLON;
            else if (c == ',') tt = T_COMMA;
            else if (c == '.') tt = T_DOT;
            else if (c == '>') tt = T_GT;
            else if (c == '<') tt = T_LT;
            else if (c == '&') tt = T_AMPERSAND;
            if (tt == T_EOF) { fprintf(stderr,"Error Lexico: caracter inesperado '%%c'(%%d) en linea %%d\n",c,c,li); exit(1); }
            _P_tks[_P_ntks].tipo = tt; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = co;
            _P_ntks++; i++; co++;
        }
    }
    while (_P_nivel_pila > 0) {
        _P_tks[_P_ntks].tipo = T_DEDENT; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = 0;
        _P_ntks++; _P_nivel_pila--;
    }
    _P_tks[_P_ntks].tipo = T_EOF; _P_tks[_P_ntks].linea = li; _P_tks[_P_ntks].col = 0;
    _P_ntks++;
}

static void _P_procesar_indentacion_final() {
    while (_P_nivel_pila > 0) {
        _P_tks[_P_ntks].tipo = T_DEDENT; _P_tks[_P_ntks].linea = _P_tks[_P_ntks-1].linea; _P_tks[_P_ntks].col = 0;
        _P_ntks++; _P_nivel_pila--;
    }
}

// --- AST builder helpers ---
static CadenaSegura _P_cs(const char* s) {
    CadenaSegura c; c.longitud = (int)strlen(s);
    char* d = (char*)malloc(c.longitud + 1); strcpy(d, s); c.datos = d; return c;
}
static struct ListaNodo* _P_mk_list(struct Nodo* h, struct ListaNodo* t) {
    struct ListaNodo* n = (struct ListaNodo*)calloc(1,sizeof(struct ListaNodo));
    n->cabeza = h; n->cola = t; return n;
}

static _P_Token* _P_mirar() { return &_P_tks[_P_tpos]; }
static void _P_avanzar() { if (_P_tpos < _P_ntks) _P_tpos++; }
static int _P_posible(int t) { return _P_mirar()->tipo == t ? 1 : 0; }
static int _P_esperar(int t) {
    if (_P_mirar()->tipo == t) { _P_avanzar(); return 1; }
    fprintf(stderr, "[PARSER] L%d:%d: esperaba token %d, encontre %d\n",
            _P_mirar()->linea, _P_mirar()->col, t, _P_mirar()->tipo);
    exit(1);
}
static void _P_sinc_skip() {
    while (_P_tpos < _P_ntks) {
        int tt = _P_mirar()->tipo;
        if (tt == T_NL || tt == T_DEDENT || tt == T_EOF || tt == T_COMMA || tt == T_RPAREN || tt == T_COLON) break;
        _P_avanzar();
    }
}

// Forward declarations
static struct Nodo* _P_expr();
static struct Nodo* _P_logica();
static struct ListaNodo* _P_bloque();
static struct Nodo* _P_sentencia();
static struct Nodo* _P_comp();
static struct Nodo* _P_suma();
static struct Nodo* _P_term();
static struct Nodo* _P_una();
static struct Nodo* _P_prim();
static struct Programa _P_programa();
static struct ListaNodo* _P_bloque() {
    if (!_P_esperar(T_NL)) { _P_sinc_skip(); return NULL; }
    while (_P_mirar()->tipo == T_NL) { _P_avanzar(); }
    if (!_P_esperar(T_INDENT)) { _P_sinc_skip(); return NULL; }
    struct ListaNodo* lst = NULL;
    struct ListaNodo** cur = &lst;
    while (_P_mirar()->tipo != T_DEDENT && _P_mirar()->tipo != T_EOF) {
        if (_P_mirar()->tipo == T_NL) { _P_avanzar(); continue; }
        struct Nodo* st=_P_sentencia();
        if (st) { *cur=_P_mk_list(st,NULL); cur=&(*cur)->cola; }
    }
    _P_esperar(T_DEDENT);
    return lst;
}
static struct Nodo* _P_sentencia() {
    while (_P_mirar()->tipo == T_NL) { _P_avanzar(); }
    _P_Token* t = _P_mirar();
    if (t->tipo == T_FUNC) {
        _P_avanzar();
        if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); return NULL; }
        char _nm[256]; strncpy(_nm, _P_mirar()->val, sizeof(_nm)-1); _nm[sizeof(_nm)-1] = \'\0\';
        _P_avanzar();
        _P_esperar(T_LPAREN);
        struct ListaNodo* params = NULL;
        struct ListaNodo** pcur = &params;
        if (_P_mirar()->tipo != T_RPAREN) {
            while (1) {
                int is_transfer = 0;
                if (_P_mirar()->tipo == T_ARROW) { is_transfer=1; _P_avanzar(); }
                if (_P_mirar()->tipo != T_IDENT) break;
                char _pn[256]; strncpy(_pn, _P_mirar()->val, sizeof(_pn)-1); _pn[sizeof(_pn)-1] = \'\0\';
                _P_avanzar();
                _P_esperar(T_COLON);
                if (_P_mirar()->tipo != T_IDENT) break;
                char _pt[256]; strncpy(_pt, _P_mirar()->val, sizeof(_pt)-1); _pt[sizeof(_pt)-1] = \'\0\';
                _P_avanzar();
                while (_P_mirar()->tipo == T_MUL) { if ((int)strlen(_pt) < 255) { int _pl = (int)strlen(_pt); _pt[_pl] = '*'; _pt[_pl+1] = '\0'; } _P_avanzar(); }
                struct Parametro* pp = (struct Parametro*)calloc(1,sizeof(struct Parametro));
                pp->tipo=_P_cs("Parametro");
                pp->nombre=_P_cs(_pn); pp->tipo_param=_P_cs(_pt);
                pp->es_transferencia = is_transfer;
                *pcur=_P_mk_list((struct Nodo*)pp,NULL); pcur=&(*pcur)->cola;
                if (_P_mirar()->tipo != T_COMMA) break;
                _P_avanzar();
            }
        }
        _P_esperar(T_RPAREN); _P_esperar(T_ARROW);
        if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); return NULL; }
        char _rt[256]; strcpy(_rt, _P_mirar()->val);
        _P_avanzar();
        _P_esperar(T_COLON);
        struct ListaNodo* body=_P_bloque();
        struct DefinicionFuncion* n = (struct DefinicionFuncion*)calloc(1,sizeof(struct DefinicionFuncion));
        n->tipo=_P_cs("DefinicionFuncion");
        n->nombre=_P_cs(_nm); n->parametros=(struct ListaParametro*)params;
        n->tipo_retorno=_P_cs(_rt); n->cuerpo=body;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_STRUCT) {
        _P_avanzar();
        if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); return NULL; }
        char _snm[256]; strcpy(_snm, _P_mirar()->val);
        _P_avanzar();
        _P_esperar(T_COLON);
        if (!_P_esperar(T_NL)) { _P_sinc_skip(); return NULL; }
        while (_P_mirar()->tipo == T_NL) { _P_avanzar(); }
        if (!_P_esperar(T_INDENT)) { _P_sinc_skip(); return NULL; }
        struct ListaParametro* campos = NULL;
        struct ListaParametro** ccur = &campos;
        while (_P_mirar()->tipo != T_DEDENT && _P_mirar()->tipo != T_EOF) {
            if (_P_mirar()->tipo == T_NL) { _P_avanzar(); continue; }
            if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); break; }
            char _pn[256]; strncpy(_pn, _P_mirar()->val, sizeof(_pn)-1); _pn[sizeof(_pn)-1] = \'\0\';
            _P_avanzar();
            _P_esperar(T_COLON);
            if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); break; }
            char _pt[256]; strncpy(_pt, _P_mirar()->val, sizeof(_pt)-1); _pt[sizeof(_pt)-1] = \'\0\';
            _P_avanzar();
            struct Parametro* pp=(struct Parametro*)calloc(1,sizeof(struct Parametro));
            pp->tipo=_P_cs("Parametro"); pp->nombre=_P_cs(_pn); pp->tipo_param=_P_cs(_pt); pp->es_transferencia=0;
            *ccur=(struct ListaParametro*)_P_mk_list((struct Nodo*)pp,NULL); ccur=&(*ccur)->cola;
        }
        _P_esperar(T_DEDENT);
        struct DefinicionEstructura* n = (struct DefinicionEstructura*)calloc(1,sizeof(struct DefinicionEstructura));
        n->tipo=_P_cs("DefinicionEstructura"); n->nombre=_P_cs(_snm); n->campos=campos;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_IF) {
        _P_avanzar();
        struct Nodo* cond=_P_expr();
        _P_esperar(T_COLON);
        struct ListaNodo* cpo=_P_bloque();
        struct ListaNodo* sino = NULL;
        if (_P_mirar()->tipo == T_ELSE) { _P_avanzar(); _P_esperar(T_COLON); sino=_P_bloque(); }
        struct SentenciaSi* n = (struct SentenciaSi*)calloc(1,sizeof(struct SentenciaSi));
        n->tipo=_P_cs("SentenciaSi"); n->condicion=cond;
        n->cuerpo=cpo; n->cuerpo_sino=sino;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_WHILE) {
        _P_avanzar();
        struct Nodo* cond=_P_expr();
        _P_esperar(T_COLON);
        struct ListaNodo* cpo=_P_bloque();
        struct SentenciaMientras* n = (struct SentenciaMientras*)calloc(1,sizeof(struct SentenciaMientras));
        n->tipo=_P_cs("SentenciaMientras"); n->condicion=cond; n->cuerpo=cpo;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_RET) {
        _P_avanzar();
        struct Nodo* expr = NULL;
        if (_P_mirar()->tipo == T_ARROW) { _P_avanzar(); expr=_P_expr(); }
        else if (_P_mirar()->tipo != T_NL && _P_mirar()->tipo != T_DEDENT && _P_mirar()->tipo != T_EOF) { expr=_P_expr(); }
        struct SentenciaRetornar* n = (struct SentenciaRetornar*)calloc(1,sizeof(struct SentenciaRetornar));
        n->tipo=_P_cs("SentenciaRetornar"); n->expr=expr;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_SPAWN) { _P_avanzar();
        struct Nodo* ll=_P_expr();
        struct SentenciaLanzar* n = (struct SentenciaLanzar*)calloc(1,sizeof(struct SentenciaLanzar));
        n->tipo=_P_cs("SentenciaLanzar"); n->llamada=ll;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_RECOVER) { _P_avanzar();
        struct Nodo* ac=_P_expr(); _P_esperar(T_COLON);
        struct Nodo* pb=_P_expr();
        struct SentenciaRecuperar* n = (struct SentenciaRecuperar*)calloc(1,sizeof(struct SentenciaRecuperar));
        n->tipo=_P_cs("SentenciaRecuperar"); n->accion_critica=ac; n->plan_b=pb;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_LISTEN) { _P_avanzar();
        struct Nodo* cn=_P_expr(); _P_esperar(T_ARROW);
        struct Nodo* rp=_P_expr();
        struct SentenciaEscuchar* n = (struct SentenciaEscuchar*)calloc(1,sizeof(struct SentenciaEscuchar));
        n->tipo=_P_cs("SentenciaEscuchar"); n->canal=cn; n->respuesta=rp;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_BREAK) { _P_avanzar();
        struct SentenciaRomper* n = (struct SentenciaRomper*)calloc(1,sizeof(struct SentenciaRomper));
        n->tipo=_P_cs("SentenciaRomper");
        return (struct Nodo*)n;
    }
    if (t->tipo == T_CONTINUE) { _P_avanzar();
        struct SentenciaSiguiente* n = (struct SentenciaSiguiente*)calloc(1,sizeof(struct SentenciaSiguiente));
        n->tipo=_P_cs("SentenciaSiguiente");
        return (struct Nodo*)n;
    }
    if (t->tipo == T_IMPORT) { _P_avanzar();
        if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); return NULL; }
        char _imp[256]; strncpy(_imp, _P_mirar()->val, sizeof(_imp)-1); _imp[sizeof(_imp)-1] = \'\0\'; int _iml = (int)strlen(_imp);
        _P_avanzar();
        while (_P_mirar()->tipo == T_DOT) { _P_avanzar(); if (_P_mirar()->tipo != T_IDENT) break; { int _il = (int)strlen(_imp); if (_il < 254) { _imp[_il] = '.'; _imp[_il+1] = '\0'; } if ((int)strlen(_imp) + (int)strlen(_P_mirar()->val) < 255) { strncat(_imp, _P_mirar()->val, 255 - (int)strlen(_imp) - 1); } } _P_avanzar(); }
        struct SentenciaImportar* n = (struct SentenciaImportar*)calloc(1,sizeof(struct SentenciaImportar));
        n->tipo=_P_cs("SentenciaImportar"); n->ruta=_P_cs(_imp);
        return (struct Nodo*)n;
    }
    if (t->tipo == T_IMPORTAR_C) { _P_avanzar();
        if (_P_mirar()->tipo != T_STR) { _P_sinc_skip(); return NULL; }
        char _hc[256]; strcpy(_hc, _P_mirar()->val);
        int _hsys = (_hc[0]=='<' && _hc[strlen(_hc)-1]=='>');
        if(_hsys){{ memmove(_hc,_hc+1,strlen(_hc)-2); _hc[strlen(_hc)-2]=0; }}
        _P_avanzar();
        struct ImportarC* n = (struct ImportarC*)calloc(1,sizeof(struct ImportarC));
        n->tipo=_P_cs("ImportarC"); n->ruta=_P_cs(_hc); n->es_sistema=_hsys;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_EXTERNO) { _P_avanzar();
        if (_P_mirar()->tipo != T_FUNC) { _P_sinc_skip(); return NULL; }
        _P_avanzar();
        if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); return NULL; }
        char _enm[256]; strcpy(_enm, _P_mirar()->val);
        _P_avanzar();
        _P_esperar(T_LPAREN);
        struct ListaParametro* eparams = NULL;
        struct ListaParametro** epcur = &eparams;
        if (_P_mirar()->tipo != T_RPAREN) {
            while (1) {
                if (_P_mirar()->tipo != T_IDENT) break;
                char _epn[256]; strcpy(_epn, _P_mirar()->val);
                _P_avanzar();
                _P_esperar(T_COLON);
                if (_P_mirar()->tipo != T_IDENT) break;
                char _ept[256]; strcpy(_ept, _P_mirar()->val);
                _P_avanzar();
                while (_P_mirar()->tipo == T_MUL) { strcat(_ept,"*"); _P_avanzar(); }
                struct Parametro* epp=(struct Parametro*)calloc(1,sizeof(struct Parametro));
                epp->tipo=_P_cs("Parametro"); epp->nombre=_P_cs(_epn); epp->tipo_param=_P_cs(_ept); epp->es_transferencia=0;
                *epcur=(struct ListaParametro*)_P_mk_list((struct Nodo*)epp,NULL); epcur=&(*epcur)->cola;
                if (_P_mirar()->tipo != T_COMMA) break;
                _P_avanzar();
            }
        }
        _P_esperar(T_RPAREN); _P_esperar(T_ARROW);
        if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); return NULL; }
        char _ert[256]; strcpy(_ert, _P_mirar()->val);
        _P_avanzar();
        struct DeclaracionExterna* n = (struct DeclaracionExterna*)calloc(1,sizeof(struct DeclaracionExterna));
        n->tipo=_P_cs("DeclaracionExterna"); n->nombre=_P_cs(_enm);
        n->parametros=eparams; n->tipo_retorno=_P_cs(_ert);
        return (struct Nodo*)n;
    }
    if (t->tipo == T_INSEGURO) { _P_avanzar();
        _P_esperar(T_COLON);
        struct ListaNodo* cpo=_P_bloque();
        struct BloqueInseguro* n = (struct BloqueInseguro*)calloc(1,sizeof(struct BloqueInseguro));
        n->tipo=_P_cs("BloqueInseguro"); n->cuerpo=cpo;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_IDENT && _P_tpos + 1 < _P_ntks && _P_tks[_P_tpos + 1].tipo == T_ASSIGN) {
        char _vn[256]; strcpy(_vn, t->val);
        _P_avanzar(); _P_avanzar();
        struct Nodo* val=_P_expr();
        struct AsignacionVariable* n = (struct AsignacionVariable*)calloc(1,sizeof(struct AsignacionVariable));
        n->tipo=_P_cs("AsignacionVariable");
        n->nombre=_P_cs(_vn); n->expresion=val;
        return (struct Nodo*)n;
    }
    { struct Nodo* e=_P_expr();
        if (e && _P_mirar()->tipo == T_ASSIGN) {
            _P_avanzar();
            struct Nodo* val=_P_expr();
            if (strcmp(e->tipo.datos,"Identificador")==0) {
                struct AsignacionVariable* n = (struct AsignacionVariable*)calloc(1,sizeof(struct AsignacionVariable));
                n->tipo=_P_cs("AsignacionVariable");
                n->nombre=((struct Identificador*)e)->nombre; n->expresion=val;
                return (struct Nodo*)n;
            }
            if (strcmp(e->tipo.datos,"ExprAccesoCampo")==0) {
                struct AsignacionCampo* n = (struct AsignacionCampo*)calloc(1,sizeof(struct AsignacionCampo));
                n->tipo=_P_cs("AsignacionCampo");
                n->objeto=((struct ExprAccesoCampo*)e)->objeto; n->nombre_campo=((struct ExprAccesoCampo*)e)->nombre_campo; n->expresion=val;
                return (struct Nodo*)n;
            }
        }
        struct SentenciaExpr* n = (struct SentenciaExpr*)calloc(1,sizeof(struct SentenciaExpr));
        n->tipo=_P_cs("SentenciaExpr"); n->expr=e;
        return (struct Nodo*)n;
    }
}
static struct Nodo* _P_expr() { return _P_logica(); }

static struct Nodo* _P_logica() {
    struct Nodo* izq=_P_comp();
    while (1) {
        int tt=_P_mirar()->tipo;
        if (tt!=T_AND&&tt!=T_OR) break;
        _P_avanzar();
        struct Nodo* der=_P_comp();
        struct OpBinaria* n=(struct OpBinaria*)calloc(1,sizeof(struct OpBinaria));
        n->tipo=_P_cs("OpBinaria"); n->izquierdo=izq; n->derecho=der;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=_P_cs(tt==T_AND?"&&":"||");
        izq=(struct Nodo*)n;
    }
    return izq;
}

static struct Nodo* _P_comp() {
    struct Nodo* izq=_P_suma();
    while (1) {
        int tt=_P_mirar()->tipo;
        if (tt!=T_EQ&&tt!=T_NE&&tt!=T_LT&&tt!=T_GT&&tt!=T_LE&&tt!=T_GE) break;
        _P_avanzar();
        struct Nodo* der=_P_suma();
        struct OpBinaria* n=(struct OpBinaria*)calloc(1,sizeof(struct OpBinaria));
        n->tipo=_P_cs("OpBinaria"); n->izquierdo=izq; n->derecho=der;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        {char _b[4]={0,0,0,0};if(tt==T_EQ){_b[0]='=';_b[1]='=';}
        else if(tt==T_NE){_b[0]='!';_b[1]='=';}
        else if(tt==T_LE){_b[0]='<';_b[1]='=';}
        else if(tt==T_GE){_b[0]='>';_b[1]='=';}
        else if(tt==T_LT){_b[0]='<';}else{_b[0]='>';}
        n->operador->lexema=_P_cs(_b);}
        izq=(struct Nodo*)n;
    }
    return izq;
}
static struct Nodo* _P_suma() {
    struct Nodo* izq=_P_term();
    while (_P_mirar()->tipo==T_PLUS||_P_mirar()->tipo==T_MINUS) {
        int tt=_P_mirar()->tipo; _P_avanzar();
        struct Nodo* der=_P_term();
        struct OpBinaria* n=(struct OpBinaria*)calloc(1,sizeof(struct OpBinaria));
        n->tipo=_P_cs("OpBinaria"); n->izquierdo=izq; n->derecho=der;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=_P_cs(tt==T_PLUS?"+":"-");
        izq=(struct Nodo*)n;
    }
    return izq;
}
static struct Nodo* _P_term() {
    struct Nodo* izq=_P_una();
    while (_P_mirar()->tipo==T_MUL||_P_mirar()->tipo==T_DIV||_P_mirar()->tipo==T_MOD) {
        int tt=_P_mirar()->tipo; _P_avanzar();
        struct Nodo* der=_P_una();
        struct OpBinaria* n=(struct OpBinaria*)calloc(1,sizeof(struct OpBinaria));
        n->tipo=_P_cs("OpBinaria"); n->izquierdo=izq; n->derecho=der;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=_P_cs(tt==T_MUL?"*":tt==T_DIV?"/":"%");
        izq=(struct Nodo*)n;
    }
    return izq;
}
static struct Nodo* _P_una() {
    if (_P_mirar()->tipo==T_MINUS||_P_mirar()->tipo==T_PLUS) {
        int tt=_P_mirar()->tipo; _P_avanzar();
        struct Nodo* e=_P_una();
        struct OpUnaria* n=(struct OpUnaria*)calloc(1,sizeof(struct OpUnaria));
        n->tipo=_P_cs("OpUnaria"); n->expr=e;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=_P_cs(tt==T_PLUS?"+":"-");
        return (struct Nodo*)n;
    }
    if (_P_mirar()->tipo==T_NOT) {
        int tt=_P_mirar()->tipo; _P_avanzar();
        struct Nodo* e=_P_una();
        struct OpUnaria* n=(struct OpUnaria*)calloc(1,sizeof(struct OpUnaria));
        n->tipo=_P_cs("OpUnaria"); n->expr=e;
        n->operador=(struct Token*)calloc(1,sizeof(struct Token)); n->operador->tipo=tt; n->operador->linea=0; n->operador->columna=0;
        n->operador->lexema=_P_cs("!");
        return (struct Nodo*)n;
    }
    if (_P_mirar()->tipo==T_AMPERSAND) {
        _P_avanzar();
        struct Nodo* e=_P_una();
        struct ExprObtenerDireccion* n=(struct ExprObtenerDireccion*)calloc(1,sizeof(struct ExprObtenerDireccion));
        n->tipo=_P_cs("ExprObtenerDireccion"); n->expr=e;
        return (struct Nodo*)n;
    }
    if (_P_mirar()->tipo==T_MUL) {
        _P_avanzar();
        struct Nodo* e=_P_una();
        struct ExprDereferencia* n=(struct ExprDereferencia*)calloc(1,sizeof(struct ExprDereferencia));
        n->tipo=_P_cs("ExprDereferencia"); n->expr=e;
        return (struct Nodo*)n;
    }
    return _P_prim();
}
static struct Nodo* _P_prim() {
    _P_Token* t=_P_mirar();
    if (t->tipo==T_NUM) {
        struct LiteralNumero* n=(struct LiteralNumero*)calloc(1,sizeof(struct LiteralNumero));
        n->tipo=_P_cs("LiteralNumero"); n->valor=atoi(t->val);
        _P_avanzar(); return (struct Nodo*)n;
    }
    if (t->tipo==T_STR) {
        struct LiteralCadena* n=(struct LiteralCadena*)calloc(1,sizeof(struct LiteralCadena));
        n->tipo=_P_cs("LiteralCadena"); n->valor=_P_cs(t->val);
        _P_avanzar(); return (struct Nodo*)n;
    }
    if (t->tipo==T_TRUE) {
        _P_avanzar();
        struct LiteralNumero* n=(struct LiteralNumero*)calloc(1,sizeof(struct LiteralNumero));
        n->tipo=_P_cs("LiteralNumero"); n->valor=1;
        return (struct Nodo*)n;
    }
    if (t->tipo==T_FALSE) {
        _P_avanzar();
        struct LiteralNumero* n=(struct LiteralNumero*)calloc(1,sizeof(struct LiteralNumero));
        n->tipo=_P_cs("LiteralNumero"); n->valor=0;
        return (struct Nodo*)n;
    }
    if (t->tipo==T_IDENT) {
        char _nm[256]; strncpy(_nm, t->val, sizeof(_nm)-1); _nm[sizeof(_nm)-1] = \'\0\';
        _P_avanzar();
        if (_P_mirar()->tipo==T_LPAREN) {
            _P_avanzar();
            struct ListaNodo* args=NULL; struct ListaNodo** acur=&args;
            if (_P_mirar()->tipo!=T_RPAREN) {
                while (1) {
                    if (_P_mirar()->tipo==T_ARROW) {
                        _P_avanzar();
                        struct Nodo* ae=_P_expr();
                        struct ArgumentoTransferido* at=(struct ArgumentoTransferido*)calloc(1,sizeof(struct ArgumentoTransferido));
                        at->tipo=_P_cs("ArgumentoTransferido"); at->expr=ae;
                        *acur=_P_mk_list((struct Nodo*)at,NULL);
                    } else { *acur=_P_mk_list(_P_expr(),NULL); }
                    acur=&(*acur)->cola;
                    if (_P_mirar()->tipo!=T_COMMA) break;
                    _P_avanzar();
                }
            }
            _P_esperar(T_RPAREN);
            if(strcmp(_nm,"log")==0) {
                struct LogLlamada* n=(struct LogLlamada*)calloc(1,sizeof(struct LogLlamada));
                n->tipo=_P_cs("LogLlamada"); n->argumentos=args;
                return (struct Nodo*)n;
            }
            struct LlamadaFuncion* n=(struct LlamadaFuncion*)calloc(1,sizeof(struct LlamadaFuncion));
            n->tipo=_P_cs("LlamadaFuncion"); n->nombre=_P_cs(_nm); n->argumentos=args;
            return (struct Nodo*)n;
        }
        if (_P_mirar()->tipo==T_DOT) {
            /* Build chain: a.b.c -> ExprAccesoCampo(ExprAccesoCampo(Ident("a"), "b"), "c") */
            struct Nodo* prev=(struct Nodo*)NULL;
            while (_P_mirar()->tipo==T_DOT) {
                _P_avanzar();
                if (_P_mirar()->tipo!=T_IDENT) break;
                if (!prev) {
                    struct Identificador* obj=(struct Identificador*)calloc(1,sizeof(struct Identificador));
                    obj->tipo=_P_cs("Identificador"); obj->nombre=_P_cs(_nm);
                    prev=(struct Nodo*)obj;
                }
                strncpy(_nm, _P_mirar()->val, sizeof(_nm)-1); _nm[sizeof(_nm)-1] = \'\0\'; _P_avanzar();
                if (_P_mirar()->tipo==T_LPAREN && _P_tpos + 1 < _P_ntks && _P_tks[_P_tpos + 1].tipo!=T_DOT) {
                    /* method call on last segment */
                    if(prev) free(prev);
                    _P_avanzar();
                    struct ListaNodo* args=NULL; struct ListaNodo** acur=&args;
                    if (_P_mirar()->tipo!=T_RPAREN) {
                        while (1) {
                            if (_P_mirar()->tipo==T_ARROW) {
                                _P_avanzar();
                                struct Nodo* ae=_P_expr();
                                struct ArgumentoTransferido* at=(struct ArgumentoTransferido*)calloc(1,sizeof(struct ArgumentoTransferido));
                                at->tipo=_P_cs("ArgumentoTransferido"); at->expr=ae;
                                *acur=_P_mk_list((struct Nodo*)at,NULL);
                            } else { *acur=_P_mk_list(_P_expr(),NULL); }
                            acur=&(*acur)->cola;
                            if (_P_mirar()->tipo!=T_COMMA) break;
                            _P_avanzar();
                        }
                    }
                    _P_esperar(T_RPAREN);
                    struct LlamadaFuncion* n=(struct LlamadaFuncion*)calloc(1,sizeof(struct LlamadaFuncion));
                    n->tipo=_P_cs("LlamadaFuncion"); n->nombre=_P_cs(_nm); n->argumentos=args;
                    return (struct Nodo*)n;
                }
                struct ExprAccesoCampo* ac=(struct ExprAccesoCampo*)calloc(1,sizeof(struct ExprAccesoCampo));
                ac->tipo=_P_cs("ExprAccesoCampo"); ac->objeto=prev; ac->nombre_campo=_P_cs(_nm);
                prev=(struct Nodo*)ac;
                if (_P_mirar()->tipo!=T_DOT) break;
            }
            return prev;
        }
        struct Identificador* n=(struct Identificador*)calloc(1,sizeof(struct Identificador));
        n->tipo=_P_cs("Identificador"); n->nombre=_P_cs(_nm);
        return (struct Nodo*)n;
    }
    if (t->tipo==T_LPAREN) { _P_avanzar(); struct Nodo* e=_P_expr(); _P_esperar(T_RPAREN); return e; }
    fprintf(stderr,"[PARSER] L%d:%d: expresion inesperada token=%d\n",t->linea,t->col,t->tipo);
    exit(1);
}
static struct Programa _P_programa() {
    struct ListaNodo* lst=NULL; struct ListaNodo** cur=&lst;
    while (_P_mirar()->tipo!=T_EOF) {
        if (_P_mirar()->tipo==T_NL||_P_mirar()->tipo==T_DEDENT) { _P_avanzar(); continue; }
        struct Nodo* st=_P_sentencia();
        if (st) { *cur=_P_mk_list(st,NULL); cur=&(*cur)->cola; }
    }
    struct Programa p; memset(&p,0,sizeof(p));
    p.tipo=_P_cs("Programa"); p.sentencias=lst;
    return p;
}
struct Programa parsear(CadenaSegura fuente) {
    _P_ntks = 0; _P_tpos = 0; _P_p_err = 0; _P_nivel_pila = 0;
    _P_pila_indent[0] = 0;
    _P_tokenizar(fuente.datos, fuente.longitud);
    _P_procesar_indentacion_final();
    struct Programa _prog = _P_programa();
    return _prog;
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    synapse_esperar_hilos();
    return 0;
}