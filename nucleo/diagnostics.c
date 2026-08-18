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

struct ReporteError;
struct GestorDiagnostico;

struct GestorDiagnostico gestor_nuevo(CadenaSegura idioma, CadenaSegura ruta, int capacidad);
void reportar_error(struct GestorDiagnostico diag, int codigo, int linea, int columna, CadenaSegura mensaje);
int hay_errores(struct GestorDiagnostico diag);
int contar_errores(struct GestorDiagnostico diag);
int codigo_salida(struct GestorDiagnostico diag);
CadenaSegura resumen_errores(struct GestorDiagnostico diag);
CadenaSegura obtener_plantilla_error(int codigo, CadenaSegura idioma);
CadenaSegura obtener_linea_contexto(CadenaSegura lineas, int linea_num);
CadenaSegura formatear_entrada_error(CadenaSegura ruta, int linea, int columna, CadenaSegura mensaje);
CadenaSegura formatear_ubicacion(CadenaSegura ruta, int linea, int columna);

#define ERR_SYNTAX_EXPECTED_TOKEN (1)
#define ERR_SYNTAX_UNEXPECTED_TOKEN (2)
#define ERR_SYNTAX_UNEXPECTED_EXPR (3)
#define ERR_SYNTAX_EXPECTED_NEWLINE (4)
#define ERR_LANG_MISSING (5)
#define ERR_LANG_UNSUPPORTED (6)
#define ERR_INDENT_INVALID (7)
#define ERR_INDENT_INCONSISTENT (8)
#define ERR_STRING_UNCLOSED (9)
#define ERR_LEX_CHAR_UNEXPECTED (10)
#define ERR_LEX (11)
#define ERR_FILE_NOT_FOUND (12)
#define ERR_CANONICAL_FORMAT (13)
#define ERR_SEM_VAR_NO_DECLARADA (14)
#define ERR_SEM_TIPO_INCOMPATIBLE (15)
#define ERR_SEM_TIPO_RETORNO (16)
#define ERR_SEM_FUNC_NO_DEFINIDA (17)
#define ERR_SEM_REDEFINICION (18)
#define ERR_SEM_ARGUMENTOS_INVALIDOS (19)
#define ERR_SEM_ESTRUCTURA_NO_DEFINIDA (20)
#define ERR_SEM_CAMPO_NO_EXISTE (21)
#define ERR_SEM_VAR_MOVIDA (22)
#define ERR_SEM_ACCESO_MEMORIA_MOVIDA (23)
#define ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR (24)
#define ERR_MANIFEST_NOT_FOUND (25)
#define ERR_MODULE_STD_NOT_FOUND (26)
#define ERR_MODULE_AXON_NOT_FOUND (27)
#define ERR_DEP_NOT_DECLARED (28)
#define ERR_LOCK_HASH_MISMATCH (29)
#define ERR_GIT_FAILURE (30)
#define ERR_SEM_ASM_FUERA_INSEGURO (31)
#define ERR_SEM_CONSTANTE_INMUTABLE (32)
typedef struct ReporteError {
    int codigo;
    int linea;
    int columna;
    CadenaSegura mensaje;
} ReporteError;

static inline struct ReporteError ReporteError_nuevo() {
    struct ReporteError _r = {0};
    return _r;
}

typedef struct GestorDiagnostico {
    struct ReporteError* reportes;
    int total_reportes;
    int capacidad;
    CadenaSegura idioma;
    CadenaSegura ruta_archivo;
} GestorDiagnostico;

static inline struct GestorDiagnostico GestorDiagnostico_nuevo() {
    struct GestorDiagnostico _r = {0};
    return _r;
}

struct GestorDiagnostico gestor_nuevo(CadenaSegura idioma, CadenaSegura ruta, int capacidad) {
    struct GestorDiagnostico g = GestorDiagnostico_nuevo();
    g.idioma = idioma;
    g.ruta_archivo = ruta;
    g.total_reportes = 0;
    g.capacidad = capacidad;
    struct GestorDiagnostico _ret_58 = g;
    return _ret_58;
}

void reportar_error(struct GestorDiagnostico diag, int codigo, int linea, int columna, CadenaSegura mensaje) {
    { /* unsafe */
        if (diag.total_reportes >= diag.capacidad) return;
        diag.reportes[diag.total_reportes].codigo = codigo;
        diag.reportes[diag.total_reportes].linea = linea;
        diag.reportes[diag.total_reportes].columna = columna;
        diag.total_reportes = diag.total_reportes + 1;
    }
}

int hay_errores(struct GestorDiagnostico diag) {
    if ((diag.total_reportes > 0)) {
        int _ret_73 = 1;
        return _ret_73;
    }
    int _ret_74 = 0;
    return _ret_74;
}

int contar_errores(struct GestorDiagnostico diag) {
    int _ret_77 = diag.total_reportes;
    return _ret_77;
}

int codigo_salida(struct GestorDiagnostico diag) {
    if ((hay_errores(diag) == 1)) {
        int _ret_81 = 1;
        return _ret_81;
    }
    int _ret_82 = 0;
    return _ret_82;
}

CadenaSegura resumen_errores(struct GestorDiagnostico diag) {
    if ((hay_errores(diag) == 0)) {
        CadenaSegura _ret_86 = (CadenaSegura){ .longitud = 9, .datos = "0 errores" };
        return _ret_86;
    }
    CadenaSegura r = (CadenaSegura){ .longitud = 0, .datos = "" };
    { /* unsafe */
        // resumen: N error(es) encontrado(s);
        r = (diag.total_reportes == 1) ? "1 error encontrado" : "2 errores encontrados";
        { char _buf[64]; snprintf(_buf, 64, "%d errores encontrados", diag.total_reportes); r = _buf; };
    }
    CadenaSegura _ret_92 = r;
    return _ret_92;
}

CadenaSegura obtener_plantilla_error(int codigo, CadenaSegura idioma) {
    if ((strcmp(idioma.datos, (CadenaSegura){ .longitud = 2, .datos = "es" }.datos) == 0)) {
        if ((codigo == ERR_SYNTAX_EXPECTED_TOKEN)) {
            CadenaSegura _ret_98 = (CadenaSegura){ .longitud = 50, .datos = "Se esperaba {esperado}, se encontro '{encontrado}'" };
            return _ret_98;
        }
        if ((codigo == ERR_SYNTAX_UNEXPECTED_TOKEN)) {
            CadenaSegura _ret_100 = (CadenaSegura){ .longitud = 44, .datos = "Token inesperado '{tok_name}' tras expresion" };
            return _ret_100;
        }
        if ((codigo == ERR_SYNTAX_UNEXPECTED_EXPR)) {
            CadenaSegura _ret_102 = (CadenaSegura){ .longitud = 30, .datos = "Expresion inesperada: '{tipo}'" };
            return _ret_102;
        }
        if ((codigo == ERR_SYNTAX_EXPECTED_NEWLINE)) {
            CadenaSegura _ret_104 = (CadenaSegura){ .longitud = 51, .datos = "Se esperaba nueva linea despues de '{construccion}'" };
            return _ret_104;
        }
        if ((codigo == ERR_LANG_MISSING)) {
            CadenaSegura _ret_106 = (CadenaSegura){ .longitud = 59, .datos = "Falta declaracion de idioma '#lang: <codigo>' en la linea 1" };
            return _ret_106;
        }
        if ((codigo == ERR_LANG_UNSUPPORTED)) {
            CadenaSegura _ret_108 = (CadenaSegura){ .longitud = 30, .datos = "Idioma '{idioma}' no soportado" };
            return _ret_108;
        }
        if ((codigo == ERR_INDENT_INVALID)) {
            CadenaSegura _ret_110 = (CadenaSegura){ .longitud = 46, .datos = "La indentacion debe ser multiplo de 4 espacios" };
            return _ret_110;
        }
        if ((codigo == ERR_INDENT_INCONSISTENT)) {
            CadenaSegura _ret_112 = (CadenaSegura){ .longitud = 34, .datos = "Nivel de indentacion inconsistente" };
            return _ret_112;
        }
        if ((codigo == ERR_STRING_UNCLOSED)) {
            CadenaSegura _ret_114 = (CadenaSegura){ .longitud = 17, .datos = "Cadena sin cerrar" };
            return _ret_114;
        }
        if ((codigo == ERR_LEX)) {
            CadenaSegura _ret_116 = (CadenaSegura){ .longitud = 9, .datos = "{mensaje}" };
            return _ret_116;
        }
        if ((codigo == ERR_LEX_CHAR_UNEXPECTED)) {
            CadenaSegura _ret_118 = (CadenaSegura){ .longitud = 28, .datos = "Caracter inesperado '{char}'" };
            return _ret_118;
        }
        if ((codigo == ERR_FILE_NOT_FOUND)) {
            CadenaSegura _ret_120 = (CadenaSegura){ .longitud = 32, .datos = "Archivo no encontrado: {archivo}" };
            return _ret_120;
        }
        if ((codigo == ERR_CANONICAL_FORMAT)) {
            CadenaSegura _ret_122 = (CadenaSegura){ .longitud = 41, .datos = "Formato canonico no reconocido o corrupto" };
            return _ret_122;
        }
        if ((codigo == ERR_SEM_VAR_NO_DECLARADA)) {
            CadenaSegura _ret_124 = (CadenaSegura){ .longitud = 47, .datos = "Variable '{nombre}' no declarada en este ambito" };
            return _ret_124;
        }
        if ((codigo == ERR_SEM_TIPO_INCOMPATIBLE)) {
            CadenaSegura _ret_126 = (CadenaSegura){ .longitud = 78, .datos = "Tipos incompatibles: no se puede usar '{tipo1}' con '{tipo2}' en '{operacion}'" };
            return _ret_126;
        }
        if ((codigo == ERR_SEM_TIPO_RETORNO)) {
            CadenaSegura _ret_128 = (CadenaSegura){ .longitud = 76, .datos = "Tipo de retorno incorrecto: se esperaba '{esperado}', se obtuvo '{obtenido}'" };
            return _ret_128;
        }
        if ((codigo == ERR_SEM_FUNC_NO_DEFINIDA)) {
            CadenaSegura _ret_130 = (CadenaSegura){ .longitud = 30, .datos = "Funcion '{nombre}' no definida" };
            return _ret_130;
        }
        if ((codigo == ERR_SEM_REDEFINICION)) {
            CadenaSegura _ret_132 = (CadenaSegura){ .longitud = 45, .datos = "Redefinicion de '{nombre}' en el mismo ambito" };
            return _ret_132;
        }
        if ((codigo == ERR_SEM_ARGUMENTOS_INVALIDOS)) {
            CadenaSegura _ret_134 = (CadenaSegura){ .longitud = 73, .datos = "Cantidad de argumentos invalida para '{nombre}': se esperaban {esperados}" };
            return _ret_134;
        }
        if ((codigo == ERR_SEM_ESTRUCTURA_NO_DEFINIDA)) {
            CadenaSegura _ret_136 = (CadenaSegura){ .longitud = 33, .datos = "Estructura '{nombre}' no definida" };
            return _ret_136;
        }
        if ((codigo == ERR_SEM_CAMPO_NO_EXISTE)) {
            CadenaSegura _ret_138 = (CadenaSegura){ .longitud = 52, .datos = "La estructura '{struct}' no tiene un campo '{campo}'" };
            return _ret_138;
        }
        if ((codigo == ERR_SEM_VAR_MOVIDA)) {
            CadenaSegura _ret_140 = (CadenaSegura){ .longitud = 43, .datos = "Uso ilegal de variable ya movida '{nombre}'" };
            return _ret_140;
        }
        if ((codigo == ERR_SEM_ACCESO_MEMORIA_MOVIDA)) {
            CadenaSegura _ret_142 = (CadenaSegura){ .longitud = 44, .datos = "Acceso prohibido a memoria movida '{nombre}'" };
            return _ret_142;
        }
        if ((codigo == ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR)) {
            CadenaSegura _ret_144 = (CadenaSegura){ .longitud = 36, .datos = "Resultado de canal sin desempaquetar" };
            return _ret_144;
        }
        if ((codigo == ERR_MANIFEST_NOT_FOUND)) {
            CadenaSegura _ret_146 = (CadenaSegura){ .longitud = 58, .datos = "Manifiesto axon.toml no encontrado en el directorio actual" };
            return _ret_146;
        }
        if ((codigo == ERR_MODULE_STD_NOT_FOUND)) {
            CadenaSegura _ret_148 = (CadenaSegura){ .longitud = 58, .datos = "Modulo estandar '{modulo}' no encontrado. Sysroot corrupto" };
            return _ret_148;
        }
        if ((codigo == ERR_MODULE_AXON_NOT_FOUND)) {
            CadenaSegura _ret_150 = (CadenaSegura){ .longitud = 52, .datos = "Dependencia '{modulo}' no encontrada en axon_modules" };
            return _ret_150;
        }
        if ((codigo == ERR_DEP_NOT_DECLARED)) {
            CadenaSegura _ret_152 = (CadenaSegura){ .longitud = 76, .datos = "Dependencia '{modulo}' importada en el codigo pero no declarada en axon.toml" };
            return _ret_152;
        }
        if ((codigo == ERR_LOCK_HASH_MISMATCH)) {
            CadenaSegura _ret_154 = (CadenaSegura){ .longitud = 62, .datos = "El hash de la dependencia '{modulo}' no coincide con axon.lock" };
            return _ret_154;
        }
        if ((codigo == ERR_GIT_FAILURE)) {
            CadenaSegura _ret_156 = (CadenaSegura){ .longitud = 67, .datos = "Error de red o revision Git invalida para la dependencia '{modulo}'" };
            return _ret_156;
        }
        if ((codigo == ERR_SEM_ASM_FUERA_INSEGURO)) {
            CadenaSegura _ret_158 = (CadenaSegura){ .longitud = 55, .datos = "asm() solo puede usarse dentro de un bloque 'inseguro:'" };
            return _ret_158;
        }
        if ((codigo == ERR_SEM_CONSTANTE_INMUTABLE)) {
            CadenaSegura _ret_160 = (CadenaSegura){ .longitud = 45, .datos = "No se puede reasignar la constante '{nombre}'" };
            return _ret_160;
        }
        CadenaSegura _ret_161 = (CadenaSegura){ .longitud = 17, .datos = "Error desconocido" };
        return _ret_161;
    }
    if ((codigo == ERR_SYNTAX_EXPECTED_TOKEN)) {
        CadenaSegura _ret_164 = (CadenaSegura){ .longitud = 41, .datos = "Expected {esperado}, found '{encontrado}'" };
        return _ret_164;
    }
    if ((codigo == ERR_SYNTAX_UNEXPECTED_TOKEN)) {
        CadenaSegura _ret_166 = (CadenaSegura){ .longitud = 46, .datos = "Unexpected token '{tok_name}' after expression" };
        return _ret_166;
    }
    if ((codigo == ERR_SYNTAX_UNEXPECTED_EXPR)) {
        CadenaSegura _ret_168 = (CadenaSegura){ .longitud = 31, .datos = "Unexpected expression: '{tipo}'" };
        return _ret_168;
    }
    if ((codigo == ERR_SYNTAX_EXPECTED_NEWLINE)) {
        CadenaSegura _ret_170 = (CadenaSegura){ .longitud = 39, .datos = "Expected newline after '{construccion}'" };
        return _ret_170;
    }
    if ((codigo == ERR_LANG_MISSING)) {
        CadenaSegura _ret_172 = (CadenaSegura){ .longitud = 54, .datos = "Missing language declaration '#lang: <code>' at line 1" };
        return _ret_172;
    }
    if ((codigo == ERR_LANG_UNSUPPORTED)) {
        CadenaSegura _ret_174 = (CadenaSegura){ .longitud = 33, .datos = "Language '{idioma}' not supported" };
        return _ret_174;
    }
    if ((codigo == ERR_INDENT_INVALID)) {
        CadenaSegura _ret_176 = (CadenaSegura){ .longitud = 42, .datos = "Indentation must be a multiple of 4 spaces" };
        return _ret_176;
    }
    if ((codigo == ERR_INDENT_INCONSISTENT)) {
        CadenaSegura _ret_178 = (CadenaSegura){ .longitud = 30, .datos = "Inconsistent indentation level" };
        return _ret_178;
    }
    if ((codigo == ERR_STRING_UNCLOSED)) {
        CadenaSegura _ret_180 = (CadenaSegura){ .longitud = 23, .datos = "Unclosed string literal" };
        return _ret_180;
    }
    if ((codigo == ERR_LEX)) {
        CadenaSegura _ret_182 = (CadenaSegura){ .longitud = 9, .datos = "{mensaje}" };
        return _ret_182;
    }
    if ((codigo == ERR_LEX_CHAR_UNEXPECTED)) {
        CadenaSegura _ret_184 = (CadenaSegura){ .longitud = 29, .datos = "Unexpected character '{char}'" };
        return _ret_184;
    }
    if ((codigo == ERR_FILE_NOT_FOUND)) {
        CadenaSegura _ret_186 = (CadenaSegura){ .longitud = 25, .datos = "File not found: {archivo}" };
        return _ret_186;
    }
    if ((codigo == ERR_CANONICAL_FORMAT)) {
        CadenaSegura _ret_188 = (CadenaSegura){ .longitud = 42, .datos = "Unrecognized or corrupted canonical format" };
        return _ret_188;
    }
    if ((codigo == ERR_SEM_VAR_NO_DECLARADA)) {
        CadenaSegura _ret_190 = (CadenaSegura){ .longitud = 46, .datos = "Variable '{nombre}' not declared in this scope" };
        return _ret_190;
    }
    if ((codigo == ERR_SEM_TIPO_INCOMPATIBLE)) {
        CadenaSegura _ret_192 = (CadenaSegura){ .longitud = 72, .datos = "Incompatible types: cannot use '{tipo1}' with '{tipo2}' in '{operacion}'" };
        return _ret_192;
    }
    if ((codigo == ERR_SEM_TIPO_RETORNO)) {
        CadenaSegura _ret_194 = (CadenaSegura){ .longitud = 62, .datos = "Incorrect return type: expected '{esperado}', got '{obtenido}'" };
        return _ret_194;
    }
    if ((codigo == ERR_SEM_FUNC_NO_DEFINIDA)) {
        CadenaSegura _ret_196 = (CadenaSegura){ .longitud = 31, .datos = "Function '{nombre}' not defined" };
        return _ret_196;
    }
    if ((codigo == ERR_SEM_REDEFINICION)) {
        CadenaSegura _ret_198 = (CadenaSegura){ .longitud = 44, .datos = "Redefinition of '{nombre}' in the same scope" };
        return _ret_198;
    }
    if ((codigo == ERR_SEM_ARGUMENTOS_INVALIDOS)) {
        CadenaSegura _ret_200 = (CadenaSegura){ .longitud = 59, .datos = "Invalid argument count for '{nombre}': expected {esperados}" };
        return _ret_200;
    }
    if ((codigo == ERR_SEM_ESTRUCTURA_NO_DEFINIDA)) {
        CadenaSegura _ret_202 = (CadenaSegura){ .longitud = 29, .datos = "Struct '{nombre}' not defined" };
        return _ret_202;
    }
    if ((codigo == ERR_SEM_CAMPO_NO_EXISTE)) {
        CadenaSegura _ret_204 = (CadenaSegura){ .longitud = 40, .datos = "Struct '{struct}' has no field '{campo}'" };
        return _ret_204;
    }
    if ((codigo == ERR_SEM_VAR_MOVIDA)) {
        CadenaSegura _ret_206 = (CadenaSegura){ .longitud = 48, .datos = "Illegal use of already moved variable '{nombre}'" };
        return _ret_206;
    }
    if ((codigo == ERR_SEM_ACCESO_MEMORIA_MOVIDA)) {
        CadenaSegura _ret_208 = (CadenaSegura){ .longitud = 43, .datos = "Forbidden access to moved memory '{nombre}'" };
        return _ret_208;
    }
    if ((codigo == ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR)) {
        CadenaSegura _ret_210 = (CadenaSegura){ .longitud = 23, .datos = "Unpacked channel result" };
        return _ret_210;
    }
    if ((codigo == ERR_MANIFEST_NOT_FOUND)) {
        CadenaSegura _ret_212 = (CadenaSegura){ .longitud = 49, .datos = "axon.toml manifest not found in current directory" };
        return _ret_212;
    }
    if ((codigo == ERR_MODULE_STD_NOT_FOUND)) {
        CadenaSegura _ret_214 = (CadenaSegura){ .longitud = 53, .datos = "Standard module '{modulo}' not found. Corrupt Sysroot" };
        return _ret_214;
    }
    if ((codigo == ERR_MODULE_AXON_NOT_FOUND)) {
        CadenaSegura _ret_216 = (CadenaSegura){ .longitud = 47, .datos = "Dependency '{modulo}' not found in axon_modules" };
        return _ret_216;
    }
    if ((codigo == ERR_DEP_NOT_DECLARED)) {
        CadenaSegura _ret_218 = (CadenaSegura){ .longitud = 68, .datos = "Dependency '{modulo}' imported in code but not declared in axon.toml" };
        return _ret_218;
    }
    if ((codigo == ERR_LOCK_HASH_MISMATCH)) {
        CadenaSegura _ret_220 = (CadenaSegura){ .longitud = 54, .datos = "Hash of dependency '{modulo}' does not match axon.lock" };
        return _ret_220;
    }
    if ((codigo == ERR_GIT_FAILURE)) {
        CadenaSegura _ret_222 = (CadenaSegura){ .longitud = 63, .datos = "Network error or invalid Git revision for dependency '{modulo}'" };
        return _ret_222;
    }
    if ((codigo == ERR_SEM_ASM_FUERA_INSEGURO)) {
        CadenaSegura _ret_224 = (CadenaSegura){ .longitud = 48, .datos = "asm() can only be used inside an 'unsafe:' block" };
        return _ret_224;
    }
    if ((codigo == ERR_SEM_CONSTANTE_INMUTABLE)) {
        CadenaSegura _ret_226 = (CadenaSegura){ .longitud = 35, .datos = "Cannot reassign constant '{nombre}'" };
        return _ret_226;
    }
    CadenaSegura _ret_227 = (CadenaSegura){ .longitud = 13, .datos = "Unknown error" };
    return _ret_227;
}

CadenaSegura obtener_linea_contexto(CadenaSegura lineas, int linea_num) {
    CadenaSegura r = (CadenaSegura){ .longitud = 0, .datos = "" };
    { /* unsafe */
        // buscar linea_num en buffer de lineas (pendiente);
    }
    CadenaSegura _ret_234 = r;
    return _ret_234;
}

CadenaSegura formatear_entrada_error(CadenaSegura ruta, int linea, int columna, CadenaSegura mensaje) {
    CadenaSegura r = (CadenaSegura){ .longitud = 0, .datos = "" };
    { /* unsafe */
        { char _buf[1024]; snprintf(_buf, 1024, "[Synapse] %s:%d:%d - %s", ruta, linea, columna, mensaje); r = _buf; };
    }
    CadenaSegura _ret_241 = r;
    return _ret_241;
}

CadenaSegura formatear_ubicacion(CadenaSegura ruta, int linea, int columna) {
    if ((linea > 0)) {
        CadenaSegura r = (CadenaSegura){ .longitud = 0, .datos = "" };
        { /* unsafe */
            { char _buf[256]; snprintf(_buf, 256, "%s:%d:%d", ruta, linea, columna); r = _buf; };
        }
        CadenaSegura _ret_249 = r;
        return _ret_249;
    }
    CadenaSegura _ret_250 = ruta;
    return _ret_250;
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    synapse_esperar_hilos();
    return 0;
}