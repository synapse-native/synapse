// synapse_rt_types.h — Shared type definitions for modularized Synapse runtime
// This header is included by synapse_rt.c, synapse_rt_memory.c, synapse_rt_concurrency.c
#ifndef SYNAPSE_RT_TYPES_H
#define SYNAPSE_RT_TYPES_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>

// --- Core type definitions (deben coincidir exactamente con las emitidas por el generador) ---
typedef struct { int longitud; const char* datos; } CadenaSegura;
typedef struct { uint32_t filas; uint32_t columnas; float* datos; int es_mapeado; } Tensor;
typedef struct { FILE* stream; int es_valido; int es_virtual; const char* virtual_data; int virtual_len; } Canal;

// --- Resultado<T, E> (Tagged Union para manejo de errores de canal) ---
typedef struct {
    int es_ok; // 1 = ok, 0 = error
    union {
        void* ok_valor;
        const char* err_mensaje;
    } datos;
} Resultado_T;

// --- CanalConcurrencia (Buffer circular thread-safe + sync handoff) ---
typedef struct CanalConcurrencia {
    void** buffer;
    uint32_t capacidad;
    uint32_t cabeza;  // índice de escritura
    uint32_t cola;    // índice de lectura
    uint32_t contador; // número de elementos en el buffer
    int es_sync;       // 1 = canal síncrono (handoff directo, capacidad=0)
    void* sync_item;   // elemento en tránsito (solo para sync)
    int cerrado;       // 1 = canal cerrado (Manual 5 §5.3)
    pthread_mutex_t mutex;
    pthread_cond_t no_vacio;  // señal para receptores
    pthread_cond_t no_lleno;  // señal para emisores
} CanalConcurrencia;

// --- Memory pool constants ---
#define POOL_BLOQUES 64
#define TAMANO_BLOQUE 4096
#define SLAB_COUNT 4
#define SLOTS_PER_BLOCK(slab_sz) (TAMANO_BLOQUE / (slab_sz))

// --- MemoryPool (slab allocator) ---
typedef struct {
    uint8_t* pool_base;
    uint32_t* bitmap;
    uint32_t total_blocks;
    uint32_t block_size;
    uint8_t* slab_base[SLAB_COUNT];
    uint32_t slab_block_idx[SLAB_COUNT];
    uint32_t slab_next_free[SLAB_COUNT];
    uint32_t* slab_bitmap[SLAB_COUNT];
    uint32_t slab_slots_per_block[SLAB_COUNT];
} MemoryPool;

// --- Thread tracker helpers ---
struct _HiloArgs {
    void* (*fn)(void*);
    void* arg;
};

// --- JSON parser types ---
#define JSON_MAX_NODES 65536
#define JSON_INIT_CAP 64

typedef struct ParJson ParJson;
typedef struct NodoJson NodoJson;

struct ParJson {
    CadenaSegura clave;
    NodoJson* valor;
};

struct NodoJson {
    int tipo;                // -1=Error, 0=Nulo, 1=Booleano, 2=Numero, 3=Cadena, 4=Arreglo, 5=Objeto
    int valor_bool;
    float valor_num;
    CadenaSegura valor_str;
    NodoJson* arreglo_hijos;
    ParJson* objeto_pares;
    int longitud;
};

// --- Dynamic array helpers for JSON ---
typedef struct {
    NodoJson* items;
    int count;
    int cap;
} NodoArr;

typedef struct {
    ParJson* items;
    int count;
    int cap;
} ParArr;

// --- Watchdog types (debug mode) ---
#ifdef SYNAPSE_DEBUG_MEM
#define MAX_WATCHDOG_ENTRIES 100000

typedef struct {
    void* ptr;
    size_t size;
    const char* file;
    int line;
} WatchdogEntry;
#endif

// ============================================================
// Cross-module function declarations
// Defined in synapse_rt_memory.c:
// ============================================================
void pool_init(uint32_t total_blocks, uint32_t block_size);
void* pool_alloc(size_t size);
void pool_free(void* ptr);
void pool_destroy(void);
float* _pool_malloc(size_t tamano);
void watchdog_report(void);
void* _syn_buffer_alloc(int tamano);
void _syn_buffer_free(void* ptr);
CadenaSegura _syn_recibir_como_texto(int fd, int tamano);
void _syn_texto_liberar(CadenaSegura s);

// ============================================================
// Defined in synapse_rt_concurrency.c:
// ============================================================
void escribir(CadenaSegura contenido);
void escribir_linea(CadenaSegura contenido);
CadenaSegura leer_linea(void);
void synapse_lanzar_hilo(void* (*fn)(void*), void* arg);
void synapse_esperar_hilos(void);
CanalConcurrencia* canal_crear(uint32_t capacidad);
void canal_enviar(CanalConcurrencia* canal, void* paquete);
void* canal_recibir(CanalConcurrencia* canal);
void canal_destruir(CanalConcurrencia* canal);

// ============================================================
// Defined in synapse_rt.c:
// ============================================================
Canal abrir(CadenaSegura ruta, CadenaSegura modo);
CadenaSegura leer(Canal canal);
void cerrar(Canal canal);

#endif /* SYNAPSE_RT_TYPES_H */
