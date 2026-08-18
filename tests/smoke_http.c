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
extern void* canal_recibir(CanalConcurrencia* canal, bool* cerrado);
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
struct SocketTCP;

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

typedef struct SocketTCP {
    int descriptor;
} SocketTCP;

static inline struct SocketTCP SocketTCP_nuevo() {
    struct SocketTCP _r = {0};
    return _r;
}

extern int _syn_iniciar_red(void);
extern int _syn_cerrar_red(void);
extern int _syn_socket(void);
extern int _syn_conectar(int fd, char* ip, int puerto);
extern int _syn_enviar(int fd, char* datos, int lon);
extern int _syn_recibir(int fd, char* buf, int lon);
extern int _syn_cerrar_socket(int fd);
extern CadenaSegura _syn_recibir_como_texto(int fd, int tamano);
extern void _syn_texto_liberar(CadenaSegura t);
int iniciar_red(void) {
    return _syn_iniciar_red();
}

void cerrar_red(void) {
    _syn_cerrar_red();
    return;
}

int crear_socket(void) {
    return _syn_socket();
}

struct Resultado conectar(CadenaSegura ip, int puerto) {
    struct Resultado r = Resultado_nuevo();
    int fd = _syn_socket();
    if ((fd < 0)) {
        r.tag = 1;
        r.dato.valor = fd;
        return r;
    }
    int res = _syn_conectar(fd, (ip).datos, puerto);
    if ((res < 0)) {
        _syn_cerrar_socket(fd);
        r.tag = 1;
        r.dato.valor = res;
        return r;
    }
    r.tag = 0;
    r.dato.valor = fd;
    return r;
}

int enviar_datos(int fd, CadenaSegura datos, int lon) {
    return _syn_enviar(fd, (datos).datos, lon);
}

struct Resultado recibir_datos(struct SocketTCP socket, int tamano_maximo) {
    struct Resultado r = Resultado_nuevo();
    CadenaSegura recibido = _syn_recibir_como_texto(socket.descriptor, tamano_maximo);
    if ((strcmp(recibido.datos, (CadenaSegura){ .longitud = 0, .datos = "" }.datos) == 0)) {
        r.tag = 1;
        r.dato.valor = (-1);
        return r;
    }
    r.tag = 0;
    r.dato.valor_str = recibido;
    return r;
}

int cerrar_socket(int fd) {
    return _syn_cerrar_socket(fd);
}

void liberar_texto(CadenaSegura t) {
    _syn_texto_liberar(t);
    return;
}

void principal(void) {
    iniciar_red();
    struct Resultado r = conectar((CadenaSegura){ .longitud = 7, .datos = "1.1.1.1" }, 80);
    if ((r.tag == 0)) {
        int fd = r.dato.valor;
        struct SocketTCP s = SocketTCP_nuevo();
        s.descriptor = fd;
        enviar_datos(fd, (CadenaSegura){ .longitud = 52, .datos = "GET / HTTP/1.1\r\nHost: 1.1.1.1\r\nConnection: close\r\n\r\n" }, 52);
        struct Resultado respuesta = recibir_datos(s, 512);
        if ((respuesta.tag == 0)) {
            printf("HTTP:  %s\n", (respuesta.dato.valor_str).datos);
            liberar_texto(respuesta.dato.valor_str);
        } else {
            printf("recibir_datos fallo\n");
        }
        cerrar_socket(fd);
    } else {
        printf("conectar fallo:  %d\n", r.dato.valor);
    }
    cerrar_red();
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    principal();
    synapse_esperar_hilos();
    return 0;
}