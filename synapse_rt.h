// synapse_rt.h — Public API del runtime Synapse
#ifndef SYNAPSE_RT_H
#define SYNAPSE_RT_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;
typedef struct { uint32_t filas; uint32_t columnas; float* datos; } Tensor;
typedef struct { FILE* stream; int es_valido; int es_virtual; const char* virtual_data; int virtual_len; } Canal;

void escribir(CadenaSegura contenido);
void escribir_linea(CadenaSegura contenido);
CadenaSegura leer_linea(void);
Canal abrir(CadenaSegura ruta, CadenaSegura modo);
CadenaSegura leer(Canal canal);
void cerrar(Canal canal);

Tensor crear_tensor(int filas, int columnas);
Tensor suma_tensor(Tensor a, Tensor b);
Tensor producto_punto(Tensor a, Tensor b);
Tensor relu(Tensor a);
Tensor suma(Tensor a, Tensor b);
Tensor producto(Tensor a, Tensor b);

Tensor reserva(int tamano);
void libera(Tensor bloque);

int texto_a_entero(CadenaSegura str);
float texto_a_decimal(CadenaSegura str);
CadenaSegura decimal_a_texto(float n);
CadenaSegura entero_a_texto(int n);

// --- CanalConcurrencia API (Zero-Copy, Thread-Safe) ---
typedef struct {
    int es_ok;
    union {
        void* ok_valor;
        const char* err_mensaje;
    } datos;
} Resultado_T;

typedef struct CanalConcurrencia CanalConcurrencia;
CanalConcurrencia* canal_crear(uint32_t capacidad);
void canal_enviar(CanalConcurrencia* canal, void* paquete);
void* canal_recibir(CanalConcurrencia* canal);
void canal_destruir(CanalConcurrencia* canal);

void synapse_lanzar_hilo(void* (*fn)(void*), void* arg);
void synapse_esperar_hilos(void);

#endif
