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

struct SemNodo;
struct SemSimbolo;
struct SemTablaSimbolos;
struct SemEstructuraInfo;
struct AnalizadorSemanticoEst;

void sem_error(struct AnalizadorSemanticoEst est, int codigo, int idx_nodo, CadenaSegura mensaje);
int tabla_declarar(struct AnalizadorSemanticoEst est, CadenaSegura nombre, CadenaSegura tipo, int idx_nodo, int es_constante);
int tabla_buscar(struct AnalizadorSemanticoEst est, CadenaSegura nombre);
void tabla_entrar_scope(struct AnalizadorSemanticoEst est);
void tabla_salir_scope(struct AnalizadorSemanticoEst est);
void tabla_marcar_movido(struct AnalizadorSemanticoEst est, CadenaSegura nombre);
int tabla_esta_movido(struct AnalizadorSemanticoEst est, CadenaSegura nombre);
CadenaSegura tipo_normalizado(CadenaSegura tipo);
int es_builtin(CadenaSegura nombre);
int builtin_cantidad_args(CadenaSegura nombre);
CadenaSegura builtin_tipo_retorno(CadenaSegura nombre);
CadenaSegura builtin_tipo_parametro(CadenaSegura nombre, int idx);
int nodo_tipo(struct AnalizadorSemanticoEst est, int idx);
int nodo_linea(struct AnalizadorSemanticoEst est, int idx);
int nodo_hijo_izq(struct AnalizadorSemanticoEst est, int idx);
int nodo_hijo_der(struct AnalizadorSemanticoEst est, int idx);
int nodo_hermano(struct AnalizadorSemanticoEst est, int idx);
void registrar_estructura(struct AnalizadorSemanticoEst est, CadenaSegura nombre, int idx_nodo);
int parsear_patron_coincidir(CadenaSegura patron, CadenaSegura tag_nombre, CadenaSegura var_nombre);
void analizar_sentencia(struct AnalizadorSemanticoEst est, int idx_nodo);
void analizar_paso_estructuras(struct AnalizadorSemanticoEst est, int idx_programa);
void analizar_paso_funciones(struct AnalizadorSemanticoEst est, int idx_programa);
void analizar_paso_cuerpos(struct AnalizadorSemanticoEst est, int idx_programa);
void analizar(struct AnalizadorSemanticoEst est);
struct AnalizadorSemanticoEst analizador_nuevo(struct SemNodo nodos, int total);

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
#define ERR_SEM_VAR_NO_DECLARADA (14)
#define ERR_SEM_TIPO_INCOMPATIBLE (15)
#define ERR_SEM_TIPO_RETORNO (16)
#define ERR_SEM_FUNC_NO_DEFINIDA (17)
#define ERR_SEM_REDEFINICION (18)
#define ERR_SEM_ARGUMENTOS_INVALIDOS (19)
#define ERR_SEM_ESTRUCTURA_NO_DEFINIDA (20)
#define ERR_SEM_CAMPO_NO_EXISTE (21)
#define ERR_SEM_VAR_MOVIDA (22)
#define ERR_SEM_ASM_FUERA_INSEGURO (31)
#define ERR_SEM_CONSTANTE_INMUTABLE (32)
#define PROPIEDAD_VIVO (1)
#define PROPIEDAD_MOVIDO (2)
typedef struct SemNodo {
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
} SemNodo;

static inline struct SemNodo SemNodo_nuevo() {
    struct SemNodo _r = {0};
    return _r;
}

typedef struct SemSimbolo {
    CadenaSegura nombre;
    CadenaSegura tipo;
    int nivel_ambito;
    int propiedad;
    int es_constante;
    int linea;
    int columna;
} SemSimbolo;

static inline struct SemSimbolo SemSimbolo_nuevo() {
    struct SemSimbolo _r = {0};
    return _r;
}

typedef struct SemTablaSimbolos {
    struct SemSimbolo* entradas;
    int total_entradas;
    int nivel_actual;
} SemTablaSimbolos;

static inline struct SemTablaSimbolos SemTablaSimbolos_nuevo() {
    struct SemTablaSimbolos _r = {0};
    return _r;
}

typedef struct SemEstructuraInfo {
    CadenaSegura nombre;
    CadenaSegura campos_nombre;
    CadenaSegura campos_tipo;
    int total_campos;
} SemEstructuraInfo;

static inline struct SemEstructuraInfo SemEstructuraInfo_nuevo() {
    struct SemEstructuraInfo _r = {0};
    return _r;
}

typedef struct AnalizadorSemanticoEst {
    struct SemNodo* nodos;
    int total_nodos;
    struct SemTablaSimbolos* tabla;
    CadenaSegura func_retorno;
    CadenaSegura func_actual;
    int en_coincidir;
    int dentro_de_inseguro;
    int hay_error;
    struct SemEstructuraInfo* info_estructuras;
    int total_estructuras;
    CadenaSegura asignaciones_campos_var;
    CadenaSegura asignaciones_campos_campo;
    CadenaSegura asignaciones_campos_tipo;
    int total_asignaciones;
} AnalizadorSemanticoEst;

static inline struct AnalizadorSemanticoEst AnalizadorSemanticoEst_nuevo() {
    struct AnalizadorSemanticoEst _r = {0};
    return _r;
}

void sem_error(struct AnalizadorSemanticoEst est, int codigo, int idx_nodo, CadenaSegura mensaje) {
    int linea = 0;
    int columna = 0;
    { /* unsafe */
        linea = (idx_nodo >= 0 && idx_nodo < est.total_nodos) ? est.nodos[idx_nodo].linea : 0;
        columna = (idx_nodo >= 0 && idx_nodo < est.total_nodos) ? est.nodos[idx_nodo].columna : 0;
    }
    est.hay_error = 1;
    { /* unsafe */
        // sem_error: reportado;
    }
}

int tabla_declarar(struct AnalizadorSemanticoEst est, CadenaSegura nombre, CadenaSegura tipo, int idx_nodo, int es_constante) {
    int linea = 0;
    int columna = 0;
    { /* unsafe */
        linea = (idx_nodo >= 0) ? est.nodos[idx_nodo].linea : 0;
        columna = (idx_nodo >= 0) ? est.nodos[idx_nodo].columna : 0;
    }
    int i = 0;
    int encontrado = 0;
    int r = 1;
    while ((r == 1)) {
        { /* unsafe */
            r = (i < est.tabla.total_entradas) ? 1 : 0;
            if ((r == 0)) {
                break;
            }
            if (est.tabla.entradas[i].nivel_ambito == est.tabla.nivel_actual) {;
                int _eq = 1;;
                for (int _si = 0; _si < 256; _si++) { if (((const char*)nombre)[_si] != ((const char*)est.tabla.entradas[i].nombre)[_si]) { _eq = 0; break; } if (((const char*)nombre)[_si] == 0) break; };
                if (_eq) { encontrado = 1; };
            };
            i = i + 1;
        }
    }
    if ((encontrado == 1)) {
        int _ret_151 = 0;
        return _ret_151;
    }
    { /* unsafe */
        est.tabla.entradas[est.tabla.total_entradas].nombre = nombre;
        est.tabla.entradas[est.tabla.total_entradas].tipo = tipo;
        est.tabla.entradas[est.tabla.total_entradas].nivel_ambito = est.tabla.nivel_actual;
        est.tabla.entradas[est.tabla.total_entradas].propiedad = 1;
        est.tabla.entradas[est.tabla.total_entradas].es_constante = es_constante;
        est.tabla.entradas[est.tabla.total_entradas].linea = linea;
        est.tabla.entradas[est.tabla.total_entradas].columna = columna;
        est.tabla.total_entradas = est.tabla.total_entradas + 1;
    }
    int _ret_162 = 1;
    return _ret_162;
}

int tabla_buscar(struct AnalizadorSemanticoEst est, CadenaSegura nombre) {
    int i = 0;
    int r = 1;
    while ((r == 1)) {
        { /* unsafe */
            r = (i < est.tabla.total_entradas) ? 1 : 0;
            if ((r == 0)) {
                break;
            }
            int _eq = 1;;
            for (int _si = 0; _si < 256; _si++) {;
                char _a = ((const char*)nombre)[_si];;
                char _b = ((const char*)est.tabla.entradas[i].nombre)[_si];;
                if (_a != _b) { _eq = 0; break; };
                if (_a == 0) break;;
            };
            if (_eq) { return i };
            i = i + 1;
        }
    }
    int _ret_181 = (-1);
    return _ret_181;
}

void tabla_entrar_scope(struct AnalizadorSemanticoEst est) {
    { /* unsafe */
        est.tabla.nivel_actual = est.tabla.nivel_actual + 1;
    }
}

void tabla_salir_scope(struct AnalizadorSemanticoEst est) {
    { /* unsafe */
        while (est.tabla.total_entradas > 0) {;
            if (est.tabla.entradas[est.tabla.total_entradas - 1].nivel_ambito < est.tabla.nivel_actual) break;;
            est.tabla.total_entradas = est.tabla.total_entradas - 1;;
        };
        est.tabla.nivel_actual = est.tabla.nivel_actual - 1;
    }
}

void tabla_marcar_movido(struct AnalizadorSemanticoEst est, CadenaSegura nombre) {
    int idx = tabla_buscar(est, nombre);
    if ((idx >= 0)) {
        { /* unsafe */
            est.tabla.entradas[idx].propiedad = 2;
        }
    }
}

int tabla_esta_movido(struct AnalizadorSemanticoEst est, CadenaSegura nombre) {
    int idx = tabla_buscar(est, nombre);
    if ((idx >= 0)) {
        int r = 0;
        { /* unsafe */
            r = (est.tabla.entradas[idx].propiedad == 2) ? 1 : 0;
        }
        if ((r == 1)) {
            int _ret_208 = 1;
            return _ret_208;
        }
    }
    int _ret_209 = 0;
    return _ret_209;
}

CadenaSegura tipo_normalizado(CadenaSegura tipo) {
    { /* unsafe */
        if (strcmp(tipo.datos, "entero") == 0) { return "int" };
        if (strcmp(tipo.datos, "int") == 0) { return "int" };
        if (strcmp(tipo.datos, "decimal") == 0) { return "decimal" };
        if (strcmp(tipo.datos, "real") == 0) { return "decimal" };
        if (strcmp(tipo.datos, "flotante") == 0) { return "decimal" };
        if (strcmp(tipo.datos, "booleano") == 0) { return "booleano" };
        if (strcmp(tipo.datos, "logico") == 0) { return "booleano" };
        if (strcmp(tipo.datos, "texto") == 0) { return "texto" };
        if (strcmp(tipo.datos, "cadena") == 0) { return "texto" };
        if (strcmp(tipo.datos, "nulo") == 0) { return "nulo" };
        if (strcmp(tipo.datos, "vacio") == 0) { return "nulo" };
        if (strcmp(tipo.datos, "tensor") == 0) { return "tensor" };
        if (strcmp(tipo.datos, "CanalConcurrencia*") == 0) { return "CanalConcurrencia*" };
    }
    CadenaSegura _ret_227 = tipo;
    return _ret_227;
}

int es_builtin(CadenaSegura nombre) {
    { /* unsafe */
        if (strcmp(nombre.datos, "reserva") == 0) { return 1 };
        if (strcmp(nombre.datos, "libera") == 0) { return 1 };
        if (strcmp(nombre.datos, "crear_tensor") == 0) { return 1 };
        if (strcmp(nombre.datos, "suma_tensor") == 0) { return 1 };
        if (strcmp(nombre.datos, "producto_punto") == 0) { return 1 };
        if (strcmp(nombre.datos, "abrir") == 0) { return 1 };
        if (strcmp(nombre.datos, "leer") == 0) { return 1 };
        if (strcmp(nombre.datos, "escribir") == 0) { return 1 };
        if (strcmp(nombre.datos, "escribir_linea") == 0) { return 1 };
        if (strcmp(nombre.datos, "leer_linea") == 0) { return 1 };
        if (strcmp(nombre.datos, "cerrar") == 0) { return 1 };
        if (strcmp(nombre.datos, "suma") == 0) { return 1 };
        if (strcmp(nombre.datos, "producto") == 0) { return 1 };
        if (strcmp(nombre.datos, "relu") == 0) { return 1 };
        if (strcmp(nombre.datos, "tokenizar") == 0) { return 1 };
        if (strcmp(nombre.datos, "parsear") == 0) { return 1 };
        if (strcmp(nombre.datos, "generar") == 0) { return 1 };
        if (strcmp(nombre.datos, "_argc") == 0) { return 1 };
        if (strcmp(nombre.datos, "_argv") == 0) { return 1 };
        if (strcmp(nombre.datos, "salir") == 0) { return 1 };
        if (strcmp(nombre.datos, "concat") == 0) { return 1 };
        if (strcmp(nombre.datos, "texto_a_entero") == 0) { return 1 };
        if (strcmp(nombre.datos, "texto_a_decimal") == 0) { return 1 };
        if (strcmp(nombre.datos, "entero_a_texto") == 0) { return 1 };
        if (strcmp(nombre.datos, "decimal_a_texto") == 0) { return 1 };
        if (strcmp(nombre.datos, "volcar_ast") == 0) { return 1 };
        if (strcmp(nombre.datos, "canal_crear") == 0) { return 1 };
        if (strcmp(nombre.datos, "canal_enviar") == 0) { return 1 };
        if (strcmp(nombre.datos, "canal_recibir") == 0) { return 1 };
        if (strcmp(nombre.datos, "cerrar_canal") == 0) { return 1 };
    }
    int _ret_262 = 0;
    return _ret_262;
}

int builtin_cantidad_args(CadenaSegura nombre) {
    { /* unsafe */
        if (strcmp(nombre.datos, "reserva") == 0) { return 1 };
        if (strcmp(nombre.datos, "libera") == 0) { return 1 };
        if (strcmp(nombre.datos, "crear_tensor") == 0) { return 2 };
        if (strcmp(nombre.datos, "suma_tensor") == 0) { return 2 };
        if (strcmp(nombre.datos, "producto_punto") == 0) { return 2 };
        if (strcmp(nombre.datos, "abrir") == 0) { return 2 };
        if (strcmp(nombre.datos, "leer") == 0) { return 1 };
        if (strcmp(nombre.datos, "escribir") == 0) { return 1 };
        if (strcmp(nombre.datos, "escribir_linea") == 0) { return 1 };
        if (strcmp(nombre.datos, "leer_linea") == 0) { return 0 };
        if (strcmp(nombre.datos, "cerrar") == 0) { return 1 };
        if (strcmp(nombre.datos, "suma") == 0) { return 2 };
        if (strcmp(nombre.datos, "producto") == 0) { return 2 };
        if (strcmp(nombre.datos, "relu") == 0) { return 1 };
        if (strcmp(nombre.datos, "tokenizar") == 0) { return 1 };
        if (strcmp(nombre.datos, "parsear") == 0) { return 1 };
        if (strcmp(nombre.datos, "generar") == 0) { return 2 };
        if (strcmp(nombre.datos, "_argc") == 0) { return 0 };
        if (strcmp(nombre.datos, "_argv") == 0) { return 1 };
        if (strcmp(nombre.datos, "salir") == 0) { return 1 };
        if (strcmp(nombre.datos, "concat") == 0) { return 2 };
        if (strcmp(nombre.datos, "texto_a_entero") == 0) { return 1 };
        if (strcmp(nombre.datos, "texto_a_decimal") == 0) { return 1 };
        if (strcmp(nombre.datos, "entero_a_texto") == 0) { return 1 };
        if (strcmp(nombre.datos, "decimal_a_texto") == 0) { return 1 };
        if (strcmp(nombre.datos, "volcar_ast") == 0) { return 2 };
        if (strcmp(nombre.datos, "canal_crear") == 0) { return 1 };
        if (strcmp(nombre.datos, "canal_enviar") == 0) { return 2 };
        if (strcmp(nombre.datos, "canal_recibir") == 0) { return 1 };
        if (strcmp(nombre.datos, "cerrar_canal") == 0) { return 1 };
    }
    int _ret_296 = 0;
    return _ret_296;
}

CadenaSegura builtin_tipo_retorno(CadenaSegura nombre) {
    { /* unsafe */
        if (strcmp(nombre.datos, "reserva") == 0) { return "tensor" };
        if (strcmp(nombre.datos, "libera") == 0) { return "nulo" };
        if (strcmp(nombre.datos, "crear_tensor") == 0) { return "tensor" };
        if (strcmp(nombre.datos, "suma_tensor") == 0) { return "tensor" };
        if (strcmp(nombre.datos, "producto_punto") == 0) { return "tensor" };
        if (strcmp(nombre.datos, "abrir") == 0) { return "Canal" };
        if (strcmp(nombre.datos, "leer") == 0) { return "texto" };
        if (strcmp(nombre.datos, "escribir") == 0) { return "nulo" };
        if (strcmp(nombre.datos, "escribir_linea") == 0) { return "nulo" };
        if (strcmp(nombre.datos, "leer_linea") == 0) { return "texto" };
        if (strcmp(nombre.datos, "cerrar") == 0) { return "nulo" };
        if (strcmp(nombre.datos, "suma") == 0) { return "tensor" };
        if (strcmp(nombre.datos, "producto") == 0) { return "tensor" };
        if (strcmp(nombre.datos, "relu") == 0) { return "tensor" };
        if (strcmp(nombre.datos, "tokenizar") == 0) { return "int" };
        if (strcmp(nombre.datos, "parsear") == 0) { return "Programa" };
        if (strcmp(nombre.datos, "generar") == 0) { return "int" };
        if (strcmp(nombre.datos, "_argc") == 0) { return "int" };
        if (strcmp(nombre.datos, "_argv") == 0) { return "texto" };
        if (strcmp(nombre.datos, "salir") == 0) { return "nulo" };
        if (strcmp(nombre.datos, "concat") == 0) { return "texto" };
        if (strcmp(nombre.datos, "texto_a_entero") == 0) { return "int" };
        if (strcmp(nombre.datos, "texto_a_decimal") == 0) { return "decimal" };
        if (strcmp(nombre.datos, "entero_a_texto") == 0) { return "texto" };
        if (strcmp(nombre.datos, "decimal_a_texto") == 0) { return "texto" };
        if (strcmp(nombre.datos, "volcar_ast") == 0) { return "nulo" };
        if (strcmp(nombre.datos, "canal_crear") == 0) { return "CanalConcurrencia*" };
        if (strcmp(nombre.datos, "canal_enviar") == 0) { return "nulo" };
        if (strcmp(nombre.datos, "canal_recibir") == 0) { return "void*" };
        if (strcmp(nombre.datos, "cerrar_canal") == 0) { return "nulo" };
    }
    CadenaSegura _ret_330 = (CadenaSegura){ .longitud = 0, .datos = "" };
    return _ret_330;
}

CadenaSegura builtin_tipo_parametro(CadenaSegura nombre, int idx) {
    { /* unsafe */
        if (strcmp(nombre.datos, "reserva") == 0) { if (idx == 0) return "int" };
        if (strcmp(nombre.datos, "libera") == 0) { if (idx == 0) return "tensor" };
        if (strcmp(nombre.datos, "crear_tensor") == 0) { if (idx == 0) return "int"; if (idx == 1) return "int" };
        if (strcmp(nombre.datos, "suma_tensor") == 0) { if (idx == 0) return "tensor"; if (idx == 1) return "tensor" };
        if (strcmp(nombre.datos, "abrir") == 0) { if (idx == 0) return "texto"; if (idx == 1) return "texto" };
        if (strcmp(nombre.datos, "leer") == 0) { if (idx == 0) return "Canal" };
        if (strcmp(nombre.datos, "escribir") == 0) { if (idx == 0) return "texto" };
        if (strcmp(nombre.datos, "escribir_linea") == 0) { if (idx == 0) return "texto" };
        if (strcmp(nombre.datos, "leer_linea") == 0) { };
        if (strcmp(nombre.datos, "cerrar") == 0) { if (idx == 0) return "Canal" };
        if (strcmp(nombre.datos, "suma") == 0) { if (idx == 0) return "tensor"; if (idx == 1) return "tensor" };
        if (strcmp(nombre.datos, "producto") == 0) { if (idx == 0) return "tensor"; if (idx == 1) return "tensor" };
        if (strcmp(nombre.datos, "relu") == 0) { if (idx == 0) return "tensor" };
        if (strcmp(nombre.datos, "tokenizar") == 0) { if (idx == 0) return "texto" };
        if (strcmp(nombre.datos, "parsear") == 0) { if (idx == 0) return "texto" };
        if (strcmp(nombre.datos, "generar") == 0) { if (idx == 0) return "Programa"; if (idx == 1) return "texto" };
        if (strcmp(nombre.datos, "_argv") == 0) { if (idx == 0) return "int" };
        if (strcmp(nombre.datos, "salir") == 0) { if (idx == 0) return "int" };
        if (strcmp(nombre.datos, "concat") == 0) { if (idx == 0) return "texto"; if (idx == 1) return "texto" };
        if (strcmp(nombre.datos, "texto_a_entero") == 0) { if (idx == 0) return "texto" };
        if (strcmp(nombre.datos, "texto_a_decimal") == 0) { if (idx == 0) return "texto" };
        if (strcmp(nombre.datos, "entero_a_texto") == 0) { if (idx == 0) return "int" };
        if (strcmp(nombre.datos, "decimal_a_texto") == 0) { if (idx == 0) return "decimal" };
        if (strcmp(nombre.datos, "volcar_ast") == 0) { if (idx == 0) return "Programa"; if (idx == 1) return "int" };
        if (strcmp(nombre.datos, "canal_crear") == 0) { if (idx == 0) return "int" };
        if (strcmp(nombre.datos, "canal_enviar") == 0) { if (idx == 0) return "CanalConcurrencia*"; if (idx == 1) return "void*" };
        if (strcmp(nombre.datos, "canal_recibir") == 0) { if (idx == 0) return "CanalConcurrencia*" };
        if (strcmp(nombre.datos, "cerrar_canal") == 0) { if (idx == 0) return "CanalConcurrencia*" };
    }
    CadenaSegura _ret_362 = (CadenaSegura){ .longitud = 0, .datos = "" };
    return _ret_362;
}

int nodo_tipo(struct AnalizadorSemanticoEst est, int idx) {
    int r = 0;
    { /* unsafe */
        r = (idx >= 0 && idx < est.total_nodos) ? est.nodos[idx].tipo_nodo : 0;
    }
    int _ret_369 = r;
    return _ret_369;
}

int nodo_linea(struct AnalizadorSemanticoEst est, int idx) {
    int r = 0;
    { /* unsafe */
        r = (idx >= 0 && idx < est.total_nodos) ? est.nodos[idx].linea : 0;
    }
    int _ret_375 = r;
    return _ret_375;
}

int nodo_hijo_izq(struct AnalizadorSemanticoEst est, int idx) {
    int r = 0;
    { /* unsafe */
        r = (idx >= 0 && idx < est.total_nodos) ? est.nodos[idx].hijo_izq : 0;
    }
    int _ret_381 = r;
    return _ret_381;
}

int nodo_hijo_der(struct AnalizadorSemanticoEst est, int idx) {
    int r = 0;
    { /* unsafe */
        r = (idx >= 0 && idx < est.total_nodos) ? est.nodos[idx].hijo_der : 0;
    }
    int _ret_387 = r;
    return _ret_387;
}

int nodo_hermano(struct AnalizadorSemanticoEst est, int idx) {
    int r = 0;
    { /* unsafe */
        r = (idx >= 0 && idx < est.total_nodos) ? est.nodos[idx].hermano : 0;
    }
    int _ret_393 = r;
    return _ret_393;
}

void registrar_estructura(struct AnalizadorSemanticoEst est, CadenaSegura nombre, int idx_nodo) {
    int i = 0;
    int r = 1;
    while ((r == 1)) {
        { /* unsafe */
            r = (i < est.total_estructuras) ? 1 : 0;
            if ((r == 0)) {
                break;
            }
            int _eq = 1;;
            for (int _si = 0; _si < 256; _si++) { if (((const char*)nombre)[_si] != ((const char*)est.info_estructuras[i].nombre)[_si]) { _eq = 0; break; } if (((const char*)nombre)[_si] == 0) break; };
            if (_eq) {;
                sem_error(est, ERR_SEM_REDEFINICION, idx_nodo, nombre);;
                return;;
            };
            i = i + 1;
        }
    }
    { /* unsafe */
        est.info_estructuras[est.total_estructuras].nombre = nombre;
        est.info_estructuras[est.total_estructuras].total_campos = 0;
        est.total_estructuras = est.total_estructuras + 1;
    }
}

int parsear_patron_coincidir(CadenaSegura patron, CadenaSegura tag_nombre, CadenaSegura var_nombre) {
    { /* unsafe */
        if (((const char*)patron)[0] == '_' && ((const char*)patron)[1] == 0) { return 0 };
        // Extract tag name before '(';
        int _i = 0;;
        char _tag[64]; int _tp = 0;;
        while (((const char*)patron)[_i] != 0 && ((const char*)patron)[_i] != '(') { _tag[_tp++] = ((const char*)patron)[_i]; _i++; };
        _tag[_tp] = 0;;
        if (((const char*)patron)[_i] != '(') { return -1 };
        _i++; // skip '(';
        char _var[64]; int _vp = 0;;
        while (((const char*)patron)[_i] != 0 && ((const char*)patron)[_i] != ')') { _var[_vp++] = ((const char*)patron)[_i]; _i++; };
        _var[_vp] = 0;;
        if (((const char*)patron)[_i] != ')') { return -1 };
        // Copy results;
        int _tk = 0; while (_tag[_tk]) { ((char*)tag_nombre)[_tk] = _tag[_tk]; _tk++; } ((char*)tag_nombre)[_tk] = 0;;
        int _vk = 0; while (_var[_vk]) { ((char*)var_nombre)[_vk] = _var[_vk]; _vk++; } ((char*)var_nombre)[_vk] = 0;;
    }
    int _ret_439 = 1;
    return _ret_439;
}

void analizar_sentencia(struct AnalizadorSemanticoEst est, int idx_nodo) {
    if ((idx_nodo < 0)) {
        return;
    }
    int tipo = nodo_tipo(est, idx_nodo);
    int linea = nodo_linea(est, idx_nodo);
    if ((tipo == NODO_ASIGNACION)) {
        { /* unsafe */
            // Asignacion: buscar variable, inferir tipo, declarar si no existe;
        }
        return;
    }
    if ((tipo == NODO_DECLARACION)) {
        return;
    }
    if ((tipo == NODO_SI)) {
        tabla_entrar_scope(est);
        int cuerpo = nodo_hijo_izq(est, idx_nodo);
        int stmt = cuerpo;
        int r = 1;
        while ((r == 1)) {
            if ((stmt <= 0)) {
                r = 0;
                break;
            }
            analizar_sentencia(est, stmt);
            { /* unsafe */
                stmt = est.nodos[stmt].hermano;
            }
        }
        tabla_salir_scope(est);
        return;
    }
    if ((tipo == NODO_MIENTRAS)) {
        tabla_entrar_scope(est);
        cuerpo = nodo_hijo_izq(est, idx_nodo);
        stmt = cuerpo;
        r = 1;
        while ((r == 1)) {
            if ((stmt <= 0)) {
                r = 0;
                break;
            }
            analizar_sentencia(est, stmt);
            { /* unsafe */
                stmt = est.nodos[stmt].hermano;
            }
        }
        tabla_salir_scope(est);
        return;
    }
    if ((tipo == NODO_INSEGURO)) {
        tabla_entrar_scope(est);
        int prev = est.dentro_de_inseguro;
        est.dentro_de_inseguro = 1;
        cuerpo = nodo_hijo_izq(est, idx_nodo);
        stmt = cuerpo;
        r = 1;
        while ((r == 1)) {
            if ((stmt <= 0)) {
                r = 0;
                break;
            }
            analizar_sentencia(est, stmt);
            { /* unsafe */
                stmt = est.nodos[stmt].hermano;
            }
        }
        est.dentro_de_inseguro = prev;
        tabla_salir_scope(est);
        return;
    }
    if ((tipo == NODO_COINCIDIR)) {
        est.en_coincidir = 1;
        int casos = nodo_hijo_izq(est, idx_nodo);
        int idx_caso = casos;
        r = 1;
        while ((r == 1)) {
            if ((idx_caso <= 0)) {
                r = 0;
                break;
            }
            CadenaSegura tag_nombre = (CadenaSegura){ .longitud = 0, .datos = "" };
            CadenaSegura var_nombre = (CadenaSegura){ .longitud = 0, .datos = "" };
            int res = 0;
            { /* unsafe */
                // parsear patron del caso via parsear_patron_coincidir;
                res = parsear_patron_coincidir(;
                    est.nodos[idx_caso].ptr_str, tag_nombre, var_nombre);
            }
            if ((res == 0)) {
                tabla_entrar_scope(est);
                int cuerpo_caso = nodo_hijo_izq(est, idx_caso);
                int stmt_c = cuerpo_caso;
                int r2 = 1;
                while ((r2 == 1)) {
                    if ((stmt_c <= 0)) {
                        r2 = 0;
                        break;
                    }
                    analizar_sentencia(est, stmt_c);
                    { /* unsafe */
                        stmt_c = est.nodos[stmt_c].hermano;
                    }
                }
                tabla_salir_scope(est);
            }
            if ((res == 1)) {
                tabla_declarar(est, var_nombre, (CadenaSegura){ .longitud = 3, .datos = "int" }, idx_caso, 0);
                tabla_entrar_scope(est);
                cuerpo_caso = nodo_hijo_izq(est, idx_caso);
                stmt_c = cuerpo_caso;
                r2 = 1;
                while ((r2 == 1)) {
                    if ((stmt_c <= 0)) {
                        r2 = 0;
                        break;
                    }
                    analizar_sentencia(est, stmt_c);
                    { /* unsafe */
                        stmt_c = est.nodos[stmt_c].hermano;
                    }
                }
                tabla_salir_scope(est);
            }
            { /* unsafe */
                idx_caso = est.nodos[idx_caso].hermano;
            }
        }
        est.en_coincidir = 0;
        return;
    }
    if ((tipo == NODO_EXPR)) {
        return;
    }
    if ((tipo == NODO_LOG)) {
        return;
    }
    return;
}

void analizar_paso_estructuras(struct AnalizadorSemanticoEst est, int idx_programa) {
    int stmt = nodo_hijo_izq(est, idx_programa);
    int r = 1;
    while ((r == 1)) {
        if ((stmt <= 0)) {
            r = 0;
            break;
        }
        int tipo = nodo_tipo(est, stmt);
        if ((tipo == NODO_ESTRUCTURA)) {
            CadenaSegura nombre = (CadenaSegura){ .longitud = 0, .datos = "" };
            { /* unsafe */
                // Obtener nombre de estructura del nodo;
            }
            registrar_estructura(est, nombre, stmt);
        }
        { /* unsafe */
            stmt = est.nodos[stmt].hermano;
        }
    }
}

void analizar_paso_funciones(struct AnalizadorSemanticoEst est, int idx_programa) {
    int stmt = nodo_hijo_izq(est, idx_programa);
    int r = 1;
    while ((r == 1)) {
        if ((stmt <= 0)) {
            r = 0;
            break;
        }
        int tipo = nodo_tipo(est, stmt);
        if ((tipo == NODO_FUNCION)) {
            CadenaSegura nombre = (CadenaSegura){ .longitud = 0, .datos = "" };
            { /* unsafe */
                // Obtener nombre de funcion del nodo;
            }
            if ((es_builtin(nombre) == 0)) {
                int ok = tabla_declarar(est, nombre, (CadenaSegura){ .longitud = 3, .datos = "int" }, stmt, 0);
                if ((ok == 0)) {
                    sem_error(est, ERR_SEM_REDEFINICION, stmt, nombre);
                }
            }
        }
        if ((tipo == NODO_EXTERNO)) {
            _syn_texto_liberar(nombre);
            nombre = (CadenaSegura){ .longitud = 0, .datos = "" };
            { /* unsafe */
                // Obtener nombre externo del nodo;
            }
            ok = tabla_declarar(est, nombre, (CadenaSegura){ .longitud = 3, .datos = "int" }, stmt, 0);
            if ((ok == 0)) {
                sem_error(est, ERR_SEM_REDEFINICION, stmt, nombre);
            }
        }
        { /* unsafe */
            stmt = est.nodos[stmt].hermano;
        }
    }
}

void analizar_paso_cuerpos(struct AnalizadorSemanticoEst est, int idx_programa) {
    int stmt = nodo_hijo_izq(est, idx_programa);
    int r = 1;
    while ((r == 1)) {
        if ((stmt <= 0)) {
            r = 0;
            break;
        }
        int tipo = nodo_tipo(est, stmt);
        if ((tipo == NODO_FUNCION)) {
            CadenaSegura nombre = (CadenaSegura){ .longitud = 0, .datos = "" };
            { /* unsafe */
                // Obtener nombre de funcion y analizar cuerpo;
            }
            if ((es_builtin(nombre) == 0)) {
                tabla_entrar_scope(est);
                est.func_actual = nombre;
                int cuerpo = nodo_hijo_izq(est, stmt);
                int stmt_cuerpo = cuerpo;
                int r2 = 1;
                while ((r2 == 1)) {
                    if ((stmt_cuerpo <= 0)) {
                        r2 = 0;
                        break;
                    }
                    analizar_sentencia(est, stmt_cuerpo);
                    { /* unsafe */
                        stmt_cuerpo = est.nodos[stmt_cuerpo].hermano;
                    }
                }
                tabla_salir_scope(est);
                est.func_actual = (CadenaSegura){ .longitud = 0, .datos = "" };
            }
        }
        { /* unsafe */
            stmt = est.nodos[stmt].hermano;
        }
    }
}

void analizar(struct AnalizadorSemanticoEst est) {
    int idx_programa = 0;
    { /* unsafe */
        idx_programa = 0;
        // Buscar el nodo raiz NODO_PROGRAMA;
        for (int _i = 0; _i < est.total_nodos; _i++) {;
            if (est.nodos[_i].tipo_nodo == 1) { idx_programa = _i; break; };
        };
    }
    if ((idx_programa < 0)) {
        return;
    }
    analizar_paso_estructuras(est, idx_programa);
    analizar_paso_funciones(est, idx_programa);
    analizar_paso_cuerpos(est, idx_programa);
}

struct AnalizadorSemanticoEst analizador_nuevo(struct SemNodo nodos, int total) {
    struct AnalizadorSemanticoEst est = AnalizadorSemanticoEst_nuevo();
    est->nodos = nodos;
    est.total_nodos = total;
    { /* unsafe */
        est.tabla->nivel_actual = 0;
        est.tabla->total_entradas = 0;
    }
    est.func_retorno = (CadenaSegura){ .longitud = 0, .datos = "" };
    est.func_actual = (CadenaSegura){ .longitud = 0, .datos = "" };
    est.en_coincidir = 0;
    est.dentro_de_inseguro = 0;
    est.hay_error = 0;
    est.total_estructuras = 0;
    est.total_asignaciones = 0;
    struct AnalizadorSemanticoEst _ret_680 = est;
    return _ret_680;
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    synapse_esperar_hilos();
    return 0;
}