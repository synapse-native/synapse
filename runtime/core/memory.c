// synapse_rt_memory.c — Memory management module for Synapse runtime
// Extracted from synapse_rt.c: pool allocator, watchdog, buffer helpers
// Compilar: gcc -c synapse_rt_memory.c -o synapse_rt_memory.o -lpthread

#include "synapse_rt_types.h"
#include "librerias/embedded_libs.h"
#include "axon/tweetnacl.h"

#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #include <windows.h>
#else
  #include <sys/socket.h>
#endif

// ============================================================
// Watchdog memory tracker (SYNAPSE_DEBUG_MEM mode)
// ============================================================

#ifdef SYNAPSE_DEBUG_MEM

static WatchdogEntry watchdog_entries[MAX_WATCHDOG_ENTRIES];
static int watchdog_count = 0;
static pthread_mutex_t watchdog_mutex = PTHREAD_MUTEX_INITIALIZER;

void* watchdog_malloc(size_t size, const char* file, int line) {
    void* ptr = malloc(size);
    if (!ptr) return NULL;
    pthread_mutex_lock(&watchdog_mutex);
    if (watchdog_count < MAX_WATCHDOG_ENTRIES) {
        watchdog_entries[watchdog_count].ptr = ptr;
        watchdog_entries[watchdog_count].size = size;
        watchdog_entries[watchdog_count].file = file;
        watchdog_entries[watchdog_count].line = line;
        watchdog_count++;
    }
    pthread_mutex_unlock(&watchdog_mutex);
    return ptr;
}

void* watchdog_calloc(size_t n, size_t size, const char* file, int line) {
    void* ptr = calloc(n, size);
    if (!ptr) return NULL;
    pthread_mutex_lock(&watchdog_mutex);
    if (watchdog_count < MAX_WATCHDOG_ENTRIES) {
        watchdog_entries[watchdog_count].ptr = ptr;
        watchdog_entries[watchdog_count].size = n * size;
        watchdog_entries[watchdog_count].file = file;
        watchdog_entries[watchdog_count].line = line;
        watchdog_count++;
    }
    pthread_mutex_unlock(&watchdog_mutex);
    return ptr;
}

void watchdog_free(void* ptr, const char* file, int line) {
    if (!ptr) return;
    pthread_mutex_lock(&watchdog_mutex);
    for (int i = 0; i < watchdog_count; i++) {
        if (watchdog_entries[i].ptr == ptr) {
            watchdog_entries[i] = watchdog_entries[watchdog_count - 1];
            watchdog_count--;
            break;
        }
    }
    pthread_mutex_unlock(&watchdog_mutex);
    free(ptr);
}

void watchdog_report(void) {
    pthread_mutex_lock(&watchdog_mutex);
    if (watchdog_count == 0) {
        fprintf(stderr, "0 bytes perdidos\n");
    } else {
        size_t total = 0;
        for (int i = 0; i < watchdog_count; i++) {
            fprintf(stderr, "Fuga detectada: %zu bytes en %s:%d\n",
                    watchdog_entries[i].size,
                    watchdog_entries[i].file,
                    watchdog_entries[i].line);
            total += watchdog_entries[i].size;
        }
        fprintf(stderr, "%zu bytes perdidos en total\n", total);
    }
    pthread_mutex_unlock(&watchdog_mutex);
}

#define malloc(size) watchdog_malloc(size, __FILE__, __LINE__)
#define calloc(n, size) watchdog_calloc(n, size, __FILE__, __LINE__)
#define free(ptr) watchdog_free(ptr, __FILE__, __LINE__)

#else
void watchdog_report(void) {
    // no-op in non-debug mode
}
#endif

// ============================================================
// Memory pool with slab allocator + Thread-Local Cache (M19.B)
// ============================================================

static const uint32_t SLAB_SIZES[SLAB_COUNT] = {32, 64, 128, 256};

/* --- Tamanio del lote de la cache local por hilo ---
 * Cada hilo mantiene una reserva de LOCAL_CACHE_BATCH bloques
 * por clase slab. Cuando la reserva se agota, se adquiere un
 * lote nuevo desde el pool global bajo el mutex. Cuando la
 * reserva esta llena, se vacia al pool global bajo el mutex.
 * En el regimen estacionario (cache caliente), 0 accesos al mutex.
 */
#define LOCAL_CACHE_BATCH 8

/* Cache local por hilo (TLS): una cola LIFO por clase slab
 * 'base' almacena el slab_base original del bloque donde se alojo
 * este slot. Permite al flush computar el offset correcto aun
 * cuando _slab_alloc_block haya reasignado g_slab_bases[] a un
 * nuevo bloque (evita SEGV por offset invalido).
 */
typedef struct { void* ptr; int slab_idx; uint8_t* base; } CacheSlot;

typedef struct {
    CacheSlot slots[LOCAL_CACHE_BATCH];
    int count;
} ThreadCache;

static __thread ThreadCache tls_cache[SLAB_COUNT];

/* Array auxiliar para que pool_free lea slab_base sin TSan false positive.
 * Se escribe UNA VEZ por clase slab via __atomic_store_n (release).
 * Se lee via __atomic_load_n (relaxed) en pool_free — cero races.
 */
static uint8_t* g_slab_bases[SLAB_COUNT];

/* --- Pool global --- */
static volatile MemoryPool _g_pool;
static pthread_mutex_t _g_pool_mutex = PTHREAD_MUTEX_INITIALIZER;

/* --- R10: registro de punteros fuera-del-pool -------------------------
 * pool_alloc usa malloc de escape cuando el pool esta agotado o el tamano
 * excede el bloque. pool_free solo debe llamar free() a esos punteros.
 * Cualquier otro puntero (literal estatico ".rodata", memoria ajena) se
 * IGNORA: free() sobre un literal = 0xC0000374 / SEGV (Manual 4 S2.1:
 * nunca liberar lo que no se asigno via el allocator).
 * Protegido por _g_pool_mutex; solo se toca en el camino lento de
 * pool_free (punteros fuera del pool), nunca en la ruta rapida slab.
 */
static void** _g_extra_ptrs = NULL;
static size_t _g_extra_count = 0;
static size_t _g_extra_cap = 0;

static void _extra_registrar(void* p) {
    if (!p) return;
    pthread_mutex_lock(&_g_pool_mutex);
    if (_g_extra_count == _g_extra_cap) {
        size_t ncap = _g_extra_cap ? _g_extra_cap * 2 : 16;
        void** nptrs = (void**)realloc(_g_extra_ptrs, ncap * sizeof(void*));
        if (!nptrs) {
            /* No registrado: pool_free lo ignorara (leak controlado y
             * documentado; nunca un free() ilegal). */
            pthread_mutex_unlock(&_g_pool_mutex);
            return;
        }
        _g_extra_ptrs = nptrs;
        _g_extra_cap = ncap;
    }
    _g_extra_ptrs[_g_extra_count++] = p;
    pthread_mutex_unlock(&_g_pool_mutex);
}

/* El scan del registro se hace INLINE bajo _g_pool_mutex (ver pool_free):
 * nunca re-tomar el mutex ya tomado (R10 fix 2, deadlock). */

void pool_init(uint32_t total_blocks, uint32_t block_size) {
    pthread_mutex_lock(&_g_pool_mutex);
    /* R10 (hardening): re-inicializacion sin pool_destroy previo no debe
     * conservar entradas stale del registro fuera-del-pool (un puntero
     * ajeno que colisionara con una entrada vieja seria liberado). */
    _g_extra_count = 0;
    _g_pool.total_blocks = total_blocks;
    _g_pool.block_size = block_size;
    _g_pool.pool_base = (uint8_t*)malloc(total_blocks * block_size);
    uint32_t _words = (total_blocks + 31) / 32;
    _g_pool.bitmap = (uint32_t*)calloc(_words, sizeof(uint32_t));
    if (!_g_pool.pool_base || !_g_pool.bitmap) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: pool_init fallo\n");
        pthread_mutex_unlock(&_g_pool_mutex);
        exit(1);
    }
    for (int i = 0; i < SLAB_COUNT; i++) {
        _g_pool.slab_block_idx[i] = (uint32_t)-1;
        _g_pool.slab_base[i] = NULL;
        _g_pool.slab_next_free[i] = 0;
        _g_pool.slab_slots_per_block[i] = SLOTS_PER_BLOCK(SLAB_SIZES[i]);
        g_slab_bases[i] = NULL;
    }
    pthread_mutex_unlock(&_g_pool_mutex);
}

/* --- Asignador interno: asigna un slot RAW desde el slab --- */
static void* _slab_alloc_raw(int slab_idx) {
    uint32_t slots = _g_pool.slab_slots_per_block[slab_idx];
    uint32_t bm_words = (slots + 31) / 32;
    for (uint32_t _w = 0; _w < bm_words; _w++) {
        if (_g_pool.slab_bitmap[slab_idx][_w] != 0xFFFFFFFF) {
            uint32_t _bits = ~_g_pool.slab_bitmap[slab_idx][_w];
            uint32_t _b = 0;
            while (!(_bits & (1u << _b))) { _b++; }
            uint32_t _slot = _w * 32 + _b;
            if (_slot < slots) {
                _g_pool.slab_bitmap[slab_idx][_w] |= (1u << _b);
                return _g_pool.slab_base[slab_idx] + _slot * SLAB_SIZES[slab_idx];
            }
        }
    }
    return NULL;
}

static int _slab_alloc_block(int slab_idx) {
    uint32_t _words = (_g_pool.total_blocks + 31) / 32;
    for (uint32_t _w = 0; _w < _words; _w++) {
        if (_g_pool.bitmap[_w] != 0xFFFFFFFF) {
            uint32_t _bits = ~_g_pool.bitmap[_w];
            uint32_t _b = 0;
            while (!(_bits & (1u << _b))) { _b++; }
            uint32_t _index = _w * 32 + _b;
            if (_index >= _g_pool.total_blocks) break;
            _g_pool.bitmap[_w] |= (1u << _b);
            _g_pool.slab_block_idx[slab_idx] = _index;
            _g_pool.slab_base[slab_idx] = _g_pool.pool_base + _index * _g_pool.block_size;
            _g_pool.slab_next_free[slab_idx] = 0;
            uint32_t slots = _g_pool.slab_slots_per_block[slab_idx];
            uint32_t bm_words = (slots + 31) / 32;
            if (_g_pool.slab_bitmap[slab_idx]) {
                free(_g_pool.slab_bitmap[slab_idx]);
            }
            _g_pool.slab_bitmap[slab_idx] = (uint32_t*)calloc(bm_words, sizeof(uint32_t));
            /* Publicar slab_base via atomic store para pool_free lock-free */
            __atomic_store_n(&g_slab_bases[slab_idx],
                             _g_pool.slab_base[slab_idx], __ATOMIC_RELEASE);
            return 1;
        }
    }
    return 0;
}

void* pool_alloc(size_t size) {
    void* _r = NULL;
    for (int i = 0; i < SLAB_COUNT; i++) {
        if (size <= SLAB_SIZES[i]) {
            /* RUTA RAPIDA: cache local TLS (lock-free) */
            if (tls_cache[i].count > 0) {
                return tls_cache[i].slots[--tls_cache[i].count].ptr;
            }
            /* MISS: adquirir lote desde el pool global bajo mutex */
            pthread_mutex_lock(&_g_pool_mutex);
            if (_g_pool.slab_block_idx[i] == (uint32_t)-1) {
                if (!_slab_alloc_block(i)) {
                    pthread_mutex_unlock(&_g_pool_mutex);
                    void* _p = malloc(size);
                    if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: pool_alloc slab malloc fallo\n"); exit(1); }
                    _extra_registrar(_p);
                    return _p;
                }
            }
            /* Llenar cache local con (LOCAL_CACHE_BATCH-1) slots libres,
             * dejando 1 slot disponible para el pool_free inmediato.
             * Sin esto, la cache se llena (count=LOCAL_CACHE_BATCH) y
             * el primer free fuerza flush+mutex: 0 hits en regimen estacionario.
             */
            int cached = 0;
            for (int b = 0; b < LOCAL_CACHE_BATCH; b++) {
                void* blk = _slab_alloc_raw(i);
                if (!blk) {
                    if (!_slab_alloc_block(i)) break;
                    blk = _slab_alloc_raw(i);
                    if (!blk) break;
                }
                if (b == 0) {
                    _r = blk;  /* primer bloque: retornar */
                } else {
                    tls_cache[i].slots[cached].ptr = blk;
                    tls_cache[i].slots[cached].slab_idx = i;
                    tls_cache[i].slots[cached].base = (uint8_t*)_g_pool.slab_base[i];
                    cached++;
                }
            }
            tls_cache[i].count = cached;
            pthread_mutex_unlock(&_g_pool_mutex);
            if (_r) return _r;
            /* Cache no pudo llenarse: malloc directo */
            void* _p = malloc(size);
            if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: pool_alloc slab malloc fallo\n"); exit(1); }
            _extra_registrar(_p);
            return _p;
        }
    }
    /* Fallback: bloque grande desde el pool */
    pthread_mutex_lock(&_g_pool_mutex);
    if (size <= _g_pool.block_size) {
        uint32_t _words = (_g_pool.total_blocks + 31) / 32;
        for (uint32_t _w = 0; _w < _words; _w++) {
            if (_g_pool.bitmap[_w] != 0xFFFFFFFF) {
                uint32_t _bits = ~_g_pool.bitmap[_w];
                uint32_t _b = 0;
                while (!(_bits & (1u << _b))) { _b++; }
                uint32_t _index = _w * 32 + _b;
                if (_index >= _g_pool.total_blocks) break;
                _g_pool.bitmap[_w] |= (1u << _b);
                _r = _g_pool.pool_base + _index * _g_pool.block_size;
                pthread_mutex_unlock(&_g_pool_mutex);
                return _r;
            }
        }
    }
    pthread_mutex_unlock(&_g_pool_mutex);
    void* _p = malloc(size);
    if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: pool_alloc malloc fallo\n"); exit(1); }
    _extra_registrar(_p);
    return _p;
}

/* CONTRATO DE OWNERSHIP (R10, Manual 4 S2.1): pool_free solo es valido para
 * punteros devueltos por pool_alloc (slab / bloque grande del pool / malloc de
 * escape registrado). Literales estaticos (.rodata) y memoria ajena se IGNORAN
 * (no-op): nunca liberar lo que no se asigno via el allocator. */
void pool_free(void* ptr) {
    if (!ptr) return;
    /* Determinar clase slab via atomic reads de g_slab_bases (lock-free) */
    for (int i = 0; i < SLAB_COUNT; i++) {
        uint8_t* base = (uint8_t*)__atomic_load_n(&g_slab_bases[i], __ATOMIC_RELAXED);
        if (base && ptr >= (void*)base && ptr < (void*)(base + TAMANO_BLOQUE)) {
            /* RUTA RAPIDA: retornar a cache local TLS (lock-free) */
            if (tls_cache[i].count < LOCAL_CACHE_BATCH) {
                tls_cache[i].slots[tls_cache[i].count].ptr = ptr;
                tls_cache[i].slots[tls_cache[i].count].slab_idx = i;
                tls_cache[i].slots[tls_cache[i].count].base = base;
                tls_cache[i].count++;
                return;
            }
            /* Cache llena: vaciar al pool global bajo mutex */
            pthread_mutex_lock(&_g_pool_mutex);
            uint32_t offset = (uint32_t)((uint8_t*)ptr - base);
            uint32_t _slot = offset / SLAB_SIZES[i];
            uint32_t _w = _slot / 32;
            uint32_t _b = _slot % 32;
            _g_pool.slab_bitmap[i][_w] &= ~(1u << _b);
            /* Vaciar toda la cache al pool */
            for (int c = 0; c < tls_cache[i].count; c++) {
                void* cp = tls_cache[i].slots[c].ptr;
                int ci  = tls_cache[i].slots[c].slab_idx;
                if (ci >= 0 && ci < SLAB_COUNT) {
                    uint8_t* cbase = tls_cache[i].slots[c].base;
                    uint32_t coff = (uint32_t)((uint8_t*)cp - cbase);
                    uint32_t cs = coff / SLAB_SIZES[ci];
                    uint32_t cw = cs / 32;
                    uint32_t cb = cs % 32;
                    _g_pool.slab_bitmap[ci][cw] &= ~(1u << cb);
                }
            }
            tls_cache[i].count = 0;
            pthread_mutex_unlock(&_g_pool_mutex);
            return;
        }
    }
    /* No es slab: verificar si es bloque grande del pool */
    pthread_mutex_lock(&_g_pool_mutex);
    if (ptr >= (void*)_g_pool.pool_base &&
        ptr < (void*)(_g_pool.pool_base + _g_pool.total_blocks * _g_pool.block_size)) {
        uint32_t _index = (uint32_t)((uint8_t*)ptr - _g_pool.pool_base) / _g_pool.block_size;
        uint32_t _w = _index / 32;
        uint32_t _b = _index % 32;
        _g_pool.bitmap[_w] &= ~(1u << _b);
        pthread_mutex_unlock(&_g_pool_mutex);
        return;
    }
    /* Puntero fuera del pool: solo liberar si pool_alloc lo asigno via
     * malloc de escape (registrado). Scan INLINE bajo el mutex tomado
     * (R10 fix 2: _extra_consumir re-tomaba el mutex -> deadlock).
     * Literales estaticos (.rodata) / punteros ajenos: no-op (Manual 4
     * S2.1: nunca liberar lo que no se asigno via el allocator). */
    {
        int es_nuestro = 0;
        for (size_t i = 0; i < _g_extra_count; i++) {
            if (_g_extra_ptrs[i] == ptr) {
                _g_extra_ptrs[i] = _g_extra_ptrs[_g_extra_count - 1];
                _g_extra_count--;
                es_nuestro = 1;
                break;
            }
        }
        pthread_mutex_unlock(&_g_pool_mutex);
        if (es_nuestro) free(ptr);
    }
}

void pool_destroy(void) {
    pthread_mutex_lock(&_g_pool_mutex);
    for (int i = 0; i < SLAB_COUNT; i++) {
        if (_g_pool.slab_bitmap[i]) {
            free(_g_pool.slab_bitmap[i]);
            _g_pool.slab_bitmap[i] = NULL;
        }
        _g_pool.slab_block_idx[i] = (uint32_t)-1;
        _g_pool.slab_base[i] = NULL;
    }
    if (_g_pool.pool_base) {
        free(_g_pool.pool_base);
        _g_pool.pool_base = NULL;
    }
    if (_g_pool.bitmap) {
        free(_g_pool.bitmap);
        _g_pool.bitmap = NULL;
    }
    if (_g_extra_ptrs) {
        free(_g_extra_ptrs);
        _g_extra_ptrs = NULL;
    }
    _g_extra_count = 0;
    _g_extra_cap = 0;
    pthread_mutex_unlock(&_g_pool_mutex);
}

float* _pool_malloc(size_t tamano) {
    float* _p = (float*)pool_alloc(tamano);
    if (!_p) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: pool_alloc fallo\n");
        exit(1);
    }
    return _p;
}

// ============================================================
// Buffer helpers for std.net FFI (receive path)
// ============================================================

void* _syn_buffer_alloc(int tamano) {
    return pool_alloc((size_t)tamano);
}

void _syn_buffer_free(void* ptr) {
    if (ptr) pool_free(ptr);
}

CadenaSegura _syn_recibir_como_texto(int fd, int tamano) {
    char* buf = (char*)pool_alloc((size_t)(tamano + 1));
    int n = (int)recv(fd, buf, (size_t)tamano, 0);
    if (n <= 0) {
        pool_free(buf);
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
    buf[n] = '\0';
    return (CadenaSegura){ .longitud = n, .datos = buf };
}

void _syn_texto_liberar(CadenaSegura s) {
    if (s.datos) pool_free((void*)s.datos);
}

// ============================================================
// Arena allocator (Manual 4 §2: Arenas por ámbito)
// bump allocator: O(1) alloc, O(1) lib (bloque entero), 0 fragmentación.
// Anidamiento padre-hijo: liberar padre libera hijos en cascada (§2.4).
// Expansión (§2.3): se encadena un NUEVO segmento SIN mover el bloque
//   actual, de modo que los punteros ya devueltos por arena_alloc siguen
//   válidos (F9). El fallback a heap de arenas no globales se rastrea y
//   libera en arena_free (F10: 0 fugas).
// ============================================================

// Nodo de la lista de bloques fallback (malloc) rastreados para liberar en
// arena_free (F10). Interno al runtime.
typedef struct ArenaFallback {
    void* ptr;
    struct ArenaFallback* sig;
} ArenaFallback;

static void arena_expandir(Arena* a, size_t tamano_extra) {
    // F9: crear un NUEVO segmento encadenado; NO reubicar el bloque actual
    // (los punteros ya devueltos por arena_alloc quedarían colgantes).
    size_t nuevo = (a->tamano > tamano_extra) ? a->tamano * 2
                                              : tamano_extra * 2 + 4096;
    uint8_t* bloque = (uint8_t*)malloc(nuevo);
    if (!bloque) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: arena_expandir malloc fallo\n");
        exit(1);
    }
    Arena* seg = (Arena*)malloc(sizeof(Arena));
    if (!seg) {
        free(bloque);
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: arena_expandir malloc fallo\n");
        exit(1);
    }
    seg->inicio = bloque;
    seg->puntero = bloque;
    seg->fin = bloque + nuevo;
    seg->tamano = nuevo;
    seg->padre = NULL;
    seg->hijo = NULL;
    seg->sig_hermano = NULL;
    seg->seg_sig = NULL;
    seg->fb_list = NULL;
    seg->es_global = false;
    // Encadenar al final de la cadena de segmentos.
    Arena* cur = a;
    while (cur->seg_sig) cur = cur->seg_sig;
    cur->seg_sig = seg;
    // Tamaño reportado crece (semántica de "tamaño total" del Manual §2.2).
    a->tamano += nuevo;
}

Arena* arena_crear(size_t tamano_inicial) {
    if (tamano_inicial < 4096) tamano_inicial = 4096;

    Arena* a = (Arena*)malloc(sizeof(Arena));
    if (!a) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: arena_crear malloc fallo\n");
        return NULL;
    }

    a->inicio = (uint8_t*)malloc(tamano_inicial);
    if (!a->inicio) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: arena_crear bloque fallo\n");
        free(a);
        return NULL;
    }

    a->puntero = a->inicio;
    a->fin = a->inicio + tamano_inicial;
    a->padre = NULL;
    a->hijo = NULL;
    a->sig_hermano = NULL;
    a->seg_sig = NULL;
    a->fb_list = NULL;
    a->tamano = tamano_inicial;
    a->es_global = false;
    return a;
}

Arena* arena_crear_hijo(Arena* padre, size_t tamano_inicial) {
    if (!padre) return arena_crear(tamano_inicial);

    Arena* a = arena_crear(tamano_inicial);
    if (!a) return NULL;

    a->padre = padre;
    a->sig_hermano = padre->hijo;
    padre->hijo = a;
    return a;
}

void* arena_alloc(Arena* arena, size_t tamano, size_t alineacion) {
    if (!arena) return NULL;
    if (alineacion == 0) alineacion = 1;
    while (1) {
        // Buscar un segmento (cadena bump) con espacio; el último es el actual.
        Arena* seg = arena;
        while (1) {
            uintptr_t addr = (uintptr_t)seg->puntero;
            uintptr_t aligned = (addr + alineacion - 1) & ~((uintptr_t)alineacion - 1);
            size_t offset = aligned - addr;
            if (seg->puntero + offset + tamano <= seg->fin) {
                seg->puntero += offset + tamano;
                return (void*)aligned;
            }
            if (seg->seg_sig) { seg = seg->seg_sig; continue; }
            break;
        }
        if (arena->es_global) {
            // F9: expandir encadenando un nuevo segmento (punteros previos válidos).
            arena_expandir(arena, tamano);
            continue;
        }
        // F10: fallback a heap para arenas no globales. El bloque se rastrea en
        // fb_list para liberarlo en arena_free (0 fugas).
        void* p = malloc(tamano);
        if (!p) {
            fprintf(stderr, "ESCAPA_DEL_ALCANCE: arena_alloc fallback malloc fallo\n");
            return NULL;
        }
        ArenaFallback* fb = (ArenaFallback*)malloc(sizeof(ArenaFallback));
        if (!fb) { free(p); return NULL; }
        fb->ptr = p;
        fb->sig = (ArenaFallback*)arena->fb_list;
        arena->fb_list = fb;
        return p;
    }
}

void arena_free(Arena* arena) {
    if (!arena) return;

    // Cascada de hijos (jerarquía, §2.4)
    Arena* child = arena->hijo;
    while (child) {
        Arena* next = child->sig_hermano;
        arena_free(child);
        child = next;
    }

    // F10: liberar bloques fallback rastreados (0 fugas)
    ArenaFallback* fb = (ArenaFallback*)arena->fb_list;
    while (fb) {
        ArenaFallback* nxt = fb->sig;
        free(fb->ptr);
        free(fb);
        fb = nxt;
    }

    // F9: liberar cadena de segmentos (cada uno con su propio bloque)
    Arena* seg = arena->seg_sig;
    while (seg) {
        Arena* nxt = seg->seg_sig;
        free(seg->inicio);
        free(seg);
        seg = nxt;
    }

    if (arena->inicio) free(arena->inicio);
    free(arena);
}

void arena_reset(Arena* arena) {
    if (!arena || !arena->inicio) return;
    // Reset de TODOS los segmentos (F9): cada uno vuelve a su inicio.
    Arena* seg = arena;
    while (seg) {
        if (seg->inicio) seg->puntero = seg->inicio;
        seg = seg->seg_sig;
    }
}

// ============================================================
// Reference Counting (Manual 4 §3.2)
// rc<T>: no atómico — para objetos de una sola fibra.
// arc<T>: atómico — para objetos compartidos entre fibras (canales).
// El layout en memoria es: [Header][data...]. El usuario recibe (void*)data
// y el header está justo antes. rc_decrementar/arc_decrementar hacen
// pointer-math para recuperar el header.
// ============================================================

void* rc_alloc(size_t tamano, void (*destructor)(void*)) {
    size_t total = sizeof(RcHeader) + tamano;
    RcHeader* h = (RcHeader*)malloc(total);
    if (!h) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: rc_alloc malloc fallo\n");
        return NULL;
    }
    h->ref_count = 1;
    h->weak_count = 0;
    h->version = 0;
    h->data = (uint8_t*)h + sizeof(RcHeader);
    h->destructor = destructor;
    return h->data;
}

void rc_incrementar(void* ptr) {
    if (!ptr) return;
    RcHeader* h = (RcHeader*)((uint8_t*)ptr - sizeof(RcHeader));
    h->ref_count++;
}

void rc_decrementar(void* ptr) {
    if (!ptr) return;
    RcHeader* h = (RcHeader*)((uint8_t*)ptr - sizeof(RcHeader));
    h->ref_count--;
    if (h->ref_count == 0) {
        if (h->destructor) h->destructor(ptr);
        if (h->weak_count > 0) {
            h->version++;
            return;
        }
        free(h);
    }
}

void* arc_alloc(size_t tamano, void (*destructor)(void*)) {
    size_t total = sizeof(ArcHeader) + tamano;
    ArcHeader* h = (ArcHeader*)malloc(total);
    if (!h) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: arc_alloc malloc fallo\n");
        return NULL;
    }
    h->ref_count = 1;
    h->weak_count = 0;
    h->version = 0;
    h->data = (uint8_t*)h + sizeof(ArcHeader);
    h->destructor = destructor;
    return h->data;
}

void arc_incrementar(void* ptr) {
    if (!ptr) return;
    ArcHeader* h = (ArcHeader*)((uint8_t*)ptr - sizeof(ArcHeader));
    __atomic_fetch_add(&h->ref_count, 1, __ATOMIC_RELAXED);
}

void arc_decrementar(void* ptr) {
    if (!ptr) return;
    ArcHeader* h = (ArcHeader*)((uint8_t*)ptr - sizeof(ArcHeader));
    uint32_t prev = __atomic_fetch_sub(&h->ref_count, 1, __ATOMIC_ACQ_REL);
    if (prev == 1) {
        if (h->destructor) h->destructor(ptr);
        if (h->weak_count > 0) {
            // Manual 4 §4.2: la débil se invalida al destruir el fuerte.
            // version es compartido con lecturas __atomic_load_n en
            // arc_weak_ref/arc_weak_upgrade (F7): el incremento debe ser
            // una RMW atómica para no competir con ellas.
            __atomic_fetch_add(&h->version, 1, __ATOMIC_RELEASE);
            return;
        }
        free(h);
    }
}

// ============================================================
// WeakRef (débil<T>) — Manual 4 §4.2
// No incrementa ref_count. Se invalida al destruir el fuerte.
// El header sobrevive hasta que weak_count también llega a 0.
// ============================================================

WeakRef rc_weak_ref(void* ptr) {
    WeakRef w = { .header = NULL, .version = 0 };
    if (!ptr) return w;
    RcHeader* h = (RcHeader*)((uint8_t*)ptr - sizeof(RcHeader));
    h->weak_count++;
    w.header = h;
    w.version = h->version;
    return w;
}

WeakRef arc_weak_ref(void* ptr) {
    WeakRef w = { .header = NULL, .version = 0 };
    if (!ptr) return w;
    ArcHeader* h = (ArcHeader*)((uint8_t*)ptr - sizeof(ArcHeader));
    __atomic_fetch_add(&h->weak_count, 1, __ATOMIC_RELAXED);
    w.header = (RcHeader*)h;
    w.version = __atomic_load_n(&h->version, __ATOMIC_ACQUIRE);
    return w;
}

void* rc_weak_upgrade(WeakRef* w) {
    if (!w || !w->header) return NULL;
    if (w->header->version != w->version) return NULL;
    if (w->header->ref_count == 0) return NULL;
    w->header->ref_count++;
    return w->header->data;
}

void* arc_weak_upgrade(WeakRef* w) {
    if (!w || !w->header) return NULL;
    ArcHeader* h = (ArcHeader*)w->header;
    uint32_t ver = __atomic_load_n(&h->version, __ATOMIC_ACQUIRE);
    if (ver != w->version) return NULL;
    // Manual 4 §4.2 / F8: el camino arc entre fibras es concurrente. La
    // lectura de ref_count seguida de un fetch_add separado era un TOCTOU
    // (UAF): otro hilo podía llevar ref_count a 0 y free(h) entre medias.
    // CAS loop: solo promovemos la débil a fuerte si ref_count > 0, en una
    // sola operación atómica. Si ref_count llega a 0 el objeto ya murió.
    uint32_t rc = __atomic_load_n(&h->ref_count, __ATOMIC_ACQUIRE);
    while (rc > 0) {
        if (__atomic_compare_exchange_n(&h->ref_count, &rc, rc + 1, false,
                __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE)) {
            return h->data;
        }
        // rc se reescribió con el valor actual; reintentar mientras viva.
    }
    return NULL;
}

void rc_weak_release(WeakRef* w) {
    if (!w || !w->header) return;
    RcHeader* h = w->header;
    h->weak_count--;
    if (h->ref_count == 0 && h->weak_count == 0) {
        free(h);
    }
    w->header = NULL;
    w->version = 0;
}

void arc_weak_release(WeakRef* w) {
    if (!w || !w->header) return;
    ArcHeader* h = (ArcHeader*)w->header;
    uint32_t wc = __atomic_fetch_sub(&h->weak_count, 1, __ATOMIC_ACQ_REL);
    if (wc == 1) {
        if (__atomic_load_n(&h->ref_count, __ATOMIC_ACQUIRE) == 0) {
            free(h);
        }
    }
    w->header = NULL;
    w->version = 0;
}

// ============================================================
// SemNodo AST walker for analizador_alcance.syq (Manual 4 §5.2)
// ============================================================

static NodoAST* g_ast_base = NULL;
static int g_rc_count = 0;

void _a_set_nodos_base(NodoAST* base) {
    g_ast_base = base;
}

void _a_reset_rc_vars(void) {
    g_rc_count = 0;
}

void _a_analizar_bloque(int n) {
    if (!g_ast_base || n < 0) return;
    NodoAST* nodo = &g_ast_base[n];

    // NODO_DECLARACION (34) / NODO_LET (48): variable con ownership
    // valor_int flags: bit0=rc, bit1=arc, bit2=débil
    if (nodo->tipo_nodo == NODO_DECLARACION || nodo->tipo_nodo == NODO_LET) {
        int flags = (int)nodo->valor_int;
        // rc (bit0) o arc (bit1) pero NO débil (bit2)
        if ((flags & 3) > 0 && (flags & 4) == 0) {
            g_rc_count++;
        }
    }

    // Recursión en hijos
    _a_analizar_bloque((int)nodo->hijo_izq);
    _a_analizar_bloque((int)nodo->hijo_der);
    _a_analizar_bloque((int)nodo->hermano);
}

int _a_get_rc_count(void) {
    return g_rc_count;
}
