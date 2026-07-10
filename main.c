// Generado por Synapse (auto-hospedado)
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <pthread.h>
typedef struct {int longitud;const char* datos;} CadenaSegura;
typedef struct {uint32_t filas;uint32_t columnas;float* datos;} Tensor;
typedef struct {FILE* stream;int es_valido;int es_virtual;const char* virtual_data;int virtual_len;} Canal;
#define POOL_BLOQUES 64
#define TAMANO_BLOQUE 4096
#define nulo ((void*)0)
// --- Declaraciones extern del runtime precompilado (synapse_rt.o) ---
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
extern void pool_init(uint32_t total_blocks, uint32_t block_size);
extern void pool_free(void* ptr);
static int _g_argc;
static char** _g_argv;
int _argc(){return _g_argc;}
CadenaSegura _argv(int i){if(i<0||i>=_g_argc)return (CadenaSegura){0,(char*)""};return (CadenaSegura){.longitud=(int)strlen(_g_argv[i]),.datos=_g_argv[i]};}
void salir(int c){exit(c);}
CadenaSegura concat(CadenaSegura a,CadenaSegura b){int _tl=a.longitud+b.longitud;char* _buf=(char*)malloc(_tl+1);memcpy(_buf,a.datos,a.longitud);memcpy(_buf+a.longitud,b.datos,b.longitud);_buf[_tl]=0;CadenaSegura _r={.longitud=_tl,.datos=_buf};return _r;}
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
struct Programa parsear(CadenaSegura fuente);
void _expr_a_c(struct Nodo nodo, CadenaSegura buf);
void _visitar_nodo(struct Nodo nodo, Canal out);
void _visitar_lista(struct ListaNodo lista, Canal out);
void _visitar_programa(struct Programa programa, Canal out);
int generar(struct Programa programa, CadenaSegura ruta);
CadenaSegura _traducir_tipo_c(CadenaSegura tipo_synapse);
void volcar_ast(struct Nodo nodo, int nivel);
void ejecutar_dump(CadenaSegura ruta);
void principal();
typedef struct Token {
    int tipo;
    CadenaSegura lexema;
    int linea;
    int columna;
} Token;
static inline struct Token Token_nuevo() {
    struct Token _r={0}; return _r;
}
typedef struct Nodo {
    CadenaSegura tipo;
} Nodo;
static inline struct Nodo Nodo_nuevo() {
    struct Nodo _r={0}; return _r;
}
typedef struct ListaNodo {
    struct Nodo* cabeza;
    struct ListaNodo* cola;
} ListaNodo;
static inline struct ListaNodo ListaNodo_nuevo() {
    struct ListaNodo _r={0}; return _r;
}
typedef struct Programa {
    CadenaSegura tipo;
    struct ListaNodo* sentencias;
} Programa;
static inline struct Programa Programa_nuevo() {
    struct Programa _r={0}; return _r;
}
typedef struct Identificador {
    CadenaSegura tipo;
    CadenaSegura nombre;
} Identificador;
static inline struct Identificador Identificador_nuevo() {
    struct Identificador _r={0}; return _r;
}
typedef struct LiteralNumero {
    CadenaSegura tipo;
    int valor;
} LiteralNumero;
static inline struct LiteralNumero LiteralNumero_nuevo() {
    struct LiteralNumero _r={0}; return _r;
}
typedef struct LiteralCadena {
    CadenaSegura tipo;
    CadenaSegura valor;
} LiteralCadena;
static inline struct LiteralCadena LiteralCadena_nuevo() {
    struct LiteralCadena _r={0}; return _r;
}
typedef struct OpBinaria {
    CadenaSegura tipo;
    struct Nodo* izquierdo;
    struct Token* operador;
    struct Nodo* derecho;
} OpBinaria;
static inline struct OpBinaria OpBinaria_nuevo() {
    struct OpBinaria _r={0}; return _r;
}
typedef struct OpUnaria {
    CadenaSegura tipo;
    struct Token* operador;
    struct Nodo* expr;
} OpUnaria;
static inline struct OpUnaria OpUnaria_nuevo() {
    struct OpUnaria _r={0}; return _r;
}
typedef struct LlamadaFuncion {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct ListaNodo* argumentos;
} LlamadaFuncion;
static inline struct LlamadaFuncion LlamadaFuncion_nuevo() {
    struct LlamadaFuncion _r={0}; return _r;
}
typedef struct ExprAccesoCampo {
    CadenaSegura tipo;
    struct Nodo* objeto;
    CadenaSegura nombre_campo;
} ExprAccesoCampo;
static inline struct ExprAccesoCampo ExprAccesoCampo_nuevo() {
    struct ExprAccesoCampo _r={0}; return _r;
}
typedef struct AsignacionVariable {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct Nodo* expresion;
} AsignacionVariable;
static inline struct AsignacionVariable AsignacionVariable_nuevo() {
    struct AsignacionVariable _r={0}; return _r;
}
typedef struct AsignacionCampo {
    CadenaSegura tipo;
    struct Nodo* objeto;
    CadenaSegura nombre_campo;
    struct Nodo* expresion;
} AsignacionCampo;
static inline struct AsignacionCampo AsignacionCampo_nuevo() {
    struct AsignacionCampo _r={0}; return _r;
}
typedef struct SentenciaSi {
    CadenaSegura tipo;
    struct Nodo* condicion;
    struct ListaNodo* cuerpo;
    struct ListaNodo* cuerpo_sino;
} SentenciaSi;
static inline struct SentenciaSi SentenciaSi_nuevo() {
    struct SentenciaSi _r={0}; return _r;
}
typedef struct SentenciaMientras {
    CadenaSegura tipo;
    struct Nodo* condicion;
    struct ListaNodo* cuerpo;
} SentenciaMientras;
static inline struct SentenciaMientras SentenciaMientras_nuevo() {
    struct SentenciaMientras _r={0}; return _r;
}
typedef struct SentenciaRetornar {
    CadenaSegura tipo;
    struct Nodo* expr;
} SentenciaRetornar;
static inline struct SentenciaRetornar SentenciaRetornar_nuevo() {
    struct SentenciaRetornar _r={0}; return _r;
}
typedef struct SentenciaExpr {
    CadenaSegura tipo;
    struct Nodo* expr;
} SentenciaExpr;
static inline struct SentenciaExpr SentenciaExpr_nuevo() {
    struct SentenciaExpr _r={0}; return _r;
}
typedef struct LogLlamada {
    CadenaSegura tipo;
    struct ListaNodo* argumentos;
} LogLlamada;
static inline struct LogLlamada LogLlamada_nuevo() {
    struct LogLlamada _r={0}; return _r;
}
typedef struct Parametro {
    CadenaSegura tipo;
    CadenaSegura nombre;
    CadenaSegura tipo_param;
    int es_transferencia;
} Parametro;
static inline struct Parametro Parametro_nuevo() {
    struct Parametro _r={0}; return _r;
}
typedef struct ListaParametro {
    struct Parametro* cabeza;
    struct ListaParametro* cola;
} ListaParametro;
static inline struct ListaParametro ListaParametro_nuevo() {
    struct ListaParametro _r={0}; return _r;
}
typedef struct DefinicionFuncion {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct ListaParametro* parametros;
    CadenaSegura tipo_retorno;
    struct ListaNodo* cuerpo;
} DefinicionFuncion;
static inline struct DefinicionFuncion DefinicionFuncion_nuevo() {
    struct DefinicionFuncion _r={0}; return _r;
}
typedef struct DefinicionEstructura {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct ListaParametro* campos;
} DefinicionEstructura;
static inline struct DefinicionEstructura DefinicionEstructura_nuevo() {
    struct DefinicionEstructura _r={0}; return _r;
}
typedef struct SentenciaRomper {
    CadenaSegura tipo;
} SentenciaRomper;
static inline struct SentenciaRomper SentenciaRomper_nuevo() {
    struct SentenciaRomper _r={0}; return _r;
}
typedef struct SentenciaSiguiente {
    CadenaSegura tipo;
} SentenciaSiguiente;
static inline struct SentenciaSiguiente SentenciaSiguiente_nuevo() {
    struct SentenciaSiguiente _r={0}; return _r;
}
typedef struct SentenciaLanzar {
    CadenaSegura tipo;
    struct Nodo* llamada;
} SentenciaLanzar;
static inline struct SentenciaLanzar SentenciaLanzar_nuevo() {
    struct SentenciaLanzar _r={0}; return _r;
}
typedef struct SentenciaRecuperar {
    CadenaSegura tipo;
    struct Nodo* accion_critica;
    struct Nodo* plan_b;
} SentenciaRecuperar;
static inline struct SentenciaRecuperar SentenciaRecuperar_nuevo() {
    struct SentenciaRecuperar _r={0}; return _r;
}
typedef struct SentenciaEscuchar {
    CadenaSegura tipo;
    struct Nodo* canal;
    struct Nodo* respuesta;
} SentenciaEscuchar;
static inline struct SentenciaEscuchar SentenciaEscuchar_nuevo() {
    struct SentenciaEscuchar _r={0}; return _r;
}
typedef struct ExprTensor {
    CadenaSegura tipo;
    struct Nodo* filas;
    struct Nodo* columnas;
} ExprTensor;
static inline struct ExprTensor ExprTensor_nuevo() {
    struct ExprTensor _r={0}; return _r;
}
typedef struct ExprIndice {
    CadenaSegura tipo;
    struct Nodo* expr;
    struct Nodo* indice;
} ExprIndice;
static inline struct ExprIndice ExprIndice_nuevo() {
    struct ExprIndice _r={0}; return _r;
}
typedef struct ArgumentoTransferido {
    CadenaSegura tipo;
    struct Nodo* expr;
} ArgumentoTransferido;
static inline struct ArgumentoTransferido ArgumentoTransferido_nuevo() {
    struct ArgumentoTransferido _r={0}; return _r;
}
typedef struct SentenciaImportar {
    CadenaSegura tipo;
    CadenaSegura ruta;
} SentenciaImportar;
static inline struct SentenciaImportar SentenciaImportar_nuevo() {
    struct SentenciaImportar _r={0}; return _r;
}
/* importar compiler.ast_nodes */
struct Programa parsear(CadenaSegura fuente)
{
    return (struct Programa){0};
}
/* importar compiler.ast_nodes */
void _expr_a_c(struct Nodo nodo, CadenaSegura buf)
{
    return;
}
void _visitar_nodo(struct Nodo nodo, Canal out)
{
    return;
}
void _visitar_lista(struct ListaNodo lista, Canal out)
{
    return;
}
void _visitar_programa(struct Programa programa, Canal out)
{
    return;
}
int generar(struct Programa programa, CadenaSegura ruta)
{
    return (int){0};
}
CadenaSegura _traducir_tipo_c(CadenaSegura tipo_synapse)
{
    return tipo_synapse;
}
/* importar compiler.ast_nodes */
void volcar_ast(struct Nodo nodo, int nivel)
{
    return;
}
void ejecutar_dump(CadenaSegura ruta)
{
    return;
}
void principal()
{
    if ((_argc() < 2)) {
        printf("%s\n",(CadenaSegura){.longitud=36,.datos="Uso: main <archivo.syn> [--dump-ast]"});
        salir(1);
    }
    CadenaSegura ruta = _argv(1);
    int modo_dump = (_argc() >= 3);
    if (modo_dump) {
        ejecutar_dump(ruta);
        salir(0);
    }
    printf("%s %s\n",(CadenaSegura){.longitud=11,.datos="Compilando:"}, ruta);
    Canal canal = abrir((CadenaSegura){.longitud=32,.datos="librerias/compiler/ast_nodes.syn"}, (CadenaSegura){.longitud=1,.datos="r"});
    CadenaSegura lib_ast = leer(canal);
    cerrar(canal);
    canal = abrir((CadenaSegura){.longitud=29,.datos="librerias/compiler/parser.syn"}, (CadenaSegura){.longitud=1,.datos="r"});
    CadenaSegura lib_parse = leer(canal);
    cerrar(canal);
    canal = abrir((CadenaSegura){.longitud=32,.datos="librerias/compiler/generator.syn"}, (CadenaSegura){.longitud=1,.datos="r"});
    CadenaSegura lib_gen = leer(canal);
    cerrar(canal);
    canal = abrir((CadenaSegura){.longitud=20,.datos="librerias/std/io.syn"}, (CadenaSegura){.longitud=1,.datos="r"});
    CadenaSegura lib_io = leer(canal);
    cerrar(canal);
    canal = abrir((CadenaSegura){.longitud=22,.datos="librerias/std/math.syn"}, (CadenaSegura){.longitud=1,.datos="r"});
    CadenaSegura lib_math = leer(canal);
    cerrar(canal);
    canal = abrir((CadenaSegura){.longitud=21,.datos="librerias/std/mem.syn"}, (CadenaSegura){.longitud=1,.datos="r"});
    CadenaSegura lib_mem = leer(canal);
    cerrar(canal);
    canal = abrir(ruta, (CadenaSegura){.longitud=1,.datos="r"});
    CadenaSegura fuente = leer(canal);
    cerrar(canal);
    CadenaSegura fuente_completa = concat(concat(concat(concat(concat(concat(lib_ast, lib_parse), lib_gen), lib_io), lib_math), lib_mem), fuente);
    struct Programa programa = parsear(fuente_completa);
    int errores = generar(programa, ruta);
    if ((errores > 0)) {
        printf("%s %s %s\n",(CadenaSegura){.longitud=6,.datos="Error:"}, errores, (CadenaSegura){.longitud=8,.datos="fallo(s)"});
        salir(errores);
    }
    printf("%s %s\n",(CadenaSegura){.longitud=3,.datos="OK:"}, ruta);
}
int main(int argc, char** argv) {
    int _g_argc=argc;
    char** _g_argv=argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    principal();
    synapse_esperar_hilos();
    return 0;
}
