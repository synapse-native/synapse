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
// Memory pool with slab allocator
// ============================================================

static const uint32_t SLAB_SIZES[SLAB_COUNT] = {32, 64, 128, 256};

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
    }
    pthread_mutex_unlock(&_g_pool_mutex);
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
            /* Liberar bitmap anterior antes de asignar uno nuevo */
            if (_g_pool.slab_bitmap[slab_idx]) {
                free(_g_pool.slab_bitmap[slab_idx]);
            }
            _g_pool.slab_bitmap[slab_idx] = (uint32_t*)calloc(bm_words, sizeof(uint32_t));
            return 1;
        }
    }
    return 0;
}

void* pool_alloc(size_t size) {
    for (int i = 0; i < SLAB_COUNT; i++) {
        if (size <= SLAB_SIZES[i]) {
            pthread_mutex_lock(&_g_pool_mutex);
            if (_g_pool.slab_block_idx[i] == (uint32_t)-1) {
                if (!_slab_alloc_block(i)) {
                    pthread_mutex_unlock(&_g_pool_mutex);
                    void* _p = malloc(size);
                    if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: pool_alloc slab malloc fallo\n"); exit(1); }
                    return _p;
                }
            }
            uint32_t slots = _g_pool.slab_slots_per_block[i];
            uint32_t bm_words = (slots + 31) / 32;
            for (uint32_t _w = 0; _w < bm_words; _w++) {
                if (_g_pool.slab_bitmap[i][_w] != 0xFFFFFFFF) {
                    uint32_t _bits = ~_g_pool.slab_bitmap[i][_w];
                    uint32_t _b = 0;
                    while (!(_bits & (1u << _b))) { _b++; }
                    uint32_t _slot = _w * 32 + _b;
                    if (_slot < slots) {
                        _g_pool.slab_bitmap[i][_w] |= (1u << _b);
                        pthread_mutex_unlock(&_g_pool_mutex);
                        return _g_pool.slab_base[i] + _slot * SLAB_SIZES[i];
                    }
                }
            }
            if (!_slab_alloc_block(i)) {
                pthread_mutex_unlock(&_g_pool_mutex);
                void* _p = malloc(size);
                if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: pool_alloc slab malloc fallo\n"); exit(1); }
                return _p;
            }
            _g_pool.slab_bitmap[i][0] |= 1u;
            pthread_mutex_unlock(&_g_pool_mutex);
            return _g_pool.slab_base[i];
        }
    }
    /* Fallback: lock mutex antes de acceder a _g_pool (TSan data race fix) */
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
                pthread_mutex_unlock(&_g_pool_mutex);
                return _g_pool.pool_base + _index * _g_pool.block_size;
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
    pthread_mutex_lock(&_g_pool_mutex);
    for (int i = 0; i < SLAB_COUNT; i++) {
        if (_g_pool.slab_base[i] &&
            ptr >= (void*)_g_pool.slab_base[i] &&
            ptr < (void*)(_g_pool.slab_base[i] + TAMANO_BLOQUE)) {
            uint32_t offset = (uint32_t)((uint8_t*)ptr - _g_pool.slab_base[i]);
            uint32_t _slot = offset / SLAB_SIZES[i];
            uint32_t _w = _slot / 32;
            uint32_t _b = _slot % 32;
            _g_pool.slab_bitmap[i][_w] &= ~(1u << _b);
            pthread_mutex_unlock(&_g_pool_mutex);
            return;
        }
    }
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
