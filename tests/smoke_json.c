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
struct ParJson;
struct NodoJson;

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

typedef struct ParJson {
    CadenaSegura clave;
    struct NodoJson* valor;
} ParJson;

static inline struct ParJson ParJson_nuevo() {
    struct ParJson _r = {0};
    return _r;
}

typedef struct NodoJson {
    int tipo;
    int valor_bool;
    float valor_num;
    CadenaSegura valor_str;
    struct NodoJson* arreglo_hijos;
    struct ParJson* objeto_pares;
    int longitud;
} NodoJson;

static inline struct NodoJson NodoJson_nuevo() {
    struct NodoJson _r = {0};
    return _r;
}

extern struct NodoJson _json_parse(CadenaSegura entrada);
extern struct NodoJson _json_nodo_new(void);
extern void _json_nodo_liberar(struct NodoJson n);
struct NodoJson desde_texto(CadenaSegura entrada) {
    return _json_parse(entrada);
}

void liberar_nodo(struct NodoJson n) {
    _json_nodo_liberar(n);
    return;
}

void principal(void) {
    struct NodoJson nodo = desde_texto((CadenaSegura){ .longitud = 2, .datos = "42" });
    if ((nodo.tipo >= 0)) {
        printf("entero OK\n");
    } else {
        printf("FALLO entero\n");
    }
    liberar_nodo(nodo);
    nodo = desde_texto((CadenaSegura){ .longitud = 4, .datos = "3.14" });
    if ((nodo.tipo >= 0)) {
        printf("decimal OK\n");
    } else {
        printf("FALLO decimal\n");
    }
    liberar_nodo(nodo);
    nodo = desde_texto((CadenaSegura){ .longitud = 4, .datos = "true" });
    if ((nodo.tipo >= 0)) {
        printf("bool true OK\n");
    } else {
        printf("FALLO bool\n");
    }
    liberar_nodo(nodo);
    nodo = desde_texto((CadenaSegura){ .longitud = 5, .datos = "false" });
    if ((nodo.tipo >= 0)) {
        printf("bool false OK\n");
    } else {
        printf("FALLO bool false\n");
    }
    liberar_nodo(nodo);
    nodo = desde_texto((CadenaSegura){ .longitud = 4, .datos = "null" });
    if ((nodo.tipo >= 0)) {
        printf("null OK\n");
    } else {
        printf("FALLO null\n");
    }
    liberar_nodo(nodo);
    nodo = desde_texto((CadenaSegura){ .longitud = 9, .datos = "[1, 2, 3]" });
    if ((nodo.tipo >= 0)) {
        printf("array OK len= %d\n", nodo.longitud);
    } else {
        printf("FALLO array\n");
    }
    liberar_nodo(nodo);
    nodo = desde_texto((CadenaSegura){ .longitud = 16, .datos = "[[1, 2], [3, 4]]" });
    if ((nodo.tipo >= 0)) {
        printf("nested array OK len= %d\n", nodo.longitud);
    } else {
        printf("FALLO nested array\n");
    }
    liberar_nodo(nodo);
    nodo = desde_texto((CadenaSegura){ .longitud = 2, .datos = "{}" });
    if ((nodo.tipo >= 0)) {
        printf("objeto vacio OK\n");
    } else {
        printf("FALLO objeto vacio\n");
    }
    liberar_nodo(nodo);
    nodo = desde_texto((CadenaSegura){ .longitud = 5, .datos = "{mal}" });
    if ((nodo.tipo < 0)) {
        printf("error OK:  %s\n", (nodo.valor_str).datos);
    } else {
        printf("FALLO: debio dar error\n");
    }
    liberar_nodo(nodo);
    printf("FIN\n");
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    principal();
    synapse_esperar_hilos();
    return 0;
}