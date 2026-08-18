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

char _gen_tmp_buf[4096];

extern int _G_indent;

const char* _G_mt(const char* st);
void _G_vest(struct DefinicionEstructura* n);

#define TAG_OK 0
#define TAG_ERR 1
#define TAG_ALGUNO 0
#define TAG_NINGUNO 1

// --- Helpers de serialización primitiva ---
inline void* _synapse_box_int(int v) { return (void*)(intptr_t)v; }
inline int _synapse_unbox_int(void* p) { return (int)(intptr_t)p; }
inline void* _synapse_box_float(float v) {
    float* _p = (float*)malloc(sizeof(float));
    if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo\\n"); exit(1); }
    *_p = v;
    return (void*)_p;
}
inline float _synapse_unbox_float(void* p) {
    float _v = *(float*)p;
    free(p);
    return _v;
}

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

typedef struct { int es_ok; union {
void* ok_valor; const char* err_mensaje;
} datos; } Resultado_T;
typedef struct CanalConcurrencia CanalConcurrencia;
extern CanalConcurrencia* canal_crear(uint32_t capacidad);
extern void canal_enviar(CanalConcurrencia* canal, void* paquete);
extern void* canal_recibir(CanalConcurrencia* canal);
extern void canal_destruir(CanalConcurrencia* canal);
extern void cerrar(CanalConcurrencia* canal);
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

struct SemNodo;
struct SemSimbolo;
struct SemTablaSimbolos;
struct SemEstructuraInfo;
struct AnalizadorSemanticoEst;

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

typedef struct SemSimbolo {
    CadenaSegura nombre;
    CadenaSegura tipo;
    int nivel_ambito;
    int propiedad;
    int es_constante;
    int linea;
    int columna;
} SemSimbolo;

typedef struct SemTablaSimbolos {
    struct SemSimbolo* entradas;
    int total_entradas;
    int nivel_actual;
} SemTablaSimbolos;

typedef struct SemEstructuraInfo {
    CadenaSegura nombre;
    CadenaSegura campos_nombre;
    CadenaSegura campos_tipo;
    int total_campos;
} SemEstructuraInfo;

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
#define NODO_PARA (45)
#define NODO_CONTRATO (46)
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
void sem_error(struct AnalizadorSemanticoEst est, int codigo, int idx_nodo, CadenaSegura mensaje) {
    int linea;
    int columna;
    linea = 0;
    columna = 0;
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
    int linea;
    int columna;
    int i;
    int encontrado;
    int r;
    linea = 0;
    columna = 0;
    { /* unsafe */
        linea = (idx_nodo >= 0) ? est.nodos[idx_nodo].linea : 0;
        columna = (idx_nodo >= 0) ? est.nodos[idx_nodo].columna : 0;
    }
    i = 0;
    encontrado = 0;
    r = 1;
    while ((r == 1)) {
        { /* unsafe */
            r = (i < est.tabla->total_entradas) ? 1 : 0;
            if ((r == 0)) {
                break;
            }
            if (est.tabla->entradas[i].nivel_ambito == est.tabla->nivel_actual) {;
                int _eq = 1;
                for (int _si = 0; _si < 256; _si++) { if (((const char*)nombre.datos)[_si] != ((const char*)est.tabla->entradas[i].nombre.datos)[_si]) { _eq = 0; break; } if (((const char*)nombre.datos)[_si] == 0) break; };
                if (_eq) { encontrado = verdadero; };
            };
            i = i + 1;
        }
    }
    if ((encontrado == 1)) {
        int _ret_153 = 0;
        return _ret_153;
    }
    { /* unsafe */
        est.tabla->entradas[est.tabla->total_entradas].nombre = nombre;
        est.tabla->entradas[est.tabla->total_entradas].tipo = tipo;
        est.tabla->entradas[est.tabla->total_entradas].nivel_ambito = est.tabla->nivel_actual;
        est.tabla->entradas[est.tabla->total_entradas].propiedad = 1;
        est.tabla->entradas[est.tabla->total_entradas].es_constante = es_constante;
        est.tabla->entradas[est.tabla->total_entradas].linea = linea;
        est.tabla->entradas[est.tabla->total_entradas].columna = columna;
        est.tabla->total_entradas = est.tabla->total_entradas + 1;
    }
    int _ret_164 = 1;
    return _ret_164;
}

int tabla_buscar(struct AnalizadorSemanticoEst est, CadenaSegura nombre) {
    int i;
    int r;
    i = 0;
    r = 1;
    while ((r == 1)) {
        { /* unsafe */
            r = (i < est.tabla->total_entradas) ? 1 : 0;
            if ((r == 0)) {
                break;
            }
            int _eq = 1;
            for (int _si = 0; _si < 256; _si++) {;
                char _a = nombre.datos[_si];
                char _b = est.tabla->entradas[i].nombre.datos[_si];
                if (_a != _b) { _eq = 0; break; };
                if (_a == 0) break;
            };
            if (_eq) { return i; };
            i = i + 1;
        }
    }
    int _ret_183 = (-1);
    return _ret_183;
}

void tabla_entrar_scope(struct AnalizadorSemanticoEst est) {
    { /* unsafe */
        est.tabla->nivel_actual = est.tabla->nivel_actual + 1;
    }
}

void tabla_salir_scope(struct AnalizadorSemanticoEst est) {
    { /* unsafe */
        while (est.tabla->total_entradas > 0) {;
            if (est.tabla->entradas[est.tabla->total_entradas - 1].nivel_ambito < est.tabla->nivel_actual) break;
            est.tabla->total_entradas = est.tabla->total_entradas - 1;
        };
        est.tabla->nivel_actual = est.tabla->nivel_actual - 1;
    }
}

void tabla_marcar_movido(struct AnalizadorSemanticoEst est, CadenaSegura nombre) {
    int idx;
    idx = tabla_buscar(est, nombre);
    if ((idx >= 0)) {
        { /* unsafe */
            est.tabla->entradas[idx].propiedad = 2;
        }
    }
}

int tabla_esta_movido(struct AnalizadorSemanticoEst est, CadenaSegura nombre) {
    int idx;
    int r;
    idx = tabla_buscar(est, nombre);
    if ((idx >= 0)) {
        r = 0;
        { /* unsafe */
            r = (est.tabla->entradas[idx].propiedad == 2) ? 1 : 0;
        }
        if ((r == 1)) {
            int _ret_210 = 1;
            return _ret_210;
        }
    }
    int _ret_211 = 0;
    return _ret_211;
}

CadenaSegura tipo_normalizado(CadenaSegura tipo) {
    if (((str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("entero"), .datos = "entero" }) == 1) || (str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" }) == 1))) {
        CadenaSegura _ret_216 = (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
        return _ret_216;
    }
    if ((((str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("decimal"), .datos = "decimal" }) == 1) || (str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("real"), .datos = "real" }) == 1)) || (str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("flotante"), .datos = "flotante" }) == 1))) {
        CadenaSegura _ret_218 = (CadenaSegura){ .longitud = (int)strlen("decimal"), .datos = "decimal" };
        return _ret_218;
    }
    if (((str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("booleano"), .datos = "booleano" }) == 1) || (str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("logico"), .datos = "logico" }) == 1))) {
        CadenaSegura _ret_220 = (CadenaSegura){ .longitud = (int)strlen("booleano"), .datos = "booleano" };
        return _ret_220;
    }
    if (((str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" }) == 1) || (str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("cadena"), .datos = "cadena" }) == 1))) {
        CadenaSegura _ret_222 = (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
        return _ret_222;
    }
    if (((str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" }) == 1) || (str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("vacio"), .datos = "vacio" }) == 1))) {
        CadenaSegura _ret_224 = (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
        return _ret_224;
    }
    if ((str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" }) == 1)) {
        CadenaSegura _ret_226 = (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
        return _ret_226;
    }
    if ((str_eq(tipo, (CadenaSegura){ .longitud = (int)strlen("CanalConcurrencia*"), .datos = "CanalConcurrencia*" }) == 1)) {
        CadenaSegura _ret_228 = (CadenaSegura){ .longitud = (int)strlen("CanalConcurrencia*"), .datos = "CanalConcurrencia*" };
        return _ret_228;
    }
    CadenaSegura _ret_229 = tipo;
    return _ret_229;
}

int es_builtin(CadenaSegura nombre) {
    { /* unsafe */
        if (strcmp(nombre.datos, "reserva") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "libera") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "crear_tensor") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "suma_tensor") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "producto_punto") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "abrir") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "leer") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "escribir") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "escribir_linea") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "leer_linea") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "cerrar") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "suma") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "producto") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "relu") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "tokenizar") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "parsear") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "generar") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "_argc") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "_argv") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "salir") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "concat") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "texto_a_entero") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "texto_a_decimal") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "entero_a_texto") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "decimal_a_texto") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "volcar_ast") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "canal_crear") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "canal_enviar") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "canal_recibir") == 0) { return verdadero; };
        if (strcmp(nombre.datos, "cerrar") == 0) { return verdadero; };
    }
    int _ret_264 = 0;
    return _ret_264;
}

int builtin_cantidad_args(CadenaSegura nombre) {
    { /* unsafe */
        if (strcmp(nombre.datos, "reserva") == 0) { return 1; };
        if (strcmp(nombre.datos, "libera") == 0) { return 1; };
        if (strcmp(nombre.datos, "crear_tensor") == 0) { return 2; };
        if (strcmp(nombre.datos, "suma_tensor") == 0) { return 2; };
        if (strcmp(nombre.datos, "producto_punto") == 0) { return 2; };
        if (strcmp(nombre.datos, "abrir") == 0) { return 2; };
        if (strcmp(nombre.datos, "leer") == 0) { return 1; };
        if (strcmp(nombre.datos, "escribir") == 0) { return 1; };
        if (strcmp(nombre.datos, "escribir_linea") == 0) { return 1; };
        if (strcmp(nombre.datos, "leer_linea") == 0) { return 0; };
        if (strcmp(nombre.datos, "cerrar") == 0) { return 1; };
        if (strcmp(nombre.datos, "suma") == 0) { return 2; };
        if (strcmp(nombre.datos, "producto") == 0) { return 2; };
        if (strcmp(nombre.datos, "relu") == 0) { return 1; };
        if (strcmp(nombre.datos, "tokenizar") == 0) { return 1; };
        if (strcmp(nombre.datos, "parsear") == 0) { return 1; };
        if (strcmp(nombre.datos, "generar") == 0) { return 2; };
        if (strcmp(nombre.datos, "_argc") == 0) { return 0; };
        if (strcmp(nombre.datos, "_argv") == 0) { return 1; };
        if (strcmp(nombre.datos, "salir") == 0) { return 1; };
        if (strcmp(nombre.datos, "concat") == 0) { return 2; };
        if (strcmp(nombre.datos, "texto_a_entero") == 0) { return 1; };
        if (strcmp(nombre.datos, "texto_a_decimal") == 0) { return 1; };
        if (strcmp(nombre.datos, "entero_a_texto") == 0) { return 1; };
        if (strcmp(nombre.datos, "decimal_a_texto") == 0) { return 1; };
        if (strcmp(nombre.datos, "volcar_ast") == 0) { return 2; };
        if (strcmp(nombre.datos, "canal_crear") == 0) { return 1; };
        if (strcmp(nombre.datos, "canal_enviar") == 0) { return 2; };
        if (strcmp(nombre.datos, "canal_recibir") == 0) { return 1; };
        if (strcmp(nombre.datos, "cerrar") == 0) { return 1; };
    }
    int _ret_298 = 0;
    return _ret_298;
}

CadenaSegura builtin_tipo_retorno(CadenaSegura nombre) {
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("reserva"), .datos = "reserva" }) == 1)) {
        CadenaSegura _ret_301 = (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
        return _ret_301;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("libera"), .datos = "libera" }) == 1)) {
        CadenaSegura _ret_302 = (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
        return _ret_302;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("crear_tensor"), .datos = "crear_tensor" }) == 1)) {
        CadenaSegura _ret_303 = (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
        return _ret_303;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("suma_tensor"), .datos = "suma_tensor" }) == 1)) {
        CadenaSegura _ret_304 = (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
        return _ret_304;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("producto_punto"), .datos = "producto_punto" }) == 1)) {
        CadenaSegura _ret_305 = (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
        return _ret_305;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("abrir"), .datos = "abrir" }) == 1)) {
        CadenaSegura _ret_306 = (CadenaSegura){ .longitud = (int)strlen("Canal"), .datos = "Canal" };
        return _ret_306;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("leer"), .datos = "leer" }) == 1)) {
        CadenaSegura _ret_307 = (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
        return _ret_307;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("escribir"), .datos = "escribir" }) == 1)) {
        CadenaSegura _ret_308 = (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
        return _ret_308;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("escribir_linea"), .datos = "escribir_linea" }) == 1)) {
        CadenaSegura _ret_309 = (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
        return _ret_309;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("leer_linea"), .datos = "leer_linea" }) == 1)) {
        CadenaSegura _ret_310 = (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
        return _ret_310;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("cerrar"), .datos = "cerrar" }) == 1)) {
        CadenaSegura _ret_311 = (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
        return _ret_311;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("suma"), .datos = "suma" }) == 1)) {
        CadenaSegura _ret_312 = (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
        return _ret_312;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("producto"), .datos = "producto" }) == 1)) {
        CadenaSegura _ret_313 = (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
        return _ret_313;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("relu"), .datos = "relu" }) == 1)) {
        CadenaSegura _ret_314 = (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
        return _ret_314;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("tokenizar"), .datos = "tokenizar" }) == 1)) {
        CadenaSegura _ret_315 = (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
        return _ret_315;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("parsear"), .datos = "parsear" }) == 1)) {
        CadenaSegura _ret_316 = (CadenaSegura){ .longitud = (int)strlen("Programa"), .datos = "Programa" };
        return _ret_316;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("generar"), .datos = "generar" }) == 1)) {
        CadenaSegura _ret_317 = (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
        return _ret_317;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("_argc"), .datos = "_argc" }) == 1)) {
        CadenaSegura _ret_318 = (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
        return _ret_318;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("_argv"), .datos = "_argv" }) == 1)) {
        CadenaSegura _ret_319 = (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
        return _ret_319;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("salir"), .datos = "salir" }) == 1)) {
        CadenaSegura _ret_320 = (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
        return _ret_320;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("concat"), .datos = "concat" }) == 1)) {
        CadenaSegura _ret_321 = (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
        return _ret_321;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("texto_a_entero"), .datos = "texto_a_entero" }) == 1)) {
        CadenaSegura _ret_322 = (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
        return _ret_322;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("texto_a_decimal"), .datos = "texto_a_decimal" }) == 1)) {
        CadenaSegura _ret_323 = (CadenaSegura){ .longitud = (int)strlen("decimal"), .datos = "decimal" };
        return _ret_323;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("entero_a_texto"), .datos = "entero_a_texto" }) == 1)) {
        CadenaSegura _ret_324 = (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
        return _ret_324;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("decimal_a_texto"), .datos = "decimal_a_texto" }) == 1)) {
        CadenaSegura _ret_325 = (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
        return _ret_325;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("volcar_ast"), .datos = "volcar_ast" }) == 1)) {
        CadenaSegura _ret_326 = (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
        return _ret_326;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("canal_crear"), .datos = "canal_crear" }) == 1)) {
        CadenaSegura _ret_327 = (CadenaSegura){ .longitud = (int)strlen("CanalConcurrencia*"), .datos = "CanalConcurrencia*" };
        return _ret_327;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("canal_enviar"), .datos = "canal_enviar" }) == 1)) {
        CadenaSegura _ret_328 = (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
        return _ret_328;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("canal_recibir"), .datos = "canal_recibir" }) == 1)) {
        CadenaSegura _ret_329 = (CadenaSegura){ .longitud = (int)strlen("void*"), .datos = "void*" };
        return _ret_329;
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("cerrar"), .datos = "cerrar" }) == 1)) {
        CadenaSegura _ret_330 = (CadenaSegura){ .longitud = (int)strlen("nulo"), .datos = "nulo" };
        return _ret_330;
    }
    CadenaSegura _ret_331 = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    return _ret_331;
}

CadenaSegura builtin_tipo_parametro(CadenaSegura nombre, int idx) {
    if ((((((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("reserva"), .datos = "reserva" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("libera"), .datos = "libera" }) == 1)) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("crear_tensor"), .datos = "crear_tensor" }) == 1)) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("suma_tensor"), .datos = "suma_tensor" }) == 1)) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("producto_punto"), .datos = "producto_punto" }) == 1))) {
        if ((idx == 0)) {
            CadenaSegura _ret_335 = (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
            return _ret_335;
        }
        if ((((idx == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("reserva"), .datos = "reserva" }) == 1)) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("libera"), .datos = "libera" }) == 1))) {
            CadenaSegura _ret_336 = (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
            return _ret_336;
        }
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("abrir"), .datos = "abrir" }) == 1)) {
        if (((idx == 0) || (idx == 1))) {
            CadenaSegura _ret_338 = (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
            return _ret_338;
        }
    }
    if (((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("leer"), .datos = "leer" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("cerrar"), .datos = "cerrar" }) == 1))) {
        if ((idx == 0)) {
            CadenaSegura _ret_340 = (CadenaSegura){ .longitud = (int)strlen("Canal"), .datos = "Canal" };
            return _ret_340;
        }
    }
    if (((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("escribir"), .datos = "escribir" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("escribir_linea"), .datos = "escribir_linea" }) == 1))) {
        if ((idx == 0)) {
            CadenaSegura _ret_342 = (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
            return _ret_342;
        }
    }
    if (((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("suma"), .datos = "suma" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("producto"), .datos = "producto" }) == 1))) {
        if (((idx == 0) || (idx == 1))) {
            CadenaSegura _ret_344 = (CadenaSegura){ .longitud = (int)strlen("tensor"), .datos = "tensor" };
            return _ret_344;
        }
    }
    if ((((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("relu"), .datos = "relu" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("tokenizar"), .datos = "tokenizar" }) == 1)) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("parsear"), .datos = "parsear" }) == 1))) {
        if ((idx == 0)) {
            CadenaSegura _ret_346 = (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
            return _ret_346;
        }
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("generar"), .datos = "generar" }) == 1)) {
        if ((idx == 0)) {
            CadenaSegura _ret_348 = (CadenaSegura){ .longitud = (int)strlen("Programa"), .datos = "Programa" };
            return _ret_348;
        }
        if ((idx == 1)) {
            CadenaSegura _ret_349 = (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
            return _ret_349;
        }
    }
    if ((((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("_argv"), .datos = "_argv" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("salir"), .datos = "salir" }) == 1)) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("texto_a_entero"), .datos = "texto_a_entero" }) == 1))) {
        if ((idx == 0)) {
            CadenaSegura _ret_351 = (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
            return _ret_351;
        }
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("concat"), .datos = "concat" }) == 1)) {
        if (((idx == 0) || (idx == 1))) {
            CadenaSegura _ret_353 = (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
            return _ret_353;
        }
    }
    if (((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("texto_a_decimal"), .datos = "texto_a_decimal" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("decimal_a_texto"), .datos = "decimal_a_texto" }) == 1))) {
        if ((idx == 0)) {
            CadenaSegura _ret_355 = (CadenaSegura){ .longitud = (int)strlen("texto"), .datos = "texto" };
            return _ret_355;
        }
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("entero_a_texto"), .datos = "entero_a_texto" }) == 1)) {
        if ((idx == 0)) {
            CadenaSegura _ret_357 = (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
            return _ret_357;
        }
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("volcar_ast"), .datos = "volcar_ast" }) == 1)) {
        if ((idx == 0)) {
            CadenaSegura _ret_359 = (CadenaSegura){ .longitud = (int)strlen("Programa"), .datos = "Programa" };
            return _ret_359;
        }
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("canal_crear"), .datos = "canal_crear" }) == 1)) {
        if ((idx == 0)) {
            CadenaSegura _ret_361 = (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" };
            return _ret_361;
        }
    }
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("canal_enviar"), .datos = "canal_enviar" }) == 1)) {
        if ((idx == 0)) {
            CadenaSegura _ret_363 = (CadenaSegura){ .longitud = (int)strlen("CanalConcurrencia*"), .datos = "CanalConcurrencia*" };
            return _ret_363;
        }
        if ((idx == 1)) {
            CadenaSegura _ret_364 = (CadenaSegura){ .longitud = (int)strlen("void*"), .datos = "void*" };
            return _ret_364;
        }
    }
    if (((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("canal_recibir"), .datos = "canal_recibir" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("cerrar"), .datos = "cerrar" }) == 1))) {
        if ((idx == 0)) {
            CadenaSegura _ret_366 = (CadenaSegura){ .longitud = (int)strlen("CanalConcurrencia*"), .datos = "CanalConcurrencia*" };
            return _ret_366;
        }
    }
    CadenaSegura _ret_367 = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    return _ret_367;
}

int nodo_tipo(struct AnalizadorSemanticoEst est, int idx) {
    int r;
    r = 0;
    { /* unsafe */
        r = (idx >= 0 && idx < est.total_nodos) ? est.nodos[idx].tipo_nodo : 0;
    }
    int _ret_374 = r;
    return _ret_374;
}

int nodo_linea(struct AnalizadorSemanticoEst est, int idx) {
    int r;
    r = 0;
    { /* unsafe */
        r = (idx >= 0 && idx < est.total_nodos) ? est.nodos[idx].linea : 0;
    }
    int _ret_380 = r;
    return _ret_380;
}

int nodo_hijo_izq(struct AnalizadorSemanticoEst est, int idx) {
    int r;
    r = 0;
    { /* unsafe */
        r = (idx >= 0 && idx < est.total_nodos) ? est.nodos[idx].hijo_izq : 0;
    }
    int _ret_386 = r;
    return _ret_386;
}

int nodo_hijo_der(struct AnalizadorSemanticoEst est, int idx) {
    int r;
    r = 0;
    { /* unsafe */
        r = (idx >= 0 && idx < est.total_nodos) ? est.nodos[idx].hijo_der : 0;
    }
    int _ret_392 = r;
    return _ret_392;
}

int nodo_hermano(struct AnalizadorSemanticoEst est, int idx) {
    int r;
    r = 0;
    { /* unsafe */
        r = (idx >= 0 && idx < est.total_nodos) ? est.nodos[idx].hermano : 0;
    }
    int _ret_398 = r;
    return _ret_398;
}

void registrar_estructura(struct AnalizadorSemanticoEst est, CadenaSegura nombre, int idx_nodo) {
    int i;
    int r;
    i = 0;
    r = 1;
    while ((r == 1)) {
        { /* unsafe */
            r = (i < est.total_estructuras) ? 1 : 0;
            if ((r == 0)) {
                break;
            }
            int _eq = 1;
            for (int _si = 0; _si < 256; _si++) { if (nombre.datos[_si] != est.info_estructuras[i].nombre.datos[_si]) { _eq = 0; break; } if (nombre.datos[_si] == 0) break; };
            if (_eq) {;
                sem_error(est, ERR_SEM_REDEFINICION, idx_nodo, nombre);
                return;
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
        if (patron.datos[0] == '_' && patron.datos[1] == 0) { return 0; };
        // Extract tag name before '(';
        int _i = 0;
        char _tag[64]; int _tp = 0;
        while (patron.datos[_i] != 0 && patron.datos[_i] != '(') { _tag[_tp++] = patron.datos[_i]; _i++; };
        _tag[_tp] = 0;
        if (patron.datos[_i] != '(') { return -1; };
        _i++; // skip '(';
        char _var[64]; int _vp = 0;
        while (patron.datos[_i] != 0 && patron.datos[_i] != ')') { _var[_vp++] = patron.datos[_i]; _i++; };
        _var[_vp] = 0;
        if (patron.datos[_i] != ')') { return -1; };
        // Copy results using strdup to own memory;
        tag_nombre = (CadenaSegura){ .longitud = _tp, .datos = strdup(_tag) };
        var_nombre = (CadenaSegura){ .longitud = _vp, .datos = strdup(_var) };
    }
    int _ret_444 = 1;
    return _ret_444;
}

void analizar_sentencia(struct AnalizadorSemanticoEst est, int idx_nodo) {
    int tipo;
    int linea;
    int cuerpo;
    int stmt;
    int r;
    int prev;
    int casos;
    int idx_caso;
    int res;
    int cuerpo_caso;
    int stmt_c;
    int r2;
    if ((idx_nodo < 0)) {
        return;
    }
    tipo = nodo_tipo(est, idx_nodo);
    linea = nodo_linea(est, idx_nodo);
    if ((tipo == NODO_ASIGNACION)) {
        { /* unsafe */
            { int* _phi=(int*)est.asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est.nodos[idx_nodo].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[idx_nodo])<<32; } const char* _v=(const char*)_bp; if(_v){ CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_v}; if(tabla_buscar(est,_cs)<0) sem_error(est,ERR_SEM_VAR_NO_DECLARADA,idx_nodo,_cs); } };
        }
        return;
    }
    if ((tipo == NODO_DECLARACION)) {
        { /* unsafe */
            { int* _phi=(int*)est.asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est.nodos[idx_nodo].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[idx_nodo])<<32; } const char* _v=(const char*)_bp; if(_v){ CadenaSegura _cs={.longitud=(int)strlen(_v),.datos=_v}; if(tabla_buscar(est,_cs)>=0){ sem_error(est,ERR_SEM_REDEFINICION,idx_nodo,_cs); }else{ CadenaSegura _t={.longitud=5,.datos="entero"}; tabla_declarar(est,_cs,_t,idx_nodo,0); } } };
        }
        return;
    }
    if ((tipo == NODO_SI)) {
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
        prev = est.dentro_de_inseguro;
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
        casos = nodo_hijo_izq(est, idx_nodo);
        idx_caso = casos;
        r = 1;
        while ((r == 1)) {
            if ((idx_caso <= 0)) {
                r = 0;
                break;
            }
            CadenaSegura tag_nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
            CadenaSegura var_nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
            res = 0;
            { /* unsafe */
                int* _phi=(int*)est.asignaciones_campos_campo.datos; uintptr_t _bp=(uintptr_t)(unsigned)est.nodos[idx_caso].ptr_str; if(_phi){ _bp|=((uintptr_t)(unsigned)_phi[idx_caso])<<32; } CadenaSegura _patron_s = { .longitud = 255, .datos = (const char*)_bp };
                res = parsear_patron_coincidir(_patron_s, tag_nombre, var_nombre);
            }
            if ((res == 0)) {
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
            if ((res == 1)) {
                tabla_declarar(est, var_nombre, (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" }, idx_caso, 0);
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
    int stmt;
    int r;
    int tipo;
    stmt = nodo_hijo_izq(est, idx_programa);
    r = 1;
    while ((r == 1)) {
        if ((stmt <= 0)) {
            r = 0;
            break;
        }
        tipo = nodo_tipo(est, stmt);
        if ((tipo == NODO_ESTRUCTURA)) {
            CadenaSegura nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
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
    int stmt;
    int r;
    int tipo;
    int ok;
    CadenaSegura nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    stmt = nodo_hijo_izq(est, idx_programa);
    r = 1;
    while ((r == 1)) {
        if ((stmt <= 0)) {
            r = 0;
            break;
        }
        tipo = nodo_tipo(est, stmt);
        if ((tipo == NODO_FUNCION)) {
            { /* unsafe */
                // Obtener nombre de funcion del nodo;
            }
            if ((es_builtin(nombre) == 0)) {
                ok = tabla_declarar(est, nombre, (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" }, stmt, 0);
                if ((ok == 0)) {
                    sem_error(est, ERR_SEM_REDEFINICION, stmt, nombre);
                }
            }
        }
        if ((tipo == NODO_EXTERNO)) {
            { /* unsafe */
                // Obtener nombre externo del nodo;
            }
            ok = tabla_declarar(est, nombre, (CadenaSegura){ .longitud = (int)strlen("int"), .datos = "int" }, stmt, 0);
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
    int stmt;
    int r;
    int tipo;
    int cuerpo;
    int stmt_cuerpo;
    int r2;
    stmt = nodo_hijo_izq(est, idx_programa);
    r = 1;
    while ((r == 1)) {
        if ((stmt <= 0)) {
            r = 0;
            break;
        }
        tipo = nodo_tipo(est, stmt);
        if ((tipo == NODO_FUNCION)) {
            CadenaSegura nombre = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
            { /* unsafe */
                // Obtener nombre de funcion y analizar cuerpo;
            }
            if ((es_builtin(nombre) == 0)) {
                tabla_entrar_scope(est);
                est.func_actual = nombre;
                cuerpo = nodo_hijo_izq(est, stmt);
                stmt_cuerpo = cuerpo;
                r2 = 1;
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
                est.func_actual = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
            }
        }
        { /* unsafe */
            stmt = est.nodos[stmt].hermano;
        }
    }
}

void analizar(struct AnalizadorSemanticoEst est) {
    int idx_programa;
    idx_programa = 0;
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
    struct AnalizadorSemanticoEst est;
    est = (struct AnalizadorSemanticoEst){0};
    { /* unsafe */
        est.nodos = (struct SemNodo*)&nodos;
        est.total_nodos = total;
        est.tabla->nivel_actual = 0;
        est.tabla->total_entradas = 0;
    }
    est.func_retorno = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    est.func_actual = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    est.en_coincidir = 0;
    est.dentro_de_inseguro = 0;
    est.hay_error = 0;
    est.total_estructuras = 0;
    est.total_asignaciones = 0;
    struct AnalizadorSemanticoEst _ret_685 = est;
    return _ret_685;
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    synapse_esperar_hilos();
    return 0;
}