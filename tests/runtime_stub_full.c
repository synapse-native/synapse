#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;
typedef struct { uint32_t filas; uint32_t columnas; float* datos; } Tensor;
typedef struct { FILE* stream; int es_valido; int es_virtual; const char* virtual_data; int virtual_len; } Canal;

void pool_init(uint32_t total_blocks, uint32_t block_size) { fprintf(stderr, "pool_init\n"); }
void pool_free(void* ptr) {}
void escribir(CadenaSegura contenido) { fprintf(stderr, "%.*s", contenido.longitud, contenido.datos); }
void escribir_linea(CadenaSegura contenido) { fprintf(stderr, "%.*s\n", contenido.longitud, contenido.datos); }
CadenaSegura leer_linea(void) { return (CadenaSegura){0, ""}; }
Canal abrir(CadenaSegura ruta, CadenaSegura modo) { return (Canal){0}; }
CadenaSegura leer(Canal canal) { return (CadenaSegura){0, ""}; }
void cerrar(Canal canal) {}
Tensor crear_tensor(int filas, int columnas) { return (Tensor){0}; }
Tensor suma_tensor(Tensor a, Tensor b) { return (Tensor){0}; }
Tensor producto_punto(Tensor a, Tensor b) { return (Tensor){0}; }
Tensor relu(Tensor a) { return (Tensor){0}; }
Tensor reserva(int tamano) { return (Tensor){0}; }
void libera(Tensor bloque) {}
Tensor suma(Tensor a, Tensor b) { return (Tensor){0}; }
Tensor producto(Tensor a, Tensor b) { return (Tensor){0}; }
int texto_a_entero(CadenaSegura str) { return 0; }
float texto_a_decimal(CadenaSegura str) { return 0.0f; }
CadenaSegura decimal_a_texto(float n) { return (CadenaSegura){0, ""}; }
CadenaSegura entero_a_texto(int n) { return (CadenaSegura){0, ""}; }
void synapse_lanzar_hilo(void* (*fn)(void*), void* arg) {}
void synapse_esperar_hilos(void) { fprintf(stderr, "synapse_esperar_hilos\n"); }
