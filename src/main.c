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

extern char _gen_tmp_buf[4096];

extern char _G_emit_buf[1048576];
extern int _G_emit_pos;
extern FILE* _G_fp;

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

struct Resultado;
struct Opcion;
struct ParToml;
struct NodoToml;

typedef struct Resultado {
    int tag;
    union {
        int valor;
        CadenaSegura valor_str;
        float valor_float;
    } dato;
} Resultado;

typedef struct Opcion {
    int tag;
    union {
        int valor;
        CadenaSegura valor_str;
        float valor_float;
    } dato;
} Opcion;

typedef struct ParToml {
    CadenaSegura clave;
    struct NodoToml* valor;
} ParToml;

typedef struct NodoToml {
    int tipo;
    CadenaSegura valor_str;
    int valor_ent;
    struct ParToml* pares;
    int longitud;
} NodoToml;

struct NodoToml desde_texto(CadenaSegura entrada);
struct NodoToml obtener_campo(struct NodoToml nodo, CadenaSegura clave);
CadenaSegura sha256_texto(CadenaSegura datos);
int ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica);
CadenaSegura _validar_ruta_segura(CadenaSegura ruta);
int ejecutar_comando(CadenaSegura cmd);
int escribir_archivo(CadenaSegura ruta, CadenaSegura contenido);
CadenaSegura leer_archivo(CadenaSegura ruta);
CadenaSegura obtener_env(CadenaSegura nombre);
int existe_archivo(CadenaSegura ruta);
int eliminar_archivo(CadenaSegura ruta);
CadenaSegura _leer_archivo(CadenaSegura ruta);
CadenaSegura _campo_str(struct NodoToml nodo, CadenaSegura clave);
void principal(void);

extern struct NodoToml _toml_parse(CadenaSegura entrada);
extern struct NodoToml _toml_nodo_new(void);
extern void _toml_nodo_liberar(struct NodoToml n);
extern struct NodoToml _toml_object_get(struct NodoToml nodo, CadenaSegura clave);
struct NodoToml desde_texto(CadenaSegura entrada) {
    struct NodoToml _ret_30 = _toml_parse(entrada);
    return _ret_30;
}

struct NodoToml obtener_campo(struct NodoToml nodo, CadenaSegura clave) {
    struct NodoToml _ret_33 = _toml_object_get(nodo, clave);
    return _ret_33;
}

extern CadenaSegura _syn_sha256_texto(CadenaSegura datos);
extern int _syn_ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica);
CadenaSegura sha256_texto(CadenaSegura datos) {
    CadenaSegura _ret_20 = _syn_sha256_texto(datos);
    return _ret_20;
}

int ed25519_verificar(CadenaSegura mensaje, CadenaSegura firma, CadenaSegura clave_publica) {
    int _ret_23 = _syn_ed25519_verificar(mensaje, firma, clave_publica);
    return _ret_23;
}

extern CadenaSegura _syn_normalizar_ruta(CadenaSegura ruta);
extern CadenaSegura _syn_obtener_cwd(void);
extern int _syn_ruta_en_directorio(CadenaSegura ruta, CadenaSegura dir);
CadenaSegura _validar_ruta_segura(CadenaSegura ruta) {
    CadenaSegura normalizada = _syn_normalizar_ruta(ruta);
    CadenaSegura cwd = _syn_obtener_cwd();
    if ((!_syn_ruta_en_directorio(normalizada, cwd))) {
        CadenaSegura _ret_22 = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        _syn_texto_liberar(cwd);
        _syn_texto_liberar(normalizada);
        return _ret_22;
    }
    CadenaSegura _ret_23 = normalizada;
    return _ret_23;
}

extern int _syn_ejecutar_comando(CadenaSegura cmd);
extern int _syn_escribir_archivo(CadenaSegura ruta, CadenaSegura contenido);
extern CadenaSegura _syn_leer_archivo(CadenaSegura ruta);
extern CadenaSegura _syn_obtener_env(CadenaSegura nombre);
extern int _syn_existe_archivo(CadenaSegura ruta);
extern int _syn_eliminar_archivo(CadenaSegura ruta);
int ejecutar_comando(CadenaSegura cmd) {
    int _ret_33 = _syn_ejecutar_comando(cmd);
    return _ret_33;
}

int escribir_archivo(CadenaSegura ruta, CadenaSegura contenido) {
    CadenaSegura ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        int _ret_38 = (-1);
        _syn_texto_liberar(ruta_segura);
        return _ret_38;
    }
    int _ret_39 = _syn_escribir_archivo(ruta_segura, contenido);
    return _ret_39;
}

CadenaSegura leer_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        CadenaSegura _ret_44 = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
        _syn_texto_liberar(ruta_segura);
        return _ret_44;
    }
    CadenaSegura _ret_45 = _syn_leer_archivo(ruta_segura);
    return _ret_45;
}

CadenaSegura obtener_env(CadenaSegura nombre) {
    CadenaSegura _ret_48 = _syn_obtener_env(nombre);
    return _ret_48;
}

int existe_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        int _ret_53 = 0;
        _syn_texto_liberar(ruta_segura);
        return _ret_53;
    }
    int _ret_54 = (_syn_existe_archivo(ruta_segura) == 1);
    return _ret_54;
}

int eliminar_archivo(CadenaSegura ruta) {
    CadenaSegura ruta_segura = _validar_ruta_segura(ruta);
    if ((str_eq(ruta_segura, (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }) == 1)) {
        int _ret_59 = (-1);
        _syn_texto_liberar(ruta_segura);
        return _ret_59;
    }
    int _ret_60 = _syn_eliminar_archivo(ruta_segura);
    return _ret_60;
}

extern Canal _syn_abrir(CadenaSegura ruta, CadenaSegura modo);
extern CadenaSegura _syn_leer(Canal c);
extern void _syn_escribir(CadenaSegura texto);
extern void _syn_escribir_linea(CadenaSegura texto);
extern CadenaSegura _syn_leer_linea(void);
CadenaSegura _leer_archivo(CadenaSegura ruta) {
    Canal f;
    f = abrir(ruta, (CadenaSegura){ .longitud = (int)strlen("r"), .datos = "r" });
    CadenaSegura resultado = leer(f);
    cerrar(f);
    CadenaSegura _ret_13 = resultado;
    return _ret_13;
}

CadenaSegura _campo_str(struct NodoToml nodo, CadenaSegura clave) {
    struct NodoToml campo = obtener_campo(nodo, clave);
    if ((campo.tipo == 2)) {
        CadenaSegura _ret_18 = campo.valor_str;
        _toml_nodo_liberar(campo);
        return _ret_18;
    }
    CadenaSegura _ret_19 = (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" };
    return _ret_19;
}

void principal(void) {
    _simd_detectar();
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("Synapse v2.0 — Auto-hospedado"), .datos = "Synapse v2.0 — Auto-hospedado" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("Cargando manifiesto axon.toml..."), .datos = "Cargando manifiesto axon.toml..." });
    CadenaSegura toml_str = _leer_archivo((CadenaSegura){ .longitud = (int)strlen("axon.toml"), .datos = "axon.toml" });
    struct NodoToml doc = desde_texto(toml_str);
    struct NodoToml proy = obtener_campo(doc, (CadenaSegura){ .longitud = (int)strlen("proyecto"), .datos = "proyecto" });
    CadenaSegura nombre = _campo_str(proy, (CadenaSegura){ .longitud = (int)strlen("nombre"), .datos = "nombre" });
    CadenaSegura version = _campo_str(proy, (CadenaSegura){ .longitud = (int)strlen("version"), .datos = "version" });
    CadenaSegura entrada = _campo_str(proy, (CadenaSegura){ .longitud = (int)strlen("punto_entrada"), .datos = "punto_entrada" });
    escribir_linea(concat(concat(concat((CadenaSegura){ .longitud = (int)strlen("Proyecto: "), .datos = "Proyecto: " }, nombre), (CadenaSegura){ .longitud = (int)strlen(" v"), .datos = " v" }), version));
    escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("Entrada: "), .datos = "Entrada: " }, entrada));
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("[OK] Manifiesto cargado correctamente"), .datos = "[OK] Manifiesto cargado correctamente" });
    _syn_texto_liberar(entrada);
    _syn_texto_liberar(version);
    _syn_texto_liberar(nombre);
    _toml_nodo_liberar(proy);
    _toml_nodo_liberar(doc);
    _syn_texto_liberar(toml_str);
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    principal();
    synapse_esperar_hilos();
    pool_destroy();
    return 0;
}