// synapse_rt_memory.c — Memory management module for Synapse runtime
// Extracted from synapse_rt.c: pool allocator, watchdog, buffer helpers
// Compilar: gcc -c synapse_rt_memory.c -o synapse_rt_memory.o -lpthread

#include "synapse_rt_types.h"
#include "librerias/embedded_libs.h"
#include "tweetnacl.h"

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

/* Cache local por hilo (TLS): una cola LIFO por clase slab */
typedef struct { void* ptr; int slab_idx; } CacheSlot;

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

void pool_init(uint32_t total_blocks, uint32_t block_size) {
    pthread_mutex_lock(&_g_pool_mutex);
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
                    return _p;
                }
            }
            /* Llenar cache local con un lote del slab */
            int cached = 0;
            for (int b = 0; b <= LOCAL_CACHE_BATCH; b++) {
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
                    cached++;
                }
            }
            tls_cache[i].count = cached;
            pthread_mutex_unlock(&_g_pool_mutex);
            if (_r) return _r;
            /* Cache no pudo llenarse: malloc directo */
            void* _p = malloc(size);
            if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: pool_alloc slab malloc fallo\n"); exit(1); }
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
    return _p;
}

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
                    uint32_t coff = (uint32_t)((uint8_t*)cp - __atomic_load_n(&g_slab_bases[ci], __ATOMIC_RELAXED));
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
    } else {
        free(ptr);
    }
    pthread_mutex_unlock(&_g_pool_mutex);
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
