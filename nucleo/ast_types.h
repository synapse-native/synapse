// cumple Manual 2 4: tipos AST
// cumple Manual 8 4: toolchain
// ast_types.h — Tipos de estructuras del AST orientado a objetos (Synapse)
// Generado a partir de hola.c. NO modificar manualmente.
#ifndef AST_TYPES_H
#define AST_TYPES_H

// --- Forward declarations ---
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
struct LiteralNulo;
struct ConstructorTipo;
struct DeclaracionTipo;

// --- Struct definitions ---
typedef struct Token {
    int tipo;
    CadenaSegura lexema;
    int linea;
    int columna;
} Token;

typedef struct Nodo {
    CadenaSegura tipo;
} Nodo;

typedef struct ListaNodo {
    struct Nodo* cabeza;
    struct ListaNodo* cola;
} ListaNodo;

typedef struct Programa {
    CadenaSegura tipo;
    struct ListaNodo* sentencias;
} Programa;

typedef struct Identificador {
    CadenaSegura tipo;
    CadenaSegura nombre;
} Identificador;

typedef struct LiteralNumero {
    CadenaSegura tipo;
    int valor;
} LiteralNumero;

typedef struct LiteralCadena {
    CadenaSegura tipo;
    CadenaSegura valor;
} LiteralCadena;

typedef struct OpBinaria {
    CadenaSegura tipo;
    struct Nodo* izquierdo;
    struct Token* operador;
    struct Nodo* derecho;
} OpBinaria;

typedef struct OpUnaria {
    CadenaSegura tipo;
    struct Token* operador;
    struct Nodo* expr;
} OpUnaria;

typedef struct LlamadaFuncion {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct ListaNodo* argumentos;
} LlamadaFuncion;

typedef struct ExprAccesoCampo {
    CadenaSegura tipo;
    struct Nodo* objeto;
    CadenaSegura nombre_campo;
} ExprAccesoCampo;

typedef struct AsignacionVariable {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct Nodo* expresion;
} AsignacionVariable;

typedef struct AsignacionCampo {
    CadenaSegura tipo;
    struct Nodo* objeto;
    CadenaSegura nombre_campo;
    struct Nodo* expresion;
} AsignacionCampo;

typedef struct SentenciaSi {
    CadenaSegura tipo;
    struct Nodo* condicion;
    struct ListaNodo* cuerpo;
    struct ListaNodo* cuerpo_sino;
} SentenciaSi;

typedef struct SentenciaMientras {
    CadenaSegura tipo;
    struct Nodo* condicion;
    struct ListaNodo* cuerpo;
} SentenciaMientras;

typedef struct SentenciaRetornar {
    CadenaSegura tipo;
    struct Nodo* expr;
} SentenciaRetornar;

typedef struct SentenciaExpr {
    CadenaSegura tipo;
    struct Nodo* expr;
} SentenciaExpr;

typedef struct LogLlamada {
    CadenaSegura tipo;
    struct ListaNodo* argumentos;
} LogLlamada;

typedef struct Parametro {
    CadenaSegura tipo;
    CadenaSegura nombre;
    CadenaSegura tipo_param;
    int es_transferencia;
} Parametro;

typedef struct ListaParametro {
    struct Parametro* cabeza;
    struct ListaParametro* cola;
} ListaParametro;

typedef struct DefinicionFuncion {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct ListaParametro* parametros;
    CadenaSegura tipo_retorno;
    struct ListaNodo* cuerpo;
} DefinicionFuncion;

typedef struct DefinicionEstructura {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct ListaParametro* campos;
} DefinicionEstructura;

typedef struct SentenciaRomper {
    CadenaSegura tipo;
} SentenciaRomper;

typedef struct SentenciaSiguiente {
    CadenaSegura tipo;
} SentenciaSiguiente;

typedef struct SentenciaLanzar {
    CadenaSegura tipo;
    struct Nodo* llamada;
} SentenciaLanzar;

typedef struct SentenciaRecuperar {
    CadenaSegura tipo;
    struct Nodo* accion_critica;
    struct Nodo* plan_b;
} SentenciaRecuperar;

typedef struct SentenciaEscuchar {
    CadenaSegura tipo;
    struct Nodo* canal;
    struct Nodo* respuesta;
} SentenciaEscuchar;

typedef struct ExprTensor {
    CadenaSegura tipo;
    struct Nodo* filas;
    struct Nodo* columnas;
} ExprTensor;

typedef struct ExprIndice {
    CadenaSegura tipo;
    struct Nodo* expr;
    struct Nodo* indice;
} ExprIndice;

typedef struct ArgumentoTransferido {
    CadenaSegura tipo;
    struct Nodo* expr;
} ArgumentoTransferido;

typedef struct SentenciaImportar {
    CadenaSegura tipo;
    CadenaSegura ruta;
} SentenciaImportar;

typedef struct ImportarC {
    CadenaSegura tipo;
    CadenaSegura ruta;
    int es_sistema;
} ImportarC;

typedef struct DeclaracionExterna {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct Parametro* parametros;
    CadenaSegura tipo_retorno;
} DeclaracionExterna;

typedef struct BloqueInseguro {
    CadenaSegura tipo;
    struct Nodo* cuerpo;
} BloqueInseguro;

typedef struct ExprObtenerDireccion {
    CadenaSegura tipo;
    struct Nodo* expr;
} ExprObtenerDireccion;

typedef struct ExprDereferencia {
    CadenaSegura tipo;
    struct Nodo* expr;
} ExprDereferencia;

typedef struct LiteralNulo {
    CadenaSegura tipo;
} LiteralNulo;

typedef struct ConstructorTipo {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct ListaNodo* tipos;
} ConstructorTipo;

typedef struct DeclaracionTipo {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct ListaNodo* parametros_tipo;
    CadenaSegura tipo_base;
    struct ListaNodo* constructores;
} DeclaracionTipo;

#endif // AST_TYPES_H
