// synapse_rt_types.h — Shared type definitions for modularized Synapse runtime
// This header is included by synapse_rt.c, synapse_rt_memory.c, synapse_rt_concurrency.c
#ifndef SYNAPSE_RT_TYPES_H
#define SYNAPSE_RT_TYPES_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <pthread.h>

// --- Core type definitions (deben coincidir exactamente con las emitidas por el generador) ---
typedef struct { int longitud; const char* datos; uint8_t es_externo; } CadenaSegura;
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

// --- Fibra (definida en runtime/core/concurrency.c; Manual 5 §2.6, F4.1/F4.2) ---
typedef struct Fibra Fibra;

// Nodo de espera de una fibra parqueada en un canal (F4.2: bloqueo fiber-aware,
// Manual 5 §2.6 — la fibra bloqueada se parquea en vez de bloquear el worker).
typedef struct _EsperaFibra {
    struct _EsperaFibra* next;
    Fibra* fibra;        // fibra parqueada
    void* dato;          // dato a enviar (emisor) / dato recibido (receptor)
    int satisfecho;      // 1 = el waker completó la operación
} _EsperaFibra;

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
    struct _EsperaFibra* espera_envio;      // F4.2: fibras bloqueadas enviando (FIFO)
    struct _EsperaFibra* espera_envio_tail;
    struct _EsperaFibra* espera_recepcion;  // F4.2: fibras bloqueadas recibiendo (FIFO)
    struct _EsperaFibra* espera_recepcion_tail;
} CanalConcurrencia;

// --- Primitivas de sincronización (Manual 5 §5, F4.5) ---
// Estructuras del Manual 5 §5.4 + campos aditivos F4.5 para bloqueo
// FIBER-AWARE (la fibra bloqueada se parquea en cola_espera del scheduler en
// vez de bloquear a su worker con pthread; los hilos OS conservan el
// cond_wait — patrón F4.2 de los canales). `mutex` guarda el estado y las
// colas; `cond` es la cond de los hilos OS (aditiva en Mutex: el manual no
// la lista pero un thread no puede esperar sin ella).
typedef struct Mutex {
    pthread_mutex_t mutex;   // guard (Manual 5 §5.4)
    int tomado;              // 1 = propiedad de un bloqueador (F4.5)
    pthread_cond_t cond;     // hilos OS esperando (F4.5 aditivo)
    struct _EsperaFibra* espera;    // F4.5: fibras parqueadas (FIFO)
    struct _EsperaFibra* espera_tail;
} Mutex;

typedef struct Semaforo {
    int valor;               // contador (Manual 5 §5.2)
    pthread_mutex_t mutex;   // guard (Manual 5 §5.4)
    pthread_cond_t cond;     // hilos OS (Manual 5 §5.4)
    struct _EsperaFibra* espera;    // F4.5: fibras parqueadas (FIFO)
    struct _EsperaFibra* espera_tail;
} Semaforo;

typedef struct Barrera {
    int total;               // participantes (Manual 5 §5.3)
    int esperando;           // llegados a la ronda (Manual 5 §5.4)
    int generacion;          // n.º de ronda liberada (F4.5 aditivo)
    pthread_mutex_t mutex;   // guard (Manual 5 §5.4)
    pthread_cond_t cond;     // hilos OS (Manual 5 §5.4)
    struct _EsperaFibra* espera;    // F4.5: fibras parqueadas (FIFO)
    struct _EsperaFibra* espera_tail;
} Barrera;

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

// --- Arena (Manual 4 §2.2: bump allocator, O(1) alloc/liberación) ---
typedef struct Arena {
    uint8_t* inicio;        // Inicio del bloque de memoria
    uint8_t* puntero;       // Puntero actual (próxima posición libre)
    uint8_t* fin;           // Fin del bloque
    struct Arena* padre;    // Arena padre (para anidamiento)
    struct Arena* hijo;           // Primer hijo (para seguimiento/cascada)
    struct Arena* sig_hermano;  // Hermano siguiente en la lista de hijos
    struct Arena* seg_sig;       // Cadena de segmentos por expansión (F9: preserva punteros ya devueltos)
    void* fb_list;               // Lista de bloques fallback (malloc) rastreados para liberar en arena_free (F10)
    size_t tamano;          // Tamaño total (crece con cada expansión de segmento)
    bool es_global;         // Si es la arena global de la aplicación
} Arena;

// Arena API (Manual 4 §2.2)
Arena* arena_crear(size_t tamano_inicial);
Arena* arena_crear_hijo(Arena* padre, size_t tamano_inicial);
void* arena_alloc(Arena* arena, size_t tamano, size_t alineacion);
void arena_free(Arena* arena);
void arena_reset(Arena* arena);

// --- RC/ARC reference counting (Manual 4 §3.2, §4.2) ---
typedef struct RcHeader {
    uint32_t ref_count;          // Conteo de referencias fuertes (no atómico)
    uint32_t weak_count;         // Conteo de referencias débiles vivas
    uint32_t version;            // Generación: incrementada al destruir fuerte (§4.2)
    void* data;                  // Datos del objeto (después del header)
    void (*destructor)(void*);   // Destructor opcional
} RcHeader;

typedef struct ArcHeader {
    uint32_t ref_count;          // Conteo atómico (usamos __atomic)
    uint32_t weak_count;         // Conteo atómico de débiles
    uint32_t version;            // Generación (§4.2)
    void* data;
    void (*destructor)(void*);
} ArcHeader;

// rc<T>: no atómico, para objetos de una sola fibra
void* rc_alloc(size_t tamano, void (*destructor)(void*));
void rc_incrementar(void* ptr);
void rc_decrementar(void* ptr);

// arc<T>: atómico, para objetos entre fibras (canales)
void* arc_alloc(size_t tamano, void (*destructor)(void*));
void arc_incrementar(void* ptr);
void arc_decrementar(void* ptr);

// WeakRef typedef (Manual 4 §4.2)
typedef struct {
    RcHeader* header;
    uint32_t version;   // Versión del objeto (para detección de invalidación)
} WeakRef;

// --- ComponentArena (Manual 4 §6.3) ---
typedef struct ComponentArena {
    Arena* arena;                    // Arena subyacente
    struct ComponentArena* padre;    // Componente padre
    struct ComponentArena* primer_hijo;  // Primer hijo
    struct ComponentArena* siguiente;    // Hermano siguiente
    int num_hijos;
    int ref_count;                   // Cuenta de referencias desde el árbol UI
    bool marcado_para_liberar;
    void (*destructor)(void*);       // Destructor para el componente completo
} ComponentArena;

ComponentArena* comp_arena_crear(ComponentArena* padre, size_t tamano_inicial);
void* comp_alloc(ComponentArena* ca, size_t tamano);
void comp_destroy(ComponentArena* ca);

// --- FFI Marshaling (Manual 4 §7.2) ---
const char* texto_a_c_string(CadenaSegura* texto, Arena* arena);

// --- WeakRef (débil<T>) API (Manual 4 §4.2) ---
WeakRef rc_weak_ref(void* ptr);       // crea débil a un rc<T>
WeakRef arc_weak_ref(void* ptr);      // crea débil a un arc<T>
void* rc_weak_upgrade(WeakRef* w);    // intenta obtener fuerte (nullptr si muerto)
void* arc_weak_upgrade(WeakRef* w);
void rc_weak_release(WeakRef* w);     // libera débil (libera header si fuerte también 0)
void arc_weak_release(WeakRef* w);

// --- SemNodo AST walker (analizador_alcance.syq, Manual 4 §5.2) ---
// Forward declaration del NodoAST canónico (Manual 6 §1.2)
typedef struct NodoAST_ {
    int64_t tipo_nodo;
    int64_t linea;
    int64_t columna;
    int64_t valor_int;
    double valor_dec;
    int64_t ptr_str;
    int64_t len_str;
    int64_t hijo_izq;
    int64_t hijo_der;
    int64_t hermano;
    int64_t ptr_extra;
} NodoAST;

// NodoID canónicos (Manual 2 §7.2)
#define NODO_DECLARACION_TIPO 51
#define NODO_DECLARACION      34
#define NODO_LET              48
#define NODO_FUNCION          2
#define NODO_RETORNAR         5
#define NODO_PROPAGAR         53

// Runtime C para el analizador (externos del .syq)
void _a_set_nodos_base(NodoAST* base);  // set base pointer for walker
void _a_reset_rc_vars(void);
void _a_analizar_bloque(int n);
int _a_get_rc_count(void);

// Read-only SemNodo accessors (tr_*): externos del analizador_alcance.syq
// que permiten al programa SyQuex traversear el SemNodo[] desde C.
// Comparten el mismo g_ast_base que _a_analizar_bloque (Manual 4 §5.2-5.3).
int64_t tr_tipo(int n);
int64_t tr_hizq(int n);
int64_t tr_hder(int n);
int64_t tr_herm(int n);
int64_t tr_vi(int n);

// --- Lista (Manual 3 §5.2, lib/lista.syq) ---
void* _syn_lista_crear(void);
int _syn_lista_longitud(void* l);
void _syn_lista_agregar(void* l, int64_t elemento);
int64_t _syn_lista_obtener(void* l, int indice);
void _syn_lista_establecer(void* l, int indice, int64_t valor);
void _syn_lista_eliminar(void* l, int indice);
void _syn_lista_limpiar(void* l);
void _syn_lista_liberar(void* l);

// --- Mapa (Manual 3 §5.2, lib/mapa.syq) ---
void* _syn_mapa_crear(void);
int _syn_mapa_longitud(void* m);
void _syn_mapa_poner(void* m, const char* clave, int64_t valor);
int64_t _syn_mapa_obtener(void* m, const char* clave);
int _syn_mapa_contiene(void* m, const char* clave);
void _syn_mapa_eliminar(void* m, const char* clave);
void _syn_mapa_limpiar(void* m);
void* _syn_mapa_claves(void* m);
void* _syn_mapa_valores(void* m);
void _syn_mapa_liberar(void* m);

// --- IO extras (lib/io.syq) ---
int _syn_existe(const char* ruta);
void _syn_escribir_a(int fd, const char* contenido);

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

// --- SHA-256 context (compartido: synapse_rt.c + runtime/core/cluster.c) ---
// D-9(d) corte 4: movido aqui para que cluster.c use sha256_* sin duplicar.
#define SHA256_BLOCK_SIZE 64
#define SHA256_DIGEST_SIZE 32

typedef struct {
    uint32_t state[8];
    uint64_t bitcount;
    uint8_t buffer[SHA256_BLOCK_SIZE];
    uint32_t buffer_len;
} SHA256_CTX;

// Funciones sha256_* (definidas en synapse_rt.c, std.cripto)
void sha256_init(SHA256_CTX* ctx);
void sha256_update(SHA256_CTX* ctx, const uint8_t* data, size_t len);
void sha256_final(SHA256_CTX* ctx, uint8_t* digest);

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
void synapse_esperar_fibras(void);
CanalConcurrencia* canal_crear(uint32_t capacidad);
void canal_enviar(CanalConcurrencia* canal, void* paquete);
void* canal_recibir(CanalConcurrencia* canal, bool* cerrado);
void canal_destruir(CanalConcurrencia* canal);

// ============================================================
// Defined in synapse_rt.c:
// ============================================================
Canal abrir(CadenaSegura ruta, CadenaSegura modo);
CadenaSegura leer(Canal canal);
void cerrar_archivo(Canal canal);

#endif /* SYNAPSE_RT_TYPES_H */
