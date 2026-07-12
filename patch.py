import re

with open("synapse_rt.c", "r") as f:
    content = f.read()

watchdog_code = """
#ifdef SYNAPSE_DEBUG_MEM
#define MAX_WATCHDOG_ENTRIES 100000

typedef struct {
    void* ptr;
    size_t size;
    const char* file;
    int line;
} WatchdogEntry;

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

void watchdog_report() {
    pthread_mutex_lock(&watchdog_mutex);
    if (watchdog_count == 0) {
        fprintf(stderr, "0 bytes perdidos\\n");
    } else {
        size_t total = 0;
        for (int i = 0; i < watchdog_count; i++) {
            fprintf(stderr, "Fuga detectada: %zu bytes en %s:%d\\n", watchdog_entries[i].size, watchdog_entries[i].file, watchdog_entries[i].line);
            total += watchdog_entries[i].size;
        }
        fprintf(stderr, "%zu bytes perdidos en total\\n", total);
    }
    pthread_mutex_unlock(&watchdog_mutex);
}

#define malloc(size) watchdog_malloc(size, __FILE__, __LINE__)
#define calloc(n, size) watchdog_calloc(n, size, __FILE__, __LINE__)
#define free(ptr) watchdog_free(ptr, __FILE__, __LINE__)

#else
#define watchdog_report()
#endif

"""

# Insert watchdog code after includes
includes_end = content.find('#include "librerias/embedded_libs.h"') + len('#include "librerias/embedded_libs.h"')
content = content[:includes_end] + "\n\n" + watchdog_code + content[includes_end:]

# Also free the pool at the end to prevent it from being reported as a leak
esperar_hilos_str = """void synapse_esperar_hilos(void) {
    pthread_mutex_lock(&hilo_mutex);
    while (hilos_activos > 0) {
        pthread_cond_wait(&hilo_cond, &hilo_mutex);
    }
    pthread_mutex_unlock(&hilo_mutex);
}"""

esperar_hilos_repl = """void synapse_esperar_hilos(void) {
    pthread_mutex_lock(&hilo_mutex);
    while (hilos_activos > 0) {
        pthread_cond_wait(&hilo_cond, &hilo_mutex);
    }
    pthread_mutex_unlock(&hilo_mutex);

#ifdef SYNAPSE_DEBUG_MEM
    if (_g_pool.pool_base) {
        free(_g_pool.pool_base);
        _g_pool.pool_base = NULL;
    }
    if (_g_pool.bitmap) {
        free(_g_pool.bitmap);
        _g_pool.bitmap = NULL;
    }
#endif

    watchdog_report();
}"""

content = content.replace(esperar_hilos_str, esperar_hilos_repl)

with open("synapse_rt.c", "w") as f:
    f.write(content)
