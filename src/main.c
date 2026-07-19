// salida_metal.c - Generado por Synapse Compilador
// Lenguaje: Synapse v1.0 (#lang: es)
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <string.h>
#include <assert.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;

typedef struct { uint32_t filas; uint32_t columnas; float* datos; } Tensor;

typedef struct { FILE* stream; int es_valido; int es_virtual; const char* virtual_data; int virtual_len; } Canal;

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

static inline struct Resultado Resultado_nuevo() {
    struct Resultado _r = {0};
    return _r;
}

typedef struct Opcion {
    int tag;
    union {
        int valor;
        CadenaSegura valor_str;
        float valor_float;
    } dato;
} Opcion;

static inline struct Opcion Opcion_nuevo() {
    struct Opcion _r = {0};
    return _r;
}

typedef struct ParToml {
    CadenaSegura clave;
    struct NodoToml* valor;
} ParToml;

static inline struct ParToml ParToml_nuevo() {
    struct ParToml _r = {0};
    return _r;
}

typedef struct NodoToml {
    int tipo;
    CadenaSegura valor_str;
    struct ParToml* pares;
    int longitud;
} NodoToml;

static inline struct NodoToml NodoToml_nuevo() {
    struct NodoToml _r = {0};
    return _r;
}

extern struct NodoToml _toml_parse(CadenaSegura entrada);
extern struct NodoToml _toml_nodo_new(void);
extern void _toml_nodo_liberar(struct NodoToml n);
extern struct NodoToml _toml_object_get(struct NodoToml nodo, CadenaSegura clave);
struct NodoToml desde_texto(CadenaSegura entrada) {
    struct NodoToml _ret_29 = _toml_parse(entrada);
    return _ret_29;
}

struct NodoToml obtener_campo(struct NodoToml nodo, CadenaSegura clave) {
    struct NodoToml _ret_32 = _toml_object_get(nodo, clave);
    return _ret_32;
}

CadenaSegura _leer_archivo(CadenaSegura ruta) {
    Canal f = abrir(ruta, (CadenaSegura){ .longitud = 1, .datos = "r" });
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
    CadenaSegura _ret_19 = (CadenaSegura){ .longitud = 0, .datos = "" };
    return _ret_19;
}

void principal(void) {
    escribir_linea((CadenaSegura){ .longitud = 31, .datos = "Synapse v2.0 — Auto-hospedado" });
    escribir_linea((CadenaSegura){ .longitud = 32, .datos = "Cargando manifiesto axon.toml..." });
    CadenaSegura toml_str = _leer_archivo((CadenaSegura){ .longitud = 9, .datos = "axon.toml" });
    struct NodoToml doc = desde_texto(toml_str);
    struct NodoToml proy = obtener_campo(doc, (CadenaSegura){ .longitud = 8, .datos = "proyecto" });
    CadenaSegura nombre = _campo_str(proy, (CadenaSegura){ .longitud = 6, .datos = "nombre" });
    CadenaSegura version = _campo_str(proy, (CadenaSegura){ .longitud = 7, .datos = "version" });
    CadenaSegura entrada = _campo_str(proy, (CadenaSegura){ .longitud = 13, .datos = "punto_entrada" });
    escribir_linea(concat(concat(concat((CadenaSegura){ .longitud = 10, .datos = "Proyecto: " }, nombre), (CadenaSegura){ .longitud = 2, .datos = " v" }), version));
    escribir_linea(concat((CadenaSegura){ .longitud = 9, .datos = "Entrada: " }, entrada));
    escribir_linea((CadenaSegura){ .longitud = 37, .datos = "[OK] Manifiesto cargado correctamente" });
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
    return 0;
}