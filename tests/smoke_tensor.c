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

#include <stdlib.h>
#include <stdio.h>
#include "axon_modules/std.tensor/std_tensor_helper.h"
int crear_tensor_2d(int filas, int columnas) {
    return _syn_crear_tensor_2d(filas, columnas);
}

void liberar_tensor(int id) {
    _syn_liberar_tensor(id);
}

void escribir_tensor(int id, int f, int c, float val) {
    _syn_tensor_escribir(id, f, c, val);
}

float leer_tensor(int id, int f, int c) {
    return _syn_tensor_leer(id, f, c);
}

void multiplicar_tensor(int id_A, int id_B, int id_C) {
    _syn_tensor_matmul(id_A, id_B, id_C);
}

void principal(void) {
    int A = crear_tensor_2d(2, 2);
    int B = crear_tensor_2d(2, 2);
    int C = crear_tensor_2d(2, 2);
    escribir_tensor(A, 0, 0, 1.0f);
    escribir_tensor(A, 0, 1, 2.0f);
    escribir_tensor(A, 1, 0, 3.0f);
    escribir_tensor(A, 1, 1, 4.0f);
    escribir_tensor(B, 0, 0, 5.0f);
    escribir_tensor(B, 0, 1, 6.0f);
    escribir_tensor(B, 1, 0, 7.0f);
    escribir_tensor(B, 1, 1, 8.0f);
    multiplicar_tensor(A, B, C);
    float v = leer_tensor(C, 0, 0);
    printf("C[0,0] =  %f\n", v);
    liberar_tensor(A);
    liberar_tensor(B);
    liberar_tensor(C);
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    principal();
    synapse_esperar_hilos();
    return 0;
}