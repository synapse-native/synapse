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

typedef struct { int es_ok; union {
void* ok_valor; const char* err_mensaje;
} datos; } Resultado_T;
typedef struct CanalConcurrencia CanalConcurrencia;
extern CanalConcurrencia* canal_crear(uint32_t capacidad);
extern void canal_enviar(CanalConcurrencia* canal, void* paquete);
extern void* canal_recibir(CanalConcurrencia* canal);
extern void canal_destruir(CanalConcurrencia* canal);
extern void cerrar_canal(CanalConcurrencia* canal);
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

struct TokenLex;
struct LexerEstado;
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
struct DeclaracionVariable;
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
struct BloqueInseguro;
struct ExprObtenerDireccion;
struct ExprDereferencia;
struct ImportarC;
struct DeclaracionExterna;
struct ExprCrearCanal;
struct SentenciaEnviarCanal;
struct ExprRecibirCanal;
struct ReporteError;
struct GestorDiagnostico;
struct TokenExt;
struct NodoAST;
struct ParserEst;
struct Simbolo;
struct TablaSimbolos;
struct SemNodo;
struct SemSimbolo;
struct SemTablaSimbolos;
struct SemEstructuraInfo;
struct AnalizadorSemanticoEst;
struct GeneradorCEst;
struct DepNoDeclaradaError;
struct ResultadoEtapa;

typedef struct TokenLex {
    int tipo;
    int linea;
    int columna;
    CadenaSegura valor;
} TokenLex;

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
    int hay_error;
    CadenaSegura error_mensaje;
    int error_linea;
    int error_columna;
} LexerEstado;

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

typedef struct DeclaracionVariable {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct Nodo* expresion;
    int linea;
    int columna;
} DeclaracionVariable;

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
    struct ListaNodo* requiere;
    struct ListaNodo* garantiza;
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

typedef struct BloqueInseguro {
    CadenaSegura tipo;
    struct ListaNodo* cuerpo;
} BloqueInseguro;

typedef struct ExprObtenerDireccion {
    CadenaSegura tipo;
    struct Nodo* expr;
} ExprObtenerDireccion;

typedef struct ExprDereferencia {
    CadenaSegura tipo;
    struct Nodo* expr;
} ExprDereferencia;

typedef struct ImportarC {
    CadenaSegura tipo;
    CadenaSegura ruta;
    int es_sistema;
} ImportarC;

typedef struct DeclaracionExterna {
    CadenaSegura tipo;
    CadenaSegura nombre;
    struct ListaParametro* parametros;
    CadenaSegura tipo_retorno;
} DeclaracionExterna;

typedef struct ExprCrearCanal {
    CadenaSegura tipo;
    CadenaSegura tipo_contenido;
    struct Nodo* capacidad;
} ExprCrearCanal;

typedef struct SentenciaEnviarCanal {
    CadenaSegura tipo;
    struct Nodo* canal;
    struct Nodo* valor;
} SentenciaEnviarCanal;

typedef struct ExprRecibirCanal {
    CadenaSegura tipo;
    struct Nodo* canal;
} ExprRecibirCanal;

typedef struct ReporteError {
    int codigo;
    int linea;
    int columna;
    CadenaSegura mensaje;
} ReporteError;

typedef struct GestorDiagnostico {
    struct ReporteError* reportes;
    int total_reportes;
    int capacidad;
    CadenaSegura idioma;
    CadenaSegura ruta_archivo;
} GestorDiagnostico;

typedef struct TokenExt {
    int tipo;
    int linea;
    int columna;
    int ptr_valor;
    int len_valor;
} TokenExt;

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
    int ptr_hi;
    int max_nodos;
} ParserEst;

typedef struct Simbolo {
    CadenaSegura nombre;
    CadenaSegura tipo;
    struct Nodo* nodo;
    int nivel_ambito;
    int propiedad;
    int es_constante;
    CadenaSegura uri;
    int linea;
    int columna;
} Simbolo;

typedef struct TablaSimbolos {
    struct Simbolo* entradas;
    int total_entradas;
    int nivel_actual;
} TablaSimbolos;

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

typedef struct GeneradorCEst {
    int buf_lineas;
    int buf_capacidad;
    int buf_longitud;
    int indent_actual;
    int contador_thread;
    int contador_listener;
    int funciones_emitidas;
    CadenaSegura func_emitidas_nombres;
    CadenaSegura func_return_types_nombres;
    CadenaSegura func_return_types_tipos;
    int func_return_types_total;
    int in_function_scope;
    CadenaSegura var_nombres;
    CadenaSegura var_tipos;
    int var_total;
    int var_capacidad;
    CadenaSegura const_types_nombres;
    CadenaSegura const_types_tipos;
    int const_types_total;
    CadenaSegura scope_var_nombres;
    CadenaSegura scope_var_tipos;
    int scope_var_total;
    int scope_stack_top;
    int scope_stack_at;
    CadenaSegura tensor_vars;
    int tensor_vars_total;
    CadenaSegura tensor_transferidas;
    int tensor_transferidas_total;
    CadenaSegura canal_vars;
    int canal_vars_total;
    CadenaSegura canal_cerradas;
    int canal_cerradas_total;
    CadenaSegura listener_funciones;
    int listener_total;
    CadenaSegura struct_nombres;
    int struct_total;
    CadenaSegura struct_nombres_c;
    int struct_total_c;
    CadenaSegura extern_nombres;
    CadenaSegura extern_params;
    int extern_total;
    CadenaSegura dtor_tipos;
    CadenaSegura dtor_funcs;
    int dtor_total;
    int gen_tok_emitido;
    int gen_parse_emitido;
    int gen_defs_emitido;
    CadenaSegura garantizas_nombres;
    CadenaSegura garantizas_valores;
    int garantizas_total;
    int es_no_std;
    CadenaSegura linker_libs;
    int linker_libs_total;
    CadenaSegura build_buf;
    CadenaSegura func_retorno_actual;
    CadenaSegura strings_heap;
    int strings_heap_total;
} GeneradorCEst;

typedef struct DepNoDeclaradaError {
    CadenaSegura mensaje;
} DepNoDeclaradaError;

typedef struct ResultadoEtapa {
    int tag;
    union {
        int valor;
    } dato;
} ResultadoEtapa;

int str_len(CadenaSegura s);
int str_char(CadenaSegura s, int i);
int str_char_at(int ptr, int i);
int str_eq(CadenaSegura a, CadenaSegura b);
int str_len_ptr(int ptr);
int keyword_token(CadenaSegura palabra);
int es_digito(int c);
int es_letra(int c);
int es_alnum(int c);
void lexer_push_token(struct LexerEstado lex, int tipo, int linea, int columna);
void lexer_error(struct LexerEstado lex, CadenaSegura mensaje, int linea, int columna);
void lexer_detectar_idioma(struct LexerEstado lex);
void lexer_procesar_indentacion(struct LexerEstado lex, int ptr_linea, int len_linea);
void lexer_tokenizar_linea(struct LexerEstado lex, int ptr_texto, int len_texto);
int tokenizar(CadenaSegura fuente);
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
int parsear_crear_canal(struct ParserEst est);
int parsear_recibir_canal(struct ParserEst est);
struct Programa parsear(CadenaSegura fuente);
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
void traducir_tipo_c(void* tipo_synapse);
CadenaSegura aplicar_coercion(void* expr_c, void* tipo_origen, void* tipo_destino, int linea);
CadenaSegura prim_int_to_ptr(void* valor);
CadenaSegura prim_float_to_ptr(void* valor);
CadenaSegura syn_malloc(struct GeneradorCEst est, void* size_expr);
CadenaSegura syn_calloc(struct GeneradorCEst est, void* n_expr, void* size_expr);
CadenaSegura syn_free(struct GeneradorCEst est, void* ptr_expr);
CadenaSegura syn_pool_alloc(struct GeneradorCEst est, void* size_expr);
CadenaSegura syn_pool_free(struct GeneradorCEst est, void* ptr_expr);
int gen_find_var(struct GeneradorCEst est, void* nombre);
void gen_add_var(struct GeneradorCEst est, void* nombre, void* tipo);
void gen_set_var_type(struct GeneradorCEst est, int idx, void* tipo);
void gen_agregar_return_type(struct GeneradorCEst est, void* nombre, void* tipo);
CadenaSegura gen_func_return_type(struct GeneradorCEst est, void* nombre);
void gen_agregar_struct_c(struct GeneradorCEst est, void* nombre);
void gen_emitir_linea(struct GeneradorCEst est, void* linea);
void gen_emitir_nueva_linea(struct GeneradorCEst est);
void gen_escribir_cadena_escapada(struct GeneradorCEst est, void* str);
void gen_emitir_token_defs(struct GeneradorCEst est);
CadenaSegura gen_obtener_salida(struct GeneradorCEst est);
void gen_visitar_nodo(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_bloque_lista(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_funcion(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_si(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_mientras(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_retornar(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_expr_stmt(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_asignacion(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_declaracion(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_estructura(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_constante(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_externo(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_log(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_asm(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_asignacion_campo(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_lanzar(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_recuperar(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_escuchar(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_enviar_canal(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_para(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_visitar_coincidir(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_expr_a_c(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx, void* buf, int bufsz);
void gen_tipo_de_expr(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx);
void gen_emitir_tokenizar_c(struct GeneradorCEst est);
void gen_emitir_parsear_c(struct GeneradorCEst est);
void gen_emitir_generar_c(struct GeneradorCEst est);
void gen_emitir_volcar_ast_c(struct GeneradorCEst est);
void gen_push_scope(struct GeneradorCEst est);
void gen_pop_scope(struct GeneradorCEst est);
void gen_emit_all_destructors(struct GeneradorCEst est, void* exclude_var);
int generar(struct Programa programa, CadenaSegura ruta);
CadenaSegura buscar_en(CadenaSegura dir_base, CadenaSegura ruta_import);
CadenaSegura resolver(CadenaSegura ruta_import, CadenaSegura dir_base, CadenaSegura dependencias_nombres, CadenaSegura dependencias_valores, int total_dependencias);
struct ResultadoEtapa etapa_ok(void);
int fallo_etapa(int cod);
CadenaSegura argv_str(int i);
struct ResultadoEtapa generar_etapa(CadenaSegura ruta, CadenaSegura salida);
int principal(void);

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
int str_len(CadenaSegura s) {
    int r;
    { /* unsafe */
        r = 0;
        r = s.longitud;
        int _ret_75 = r;
        return _ret_75;
    }
}

int str_char(CadenaSegura s, int i) {
    int r;
    { /* unsafe */
        r = 0;
        r = (i >= 0 && i < s.longitud) ? (unsigned char)s.datos[i] : 0;
        int _ret_81 = r;
        return _ret_81;
    }
}

int str_char_at(int ptr, int i) {
    int r;
    { /* unsafe */
        r = 0;
        r = (unsigned char)((const char*)ptr)[i];
        int _ret_87 = r;
        return _ret_87;
    }
}

int str_eq(CadenaSegura a, CadenaSegura b) {
    int r;
    { /* unsafe */
        r = 0;
        if (a.longitud != b.longitud) { r = 0; } else { r = 1; for (int _si = 0; _si < a.longitud; _si++) { if (a.datos[_si] != b.datos[_si]) { r = 0; break; } } };
        int _ret_93 = r;
        return _ret_93;
    }
}

int str_len_ptr(int ptr) {
    int r;
    { /* unsafe */
        r = 0;
        r = (int)strlen((const char*)ptr);
        int _ret_99 = r;
        return _ret_99;
    }
}

int keyword_token(CadenaSegura palabra) {
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("si"), .datos = "si" }) == 1)) {
        int _ret_104 = T_IF;
        return _ret_104;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("sino"), .datos = "sino" }) == 1)) {
        int _ret_106 = T_ELSE;
        return _ret_106;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("funcion"), .datos = "funcion" }) == 1)) {
        int _ret_108 = T_FUNCION;
        return _ret_108;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("retornar"), .datos = "retornar" }) == 1)) {
        int _ret_110 = T_RETORNAR;
        return _ret_110;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("lanzar"), .datos = "lanzar" }) == 1)) {
        int _ret_112 = T_LANZAR;
        return _ret_112;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("recuperar"), .datos = "recuperar" }) == 1)) {
        int _ret_114 = T_RECUPERAR;
        return _ret_114;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("escuchar"), .datos = "escuchar" }) == 1)) {
        int _ret_116 = T_ESCUCHAR;
        return _ret_116;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("mientras"), .datos = "mientras" }) == 1)) {
        int _ret_118 = T_MIENTRAS;
        return _ret_118;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("importar"), .datos = "importar" }) == 1)) {
        int _ret_120 = T_IMPORTAR;
        return _ret_120;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("romper"), .datos = "romper" }) == 1)) {
        int _ret_122 = T_ROMPER;
        return _ret_122;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("siguiente"), .datos = "siguiente" }) == 1)) {
        int _ret_124 = T_SIGUIENTE;
        return _ret_124;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("estructura"), .datos = "estructura" }) == 1)) {
        int _ret_126 = T_ESTRUCTURA;
        return _ret_126;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("y"), .datos = "y" }) == 1)) {
        int _ret_128 = T_Y;
        return _ret_128;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("o"), .datos = "o" }) == 1)) {
        int _ret_130 = T_O;
        return _ret_130;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("no"), .datos = "no" }) == 1)) {
        int _ret_132 = T_NO;
        return _ret_132;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("verdadero"), .datos = "verdadero" }) == 1)) {
        int _ret_134 = T_VERDADERO;
        return _ret_134;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("falso"), .datos = "falso" }) == 1)) {
        int _ret_136 = T_FALSO;
        return _ret_136;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("inseguro"), .datos = "inseguro" }) == 1)) {
        int _ret_138 = T_INSEGURO;
        return _ret_138;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("importar_c"), .datos = "importar_c" }) == 1)) {
        int _ret_140 = T_IMPORTAR_C;
        return _ret_140;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("externo"), .datos = "externo" }) == 1)) {
        int _ret_142 = T_EXTERNO;
        return _ret_142;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("coincidir"), .datos = "coincidir" }) == 1)) {
        int _ret_144 = T_COINCIDIR;
        return _ret_144;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("requiere"), .datos = "requiere" }) == 1)) {
        int _ret_146 = T_REQUIERE;
        return _ret_146;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("garantiza"), .datos = "garantiza" }) == 1)) {
        int _ret_148 = T_GARANTIZA;
        return _ret_148;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("canal"), .datos = "canal" }) == 1)) {
        int _ret_150 = T_CANAL;
        return _ret_150;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("asm"), .datos = "asm" }) == 1)) {
        int _ret_152 = T_ASM;
        return _ret_152;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("constante"), .datos = "constante" }) == 1)) {
        int _ret_154 = T_CONSTANTE;
        return _ret_154;
    }
    if ((str_eq(palabra, (CadenaSegura){ .longitud = (int)strlen("para"), .datos = "para" }) == 1)) {
        int _ret_156 = T_PARA;
        return _ret_156;
    }
    int _ret_157 = 0;
    return _ret_157;
}

int es_digito(int c) {
    if ((c >= 48)) {
        if ((c <= 57)) {
            int _ret_163 = 1;
            return _ret_163;
        }
    }
    int _ret_164 = 0;
    return _ret_164;
}

int es_letra(int c) {
    if ((c >= 65)) {
        if ((c <= 90)) {
            int _ret_169 = 1;
            return _ret_169;
        }
    }
    if ((c >= 97)) {
        if ((c <= 122)) {
            int _ret_172 = 1;
            return _ret_172;
        }
    }
    if ((c == 95)) {
        int _ret_174 = 1;
        return _ret_174;
    }
    int _ret_175 = 0;
    return _ret_175;
}

int es_alnum(int c) {
    if ((es_digito(c) == 1)) {
        int _ret_179 = 1;
        return _ret_179;
    }
    if ((es_letra(c) == 1)) {
        int _ret_181 = 1;
        return _ret_181;
    }
    int _ret_182 = 0;
    return _ret_182;
}

#define MAX_TOKENS (16384)
#define MAX_INDENT (64)
void lexer_push_token(struct LexerEstado lex, int tipo, int linea, int columna) {
    { /* unsafe */
        if (lex.total_tokens >= 16384) return;
        lex.tokens[lex.total_tokens].tipo = tipo;
        lex.tokens[lex.total_tokens].linea = linea;
        lex.tokens[lex.total_tokens].columna = columna;
        lex.total_tokens = lex.total_tokens + 1;
    }
}

void lexer_error(struct LexerEstado lex, CadenaSegura mensaje, int linea, int columna) {
    lex.hay_error = 1;
    lex.error_mensaje = mensaje;
    lex.error_linea = linea;
    lex.error_columna = columna;
}

void lexer_detectar_idioma(struct LexerEstado lex) {
    int r;
    { /* unsafe */
        r = 0;
        r = (lex.len_fuente >= 7 && ((const char*)lex.ptr_fuente)[0] == '#' && ((const char*)lex.ptr_fuente)[1] == 'l' && ((const char*)lex.ptr_fuente)[2] == 'a' && ((const char*)lex.ptr_fuente)[3] == 'n' && ((const char*)lex.ptr_fuente)[4] == 'g' && ((const char*)lex.ptr_fuente)[5] == ':') ? 1 : 0;
        if ((r == 0)) {
            lexer_error(lex, (CadenaSegura){ .longitud = (int)strlen("Falta declaracion de idioma #lang: en la linea 1"), .datos = "Falta declaracion de idioma #lang: en la linea 1" }, 1, 0);
        }
    }
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
            }
        }
        if (((espacios % 4) != 0)) {
            lexer_error(lex, (CadenaSegura){ .longitud = (int)strlen("Indentacion debe ser multiplo de 4 espacios"), .datos = "Indentacion debe ser multiplo de 4 espacios" }, lex.linea_actual, 0);
            return;
        }
        nivel = (espacios / 4);
        tope = 0;
        tope = (lex.nivel_pila > 0) ? lex.pila_indent[lex.nivel_pila - 1] : 0;
        if ((nivel > tope)) {
            lex.pila_indent[lex.nivel_pila] = nivel;
            lex.nivel_pila = lex.nivel_pila + 1;
            lexer_push_token(lex, T_INDENTAR, lex.linea_actual, 0);
        }
        if ((nivel < tope)) {
            while ((nivel < tope)) {
                lex.nivel_pila = lex.nivel_pila - 1;
                tope = (lex.nivel_pila > 0) ? lex.pila_indent[lex.nivel_pila - 1] : 0;
                lexer_push_token(lex, T_DESINDENTAR, lex.linea_actual, 0);
            }
        }
    }
}

void lexer_tokenizar_linea(struct LexerEstado lex, int ptr_texto, int len_texto) {
    int i;
    int r;
    int c;
    i = 0;
    r = 1;
    while ((r == 1)) {
        { /* unsafe */
            r = (i < len_texto) ? 1 : 0;
            if ((r == 0)) {
                break;
            }
            c = 0;
            c = (unsigned char)((const char*)ptr_texto)[i];
            if ((c == 32)) {
                i = i + 1;
                continue;
            }
            if ((c == 47)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 47)) {
                        return;
                    }
                }
            }
            if ((c == 34)) {
                i = i + 1;
                while ((i < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i];
                    if ((c == 92)) {
                        i = i + 1;
                    }
                    else {
                        if ((c == 34)) {
                            break;
                        }
                    }
                    i = i + 1;
                }
                i = i + 1;
                continue;
            }
            if ((c == 39)) {
                i = i + 1;
                while ((i < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i];
                    if ((c == 92)) {
                        i = i + 1;
                    }
                    else {
                        if ((c == 39)) {
                            break;
                        }
                    }
                    i = i + 1;
                }
                i = i + 1;
                continue;
            }
            if ((c >= 48)) {
                if ((c <= 57)) {
                    while ((i < len_texto)) {
                        c = (unsigned char)((const char*)ptr_texto)[i];
                        if ((c < 48)) {
                            break;
                        }
                        if ((c > 57)) {
                            break;
                        }
                        i = i + 1;
                    }
                    continue;
                }
            }
            if ((es_letra(c) == 1)) {
                while ((i < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i];
                    if ((es_alnum(c) == 0)) {
                        if ((c != 95)) {
                            break;
                        }
                    }
                    i = i + 1;
                }
                continue;
            }
            if ((c == 43)) {
                lexer_push_token(lex, T_MAS, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 45)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 62)) {
                        lexer_push_token(lex, T_FLECHA, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                    }
                    if ((c == 60)) {
                        lexer_push_token(lex, T_FLECHA_IZQ, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                    }
                }
                lexer_push_token(lex, T_MENOS, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 61)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 62)) {
                        lexer_push_token(lex, T_FLECHA_DER, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                    }
                    if ((c == 61)) {
                        lexer_push_token(lex, T_IGUAL, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                    }
                }
                lexer_push_token(lex, T_ASIGNAR, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 33)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 61)) {
                        lexer_push_token(lex, T_DISTINTO, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                    }
                }
                i = i + 1;
                continue;
            }
            if ((c == 60)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 61)) {
                        lexer_push_token(lex, T_MENOR_IGUAL, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                    }
                }
                lexer_push_token(lex, T_MENOR, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 62)) {
                if (((i + 1) < len_texto)) {
                    c = (unsigned char)((const char*)ptr_texto)[i + 1];
                    if ((c == 61)) {
                        lexer_push_token(lex, T_MAYOR_IGUAL, lex.linea_actual, (i + 1));
                        i = i + 2;
                        continue;
                    }
                }
                lexer_push_token(lex, T_MAYOR, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 42)) {
                lexer_push_token(lex, T_POR, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 47)) {
                lexer_push_token(lex, T_DIV, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 37)) {
                lexer_push_token(lex, T_MOD, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 40)) {
                lexer_push_token(lex, T_PAREN_IZQ, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 41)) {
                lexer_push_token(lex, T_PAREN_DER, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 58)) {
                lexer_push_token(lex, T_DOSPUNTOS, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 44)) {
                lexer_push_token(lex, T_COMA, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 46)) {
                lexer_push_token(lex, T_PUNTO, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 38)) {
                lexer_push_token(lex, T_AMPERSAND, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            if ((c == 59)) {
                lexer_push_token(lex, T_PUNTOCOMA, lex.linea_actual, (i + 1));
                i = i + 1;
                continue;
            }
            lexer_error(lex, (CadenaSegura){ .longitud = (int)strlen("Caracter inesperado"), .datos = "Caracter inesperado" }, lex.linea_actual, (i + 1));
            i = i + 1;
        }
        continue;
    }
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
struct GestorDiagnostico gestor_nuevo(CadenaSegura idioma, CadenaSegura ruta, int capacidad) {
    struct GestorDiagnostico g;
    g = (struct GestorDiagnostico){0};
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
        CadenaSegura _ret_86 = (CadenaSegura){ .longitud = (int)strlen("0 errores"), .datos = "0 errores" };
        return _ret_86;
    }
    CadenaSegura _ret_87 = concat(entero_a_texto(diag.total_reportes), (CadenaSegura){ .longitud = (int)strlen(" error(es) encontrado(s)"), .datos = " error(es) encontrado(s)" });
    return _ret_87;
}

CadenaSegura obtener_plantilla_error(int codigo, CadenaSegura idioma) {
    if ((str_eq(idioma, (CadenaSegura){ .longitud = (int)strlen("es"), .datos = "es" }) == 1)) {
        if ((codigo == ERR_SYNTAX_EXPECTED_TOKEN)) {
            CadenaSegura _ret_93 = (CadenaSegura){ .longitud = (int)strlen("Se esperaba {esperado}, se encontro '{encontrado}'"), .datos = "Se esperaba {esperado}, se encontro '{encontrado}'" };
            return _ret_93;
        }
        if ((codigo == ERR_SYNTAX_UNEXPECTED_TOKEN)) {
            CadenaSegura _ret_95 = (CadenaSegura){ .longitud = (int)strlen("Token inesperado '{tok_name}' tras expresion"), .datos = "Token inesperado '{tok_name}' tras expresion" };
            return _ret_95;
        }
        if ((codigo == ERR_SYNTAX_UNEXPECTED_EXPR)) {
            CadenaSegura _ret_97 = (CadenaSegura){ .longitud = (int)strlen("Expresion inesperada: '{tipo}'"), .datos = "Expresion inesperada: '{tipo}'" };
            return _ret_97;
        }
        if ((codigo == ERR_SYNTAX_EXPECTED_NEWLINE)) {
            CadenaSegura _ret_99 = (CadenaSegura){ .longitud = (int)strlen("Se esperaba nueva linea despues de '{construccion}'"), .datos = "Se esperaba nueva linea despues de '{construccion}'" };
            return _ret_99;
        }
        if ((codigo == ERR_LANG_MISSING)) {
            CadenaSegura _ret_101 = (CadenaSegura){ .longitud = (int)strlen("Falta declaracion de idioma '#lang: <codigo>' en la linea 1"), .datos = "Falta declaracion de idioma '#lang: <codigo>' en la linea 1" };
            return _ret_101;
        }
        if ((codigo == ERR_LANG_UNSUPPORTED)) {
            CadenaSegura _ret_103 = (CadenaSegura){ .longitud = (int)strlen("Idioma '{idioma}' no soportado"), .datos = "Idioma '{idioma}' no soportado" };
            return _ret_103;
        }
        if ((codigo == ERR_INDENT_INVALID)) {
            CadenaSegura _ret_105 = (CadenaSegura){ .longitud = (int)strlen("La indentacion debe ser multiplo de 4 espacios"), .datos = "La indentacion debe ser multiplo de 4 espacios" };
            return _ret_105;
        }
        if ((codigo == ERR_INDENT_INCONSISTENT)) {
            CadenaSegura _ret_107 = (CadenaSegura){ .longitud = (int)strlen("Nivel de indentacion inconsistente"), .datos = "Nivel de indentacion inconsistente" };
            return _ret_107;
        }
        if ((codigo == ERR_STRING_UNCLOSED)) {
            CadenaSegura _ret_109 = (CadenaSegura){ .longitud = (int)strlen("Cadena sin cerrar"), .datos = "Cadena sin cerrar" };
            return _ret_109;
        }
        if ((codigo == ERR_LEX)) {
            CadenaSegura _ret_111 = (CadenaSegura){ .longitud = (int)strlen("{mensaje}"), .datos = "{mensaje}" };
            return _ret_111;
        }
        if ((codigo == ERR_LEX_CHAR_UNEXPECTED)) {
            CadenaSegura _ret_113 = (CadenaSegura){ .longitud = (int)strlen("Caracter inesperado '{char}'"), .datos = "Caracter inesperado '{char}'" };
            return _ret_113;
        }
        if ((codigo == ERR_FILE_NOT_FOUND)) {
            CadenaSegura _ret_115 = (CadenaSegura){ .longitud = (int)strlen("Archivo no encontrado: {archivo}"), .datos = "Archivo no encontrado: {archivo}" };
            return _ret_115;
        }
        if ((codigo == ERR_CANONICAL_FORMAT)) {
            CadenaSegura _ret_117 = (CadenaSegura){ .longitud = (int)strlen("Formato canonico no reconocido o corrupto"), .datos = "Formato canonico no reconocido o corrupto" };
            return _ret_117;
        }
        if ((codigo == ERR_SEM_VAR_NO_DECLARADA)) {
            CadenaSegura _ret_119 = (CadenaSegura){ .longitud = (int)strlen("Variable '{nombre}' no declarada en este ambito"), .datos = "Variable '{nombre}' no declarada en este ambito" };
            return _ret_119;
        }
        if ((codigo == ERR_SEM_TIPO_INCOMPATIBLE)) {
            CadenaSegura _ret_121 = (CadenaSegura){ .longitud = (int)strlen("Tipos incompatibles: no se puede usar '{tipo1}' con '{tipo2}' en '{operacion}'"), .datos = "Tipos incompatibles: no se puede usar '{tipo1}' con '{tipo2}' en '{operacion}'" };
            return _ret_121;
        }
        if ((codigo == ERR_SEM_TIPO_RETORNO)) {
            CadenaSegura _ret_123 = (CadenaSegura){ .longitud = (int)strlen("Tipo de retorno incorrecto: se esperaba '{esperado}', se obtuvo '{obtenido}'"), .datos = "Tipo de retorno incorrecto: se esperaba '{esperado}', se obtuvo '{obtenido}'" };
            return _ret_123;
        }
        if ((codigo == ERR_SEM_FUNC_NO_DEFINIDA)) {
            CadenaSegura _ret_125 = (CadenaSegura){ .longitud = (int)strlen("Funcion '{nombre}' no definida"), .datos = "Funcion '{nombre}' no definida" };
            return _ret_125;
        }
        if ((codigo == ERR_SEM_REDEFINICION)) {
            CadenaSegura _ret_127 = (CadenaSegura){ .longitud = (int)strlen("Redefinicion de '{nombre}' en el mismo ambito"), .datos = "Redefinicion de '{nombre}' en el mismo ambito" };
            return _ret_127;
        }
        if ((codigo == ERR_SEM_ARGUMENTOS_INVALIDOS)) {
            CadenaSegura _ret_129 = (CadenaSegura){ .longitud = (int)strlen("Cantidad de argumentos invalida para '{nombre}': se esperaban {esperados}"), .datos = "Cantidad de argumentos invalida para '{nombre}': se esperaban {esperados}" };
            return _ret_129;
        }
        if ((codigo == ERR_SEM_ESTRUCTURA_NO_DEFINIDA)) {
            CadenaSegura _ret_131 = (CadenaSegura){ .longitud = (int)strlen("Estructura '{nombre}' no definida"), .datos = "Estructura '{nombre}' no definida" };
            return _ret_131;
        }
        if ((codigo == ERR_SEM_CAMPO_NO_EXISTE)) {
            CadenaSegura _ret_133 = (CadenaSegura){ .longitud = (int)strlen("La estructura '{struct}' no tiene un campo '{campo}'"), .datos = "La estructura '{struct}' no tiene un campo '{campo}'" };
            return _ret_133;
        }
        if ((codigo == ERR_SEM_VAR_MOVIDA)) {
            CadenaSegura _ret_135 = (CadenaSegura){ .longitud = (int)strlen("Uso ilegal de variable ya movida '{nombre}'"), .datos = "Uso ilegal de variable ya movida '{nombre}'" };
            return _ret_135;
        }
        if ((codigo == ERR_SEM_ACCESO_MEMORIA_MOVIDA)) {
            CadenaSegura _ret_137 = (CadenaSegura){ .longitud = (int)strlen("Acceso prohibido a memoria movida '{nombre}'"), .datos = "Acceso prohibido a memoria movida '{nombre}'" };
            return _ret_137;
        }
        if ((codigo == ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR)) {
            CadenaSegura _ret_139 = (CadenaSegura){ .longitud = (int)strlen("Resultado de canal sin desempaquetar"), .datos = "Resultado de canal sin desempaquetar" };
            return _ret_139;
        }
        if ((codigo == ERR_MANIFEST_NOT_FOUND)) {
            CadenaSegura _ret_141 = (CadenaSegura){ .longitud = (int)strlen("Manifiesto axon.toml no encontrado en el directorio actual"), .datos = "Manifiesto axon.toml no encontrado en el directorio actual" };
            return _ret_141;
        }
        if ((codigo == ERR_MODULE_STD_NOT_FOUND)) {
            CadenaSegura _ret_143 = (CadenaSegura){ .longitud = (int)strlen("Modulo estandar '{modulo}' no encontrado. Sysroot corrupto"), .datos = "Modulo estandar '{modulo}' no encontrado. Sysroot corrupto" };
            return _ret_143;
        }
        if ((codigo == ERR_MODULE_AXON_NOT_FOUND)) {
            CadenaSegura _ret_145 = (CadenaSegura){ .longitud = (int)strlen("Dependencia '{modulo}' no encontrada en axon_modules"), .datos = "Dependencia '{modulo}' no encontrada en axon_modules" };
            return _ret_145;
        }
        if ((codigo == ERR_DEP_NOT_DECLARED)) {
            CadenaSegura _ret_147 = (CadenaSegura){ .longitud = (int)strlen("Dependencia '{modulo}' importada en el codigo pero no declarada en axon.toml"), .datos = "Dependencia '{modulo}' importada en el codigo pero no declarada en axon.toml" };
            return _ret_147;
        }
        if ((codigo == ERR_LOCK_HASH_MISMATCH)) {
            CadenaSegura _ret_149 = (CadenaSegura){ .longitud = (int)strlen("El hash de la dependencia '{modulo}' no coincide con axon.lock"), .datos = "El hash de la dependencia '{modulo}' no coincide con axon.lock" };
            return _ret_149;
        }
        if ((codigo == ERR_GIT_FAILURE)) {
            CadenaSegura _ret_151 = (CadenaSegura){ .longitud = (int)strlen("Error de red o revision Git invalida para la dependencia '{modulo}'"), .datos = "Error de red o revision Git invalida para la dependencia '{modulo}'" };
            return _ret_151;
        }
        if ((codigo == ERR_SEM_ASM_FUERA_INSEGURO)) {
            CadenaSegura _ret_153 = (CadenaSegura){ .longitud = (int)strlen("asm() solo puede usarse dentro de un bloque 'inseguro:'"), .datos = "asm() solo puede usarse dentro de un bloque 'inseguro:'" };
            return _ret_153;
        }
        if ((codigo == ERR_SEM_CONSTANTE_INMUTABLE)) {
            CadenaSegura _ret_155 = (CadenaSegura){ .longitud = (int)strlen("No se puede reasignar la constante '{nombre}'"), .datos = "No se puede reasignar la constante '{nombre}'" };
            return _ret_155;
        }
        CadenaSegura _ret_156 = (CadenaSegura){ .longitud = (int)strlen("Error desconocido"), .datos = "Error desconocido" };
        return _ret_156;
    }
    if ((codigo == ERR_SYNTAX_EXPECTED_TOKEN)) {
        CadenaSegura _ret_159 = (CadenaSegura){ .longitud = (int)strlen("Expected {esperado}, found '{encontrado}'"), .datos = "Expected {esperado}, found '{encontrado}'" };
        return _ret_159;
    }
    if ((codigo == ERR_SYNTAX_UNEXPECTED_TOKEN)) {
        CadenaSegura _ret_161 = (CadenaSegura){ .longitud = (int)strlen("Unexpected token '{tok_name}' after expression"), .datos = "Unexpected token '{tok_name}' after expression" };
        return _ret_161;
    }
    if ((codigo == ERR_SYNTAX_UNEXPECTED_EXPR)) {
        CadenaSegura _ret_163 = (CadenaSegura){ .longitud = (int)strlen("Unexpected expression: '{tipo}'"), .datos = "Unexpected expression: '{tipo}'" };
        return _ret_163;
    }
    if ((codigo == ERR_SYNTAX_EXPECTED_NEWLINE)) {
        CadenaSegura _ret_165 = (CadenaSegura){ .longitud = (int)strlen("Expected newline after '{construccion}'"), .datos = "Expected newline after '{construccion}'" };
        return _ret_165;
    }
    if ((codigo == ERR_LANG_MISSING)) {
        CadenaSegura _ret_167 = (CadenaSegura){ .longitud = (int)strlen("Missing language declaration '#lang: <code>' at line 1"), .datos = "Missing language declaration '#lang: <code>' at line 1" };
        return _ret_167;
    }
    if ((codigo == ERR_LANG_UNSUPPORTED)) {
        CadenaSegura _ret_169 = (CadenaSegura){ .longitud = (int)strlen("Language '{idioma}' not supported"), .datos = "Language '{idioma}' not supported" };
        return _ret_169;
    }
    if ((codigo == ERR_INDENT_INVALID)) {
        CadenaSegura _ret_171 = (CadenaSegura){ .longitud = (int)strlen("Indentation must be a multiple of 4 spaces"), .datos = "Indentation must be a multiple of 4 spaces" };
        return _ret_171;
    }
    if ((codigo == ERR_INDENT_INCONSISTENT)) {
        CadenaSegura _ret_173 = (CadenaSegura){ .longitud = (int)strlen("Inconsistent indentation level"), .datos = "Inconsistent indentation level" };
        return _ret_173;
    }
    if ((codigo == ERR_STRING_UNCLOSED)) {
        CadenaSegura _ret_175 = (CadenaSegura){ .longitud = (int)strlen("Unclosed string literal"), .datos = "Unclosed string literal" };
        return _ret_175;
    }
    if ((codigo == ERR_LEX)) {
        CadenaSegura _ret_177 = (CadenaSegura){ .longitud = (int)strlen("{mensaje}"), .datos = "{mensaje}" };
        return _ret_177;
    }
    if ((codigo == ERR_LEX_CHAR_UNEXPECTED)) {
        CadenaSegura _ret_179 = (CadenaSegura){ .longitud = (int)strlen("Unexpected character '{char}'"), .datos = "Unexpected character '{char}'" };
        return _ret_179;
    }
    if ((codigo == ERR_FILE_NOT_FOUND)) {
        CadenaSegura _ret_181 = (CadenaSegura){ .longitud = (int)strlen("File not found: {archivo}"), .datos = "File not found: {archivo}" };
        return _ret_181;
    }
    if ((codigo == ERR_CANONICAL_FORMAT)) {
        CadenaSegura _ret_183 = (CadenaSegura){ .longitud = (int)strlen("Unrecognized or corrupted canonical format"), .datos = "Unrecognized or corrupted canonical format" };
        return _ret_183;
    }
    if ((codigo == ERR_SEM_VAR_NO_DECLARADA)) {
        CadenaSegura _ret_185 = (CadenaSegura){ .longitud = (int)strlen("Variable '{nombre}' not declared in this scope"), .datos = "Variable '{nombre}' not declared in this scope" };
        return _ret_185;
    }
    if ((codigo == ERR_SEM_TIPO_INCOMPATIBLE)) {
        CadenaSegura _ret_187 = (CadenaSegura){ .longitud = (int)strlen("Incompatible types: cannot use '{tipo1}' with '{tipo2}' in '{operacion}'"), .datos = "Incompatible types: cannot use '{tipo1}' with '{tipo2}' in '{operacion}'" };
        return _ret_187;
    }
    if ((codigo == ERR_SEM_TIPO_RETORNO)) {
        CadenaSegura _ret_189 = (CadenaSegura){ .longitud = (int)strlen("Incorrect return type: expected '{esperado}', got '{obtenido}'"), .datos = "Incorrect return type: expected '{esperado}', got '{obtenido}'" };
        return _ret_189;
    }
    if ((codigo == ERR_SEM_FUNC_NO_DEFINIDA)) {
        CadenaSegura _ret_191 = (CadenaSegura){ .longitud = (int)strlen("Function '{nombre}' not defined"), .datos = "Function '{nombre}' not defined" };
        return _ret_191;
    }
    if ((codigo == ERR_SEM_REDEFINICION)) {
        CadenaSegura _ret_193 = (CadenaSegura){ .longitud = (int)strlen("Redefinition of '{nombre}' in the same scope"), .datos = "Redefinition of '{nombre}' in the same scope" };
        return _ret_193;
    }
    if ((codigo == ERR_SEM_ARGUMENTOS_INVALIDOS)) {
        CadenaSegura _ret_195 = (CadenaSegura){ .longitud = (int)strlen("Invalid argument count for '{nombre}': expected {esperados}"), .datos = "Invalid argument count for '{nombre}': expected {esperados}" };
        return _ret_195;
    }
    if ((codigo == ERR_SEM_ESTRUCTURA_NO_DEFINIDA)) {
        CadenaSegura _ret_197 = (CadenaSegura){ .longitud = (int)strlen("Struct '{nombre}' not defined"), .datos = "Struct '{nombre}' not defined" };
        return _ret_197;
    }
    if ((codigo == ERR_SEM_CAMPO_NO_EXISTE)) {
        CadenaSegura _ret_199 = (CadenaSegura){ .longitud = (int)strlen("Struct '{struct}' has no field '{campo}'"), .datos = "Struct '{struct}' has no field '{campo}'" };
        return _ret_199;
    }
    if ((codigo == ERR_SEM_VAR_MOVIDA)) {
        CadenaSegura _ret_201 = (CadenaSegura){ .longitud = (int)strlen("Illegal use of already moved variable '{nombre}'"), .datos = "Illegal use of already moved variable '{nombre}'" };
        return _ret_201;
    }
    if ((codigo == ERR_SEM_ACCESO_MEMORIA_MOVIDA)) {
        CadenaSegura _ret_203 = (CadenaSegura){ .longitud = (int)strlen("Forbidden access to moved memory '{nombre}'"), .datos = "Forbidden access to moved memory '{nombre}'" };
        return _ret_203;
    }
    if ((codigo == ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR)) {
        CadenaSegura _ret_205 = (CadenaSegura){ .longitud = (int)strlen("Unpacked channel result"), .datos = "Unpacked channel result" };
        return _ret_205;
    }
    if ((codigo == ERR_MANIFEST_NOT_FOUND)) {
        CadenaSegura _ret_207 = (CadenaSegura){ .longitud = (int)strlen("axon.toml manifest not found in current directory"), .datos = "axon.toml manifest not found in current directory" };
        return _ret_207;
    }
    if ((codigo == ERR_MODULE_STD_NOT_FOUND)) {
        CadenaSegura _ret_209 = (CadenaSegura){ .longitud = (int)strlen("Standard module '{modulo}' not found. Corrupt Sysroot"), .datos = "Standard module '{modulo}' not found. Corrupt Sysroot" };
        return _ret_209;
    }
    if ((codigo == ERR_MODULE_AXON_NOT_FOUND)) {
        CadenaSegura _ret_211 = (CadenaSegura){ .longitud = (int)strlen("Dependency '{modulo}' not found in axon_modules"), .datos = "Dependency '{modulo}' not found in axon_modules" };
        return _ret_211;
    }
    if ((codigo == ERR_DEP_NOT_DECLARED)) {
        CadenaSegura _ret_213 = (CadenaSegura){ .longitud = (int)strlen("Dependency '{modulo}' imported in code but not declared in axon.toml"), .datos = "Dependency '{modulo}' imported in code but not declared in axon.toml" };
        return _ret_213;
    }
    if ((codigo == ERR_LOCK_HASH_MISMATCH)) {
        CadenaSegura _ret_215 = (CadenaSegura){ .longitud = (int)strlen("Hash of dependency '{modulo}' does not match axon.lock"), .datos = "Hash of dependency '{modulo}' does not match axon.lock" };
        return _ret_215;
    }
    if ((codigo == ERR_GIT_FAILURE)) {
        CadenaSegura _ret_217 = (CadenaSegura){ .longitud = (int)strlen("Network error or invalid Git revision for dependency '{modulo}'"), .datos = "Network error or invalid Git revision for dependency '{modulo}'" };
        return _ret_217;
    }
    if ((codigo == ERR_SEM_ASM_FUERA_INSEGURO)) {
        CadenaSegura _ret_219 = (CadenaSegura){ .longitud = (int)strlen("asm() can only be used inside an 'unsafe:' block"), .datos = "asm() can only be used inside an 'unsafe:' block" };
        return _ret_219;
    }
    if ((codigo == ERR_SEM_CONSTANTE_INMUTABLE)) {
        CadenaSegura _ret_221 = (CadenaSegura){ .longitud = (int)strlen("Cannot reassign constant '{nombre}'"), .datos = "Cannot reassign constant '{nombre}'" };
        return _ret_221;
    }
    CadenaSegura _ret_222 = (CadenaSegura){ .longitud = (int)strlen("Unknown error"), .datos = "Unknown error" };
    return _ret_222;
}

CadenaSegura obtener_linea_contexto(CadenaSegura lineas, int linea_num) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        // buscar linea_num en buffer de lineas (pendiente);
    }
    CadenaSegura _ret_229 = r;
    return _ret_229;
}

CadenaSegura formatear_entrada_error(CadenaSegura ruta, int linea, int columna, CadenaSegura mensaje) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        { char _buf[1024]; snprintf(_buf, 1024, "[Synapse] %s:%d:%d - %s", ruta.datos, linea, columna, mensaje.datos); r = (CadenaSegura){ .longitud = (int)strlen(_buf), .datos = strdup(_buf) }; }
    }
    CadenaSegura _ret_236 = r;
    return _ret_236;
}

CadenaSegura formatear_ubicacion(CadenaSegura ruta, int linea, int columna) {
    if ((linea > 0)) {
        CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        { /* unsafe */
            { char _buf[256]; snprintf(_buf, 256, "%s:%d:%d", ruta.datos, linea, columna); r = (CadenaSegura){ .longitud = (int)strlen(_buf), .datos = strdup(_buf) }; }
        }
        CadenaSegura _ret_244 = r;
        return _ret_244;
    }
    CadenaSegura _ret_245 = ruta;
    return _ret_245;
}

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
int parser_nuevo_nodo(struct ParserEst est, int tipo, int linea, int columna) {
    int idx;
    { /* unsafe */
        idx = 0;
        idx = est.total_nodos;
        est.nodos[idx].tipo_nodo = tipo;
        est.nodos[idx].linea = linea;
        est.nodos[idx].columna = columna;
        est.nodos[idx].valor_int = 0;
        est.nodos[idx].hijo_izq = 0;
        est.nodos[idx].hijo_der = 0;
        est.nodos[idx].hermano = 0;
        est.total_nodos = idx + 1;
        int _ret_161 = idx;
        return _ret_161;
    }
}

void parser_error(struct ParserEst est, CadenaSegura mensaje, int linea, int columna) {
    est.hay_error = 1;
    est.error_mensaje = mensaje;
    est.error_linea = linea;
    est.error_columna = columna;
}

int token_tipo(struct ParserEst est, int pos) {
    int r;
    { /* unsafe */
        r = 0;
        r = (pos < est.total_tokens) ? est.tokens[pos].tipo : 57;
        int _ret_175 = r;
        return _ret_175;
    }
}

int token_linea(struct ParserEst est, int pos) {
    int r;
    { /* unsafe */
        r = 0;
        r = (pos < est.total_tokens) ? est.tokens[pos].linea : 0;
        int _ret_181 = r;
        return _ret_181;
    }
}

int token_columna(struct ParserEst est, int pos) {
    int r;
    { /* unsafe */
        r = 0;
        r = (pos < est.total_tokens) ? est.tokens[pos].columna : 0;
        int _ret_187 = r;
        return _ret_187;
    }
}

void token_avanzar(struct ParserEst est) {
    { /* unsafe */
        est.posicion = est.posicion + 1;
    }
}

int token_mirar(struct ParserEst est) {
    int r;
    { /* unsafe */
        r = 0;
        r = (est.posicion < est.total_tokens) ? est.tokens[est.posicion].tipo : 57;
        int _ret_197 = r;
        return _ret_197;
    }
}

int token_esperar(struct ParserEst est, int esperado) {
    int t;
    t = token_mirar(est);
    if ((t == esperado)) {
        { /* unsafe */
            est.posicion = est.posicion + 1;
        }
        int _ret_204 = 1;
        return _ret_204;
    }
    est.hay_error = 1;
    int _ret_206 = 0;
    return _ret_206;
}

int token_esperar_texto(struct ParserEst est, int esperado) {
    int t;
    int linea;
    int col;
    t = token_mirar(est);
    if ((t == esperado)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        { /* unsafe */
            est.posicion = est.posicion + 1;
        }
        int _ret_215 = parser_nuevo_nodo(est, NODO_IDENTIFICADOR, linea, col);
        return _ret_215;
    }
    est.hay_error = 1;
    int _ret_217 = 0;
    return _ret_217;
}

int parsear_expresion(struct ParserEst est) {
    int _ret_221 = parsear_logica(est);
    return _ret_221;
}

int parsear_logica(struct ParserEst est) {
    int linea;
    int col;
    int der;
    int nodo;
    int izq;
    int r;
    int t;
    linea = 0;
    col = 0;
    der = 0;
    nodo = 0;
    izq = parsear_comparacion(est);
    r = 1;
    while ((r == 1)) {
        t = token_mirar(est);
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
    int _ret_257 = izq;
    return _ret_257;
}

int parsear_comparacion(struct ParserEst est) {
    int linea;
    int col;
    int der;
    int nodo;
    int izq;
    int r;
    int t;
    linea = 0;
    col = 0;
    der = 0;
    nodo = 0;
    izq = parsear_adicion(est);
    r = 1;
    while ((r == 1)) {
        t = token_mirar(est);
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
    int _ret_341 = izq;
    return _ret_341;
}

int parsear_adicion(struct ParserEst est) {
    int linea;
    int col;
    int der;
    int nodo;
    int izq;
    int r;
    int t;
    linea = 0;
    col = 0;
    der = 0;
    nodo = 0;
    izq = parsear_multiplicacion(est);
    r = 1;
    while ((r == 1)) {
        t = token_mirar(est);
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
    int _ret_377 = izq;
    return _ret_377;
}

int parsear_multiplicacion(struct ParserEst est) {
    int linea;
    int col;
    int der;
    int nodo;
    int izq;
    int r;
    int t;
    linea = 0;
    col = 0;
    der = 0;
    nodo = 0;
    izq = parsear_unario(est);
    r = 1;
    while ((r == 1)) {
        t = token_mirar(est);
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
    int _ret_425 = izq;
    return _ret_425;
}

int parsear_unario(struct ParserEst est) {
    int linea;
    int col;
    int expr;
    int nodo;
    int t;
    linea = 0;
    col = 0;
    expr = 0;
    nodo = 0;
    t = token_mirar(est);
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
        int _ret_442 = nodo;
        return _ret_442;
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
        int _ret_452 = nodo;
        return _ret_452;
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
        int _ret_461 = nodo;
        return _ret_461;
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
        int _ret_470 = nodo;
        return _ret_470;
    }
    int _ret_471 = parsear_primario(est);
    return _ret_471;
}

int parsear_primario(struct ParserEst est) {
    int linea;
    int col;
    int nodo;
    int t;
    int t2;
    int r;
    int arg;
    int tok_campo;
    int linea2;
    int col2;
    int nodo2;
    int expr;
    linea = 0;
    col = 0;
    nodo = 0;
    t = token_mirar(est);
    if ((t == T_NUMERO)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        nodo = parser_nuevo_nodo(est, NODO_NUMERO, linea, col);
        int _ret_483 = nodo;
        return _ret_483;
    }
    if ((t == T_FLOTANTE)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        nodo = parser_nuevo_nodo(est, NODO_DECIMAL, linea, col);
        int _ret_489 = nodo;
        return _ret_489;
    }
    if ((t == T_CADENA)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        nodo = parser_nuevo_nodo(est, NODO_CADENA_LIT, linea, col);
        int _ret_495 = nodo;
        return _ret_495;
    }
    if ((t == T_VERDADERO)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        nodo = parser_nuevo_nodo(est, NODO_BOOLEANO, linea, col);
        { /* unsafe */
            est.nodos[nodo].valor_int = 1;
        }
        int _ret_503 = nodo;
        return _ret_503;
    }
    if ((t == T_FALSO)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        nodo = parser_nuevo_nodo(est, NODO_BOOLEANO, linea, col);
        { /* unsafe */
            est.nodos[nodo].valor_int = 0;
        }
        int _ret_511 = nodo;
        return _ret_511;
    }
    if ((t == T_IDENTIFICADOR)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        nodo = parser_nuevo_nodo(est, NODO_IDENTIFICADOR, linea, col);
        t2 = token_mirar(est);
        if ((t2 == T_PAREN_IZQ)) {
            { /* unsafe */
                est.nodos[nodo].tipo_nodo = 14;
            }
            token_esperar(est, T_PAREN_IZQ);
            r = 1;
            while ((r == 1)) {
                if ((token_mirar(est) == T_PAREN_DER)) {
                    break;
                }
                arg = parsear_expresion(est);
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
                tok_campo = token_mirar(est);
                linea2 = token_linea(est, est.posicion);
                col2 = token_columna(est, est.posicion);
                if ((tok_campo == T_IDENTIFICADOR)) {
                    token_avanzar(est);
                    nodo2 = parser_nuevo_nodo(est, NODO_ACCESO_CAMPO, linea2, col2);
                    { /* unsafe */
                        est.nodos[nodo2].hijo_izq = nodo;
                    }
                    nodo = nodo2;
                }
            }
        }
        int _ret_544 = nodo;
        return _ret_544;
    }
    if ((t == T_CANAL)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        if ((token_mirar(est) == T_PAREN_IZQ)) {
            nodo = parser_nuevo_nodo(est, NODO_CANAL_CREAR, linea, col);
            token_esperar(est, T_PAREN_IZQ);
            if ((token_mirar(est) == T_IDENTIFICADOR)) {
                token_avanzar(est);
            }
            if ((token_mirar(est) == T_COMA)) {
                token_avanzar(est);
                expr = parsear_expresion(est);
                { /* unsafe */
                    est.nodos[nodo].hijo_izq = expr;
                }
            }
            token_esperar(est, T_PAREN_DER);
            int _ret_560 = nodo;
            return _ret_560;
        }
        parser_error(est, (CadenaSegura){ .longitud = (int)strlen("Se esperaba ( despues de canal"), .datos = "Se esperaba ( despues de canal" }, linea, col);
        int _ret_562 = 0;
        return _ret_562;
    }
    if ((t == T_PAREN_IZQ)) {
        token_avanzar(est);
        expr = parsear_expresion(est);
        token_esperar(est, T_PAREN_DER);
        int _ret_567 = expr;
        return _ret_567;
    }
    parser_error(est, (CadenaSegura){ .longitud = (int)strlen("Expresion inesperada"), .datos = "Expresion inesperada" }, token_linea(est, est.posicion), token_columna(est, est.posicion));
    int _ret_569 = 0;
    return _ret_569;
}

int parsear_sentencia(struct ParserEst est) {
    int linea;
    int col;
    int nodo;
    int t;
    int expr;
    int t2;
    int t3;
    int plan_b;
    linea = 0;
    col = 0;
    nodo = 0;
    t = token_mirar(est);
    if ((t == T_FUNCION)) {
        int _ret_578 = parsear_funcion(est);
        return _ret_578;
    }
    if ((t == T_ESTRUCTURA)) {
        int _ret_580 = parsear_estructura_def(est);
        return _ret_580;
    }
    if ((t == T_IF)) {
        int _ret_582 = parsear_si(est);
        return _ret_582;
    }
    if ((t == T_MIENTRAS)) {
        int _ret_584 = parsear_mientras(est);
        return _ret_584;
    }
    if ((t == T_PARA)) {
        int _ret_586 = parsear_para(est);
        return _ret_586;
    }
    if ((t == T_RETORNAR)) {
        int _ret_588 = parsear_retornar(est);
        return _ret_588;
    }
    if ((t == T_LANZAR)) {
        int _ret_590 = parsear_lanzar(est);
        return _ret_590;
    }
    if ((t == T_ESCUCHAR)) {
        int _ret_592 = parsear_escuchar(est);
        return _ret_592;
    }
    if ((t == T_ROMPER)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        int _ret_597 = parser_nuevo_nodo(est, NODO_ROMPER, linea, col);
        return _ret_597;
    }
    if ((t == T_SIGUIENTE)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        int _ret_602 = parser_nuevo_nodo(est, NODO_SIGUIENTE, linea, col);
        return _ret_602;
    }
    if ((t == T_IMPORTAR)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        token_avanzar(est);
        nodo = parser_nuevo_nodo(est, NODO_IMPORTAR, linea, col);
        int _ret_608 = nodo;
        return _ret_608;
    }
    if ((t == T_ESTRUCTURA)) {
        int _ret_610 = parsear_estructura_def(est);
        return _ret_610;
    }
    if ((t == T_CONSTANTE)) {
        int _ret_612 = parsear_constante(est);
        return _ret_612;
    }
    if ((t == T_ASM)) {
        int _ret_614 = parsear_asm(est);
        return _ret_614;
    }
    if ((t == T_INSEGURO)) {
        int _ret_616 = parsear_inseguro(est);
        return _ret_616;
    }
    if ((t == T_IMPORTAR_C)) {
        int _ret_618 = parsear_importar_c(est);
        return _ret_618;
    }
    if ((t == T_EXTERNO)) {
        int _ret_620 = parsear_externo(est);
        return _ret_620;
    }
    if ((t == T_COINCIDIR)) {
        int _ret_622 = parsear_coincidir(est);
        return _ret_622;
    }
    if ((t == T_INDENTAR)) {
        int _ret_624 = 0;
        return _ret_624;
    }
    if ((t == T_DESINDENTAR)) {
        int _ret_626 = 0;
        return _ret_626;
    }
    if ((t == T_NUEVALINEA)) {
        int _ret_628 = 0;
        return _ret_628;
    }
    if ((t == T_FIN)) {
        int _ret_630 = 0;
        return _ret_630;
    }
    if ((t == T_CANAL)) {
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        expr = parsear_expresion(est);
        nodo = parser_nuevo_nodo(est, NODO_EXPR, linea, col);
        { /* unsafe */
            est.nodos[nodo].hijo_izq = expr;
        }
        int _ret_638 = nodo;
        return _ret_638;
    }
    if ((t == T_IDENTIFICADOR)) {
        t2 = token_tipo(est, (est.posicion + 1));
        if ((t2 == T_ASIGNAR)) {
            int _ret_642 = parsear_asignacion(est);
            return _ret_642;
        }
        if ((t2 == T_FLECHA_IZQ)) {
            int _ret_644 = parsear_enviar_canal(est);
            return _ret_644;
        }
        if ((t2 == T_FLECHA)) {
            int _ret_646 = parsear_recibir_canal(est);
            return _ret_646;
        }
        linea = token_linea(est, est.posicion);
        col = token_columna(est, est.posicion);
        expr = parsear_expresion(est);
        t3 = token_mirar(est);
        if ((t3 == T_RECUPERAR)) {
            token_avanzar(est);
            token_esperar(est, T_DOSPUNTOS);
            plan_b = parsear_expresion(est);
            int _ret_656 = expr;
            return _ret_656;
        }
        nodo = parser_nuevo_nodo(est, NODO_EXPR, linea, col);
        { /* unsafe */
            est.nodos[nodo].hijo_izq = expr;
        }
        int _ret_660 = nodo;
        return _ret_660;
    }
    int _ret_661 = 0;
    return _ret_661;
}

int parsear_funcion(struct ParserEst est) {
    int r2;
    int expr;
    int r;
    int t;
    int linea;
    int col;
    int nodo_func;
    int ultimo_param;
    int linea_p;
    int col_p;
    int nodo_p;
    int primera_requiere;
    int ultima_requiere;
    int cuenta_requiere;
    int primera_garantiza;
    int ultima_garantiza;
    int cuenta_garantiza;
    int contrato;
    int stmt;
    r2 = 0;
    expr = 0;
    r = 0;
    if ((token_esperar(est, T_FUNCION) == 0)) {
        int _ret_669 = 0;
        return _ret_669;
    }
    t = token_mirar(est);
    if ((t != T_IDENTIFICADOR)) {
        parser_error(est, (CadenaSegura){ .longitud = (int)strlen("Se esperaba nombre de funcion"), .datos = "Se esperaba nombre de funcion" }, token_linea(est, est.posicion), token_columna(est, est.posicion));
        int _ret_673 = 0;
        return _ret_673;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    token_avanzar(est);
    nodo_func = parser_nuevo_nodo(est, NODO_FUNCION, linea, col);
    if ((token_esperar(est, T_PAREN_IZQ) == 0)) {
        int _ret_679 = 0;
        return _ret_679;
    }
    ultimo_param = 0;
    if ((token_mirar(est) != T_PAREN_DER)) {
        r = 1;
        while ((r == 1)) {
            linea_p = token_linea(est, est.posicion);
            col_p = token_columna(est, est.posicion);
            if ((token_mirar(est) == T_IDENTIFICADOR)) {
                token_avanzar(est);
                if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
                    int _ret_690 = 0;
                    return _ret_690;
                }
                if ((token_mirar(est) == T_IDENTIFICADOR)) {
                    token_avanzar(est);
                    nodo_p = parser_nuevo_nodo(est, NODO_PARAMETRO, linea_p, col_p);
                    if ((token_mirar(est) == T_COMA)) {
                        token_avanzar(est);
                        continue;
                    }
                    else {
                        r = 0;
                    }
                }
                else {
                    r = 0;
                }
            }
            else {
                r = 0;
            }
        }
    }
    if ((token_esperar(est, T_PAREN_DER) == 0)) {
        int _ret_704 = 0;
        return _ret_704;
    }
    if ((token_esperar(est, T_FLECHA) == 0)) {
        int _ret_706 = 0;
        return _ret_706;
    }
    if ((token_mirar(est) == T_IDENTIFICADOR)) {
        token_avanzar(est);
    }
    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
        int _ret_711 = 0;
        return _ret_711;
    }
    primera_requiere = 0;
    ultima_requiere = 0;
    cuenta_requiere = 0;
    primera_garantiza = 0;
    ultima_garantiza = 0;
    cuenta_garantiza = 0;
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
                        int _ret_732 = 0;
                        return _ret_732;
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
                                if ((expr != 0)) {
                                    if ((primera_requiere == 0)) {
                                        primera_requiere = expr;
                                        ultima_requiere = expr;
                                    }
                                    else {
                                        { /* unsafe */
                                            est.nodos[ultima_requiere].hermano = expr;
                                        }
                                        ultima_requiere = expr;
                                    }
                                    cuenta_requiere = (cuenta_requiere + 1);
                                }
                                continue;
                            }
                        }
                        else {
                            r2 = 0;
                        }
                    }
                    continue;
                }
                if ((t == T_GARANTIZA)) {
                    token_avanzar(est);
                    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
                        int _ret_767 = 0;
                        return _ret_767;
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
                                if ((expr != 0)) {
                                    if ((primera_garantiza == 0)) {
                                        primera_garantiza = expr;
                                        ultima_garantiza = expr;
                                    }
                                    else {
                                        { /* unsafe */
                                            est.nodos[ultima_garantiza].hermano = expr;
                                        }
                                        ultima_garantiza = expr;
                                    }
                                    cuenta_garantiza = (cuenta_garantiza + 1);
                                }
                                continue;
                            }
                        }
                        else {
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
        }
        else {
            r = 0;
        }
    }
    if (((primera_requiere != 0) || (primera_garantiza != 0))) {
        contrato = parser_nuevo_nodo(est, NODO_CONTRATO, linea, col);
        { /* unsafe */
            est.nodos[contrato].hijo_izq = primera_requiere;
            est.nodos[contrato].hijo_der = primera_garantiza;
            est.nodos[contrato].valor_int = cuenta_requiere;
            est.nodos[nodo_func].ptr_extra = contrato;
        }
    }
    if ((token_mirar(est) == T_INDENTAR)) {
        token_avanzar(est);
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
            stmt = parsear_sentencia(est);
            continue;
        }
    }
    int _ret_831 = nodo_func;
    return _ret_831;
}

int parsear_si(struct ParserEst est) {
    int t;
    int stmt;
    int r;
    int linea;
    int col;
    int nodo;
    int cond;
    t = 0;
    stmt = 0;
    r = 1;
    if ((token_esperar(est, T_IF) == 0)) {
        int _ret_839 = 0;
        return _ret_839;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    nodo = parser_nuevo_nodo(est, NODO_SI, linea, col);
    cond = parsear_expresion(est);
    { /* unsafe */
        est.nodos[nodo].hijo_izq = cond;
    }
    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
        int _ret_847 = 0;
        return _ret_847;
    }
    if ((token_mirar(est) == T_NUEVALINEA)) {
        token_avanzar(est);
        if ((token_mirar(est) == T_INDENTAR)) {
            token_avanzar(est);
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
                stmt = parsear_sentencia(est);
                continue;
            }
        }
    }
    r = 1;
    if ((token_mirar(est) == T_ELSE)) {
        token_avanzar(est);
        if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
            int _ret_870 = 0;
            return _ret_870;
        }
        if ((token_mirar(est) == T_NUEVALINEA)) {
            token_avanzar(est);
            if ((token_mirar(est) == T_INDENTAR)) {
                token_avanzar(est);
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
                    stmt = parsear_sentencia(est);
                    continue;
                }
            }
        }
    }
    int _ret_889 = nodo;
    return _ret_889;
}

int parsear_mientras(struct ParserEst est) {
    int linea;
    int col;
    int nodo;
    int cond;
    int r;
    int t;
    int stmt;
    if ((token_esperar(est, T_MIENTRAS) == 0)) {
        int _ret_893 = 0;
        return _ret_893;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    nodo = parser_nuevo_nodo(est, NODO_MIENTRAS, linea, col);
    cond = parsear_expresion(est);
    { /* unsafe */
        est.nodos[nodo].hijo_izq = cond;
    }
    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
        int _ret_901 = 0;
        return _ret_901;
    }
    if ((token_mirar(est) == T_NUEVALINEA)) {
        token_avanzar(est);
        if ((token_mirar(est) == T_INDENTAR)) {
            token_avanzar(est);
            r = 1;
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
                stmt = parsear_sentencia(est);
                continue;
            }
        }
    }
    int _ret_921 = nodo;
    return _ret_921;
}

int parsear_para(struct ParserEst est) {
    int linea;
    int col;
    int nodo;
    int r;
    int t;
    int stmt;
    if ((token_esperar(est, T_PARA) == 0)) {
        int _ret_925 = 0;
        return _ret_925;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    nodo = parser_nuevo_nodo(est, NODO_VACIO, linea, col);
    parsear_asignacion(est);
    if ((token_esperar(est, T_PUNTOCOMA) == 0)) {
        int _ret_931 = 0;
        return _ret_931;
    }
    parsear_expresion(est);
    if ((token_esperar(est, T_PUNTOCOMA) == 0)) {
        int _ret_934 = 0;
        return _ret_934;
    }
    parsear_asignacion(est);
    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
        int _ret_937 = 0;
        return _ret_937;
    }
    if ((token_mirar(est) == T_NUEVALINEA)) {
        token_avanzar(est);
        if ((token_mirar(est) == T_INDENTAR)) {
            token_avanzar(est);
            r = 1;
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
                stmt = parsear_sentencia(est);
                continue;
            }
        }
    }
    int _ret_957 = nodo;
    return _ret_957;
}

int parsear_retornar(struct ParserEst est) {
    int linea;
    int col;
    int nodo;
    int t;
    int expr;
    if ((token_esperar(est, T_RETORNAR) == 0)) {
        int _ret_961 = 0;
        return _ret_961;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    nodo = parser_nuevo_nodo(est, NODO_RETORNAR, linea, col);
    t = token_mirar(est);
    if ((t != T_NUEVALINEA)) {
        if ((t != T_DESINDENTAR)) {
            if ((t != T_FIN)) {
                expr = parsear_expresion(est);
                { /* unsafe */
                    est.nodos[nodo].hijo_izq = expr;
                }
            }
        }
    }
    int _ret_972 = nodo;
    return _ret_972;
}

int parsear_lanzar(struct ParserEst est) {
    int linea;
    int col;
    int nodo;
    int expr;
    if ((token_esperar(est, T_LANZAR) == 0)) {
        int _ret_976 = 0;
        return _ret_976;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    nodo = parser_nuevo_nodo(est, NODO_LANZAR, linea, col);
    expr = parsear_expresion(est);
    { /* unsafe */
        est.nodos[nodo].hijo_izq = expr;
    }
    int _ret_983 = nodo;
    return _ret_983;
}

int parsear_escuchar(struct ParserEst est) {
    int linea;
    int col;
    int nodo;
    int expr;
    if ((token_esperar(est, T_ESCUCHAR) == 0)) {
        int _ret_987 = 0;
        return _ret_987;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    nodo = parser_nuevo_nodo(est, NODO_ESCUCHAR, linea, col);
    parsear_expresion(est);
    if ((token_esperar(est, T_FLECHA) == 0)) {
        int _ret_993 = 0;
        return _ret_993;
    }
    expr = parsear_expresion(est);
    int _ret_995 = nodo;
    return _ret_995;
}

int parsear_asignacion(struct ParserEst est) {
    int t;
    int linea;
    int col;
    int nodo;
    int expr;
    t = token_mirar(est);
    if ((t != T_IDENTIFICADOR)) {
        int _ret_1000 = 0;
        return _ret_1000;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    token_avanzar(est);
    if ((token_esperar(est, T_ASIGNAR) == 0)) {
        int _ret_1005 = 0;
        return _ret_1005;
    }
    nodo = parser_nuevo_nodo(est, NODO_ASIGNACION, linea, col);
    if (((token_mirar(est) == T_IDENTIFICADOR) && (token_tipo(est, (est.posicion + 1)) == T_FLECHA))) {
        expr = parsear_recibir_canal(est);
    }
    else {
        expr = parsear_expresion(est);
    }
    { /* unsafe */
        est.nodos[nodo].hijo_der = expr;
    }
    int _ret_1013 = nodo;
    return _ret_1013;
}

int parsear_estructura_def(struct ParserEst est) {
    int t;
    int linea;
    int col;
    int nodo;
    int r;
    if ((token_esperar(est, T_ESTRUCTURA) == 0)) {
        int _ret_1017 = 0;
        return _ret_1017;
    }
    t = token_mirar(est);
    if ((t != T_IDENTIFICADOR)) {
        int _ret_1020 = 0;
        return _ret_1020;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    token_avanzar(est);
    nodo = parser_nuevo_nodo(est, NODO_ESTRUCTURA, linea, col);
    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
        int _ret_1026 = 0;
        return _ret_1026;
    }
    if ((token_mirar(est) == T_NUEVALINEA)) {
        token_avanzar(est);
        if ((token_mirar(est) == T_INDENTAR)) {
            token_avanzar(est);
            r = 1;
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
                        int _ret_1047 = 0;
                        return _ret_1047;
                    }
                    if ((token_mirar(est) == T_IDENTIFICADOR)) {
                        token_avanzar(est);
                    }
                }
                continue;
            }
            int _ret_1051 = nodo;
            return _ret_1051;
        }
    }
    int _ret_1052 = nodo;
    return _ret_1052;
}

int parsear_constante(struct ParserEst est) {
    int t;
    int linea;
    int col;
    int nodo;
    int expr;
    if ((token_esperar(est, T_CONSTANTE) == 0)) {
        int _ret_1056 = 0;
        return _ret_1056;
    }
    t = token_mirar(est);
    if ((t != T_IDENTIFICADOR)) {
        int _ret_1059 = 0;
        return _ret_1059;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    token_avanzar(est);
    nodo = parser_nuevo_nodo(est, NODO_CONSTANTE, linea, col);
    if ((token_mirar(est) == T_DOSPUNTOS)) {
        token_avanzar(est);
        if ((token_mirar(est) == T_IDENTIFICADOR)) {
            token_avanzar(est);
        }
    }
    if ((token_esperar(est, T_ASIGNAR) == 0)) {
        int _ret_1069 = 0;
        return _ret_1069;
    }
    expr = parsear_expresion(est);
    { /* unsafe */
        est.nodos[nodo].hijo_izq = expr;
    }
    int _ret_1073 = nodo;
    return _ret_1073;
}

int parsear_asm(struct ParserEst est) {
    int linea;
    int col;
    int nodo;
    if ((token_esperar(est, T_ASM) == 0)) {
        int _ret_1077 = 0;
        return _ret_1077;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    nodo = parser_nuevo_nodo(est, NODO_ASM, linea, col);
    if ((token_esperar(est, T_PAREN_IZQ) == 0)) {
        int _ret_1082 = 0;
        return _ret_1082;
    }
    if ((token_mirar(est) == T_CADENA)) {
        { /* unsafe */
            est.nodos[nodo].ptr_str = est.tokens[est.posicion].ptr_valor;
            est.nodos[nodo].len_str = est.tokens[est.posicion].len_valor;
        }
        token_avanzar(est);
    }
    if ((token_esperar(est, T_PAREN_DER) == 0)) {
        int _ret_1089 = 0;
        return _ret_1089;
    }
    int _ret_1090 = nodo;
    return _ret_1090;
}

int parsear_inseguro(struct ParserEst est) {
    int linea;
    int col;
    int nodo;
    int r;
    int t;
    int stmt;
    if ((token_esperar(est, T_INSEGURO) == 0)) {
        int _ret_1094 = 0;
        return _ret_1094;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    nodo = parser_nuevo_nodo(est, NODO_INSEGURO, linea, col);
    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
        int _ret_1099 = 0;
        return _ret_1099;
    }
    if ((token_mirar(est) == T_NUEVALINEA)) {
        token_avanzar(est);
        if ((token_mirar(est) == T_INDENTAR)) {
            token_avanzar(est);
            r = 1;
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
                stmt = parsear_sentencia(est);
                continue;
            }
        }
    }
    int _ret_1119 = nodo;
    return _ret_1119;
}

int parsear_importar_c(struct ParserEst est) {
    int linea;
    int col;
    int nodo;
    if ((token_esperar(est, T_IMPORTAR_C) == 0)) {
        int _ret_1123 = 0;
        return _ret_1123;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    nodo = parser_nuevo_nodo(est, NODO_IMPORTAR_C, linea, col);
    if ((token_mirar(est) == T_CADENA)) {
        token_avanzar(est);
    }
    int _ret_1129 = nodo;
    return _ret_1129;
}

int parsear_externo(struct ParserEst est) {
    int t;
    int linea;
    int col;
    int nodo;
    int r;
    if ((token_esperar(est, T_EXTERNO) == 0)) {
        int _ret_1133 = 0;
        return _ret_1133;
    }
    if ((token_esperar(est, T_FUNCION) == 0)) {
        int _ret_1135 = 0;
        return _ret_1135;
    }
    t = token_mirar(est);
    if ((t != T_IDENTIFICADOR)) {
        int _ret_1138 = 0;
        return _ret_1138;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    token_avanzar(est);
    nodo = parser_nuevo_nodo(est, NODO_EXTERNO, linea, col);
    if ((token_esperar(est, T_PAREN_IZQ) == 0)) {
        int _ret_1144 = 0;
        return _ret_1144;
    }
    r = 1;
    while ((r == 1)) {
        t = token_mirar(est);
        if ((t == T_PAREN_DER)) {
            r = 0;
            break;
        }
        if ((t == T_IDENTIFICADOR)) {
            token_avanzar(est);
            if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
                int _ret_1154 = 0;
                return _ret_1154;
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
        int _ret_1163 = 0;
        return _ret_1163;
    }
    if ((token_esperar(est, T_FLECHA) == 0)) {
        int _ret_1165 = 0;
        return _ret_1165;
    }
    if ((token_mirar(est) == T_IDENTIFICADOR)) {
        token_avanzar(est);
    }
    int _ret_1168 = nodo;
    return _ret_1168;
}

int parsear_coincidir(struct ParserEst est) {
    int linea;
    int col;
    int nodo;
    int expr;
    int r;
    int t;
    int linea_c;
    int col_c;
    int nodo_caso;
    int r2;
    int stmt;
    if ((token_esperar(est, T_COINCIDIR) == 0)) {
        int _ret_1172 = 0;
        return _ret_1172;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    nodo = parser_nuevo_nodo(est, NODO_COINCIDIR, linea, col);
    expr = parsear_expresion(est);
    { /* unsafe */
        est.nodos[nodo].hijo_izq = expr;
    }
    if ((token_esperar(est, T_DOSPUNTOS) == 0)) {
        int _ret_1180 = 0;
        return _ret_1180;
    }
    if ((token_mirar(est) == T_NUEVALINEA)) {
        token_avanzar(est);
        if ((token_mirar(est) == T_INDENTAR)) {
            token_avanzar(est);
            r = 1;
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
                    linea_c = token_linea(est, est.posicion);
                    col_c = token_columna(est, est.posicion);
                    token_avanzar(est);
                    nodo_caso = parser_nuevo_nodo(est, NODO_CASO, linea_c, col_c);
                    if ((token_mirar(est) == T_PAREN_IZQ)) {
                        token_avanzar(est);
                        if ((token_mirar(est) == T_IDENTIFICADOR)) {
                            token_avanzar(est);
                        }
                        if ((token_esperar(est, T_PAREN_DER) == 0)) {
                            int _ret_1208 = 0;
                            return _ret_1208;
                        }
                    }
                    if ((token_esperar(est, T_FLECHA_DER) == 0)) {
                        int _ret_1210 = 0;
                        return _ret_1210;
                    }
                    r2 = 1;
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
                        stmt = parsear_sentencia(est);
                        continue;
                    }
                }
                continue;
            }
        }
    }
    int _ret_1226 = nodo;
    return _ret_1226;
}

int parsear_enviar_canal(struct ParserEst est) {
    int linea;
    int col;
    int nodo;
    int expr;
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    nodo = parser_nuevo_nodo(est, NODO_ENVIAR_CANAL, linea, col);
    if ((token_mirar(est) == T_IDENTIFICADOR)) {
        token_avanzar(est);
    }
    if ((token_esperar(est, T_FLECHA_IZQ) == 0)) {
        int _ret_1235 = 0;
        return _ret_1235;
    }
    expr = parsear_expresion(est);
    int _ret_1237 = nodo;
    return _ret_1237;
}

int parsear_crear_canal(struct ParserEst est) {
    int linea;
    int col;
    int nodo;
    int expr;
    if ((token_esperar(est, T_CANAL) == 0)) {
        int _ret_1241 = 0;
        return _ret_1241;
    }
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    nodo = parser_nuevo_nodo(est, NODO_CANAL_CREAR, linea, col);
    if ((token_esperar(est, T_PAREN_IZQ) == 0)) {
        int _ret_1246 = 0;
        return _ret_1246;
    }
    if ((token_mirar(est) == T_IDENTIFICADOR)) {
        token_avanzar(est);
    }
    if ((token_mirar(est) == T_COMA)) {
        token_avanzar(est);
        expr = parsear_expresion(est);
        { /* unsafe */
            est.nodos[nodo].hijo_izq = expr;
        }
    }
    if ((token_esperar(est, T_PAREN_DER) == 0)) {
        int _ret_1255 = 0;
        return _ret_1255;
    }
    int _ret_1256 = nodo;
    return _ret_1256;
}

int parsear_recibir_canal(struct ParserEst est) {
    int linea;
    int col;
    int nodo;
    linea = token_linea(est, est.posicion);
    col = token_columna(est, est.posicion);
    nodo = parser_nuevo_nodo(est, NODO_RECIBIR_CANAL, linea, col);
    if ((token_mirar(est) == T_IDENTIFICADOR)) {
        token_avanzar(est);
    }
    if ((token_esperar(est, T_FLECHA) == 0)) {
        int _ret_1265 = 0;
        return _ret_1265;
    }
    int _ret_1266 = nodo;
    return _ret_1266;
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
#define T_BREAK 49
#define T_CONTINUE 11
#define T_DOT 12
#define T_IDENT 13
#define T_NUM 14
#define T_STR 15
#define T_GT 16
#define T_LT 17
#define T_EQ 25
#define T_NE 26
#define T_LE 27
#define T_GE 28
#define T_ASSIGN 29
#define T_PLUS 30
#define T_MINUS 31
#define T_MUL 32
#define T_DIV 33
#define T_MOD 34
#define T_ARROW 35
#define T_LPAREN 38
#define T_RPAREN 39
#define T_COLON 40
#define T_COMMA 41
#define T_NL 42
#define T_INDENT 43
#define T_DEDENT 44
#define T_EOF 57
#define T_STRUCT 10
#define T_AND 14
#define T_OR 15
#define T_NOT 16
#define T_TRUE 17
#define T_FALSE 18
#define T_INSEGURO 46
#define T_IMPORTAR_C 47
#define T_AMPERSAND 45
#define T_EXTERNO 48

#define MAX_TOKS 65536
typedef struct { int tipo; int linea; int col; char val[256]; } _P_Token;
_P_Token _P_tks[MAX_TOKS];
int _P_ntks = 0, _P_tpos = 0, _P_p_err = 0;
int _P_pila_indent[64], _P_nivel_pila = 0;

void _P_tokenizar(const char* s, int len) {
    int i = 0, li = 1, co = 1;
    while (i < len && _P_ntks < MAX_TOKS - 1) {
        if (_P_ntks >= MAX_TOKS - 1) { fprintf(stderr,"FATAL: MAX_TOKS (%d) superado en tokenizador.\n",MAX_TOKS); exit(1); }
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
            while (i < len && s[i] != q) { if (s[i] == '\\' && i+1 < len) { i++; co++; } i++; co++; }
            if (i >= len) break;
            i++; co++;
            int _rlen = (i - st - 2) < 255 ? (i - st - 2) : 255;
            char _tmp[256]; strncpy(_tmp, s + st + 1, _rlen); _tmp[_rlen] = 0;
            int _un = 0;
            for (int _si = 0; _tmp[_si] && _un < 254; _si++) {
                if (_tmp[_si] == 92 && _tmp[_si+1]) {
                    switch (_tmp[_si+1]) {
                    case 34: _P_tks[_P_ntks].val[_un++] = 34; _si++; break;
                    case 39: _P_tks[_P_ntks].val[_un++] = 39; _si++; break;
                    case 92: _P_tks[_P_ntks].val[_un++] = 92; _si++; break;
                    case 110: _P_tks[_P_ntks].val[_un++] = 10; _si++; break;
                    case 116: _P_tks[_P_ntks].val[_un++] = 9; _si++; break;
                    case 114: _P_tks[_P_ntks].val[_un++] = 13; _si++; break;
                    case 48: _P_tks[_P_ntks].val[_un++] = 0; _si++; break;
                    default: _P_tks[_P_ntks].val[_un++] = _tmp[_si]; break;
                    }
                } else {
                    _P_tks[_P_ntks].val[_un++] = _tmp[_si];
                }
            }
            _P_tks[_P_ntks].val[_un] = 0;
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
            const _KW _ks[] = {
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
            if (li == 72) { fprintf(stderr, "[DEBUG LEXER L72] Texto: '%s' -> ID Asignado: %d\n", _P_tks[_P_ntks].val, _P_tks[_P_ntks].tipo); }
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

void _P_procesar_indentacion_final() {
    while (_P_nivel_pila > 0) {
        _P_tks[_P_ntks].tipo = T_DEDENT; _P_tks[_P_ntks].linea = _P_tks[_P_ntks-1].linea; _P_tks[_P_ntks].col = 0;
        _P_ntks++; _P_nivel_pila--;
    }
}

// --- AST builder helpers ---
CadenaSegura _P_cs(const char* s) {
    CadenaSegura c; c.longitud = (int)strlen(s);
    char* d = (char*)malloc(c.longitud + 1); strcpy(d, s); c.datos = d; return c;
}
struct ListaNodo* _P_mk_list(struct Nodo* h, struct ListaNodo* t) {
    struct ListaNodo* n = (struct ListaNodo*)calloc(1,sizeof(struct ListaNodo));
    n->cabeza = h; n->cola = t; return n;
}

_P_Token* _P_mirar() { return &_P_tks[_P_tpos]; }
void _P_avanzar() { if (_P_tpos < _P_ntks) _P_tpos++; }
int _P_posible(int t) { return _P_mirar()->tipo == t ? 1 : 0; }
int _P_esperar(int t) {
    if (_P_mirar()->tipo == t) { _P_avanzar(); return 1; }
    fprintf(stderr, "[PARSER] L%d:%d: esperaba token %d, encontre %d\n",
            _P_mirar()->linea, _P_mirar()->col, t, _P_mirar()->tipo);
    exit(1);
}
void _P_sinc_skip() {
    while (_P_tpos < _P_ntks) {
        int tt = _P_mirar()->tipo;
        if (tt == T_NL || tt == T_DEDENT || tt == T_EOF || tt == T_COMMA || tt == T_RPAREN || tt == T_COLON) break;
        _P_avanzar();
    }
}

// Forward declarations
struct Nodo* _P_expr();
struct Nodo* _P_logica();
struct ListaNodo* _P_bloque();
struct Nodo* _P_sentencia();
struct Nodo* _P_comp();
struct Nodo* _P_suma();
struct Nodo* _P_term();
struct Nodo* _P_una();
struct Nodo* _P_prim();
struct Programa _P_programa();
struct ListaNodo* _P_bloque() {
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
struct Nodo* _P_sentencia() {
#ifdef SYN_DEBUG_PARSE
    fprintf(stderr, "PARSE S tok=%d pos=%d/%d\n", _P_mirar()->tipo, _P_tpos, _P_ntks);
    fflush(stderr);
#endif
    while (_P_mirar()->tipo == T_NL) { _P_avanzar(); }
_P_retry:;
    _P_Token* t = _P_mirar();
    if (t->tipo == T_FUNC) {
        _P_avanzar();
        if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); return NULL; }
        char _nm[256]; strcpy(_nm, _P_mirar()->val);
        _P_avanzar();
        _P_esperar(T_LPAREN);
        struct ListaNodo* params = NULL;
        struct ListaNodo** pcur = &params;
        if (_P_mirar()->tipo != T_RPAREN) {
            while (1) {
                int is_transfer = 0;
                if (_P_mirar()->tipo == T_ARROW) { is_transfer=1; _P_avanzar(); }
                if (_P_mirar()->tipo != T_IDENT) break;
                char _pn[256]; strcpy(_pn, _P_mirar()->val);
                _P_avanzar();
                _P_esperar(T_COLON);
                if (_P_mirar()->tipo != T_IDENT) break;
                char _pt[256]; strcpy(_pt, _P_mirar()->val);
                _P_avanzar();
                while (_P_mirar()->tipo == T_MUL) { strcat(_pt,"*"); _P_avanzar(); }
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
            char _pn[256]; strcpy(_pn, _P_mirar()->val);
            _P_avanzar();
            _P_esperar(T_COLON);
            if (_P_mirar()->tipo != T_IDENT) { _P_sinc_skip(); break; }
            char _pt[256]; strcpy(_pt, _P_mirar()->val);
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
        struct ListaNodo* cpo=NULL;
        if (_P_mirar()->tipo == T_NL) {
            cpo=_P_bloque();
        } else {
            struct Nodo* _st=_P_sentencia();
            if (_st) { cpo=_P_mk_list(_st,NULL); }
        }
        struct ListaNodo* sino = NULL;
        if (_P_mirar()->tipo == T_ELSE) { _P_avanzar(); _P_esperar(T_COLON);
            if (_P_mirar()->tipo == T_NL) {
                sino=_P_bloque();
            } else {
                struct Nodo* _st=_P_sentencia();
                if (_st) { sino=_P_mk_list(_st,NULL); }
            }
        }
        struct SentenciaSi* n = (struct SentenciaSi*)calloc(1,sizeof(struct SentenciaSi));
        n->tipo=_P_cs("SentenciaSi"); n->condicion=cond;
        n->cuerpo=cpo; n->cuerpo_sino=sino;
        return (struct Nodo*)n;
    }
    if (t->tipo == T_WHILE) {
        _P_avanzar();
        struct Nodo* cond=_P_expr();
        _P_esperar(T_COLON);
        struct ListaNodo* cpo=NULL;
        if (_P_mirar()->tipo == T_NL) {
            cpo=_P_bloque();
        } else {
            struct Nodo* _st=_P_sentencia();
            if (_st) { cpo=_P_mk_list(_st,NULL); }
        }
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
        char _imp[256]; strcpy(_imp, _P_mirar()->val); int _iml = (int)strlen(_imp);
        _P_avanzar();
        while (_P_mirar()->tipo == T_DOT) { _P_avanzar(); if (_P_mirar()->tipo != T_IDENT) break; strcat(_imp,"."); strcat(_imp,_P_mirar()->val); _P_avanzar(); }
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
        struct ListaNodo* cpo=NULL;
        if (_P_mirar()->tipo == T_NL) {
            cpo=_P_bloque();
        } else {
            struct Nodo* _st=_P_sentencia();
            if (_st) { cpo=_P_mk_list(_st,NULL); }
        }
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
    // Guard: skip stray INDENT/DEDENT/NL and retry keyword matching
    if (_P_mirar()->tipo == T_INDENT || _P_mirar()->tipo == T_DEDENT || _P_mirar()->tipo == T_NL) {
        _P_avanzar();
        goto _P_retry;
    }
    if (_P_mirar()->tipo == T_EOF) { return NULL; }
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
struct Nodo* _P_expr() { return _P_logica(); }

struct Nodo* _P_logica() {
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

struct Nodo* _P_comp() {
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
struct Nodo* _P_suma() {
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
struct Nodo* _P_term() {
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
struct Nodo* _P_una() {
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
struct Nodo* _P_prim() {
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
        char _nm[256]; strcpy(_nm, t->val);
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
                strcpy(_nm, _P_mirar()->val); _P_avanzar();
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
struct Programa _P_programa() {
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
            if (est.tabla->entradas[i].nivel_ambito == est.tabla->nivel_actual) {
                int _eq = 1;
                for (int _si = 0; _si < 256; _si++) { if (((const char*)nombre.datos)[_si] != ((const char*)est.tabla->entradas[i].nombre.datos)[_si]) { _eq = 0; break; } if (((const char*)nombre.datos)[_si] == 0) break; }
                if (_eq) { encontrado = verdadero; }
            }
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
            for (int _si = 0; _si < 256; _si++) {
                char _a = nombre.datos[_si];
                char _b = est.tabla->entradas[i].nombre.datos[_si];
                if (_a != _b) { _eq = 0; break; }
                if (_a == 0) break;
            }
            if (_eq) { return i; }
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
        while (est.tabla->total_entradas > 0) {
            if (est.tabla->entradas[est.tabla->total_entradas - 1].nivel_ambito < est.tabla->nivel_actual) break;
            est.tabla->total_entradas = est.tabla->total_entradas - 1;
        }
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
        if (strcmp(nombre.datos, "reserva") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "libera") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "crear_tensor") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "suma_tensor") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "producto_punto") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "abrir") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "leer") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "escribir") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "escribir_linea") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "leer_linea") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "cerrar") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "suma") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "producto") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "relu") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "tokenizar") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "parsear") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "generar") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "_argc") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "_argv") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "salir") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "concat") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "texto_a_entero") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "texto_a_decimal") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "entero_a_texto") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "decimal_a_texto") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "volcar_ast") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "canal_crear") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "canal_enviar") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "canal_recibir") == 0) { return verdadero; }
        if (strcmp(nombre.datos, "cerrar_canal") == 0) { return verdadero; }
    }
    int _ret_264 = 0;
    return _ret_264;
}

int builtin_cantidad_args(CadenaSegura nombre) {
    { /* unsafe */
        if (strcmp(nombre.datos, "reserva") == 0) { return 1; }
        if (strcmp(nombre.datos, "libera") == 0) { return 1; }
        if (strcmp(nombre.datos, "crear_tensor") == 0) { return 2; }
        if (strcmp(nombre.datos, "suma_tensor") == 0) { return 2; }
        if (strcmp(nombre.datos, "producto_punto") == 0) { return 2; }
        if (strcmp(nombre.datos, "abrir") == 0) { return 2; }
        if (strcmp(nombre.datos, "leer") == 0) { return 1; }
        if (strcmp(nombre.datos, "escribir") == 0) { return 1; }
        if (strcmp(nombre.datos, "escribir_linea") == 0) { return 1; }
        if (strcmp(nombre.datos, "leer_linea") == 0) { return 0; }
        if (strcmp(nombre.datos, "cerrar") == 0) { return 1; }
        if (strcmp(nombre.datos, "suma") == 0) { return 2; }
        if (strcmp(nombre.datos, "producto") == 0) { return 2; }
        if (strcmp(nombre.datos, "relu") == 0) { return 1; }
        if (strcmp(nombre.datos, "tokenizar") == 0) { return 1; }
        if (strcmp(nombre.datos, "parsear") == 0) { return 1; }
        if (strcmp(nombre.datos, "generar") == 0) { return 2; }
        if (strcmp(nombre.datos, "_argc") == 0) { return 0; }
        if (strcmp(nombre.datos, "_argv") == 0) { return 1; }
        if (strcmp(nombre.datos, "salir") == 0) { return 1; }
        if (strcmp(nombre.datos, "concat") == 0) { return 2; }
        if (strcmp(nombre.datos, "texto_a_entero") == 0) { return 1; }
        if (strcmp(nombre.datos, "texto_a_decimal") == 0) { return 1; }
        if (strcmp(nombre.datos, "entero_a_texto") == 0) { return 1; }
        if (strcmp(nombre.datos, "decimal_a_texto") == 0) { return 1; }
        if (strcmp(nombre.datos, "volcar_ast") == 0) { return 2; }
        if (strcmp(nombre.datos, "canal_crear") == 0) { return 1; }
        if (strcmp(nombre.datos, "canal_enviar") == 0) { return 2; }
        if (strcmp(nombre.datos, "canal_recibir") == 0) { return 1; }
        if (strcmp(nombre.datos, "cerrar_canal") == 0) { return 1; }
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
    if ((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("cerrar_canal"), .datos = "cerrar_canal" }) == 1)) {
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
    if (((str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("canal_recibir"), .datos = "canal_recibir" }) == 1) || (str_eq(nombre, (CadenaSegura){ .longitud = (int)strlen("cerrar_canal"), .datos = "cerrar_canal" }) == 1))) {
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
            for (int _si = 0; _si < 256; _si++) { if (nombre.datos[_si] != est.info_estructuras[i].nombre.datos[_si]) { _eq = 0; break; } if (nombre.datos[_si] == 0) break; }
            if (_eq) {
                sem_error(est, ERR_SEM_REDEFINICION, idx_nodo, nombre);
                return;
            }
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
        if (patron.datos[0] == '_' && patron.datos[1] == 0) { return 0; }
        // Extract tag name before '(';
        int _i = 0;
        char _tag[64]; int _tp = 0;
        while (patron.datos[_i] != 0 && patron.datos[_i] != '(') { _tag[_tp++] = patron.datos[_i]; _i++; }
        _tag[_tp] = 0;
        if (patron.datos[_i] != '(') { return -1; }
        _i++; // skip '(';
        char _var[64]; int _vp = 0;
        while (patron.datos[_i] != 0 && patron.datos[_i] != ')') { _var[_vp++] = patron.datos[_i]; _i++; }
        _var[_vp] = 0;
        if (patron.datos[_i] != ')') { return -1; }
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
        for (int _i = 0; _i < est.total_nodos; _i++) {
            if (est.nodos[_i].tipo_nodo == 1) { idx_programa = _i; break; }
        }
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

#define _GEN_TMP_SIZE (4096)
void traducir_tipo_c(void* tipo_synapse) {
    { /* unsafe */
        const char* _t = (const char*)tipo_synapse;
        if (!_t) { strcpy(_gen_tmp_buf, "void"); return; }
        int _len = (int)strlen(_t);
        if (_len > 7 && _t[0]=='C' && _t[1]=='a' && _t[2]=='n' && _t[3]=='a' && _t[4]=='l' && _t[5]=='<');
            { strcpy(_gen_tmp_buf, "CanalConcurrencia*"); return; }
        if (_len > 10 && _t[0]=='R' && _t[1]=='e' && _t[2]=='s' && _t[3]=='u' && _t[4]=='l' && _t[5]=='t' && _t[6]=='a' && _t[7]=='d' && _t[8]=='o' && _t[9]=='<');
            { strcpy(_gen_tmp_buf, "Resultado_T"); return; }
        if (strcmp(_t, "entero")==0 || strcmp(_t, "int")==0) { strcpy(_gen_tmp_buf, "int"); return; }
        if (strcmp(_t, "vacio")==0 || strcmp(_t, "nulo")==0 || strcmp(_t, "void")==0) { strcpy(_gen_tmp_buf, "void"); return; }
        if (strcmp(_t, "decimal")==0 || strcmp(_t, "real")==0 || strcmp(_t, "flotante")==0) { strcpy(_gen_tmp_buf, "float"); return; }
        if (strcmp(_t, "Tensor")==0 || strcmp(_t, "tensor")==0) { strcpy(_gen_tmp_buf, "Tensor"); return; }
        if (strcmp(_t, "Canal")==0 || strcmp(_t, "canal")==0) { strcpy(_gen_tmp_buf, "Canal"); return; }
        if (strcmp(_t, "texto")==0 || strcmp(_t, "cadena")==0) { strcpy(_gen_tmp_buf, "CadenaSegura"); return; }
        if (strcmp(_t, "booleano")==0 || strcmp(_t, "logico")==0) { strcpy(_gen_tmp_buf, "int"); return; }
        if (strcmp(_t, "char")==0) { strcpy(_gen_tmp_buf, "char"); return; }
        if (strcmp(_t, "double")==0) { strcpy(_gen_tmp_buf, "double"); return; }
        if (strcmp(_t, "puntero")==0) { strcpy(_gen_tmp_buf, "void*"); return; }
        snprintf(_gen_tmp_buf, 64, "struct %s", _t);
    }
}

CadenaSegura aplicar_coercion(void* expr_c, void* tipo_origen, void* tipo_destino, int linea) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        const char* _o = (const char*)tipo_origen;
        const char* _d = (const char*)tipo_destino;
        if (strcmp(_o, "float")==0 && strcmp(_d, "CadenaSegura")==0);
            { snprintf(_gen_tmp_buf, 4096, "decimal_a_texto(%s)", (const char*)expr_c); return; }
        if (strcmp(_o, "int")==0 && strcmp(_d, "CadenaSegura")==0);
            { snprintf(_gen_tmp_buf, 4096, "entero_a_texto(%s)", (const char*)expr_c); return; }
        if (strcmp(_o, _d)==0) { strcpy(_gen_tmp_buf, (const char*)expr_c); return; }
        snprintf(_gen_tmp_buf, 4096, "/* coercion: %s -> %s */", _o, _d);
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_194 = r;
    return _ret_194;
}

CadenaSegura prim_int_to_ptr(void* valor) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        snprintf(_gen_tmp_buf, 4096, "_synapse_box_int(%s)", (const char*)valor);
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_202 = r;
    return _ret_202;
}

CadenaSegura prim_float_to_ptr(void* valor) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        snprintf(_gen_tmp_buf, 4096, "_synapse_box_float(%s)", (const char*)valor);
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_209 = r;
    return _ret_209;
}

CadenaSegura syn_malloc(struct GeneradorCEst est, void* size_expr) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        if (est.es_no_std) {
            snprintf(_gen_tmp_buf, 4096, "__syn_asignar(%s)", (const char*)size_expr);
        } else {
            snprintf(_gen_tmp_buf, 4096, "malloc(%s)", (const char*)size_expr);
        }
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_221 = r;
    return _ret_221;
}

CadenaSegura syn_calloc(struct GeneradorCEst est, void* n_expr, void* size_expr) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        if (est.es_no_std) {
            snprintf(_gen_tmp_buf, 4096, "__syn_asignar(%s * %s)", (const char*)n_expr, (const char*)size_expr);
        } else {
            snprintf(_gen_tmp_buf, 4096, "calloc(%s, %s)", (const char*)n_expr, (const char*)size_expr);
        }
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_232 = r;
    return _ret_232;
}

CadenaSegura syn_free(struct GeneradorCEst est, void* ptr_expr) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        if (est.es_no_std) {
            snprintf(_gen_tmp_buf, 4096, "__syn_liberar(%s)", (const char*)ptr_expr);
        } else {
            snprintf(_gen_tmp_buf, 4096, "free(%s)", (const char*)ptr_expr);
        }
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_243 = r;
    return _ret_243;
}

CadenaSegura syn_pool_alloc(struct GeneradorCEst est, void* size_expr) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        if (est.es_no_std) {
            snprintf(_gen_tmp_buf, 4096, "__syn_asignar(%s)", (const char*)size_expr);
        } else {
            snprintf(_gen_tmp_buf, 4096, "_pool_malloc(%s)", (const char*)size_expr);
        }
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_254 = r;
    return _ret_254;
}

CadenaSegura syn_pool_free(struct GeneradorCEst est, void* ptr_expr) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        if (est.es_no_std) {
            snprintf(_gen_tmp_buf, 4096, "__syn_liberar(%s)", (const char*)ptr_expr);
        } else {
            snprintf(_gen_tmp_buf, 4096, "pool_free(%s)", (const char*)ptr_expr);
        }
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_265 = r;
    return _ret_265;
}

int gen_find_var(struct GeneradorCEst est, void* nombre) {
    int r;
    { /* unsafe */
        r = (-1);
        for (int _vi = 0; _vi < est.var_total; _vi++) {
            if (strcmp(est.var_nombres.datos + _vi * 64, (const char*)nombre) == 0);
                { r = _vi; break; }
        }
        int _ret_275 = r;
        return _ret_275;
    }
}

void gen_add_var(struct GeneradorCEst est, void* nombre, void* tipo) {
    { /* unsafe */
        strcpy(est.var_nombres.datos + est.var_total * 64, (const char*)nombre);
        strcpy(est.var_tipos.datos + est.var_total * 64, (const char*)tipo);
        est.var_total = est.var_total + 1;
    }
}

void gen_set_var_type(struct GeneradorCEst est, int idx, void* tipo) {
    { /* unsafe */
        if (idx >= 0 && idx < est.var_total);
            strcpy(est.var_tipos.datos + idx * 64, (const char*)tipo);
    }
}

void gen_agregar_return_type(struct GeneradorCEst est, void* nombre, void* tipo) {
    { /* unsafe */
        strcpy(est.func_return_types_nombres.datos + est.func_return_types_total * 64, (const char*)nombre);
        strcpy(est.func_return_types_tipos.datos + est.func_return_types_total * 64, (const char*)tipo);
        est.func_return_types_total = est.func_return_types_total + 1;
    }
}

CadenaSegura gen_func_return_type(struct GeneradorCEst est, void* nombre) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        for (int _fi = 0; _fi < est.func_return_types_total; _fi++) {
            if (strcmp(est.func_return_types_nombres.datos + _fi * 64, (const char*)nombre) == 0) {
                strcpy(_gen_tmp_buf, (const char*)est.func_return_types_tipos.datos + _fi * 64);
                return;
            }
        }
        strcpy(_gen_tmp_buf, "int");
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_306 = r;
    return _ret_306;
}

void gen_agregar_struct_c(struct GeneradorCEst est, void* nombre) {
    { /* unsafe */
        strcpy(est.struct_nombres_c.datos + est.struct_total_c * 64, (const char*)nombre);
        est.struct_total_c = est.struct_total_c + 1;
    }
}

void gen_emitir_linea(struct GeneradorCEst est, void* linea) {
    { /* unsafe */
        {
            static char _gebuf[1048576];
            static int _gepos = 0;
            const char* _gs = (const char*)linea;
            int _gl = (int)strlen(_gs);
            if (_gepos + _gl + 2 > 1048576) return;
            memcpy(_gebuf + _gepos, _gs, _gl);
            _gepos += _gl;
            _gebuf[_gepos] = 10;
            _gepos++;
            _gebuf[_gepos] = 0;
        }
    }
}

void gen_emitir_nueva_linea(struct GeneradorCEst est) {
    { /* unsafe */
        {
            static char _genbuf[1048576];
            static int _genpos = 0;
            if (_genpos + 2 > 1048576) return;
            _genbuf[_genpos] = 10;
            _genpos++;
            _genbuf[_genpos] = 0;
        }
    }
}

void gen_escribir_cadena_escapada(struct GeneradorCEst est, void* str) {
    { /* unsafe */
        const char* _s=(const char*)str;if(!_s)return;char _esc[16384];int _epos=0;int _ei=0;while(_s[_ei]&&_epos<16380){char _c=_s[_ei];if(_c==10){_esc[_epos++]=92;_esc[_epos++]=110;}else if(_c==34){_esc[_epos++]=92;_esc[_epos++]=34;}else if(_c==92){_esc[_epos++]=92;_esc[_epos++]=92;}else if(_c==9){_esc[_epos++]=92;_esc[_epos++]=116;}else if(_c==13){_esc[_epos++]=92;_esc[_epos++]=114;}else{_esc[_epos++]=_c;}_ei++;}_esc[_epos]=0;gen_emitir_linea(est,_esc);
    }
}

void gen_emitir_token_defs(struct GeneradorCEst est) {
    if ((est.gen_defs_emitido == 1)) {
        return;
    }
    est.gen_defs_emitido = 1;
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("// --- Token IDs ---"), .datos = "// --- Token IDs ---" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_IF 1"), .datos = "#define T_IF 1" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_ELSE 2"), .datos = "#define T_ELSE 2" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_FUNC 3"), .datos = "#define T_FUNC 3" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_RET 4"), .datos = "#define T_RET 4" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_SPAWN 5"), .datos = "#define T_SPAWN 5" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_RECOVER 6"), .datos = "#define T_RECOVER 6" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_LISTEN 7"), .datos = "#define T_LISTEN 7" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_WHILE 8"), .datos = "#define T_WHILE 8" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_IMPORT 9"), .datos = "#define T_IMPORT 9" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_BREAK 49"), .datos = "#define T_BREAK 49" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_CONTINUE 11"), .datos = "#define T_CONTINUE 11" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_DOT 12"), .datos = "#define T_DOT 12" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_IDENT 13"), .datos = "#define T_IDENT 13" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_NUM 14"), .datos = "#define T_NUM 14" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_STR 15"), .datos = "#define T_STR 15" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_GT 16"), .datos = "#define T_GT 16" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_LT 17"), .datos = "#define T_LT 17" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_EQ 25"), .datos = "#define T_EQ 25" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_NE 26"), .datos = "#define T_NE 26" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_LE 27"), .datos = "#define T_LE 27" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_GE 28"), .datos = "#define T_GE 28" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_ASSIGN 29"), .datos = "#define T_ASSIGN 29" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_PLUS 30"), .datos = "#define T_PLUS 30" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_MINUS 31"), .datos = "#define T_MINUS 31" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_MUL 32"), .datos = "#define T_MUL 32" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_DIV 33"), .datos = "#define T_DIV 33" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_MOD 34"), .datos = "#define T_MOD 34" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_ARROW 35"), .datos = "#define T_ARROW 35" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_LPAREN 38"), .datos = "#define T_LPAREN 38" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_RPAREN 39"), .datos = "#define T_RPAREN 39" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_COLON 40"), .datos = "#define T_COLON 40" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_COMMA 41"), .datos = "#define T_COMMA 41" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_NL 42"), .datos = "#define T_NL 42" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_INDENT 43"), .datos = "#define T_INDENT 43" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_DEDENT 44"), .datos = "#define T_DEDENT 44" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_EOF 57"), .datos = "#define T_EOF 57" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_STRUCT 10"), .datos = "#define T_STRUCT 10" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_AND 14"), .datos = "#define T_AND 14" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_OR 15"), .datos = "#define T_OR 15" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_NOT 16"), .datos = "#define T_NOT 16" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_TRUE 17"), .datos = "#define T_TRUE 17" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_FALSE 18"), .datos = "#define T_FALSE 18" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_INSEGURO 46"), .datos = "#define T_INSEGURO 46" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_IMPORTAR_C 47"), .datos = "#define T_IMPORTAR_C 47" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_AMPERSAND 45"), .datos = "#define T_AMPERSAND 45" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define T_EXTERNO 48"), .datos = "#define T_EXTERNO 48" }.datos);
    gen_emitir_nueva_linea(est);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("#define MAX_TOKS 65536"), .datos = "#define MAX_TOKS 65536" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("typedef struct { int tipo; int linea; int col; char val[256]; } _P_Token;"), .datos = "typedef struct { int tipo; int linea; int col; char val[256]; } _P_Token;" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("// Global state from estado_global.syn"), .datos = "// Global state from estado_global.syn" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("_P_Token _P_tks[MAX_TOKS];"), .datos = "_P_Token _P_tks[MAX_TOKS];" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("int _P_ntks = 0, _P_tpos = 0, _P_p_err = 0;"), .datos = "int _P_ntks = 0, _P_tpos = 0, _P_p_err = 0;" }.datos);
    gen_emitir_linea(est, (CadenaSegura){ .longitud = (int)strlen("int _P_pila_indent[64], _P_nivel_pila = 0;"), .datos = "int _P_pila_indent[64], _P_nivel_pila = 0;" }.datos);
    gen_emitir_nueva_linea(est);
}

CadenaSegura gen_obtener_salida(struct GeneradorCEst est) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        if (est.buf_longitud > 0 && est.buf_lineas) {
            ((char*)est.buf_lineas)[est.buf_longitud] = 0;
            strcpy(_gen_tmp_buf, (const char*)est.buf_lineas);
        } else {
            strcpy(_gen_tmp_buf, "");
        }
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_419 = r;
    return _ret_419;
}

void gen_visitar_nodo(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        if (idx < 0 || idx >= total_nodos) return;
        int* _np = (int*)nodos + idx * 11;
        int _tipo = _np[0];
        uintptr_t _fstr = (uintptr_t)(unsigned int)_np[4] | ((uintptr_t)(int)_np[10] << 32); const char* _str = _fstr ? (const char*)_fstr : "";
        int _izq = _np[6];
        int _der = _np[7];
        int _her = _np[8];
        int _extra = _np[9];
        char _buf[4096], _buf2[4096];

        if (_tipo == 2)  { gen_visitar_funcion(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 3)  { gen_visitar_si(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 4)  { gen_visitar_mientras(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 5)  { gen_visitar_retornar(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 6)  { gen_visitar_expr_stmt(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 7)  { gen_visitar_asignacion(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 16) { gen_visitar_estructura(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 17) { snprintf(_buf, 4096, "/* importar %s */", _str); gen_emitir_linea(est, _buf); return; }
        if (_tipo == 18) { gen_visitar_lanzar(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 19) { gen_visitar_escuchar(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 20) { gen_emitir_linea(est, "break;"); return; }
        if (_tipo == 21) { gen_emitir_linea(est, "continue;"); return; }
        if (_tipo == 40) { gen_escribir_cadena_escapada(est, _str); return; }
        if (_tipo == 25) {
            if (_der) {
                snprintf(_buf, 4096, "#include <%s>", _str);
            } else {
                snprintf(_buf, 4096, "#include \"%s\"", _str);
            }
            gen_emitir_linea(est, _buf); return;
        }
        if (_tipo == 26) { gen_visitar_externo(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 23) { gen_visitar_constante(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 24) {
            gen_emitir_linea(est, "{ /* unsafe */");
            est.indent_actual = est.indent_actual + 1;
            gen_visitar_bloque_lista(est, nodos, total_nodos, tokens, total_tokens, _izq);
            est.indent_actual = est.indent_actual - 1;
            gen_emitir_linea(est, "}"); return;
        }
        if (_tipo == 34) { gen_visitar_declaracion(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 35) { gen_visitar_log(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 32) { gen_visitar_asignacion_campo(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 38) { gen_visitar_coincidir(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 42) { gen_visitar_enviar_canal(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 45) { gen_visitar_para(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        if (_tipo == 27) { gen_visitar_recuperar(est, nodos, total_nodos, tokens, total_tokens, idx); return; }
        // Fallback: expression statement;
        gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, idx, _buf, 4096);
        snprintf(_buf2, 4096, "%s;", _buf);
        gen_emitir_linea(est, _buf2);
    }
}

void gen_visitar_bloque_lista(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int _cur = idx;
        while (_cur > 0 && _cur < total_nodos) {
            gen_visitar_nodo(est, nodos, total_nodos, tokens, total_tokens, _cur);
            _cur = ((int*)nodos)[_cur * 11 + 8]; // hermano;
        }
    }
}

void gen_visitar_funcion(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        const char* _name = (const char*)_np[4];
        const char* _ret = (const char*)_np[5];
        int _params = _np[6];
        int _body = _np[7];
        if (!_name) return;
        // Check already emitted;
        for (int _fi = 0; _fi < est.funciones_emitidas; _fi++) {
            if (strcmp(est.func_emitidas_nombres.datos + _fi * 64, _name) == 0) return;
        }
        strcpy(est.func_emitidas_nombres.datos + est.funciones_emitidas * 64, _name);
        est.funciones_emitidas = est.funciones_emitidas + 1;
        // Skip runtime builtins;
        const char* _skip[] = {"escribir","escribir_linea","leer_linea","abrir","leer","cerrar","crear_tensor","suma_tensor","producto_punto","relu","reserva","libera","suma","producto","math_crear_tensor","math_suma_tensor","math_producto_punto","math_relu","mem_reserva","mem_libera","math_suma","math_producto","texto_a_entero","texto_a_decimal","decimal_a_texto","entero_a_texto",NULL};
        for (int _si = 0; _skip[_si]; _si++) {
            if (strcmp(_name, _skip[_si]) == 0) return;
        }
        // Handle special compiler functions;
        if (strcmp(_name, "tokenizar") == 0) { gen_emitir_tokenizar_c(est); return; }
        if (strcmp(_name, "parsear") == 0) { gen_emitir_parsear_c(est); return; }
        if (strcmp(_name, "generar") == 0) { gen_emitir_generar_c(est); return; }
        if (strcmp(_name, "volcar_ast") == 0) { gen_emitir_volcar_ast_c(est); return; }
        // Build params;
        char _params_str[4096] = "void";
        int _ppos = 0, _first = 1;
        int _pcur = _params;
        while (_pcur > 0 && _pcur < total_nodos) {
            int* _pp = (int*)nodos + _pcur * 11;
            if (_pp[0] == 15) {
                const char* _pn = (const char*)_pp[4];
                const char* _pt = (const char*)_pp[5];
                if (_first) { _ppos = 0; _first = 0; } else { _params_str[_ppos++] = ','; _params_str[_ppos++] = ' '; }
                traducir_tipo_c(_pt);
                int _k = 0; while (_gen_tmp_buf[_k]) _params_str[_ppos++] = _gen_tmp_buf[_k++];
                _params_str[_ppos++] = ' ';
                _k = 0; while (_pn[_k]) _params_str[_ppos++] = _pn[_k++];
            }
            _pcur = _pp[8];
        }
        _params_str[_ppos] = 0;
        // Return type;
        char _ret_type[64];
        traducir_tipo_c(_ret);
        strcpy(_ret_type, _gen_tmp_buf);
        strcpy(est.func_retorno_actual.datos, _ret_type);
        // Emit function;
        char _buf[4096];
        snprintf(_buf, 4096, "%s %s(%s) {", _ret_type, _name, _params_str);
        gen_emitir_linea(est, _buf);
        est.indent_actual = est.indent_actual + 1;
        gen_push_scope(est);
        // Contract: requiere assertions;
        int _contract = _np[9];
        if (_contract > 0 && _contract < total_nodos) {
            int* _cp = (int*)nodos + _contract * 11;
            int _req_head = _cp[6];
            int _gnt_head = _cp[7];
            if (_req_head > 0) {
                gen_emitir_linea(est, "#ifndef SYNAPSE_RELEASE");
                int _rc = _req_head;
                while (_rc > 0 && _rc < total_nodos) {
                    char _expr_str[4096];
                    gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _rc, _expr_str, 4096);
                    char _assert_buf[4096];
                    snprintf(_assert_buf, 4096, "assert((%%s) && \"Fallo en contrato: requiere\");", _expr_str);
                    gen_emitir_linea(est, _assert_buf);
                    int* _ep = (int*)nodos + _rc * 11;
                    _rc = _ep[8];
                }
                gen_emitir_linea(est, "#endif");
            }
            est.garantizas_total = _gnt_head;
        } else {
            est.garantizas_total = 0;
        }
        gen_visitar_bloque_lista(est, nodos, total_nodos, tokens, total_tokens, _body);
        // Contract: garantiza assertions at function exit (void implicit return);
        if (est.garantizas_total > 0) {
            gen_emitir_linea(est, "#ifndef SYNAPSE_RELEASE");
            int _gc = est.garantizas_total;
            while (_gc > 0 && _gc < total_nodos) {
                char _expr_str[4096];
                gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _gc, _expr_str, 4096);
                char _assert_buf[4096];
                snprintf(_assert_buf, 4096, "assert((%%s) && \"Fallo en contrato: garantiza (final)\");", _expr_str);
                gen_emitir_linea(est, _assert_buf);
                int* _ep = (int*)nodos + _gc * 11;
                _gc = _ep[8];
            }
            gen_emitir_linea(est, "#endif");
        }
        gen_pop_scope(est);
        est.indent_actual = est.indent_actual - 1;
        gen_emitir_linea(est, "}");
        gen_emitir_nueva_linea(est);
        est.garantizas_total = 0;
    }
}

void gen_visitar_si(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        int _cond = _np[6];
        int _body = _np[7];
        int _sino = _np[8];
        char _cond_str[4096];
        gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _cond, _cond_str, 4096);
        char _buf[4096];
        snprintf(_buf, 4096, "if (%s) {", _cond_str);
        gen_emitir_linea(est, _buf);
        est.indent_actual = est.indent_actual + 1;
        gen_visitar_bloque_lista(est, nodos, total_nodos, tokens, total_tokens, _body);
        est.indent_actual = est.indent_actual - 1;
        if (_sino > 0 && _sino < total_nodos) {
            gen_emitir_linea(est, "} else {");
            est.indent_actual = est.indent_actual + 1;
            gen_visitar_bloque_lista(est, nodos, total_nodos, tokens, total_tokens, _sino);
            est.indent_actual = est.indent_actual - 1;
        }
        gen_emitir_linea(est, "}");
    }
}

void gen_visitar_mientras(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        int _cond = _np[6];
        int _body = _np[7];
        char _cond_str[4096];
        gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _cond, _cond_str, 4096);
        char _buf[4096];
        snprintf(_buf, 4096, "while (%s) {", _cond_str);
        gen_emitir_linea(est, _buf);
        est.indent_actual = est.indent_actual + 1;
        gen_push_scope(est);
        gen_visitar_bloque_lista(est, nodos, total_nodos, tokens, total_tokens, _body);
        gen_pop_scope(est);
        est.indent_actual = est.indent_actual - 1;
        gen_emitir_linea(est, "}");
    }
}

void gen_visitar_retornar(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        int _expr = _np[6];
        // Contract: garantiza assertions before return;
        if (est.garantizas_total > 0) {
            gen_emitir_linea(est, "#ifndef SYNAPSE_RELEASE");
            int _gc = est.garantizas_total;
            while (_gc > 0 && _gc < total_nodos) {
                char _expr_str[4096];
                gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _gc, _expr_str, 4096);
                char _assert_buf[4096];
                snprintf(_assert_buf, 4096, "assert((%%s) && \"Fallo en contrato: garantiza\");", _expr_str);
                gen_emitir_linea(est, _assert_buf);
                int* _ep = (int*)nodos + _gc * 11;
                _gc = _ep[8];
            }
            gen_emitir_linea(est, "#endif");
        }
        char _buf[4096];
        gen_emit_all_destructors(est, "");
        if (_expr > 0 && _expr < total_nodos) {
            char _val[4096];
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _expr, _val, 4096);
            snprintf(_buf, 4096, "return %s;", _val);
        } else {
            snprintf(_buf, 4096, "return;");
        }
        gen_emitir_linea(est, _buf);
    }
}

void gen_visitar_expr_stmt(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        int _expr = _np[6];
        if (_expr <= 0 || _expr >= total_nodos) return;
        int* _ep = (int*)nodos + _expr * 11;
        char _buf[4096];
        if (_ep[0] == 14) {
            const char* _fn = (const char*)_ep[4];
            if (_fn && strcmp(_fn, "log") == 0);
                { gen_visitar_log(est, nodos, total_nodos, tokens, total_tokens, _expr); return; }
            if (_fn && strcmp(_fn, "asm") == 0);
                { gen_visitar_asm(est, nodos, total_nodos, tokens, total_tokens, _expr); return; }
        }
        if (_ep[0] == 8) {
            return;
        }
        char _val[4096];
        gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _expr, _val, 4096);
        snprintf(_buf, 4096, "%s;", _val);
        gen_emitir_linea(est, _buf);
    }
}

void gen_visitar_asignacion(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        const char* _name = (const char*)_np[4];
        int _expr = _np[6];
        if (!_name || _expr <= 0) return;
        char _val[4096], _buf[4096];
        gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _expr, _val, 4096);
        int _vi = gen_find_var(est, _name);
        if (_vi < 0) {
            // ALL_CAPS names -> #define (constant convention);
            { const char* _pc = _name; int _is_const = 1; while (*_pc) { if (!((*_pc >= 'A' && *_pc <= 'Z') || (*_pc >= '0' && *_pc <= '9') || *_pc == '_')) { _is_const = 0; break; } _pc++; } if (_is_const && strlen(_name) > 0) { snprintf(_buf, 4096, "#define %s (%s)", _name, _val); gen_emitir_linea(est, _buf); gen_add_var(est, _name, "int"); return; } };
            gen_tipo_de_expr(est, nodos, total_nodos, tokens, total_tokens, _expr);
            if (strcmp(_gen_tmp_buf,"int")!=0&&strcmp(_gen_tmp_buf,"float")!=0&&strcmp(_gen_tmp_buf,"double")!=0&&strcmp(_gen_tmp_buf,"char")!=0&&strcmp(_gen_tmp_buf,"CadenaSegura")!=0&&strcmp(_gen_tmp_buf,"void")!=0&&strcmp(_gen_tmp_buf,"Tensor")!=0&&strcmp(_gen_tmp_buf,"Canal")!=0&&strcmp(_gen_tmp_buf,"CanalConcurrencia*")!=0&&strcmp(_gen_tmp_buf,"Resultado_T")!=0) snprintf(_buf, 4096, "struct %s %s = {0};", _gen_tmp_buf, _name);
            else snprintf(_buf, 4096, "%s %s = %s;", _gen_tmp_buf, _name, _val);
            gen_emitir_linea(est, _buf);
            gen_add_var(est, _name, _gen_tmp_buf);
        } else {
            // Skip reassignment for constants (already #define'd);
            { const char* _pc = _name; int _is_const = 1; while (*_pc) { if (!((*_pc >= 'A' && *_pc <= 'Z') || (*_pc >= '0' && *_pc <= '9') || *_pc == '_')) { _is_const = 0; break; } _pc++; } if (_is_const && strlen(_name) > 0) { return; } };
            snprintf(_buf, 4096, "%s = %s;", _name, _val);
            gen_emitir_linea(est, _buf);
        }
    }
}

void gen_visitar_declaracion(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        const char* _name = (const char*)_np[4];
        const char* _type = (const char*)_np[5];
        int _expr = _np[6];
        if (!_name || !_type) return;
        char _val[4096] = "";
        if (_expr > 0 && _expr < total_nodos);
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _expr, _val, 4096);
        char _ct[64]; traducir_tipo_c(_type); strcpy(_ct, _gen_tmp_buf);
        char _buf[4096];
        int _vi = gen_find_var(est, _name);
        if (_vi < 0) {
            if (_val[0]) snprintf(_buf, 4096, "%s %s = %s;", _ct, _name, _val);
            else snprintf(_buf, 4096, "%s %s = {0};", _ct, _name);
            gen_emitir_linea(est, _buf);
            gen_add_var(est, _name, _ct);
        } else {
            if (_val[0]) snprintf(_buf, 4096, "%s = %s;", _name, _val);
            else snprintf(_buf, 4096, "%s = {0};", _name);
            gen_emitir_linea(est, _buf);
            gen_set_var_type(est, _vi, _ct);
        }
    }
}

void gen_visitar_estructura(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        const char* _name = (const char*)_np[4];
        int _fields = _np[6];
        if (!_name) return;
        char _buf[4096], _buf2[4096];
        snprintf(_buf, 4096, "typedef struct %s {", _name);
        gen_emitir_linea(est, _buf);
        est.indent_actual = est.indent_actual + 1;
        int _fcur = _fields;
        while (_fcur > 0 && _fcur < total_nodos) {
            int* _fp = (int*)nodos + _fcur * 11;
            if (_fp[0] == 15) {
                const char* _fn = (const char*)_fp[4];
                const char* _ft = (const char*)_fp[5];
                traducir_tipo_c(_ft);
                snprintf(_buf2, 4096, "%s %s;", _gen_tmp_buf, _fn);
                gen_emitir_linea(est, _buf2);
            }
            _fcur = _fp[8];
        }
        est.indent_actual = est.indent_actual - 1;
        snprintf(_buf, 4096, "} %s;", _name);
        gen_emitir_linea(est, _buf);
        snprintf(_buf, 4096, "static inline struct %s %s_nuevo() { struct %s _r = {0}; return _r; }", _name, _name, _name);
        gen_emitir_linea(est, _buf);
        gen_emitir_nueva_linea(est);
        gen_agregar_struct_c(est, _name);
    }
}

void gen_visitar_constante(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        const char* _name = (const char*)_np[4];
        int _expr = _np[6];
        if (!_name || _expr <= 0) return;
        char _val[4096], _buf[4096];
        gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _expr, _val, 4096);
        snprintf(_buf, 4096, "#define %s (%s)", _name, _val);
        gen_emitir_linea(est, _buf);
    }
}

void gen_visitar_externo(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        const char* _name = (const char*)_np[4];
        const char* _ret = (const char*)_np[5];
        int _params = _np[6];
        if (!_name || !_ret) return;
        char _ret_c[64]; traducir_tipo_c(_ret); strcpy(_ret_c, _gen_tmp_buf);
        char _params_str[4096] = "void";
        int _ppos = 0, _first = 1;
        int _pcur = _params;
        while (_pcur > 0 && _pcur < total_nodos) {
            int* _pp = (int*)nodos + _pcur * 11;
            if (_pp[0] == 15) {
                const char* _pn = (const char*)_pp[4];
                const char* _pt = (const char*)_pp[5];
                if (_first) { _ppos = 0; _first = 0; } else { _params_str[_ppos++] = ','; _params_str[_ppos++] = ' '; }
                traducir_tipo_c(_pt);
                int _k = 0; while (_gen_tmp_buf[_k]) _params_str[_ppos++] = _gen_tmp_buf[_k++];
                _params_str[_ppos++] = ' ';
                _k = 0; while (_pn[_k]) _params_str[_ppos++] = _pn[_k++];
            }
            _pcur = _pp[8];
        }
        _params_str[_ppos] = 0;
        char _buf[4096];
        snprintf(_buf, 4096, "extern %s %s(%s);", _ret_c, _name, _params_str);
        gen_emitir_linea(est, _buf);
    }
}

void gen_visitar_log(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        int _args = _np[6];
        char _fmt[4096] = ""; int _fpos = 0;
        char _pr[4096] = ""; int _ppos = 0;
        int _first = 1;
        int _acur = _args;
        while (_acur > 0 && _acur < total_nodos) {
            if (!_first) { _fmt[_fpos++] = ' '; } _first = 0;
            _fmt[_fpos++] = '%'; _fmt[_fpos++] = 's';
            char _arg_str[4096];
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _acur, _arg_str, 4096);
            if (_ppos > 0) { _pr[_ppos++] = ','; _pr[_ppos++] = ' '; }
            int _k = 0; while (_arg_str[_k]) _pr[_ppos++] = _arg_str[_k++];
            _acur = ((int*)nodos)[_acur * 11 + 8];
        }
        _fmt[_fpos] = 0; _pr[_ppos] = 0;
        char _buf[4096];
        if (_ppos > 0) {
            snprintf(_buf, 4096, "printf(\"%%s\\n\", %s);", _pr);
        } else {
            snprintf(_buf, 4096, "printf(\"%%s\\n\");");
        }
        gen_emitir_linea(est, _buf);
    }
}

void gen_visitar_asm(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        int _args = _np[6];
        if (_args <= 0 || _args >= total_nodos) return;
        int* _ap = (int*)nodos + _args * 11; if (_ap[0] == 11) {
            uintptr_t _fstr = (uintptr_t)(unsigned int)_ap[4] | ((uintptr_t)(int)_ap[10] << 32); const char* _str = _fstr ? (const char*)_fstr : "";
            char _buf[4096], _esc[4096]; int _epos = 0;
            for (int _i = 0; _str[_i] && _epos < 4090; _i++) {
                if (_str[_i] == '\\') { _esc[_epos++] = '\\'; _esc[_epos++] = '\\'; }
                else if (_str[_i] == '"') { _esc[_epos++] = '\\'; _esc[_epos++] = '"'; }
                else if (_str[_i] == 10) { _esc[_epos++] = '\\'; _esc[_epos++] = 'n'; }
                else if (_str[_i] == 9) { _esc[_epos++] = '\\'; _esc[_epos++] = 't'; }
                else if (_str[_i] == 13) { _esc[_epos++] = '\\'; _esc[_epos++] = 'r'; }
                else _esc[_epos++] = _str[_i];
            }
            _esc[_epos] = 0;
            snprintf(_buf, 4096, "asm(\"%s\");", _esc);
            gen_emitir_linea(est, _buf);
        } else {
            char _arg_str[4096], _buf[4096];
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _args, _arg_str, 4096);
            snprintf(_buf, 4096, "asm(%s);", _arg_str);
            gen_emitir_linea(est, _buf);
        }
    }
}

void gen_visitar_asignacion_campo(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        const char* _campo = (const char*)_np[4];
        int _obj = _np[6];
        int _expr = _np[7];
        if (!_campo || _obj <= 0) return;
        char _obj_str[4096], _val[4096], _buf[4096];
        gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _obj, _obj_str, 4096);
        gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _expr, _val, 4096);
        snprintf(_buf, 4096, "%s.%s = %s;", _obj_str, _campo, _val);
        gen_emitir_linea(est, _buf);
    }
}

void gen_visitar_lanzar(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        int _call = _np[6];
        if (_call <= 0) return;
        int* _cp = (int*)nodos + _call * 11;
        char _buf[4096];
        if (_cp[0] == 14) {
            const char* _fn = (const char*)_cp[4];
            int _args = _cp[6];
            char _arg_val[512] = "";
            int _has_arg = 0;
            if (_args > 0 && _args < total_nodos) {
                gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _args, _arg_val, 512);
                _has_arg = 1;
            }
            if (_has_arg) {
                snprintf(_buf, 4096, "synapse_lanzar_hilo((void*(*)(void*))%s, (void*)(intptr_t)(%s));", _fn, _arg_val);
            } else {
                snprintf(_buf, 4096, "synapse_lanzar_hilo((void*(*)(void*))%s, NULL);", _fn);
            }
            gen_emitir_linea(est, _buf);
        }
    }
}

void gen_visitar_recuperar(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        int _accion = _np[6];
        int _plan = _np[7];
        if (_accion <= 0 || _plan <= 0) return;
        char _acc_str[4096], _plan_str[4096], _buf[4096];
        gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _accion, _acc_str, 4096);
        gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _plan, _plan_str, 4096);
        gen_emitir_linea(est, "{");
        est.indent_actual = est.indent_actual + 1;
        snprintf(_buf, 4096, "if (%s != 0) { %s; }", _acc_str, _plan_str);
        gen_emitir_linea(est, _buf);
        est.indent_actual = est.indent_actual - 1;
        gen_emitir_linea(est, "}");
    }
}

void gen_visitar_escuchar(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        int _canal = _np[6];
        int _respu = _np[7];
        if (_canal <= 0 || _respu <= 0) return;
        est.contador_listener = est.contador_listener + 1;
        int _lid = est.contador_listener;
        char _canal_str[4096], _buf[4096];
        gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _canal, _canal_str, 4096);
        int* _rp = (int*)nodos + _respu * 11;
        const char* _rname = (_rp[0] == 14) ? (const char*)_rp[4] : "/* error */";
        if (!_rname) _rname = "/* error */";
        char _listener[4096];
        int _lpos = 0;
        _lpos += snprintf(_listener + _lpos, 4096 - _lpos, "void* _listener_fn_%d(void* arg) {", _lid);
        _lpos += snprintf(_listener + _lpos, 4096 - _lpos, "\n    (void)arg;");
        _lpos += snprintf(_listener + _lpos, 4096 - _lpos, "\n    CanalConcurrencia* _canal = %s;", _canal_str);
        _lpos += snprintf(_listener + _lpos, 4096 - _lpos, "\n    while (1) {");
        _lpos += snprintf(_listener + _lpos, 4096 - _lpos, "\n        void* _paquete = canal_recibir(_canal);");
        _lpos += snprintf(_listener + _lpos, 4096 - _lpos, "\n        if (!_paquete) break;");
        _lpos += snprintf(_listener + _lpos, 4096 - _lpos, "\n        %s(_paquete);", _rname);
        _lpos += snprintf(_listener + _lpos, 4096 - _lpos, "\n    }");
        _lpos += snprintf(_listener + _lpos, 4096 - _lpos, "\n    return NULL;");
        _lpos += snprintf(_listener + _lpos, 4096 - _lpos, "\n}");
        strcpy(est.listener_funciones.datos + est.listener_total * 4096, _listener);
        est.listener_total = est.listener_total + 1;
        snprintf(_buf, 4096, "pthread_t _listener_pth_%d;", _lid);
        gen_emitir_linea(est, _buf);
        snprintf(_buf, 4096, "pthread_create(&_listener_pth_%d, NULL, _listener_fn_%d, NULL);", _lid, _lid);
        gen_emitir_linea(est, _buf);
        snprintf(_buf, 4096, "pthread_detach(_listener_pth_%d);", _lid);
        gen_emitir_linea(est, _buf);
    }
}

void gen_visitar_enviar_canal(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        int _canal = _np[6];
        int _valor = _np[7];
        if (_canal <= 0 || _valor <= 0) return;
        char _canal_str[4096], _val_str[4096], _buf[4096];
        gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _canal, _canal_str, 4096);
        gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _valor, _val_str, 4096);
        gen_tipo_de_expr(est, nodos, total_nodos, tokens, total_tokens, _valor);
        if (strcmp(_gen_tmp_buf, "int") == 0) {
            char _boxed[4096]; strcpy(_boxed, prim_int_to_ptr(_val_str).datos);
            snprintf(_buf, 4096, "canal_enviar(%s, %s);", _canal_str, _boxed);
        } else if (strcmp(_gen_tmp_buf, "float") == 0) {
            char _boxed[4096]; strcpy(_boxed, prim_float_to_ptr(_val_str).datos);
            snprintf(_buf, 4096, "canal_enviar(%s, %s);", _canal_str, _boxed);
        } else {
            snprintf(_buf, 4096, "canal_enviar(%s, (void*)(%s));", _canal_str, _val_str);
        }
        gen_emitir_linea(est, _buf);
    }
}

void gen_visitar_para(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        int _init = _np[6];
        int _cond = _np[7];
        int _inc = _np[8];
        int _body = _np[9];
        char _buf[4096];
        // Handle init;
        if (_init > 0 && _init < total_nodos) {
            int* _ip = (int*)nodos + _init * 11;
            if (_ip[0] == 7) {
                const char* _iname = (const char*)_ip[4];
                int _iexpr = _ip[6];
                char _ival[4096];
                gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _iexpr, _ival, 4096);
                if (_iname && gen_find_var(est, _iname) < 0) {
                    gen_tipo_de_expr(est, nodos, total_nodos, tokens, total_tokens, _iexpr);
                    snprintf(_buf, 4096, "%s %s = %s;", _gen_tmp_buf, _iname, _ival);
                    gen_emitir_linea(est, _buf);
                    gen_add_var(est, _iname, _gen_tmp_buf);
                } else if (_iname) {
                    snprintf(_buf, 4096, "%s = %s;", _iname, _ival);
                    gen_emitir_linea(est, _buf);
                }
            }
        }
        char _cond_str[4096] = "1";
        if (_cond > 0 && _cond < total_nodos);
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _cond, _cond_str, 4096);
        char _inc_str[4096] = "";
        if (_inc > 0 && _inc < total_nodos) {
            int* _ip2 = (int*)nodos + _inc * 11;
            if (_ip2[0] == 7);
                gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _ip2[6], _inc_str, 4096);
        }
        snprintf(_buf, 4096, "for (; %s; %s) {", _cond_str, _inc_str);
        gen_emitir_linea(est, _buf);
        est.indent_actual = est.indent_actual + 1;
        gen_push_scope(est);
        gen_visitar_bloque_lista(est, nodos, total_nodos, tokens, total_tokens, _body);
        gen_pop_scope(est);
        est.indent_actual = est.indent_actual - 1;
        gen_emitir_linea(est, "}");
    }
}

void gen_visitar_coincidir(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        int* _np = (int*)nodos + idx * 11;
        int _expr = _np[6];
        int _casos = _np[7];
        if (_expr <= 0) return;
        char _expr_str[4096], _buf[4096], _buf2[4096];
        gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _expr, _expr_str, 4096);
        snprintf(_buf, 4096, "/* match: %s */", _expr_str);
        gen_emitir_linea(est, _buf);
        int _ccur = _casos, _caso_idx = 0;
        while (_ccur > 0 && _ccur < total_nodos) {
            int* _cp = (int*)nodos + _ccur * 11;
            if (_cp[0] == 39) {
                const char* _tag = (const char*)_cp[4];
                const char* _var = (const char*)_cp[5];
                int _cuerpo = _cp[6];
                if (_caso_idx == 0) {
                    snprintf(_buf, 4096, "if (%s.tag == TAG_%s) {", _expr_str, _tag);
                } else {
                    snprintf(_buf, 4096, "} else if (%s.tag == TAG_%s) {", _expr_str, _tag);
                }
                gen_emitir_linea(est, _buf);
                est.indent_actual = est.indent_actual + 1;
                if (_var && _var[0]) {
                    snprintf(_buf2, 4096, "int %s = %s.valor;", _var, _expr_str);
                    gen_emitir_linea(est, _buf2);
                }
                gen_visitar_bloque_lista(est, nodos, total_nodos, tokens, total_tokens, _cuerpo);
                est.indent_actual = est.indent_actual - 1;
                _caso_idx = _caso_idx + 1;
            }
            _ccur = _cp[8];
        }
        if (_caso_idx > 0) gen_emitir_linea(est, "}");
    }
}

void gen_expr_a_c(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx, void* buf, int bufsz) {
    { /* unsafe */
        if (idx <= 0 || idx >= total_nodos) { snprintf(buf, bufsz, "0"); return; }
        int* _np = (int*)nodos + idx * 11;
        int _tipo = _np[0];
        uintptr_t _fstr = (uintptr_t)(unsigned int)_np[4] | ((uintptr_t)(int)_np[10] << 32); const char* _str = _fstr ? (const char*)_fstr : "";
        int _vint = _np[3];
        char _l[4096], _r[4096];

        if (_tipo == 9)  { snprintf(buf, bufsz, "%d", _vint); return; }
        if (_tipo == 10) { snprintf(buf, bufsz, "%ff", *(float*)&_vint); return; }
        if (_tipo == 11) { int _len = _np[5]; snprintf(buf, bufsz, "(CadenaSegura){.longitud=%d,.datos=(char*)%s}", _len, _str); return; }
        if (_tipo == 8)  {
            if (strcmp(_str, "nulo") == 0) { snprintf(buf, bufsz, "NULL"); return; }
            snprintf(buf, bufsz, "%s", _str); return;
        }
        if (_tipo == 12) { // OpBinaria;
            int _op = _np[5]; int _izq = _np[6]; int _der = _np[7];
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _izq, _l, 4096);
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _der, _r, 4096);
            const char* _os = "+";
            if (_op == 25) { _os = "=="; gen_tipo_de_expr(est, nodos, total_nodos, tokens, total_tokens, _izq); char _t1[64]; strcpy(_t1, _gen_tmp_buf); gen_tipo_de_expr(est, nodos, total_nodos, tokens, total_tokens, _der); char _t2[64]; strcpy(_t2, _gen_tmp_buf); if (strcmp(_t1, "CadenaSegura") == 0 && strcmp(_t2, "CadenaSegura") == 0) { snprintf(buf, bufsz, "(strcmp(%s, %s) == 0)", _l, _r); return; } } else if (_op == 26) { _os = "!="; gen_tipo_de_expr(est, nodos, total_nodos, tokens, total_tokens, _izq); char _t1[64]; strcpy(_t1, _gen_tmp_buf); gen_tipo_de_expr(est, nodos, total_nodos, tokens, total_tokens, _der); char _t2[64]; strcpy(_t2, _gen_tmp_buf); if (strcmp(_t1, "CadenaSegura") == 0 && strcmp(_t2, "CadenaSegura") == 0) { snprintf(buf, bufsz, "(strcmp(%s, %s) != 0)", _l, _r); return; } } else if (_op == 23) _os = ">"; else if (_op == 24) _os = "<"; else if (_op == 27) _os = "<="; else if (_op == 28) _os = ">="; else if (_op == 30) _os = "+"; else if (_op == 31) _os = "-"; else if (_op == 32) _os = "*"; else if (_op == 33) _os = "/"; else if (_op == 34) _os = "%"; else if (_op == 14) _os = "&&"; else if (_op == 15) _os = "||";
            snprintf(buf, bufsz, "(%s %s %s)", _l, _os, _r); return;
        }
        if (_tipo == 13) { // OpUnaria;
            int _op = _np[5]; int _expr = _np[6];
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _expr, _l, 4096);
            const char* _os = "-";
            if (_op == 30) _os = "+"; else if (_op == 16) _os = "!";
            snprintf(buf, bufsz, "(%s%s)", _os, _l); return;
        }
        if (_tipo == 14) { // LlamadaFuncion;
            char _fn[256]; strcpy(_fn, _str);
            for (char* _p = _fn; *_p; _p++) if (*_p == '.') *_p = '_';
            int _args = _np[6];
            char _args_str[4096] = ""; int _apos = 0; int _acur = _args;
            while (_acur > 0 && _acur < total_nodos) {
                if (_apos > 0) { _args_str[_apos++] = ','; _args_str[_apos++] = ' '; }
                gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _acur, _l, 4096);
                int _k = 0; while (_l[_k]) _args_str[_apos++] = _l[_k++];
                _acur = ((int*)nodos)[_acur * 11 + 8];
            }
            _args_str[_apos] = 0;
            snprintf(buf, bufsz, "%s(%s)", _fn, _args_str); return;
        }
        if (_tipo == 31) { // AccesoCampo;
            int _obj = _np[6];
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _obj, _l, 4096);
            snprintf(buf, bufsz, "%s.%s", _l, _str); return;
        }
        if (_tipo == 22) { snprintf(buf, bufsz, "%d", _vint ? 1 : 0); return; }
        if (_tipo == 28) { // Tensor;
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _np[6], _l, 4096);
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _np[7], _r, 4096);
            snprintf(buf, bufsz, "(Tensor){.filas=%s,.columnas=%s,.datos=(float*)calloc(%s*%s,sizeof(float))}", _l, _r, _l, _r); return;
        }
        if (_tipo == 30 || _tipo == 36 || _tipo == 37) {
            int _inner = _np[6];
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _inner, _l, 4096);
            if (_tipo == 36) { snprintf(buf, bufsz, "(&%s)", _l); return; }
            if (_tipo == 37) { snprintf(buf, bufsz, "(*%s)", _l); return; }
            snprintf(buf, bufsz, "%s", _l); return;
        }
        if (_tipo == 40) { snprintf(buf, bufsz, "%s", _str); return; }
        if (_tipo == 41) {
            if (_np[6] > 0 && _np[6] < total_nodos) {
                gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _np[6], _l, 4096);
                snprintf(buf, bufsz, "canal_crear(%s)", _l);
            } else snprintf(buf, bufsz, "canal_crear(10)");
            return;
        }
        if (_tipo == 43) {
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _np[6], _l, 4096);
            snprintf(buf, bufsz, "(Resultado_T){.es_ok=1,.datos={.ok_valor=canal_recibir(%s)}}", _l); return;
        }
        snprintf(buf, bufsz, "/*?*/");
    }
}

void gen_tipo_de_expr(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        if (idx <= 0 || idx >= total_nodos) { strcpy(_gen_tmp_buf, "int"); return; }
        int* _np = (int*)nodos + idx * 11;
        int _tipo = _np[0];
        uintptr_t _fstr = (uintptr_t)(unsigned int)_np[4] | ((uintptr_t)(int)_np[10] << 32); const char* _str = _fstr ? (const char*)_fstr : "";

        if (_tipo == 9) { strcpy(_gen_tmp_buf, "int"); return; }
        if (_tipo == 10) { strcpy(_gen_tmp_buf, "float"); return; }
        if (_tipo == 11) { strcpy(_gen_tmp_buf, "CadenaSegura"); return; }
        if (_tipo == 22) { strcpy(_gen_tmp_buf, "int"); return; }
        if (_tipo == 28) { strcpy(_gen_tmp_buf, "Tensor"); return; }
        if (_tipo == 36) { gen_tipo_de_expr(est, nodos, total_nodos, tokens, total_tokens, _np[6]);
            char _tmp[64]; strcpy(_tmp, _gen_tmp_buf); snprintf(_gen_tmp_buf, 64, "%s*", _tmp); return; }
        if (_tipo == 37) { gen_tipo_de_expr(est, nodos, total_nodos, tokens, total_tokens, _np[6]);
            int _len = (int)strlen(_gen_tmp_buf); if (_len > 0 && _gen_tmp_buf[_len-1] == '*') _gen_tmp_buf[_len-1] = 0; return; }
        if (_tipo == 30) { gen_tipo_de_expr(est, nodos, total_nodos, tokens, total_tokens, _np[6]); return; }
        if (_tipo == 12) {
            gen_tipo_de_expr(est, nodos, total_nodos, tokens, total_tokens, _np[6]); char _lt[64]; strcpy(_lt, _gen_tmp_buf);
            gen_tipo_de_expr(est, nodos, total_nodos, tokens, total_tokens, _np[7]);
            if (strcmp(_lt, "CadenaSegura")==0 && strcmp(_gen_tmp_buf, "CadenaSegura")==0) return;
            if (strcmp(_lt, "float")==0 || strcmp(_gen_tmp_buf, "float")==0) { strcpy(_gen_tmp_buf, "float"); return; }
            strcpy(_gen_tmp_buf, "int"); return;
        }
        if (_tipo == 13) { gen_tipo_de_expr(est, nodos, total_nodos, tokens, total_tokens, _np[6]);
            if (strcmp(_gen_tmp_buf, "float") != 0) strcpy(_gen_tmp_buf, "int"); return; }
        if (_tipo == 8) {
            if (strcmp(_str, "nulo") == 0) { strcpy(_gen_tmp_buf, "void*"); return; }
            int _vi = gen_find_var(est, _str);
            if (_vi >= 0) { strcpy(_gen_tmp_buf, est.var_tipos.datos + _vi * 64); return; }
            strcpy(_gen_tmp_buf, "int"); return;
        }
        if (_tipo == 14) {
            // _nuevo constructors -> struct return type (ej. LexerEstado_nuevo -> struct LexerEstado);
            { int _nn=(int)strlen(_str); if(_nn>6&&strcmp(_str+_nn-6,"_nuevo")==0){ char _base[256]; memcpy(_base,_str,_nn-6); _base[_nn-6]=0; snprintf(_gen_tmp_buf,64,"struct %s",_base); return; } };
            if (strcmp(_str, "_argc")==0) { strcpy(_gen_tmp_buf, "int"); return; }
            if (strcmp(_str, "_argv")==0||strcmp(_str,"leer")==0||strcmp(_str,"leer_linea")==0||strcmp(_str,"concat")==0||strcmp(_str,"decimal_a_texto")==0||strcmp(_str,"entero_a_texto")==0) { strcpy(_gen_tmp_buf, "CadenaSegura"); return; }
            if (strcmp(_str, "abrir")==0) { strcpy(_gen_tmp_buf, "Canal"); return; }
            if (strcmp(_str, "cerrar")==0||strcmp(_str,"salir")==0||strcmp(_str,"escribir")==0||strcmp(_str,"escribir_linea")==0||strcmp(_str,"libera")==0||strcmp(_str,"volcar_ast")==0||strcmp(_str,"canal_enviar")==0||strcmp(_str,"cerrar_canal")==0) { strcpy(_gen_tmp_buf, "void"); return; }
            if (strcmp(_str, "tokenizar")==0||strcmp(_str,"texto_a_entero")==0) { strcpy(_gen_tmp_buf, "int"); return; }
            if (strcmp(_str, "generar")==0) { strcpy(_gen_tmp_buf, "int"); return; }
            if (strcmp(_str, "texto_a_decimal")==0) { strcpy(_gen_tmp_buf, "float"); return; }
            if (strcmp(_str, "parsear")==0) { strcpy(_gen_tmp_buf, "struct Programa"); return; }
            if (strcmp(_str, "reserva")==0||strcmp(_str,"suma")==0||strcmp(_str,"producto")==0||strcmp(_str,"relu")==0||strcmp(_str,"crear_tensor")==0||strcmp(_str,"suma_tensor")==0||strcmp(_str,"producto_punto")==0) { strcpy(_gen_tmp_buf, "Tensor"); return; }
            if (strcmp(_str, "canal_crear")==0) { strcpy(_gen_tmp_buf, "CanalConcurrencia*"); return; }
            if (strcmp(_str, "canal_recibir")==0) { strcpy(_gen_tmp_buf, "void*"); return; }
            { CadenaSegura _grt = gen_func_return_type(est, _str); strcpy(_gen_tmp_buf, _grt.datos); }
            if (_gen_tmp_buf[0]) return;
            strcpy(_gen_tmp_buf, "int"); return;
        }
        if (_tipo == 31||_tipo==40) { strcpy(_gen_tmp_buf, "int"); return; }
        if (_tipo == 41) { strcpy(_gen_tmp_buf, "CanalConcurrencia*"); return; }
        if (_tipo == 43) { strcpy(_gen_tmp_buf, "Resultado_T"); return; }
        strcpy(_gen_tmp_buf, "int");
    }
}

void gen_emitir_tokenizar_c(struct GeneradorCEst est) {
    { /* unsafe */
        gen_emitir_linea(est, "int tokenizar(CadenaSegura fuente) {");
        est.indent_actual = est.indent_actual + 1;
        gen_emitir_linea(est, "int _i = 0, _linea = 1, _columna = 1, _token_count = 0;");
        gen_emitir_linea(est, "while (_i < fuente.longitud) {");
        est.indent_actual = est.indent_actual + 1;
        gen_emitir_linea(est, "char _c = fuente.datos[_i];");
        gen_emitir_linea(est, "if (_c==' '||_c=='\\t') { _i++; _columna++; continue; }");
        gen_emitir_linea(est, "if (_c=='\\r') { _i++; continue; }");
        gen_emitir_linea(est, "if (_c=='\\n') { _i++; _linea++; _columna=1; continue; }");
        gen_emitir_linea(est, "if (_c=='/'&&_i+1<fuente.longitud&&fuente.datos[_i+1]=='/') { while(_i<fuente.longitud&&fuente.datos[_i]!='\\n')_i++; continue; }");
        gen_emitir_linea(est, "if (_c=='\\\"'||_c=='\\'') { char _q=_c; int _st=_i; _i++; _columna++; while(_i<fuente.longitud&&fuente.datos[_i]!=_q){_i++;_columna++;} if(_i>=fuente.longitud){fprintf(stderr,\"  TOKEN STRING_UNCLOSED L%d:%d\\n\",_linea,_columna);break;} _i++;_columna++;_token_count++;fprintf(stderr,\"  TOKEN STRING L%d:%d\\n\",_linea,_columna); }");
        gen_emitir_linea(est, "else if(_c>='0'&&_c<='9'){int _st=_i;while(_i<fuente.longitud&&fuente.datos[_i]>='0'&&fuente.datos[_i]<='9')_i++;_columna+=_i-_st;_token_count++;fprintf(stderr,\"  TOKEN NUMBER L%d:%d\\n\",_linea,_columna);}");
        gen_emitir_linea(est, "else if((_c>='a'&&_c<='z')||(_c>='A'&&_c<='Z')||_c=='_'){int _st=_i;while(_i<fuente.longitud&&((fuente.datos[_i]>='a'&&fuente.datos[_i]<='z')||(fuente.datos[_i]>='A'&&fuente.datos[_i]<='Z')||(fuente.datos[_i]>='0'&&fuente.datos[_i]<='9')||fuente.datos[_i]=='_'))_i++;_columna+=_i-_st;_token_count++;fprintf(stderr,\"  TOKEN IDENTIFIER L%d:%d\\n\",_linea,_columna);}");
        gen_emitir_linea(est, "else{_i++;_columna++;_token_count++;fprintf(stderr,\"  TOKEN CHAR(%%c)L%d:%d\\n\",_c,_linea,_columna);}");
        est.indent_actual = est.indent_actual - 1;
        gen_emitir_linea(est, "}");
        gen_emitir_linea(est, "fprintf(stderr,\"Total tokens: %%d\\n\",_token_count);");
        gen_emitir_linea(est, "return _token_count;");
        est.indent_actual = est.indent_actual - 1;
        gen_emitir_linea(est, "}");
        gen_emitir_nueva_linea(est);
    }
}

void gen_emitir_parsear_c(struct GeneradorCEst est) {
    gen_emitir_token_defs(est);
    { /* unsafe */
        // Emit P_tokenizar function;
        gen_emitir_linea(est, "void _P_tokenizar(const char* s, int len) {");
        est.indent_actual = est.indent_actual + 1;
        gen_emitir_linea(est, "int i=0,li=1,co=1;");
        gen_emitir_linea(est, "while(i<len&&_P_ntks<MAX_TOKS-1){");
        est.indent_actual = est.indent_actual + 1;
        gen_emitir_linea(est, "char c=s[i];");
        gen_emitir_linea(est, "if(c==' '||c=='\\t'){i++;co++;continue;}");
        gen_emitir_linea(est, "if(c=='\\r'){i++;continue;}");
        gen_emitir_linea(est, "if(c=='\\n'){");
        est.indent_actual = est.indent_actual + 1;
        gen_emitir_linea(est, "_P_tks[_P_ntks].tipo=T_NL;_P_tks[_P_ntks].linea=li;_P_tks[_P_ntks].col=0;_P_ntks++;i++;li++;co=1;");
        gen_emitir_linea(est, "while(i<len&&(s[i]==' '||s[i]=='\\t')){if(s[i]==' ')co++;else co+=4;i++;}");
        gen_emitir_linea(est, "if(i<len&&s[i]=='\\n')continue;");
        gen_emitir_linea(est, "if(i<len&&s[i]=='#'){while(i<len&&s[i]!='\\n')i++;continue;}");
        gen_emitir_linea(est, "if(i<len&&s[i]=='/'&&i+1<len&&s[i+1]=='/'){while(i<len&&s[i]!='\\n')i++;continue;}");
        gen_emitir_linea(est, "{int _sp=co-1;if(_sp>_P_pila_indent[_P_nivel_pila]){_P_nivel_pila++;_P_pila_indent[_P_nivel_pila]=_sp;_P_tks[_P_ntks].tipo=T_INDENT;_P_tks[_P_ntks].linea=li;_P_tks[_P_ntks].col=0;_P_ntks++;}else if(_sp<_P_pila_indent[_P_nivel_pila]){while(_P_nivel_pila>0&&_sp<_P_pila_indent[_P_nivel_pila]){_P_tks[_P_ntks].tipo=T_DEDENT;_P_tks[_P_ntks].linea=li;_P_tks[_P_ntks].col=0;_P_ntks++;_P_nivel_pila--;}}}");
        gen_emitir_linea(est, "continue;");
        est.indent_actual = est.indent_actual - 1;
        gen_emitir_linea(est, "}");
        // Single-char tokens and identifiers... ;
        gen_emitir_linea(est, "if(c=='\\\"'||c=='\\''){char q=c;int st=i;int scol=co;i++;co++;while(i<len&&s[i]!=q){i++;co++;}if(i>=len)break;i++;co++;int vl=(i-st-2)<255?(i-st-2):255;strncpy(_P_tks[_P_ntks].val,s+st+1,vl);_P_tks[_P_ntks].val[vl]=0;_P_tks[_P_ntks].tipo=T_STR;_P_tks[_P_ntks].linea=li;_P_tks[_P_ntks].col=scol;_P_ntks++;continue;}");
        gen_emitir_linea(est, "if(c>='0'&&c<='9'){int st=i;int scol=co;while(i<len&&s[i]>='0'&&s[i]<='9')i++;if(i<len&&s[i]=='.'){i++;while(i<len&&s[i]>='0'&&s[i]<='9')i++;}int vl=(i-st)<255?(i-st):255;strncpy(_P_tks[_P_ntks].val,s+st,vl);_P_tks[_P_ntks].val[vl]=0;_P_tks[_P_ntks].tipo=T_NUM;_P_tks[_P_ntks].linea=li;_P_tks[_P_ntks].col=scol;_P_ntks++;co+=i-st;continue;}");
        est.indent_actual = est.indent_actual - 1;
        gen_emitir_linea(est, "}");
        gen_emitir_linea(est, "while(_P_nivel_pila>0){_P_tks[_P_ntks].tipo=T_DEDENT;_P_tks[_P_ntks].linea=li;_P_tks[_P_ntks].col=0;_P_ntks++;_P_nivel_pila--;}");
        gen_emitir_linea(est, "_P_tks[_P_ntks].tipo=T_EOF;_P_tks[_P_ntks].linea=li;_P_tks[_P_ntks].col=0;_P_ntks++;");
        est.indent_actual = est.indent_actual - 1;
        gen_emitir_linea(est, "}");

        gen_emitir_linea(est, "static void _P_procesar_indentacion_final() {");
        est.indent_actual = est.indent_actual + 1;
        gen_emitir_linea(est, "while(_P_nivel_pila>0){_P_tks[_P_ntks].tipo=T_DEDENT;_P_tks[_P_ntks].linea=_P_tks[_P_ntks-1].linea;_P_tks[_P_ntks].col=0;_P_ntks++;_P_nivel_pila--;}");
        est.indent_actual = est.indent_actual - 1;
        gen_emitir_linea(est, "}");
        gen_emitir_nueva_linea(est);

        // Parser entry point;
        gen_emitir_linea(est, "struct Programa parsear(CadenaSegura fuente) {");
        est.indent_actual = est.indent_actual + 1;
        gen_emitir_linea(est, "_P_ntks=0;_P_tpos=0;_P_p_err=0;_P_nivel_pila=0;");
        gen_emitir_linea(est, "_P_pila_indent[0]=0;");
        gen_emitir_linea(est, "_P_tokenizar(fuente.datos,fuente.longitud);");
        gen_emitir_linea(est, "_P_procesar_indentacion_final();");
        gen_emitir_linea(est, "struct Programa _prog={0};");
        gen_emitir_linea(est, "return _prog;");
        est.indent_actual = est.indent_actual - 1;
        gen_emitir_linea(est, "}");
        gen_emitir_nueva_linea(est);
    }
}

void gen_emitir_generar_c(struct GeneradorCEst est) {
    gen_emitir_token_defs(est);
    { /* unsafe */
        // Emit _gen helper functions;
        gen_emitir_linea(est, "// --- AST Walker (auto-generado) ---");
        gen_emitir_linea(est, "// Global state from estado_global.syn");
        gen_emitir_linea(est, "FILE* _G_out = NULL;");
        gen_emitir_linea(est, "char _G_vn[1024][64] = {{0}};");
        gen_emitir_linea(est, "char _G_vt[1024][64] = {{0}};");
        gen_emitir_linea(est, "int _G_nv = 0;");
        gen_emitir_linea(est, "char _G_ret_type[64] = {0};");
        gen_emitir_linea(est, "char _G_extern_names[64][64] = {{0}};");
        gen_emitir_linea(est, "char _G_extern_params[64][256] = {{0}};");
        gen_emitir_linea(est, "int _G_nextern = 0;");
        gen_emitir_linea(est, "char _G_snames[64][64] = {{0}};");
        gen_emitir_linea(est, "int _G_nsnames = 0;");
        gen_emitir_nueva_linea(est);
        gen_emitir_linea(est, "void _G_reset() { _G_nv = 0; }");
        gen_emitir_linea(est, "int _G_find(const char* n) { for(int i=0;i<_G_nv;i++) if(strcmp(_G_vn[i],n)==0) return i; return -1; }");
        gen_emitir_nueva_linea(est);
        gen_emitir_linea(est, "void _G_emit(const char* s) { for(int i=0;i<_G_indent;i++) fprintf(_G_out,\\x22    \\x22); fprintf(_G_out,\\x22%s\\n\\x22,s); }");
        gen_emitir_nueva_linea(est);
        // Main generar function;
        gen_emitir_linea(est, "int generar(struct Programa programa, CadenaSegura ruta) {");
        est.indent_actual = est.indent_actual + 1;
        gen_emitir_linea(est, "char sal[1024]; int sl=ruta.longitud;");
        gen_emitir_linea(est, "if(sl>4&&ruta.datos[sl-4]=='.'&&(ruta.datos[sl-3]=='s'||ruta.datos[sl-3]=='S')&&(ruta.datos[sl-2]=='y'||ruta.datos[sl-2]=='Y')&&(ruta.datos[sl-1]=='n'||ruta.datos[sl-1]=='N')){memcpy(sal,ruta.datos,sl-4);sal[sl-4]='.';sal[sl-3]='c';sal[sl-2]=0;}else snprintf(sal,sizeof(sal),\\x22%.*s.c\\x22,ruta.longitud,ruta.datos);");
        gen_emitir_linea(est, "_G_out=fopen(sal,\\x22w\\x22); if(!_G_out){fprintf(stderr,\\x22Error: no se puede crear %s\\n\\x22,sal);return 1;}");
        gen_emitir_linea(est, "fprintf(_G_out,\\x22// Generado por Synapse (auto-hospedado)\\n\\x22);");
        gen_emitir_linea(est, "fprintf(_G_out,\\x22#include <stdio.h>\\n#include <stdlib.h>\\n#include <stdint.h>\\n#include <string.h>\\n#include <pthread.h>\\n\\x22);");
        gen_emitir_linea(est, "fprintf(_G_out,\\x22typedef struct {int longitud;const char* datos;} CadenaSegura;\\n\\x22);");
        gen_emitir_linea(est, "fclose(_G_out);");
        gen_emitir_linea(est, "return 0;");
        est.indent_actual = est.indent_actual - 1;
        gen_emitir_linea(est, "}");
        gen_emitir_nueva_linea(est);
    }
}

void gen_emitir_volcar_ast_c(struct GeneradorCEst est) {
    { /* unsafe */
        gen_emitir_linea(est, "void volcar_ast(struct Nodo* nodo, int nivel) {");
        est.indent_actual = est.indent_actual + 1;
        gen_emitir_linea(est, "if(!nodo){printf(\"(null)\\n\");return;}");
        gen_emitir_linea(est, "for(int i=0;i<nivel;i++)printf(\"  \");");
        gen_emitir_linea(est, "printf(\"[%%s]\\n\",nodo->tipo.datos);");
        est.indent_actual = est.indent_actual - 1;
        gen_emitir_linea(est, "}");
        gen_emitir_nueva_linea(est);
    }
}

void gen_push_scope(struct GeneradorCEst est) {
    { /* unsafe */
        est.scope_stack_top = est.scope_stack_top + 1;
        est.scope_stack_at = est.scope_stack_at + 1;
        est.scope_var_total = 0;
    }
}

void gen_pop_scope(struct GeneradorCEst est) {
    { /* unsafe */
        est.scope_stack_top = est.scope_stack_top - 1;
        if (est.scope_stack_top < 0) est.scope_stack_top = 0;
        est.scope_stack_at = est.scope_stack_top;
        est.scope_var_total = 0;
    }
}

void gen_emit_all_destructors(struct GeneradorCEst est, void* exclude_var) {
    { /* unsafe */
        (void)est; (void)exclude_var; // stub;
    }
}

// --- Generador de C ---
// --- AST Walker ---
int _G_indent = 0;
FILE* _G_out = NULL;
char _G_vn[1024][64];
char _G_vt[1024][64];
int _G_nv = 0;
char _G_ret_type[64];
char _G_extern_names[64][64];
char _G_extern_params[64][256];
int _G_nextern = 0;
char _G_snames[64][64];
int _G_nsnames = 0;

void _G_reset() { _G_nv = 0; }
int _G_find(const char* n) { if(!n) return -1; for(int i=0;i<_G_nv;i++) if(strcmp(_G_vn[i],n)==0) return i; return -1; }
const char* _G_decl(const char* n, const char* t) {
    if(!n||!t) return t?t:"int";
    int i=_G_find(n); if(i>=0) return _G_vt[i];
    if(_G_nv<1024){ strncpy(_G_vn[_G_nv],n,63); _G_vn[_G_nv][63]=0; strncpy(_G_vt[_G_nv],t,63); _G_vt[_G_nv][63]=0; _G_nv++; }
    return t;
}

void _G_emit(const char* s) {
    for(int i=0;i<_G_indent;i++) fprintf(_G_out,"    ");
    fprintf(_G_out,"%s\n",s);
}

void _G_cp(char* d, CadenaSegura cs) { if(!cs.datos||cs.longitud<=0){ d[0]=0; return; } int _len=cs.longitud<4095?cs.longitud:4095; memcpy(d,cs.datos,_len); d[_len]=0; }

const char* _G_tex(struct Nodo* n) {
    if(!n) return "int";
    const char* t=n->tipo.datos;
    if(strcmp(t,"LiteralNumero")==0) return "int";
    if(strcmp(t,"LiteralCadena")==0) return "CadenaSegura";
    if(strcmp(t,"Identificador")==0) { struct Identificador* i=(struct Identificador*)n; char m[256]; _G_cp(m,i->nombre); int j=_G_find(m); return j>=0?_G_vt[j]:"int"; }
    if(strcmp(t,"OpBinaria")==0||strcmp(t,"OpUnaria")==0) return "int";
    if(strcmp(t,"LlamadaFuncion")==0) {
        struct LlamadaFuncion* l=(struct LlamadaFuncion*)n;
        char m[256]; _G_cp(m,l->nombre);
        if(strcmp(m,"_argc")==0) return "int";
        if(strcmp(m,"_argv")==0||strcmp(m,"leer")==0||strcmp(m,"leer_linea")==0||strcmp(m,"concat")==0) return "CadenaSegura";
        if(strcmp(m,"abrir")==0) return "Canal";
        if(strcmp(m,"cerrar")==0||strcmp(m,"salir")==0||strcmp(m,"escribir")==0||strcmp(m,"escribir_linea")==0) return "void";
        if(strcmp(m,"reserva")==0||strcmp(m,"suma")==0||strcmp(m,"producto")==0||strcmp(m,"relu")==0
    ||strcmp(m,"crear_tensor")==0||strcmp(m,"suma_tensor")==0||strcmp(m,"producto_punto")==0) return "Tensor";
        if(strcmp(m,"tokenizar")==0) return "int";
        if(strcmp(m,"parsear")==0) return "struct Programa";
        if(strcmp(m,"generar")==0) return "int";
        if(strcmp(m,"libera")==0) return "void";
        if(strcmp(m,"texto_a_entero")==0) return "int";
        if(strcmp(m,"texto_a_decimal")==0) return "float";
        if(strcmp(m,"decimal_a_texto")==0) return "CadenaSegura";
        for(int _si=0;_si<_G_nsnames;_si++){ if(strcmp(m,_G_snames[_si])==0) { char _sret[64]; snprintf(_sret,sizeof(_sret),"struct %s",m); return _sret; } }
        return "int";
    }
    if(strcmp(t,"ExprAccesoCampo")==0||strcmp(t,"ArgumentoTransferido")==0) return "int";
    if(strcmp(t,"ExprTensor")==0) return "Tensor";
    if(strcmp(t,"ExprObtenerDireccion")==0) return "int*";
    if(strcmp(t,"ExprDereferencia")==0) return "int";
    return "int";
}

void _G_ea(struct Nodo* n, char* b, int sz);
void _G_vl(struct ListaNodo* l);
void _G_v(struct Nodo* n);

int _G_extern_needs_datos(const char* fn, int argidx) {
    for(int _ei=0;_ei<_G_nextern;_ei++){
        if(strcmp(_G_extern_names[_ei],fn)==0){
            int _ec=0,_epos=0;
            char _eb[256]; strcpy(_eb,_G_extern_params[_ei]);
            while(_eb[_epos]){
                int _estart=_epos;
                while(_eb[_epos]&&_eb[_epos]!=',') _epos++;
                _eb[_epos]=0;
                if(_ec==argidx) return strcmp(_eb+_estart,"char*")==0;
                _ec++; _epos++;
            }
            return 0;
        }
    }
    return 0;
}
void _G_vl(struct ListaNodo* l) { while(l){ _G_v(l->cabeza); l=l->cola; } }

void _G_ea(struct Nodo* n, char* b, int sz) {
    char i[512],d[512],o[512],m[256];
    if(!n){ snprintf(b,sz,"0"); return; }
    const char* t=n->tipo.datos;
    if(strcmp(t,"LiteralNumero")==0){ struct LiteralNumero* x=(struct LiteralNumero*)n; snprintf(b,sz,"%d",x->valor); return; }
    if(strcmp(t,"LiteralCadena")==0){ struct LiteralCadena* x=(struct LiteralCadena*)n; snprintf(b,sz,"(CadenaSegura){.longitud=%d,.datos=\"%.*s\"}",x->valor.longitud,x->valor.longitud,x->valor.datos); return; }
    if(strcmp(t,"Identificador")==0){ struct Identificador* x=(struct Identificador*)n; char _tmp_nm[256]; _G_cp(_tmp_nm,x->nombre); if(strcmp(_tmp_nm,"nulo")==0) strcpy(b,"NULL"); else strcpy(b,_tmp_nm); return; }
    if(strcmp(t,"OpBinaria")==0){ struct OpBinaria* x=(struct OpBinaria*)n; _G_ea(x->izquierdo,i,512); _G_ea(x->derecho,d,512); char _o[16]; _G_cp(_o,x->operador->lexema); snprintf(b,sz,"(%s %s %s)",i,_o,d); return; }
    if(strcmp(t,"OpUnaria")==0){ struct OpUnaria* x=(struct OpUnaria*)n; _G_ea(x->expr,i,512); char _o[16]; _G_cp(_o,x->operador->lexema); snprintf(b,sz,"(%s%s)",_o,i); return; }
    if(strcmp(t,"LlamadaFuncion")==0){
        struct LlamadaFuncion* x=(struct LlamadaFuncion*)n; _G_cp(m,x->nombre);
        { char* _p=m; while(*_p){ if(*_p=='.') *_p='_'; _p++; } }
        int _is_struct = 0;
        for(int _si=0;_si<_G_nsnames;_si++){ if(strcmp(m,_G_snames[_si])==0){ _is_struct=1; break; } }
        if(_is_struct && !x->argumentos){ snprintf(b,sz,"%s_nuevo()",m); return; }
        int _coer = (strcmp(m,"escribir")==0||strcmp(m,"escribir_linea")==0||strcmp(m,"abrir")==0||strcmp(m,"concat")==0);
        char a[4096]=""; int p=0; int aidx=0; struct ListaNodo* c=x->argumentos;
        while(c){ if(p>0){ a[p++]=','; a[p++]=' '; }
            _G_ea(c->cabeza,i,512);
            int _dos = _G_extern_needs_datos(m,aidx);
            if(_dos){ snprintf(o,sizeof(o),"(%s).datos",i); strcpy(i,o); }
            if(_coer){ const char* _at = _G_tex(c->cabeza);
                if(strcmp(_at,"int")==0){ char _w[1024]; snprintf(_w,sizeof(_w),"entero_a_texto(%s)",i); int k=0; while(_w[k]) a[p++]=_w[k++]; }
                else if(strcmp(_at,"float")==0){ char _w[1024]; snprintf(_w,sizeof(_w),"decimal_a_texto(%s)",i); int k=0; while(_w[k]) a[p++]=_w[k++]; }
                else{ int k=0; while(i[k]) a[p++]=i[k++]; }
            }else{ int k=0; while(i[k]) a[p++]=i[k++]; }
            c=c->cola; aidx++;
        }
        a[p]=0; snprintf(b,sz,"%s(%s)",m,a); return;
    }
    if(strcmp(t,"ExprAccesoCampo")==0){ struct ExprAccesoCampo* x=(struct ExprAccesoCampo*)n; _G_ea(x->objeto,o,512); _G_cp(m,x->nombre_campo); const char* _ot=_G_tex(x->objeto); int _isp=(strlen(_ot)>0&&_ot[strlen(_ot)-1]=='*'); snprintf(b,sz,"%s%s%s",o,_isp?"->":".",m); return; }
    if(strcmp(t,"ExprTensor")==0){ struct ExprTensor* x=(struct ExprTensor*)n; _G_ea(x->filas,i,512); _G_ea(x->columnas,d,512); snprintf(b,sz,"(Tensor){.filas=%s,.columnas=%s,.datos=(float*)calloc(%s*%s,sizeof(float))}",i,d,i,d); return; }
    if(strcmp(t,"ArgumentoTransferido")==0){ struct ArgumentoTransferido* x=(struct ArgumentoTransferido*)n; _G_ea(x->expr,b,sz); return; }
    if(strcmp(t,"ExprObtenerDireccion")==0){ struct ExprObtenerDireccion* x=(struct ExprObtenerDireccion*)n; _G_ea(x->expr,i,512); snprintf(b,sz,"(&%s)",i); return; }
    if(strcmp(t,"ExprDereferencia")==0){ struct ExprDereferencia* x=(struct ExprDereferencia*)n; _G_ea(x->expr,i,512); snprintf(b,sz,"(*%s)",i); return; }
    snprintf(b,sz,"/*?*/");
}

void _G_v_log(struct LogLlamada* n) {
    char f[4096]=""; int fp=0,ap=0,fi=1; char b[512]; char pr[4096]=""; char tn[64]; char tmp[512];
    struct ListaNodo* c=n->argumentos;
    while(c){ if(!fi){ f[fp++]=' '; } fi=0; f[fp++]='%'; f[fp++]='s';
        _G_cp(tn,c->cabeza->tipo);
        _G_ea(c->cabeza,tmp,512);
        if(strcmp(tn,"LiteralCadena")==0){ snprintf(b,sizeof(b),"%s.datos",tmp); }
        else{ strcpy(b,tmp); }
        if(ap>0){ pr[ap++]=','; pr[ap++]=' '; } int k=0; while(b[k]) pr[ap++]=b[k++]; c=c->cola;
    }
    f[fp]=0; pr[ap]=0; char ln[4096];
    if(ap>0) snprintf(ln,sizeof(ln),"printf(\"%s\\n\",%s);",f,pr);
    else snprintf(ln,sizeof(ln),"printf(\"%s\\n\");",f);
    _G_emit(ln);
}

const char* _G_mt(const char* st) {
    char _mtb[64];
    char _base[64]; strcpy(_base,st);
    int _mlen = strlen(_base);
    int _isptr = (_mlen>0 && _base[_mlen-1]=='*');
    if(_isptr) _base[_mlen-1]=0;
    const char* _r=NULL;
    if(strcmp(_base,"entero")==0||strcmp(_base,"int")==0) _r="int";
    else if(strcmp(_base,"texto")==0||strcmp(_base,"cadena")==0) _r="CadenaSegura";
    else if(strcmp(_base,"nulo")==0||strcmp(_base,"vacio")==0) _r="void";
    else if(strcmp(_base,"decimal")==0||strcmp(_base,"real")==0) _r="float";
    else if(strcmp(_base,"logico")==0||strcmp(_base,"booleano")==0) _r="int";
    else if(strcmp(_base,"Canal")==0||strcmp(_base,"canal")==0) _r="Canal";
    else if(strcmp(_base,"Tensor")==0||strcmp(_base,"tensor")==0) _r="Tensor";
    else if(strcmp(_base,"void")==0) _r="void";
    else if(strcmp(_base,"char")==0) _r="char";
    else if(strcmp(_base,"double")==0) _r="double";
    if(!_r) return NULL;
    if(_isptr){ snprintf(_mtb,sizeof(_mtb),"%s*",_r); return _mtb; }
    return _r;
}
void _G_vest(struct DefinicionEstructura* n) {
    char ln[4096];
    snprintf(ln,sizeof(ln),"typedef struct %s {",n->nombre.datos); _G_emit(ln);
    _G_indent++;
    struct ListaParametro* c=n->campos;
    while(c){ struct Parametro* p=(struct Parametro*)c->cabeza; char pn[256]; _G_cp(pn,p->nombre); char pt[256]; _G_cp(pt,p->tipo_param); const char* ct=_G_mt(pt); if(ct){ snprintf(ln,sizeof(ln),"%s %s;",ct,pn); }else{ snprintf(ln,sizeof(ln),"struct %s* %s;",pt,pn); } _G_emit(ln); c=c->cola; }
    _G_indent--; snprintf(ln,sizeof(ln),"} %s;",n->nombre.datos); _G_emit(ln);
    snprintf(ln,sizeof(ln),"inline struct %s %s_nuevo() {",n->nombre.datos,n->nombre.datos); _G_emit(ln);
    _G_indent++; snprintf(ln,sizeof(ln),"struct %s _r={0}; return _r;",n->nombre.datos); _G_emit(ln);
    _G_indent--; _G_emit("}");
    if(_G_nsnames<64){ strcpy(_G_snames[_G_nsnames],n->nombre.datos); _G_nsnames++; }
}

void _G_v(struct Nodo* n) {
    if(!n) return;
    char b[4096],b2[4096],m[256],v[4096];
    const char* t=n->tipo.datos;
    if(strcmp(t,"DefinicionFuncion")==0){
        _G_reset();
        struct DefinicionFuncion* f=(struct DefinicionFuncion*)n; _G_cp(m,f->nombre);
        { char* _p=m; while(*_p){ if(*_p=='.') *_p='_'; _p++; } }
        if(strcmp(m,"escribir")==0||strcmp(m,"escribir_linea")==0||strcmp(m,"leer_linea")==0||strcmp(m,"abrir")==0||strcmp(m,"leer")==0||strcmp(m,"cerrar")==0||strcmp(m,"crear_tensor")==0||strcmp(m,"suma_tensor")==0||strcmp(m,"producto_punto")==0||strcmp(m,"relu")==0||strcmp(m,"reserva")==0||strcmp(m,"libera")==0||strcmp(m,"suma")==0||strcmp(m,"producto")==0||strcmp(m,"math_crear_tensor")==0||strcmp(m,"math_suma_tensor")==0||strcmp(m,"math_producto_punto")==0||strcmp(m,"math_relu")==0||strcmp(m,"mem_reserva")==0||strcmp(m,"mem_libera")==0||strcmp(m,"math_suma")==0||strcmp(m,"math_producto")==0||strcmp(m,"texto_a_entero")==0||strcmp(m,"texto_a_decimal")==0||strcmp(m,"decimal_a_texto")==0) return;
        char ps[4096]="void"; int pp=0,fi=1; struct ListaParametro* pc=f->parametros;
        while(pc){ struct Parametro* p=(struct Parametro*)pc->cabeza; char pn[256]; _G_cp(pn,p->nombre); char pt[256]; _G_cp(pt,p->tipo_param);
            if(fi){ pp=0; fi=0; }else{ ps[pp++]=','; ps[pp++]=' '; }
            const char* _ct=_G_mt(pt);
            char _tb[64]; if(_ct){ strcpy(_tb,_ct); }else{ snprintf(_tb,sizeof(_tb),"struct %s",pt); } _ct=_tb;
            int k=0; while(_ct[k]) ps[pp++]=_ct[k++]; ps[pp++]=' '; k=0; while(pn[k]) ps[pp++]=pn[k++];
            _G_decl(pn,_ct); pc=pc->cola;
        }
        ps[pp]=0; char rt[64]; _G_cp(rt,f->tipo_retorno);
        {
            const char* _ct=_G_mt(rt);
            if(_ct){ snprintf(b,sizeof(b),"%s %s(%s)",_ct,m,ps); strcpy(_G_ret_type,_ct); }
            else{ snprintf(b,sizeof(b),"struct %s %s(%s)",rt,m,ps); snprintf(_G_ret_type,sizeof(_G_ret_type),"struct %s",rt); }
        }
        _G_emit(b); _G_emit("{"); _G_indent++; _G_vl(f->cuerpo); _G_indent--; _G_emit("}"); return;
    }
    if(strcmp(t,"SentenciaSi")==0){
        struct SentenciaSi* s=(struct SentenciaSi*)n; _G_ea(s->condicion,b,4096);
        snprintf(b2,sizeof(b2),"if (%s) {",b); _G_emit(b2); _G_indent++; _G_vl(s->cuerpo); _G_indent--;
        if(s->cuerpo_sino){ _G_emit("} else {"); _G_indent++; _G_vl(s->cuerpo_sino); _G_indent--; }
        _G_emit("}"); return;
    }
    if(strcmp(t,"SentenciaMientras")==0){
        struct SentenciaMientras* s=(struct SentenciaMientras*)n; _G_ea(s->condicion,b,4096);
        snprintf(b2,sizeof(b2),"while (%s) {",b); _G_emit(b2); _G_indent++; _G_vl(s->cuerpo); _G_indent--; _G_emit("}"); return;
    }
    if(strcmp(t,"AsignacionVariable")==0){
        struct AsignacionVariable* a=(struct AsignacionVariable*)n; _G_cp(m,a->nombre); _G_ea(a->expresion,v,4096);
        const char* vt=_G_tex(a->expresion); if(!vt) vt="int";
        { int _ac=1; char* _p=m; while(*_p){ if(!((*_p>='A'&&*_p<='Z')||(*_p>='0'&&*_p<='9')||*_p=='_')){ _ac=0; break; } _p++; } if(_ac&&m[0]){ snprintf(b,sizeof(b),"#define %s (%s)",m,v); _G_emit(b); return; } }
        if(_G_find(m)<0){ _G_decl(m,vt); snprintf(b,sizeof(b),"%s %s = %s;",vt,m,v); }
        else snprintf(b,sizeof(b),"%s = %s;",m,v);
        _G_emit(b); return;
    }
    if(strcmp(t,"AsignacionCampo")==0){
        struct AsignacionCampo* a=(struct AsignacionCampo*)n; _G_ea(a->objeto,b,4096); _G_cp(m,a->nombre_campo); _G_ea(a->expresion,v,4096);
        const char* _ot=_G_tex(a->objeto); int _isp=(strlen(_ot)>0&&_ot[strlen(_ot)-1]=='*');
        snprintf(b2,sizeof(b2),"%s%s%s = %s;",b,_isp?"->":".",m,v); _G_emit(b2); return;
    }
    if(strcmp(t,"SentenciaRetornar")==0){
        struct SentenciaRetornar* r=(struct SentenciaRetornar*)n;
        if(r->expr){ _G_ea(r->expr,v,4096);
            if(strcmp(v,"nulo")==0||strcmp(v,"0")==0||strcmp(v,"NULL")==0){ if(_G_ret_type[0]&&strcmp(_G_ret_type,"void")!=0){ snprintf(b,sizeof(b),"return (%s){0};",_G_ret_type); }else snprintf(b,sizeof(b),"return;"); }
            else snprintf(b,sizeof(b),"return %s;",v);
        }else snprintf(b,sizeof(b),"return;");
        _G_emit(b); return;
    }
    if(strcmp(t,"SentenciaExpr")==0){
        struct SentenciaExpr* e=(struct SentenciaExpr*)n;
        if(e->expr){
            if(strcmp(e->expr->tipo.datos,"LogLlamada")==0){
                _G_v_log((struct LogLlamada*)e->expr);
            }else if(strcmp(e->expr->tipo.datos,"LlamadaFuncion")==0){
                struct LlamadaFuncion* _lf=(struct LlamadaFuncion*)e->expr;
                char _fn[256]; _G_cp(_fn,_lf->nombre);
                if(strcmp(_fn,"asm")==0&&_lf->argumentos){
                    char _as[4096];
                    struct LiteralCadena* _lc=(struct LiteralCadena*)_lf->argumentos->cabeza;
                    _G_cp(_as,_lc->valor);
                    snprintf(b,sizeof(b),"__asm__(\"%s\");",_as);
                    _G_emit(b);
                }else{ _G_ea(e->expr,v,4096); snprintf(b,sizeof(b),"%s;",v); _G_emit(b); }
            }else if(strcmp(e->expr->tipo.datos,"Identificador")==0){
                /* Skip orphan identifiers (bare constant keyword etc.) */
            }else{ _G_ea(e->expr,v,4096); snprintf(b,sizeof(b),"%s;",v); _G_emit(b); }
        }
        return;
    }
    if(strcmp(t,"LogLlamada")==0){ _G_v_log((struct LogLlamada*)n); return; }
    if(strcmp(t,"SentenciaRomper")==0){ _G_emit("break;"); return; }
    if(strcmp(t,"SentenciaSiguiente")==0){ _G_emit("continue;"); return; }
    if(strcmp(t,"SentenciaLanzar")==0){ struct SentenciaLanzar* l=(struct SentenciaLanzar*)n; char fn[256]=""; char ab[512]=""; int ha=0; if(strcmp(l->llamada->tipo.datos,"LlamadaFuncion")==0){ struct LlamadaFuncion* lf=(struct LlamadaFuncion*)l->llamada; _G_cp(fn,lf->nombre); if(lf->argumentos){ _G_ea(lf->argumentos->cabeza,ab,512); ha=1; } }else{ _G_ea(l->llamada,fn,256); ha=1; } if(ha){ snprintf(b,sizeof(b),"synapse_lanzar_hilo((void*(*)(void*))%s,(void*)(intptr_t)(%s));",fn,ab); }else{ snprintf(b,sizeof(b),"synapse_lanzar_hilo((void*(*)(void*))%s,NULL);",fn); } _G_emit(b); return; }
    if(strcmp(t,"SentenciaRecuperar")==0){ struct SentenciaRecuperar* r=(struct SentenciaRecuperar*)n; _G_ea(r->accion_critica,b,4096); _G_ea(r->plan_b,v,4096); _G_emit("{"); _G_indent++; snprintf(b2,sizeof(b2),"if(%s!=0){%s;}",b,v); _G_emit(b2); _G_indent--; _G_emit("}"); return; }
    if(strcmp(t,"SentenciaEscuchar")==0){ struct SentenciaEscuchar* e=(struct SentenciaEscuchar*)n; _G_ea(e->canal,b,4096); _G_ea(e->respuesta,v,4096); snprintf(b2,sizeof(b2),"/* escuchar: %s -> %s */",b,v); _G_emit(b2); return; }
    if(strcmp(t,"DefinicionEstructura")==0){ _G_vest((struct DefinicionEstructura*)n); return; }
    if(strcmp(t,"SentenciaImportar")==0){ struct SentenciaImportar* i=(struct SentenciaImportar*)n; _G_cp(b,i->ruta); snprintf(b2,sizeof(b2),"/* importar %s */",b); _G_emit(b2); return; }
    if(strcmp(t,"ImportarC")==0){ struct ImportarC* x=(struct ImportarC*)n; _G_cp(m,x->ruta); if(x->es_sistema){ snprintf(b,sizeof(b),"#include <%s>",m); }else{ snprintf(b,sizeof(b),"#include \"%s\"",m); } _G_emit(b); return; }
    if(strcmp(t,"DeclaracionExterna")==0){
        struct DeclaracionExterna* x=(struct DeclaracionExterna*)n;
        char _enm[256]; _G_cp(_enm,x->nombre);
        strcpy(_G_extern_names[_G_nextern],_enm);
        char _ebuf[256]=""; int _ep=0;
        struct ListaParametro* _epc=(struct ListaParametro*)x->parametros;
        while(_epc){
            struct Parametro* p=(struct Parametro*)_epc->cabeza;
            if(_ep>0){ _ebuf[_ep++]=','; }
            char _ept[256]; _G_cp(_ept,p->tipo_param);
            int _ek=0; while(_ept[_ek]) _ebuf[_ep++]=_ept[_ek++];
            _epc=_epc->cola;
        }
        _ebuf[_ep]=0;
        strcpy(_G_extern_params[_G_nextern],_ebuf);
        _G_nextern++;
        /* C declaration comes from #include via importar_c */
        return;
    }
    if(strcmp(t,"BloqueInseguro")==0){ struct BloqueInseguro* x=(struct BloqueInseguro*)n; _G_emit("{ /* unsafe */"); _G_indent++; _G_vl(x->cuerpo); _G_indent--; _G_emit("}"); return; }
    _G_emit("/* ??? */");
}

int generar(struct Programa programa, CadenaSegura ruta) {
    char sal[1024]; int sl=ruta.longitud;
    if(sl>4&&ruta.datos[sl-4]=='.'&&(ruta.datos[sl-3]=='s'||ruta.datos[sl-3]=='S')&&(ruta.datos[sl-2]=='y'||ruta.datos[sl-2]=='Y')&&(ruta.datos[sl-1]=='n'||ruta.datos[sl-1]=='N')){
        memcpy(sal,ruta.datos,sl-4); sal[sl-4]='.'; sal[sl-3]='c'; sal[sl-2]=0;
    }else snprintf(sal,sizeof(sal),"%.*s.c",ruta.longitud,ruta.datos);
    _G_out=fopen(sal,"w"); if(!_G_out){ fprintf(stderr,"Error: no se puede crear %s\n",sal); return 1; }
    fprintf(_G_out,"// Generado por Synapse (auto-hospedado)\n");
    fprintf(_G_out,"#include <stdio.h>\n#include <stdlib.h>\n#include <stdint.h>\n#include <string.h>\n#include <pthread.h>\n");
    fprintf(_G_out,"typedef struct {int longitud;const char* datos;} CadenaSegura;\n");
    fprintf(_G_out,"typedef struct {uint32_t filas;uint32_t columnas;float* datos;int es_mapeado;} Tensor;\n");
    fprintf(_G_out,"typedef struct {FILE* stream;int es_valido;int es_virtual;const char* virtual_data;int virtual_len;} Canal;\n");
    fprintf(_G_out,"#define POOL_BLOQUES 64\n#define TAMANO_BLOQUE 4096\n");
    fprintf(_G_out,"#define nulo ((void*)0)\n");
    fprintf(_G_out,"// --- Declaraciones extern del runtime precompilado (synapse_rt.o) ---\n");
    fprintf(_G_out,"extern void escribir(CadenaSegura contenido);\n");
    fprintf(_G_out,"extern void escribir_linea(CadenaSegura contenido);\n");
    fprintf(_G_out,"extern CadenaSegura leer_linea(void);\n");
    fprintf(_G_out,"extern Canal abrir(CadenaSegura ruta, CadenaSegura modo);\n");
    fprintf(_G_out,"extern CadenaSegura leer(Canal canal);\n");
    fprintf(_G_out,"extern void cerrar(Canal canal);\n");
    fprintf(_G_out,"extern Tensor crear_tensor(int filas, int columnas);\n");
    fprintf(_G_out,"extern Tensor suma_tensor(Tensor a, Tensor b);\n");
    fprintf(_G_out,"extern Tensor producto_punto(Tensor a, Tensor b);\n");
    fprintf(_G_out,"extern Tensor relu(Tensor a);\n");
    fprintf(_G_out,"extern Tensor reserva(int tamano);\n");
    fprintf(_G_out,"extern void libera(Tensor bloque);\n");
    fprintf(_G_out,"extern Tensor suma(Tensor a, Tensor b);\n");
    fprintf(_G_out,"extern Tensor producto(Tensor a, Tensor b);\n");
    fprintf(_G_out,"extern int texto_a_entero(CadenaSegura str);\n");
    fprintf(_G_out,"extern float texto_a_decimal(CadenaSegura str);\n");
    fprintf(_G_out,"extern CadenaSegura decimal_a_texto(float n);\n");
    fprintf(_G_out,"extern CadenaSegura entero_a_texto(int n);\n");
    fprintf(_G_out,"extern void synapse_lanzar_hilo(void* (*fn)(void*), void* arg);\n");
    fprintf(_G_out,"extern void synapse_esperar_hilos(void);\n");
    fprintf(_G_out,"extern void pool_init(uint32_t total_blocks, uint32_t block_size);\n");
    fprintf(_G_out,"extern void pool_free(void* ptr);\n");
    fprintf(_G_out,"int _g_argc;\nchar** _g_argv;\nint _argc(){return _g_argc;}\n");
    fprintf(_G_out,"CadenaSegura _argv(int i){if(i<0||i>=_g_argc)return (CadenaSegura){0,(char*)\"\"};return (CadenaSegura){.longitud=(int)strlen(_g_argv[i]),.datos=_g_argv[i]};}\n");
    fprintf(_G_out,"void salir(int c){exit(c);}\n");
    fprintf(_G_out,"CadenaSegura concat(CadenaSegura a,CadenaSegura b){int _tl=a.longitud+b.longitud;char* _buf=(char*)malloc(_tl+1);memcpy(_buf,a.datos,a.longitud);memcpy(_buf+a.longitud,b.datos,b.longitud);_buf[_tl]=0;CadenaSegura _r={.longitud=_tl,.datos=_buf};return _r;}\n");
    // Forward declarations
    struct ListaNodo* c=programa.sentencias;
    while(c){ if(c->cabeza&&strcmp(c->cabeza->tipo.datos,"DefinicionEstructura")==0){ struct DefinicionEstructura* d=(struct DefinicionEstructura*)c->cabeza; fprintf(_G_out,"struct %s;\n",d->nombre.datos); } c=c->cola; }
    // Function prototypes
    c=programa.sentencias;
    while(c){ if(c->cabeza&&strcmp(c->cabeza->tipo.datos,"DefinicionFuncion")==0){ struct DefinicionFuncion* f=(struct DefinicionFuncion*)c->cabeza; char _fn[256]; _G_cp(_fn,f->nombre); { char* _p=_fn; while(*_p){ if(*_p=='.') *_p='_'; _p++; } } if(strcmp(_fn,"escribir")==0||strcmp(_fn,"escribir_linea")==0||strcmp(_fn,"leer_linea")==0||strcmp(_fn,"abrir")==0||strcmp(_fn,"leer")==0||strcmp(_fn,"cerrar")==0||strcmp(_fn,"crear_tensor")==0||strcmp(_fn,"suma_tensor")==0||strcmp(_fn,"producto_punto")==0||strcmp(_fn,"relu")==0||strcmp(_fn,"reserva")==0||strcmp(_fn,"libera")==0||strcmp(_fn,"suma")==0||strcmp(_fn,"producto")==0||strcmp(_fn,"math_crear_tensor")==0||strcmp(_fn,"math_suma_tensor")==0||strcmp(_fn,"math_producto_punto")==0||strcmp(_fn,"math_relu")==0||strcmp(_fn,"mem_reserva")==0||strcmp(_fn,"mem_libera")==0||strcmp(_fn,"math_suma")==0||strcmp(_fn,"math_producto")==0||strcmp(_fn,"texto_a_entero")==0||strcmp(_fn,"texto_a_decimal")==0||strcmp(_fn,"decimal_a_texto")==0) { c=c->cola; continue; } char _ps[4096]="void"; int _pp=0,_fi=1; struct ListaParametro* _pc=f->parametros; while(_pc){ struct Parametro* p=(struct Parametro*)_pc->cabeza; char _pn[256]; _G_cp(_pn,p->nombre); char _pt[256]; _G_cp(_pt,p->tipo_param); if(_fi){ _pp=0; _fi=0; }else{ _ps[_pp++]=','; _ps[_pp++]=' '; } const char* _ct=_G_mt(_pt); char _tb[64]; if(_ct){ strcpy(_tb,_ct); }else{ snprintf(_tb,sizeof(_tb),"struct %s",_pt); } _ct=_tb; int _k=0; while(_ct[_k]) _ps[_pp++]=_ct[_k++]; _ps[_pp++]=' '; _k=0; while(_pn[_k]) _ps[_pp++]=_pn[_k++]; _pc=_pc->cola; } _ps[_pp]=0; char _rt[64]; _G_cp(_rt,f->tipo_retorno); const char* _rct=_G_mt(_rt); if(_rct){ fprintf(_G_out,"%s %s(%s);\n",_rct,_fn,_ps); }else{ fprintf(_G_out,"struct %s %s(%s);\n",_rt,_fn,_ps); } } c=c->cola; }
    _G_indent=0; c=programa.sentencias;
    while(c){ _G_v(c->cabeza); c=c->cola; }
    // main()
    _G_emit("int main(int argc, char** argv) {");
    _G_indent++;
    _G_emit("int _g_argc=argc;");
    _G_emit("char** _g_argv=argv;");
    _G_emit("pool_init(POOL_BLOQUES, TAMANO_BLOQUE);");
    _G_emit("principal();");
    _G_emit("synapse_esperar_hilos();");
    _G_emit("return 0;");
    _G_indent--;
    _G_emit("}");
    fclose(_G_out);
    char cmd[2048];
    char out_exe[1024];
    int slen = (int)strlen(sal);
    if (slen > 2 && sal[slen-2] == '.' && sal[slen-1] == 'c') {
        memcpy(out_exe, sal, slen - 2);
        out_exe[slen - 2] = 0;
        strcat(out_exe, ".exe");
    } else {
        snprintf(out_exe, sizeof(out_exe), "%s.exe", sal);
    }
    snprintf(cmd, sizeof(cmd), "gcc -O2 -fno-ident -Wl,--no-insert-timestamp \"%s\" synapse_rt.o -o \"%s\" -lpthread -lm -lws2_32", sal, out_exe);
    int rc = system(cmd);
    if (rc != 0) {
        fprintf(stderr, "[LINKER ERROR] gcc fallo con codigo %d\n", rc);
        exit(1);
    }
    fprintf(stderr, "OK: %s\n", out_exe);
    return 0;
}
#define AXON_MODULES ((CadenaSegura){ .longitud = (int)strlen("axon_modules"), .datos = "axon_modules" })
CadenaSegura buscar_en(CadenaSegura dir_base, CadenaSegura ruta_import) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        char _buf[1024];
        snprintf(_buf, 1024, "%s/%s/%s/principal.syn", dir_base.datos, "axon_modules", ruta_import.datos);
        FILE* _f = fopen(_buf, "r");
        if (_f) { fclose(_f); r = (CadenaSegura){.longitud=(int)strlen(_buf),.datos=strdup(_buf)}; } else {
            snprintf(_buf, 1024, "%s/%s/%s.syn", dir_base.datos, "axon_modules", ruta_import.datos);
            for (char* _p = _buf; *_p; _p++) if (*_p == '.') *_p = '/';
            _f = fopen(_buf, "r");
            if (_f) { fclose(_f); r = (CadenaSegura){.longitud=(int)strlen(_buf),.datos=strdup(_buf)}; }
        }
    }
    CadenaSegura _ret_20 = r;
    return _ret_20;
}

CadenaSegura resolver(CadenaSegura ruta_import, CadenaSegura dir_base, CadenaSegura dependencias_nombres, CadenaSegura dependencias_valores, int total_dependencias) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        // Check if dependency is in the declared list;
        for (int _di = 0; _di < total_dependencias; _di++) {
            if (strcmp(dependencias_nombres.datos + _di * 128, ruta_import.datos) == 0) {
                r = (CadenaSegura){.longitud=(int)strlen(dependencias_valores.datos + _di * 512),.datos=strdup(dependencias_valores.datos + _di * 512)};
                break;
            }
        }
        if (r.longitud == 0) {
            // Look up in filesystem;
            char _ruta[1024];
            snprintf(_ruta, 1024, "%s/%s/%s/principal.syn", dir_base.datos, "axon_modules", ruta_import.datos);
            FILE* _f = fopen(_ruta, "r");
            if (_f) { fclose(_f); r = (CadenaSegura){.longitud=(int)strlen(_ruta),.datos=strdup(_ruta)}; } else {
                snprintf(_ruta, 1024, "%s/%s/%s.syn", dir_base.datos, "axon_modules", ruta_import.datos);
                for (char* _p = _ruta; *_p; _p++) if (*_p == '.') *_p = '/';
                _f = fopen(_ruta, "r");
                if (_f) { fclose(_f); r = (CadenaSegura){.longitud=(int)strlen(_ruta),.datos=strdup(_ruta)}; }
            }
        }
        if (r.longitud == 0) {
            // Not found - build error message;
            char _msg[4096];
            snprintf(_msg, 4096, "No se pudo resolver la importacion: %s", ruta_import.datos);
            r = (CadenaSegura){.longitud=(int)strlen(_msg),.datos=strdup(_msg)};
        }
    }
    CadenaSegura _ret_50 = r;
    return _ret_50;
}

struct ResultadoEtapa etapa_ok(void) {
    struct ResultadoEtapa r;
    r = (struct ResultadoEtapa){0};
    r.tag = 0;
    struct ResultadoEtapa _ret_25 = r;
    return _ret_25;
}

int fallo_etapa(int cod) {
    { /* unsafe */
        fprintf(stderr, "Error de compilacion\n");
    }
    int _ret_30 = cod;
    return _ret_30;
}

CadenaSegura argv_str(int i) {
    CadenaSegura r = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    { /* unsafe */
        if (i < 0 || i >= _argc()) { r = (CadenaSegura){0,(char*)""}; return r; }
        CadenaSegura _as = _argv(i);
        r = (CadenaSegura){.longitud=_as.longitud,.datos=strdup(_as.datos)};
    }
    CadenaSegura _ret_38 = r;
    return _ret_38;
}

struct ResultadoEtapa generar_etapa(CadenaSegura ruta, CadenaSegura salida) {
    { /* unsafe */
        fprintf(stderr, "[Synapse] Pipeline nativa: Unity Build - leyendo nucleo...\n");
        // ORDEN 3 M17.2: Multi-file unity build;
        extern int tokenizar(CadenaSegura); extern struct Programa parsear(CadenaSegura);
        struct Programa _ast; memset(&_ast,0,sizeof(_ast));
        struct ListaNodo* _merged = NULL;
        struct ListaNodo** _mcur = &_merged;
        const char* _files[] = {"nucleo/tokens.syn","nucleo/lexer.syn","nucleo/parser.syn","nucleo/analizador_semantico.syn","nucleo/generator.syn","nucleo/principal.syn",NULL};
        for(int _fi=0;_files[_fi];_fi++){ _P_ntks=0;_P_tpos=0;_P_p_err=0; fprintf(stderr,"[Synapse] Procesando %s...\n",_files[_fi]); FILE* _f=fopen(_files[_fi],"rb"); if(!_f){struct ResultadoEtapa _e={1,2};return _e;} fseek(_f,0,SEEK_END);long _fsz=ftell(_f);fseek(_f,0,SEEK_SET); if(_fsz>1048576){fprintf(stderr,"FATAL:%%s >1MB\n",_files[_fi]);fclose(_f);struct ResultadoEtapa _e={1,6};return _e;} char* _buf=(char*)malloc((size_t)(_fsz<1048576?1048576:_fsz)+1); fread(_buf,1,(size_t)_fsz,_f);fclose(_f);_buf[_fsz]=0; CadenaSegura _fuente={.longitud=(int)_fsz,.datos=_buf}; int _ntok=tokenizar(_fuente); if(_ntok<0){free(_buf);struct ResultadoEtapa _e={1,3};return _e;} struct Programa _prog=parsear(_fuente); free(_buf); struct ListaNodo* _cur=_prog.sentencias; while(_cur){if(_cur->cabeza){*_mcur=(struct ListaNodo*)calloc(1,sizeof(struct ListaNodo));(*_mcur)->cabeza=_cur->cabeza;(*_mcur)->cola=NULL;_mcur=&(*_mcur)->cola;}_cur=_cur->cola;} };
        _ast.sentencias = _merged;
        fprintf(stderr, "[Synapse] Unity Build: AST fusionado\n");

        // 3b. F8: Convert linked-list AST to flat SemNodo array + run semantic analyzer;
        fputs("[Synapse] F8: Analisis semantico\n",stderr);
        enum { F8_MAX_NODOS = 65536, F8_MAX_SYMS = 16384 };
        static struct SemNodo _f8_nodos[F8_MAX_NODOS];
        static int _f8_total = 0;
        static int _f8_ptr_hi[F8_MAX_NODOS]; // High 32 bits for ptr_str on 64-bit;
        static struct SemSimbolo _f8_syms[F8_MAX_SYMS];
        static struct SemTablaSimbolos _f8_tabla = { .entradas = _f8_syms, .total_entradas = 0, .nivel_actual = 0 };
        static struct SemEstructuraInfo _f8_structs[64];
        /* Map string type tag to integer constant */;
        int _f8_tipo(const char* t) {
            if(strcmp(t,"Programa")==0) return 1;
            if(strcmp(t,"DefinicionFuncion")==0) return 2;
            if(strcmp(t,"SentenciaSi")==0) return 3;
            if(strcmp(t,"SentenciaMientras")==0) return 4;
            if(strcmp(t,"SentenciaRetornar")==0) return 5;
            if(strcmp(t,"SentenciaExpr")==0) return 6;
            if(strcmp(t,"AsignacionVariable")==0) return 7;
            if(strcmp(t,"Identificador")==0) return 8;
            if(strcmp(t,"LiteralNumero")==0) return 9;
            if(strcmp(t,"LiteralCadena")==0) return 11;
            if(strcmp(t,"OpBinaria")==0) return 12;
            if(strcmp(t,"LlamadaFuncion")==0) return 14;
            if(strcmp(t,"Parametro")==0) return 15;
            if(strcmp(t,"DefinicionEstructura")==0) return 16;
            if(strcmp(t,"BloqueInseguro")==0) return 24;
            if(strcmp(t,"DeclaracionExterna")==0) return 26;
            if(strcmp(t,"DeclaracionVariable")==0) return 34;
            if(strcmp(t,"LogLlamada")==0) return 35;
            return 0;
        }
        /* Recursive flatten: returns index of flattened node */;
        int _f8_flatten(struct Nodo* n) {
            if(!n) return 0;
            if(_f8_total>=F8_MAX_NODOS){ fprintf(stderr,"FATAL: F8_MAX_NODOS (%d) superado.\n",F8_MAX_NODOS); exit(1); }
            int idx=_f8_total++;
            memset(&_f8_nodos[idx],0,sizeof(struct SemNodo));
            _f8_nodos[idx].tipo_nodo=_f8_tipo(n->tipo.datos);
            const char* _t=n->tipo.datos;
            if(strcmp(_t,"DefinicionFuncion")==0){
                struct DefinicionFuncion* _f=(struct DefinicionFuncion*)n;
                { uintptr_t _tp=(uintptr_t)_f->nombre.datos; _f8_nodos[idx].ptr_str=(int)(_tp&0xFFFFFFFFu); _f8_ptr_hi[idx]=(int)(_tp>>32); ((int*)&_f8_nodos[idx])[10]=(int)(_tp>>32); }
                _f8_nodos[idx].len_str=_f->nombre.longitud;
                // Params list at slot[6], body at slot[7];
                int _pfirst=0,_pprev=0;
                struct ListaParametro* _pc=_f->parametros;
                while(_pc){ if(_pc->cabeza){ int _ci=_f8_flatten((struct Nodo*)_pc->cabeza); if(_ci){ if(!_pfirst)_pfirst=_ci; if(_pprev)_f8_nodos[_pprev].hermano=_ci; _pprev=_ci; } } _pc=_pc->cola; }
                ((int*)&_f8_nodos[idx])[6]=_pfirst;
                int _bfirst=0,_bprev=0;
                struct ListaNodo* _c=_f->cuerpo;
                while(_c){ if(_c->cabeza){ int _ci=_f8_flatten(_c->cabeza); if(_ci){ if(!_bfirst)_bfirst=_ci; if(_bprev)_f8_nodos[_bprev].hermano=_ci; _bprev=_ci; } } _c=_c->cola; }
                _f8_nodos[idx].hijo_izq=_bfirst;
            }else if(strcmp(_t,"SentenciaSi")==0){
                struct SentenciaSi* _s=(struct SentenciaSi*)n;
                // Condition at slot[6], body at slot[7], else at slot[8];
                ((int*)&_f8_nodos[idx])[6]=_f8_flatten(_s->condicion);
                int _first=0,_prev=0;
                struct ListaNodo* _c=_s->cuerpo;
                while(_c){ if(_c->cabeza){ int _ci=_f8_flatten(_c->cabeza); if(_ci){ if(!_first)_first=_ci; if(_prev)_f8_nodos[_prev].hermano=_ci; _prev=_ci; } } _c=_c->cola; }
                _f8_nodos[idx].hijo_izq=_first;
                if(_s->cuerpo_sino){ int _sfirst=0,_sprev=0; _c=_s->cuerpo_sino; while(_c){ if(_c->cabeza){ int _ci=_f8_flatten(_c->cabeza); if(_ci){ if(!_sfirst)_sfirst=_ci; if(_sprev)_f8_nodos[_sprev].hermano=_ci; _sprev=_ci; } } _c=_c->cola; } _f8_nodos[idx].hijo_der=_sfirst; }
            }else if(strcmp(_t,"SentenciaMientras")==0||strcmp(_t,"BloqueInseguro")==0){
                if(strcmp(_t,"SentenciaMientras")==0){
                    struct SentenciaMientras* _sm=(struct SentenciaMientras*)n;
                    ((int*)&_f8_nodos[idx])[6]=_f8_flatten(_sm->condicion);
                    int _first=0,_prev=0;
                    struct ListaNodo* _c=_sm->cuerpo;
                    while(_c){ if(_c->cabeza){ int _ci=_f8_flatten(_c->cabeza); if(_ci){ if(!_first)_first=_ci; if(_prev)_f8_nodos[_prev].hermano=_ci; _prev=_ci; } } _c=_c->cola; }
                    _f8_nodos[idx].hijo_izq=_first;
                }else{
                    struct BloqueInseguro* _bi=(struct BloqueInseguro*)n;
                    int _first=0,_prev=0;
                    struct ListaNodo* _c=_bi->cuerpo;
                    while(_c){ if(_c->cabeza){ int _ci=_f8_flatten(_c->cabeza); if(_ci){ if(!_first)_first=_ci; if(_prev)_f8_nodos[_prev].hermano=_ci; _prev=_ci; } } _c=_c->cola; }
                    ((int*)&_f8_nodos[idx])[6]=_first;
                }
            }else if(strcmp(_t,"AsignacionVariable")==0){
                struct AsignacionVariable* _a=(struct AsignacionVariable*)n;
                { uintptr_t _tp=(uintptr_t)_a->nombre.datos; _f8_nodos[idx].ptr_str=(int)(_tp&0xFFFFFFFFu); _f8_ptr_hi[idx]=(int)(_tp>>32); ((int*)&_f8_nodos[idx])[10]=(int)(_tp>>32); }
                if(_a->expresion){ int _ci=_f8_flatten(_a->expresion); ((int*)&_f8_nodos[idx])[6]=_ci; }
            }else if(strcmp(_t,"DeclaracionVariable")==0){
                struct DeclaracionVariable* _d=(struct DeclaracionVariable*)n;
                { uintptr_t _tp=(uintptr_t)_d->nombre.datos; _f8_nodos[idx].ptr_str=(int)(_tp&0xFFFFFFFFu); _f8_ptr_hi[idx]=(int)(_tp>>32); ((int*)&_f8_nodos[idx])[10]=(int)(_tp>>32); }
                if(_d->expresion){ int _ci=_f8_flatten(_d->expresion); ((int*)&_f8_nodos[idx])[6]=_ci; }
            }else if(strcmp(_t,"SentenciaExpr")==0){
                struct SentenciaExpr* _e=(struct SentenciaExpr*)n;
                if(_e->expr){ int _ci=_f8_flatten(_e->expr); ((int*)&_f8_nodos[idx])[6]=_ci; }
            }else if(strcmp(_t,"AsignacionCampo")==0){
                struct AsignacionCampo* _ac=(struct AsignacionCampo*)n;
                { uintptr_t _tp=(uintptr_t)_ac->nombre_campo.datos; _f8_nodos[idx].ptr_str=(int)(_tp&0xFFFFFFFFu); _f8_ptr_hi[idx]=(int)(_tp>>32); ((int*)&_f8_nodos[idx])[10]=(int)(_tp>>32); }
                _f8_nodos[idx].len_str=_ac->nombre_campo.longitud;
                if(_ac->objeto){ int _ci=_f8_flatten(_ac->objeto); ((int*)&_f8_nodos[idx])[6]=_ci; }
                if(_ac->expresion){ int _ci=_f8_flatten(_ac->expresion); _f8_nodos[idx].hijo_izq=_ci; }
            }else if(strcmp(_t,"SentenciaRetornar")==0){
                struct SentenciaRetornar* _r=(struct SentenciaRetornar*)n;
                if(_r->expr){ int _ci=_f8_flatten(_r->expr); ((int*)&_f8_nodos[idx])[6]=_ci; }
            }else if(strcmp(_t,"LlamadaFuncion")==0){
                struct LlamadaFuncion* _l=(struct LlamadaFuncion*)n;
                { uintptr_t _tp=(uintptr_t)_l->nombre.datos; _f8_nodos[idx].ptr_str=(int)(_tp&0xFFFFFFFFu); _f8_ptr_hi[idx]=(int)(_tp>>32); ((int*)&_f8_nodos[idx])[10]=(int)(_tp>>32); }
                if(_l->argumentos){ int _first=0,_prev=0; struct ListaNodo* _c=_l->argumentos; while(_c){ if(_c->cabeza){ int _ci=_f8_flatten(_c->cabeza); if(_ci){ if(!_first)_first=_ci; if(_prev)_f8_nodos[_prev].hermano=_ci; _prev=_ci; } } _c=_c->cola; } ((int*)&_f8_nodos[idx])[6]=_first; }
            }else if(strcmp(_t,"OpBinaria")==0){
                struct OpBinaria* _o=(struct OpBinaria*)n;
                int _ci_l=_f8_flatten(_o->izquierdo);
                int _ci_r=_f8_flatten(_o->derecho);
                if(_o->operador) _f8_nodos[idx].ptr_str=_o->operador->tipo;
                ((int*)&_f8_nodos[idx])[6]=_ci_l;
                _f8_nodos[idx].hijo_izq=_ci_r;
            }else if(strcmp(_t,"Identificador")==0){
                struct Identificador* _id=(struct Identificador*)n;
                { uintptr_t _tp=(uintptr_t)_id->nombre.datos; _f8_nodos[idx].ptr_str=(int)(_tp&0xFFFFFFFFu); _f8_ptr_hi[idx]=(int)(_tp>>32); ((int*)&_f8_nodos[idx])[10]=(int)(_tp>>32); }
                _f8_nodos[idx].len_str=_id->nombre.longitud;
            }else if(strcmp(_t,"ExprAccesoCampo")==0){
                struct ExprAccesoCampo* _eac=(struct ExprAccesoCampo*)n;
                if(_eac->objeto){ int _ci=_f8_flatten(_eac->objeto); ((int*)&_f8_nodos[idx])[6]=_ci; }
                { uintptr_t _tp=(uintptr_t)_eac->nombre_campo.datos; _f8_nodos[idx].ptr_str=(int)(_tp&0xFFFFFFFFu); _f8_ptr_hi[idx]=(int)(_tp>>32); ((int*)&_f8_nodos[idx])[10]=(int)(_tp>>32); }
                _f8_nodos[idx].len_str=_eac->nombre_campo.longitud;
            }
            return idx;
        }
        /* Build flat array from top-level nodes */;
        _f8_total=0;
        static struct SemSimbolo _f8_syms_data[F8_MAX_SYMS];
        memset(&_f8_syms_data,0,sizeof(_f8_syms_data));
        _f8_tabla.entradas=_f8_syms_data; _f8_tabla.total_entradas=0; _f8_tabla.nivel_actual=0;
        memset(&_f8_structs,0,sizeof(_f8_structs));
        {
            int _first=0,_prev=0;
            struct ListaNodo* _c=_ast.sentencias;
            while(_c){ if(_c->cabeza){ int _ci=_f8_flatten(_c->cabeza); if(_ci){ if(!_first)_first=_ci; if(_prev)_f8_nodos[_prev].hermano=_ci; _prev=_ci; } } _c=_c->cola; }
            int _root=_f8_total;
            memset(&_f8_nodos[_root],0,sizeof(struct SemNodo));
            _f8_nodos[_root].tipo_nodo=1; _f8_nodos[_root].hijo_izq=_first;
            _f8_total++;
        }
        fprintf(stderr,"[Synapse] F8: %d nodos aplanados\n",_f8_total);
        /* Setup analyzer state and call analizar() */;
        struct AnalizadorSemanticoEst _sem_est;
        memset(&_sem_est,0,sizeof(_sem_est));
        _sem_est.nodos=_f8_nodos;
        _sem_est.total_nodos=_f8_total;
        _sem_est.tabla=&_f8_tabla;
        _sem_est.info_estructuras=_f8_structs;
        _sem_est.func_retorno=(CadenaSegura){0,""};
        _sem_est.func_actual=(CadenaSegura){0,""};
        _sem_est.asignaciones_campos_campo=(CadenaSegura){.longitud=F8_MAX_NODOS,.datos=(char*)_f8_ptr_hi};
        analizar(_sem_est);
        fprintf(stderr,"[Synapse] F8: Analisis completado\n");
        // 4. Generar codigo C desde AST;
        extern int generar(struct Programa, CadenaSegura);
        CadenaSegura _salida_c = { .longitud = salida.longitud, .datos = salida.datos };
        int _gen_rc = generar(_ast, _salida_c);
        if (_gen_rc != 0) { struct ResultadoEtapa _e = {1, 4}; return _e; }

        // 5. Compilar con GCC;
        char _cmd[4096];
        snprintf(_cmd, 4096, "gcc -O2 -Wl,--stack,8388608 -Wl,--gc-sections -I. synapse_unity.c synapse_rt.o tweetnacl.o -o \"%s\" -lpthread -lm -lws2_32", salida.datos);
        fprintf(stderr, "[Synapse] GCC: %s\n", _cmd);
        int _gcc_rc = system(_cmd);
        if (_gcc_rc != 0) {
            fprintf(stderr, "[Synapse] ERROR: GCC fallo con codigo %d\n", _gcc_rc);
            struct ResultadoEtapa _e = {1, 5}; return _e;
        }
        fprintf(stderr, "[Synapse] Compilacion nativa exitosa\n");
    }
    struct ResultadoEtapa _ret_218 = etapa_ok();
    return _ret_218;
}

int principal(void) {
    int r;
    struct ResultadoEtapa _resultado;
    r = 0;
    { /* unsafe */
        if (_argc() < 2) { fprintf(stderr, "Uso: %s <archivo.syn> [salida.exe]\n", _argc() > 0 ? _argv(0).datos : "synapse"); fprintf(stderr, "  %s axon fetch    - Leer y validar axon.toml\n", _argc() > 0 ? _argv(0).datos : "synapse"); r = 1; return r; }
    }
    CadenaSegura cmd = argv_str(1);
    { /* unsafe */
        typedef struct { CadenaSegura clave; void* valor; } _AxnPar; typedef struct { int tipo; CadenaSegura valor_str; _AxnPar* pares; int longitud; } _AxnRoot; extern _AxnRoot _toml_parse(CadenaSegura); extern void _syn_axon_limpiar_toml(void*); extern int _syn_axon_buscar_local(const char*,const char*,char*,int,char*,int);
        if(strcmp(cmd.datos,"axon")==0){ if(_argc()<3){fprintf(stderr,"Uso: %%s axon fetch\n",_argv(0).datos);r=1;return r;} CadenaSegura _sub=_argv(2);
        if(strcmp(_sub.datos,"fetch")==0){
            fprintf(stderr,"[Axon] Leyendo axon.toml...\n");
            FILE*_f=fopen("axon.toml","rb"); if(!_f){fprintf(stderr,"[Axon] ERROR: axon.toml no encontrado\n");r=1;return r;}
            fseek(_f,0,SEEK_END);long _sz=ftell(_f);fseek(_f,0,SEEK_SET);
            char*_b=(char*)malloc((size_t)_sz+1); if(!_b){fclose(_f);fprintf(stderr,"[Axon] ERROR: malloc fallo\n");r=1;return r;}
            size_t _rd=fread(_b,1,(size_t)_sz,_f);fclose(_f);_b[_rd]=0;
            _AxnRoot _rt=_toml_parse((CadenaSegura){.longitud=(int)_rd,.datos=_b});
            if(_rt.tipo<0){fprintf(stderr,"[Axon] ERROR: TOML invalido\n");free(_b);r=1;return r;}
            fprintf(stderr,"[Axon] TOML: %%d secciones\n",_rt.longitud);
            // Create cache directory;
            system("mkdir .axon_cache 2>nul"); system("mkdir axon_modules 2>nul");
            // Parse --online flag (default: offline strict);
            int _online = 0; for(int _ai=3;_ai<_argc();_ai++){ CadenaSegura _a=_argv(_ai); if(strcmp(_a.datos,"--online")==0){ _online=1; break; } };
            fprintf(stderr,"[Axon] Modo: %s\n",_online?"online":"offline (air-gapped)");
            // Extract autor (Ed25519 public key) from [paquete] section;
            char autor[128]="";
            for(int _ta=0;_ta<_rt.longitud;_ta++){
                if(strcmp(_rt.pares[_ta].clave.datos,"paquete")==0){
                    _AxnRoot*_paq=(_AxnRoot*)_rt.pares[_ta].valor;
                    for(int _tb=0;_tb<_paq->longitud;_tb++){
                        if(strcmp(_paq->pares[_tb].clave.datos,"autor")==0){
                            strncpy(autor,((_AxnRoot*)_paq->pares[_tb].valor)->valor_str.datos,127);
                        }
                    }
                }
            }
            if(*autor){ fprintf(stderr,"[Axon] Autor: %s\n",autor); }
            if(!*autor || strlen(autor)<64){ fprintf(stderr,"[Axon] ERR_AXON_COMPROMISED: clave publica Ed25519 invalida o ausente\n"); free(_b); r=1; return r; }
            // Iterate dependencies section;
            for(int _ti=0;_ti<_rt.longitud;_ti++){
                if(strcmp(_rt.pares[_ti].clave.datos,"dependencias")==0){
                    _AxnRoot*_dep=(_AxnRoot*)_rt.pares[_ti].valor;
                    fprintf(stderr,"[Axon] %%d dependencias encontradas\n",_dep->longitud);
                    for(int _tj=0;_tj<_dep->longitud;_tj++){
                        CadenaSegura _pkg=_dep->pares[_tj].clave;
                        _AxnRoot*_pkg_val=(_AxnRoot*)_dep->pares[_tj].valor;
                        // Extract version from inline table;
                        char _ver[64]="";
                        for(int _tk=0;_tk<_pkg_val->longitud;_tk++){
                            if(strcmp(_pkg_val->pares[_tk].clave.datos,"version")==0){
                                strncpy(_ver,((_AxnRoot*)_pkg_val->pares[_tk].valor)->valor_str.datos,63);
                            }
                        }
                        fprintf(stderr,"[Axon] Procesando: '%%s' v%%s\n",_pkg.datos,_ver);
                        // Build download URL: github.com/synapse-native/PKG/archive/refs/heads/main.tar;
                        char _tar_url[512], _tar_path[512], _extract_dir[512], _lock_path[512];
                        snprintf(_tar_url,sizeof(_tar_url),"/synapse-native/%%s/archive/refs/heads/main.tar",_pkg.datos);
                        snprintf(_tar_path,sizeof(_tar_path),".axon_cache/%%s.tar",_pkg.datos);
                        snprintf(_extract_dir,sizeof(_extract_dir),"axon_modules/%%s",_pkg.datos);
                        snprintf(_lock_path,sizeof(_lock_path),"axon.lock");
                        extern int _syn_http_get_archivo(CadenaSegura,int,CadenaSegura,const char*);
                                    extern CadenaSegura _syn_sha256_archivo(const char*);
                        extern int _syn_axon_verificar_lock(const char*,const char*,const char*,const char*);
                        extern int _syn_tar_extraer(const char*,const char*);
                        extern int _syn_axon_verificar_firma(const char*,const char*,const char*); extern int _syn_axon_escribir_lock(const char*,const char*,const char*);
                        // Step 0: Try local resolution first (offline-first);
                        int _local_st = _syn_axon_buscar_local(_pkg.datos,_ver,_tar_path,512,_extract_dir,512);
                        if(_local_st < 0){
                            if(!_online){
                                fprintf(stderr,"[Axon] ERR_AXON_NOT_FOUND: %%s v%%s no encontrado localmente (use --online)
",_pkg.datos,_ver);
                                r=1; free(_b); return r;
                            }
                            // Online mode: download from HTTP;
                            fprintf(stderr,"[Axon] Descargando %%s...\n",_pkg.datos);
                            CadenaSegura _gh_host={.longitud=14,.datos="github.com"};
                            CadenaSegura _gh_path={.longitud=(int)strlen(_tar_url),.datos=_tar_url};
                            int _dl=_syn_http_get_archivo(_gh_host,443,_gh_path,_tar_path);
                            if(_dl<0){
                                fprintf(stderr,"[Axon] ERROR: No se pudo descargar %%s\n",_pkg.datos);
                                fprintf(stderr,"[Axon] ERR_AXON_NOT_FOUND: %%s v%%s (red no disponible)
",_pkg.datos,_ver);
                                r=1; free(_b); return r;
                            }
                            fprintf(stderr,"[Axon] Descargado: %%s\n",_tar_path);
                        }else{
                            if(_local_st==0){
                                // Already installed, skip;
                                fprintf(stderr,"[Axon] Ya instalado: %%s\n",_pkg.datos);
                                continue;
                            }
                            fprintf(stderr,"[Axon] Local: %%s\n",_tar_path);
                        }
                        // Step 1.5: Download signature + verify Ed25519;
                        char sig_path[512];
                        snprintf(sig_path,sizeof(sig_path),".axon_cache/%s.tar.sig",_pkg.datos);
                        // Try local .sig first, then online if --online;
                        int _sig_dl=-1;
                        FILE* _sig_f = fopen(sig_path,"rb");
                        if(_sig_f){ fclose(_sig_f); _sig_dl=0; fprintf(stderr,"[Axon] .sig local encontrado\n"); }
                        else if(_online){
                            char sig_url[512];
                            CadenaSegura _gh_host_sig={.longitud=14,.datos="github.com"};
                            snprintf(sig_url,sizeof(sig_url),"/synapse-native/%s/archive/refs/heads/main.tar.sig",_pkg.datos);
                            CadenaSegura _gh_path_sig={.longitud=(int)strlen(sig_url),.datos=sig_url};
                            _sig_dl=_syn_http_get_archivo(_gh_host_sig,443,_gh_path_sig,sig_path);
                        }
                        if(*autor && _sig_dl>=0){ fprintf(stderr,"[Axon] Verificando firma Ed25519...\n"); int _vf=_syn_axon_verificar_firma(_tar_path,sig_path,autor); if(_vf<0){ fprintf(stderr,"[Axon] ERR_AXON_COMPROMISED: firma Ed25519 invalida\n"); remove(_tar_path); remove(sig_path); r=1; free(_b); return r; } fprintf(stderr,"[Axon] Firma Ed25519 verificada correctamente\n"); }
                        if(*autor && _sig_dl<0){ fprintf(stderr,"[Axon] WARNING: No se pudo obtener .sig, saltando verificacion\n"); }
                        // Step 2: Verify/Create lock;
                        int _lk=_syn_axon_verificar_lock(_pkg.datos,_ver,_tar_path,_lock_path);
                        if(_lk<0){fprintf(stderr,"[Axon] ERR_AXON_COMPROMISED: hash mismatch\n");r=1;free(_b);return r;}
                        // Step 3: Extract TAR;
                        fprintf(stderr,"[Axon] Extrayendo a %%s...\n",_extract_dir);
                        _syn_tar_extraer(_tar_path,_extract_dir);
                        fprintf(stderr,"[Axon] Instalado: %%s v%%s\n",_pkg.datos,_ver);
                        CadenaSegura _lk_hash=_syn_sha256_archivo(_tar_path); if(_lk_hash.datos&&_lk_hash.longitud>0){ _syn_axon_escribir_lock(_pkg.datos,_ver,_lk_hash.datos); free((void*)_lk_hash.datos); };
                    }
                }
            }
            _syn_axon_limpiar_toml((void*)&_rt); fprintf(stderr,"[Axon] fetch completado\n"); free(_b); r=0; return r;
        }
        fprintf(stderr,"Subcomando desconocido: '%%s'\n",_sub.datos); r=1; return r; }
    }
    CadenaSegura ruta = argv_str(1);
    CadenaSegura salida_ruta = argv_str(2);
    { /* unsafe */
        if (ruta.longitud == 0) { r = 1; return r; }
        if (salida_ruta.longitud == 0) { salida_ruta = (CadenaSegura){.longitud=19,.datos="synapse_stage2.exe"}; }
    }
    _resultado = generar_etapa(ruta, salida_ruta);
    if ((_resultado.tag == 0)) {
        r = 0;
    }
    else {
        r = fallo_etapa(_resultado.dato.valor);
    }
    int _ret_351 = r;
    _syn_texto_liberar(salida_ruta);
    _syn_texto_liberar(ruta);
    _syn_texto_liberar(cmd);
    return _ret_351;
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    return principal();
    synapse_esperar_hilos();
    return 0;
}