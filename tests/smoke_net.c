// salida_metal.c - Generado por Synapse Compilador
// Lenguaje: Synapse v1.0 (#lang: es)
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <string.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;

typedef struct { uint32_t filas; uint32_t columnas; float* datos; } Tensor;

typedef struct { FILE* stream; int es_valido; int es_virtual; const char* virtual_data; int virtual_len; } Canal;

// Constantes del pool de memoria (definidas en synapse_rt.c)
#define POOL_BLOQUES 64
#define TAMANO_BLOQUE 4096

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

struct DatosRed;

#include <winsock2.h>
#include <windows.h>
typedef struct DatosRed {
    int d0;
    int d1;
    int d2;
    int d3;
    int d4;
    int d5;
    int d6;
    int d7;
    int d8;
    int d9;
    int d10;
    int d11;
    int d12;
    int d13;
    int d14;
    int d15;
    int d16;
    int d17;
    int d18;
    int d19;
    int d20;
    int d21;
    int d22;
    int d23;
    int d24;
    int d25;
    int d26;
    int d27;
    int d28;
    int d29;
    int d30;
    int d31;
    int d32;
    int d33;
    int d34;
    int d35;
    int d36;
    int d37;
    int d38;
    int d39;
    int d40;
    int d41;
    int d42;
    int d43;
    int d44;
    int d45;
    int d46;
    int d47;
    int d48;
    int d49;
    int d50;
    int d51;
    int d52;
    int d53;
    int d54;
    int d55;
    int d56;
    int d57;
    int d58;
    int d59;
    int d60;
    int d61;
    int d62;
    int d63;
    int d64;
    int d65;
    int d66;
    int d67;
    int d68;
    int d69;
    int d70;
    int d71;
    int d72;
    int d73;
    int d74;
    int d75;
    int d76;
    int d77;
    int d78;
    int d79;
    int d80;
    int d81;
    int d82;
    int d83;
    int d84;
    int d85;
    int d86;
    int d87;
    int d88;
    int d89;
    int d90;
    int d91;
    int d92;
    int d93;
    int d94;
    int d95;
    int d96;
    int d97;
    int d98;
    int d99;
} DatosRed;

static inline struct DatosRed DatosRed_nuevo() {
    struct DatosRed _r = {0};
    return _r;
}

int iniciar_red(void) {
    struct DatosRed datos = DatosRed_nuevo();
    return WSAStartup(514, (&datos));
}

void cerrar_red(void) {
    WSACleanup();
    return;
}

int crear_socket(void) {
    return socket(2, 1, 0);
}

void principal(void) {
    int r = iniciar_red();
    printf("iniciar_red:  %d\n", r);
    int s = crear_socket();
    printf("socket:  %d\n", s);
    cerrar_red();
    printf("red cerrada\n");
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    principal();
    synapse_esperar_hilos();
    return 0;
}