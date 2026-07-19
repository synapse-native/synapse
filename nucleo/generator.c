// Parser state (file scope)
#define MAX_TOKS 16384
typedef struct { int tipo; int linea; int col; char val[256]; } _P_Token;
_P_Token _P_tks[MAX_TOKS];
int _P_ntks = 0, _P_tpos = 0, _P_p_err = 0;
int _P_pila_indent[64], _P_nivel_pila = 0;

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

// Buffer temporal global para funciones del generador
#define _GEN_TMP_SIZE (4096)
char _gen_tmp_buf[4096];

// Variable global de indentación para el AST Walker
int _G_indent = 0;

// Forward declarations de runtime del AST Walker
const char* _G_mt(const char* st);
void _G_vest(struct DefinicionEstructura* n);

// Constantes de tags para uniones etiquetadas (ADTs)
#define TAG_OK 0
#define TAG_ERR 1
#define TAG_ALGUNO 0
#define TAG_NINGUNO 1

// --- Helpers de serialización primitiva para canales (Zero-Copy) ---
inline void* _synapse_box_int(int v) { return (void*)(intptr_t)v; }
inline int _synapse_unbox_int(void* p) { return (int)(intptr_t)p; }
inline void* _synapse_box_float(float v) {
    float* _p = (float*)malloc(sizeof(float));
    if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en _synapse_box_float\n"); exit(1); }
    *_p = v;
    return (void*)_p;
}
inline float _synapse_unbox_float(void* p) {
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
    if (!_buf) { fprintf(stderr,"Error: Asignación de memoria falló en concat()\n"); exit(1); }
    memcpy(_buf, a.datos, a.longitud);
    memcpy(_buf + a.longitud, b.datos, b.longitud);
    _buf[_tl] = 0;
    CadenaSegura _r = { .longitud = _tl, .datos = _buf };
    return _r;
}

struct GeneradorCEst;

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

inline struct GeneradorCEst GeneradorCEst_nuevo() {
    struct GeneradorCEst _r = {0};
    return _r;
}

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
#define T_IDENTIFICADOR (19)
#define T_NUMERO (20)
#define T_CADENA (22)
#define T_FLECHA_DER (37)
#define T_PAREN_IZQ (38)
#define T_PAREN_DER (39)
#define T_DOSPUNTOS (40)
#define T_COMA (41)
#define T_NUEVALINEA (42)
#define T_INDENTAR (43)
#define T_DESINDENTAR (44)
#define T_ASIGNAR (29)
#define T_MAS (30)
#define T_MENOS (31)
#define T_POR (32)
#define T_DIV (33)
#define T_MOD (34)
#define T_PUNTO (13)
#define T_IGUAL (25)
#define T_DISTINTO (26)
#define T_MENOR (24)
#define T_MAYOR (23)
#define T_MENOR_IGUAL (27)
#define T_MAYOR_IGUAL (28)
#define T_Y (14)
#define T_O (15)
#define T_NO (16)
#define T_AMPERSAND (45)
#define T_FLECHA (35)
#define T_FIN (57)
#define _GEN_TMP_SIZE (4096)
void traducir_tipo_c(void* tipo_synapse) {
    { /* unsafe */
        const char* _t = (const char*)tipo_synapse;
        if (!_t) { strcpy(_gen_tmp_buf, "void"); return; }
        int _len = (int)strlen(_t);
        if (_len > 7 && _t[0]=='C' && _t[1]=='a' && _t[2]=='n' && _t[3]=='a' && _t[4]=='l' && _t[5]=='<')
            { strcpy(_gen_tmp_buf, "CanalConcurrencia*"); return; }
        if (_len > 10 && _t[0]=='R' && _t[1]=='e' && _t[2]=='s' && _t[3]=='u' && _t[4]=='l' && _t[5]=='t' && _t[6]=='a' && _t[7]=='d' && _t[8]=='o' && _t[9]=='<')
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
    CadenaSegura r = (CadenaSegura){ .longitud = 0, .datos = "" };
    { /* unsafe */
        const char* _o = (const char*)tipo_origen;
        const char* _d = (const char*)tipo_destino;
        if (strcmp(_o, "float")==0 && strcmp(_d, "CadenaSegura")==0)
            { snprintf(_gen_tmp_buf, 4096, "decimal_a_texto(%s)", (const char*)expr_c); return; }
        if (strcmp(_o, "int")==0 && strcmp(_d, "CadenaSegura")==0)
            { snprintf(_gen_tmp_buf, 4096, "entero_a_texto(%s)", (const char*)expr_c); return; }
        if (strcmp(_o, _d)==0) { strcpy(_gen_tmp_buf, (const char*)expr_c); return; }
        snprintf(_gen_tmp_buf, 4096, "/* coercion: %s -> %s */", _o, _d);
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_193 = r;
    return _ret_193;
}

CadenaSegura prim_int_to_ptr(void* valor) {
    CadenaSegura r = (CadenaSegura){ .longitud = 0, .datos = "" };
    { /* unsafe */
        snprintf(_gen_tmp_buf, 4096, "_synapse_box_int(%s)", (const char*)valor);
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_201 = r;
    return _ret_201;
}

CadenaSegura prim_float_to_ptr(void* valor) {
    CadenaSegura r = (CadenaSegura){ .longitud = 0, .datos = "" };
    { /* unsafe */
        snprintf(_gen_tmp_buf, 4096, "_synapse_box_float(%s)", (const char*)valor);
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_208 = r;
    return _ret_208;
}

CadenaSegura syn_malloc(struct GeneradorCEst est, void* size_expr) {
    CadenaSegura r = (CadenaSegura){ .longitud = 0, .datos = "" };
    { /* unsafe */
        if (est.es_no_std) {
            snprintf(_gen_tmp_buf, 4096, "__syn_asignar(%s)", (const char*)size_expr);
        } else {
            snprintf(_gen_tmp_buf, 4096, "malloc(%s)", (const char*)size_expr);
        }
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_220 = r;
    return _ret_220;
}

CadenaSegura syn_calloc(struct GeneradorCEst est, void* n_expr, void* size_expr) {
    CadenaSegura r = (CadenaSegura){ .longitud = 0, .datos = "" };
    { /* unsafe */
        if (est.es_no_std) {
            snprintf(_gen_tmp_buf, 4096, "__syn_asignar(%s * %s)", (const char*)n_expr, (const char*)size_expr);
        } else {
            snprintf(_gen_tmp_buf, 4096, "calloc(%s, %s)", (const char*)n_expr, (const char*)size_expr);
        }
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_231 = r;
    return _ret_231;
}

CadenaSegura syn_free(struct GeneradorCEst est, void* ptr_expr) {
    CadenaSegura r = (CadenaSegura){ .longitud = 0, .datos = "" };
    { /* unsafe */
        if (est.es_no_std) {
            snprintf(_gen_tmp_buf, 4096, "__syn_liberar(%s)", (const char*)ptr_expr);
        } else {
            snprintf(_gen_tmp_buf, 4096, "free(%s)", (const char*)ptr_expr);
        }
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_242 = r;
    return _ret_242;
}

CadenaSegura syn_pool_alloc(struct GeneradorCEst est, void* size_expr) {
    CadenaSegura r = (CadenaSegura){ .longitud = 0, .datos = "" };
    { /* unsafe */
        if (est.es_no_std) {
            snprintf(_gen_tmp_buf, 4096, "__syn_asignar(%s)", (const char*)size_expr);
        } else {
            snprintf(_gen_tmp_buf, 4096, "_pool_malloc(%s)", (const char*)size_expr);
        }
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_253 = r;
    return _ret_253;
}

CadenaSegura syn_pool_free(struct GeneradorCEst est, void* ptr_expr) {
    CadenaSegura r = (CadenaSegura){ .longitud = 0, .datos = "" };
    { /* unsafe */
        if (est.es_no_std) {
            snprintf(_gen_tmp_buf, 4096, "__syn_liberar(%s)", (const char*)ptr_expr);
        } else {
            snprintf(_gen_tmp_buf, 4096, "pool_free(%s)", (const char*)ptr_expr);
        }
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_264 = r;
    return _ret_264;
}

int gen_find_var(struct GeneradorCEst est, void* nombre) {
    { /* unsafe */
        int r = (-1);
        for (int _vi = 0; _vi < est.var_total; _vi++) {
            if (strcmp(est.var_nombres.datos + _vi * 64, (const char*)nombre) == 0)
                { r = _vi; break; }
        }
        int _ret_274 = r;
        return _ret_274;
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
        if (idx >= 0 && idx < est.var_total)
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
    CadenaSegura r = (CadenaSegura){ .longitud = 0, .datos = "" };
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
    CadenaSegura _ret_305 = r;
    return _ret_305;
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

void gen_emitir_token_defs(struct GeneradorCEst est) {
    if ((est.gen_defs_emitido == 1)) {
        return;
    }
    est.gen_defs_emitido = 1;
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 20, .datos = "// --- Token IDs ---" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 14, .datos = "#define T_IF 1" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 16, .datos = "#define T_ELSE 2" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 16, .datos = "#define T_FUNC 3" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 15, .datos = "#define T_RET 4" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 17, .datos = "#define T_SPAWN 5" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 19, .datos = "#define T_RECOVER 6" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 18, .datos = "#define T_LISTEN 7" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 17, .datos = "#define T_WHILE 8" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 18, .datos = "#define T_IMPORT 9" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 18, .datos = "#define T_BREAK 10" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 21, .datos = "#define T_CONTINUE 11" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 16, .datos = "#define T_DOT 12" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 18, .datos = "#define T_IDENT 13" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 16, .datos = "#define T_NUM 14" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 16, .datos = "#define T_STR 15" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 15, .datos = "#define T_GT 16" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 15, .datos = "#define T_LT 17" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 15, .datos = "#define T_EQ 18" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 15, .datos = "#define T_NE 19" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 15, .datos = "#define T_LE 20" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 15, .datos = "#define T_GE 21" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 19, .datos = "#define T_ASSIGN 22" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 17, .datos = "#define T_PLUS 23" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 18, .datos = "#define T_MINUS 24" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 16, .datos = "#define T_MUL 25" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 16, .datos = "#define T_DIV 26" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 16, .datos = "#define T_MOD 27" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 18, .datos = "#define T_ARROW 28" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 19, .datos = "#define T_LPAREN 29" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 19, .datos = "#define T_RPAREN 30" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 18, .datos = "#define T_COLON 31" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 18, .datos = "#define T_COMMA 32" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 15, .datos = "#define T_NL 33" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 19, .datos = "#define T_INDENT 34" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 19, .datos = "#define T_DEDENT 35" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 16, .datos = "#define T_EOF 36" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 19, .datos = "#define T_STRUCT 37" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 16, .datos = "#define T_AND 38" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 15, .datos = "#define T_OR 39" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 16, .datos = "#define T_NOT 40" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 17, .datos = "#define T_TRUE 41" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 18, .datos = "#define T_FALSE 42" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 21, .datos = "#define T_INSEGURO 43" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 23, .datos = "#define T_IMPORTAR_C 44" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 22, .datos = "#define T_AMPERSAND 45" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 20, .datos = "#define T_EXTERNO 46" }).datos);
    gen_emitir_nueva_linea(est);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 22, .datos = "#define MAX_TOKS 16384" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 38, .datos = "// Global state from estado_global.syn" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 26, .datos = "_P_Token _P_tks[MAX_TOKS];" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 43, .datos = "int _P_ntks = 0, _P_tpos = 0, _P_p_err = 0;" }).datos);
    gen_emitir_linea(est, ((CadenaSegura){ .longitud = 42, .datos = "int _P_pila_indent[64], _P_nivel_pila = 0;" }).datos);
    gen_emitir_nueva_linea(est);
}

CadenaSegura gen_obtener_salida(struct GeneradorCEst est) {
    CadenaSegura r = (CadenaSegura){ .longitud = 0, .datos = "" };
    { /* unsafe */
        if (est.buf_longitud > 0 && est.buf_lineas) {
            ((char*)est.buf_lineas)[est.buf_longitud] = 0;
            strcpy(_gen_tmp_buf, (const char*)est.buf_lineas);
        } else {
            strcpy(_gen_tmp_buf, "");
        }
        r = (CadenaSegura){.longitud=(int)strlen(_gen_tmp_buf), .datos=strdup(_gen_tmp_buf)};
    }
    CadenaSegura _ret_412 = r;
    return _ret_412;
}

void gen_visitar_nodo(struct GeneradorCEst est, int nodos, int total_nodos, int tokens, int total_tokens, int idx) {
    { /* unsafe */
        if (idx < 0 || idx >= total_nodos) return;
        int* _np = (int*)nodos + idx * 11;
        int _tipo = _np[0];
        const char* _str = _np[4] ? (const char*)_np[4] : "";
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
        if (_tipo == 40) { gen_emitir_linea(est, _str); return; }
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
        // Fallback: expression statement
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
            _cur = ((int*)nodos)[_cur * 11 + 8]; // hermano
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
        // Check already emitted
        for (int _fi = 0; _fi < est.funciones_emitidas; _fi++) {
            if (strcmp((const char*)est.func_emitidas_nombres.datos + _fi * 64, _name) == 0) return;
        }
        strcpy(est.func_emitidas_nombres.datos + est.funciones_emitidas * 64, _name);
        est.funciones_emitidas = est.funciones_emitidas + 1;
        // Skip runtime builtins
        const char* _skip[] = {"escribir","escribir_linea","leer_linea","abrir","leer","cerrar",
            "crear_tensor","suma_tensor","producto_punto","relu","reserva","libera",
            "suma","producto","math_crear_tensor","math_suma_tensor","math_producto_punto",
            "math_relu","mem_reserva","mem_libera","math_suma","math_producto",
            "texto_a_entero","texto_a_decimal","decimal_a_texto","entero_a_texto",NULL};
        for (int _si = 0; _skip[_si]; _si++) {
            if (strcmp(_name, _skip[_si]) == 0) return;
        }
        // Handle special compiler functions
        if (strcmp(_name, "tokenizar") == 0) { gen_emitir_tokenizar_c(est); return; }
        if (strcmp(_name, "parsear") == 0) { gen_emitir_parsear_c(est); return; }
        if (strcmp(_name, "generar") == 0) { gen_emitir_generar_c(est); return; }
        if (strcmp(_name, "volcar_ast") == 0) { gen_emitir_volcar_ast_c(est); return; }
        // Build params
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
        // Return type
        char _ret_type[64];
        traducir_tipo_c(_ret);
        strcpy(_ret_type, _gen_tmp_buf);
        strcpy((char*)est.func_retorno_actual.datos, _ret_type);
        // Emit function
        char _buf[4096];
        snprintf(_buf, 4096, "%s %s(%s) {", _ret_type, _name, _params_str);
        gen_emitir_linea(est, _buf);
        est.indent_actual = est.indent_actual + 1;
        gen_push_scope(est);
        gen_visitar_bloque_lista(est, nodos, total_nodos, tokens, total_tokens, _body);
        gen_pop_scope(est);
        est.indent_actual = est.indent_actual - 1;
        gen_emitir_linea(est, "}");
        gen_emitir_nueva_linea(est);
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
            if (_fn && strcmp(_fn, "log") == 0)
                { gen_visitar_log(est, nodos, total_nodos, tokens, total_tokens, _expr); return; }
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
            gen_tipo_de_expr(est, nodos, total_nodos, tokens, total_tokens, _expr);
            snprintf(_buf, 4096, "%s %s = %s;", _gen_tmp_buf, _name, _val);
            gen_emitir_linea(est, _buf);
            gen_add_var(est, _name, _gen_tmp_buf);
        } else {
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
        if (_expr > 0 && _expr < total_nodos)
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
        // Handle init
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
        if (_cond > 0 && _cond < total_nodos)
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _cond, _cond_str, 4096);
        char _inc_str[4096] = "";
        if (_inc > 0 && _inc < total_nodos) {
            int* _ip2 = (int*)nodos + _inc * 11;
            if (_ip2[0] == 7)
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
        const char* _str = _np[4] ? (const char*)_np[4] : "";
        int _vint = _np[3];
        char _l[4096], _r[4096];

        if (_tipo == 9)  { snprintf(buf, bufsz, "%d", _vint); return; }
        if (_tipo == 10) { snprintf(buf, bufsz, "%ff", *(float*)&_vint); return; }
        if (_tipo == 11) { int _len = _np[5]; snprintf(buf, bufsz, "(CadenaSegura){.longitud=%d,.datos=(char*)%s}", _len, _str); return; }
        if (_tipo == 8)  {
            if (strcmp(_str, "nulo") == 0) { snprintf(buf, bufsz, "NULL"); return; }
            snprintf(buf, bufsz, "%s", _str); return;
        }
        if (_tipo == 12) { // OpBinaria
            int _op = _np[5]; int _izq = _np[6]; int _der = _np[7];
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _izq, _l, 4096);
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _der, _r, 4096);
            const char* _os = "+";
            if (_op == 25) _os = "=="; else if (_op == 26) _os = "!=";
            else if (_op == 23) _os = ">"; else if (_op == 24) _os = "<";
            else if (_op == 27) _os = "<="; else if (_op == 28) _os = ">=";
            else if (_op == 30) _os = "+"; else if (_op == 31) _os = "-";
            else if (_op == 32) _os = "*"; else if (_op == 33) _os = "/";
            else if (_op == 34) _os = "%"; else if (_op == 14) _os = "&&";
            else if (_op == 15) _os = "||";
            snprintf(buf, bufsz, "(%s %s %s)", _l, _os, _r); return;
        }
        if (_tipo == 13) { // OpUnaria
            int _op = _np[5]; int _expr = _np[6];
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _expr, _l, 4096);
            const char* _os = "-";
            if (_op == 30) _os = "+"; else if (_op == 16) _os = "!";
            snprintf(buf, bufsz, "(%s%s)", _os, _l); return;
        }
        if (_tipo == 14) { // LlamadaFuncion
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
        if (_tipo == 31) { // AccesoCampo
            int _obj = _np[6];
            gen_expr_a_c(est, nodos, total_nodos, tokens, total_tokens, _obj, _l, 4096);
            snprintf(buf, bufsz, "%s.%s", _l, _str); return;
        }
        if (_tipo == 22) { snprintf(buf, bufsz, "%d", _vint ? 1 : 0); return; }
        if (_tipo == 28) { // Tensor
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
        const char* _str = _np[4] ? (const char*)_np[4] : "";

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
            if (_vi >= 0) { strcpy(_gen_tmp_buf, (const char*)est.var_tipos.datos + _vi * 64); return; }
            strcpy(_gen_tmp_buf, "int"); return;
        }
        if (_tipo == 14) {
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
            strcpy(_gen_tmp_buf, gen_func_return_type(est, _str).datos);
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
        // Emit P_tokenizar function
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
        // Single-char tokens and identifiers... 
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

        // Parser entry point
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
        // Emit _gen helper functions
        gen_emitir_linea(est, "// --- AST Walker (auto-generado) ---");
        gen_emitir_linea(est, "// Global state from estado_global.syn");
        gen_emitir_linea(est, "int _G_indent = 0;");
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
        gen_emitir_linea(est, "void _G_emit(const char* s) { for(int i=0;i<_G_indent;i++) fprintf(_G_out,\"    \") fprintf(_G_out,\"%s\\n\",s) }");
        gen_emitir_nueva_linea(est);
        // Main generar function
        gen_emitir_linea(est, "int generar(struct Programa programa, CadenaSegura ruta) {");
        est.indent_actual = est.indent_actual + 1;
        gen_emitir_linea(est, "char sal[1024]; int sl=ruta.longitud;");
        gen_emitir_linea(est, "if(sl>4&&ruta.datos[sl-4]=='.'&&(ruta.datos[sl-3]=='s'||ruta.datos[sl-3]=='S')&&(ruta.datos[sl-2]=='y'||ruta.datos[sl-2]=='Y')&&(ruta.datos[sl-1]=='n'||ruta.datos[sl-1]=='N')){memcpy(sal,ruta.datos,sl-4);sal[sl-4]='.';sal[sl-3]='c';sal[sl-2]=0;}else snprintf(sal,sizeof(sal),\"%.*s.c\",ruta.longitud,ruta.datos);");
        gen_emitir_linea(est, "_G_out=fopen(sal,\"w\"); if(!_G_out){fprintf(stderr,\"Error: no se puede crear %%s\\n\",sal);return 1;}");
        gen_emitir_linea(est, "fprintf(_G_out,\"// Generado por Synapse (auto-hospedado)\\n\");");
        gen_emitir_linea(est, "fprintf(_G_out,\"#include <stdio.h>\\n#include <stdlib.h>\\n#include <stdint.h>\\n#include <string.h>\\n#include <pthread.h>\\n\");");
        gen_emitir_linea(est, "fprintf(_G_out,\"typedef struct {int longitud;const char* datos;} CadenaSegura;\\n\");");
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
        gen_emitir_linea(est, "for(int i=0;i<nivel;i++)printf(\"  \")");
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
        (void)est; (void)exclude_var; // stub
    }
}

// --- Generador de C ---
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

void _P_tokenizar(const char* s, int len) {
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
    while (_P_mirar()->tipo == T_NL) { _P_avanzar(); }
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
                _P_avanzar(); if (_P_mirar()->tipo!=T_IDENT) break;
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
// --- AST Walker ---
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
int _G_find(const char* n) { for(int i=0;i<_G_nv;i++) if(strcmp(_G_vn[i],n)==0) return i; return -1; }
const char* _G_decl(const char* n, const char* t) {
    int i=_G_find(n); if(i>=0) return _G_vt[i];
    if(_G_nv<1024){ strcpy(_G_vn[_G_nv],n); strcpy(_G_vt[_G_nv],t); _G_nv++; }
    return t;
}

void _G_emit(const char* s) {
    for(int i=0;i<_G_indent;i++) fprintf(_G_out,"    ");
    fprintf(_G_out,"%s\n",s);
}

void _G_cp(char* d, CadenaSegura cs) { memcpy(d,cs.datos,cs.longitud); d[cs.longitud]=0; }

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
    char f[4096]=""; int fp=0,ap=0,fi=1; char b[512]; char pr[4096]="";
    struct ListaNodo* c=n->argumentos;
    while(c){ if(!fi){ f[fp++]=' '; } fi=0; f[fp++]='%'; f[fp++]='s';
        _G_ea(c->cabeza,b,512); if(ap>0){ pr[ap++]=','; pr[ap++]=' '; } int k=0; while(b[k]) pr[ap++]=b[k++]; c=c->cola;
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
        const char* vt=_G_tex(a->expresion);
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
    if(strcmp(t,"SentenciaExpr")==0){ struct SentenciaExpr* e=(struct SentenciaExpr*)n; if(e->expr){ if(strcmp(e->expr->tipo.datos,"LogLlamada")==0){ _G_v_log((struct LogLlamada*)e->expr); } else { _G_ea(e->expr,v,4096); snprintf(b,sizeof(b),"%s;",v); _G_emit(b); } } return; }
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
    snprintf(cmd, sizeof(cmd), "gcc -O2 -fno-ident -Wl,--no-insert-timestamp \"%s\" \"C:\\Synapse\\lib\\synapse_rt.o\" -o \"%s\" -lpthread -lm", sal, out_exe);
    int rc = system(cmd);
    if (rc != 0) {
        fprintf(stderr, "[LINKER ERROR] gcc fallo con codigo %d\n", rc);
        exit(1);
    }
    fprintf(stderr, "OK: %s\n", out_exe);
    return 0;
}
int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    synapse_esperar_hilos();
    return 0;
}