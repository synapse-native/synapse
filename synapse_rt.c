// synapse_rt.c — Runtime precompilado para Synapse
// Compilar una sola vez: gcc -c synapse_rt.c -o synapse_rt.o
// Linkear: gcc programa.c synapse_rt.o -o programa -lpthread

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <pthread.h>
#include <time.h>
#include "librerias/embedded_libs.h"

#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #include <windows.h>
#else
  #include <sys/socket.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
  #include <unistd.h>
#endif


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
        fprintf(stderr, "0 bytes perdidos\n");
    } else {
        size_t total = 0;
        for (int i = 0; i < watchdog_count; i++) {
            fprintf(stderr, "Fuga detectada: %zu bytes en %s:%d\n", watchdog_entries[i].size, watchdog_entries[i].file, watchdog_entries[i].line);
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
#define watchdog_report()
#endif



// --- Type definitions (deben coincidir exactamente con las emitidas por el generador) ---
typedef struct { int longitud; const char* datos; } CadenaSegura;
typedef struct { uint32_t filas; uint32_t columnas; float* datos; } Tensor;
typedef struct { FILE* stream; int es_valido; int es_virtual; const char* virtual_data; int virtual_len; } Canal;

// --- Resultado<T, E> (Tagged Union para manejo de errores de canal) ---
typedef struct {
    int es_ok; // 1 = ok, 0 = error
    union {
        void* ok_valor;
        const char* err_mensaje;
    } datos;
} Resultado_T;

// --- CanalConcurrencia (Buffer circular thread-safe para canales) ---
typedef struct {
    void** buffer;
    uint32_t capacidad;
    uint32_t cabeza;  // índice de escritura
    uint32_t cola;    // índice de lectura
    uint32_t contador; // número de elementos en el buffer
    pthread_mutex_t mutex;
    pthread_cond_t no_vacio;  // señal para receptores
    pthread_cond_t no_lleno;  // señal para emisores
} CanalConcurrencia;

// --- Memory pool ---
#define POOL_BLOQUES 64
#define TAMANO_BLOQUE 4096

typedef struct {
    uint8_t* pool_base;
    uint32_t* bitmap;
    uint32_t total_blocks;
    uint32_t block_size;
} MemoryPool;

static MemoryPool _g_pool;
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
    pthread_mutex_unlock(&_g_pool_mutex);
}

void* pool_alloc() {
    pthread_mutex_lock(&_g_pool_mutex);
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
    pthread_mutex_unlock(&_g_pool_mutex);
    return NULL;
}

void pool_free(void* ptr) {
    pthread_mutex_lock(&_g_pool_mutex);
    if (ptr >= (void*)_g_pool.pool_base
        && ptr < (void*)(_g_pool.pool_base + _g_pool.total_blocks * _g_pool.block_size)) {
        uint32_t _index = (uint32_t)((uint8_t*)ptr - _g_pool.pool_base) / _g_pool.block_size;
        uint32_t _w = _index / 32;
        uint32_t _b = _index % 32;
        _g_pool.bitmap[_w] &= ~(1u << _b);
    } else {
        free(ptr);
    }
    pthread_mutex_unlock(&_g_pool_mutex);
}

static inline float* _pool_malloc(size_t tamano) {
    if (tamano <= TAMANO_BLOQUE) {
        float* _p = (float*)pool_alloc();
        if (_p) return _p;
        fprintf(stderr, "ADVERTENCIA: pool agotado, usando malloc\n");
    }
    float* _p = (float*)malloc(tamano);
    if (!_p) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo\n");
        exit(1);
    }
    return _p;
}

// --- Thread-safe I/O ---
pthread_mutex_t io_mutex = PTHREAD_MUTEX_INITIALIZER;

void escribir(CadenaSegura contenido) {
    pthread_mutex_lock(&io_mutex);
    fwrite(contenido.datos, 1, contenido.longitud, stdout);
    fflush(stdout);
    pthread_mutex_unlock(&io_mutex);
}

void escribir_linea(CadenaSegura contenido) {
    pthread_mutex_lock(&io_mutex);
    fwrite(contenido.datos, 1, contenido.longitud, stdout);
    fwrite("\n", 1, 1, stdout);
    fflush(stdout);
    pthread_mutex_unlock(&io_mutex);
}

CadenaSegura leer_linea() {
    static char _buf[4096];
    if (fgets(_buf, 4096, stdin)) {
        int _len = (int)strlen(_buf);
        if (_len > 0 && _buf[_len - 1] == '\n') { _buf[_len - 1] = '\0'; _len--; }
        char* _dup = (char*)malloc(_len + 1);
        if (!_dup) { return (CadenaSegura){ .longitud = 0, .datos = "" }; }
        memcpy(_dup, _buf, _len + 1);
        return (CadenaSegura){ .longitud = _len, .datos = _dup };
    }
    return (CadenaSegura){ .longitud = 0, .datos = "" };
}

Canal abrir(CadenaSegura ruta, CadenaSegura modo) {
    Canal _c = {0};
    _c.es_virtual = 0;
    if (strcmp(ruta.datos, "librerias/compiler/ast_nodes.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_AST; _c.virtual_len = (int)strlen(LIB_AST); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "librerias/compiler/lexer.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_LEXER; _c.virtual_len = (int)strlen(LIB_LEXER); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "librerias/compiler/parser.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_PARSER; _c.virtual_len = (int)strlen(LIB_PARSER); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "librerias/compiler/generator.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_GENERATOR; _c.virtual_len = (int)strlen(LIB_GENERATOR); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "librerias/std/io.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_IO; _c.virtual_len = (int)strlen(LIB_IO); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "librerias/std/mem.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_MEM; _c.virtual_len = (int)strlen(LIB_MEM); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "librerias/std/math.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_MATH; _c.virtual_len = (int)strlen(LIB_MATH); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "librerias/std/fs.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_FS; _c.virtual_len = (int)strlen(LIB_FS); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "librerias/std/sys.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_SYS; _c.virtual_len = (int)strlen(LIB_SYS); _c.es_valido = 1; return _c; }
    _c.stream = fopen(ruta.datos, modo.datos);
    _c.es_valido = (_c.stream != NULL) ? 1 : 0;
    if (!_c.es_valido) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: fopen fallo en abrir()\n");
    }
    return _c;
}

CadenaSegura leer(Canal canal) {
    if (!canal.es_valido) { return (CadenaSegura){ .longitud = 0, .datos = "" }; }
    if (canal.es_virtual) {
        char* _buf = (char*)malloc(canal.virtual_len + 1);
        if (!_buf) { return (CadenaSegura){ .longitud = 0, .datos = "" }; }
        memcpy(_buf, canal.virtual_data, canal.virtual_len);
        _buf[canal.virtual_len] = '\0';
        return (CadenaSegura){ .longitud = canal.virtual_len, .datos = (const char*)_buf };
    }
    fseek(canal.stream, 0, SEEK_END);
    long _tam = ftell(canal.stream);
    rewind(canal.stream);
    char* _buf = (char*)malloc(_tam + 1);
    if (!_buf) { return (CadenaSegura){ .longitud = 0, .datos = "" }; }
    size_t _leido = fread(_buf, 1, _tam, canal.stream);
    _buf[_leido] = '\0';
    return (CadenaSegura){ .longitud = (int)_leido, .datos = (const char*)_buf };
}

void cerrar(Canal canal) {
    if (canal.es_virtual) { return; }
    if (canal.stream) {
        fclose(canal.stream);
    }
}

// --- std.math ---
Tensor crear_tensor(int filas, int columnas) {
    Tensor r;
    r.filas = filas;
    r.columnas = columnas;
    r.datos = _pool_malloc(filas * columnas * sizeof(float));
    memset(r.datos, 0, filas * columnas * sizeof(float));
    return r;
}

Tensor suma_tensor(Tensor a, Tensor b) {
    if (a.filas != b.filas || a.columnas != b.columnas) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: dimensiones incompatibles en suma_tensor()\n");
        return (Tensor){ .filas = 0, .columnas = 0, .datos = NULL };
    }
    Tensor r;
    r.filas = a.filas;
    r.columnas = a.columnas;
    r.datos = _pool_malloc(r.filas * r.columnas * sizeof(float));
    for (int _i = 0; _i < r.filas * r.columnas; _i++) {
        r.datos[_i] = a.datos[_i] + b.datos[_i];
    }
    pool_free(a.datos);
    pool_free(b.datos);
    return r;
}

Tensor producto_punto(Tensor a, Tensor b) {
    if (a.columnas != b.filas) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: dimensiones incompatibles en producto_punto()\n");
        return (Tensor){ .filas = 0, .columnas = 0, .datos = NULL };
    }
    Tensor r;
    r.filas = a.filas;
    r.columnas = b.columnas;
    r.datos = (float*)calloc(r.filas * r.columnas, sizeof(float));
    for (int _i = 0; _i < r.filas; _i++) {
        for (int _j = 0; _j < r.columnas; _j++) {
            float _sum = 0;
            for (int _k = 0; _k < a.columnas; _k++) {
                _sum += a.datos[_i * a.columnas + _k] * b.datos[_k * b.columnas + _j];
            }
            r.datos[_i * r.columnas + _j] = _sum;
        }
    }
    pool_free(a.datos);
    pool_free(b.datos);
    return r;
}

Tensor relu(Tensor a) {
    Tensor r;
    r.filas = a.filas;
    r.columnas = a.columnas;
    r.datos = _pool_malloc(a.filas * a.columnas * sizeof(float));
    for (int _i = 0; _i < a.filas * a.columnas; _i++) {
        r.datos[_i] = (a.datos[_i] > 0) ? a.datos[_i] : 0.0f;
    }
    pool_free(a.datos);
    return r;
}

// --- std.math (alias) ---
Tensor suma(Tensor a, Tensor b) {
    return suma_tensor(a, b);
}

Tensor producto(Tensor a, Tensor b) {
    return producto_punto(a, b);
}

// --- std.mem ---
Tensor reserva(int tamano) {
    Tensor _bloque;
    _bloque.filas = tamano;
    _bloque.columnas = 1;
    _bloque.datos = _pool_malloc(tamano);
    return _bloque;
}

void libera(Tensor bloque) {
    if (bloque.datos) {
        pool_free(bloque.datos);
    }
}

// --- std.conv ---
int texto_a_entero(CadenaSegura str) {
    if (str.datos == NULL || str.longitud == 0) return 0;
    return (int)strtol(str.datos, NULL, 10);
}

float texto_a_decimal(CadenaSegura str) {
    if (str.datos == NULL || str.longitud == 0) return 0.0f;
    return (float)strtod(str.datos, NULL);
}

CadenaSegura decimal_a_texto(float n) {
    char buf[64];
    int len = snprintf(buf, sizeof(buf), "%f", n);
    char* data = (char*)malloc(len + 1);
    if (!data) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en decimal_a_texto\n"); exit(1); }
    memcpy(data, buf, len + 1);
    return (CadenaSegura){ .longitud = len, .datos = data };
}

CadenaSegura entero_a_texto(int n) {
    char buf[64];
    int len = snprintf(buf, sizeof(buf), "%d", n);
    char* data = (char*)malloc(len + 1);
    if (!data) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en entero_a_texto\n"); exit(1); }
    memcpy(data, buf, len + 1);
    return (CadenaSegura){ .longitud = len, .datos = data };
}

// --- CanalConcurrencia API (Zero-Copy, Thread-Safe) ---

CanalConcurrencia* canal_crear(uint32_t capacidad) {
    if (capacidad == 0) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: capacidad del canal debe ser > 0\n");
        return NULL;
    }
    
    CanalConcurrencia* canal = (CanalConcurrencia*)malloc(sizeof(CanalConcurrencia));
    if (!canal) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en canal_crear\n");
        return NULL;
    }
    
    canal->buffer = (void**)malloc(capacidad * sizeof(void*));
    if (!canal->buffer) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en canal_crear (buffer)\n");
        free(canal);
        return NULL;
    }
    
    canal->capacidad = capacidad;
    canal->cabeza = 0;
    canal->cola = 0;
    canal->contador = 0;
    
    pthread_mutex_init(&canal->mutex, NULL);
    pthread_cond_init(&canal->no_vacio, NULL);
    pthread_cond_init(&canal->no_lleno, NULL);
    
    return canal;
}

void canal_enviar(CanalConcurrencia* canal, void* paquete) {
    if (!canal) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: canal nulo en canal_enviar\n");
        return;
    }
    
    pthread_mutex_lock(&canal->mutex);
    
    // Esperar si el buffer está lleno
    while (canal->contador == canal->capacidad) {
        pthread_cond_wait(&canal->no_lleno, &canal->mutex);
    }
    
    // Escribir en la cabeza del buffer circular (Zero-Copy)
    canal->buffer[canal->cabeza] = paquete;
    canal->cabeza = (canal->cabeza + 1) % canal->capacidad;
    canal->contador++;
    
    // Señalar a receptores que hay datos
    pthread_cond_signal(&canal->no_vacio);
    
    pthread_mutex_unlock(&canal->mutex);
}

void* canal_recibir(CanalConcurrencia* canal) {
    if (!canal) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: canal nulo en canal_recibir\n");
        return NULL;
    }
    
    pthread_mutex_lock(&canal->mutex);
    
    // Esperar si el buffer está vacío
    while (canal->contador == 0) {
        pthread_cond_wait(&canal->no_vacio, &canal->mutex);
    }
    
    // Leer de la cola del buffer circular (Zero-Copy)
    void* paquete = canal->buffer[canal->cola];
    canal->cola = (canal->cola + 1) % canal->capacidad;
    canal->contador--;
    
    // Señalar a emisores que hay espacio
    pthread_cond_signal(&canal->no_lleno);
    
    pthread_mutex_unlock(&canal->mutex);
    
    return paquete;
}

void canal_destruir(CanalConcurrencia* canal) {
    if (!canal) return;
    
    pthread_mutex_destroy(&canal->mutex);
    pthread_cond_destroy(&canal->no_vacio);
    pthread_cond_destroy(&canal->no_lleno);
    
    if (canal->buffer) {
        free(canal->buffer);
    }
    
    free(canal);
}

// --- Thread tracker ---
static int hilos_activos = 0;
static pthread_mutex_t hilo_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t hilo_cond = PTHREAD_COND_INITIALIZER;

struct _HiloArgs {
    void* (*fn)(void*);
    void* arg;
};

static void* _synapse_hilo_wrapper(void* raw_args) {
    struct _HiloArgs* ha = (struct _HiloArgs*)raw_args;
    void* (*fn)(void*) = ha->fn;
    void* arg = ha->arg;
    free(ha);
    fn(arg);
    pthread_mutex_lock(&hilo_mutex);
    hilos_activos--;
    if (hilos_activos == 0) {
        pthread_cond_broadcast(&hilo_cond);
    }
    pthread_mutex_unlock(&hilo_mutex);
    return NULL;
}

void synapse_lanzar_hilo(void* (*fn)(void*), void* arg) {
    pthread_mutex_lock(&hilo_mutex);
    hilos_activos++;
    pthread_mutex_unlock(&hilo_mutex);
    struct _HiloArgs* ha = (struct _HiloArgs*)malloc(sizeof(struct _HiloArgs));
    if (!ha) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo en synapse_lanzar_hilo\n"); exit(1); }
    ha->fn = fn;
    ha->arg = arg;
    pthread_t _t;
    pthread_create(&_t, NULL, _synapse_hilo_wrapper, ha);
    pthread_detach(_t);
}

void synapse_esperar_hilos(void) {
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
}

// ============================================================
// std.net — Socket helpers (TCP client)
// ============================================================

int _syn_iniciar_red(void) {
#ifdef _WIN32
    WSADATA wsa;
    return WSAStartup(MAKEWORD(2,2), &wsa);
#else
    return 0;
#endif
}

int _syn_cerrar_red(void) {
#ifdef _WIN32
    return WSACleanup();
#else
    return 0;
#endif
}

int _syn_socket(void) {
    return (int)socket(AF_INET, SOCK_STREAM, 0);
}

int _syn_conectar(int fd, const char* ip, int puerto) {
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons((unsigned short)puerto);
    addr.sin_addr.s_addr = inet_addr(ip);
    if (addr.sin_addr.s_addr == INADDR_NONE)
        return -1;
    return connect(fd, (struct sockaddr*)&addr, sizeof(addr));
}

int _syn_enviar(int fd, const char* datos, int lon) {
    return (int)send(fd, datos, (size_t)lon, 0);
}

int _syn_recibir(int fd, char* buf, int lon) {
    return (int)recv(fd, buf, (size_t)lon, 0);
}

int _syn_cerrar_socket(int fd) {
#ifdef _WIN32
    return closesocket(fd);
#else
    return close(fd);
#endif
}

// --- Buffer helpers for std.net FFI (receive path) ---
void* _syn_buffer_alloc(int tamano) {
    return _pool_malloc((size_t)tamano);
}

void _syn_buffer_free(void* ptr) {
    if (ptr) pool_free(ptr);
}

// Receive up to tamano bytes, return as CadenaSegura (heap-allocated datos).
// On failure returns empty CadenaSegura (datos="") — caller checks via == "".
// On success caller MUST call _syn_texto_liberar() when done.
CadenaSegura _syn_recibir_como_texto(int fd, int tamano) {
    char* buf = (char*)_pool_malloc((size_t)(tamano + 1));
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
// std.json — JSON Parser (Deserializador Determinista)
// ============================================================

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

// --- Dynamic array helpers (internal) ---

typedef struct {
    NodoJson* items;
    int count;
    int cap;
} NodoArr;

static void nodo_arr_init(NodoArr* a) { a->items = NULL; a->count = 0; a->cap = 0; }

static void nodo_arr_append(NodoArr* a, NodoJson item) {
    if (a->count >= a->cap) {
        a->cap = a->cap ? a->cap * 2 : 8;
        NodoJson* new = (NodoJson*)malloc(a->cap * sizeof(NodoJson));
        if (a->items) { memcpy(new, a->items, a->count * sizeof(NodoJson)); free(a->items); }
        a->items = new;
    }
    a->items[a->count++] = item;
}

static NodoJson* nodo_arr_detach(NodoArr* a) {
    NodoJson* p = a->items;
    a->items = NULL;
    a->count = 0;
    a->cap = 0;
    return p;
}

typedef struct {
    ParJson* items;
    int count;
    int cap;
} ParArr;

static void par_arr_init(ParArr* a) { a->items = NULL; a->count = 0; a->cap = 0; }

static void par_arr_append(ParArr* a, CadenaSegura clave, NodoJson* valor) {
    if (a->count >= a->cap) {
        a->cap = a->cap ? a->cap * 2 : 8;
        ParJson* new = (ParJson*)malloc(a->cap * sizeof(ParJson));
        if (a->items) { memcpy(new, a->items, a->count * sizeof(ParJson)); free(a->items); }
        a->items = new;
    }
    a->items[a->count].clave = clave;
    a->items[a->count].valor = valor;
    a->count++;
}

static ParJson* par_arr_detach(ParArr* a) {
    ParJson* p = a->items;
    a->items = NULL;
    a->count = 0;
    a->cap = 0;
    return p;
}

// --- Parser state ---

static CadenaSegura _p_input;
static int _p_pos;

void _json_init(CadenaSegura s) {
    _p_input = s;
    _p_pos = 0;
}

NodoJson _json_nodo_new() {
    NodoJson n = {0};
    return n;
}

void _json_nodo_liberar(NodoJson n) {
    if (n.tipo == 3) {
        if (n.valor_str.datos) { free((void*)n.valor_str.datos); n.valor_str.datos = NULL; }
    } else if (n.tipo == 4) {
        if (n.arreglo_hijos) {
            for (int i = 0; i < n.longitud; i++) _json_nodo_liberar(n.arreglo_hijos[i]);
            free(n.arreglo_hijos); n.arreglo_hijos = NULL;
        }
    } else if (n.tipo == 5) {
        if (n.objeto_pares) {
            for (int i = 0; i < n.longitud; i++) {
                if (n.objeto_pares[i].clave.datos) free((void*)n.objeto_pares[i].clave.datos);
                _json_nodo_liberar(*n.objeto_pares[i].valor);
                free(n.objeto_pares[i].valor);
            }
            free(n.objeto_pares); n.objeto_pares = NULL;
        }
    }
}

// --- Lexer helpers ---

static int _peek() {
    if (_p_pos < 0 || _p_pos >= _p_input.longitud) return -1;
    return (unsigned char)_p_input.datos[_p_pos];
}

static int _advance() {
    if (_p_pos < 0 || _p_pos >= _p_input.longitud) return -1;
    return (unsigned char)_p_input.datos[_p_pos++];
}

static void _skip_ws() {
    while (_p_pos < _p_input.longitud) {
        char c = _p_input.datos[_p_pos];
        if (c == ' ' || c == '\t' || c == '\n' || c == '\r') _p_pos++;
        else break;
    }
}

static int _match_str(const char* expected) {
    int len = (int)strlen(expected);
    if (_p_pos + len > _p_input.longitud) return 0;
    if (strncmp(_p_input.datos + _p_pos, expected, len) == 0) {
        _p_pos += len;
        return 1;
    }
    return 0;
}

static CadenaSegura _parse_string_value() {
    if (_advance() != '"') return (CadenaSegura){0};
    int start = _p_pos;
    while (_p_pos < _p_input.longitud) {
        char c = _p_input.datos[_p_pos];
        if (c == '"') break;
        if (c == '\\') _p_pos++;
        _p_pos++;
    }
    if (_p_pos >= _p_input.longitud) return (CadenaSegura){0};
    int end = _p_pos;
    _p_pos++;
    int len = end - start;
    char* dup = (char*)malloc(len + 1);
    if (!dup) return (CadenaSegura){0};
    memcpy(dup, _p_input.datos + start, len);
    dup[len] = '\0';
    return (CadenaSegura){ .longitud = len, .datos = dup };
}

static float _parse_number_value() {
    int start = _p_pos;
    if (_p_pos < _p_input.longitud && _p_input.datos[_p_pos] == '-') _p_pos++;
    while (_p_pos < _p_input.longitud && _p_input.datos[_p_pos] >= '0' && _p_input.datos[_p_pos] <= '9') _p_pos++;
    if (_p_pos < _p_input.longitud && _p_input.datos[_p_pos] == '.') {
        _p_pos++;
        while (_p_pos < _p_input.longitud && _p_input.datos[_p_pos] >= '0' && _p_input.datos[_p_pos] <= '9') _p_pos++;
    }
    if (_p_pos < _p_input.longitud && (_p_input.datos[_p_pos] == 'e' || _p_input.datos[_p_pos] == 'E')) {
        _p_pos++;
        if (_p_pos < _p_input.longitud && (_p_input.datos[_p_pos] == '+' || _p_input.datos[_p_pos] == '-')) _p_pos++;
        while (_p_pos < _p_input.longitud && _p_input.datos[_p_pos] >= '0' && _p_input.datos[_p_pos] <= '9') _p_pos++;
    }
    int len = _p_pos - start;
    char* buf = (char*)malloc(len + 1);
    if (!buf) return 0.0f;
    memcpy(buf, _p_input.datos + start, len);
    buf[len] = '\0';
    float val = (float)strtod(buf, NULL);
    free(buf);
    return val;
}

// Forward declaration
static NodoJson _parse_value();

static NodoJson _parse_object() {
    NodoJson n = {0};
    n.tipo = 5;
    _advance();
    _skip_ws();
    if (_peek() == '}') { _advance(); return n; }
    ParArr pares;
    par_arr_init(&pares);
    while (1) {
        _skip_ws();
        if (_peek() == '}') break;
        if (pares.count > 0) {
            if (_peek() != ',') break;
            _advance();
            _skip_ws();
        }
        CadenaSegura key = _parse_string_value();
        if (key.datos == NULL) {
            n.tipo = -1;
            n.valor_str = (CadenaSegura){ .longitud = 27, .datos = "fjson: clave de objeto invalida" };
            return n;
        }
        _skip_ws();
        if (_advance() != ':') {
            free((void*)key.datos);
            n.tipo = -1;
            n.valor_str = (CadenaSegura){ .longitud = 25, .datos = "fjson: se esperaba ':'" };
            return n;
        }
        NodoJson val = _parse_value();
        if (val.tipo < 0) {
            free((void*)key.datos);
            _json_nodo_liberar(val);
            return val; // propagate error
        }
        NodoJson* val_ptr = (NodoJson*)malloc(sizeof(NodoJson));
        if (val_ptr) *val_ptr = val;
        par_arr_append(&pares, key, val_ptr);
    }
    _skip_ws();
    if (_peek() == '}') _advance();
    n.longitud = pares.count;
    n.objeto_pares = par_arr_detach(&pares);
    return n;
}

static NodoJson _parse_array() {
    NodoJson n = {0};
    n.tipo = 4;
    _advance();
    _skip_ws();
    if (_peek() == ']') { _advance(); return n; }
    NodoArr arr;
    nodo_arr_init(&arr);
    while (1) {
        _skip_ws();
        if (_peek() == ']') break;
        if (arr.count > 0) {
            if (_peek() != ',') break;
            _advance();
            _skip_ws();
        }
        NodoJson val = _parse_value();
        if (val.tipo < 0) {
            _json_nodo_liberar(val);
            return val; // propagate error
        }
        nodo_arr_append(&arr, val);
    }
    _skip_ws();
    if (_peek() == ']') _advance();
    n.longitud = arr.count;
    n.arreglo_hijos = nodo_arr_detach(&arr);
    return n;
}

static NodoJson _parse_value() {
    NodoJson n = {0};
    _skip_ws();
    int c = _peek();
    if (c == '{') return _parse_object();
    if (c == '[') return _parse_array();
    if (c == '"') {
        CadenaSegura s = _parse_string_value();
        if (s.datos == NULL) { n.tipo = -1; n.valor_str = (CadenaSegura){ .longitud = 25, .datos = "fjson: cadena sin cerrar" }; return n; }
        n.tipo = 3;
        n.valor_str = s;
        return n;
    }
    if (c == 't') { if (_match_str("true")) { n.tipo = 1; n.valor_bool = 1; return n; } }
    if (c == 'f') { if (_match_str("false")) { n.tipo = 1; n.valor_bool = 0; return n; } }
    if (c == 'n') { if (_match_str("null")) { n.tipo = 0; return n; } }
    if (c == '-' || (c >= '0' && c <= '9')) {
        n.tipo = 2;
        n.valor_num = _parse_number_value();
        return n;
    }
    n.tipo = -1;
    n.valor_str = (CadenaSegura){ .longitud = 22, .datos = "fjson: valor inesperado" };
    return n;
}

NodoJson _json_parse(CadenaSegura entrada) {
    _json_init(entrada);
    NodoJson resultado = _parse_value();
    if (resultado.tipo < 0) { _json_nodo_liberar(resultado); return resultado; }
    _skip_ws();
    if (_peek() != -1) {
        _json_nodo_liberar(resultado);
        NodoJson e = {0};
        e.tipo = -1;
        e.valor_str = (CadenaSegura){ .longitud = 39, .datos = "fjson: contenido extra despues del valor" };
        return e;
    }
    return resultado;
}

// --- Deep clone for safe getter returns ---

NodoJson _json_nodo_clonar(NodoJson src) {
    NodoJson n = src;
    if (n.tipo == 3 && n.valor_str.datos) {
        char* dup = (char*)malloc(n.valor_str.longitud + 1);
        if (dup) memcpy(dup, n.valor_str.datos, n.valor_str.longitud + 1);
        n.valor_str.datos = dup;
    } else if (n.tipo == 4 && n.arreglo_hijos) {
        n.arreglo_hijos = (NodoJson*)malloc(n.longitud * sizeof(NodoJson));
        for (int i = 0; i < n.longitud; i++)
            n.arreglo_hijos[i] = _json_nodo_clonar(src.arreglo_hijos[i]);
    } else if (n.tipo == 5 && n.objeto_pares) {
        n.objeto_pares = (ParJson*)malloc(n.longitud * sizeof(ParJson));
        for (int i = 0; i < n.longitud; i++) {
            n.objeto_pares[i].clave = src.objeto_pares[i].clave;
            if (n.objeto_pares[i].clave.datos) {
                char* dup = (char*)malloc(n.objeto_pares[i].clave.longitud + 1);
                if (dup) memcpy(dup, n.objeto_pares[i].clave.datos, n.objeto_pares[i].clave.longitud + 1);
                n.objeto_pares[i].clave.datos = dup;
            }
            n.objeto_pares[i].valor = (NodoJson*)malloc(sizeof(NodoJson));
            if (n.objeto_pares[i].valor)
                *n.objeto_pares[i].valor = _json_nodo_clonar(*src.objeto_pares[i].valor);
        }
    }
    return n;
}

NodoJson _json_array_get(NodoJson nodo, int indice) {
    if (nodo.tipo != 4 || indice < 0 || indice >= nodo.longitud)
        return (NodoJson){0};
    return _json_nodo_clonar(nodo.arreglo_hijos[indice]);
}

NodoJson _json_object_get(NodoJson nodo, CadenaSegura clave) {
    if (nodo.tipo != 5)
        return (NodoJson){0};
    for (int i = 0; i < nodo.longitud; i++) {
        ParJson* p = &nodo.objeto_pares[i];
        if (p->clave.longitud == clave.longitud &&
            (clave.longitud == 0 || strncmp(p->clave.datos, clave.datos, clave.longitud) == 0))
            return _json_nodo_clonar(*p->valor);
    }
    return (NodoJson){0};
}

// ============================================================
// std.toml — TOML Parser (Subset para Axon)
// ============================================================

typedef struct ParToml ParToml;
typedef struct NodoToml NodoToml;

struct ParToml {
    CadenaSegura clave;
    NodoToml* valor;
};

struct NodoToml {
    int tipo;           // -1=Error, 0=Nulo, 1=Tabla, 2=Cadena, 3=TablaEnLinea
    CadenaSegura valor_str;
    ParToml* pares;
    int longitud;
};

// --- TOML parser state ---
static CadenaSegura _t_input;
static int _t_pos;
static int _t_linea;
static int _t_error;

static int _t_peek(void) {
    if (_t_pos >= _t_input.longitud) return -1;
    return (unsigned char)_t_input.datos[_t_pos];
}

static void _t_advance(void) {
    if (_t_pos < _t_input.longitud) _t_pos++;
}

static void _t_skip_ws(void) {
    while (_t_pos < _t_input.longitud) {
        char c = _t_input.datos[_t_pos];
        if (c == ' ' || c == '\t') { _t_pos++; continue; }
        break;
    }
}

static void _t_skip_line(void) {
    while (_t_pos < _t_input.longitud && _t_input.datos[_t_pos] != '\n') _t_pos++;
    if (_t_pos < _t_input.longitud) _t_pos++;
    _t_linea++;
}

static int _t_skip_newline(void) {
    if (_t_peek() == '\r') { _t_advance(); }
    if (_t_peek() == '\n') { _t_advance(); _t_linea++; return 1; }
    return 0;
}

static NodoToml _t_parse_inline_table(void);

static CadenaSegura _t_strdup_c(const char* src, int len) {
    if (len <= 0) return (CadenaSegura){0};
    char* buf = (char*)malloc(len + 1);
    if (!buf) return (CadenaSegura){0};
    memcpy(buf, src, len);
    buf[len] = '\0';
    return (CadenaSegura){ .longitud = len, .datos = buf };
}

static CadenaSegura _t_parse_bare_key(void) {
    int start = _t_pos;
    while (_t_pos < _t_input.longitud) {
        char c = _t_input.datos[_t_pos];
        if (c == '=' || c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '#' || c == '}' || c == ',' || c == ']')
            break;
        _t_pos++;
    }
    int len = _t_pos - start;
    if (len == 0) return (CadenaSegura){0};
    return _t_strdup_c(_t_input.datos + start, len);
}

static CadenaSegura _t_parse_string(void) {
    if (_t_peek() != '"') {
        _t_error = 1;
        return (CadenaSegura){0};
    }
    _t_advance();
    int start = _t_pos;
    while (_t_pos < _t_input.longitud && _t_input.datos[_t_pos] != '"') {
        if (_t_input.datos[_t_pos] == '\\') _t_pos++;
        _t_pos++;
    }
    if (_t_pos >= _t_input.longitud) {
        _t_error = 1;
        return (CadenaSegura){0};
    }
    int raw_len = _t_pos - start;
    char* buf = (char*)malloc(raw_len + 1);
    int wi = 0;
    for (int i = 0; i < raw_len; i++) {
        if (_t_input.datos[start + i] == '\\' && i + 1 < raw_len) {
            i++;
            switch (_t_input.datos[start + i]) {
                case '"': buf[wi++] = '"'; break;
                case '\\': buf[wi++] = '\\'; break;
                case 'n': buf[wi++] = '\n'; break;
                case 't': buf[wi++] = '\t'; break;
                default: buf[wi++] = _t_input.datos[start + i]; break;
            }
        } else {
            buf[wi++] = _t_input.datos[start + i];
        }
    }
    buf[wi] = '\0';
    _t_advance();
    return (CadenaSegura){ .longitud = wi, .datos = buf };
}

static NodoToml _t_parse_value(void) {
    _t_skip_ws();
    int c = _t_peek();
    if (c == '"') {
        CadenaSegura s = _t_parse_string();
        return (NodoToml){ .tipo = 2, .valor_str = s };
    }
    if (c == '{') {
        return _t_parse_inline_table();
    }
    // Bare value (treat as string for now)
    CadenaSegura s = _t_parse_bare_key();
    if (_t_error || s.longitud == 0) {
        if (s.datos) free((void*)s.datos);
        _t_error = 1;
        return (NodoToml){ .tipo = -1 };
    }
    return (NodoToml){ .tipo = 2, .valor_str = s };
}

static void _t_nodo_liberar_internal(NodoToml n);

static NodoToml _t_parse_inline_table(void) {
    _t_advance();
    NodoToml tbl = { .tipo = 3 };
    int cap = 0;
    while (_t_pos < _t_input.longitud && !_t_error) {
        _t_skip_ws();
        int c = _t_peek();
        if (c == '}') { _t_advance(); break; }
        if (c == ',' || c == '\n' || c == '\r') { _t_advance(); continue; }

        CadenaSegura key = _t_parse_bare_key();
        if (_t_error || key.longitud == 0) { free((void*)key.datos); break; }
        _t_skip_ws();
        if (_t_peek() != '=') { _t_error = 1; free((void*)key.datos); break; }
        _t_advance();

        NodoToml val = _t_parse_value();
        if (_t_error) { free((void*)key.datos); _t_nodo_liberar_internal(val); break; }

        if (tbl.longitud >= cap) {
            cap = cap == 0 ? 4 : cap * 2;
            tbl.pares = (ParToml*)realloc(tbl.pares, cap * sizeof(ParToml));
        }
        ParToml* p = &tbl.pares[tbl.longitud++];
        p->clave = key;
        p->valor = (NodoToml*)malloc(sizeof(NodoToml));
        *p->valor = val;

        _t_skip_ws();
        if (_t_peek() == '}') { _t_advance(); break; }
        if (_t_peek() == ',') _t_advance();
    }
    return tbl;
}

static CadenaSegura _t_parse_section_key(void) {
    _t_skip_ws();
    int start = _t_pos;
    while (_t_pos < _t_input.longitud) {
        char c = _t_input.datos[_t_pos];
        if (c == ']' || c == '\n' || c == '\r') break;
        _t_pos++;
    }
    int end = _t_pos;
    while (end > start && (_t_input.datos[end-1] == ' ' || _t_input.datos[end-1] == '\t')) end--;
    if (_t_peek() != ']') return (CadenaSegura){0};
    return _t_strdup_c(_t_input.datos + start, end - start);
}

static NodoToml* _t_find_or_create_table(NodoToml* root, CadenaSegura name) {
    for (int i = 0; i < root->longitud; i++) {
        ParToml* p = &root->pares[i];
        if (p->clave.longitud == name.longitud &&
            (name.longitud == 0 || strncmp(p->clave.datos, name.datos, name.longitud) == 0)) {
            return p->valor;
        }
    }
    NodoToml* tbl = (NodoToml*)calloc(1, sizeof(NodoToml));
    tbl->tipo = 1;
    if (root->longitud >= 0) {
        root->pares = (ParToml*)realloc(root->pares, (root->longitud + 1) * sizeof(ParToml));
        root->pares[root->longitud].clave = _t_strdup_c(name.datos, name.longitud);
        root->pares[root->longitud].valor = tbl;
        root->longitud++;
    }
    return tbl;
}

static void _t_nodo_liberar_internal(NodoToml n) {
    if (n.tipo == 2 || n.tipo == -1) {
        // NOTA: NO liberamos n.valor_str.datos aquí porque la propiedad
        // se transfiere al llamante cuando accede a campo.valor_str.
    } else if (n.tipo == 1 || n.tipo == 3) {
        if (n.pares) {
            for (int i = 0; i < n.longitud; i++) {
                if (n.pares[i].clave.datos) free((void*)n.pares[i].clave.datos);
                if (n.pares[i].valor) {
                    _t_nodo_liberar_internal(*n.pares[i].valor);
                    free(n.pares[i].valor);
                    n.pares[i].valor = NULL;
                }
            }
            free(n.pares);
            n.pares = NULL;
        }
    }
}

NodoToml _toml_nodo_new(void) {
    return (NodoToml){0};
}

void _toml_nodo_liberar(NodoToml n) {
    _t_nodo_liberar_internal(n);
}

static NodoToml _t_nodo_clonar(NodoToml src) {
    NodoToml n = { .tipo = src.tipo, .longitud = 0 };
    if (src.tipo == 2 || src.tipo == -1) {
        n.valor_str = _t_strdup_c(src.valor_str.datos, src.valor_str.longitud);
    } else if (src.tipo == 1 || src.tipo == 3) {
        if (src.pares && src.longitud > 0) {
            n.pares = (ParToml*)malloc(src.longitud * sizeof(ParToml));
            n.longitud = src.longitud;
            for (int i = 0; i < src.longitud; i++) {
                n.pares[i].clave = _t_strdup_c(src.pares[i].clave.datos, src.pares[i].clave.longitud);
                n.pares[i].valor = (NodoToml*)malloc(sizeof(NodoToml));
                *n.pares[i].valor = _t_nodo_clonar(*src.pares[i].valor);
            }
        }
    }
    return n;
}

NodoToml _toml_object_get(NodoToml nodo, CadenaSegura clave) {
    if (nodo.tipo != 1 && nodo.tipo != 3)
        return (NodoToml){0};
    for (int i = 0; i < nodo.longitud; i++) {
        ParToml* p = &nodo.pares[i];
        if (p->clave.longitud == clave.longitud &&
            (clave.longitud == 0 || strncmp(p->clave.datos, clave.datos, clave.longitud) == 0))
            return _t_nodo_clonar(*p->valor);
    }
    return (NodoToml){0};
}

NodoToml _toml_parse(CadenaSegura entrada) {
    _t_input = entrada;
    _t_pos = 0;
    _t_linea = 1;
    _t_error = 0;

    NodoToml root = { .tipo = 1 };
    NodoToml* current = &root;

    while (_t_pos < _t_input.longitud && !_t_error) {
        _t_skip_ws();
        int c = _t_peek();
        if (c < 0) break;
        if (c == '\n' || c == '\r') { _t_skip_newline(); continue; }
        if (c == '#') { _t_skip_line(); continue; }

        if (c == '[') {
            _t_advance();
            CadenaSegura sec_name = _t_parse_section_key();
            if (_t_error || sec_name.longitud == 0) {
                _t_error = 1;
                break;
            }
            _t_advance();
            NodoToml* tbl = _t_find_or_create_table(&root, sec_name);
            free((void*)sec_name.datos);
            current = tbl ? tbl : &root;
            _t_skip_line();
            continue;
        }

        // Key-value pair
        CadenaSegura key = _t_parse_bare_key();
        _t_skip_ws();
        if (_t_peek() != '=') { _t_error = 1; free((void*)key.datos); break; }
        _t_advance();
        NodoToml val = _t_parse_value();
        if (_t_error) {
            free((void*)key.datos);
            _t_nodo_liberar_internal(val);
            break;
        }

        if (current->longitud >= 0) {
            current->pares = (ParToml*)realloc(current->pares, (current->longitud + 1) * sizeof(ParToml));
            current->pares[current->longitud].clave = key;
            current->pares[current->longitud].valor = (NodoToml*)malloc(sizeof(NodoToml));
            *current->pares[current->longitud].valor = val;
            current->longitud++;
        }
        _t_skip_line();
    }

    if (_t_error) {
        _t_nodo_liberar_internal(root);
        char err_buf[128];
        int err_len = snprintf(err_buf, sizeof(err_buf),
            "Error TOML linea %d", _t_linea);
        NodoToml err = { .tipo = -1 };
        err.valor_str = _t_strdup_c(err_buf, err_len);
        return err;
    }

    return root;
}

// ============================================================
// std.tiempo — Time & Profiling
// ============================================================

int64_t _syn_ahora_ms(void) {
#ifdef _WIN32
    FILETIME ft;
    GetSystemTimeAsFileTime(&ft);
    uint64_t t = ((uint64_t)ft.dwHighDateTime << 32) | ft.dwLowDateTime;
    // Convert from 100-ns intervals since 1601-01-01 to ms since 1970-01-01
    return (int64_t)((t - 116444736000000000ULL) / 10000);
#else
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (int64_t)ts.tv_sec * 1000 + (int64_t)ts.tv_nsec / 1000000;
#endif
}

void _syn_dormir_ms(int ms) {
#ifdef _WIN32
    Sleep((DWORD)ms);
#else
    struct timespec ts;
    ts.tv_sec = ms / 1000;
    ts.tv_nsec = (long)(ms % 1000) * 1000000L;
    nanosleep(&ts, NULL);
#endif
}

// ============================================================
// std.cripto — SHA-256 (FIPS 180-4)
// ============================================================

#define SHA256_BLOCK_SIZE 64
#define SHA256_DIGEST_SIZE 32

typedef struct {
    uint32_t state[8];
    uint64_t bitcount;
    uint8_t buffer[SHA256_BLOCK_SIZE];
    uint32_t buffer_len;
} SHA256_CTX;

static const uint32_t K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

#define ROTR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))
#define CH(x, y, z) (((x) & (y)) ^ (~(x) & (z)))
#define MAJ(x, y, z) (((x) & (y)) ^ ((x) & (z)) ^ ((y) & (z)))
#define SIG0(x) (ROTR(x, 2) ^ ROTR(x, 13) ^ ROTR(x, 22))
#define SIG1(x) (ROTR(x, 6) ^ ROTR(x, 11) ^ ROTR(x, 25))
#define sig0(x) (ROTR(x, 7) ^ ROTR(x, 18) ^ ((x) >> 3))
#define sig1(x) (ROTR(x, 17) ^ ROTR(x, 19) ^ ((x) >> 10))

static void sha256_transform(SHA256_CTX* ctx, const uint8_t* block) {
    uint32_t W[64];
    for (int i = 0; i < 16; i++) {
        W[i] = ((uint32_t)block[i*4] << 24) | ((uint32_t)block[i*4+1] << 16)
             | ((uint32_t)block[i*4+2] << 8)  | (uint32_t)block[i*4+3];
    }
    for (int i = 16; i < 64; i++) {
        W[i] = sig1(W[i-2]) + W[i-7] + sig0(W[i-15]) + W[i-16];
    }

    uint32_t a = ctx->state[0], b = ctx->state[1];
    uint32_t c = ctx->state[2], d = ctx->state[3];
    uint32_t e = ctx->state[4], f = ctx->state[5];
    uint32_t g = ctx->state[6], h = ctx->state[7];

    for (int i = 0; i < 64; i++) {
        uint32_t T1 = h + SIG1(e) + CH(e, f, g) + K[i] + W[i];
        uint32_t T2 = SIG0(a) + MAJ(a, b, c);
        h = g; g = f; f = e; e = d + T1;
        d = c; c = b; b = a; a = T1 + T2;
    }

    ctx->state[0] += a; ctx->state[1] += b;
    ctx->state[2] += c; ctx->state[3] += d;
    ctx->state[4] += e; ctx->state[5] += f;
    ctx->state[6] += g; ctx->state[7] += h;
}

static void sha256_init(SHA256_CTX* ctx) {
    ctx->state[0] = 0x6a09e667; ctx->state[1] = 0xbb67ae85;
    ctx->state[2] = 0x3c6ef372; ctx->state[3] = 0xa54ff53a;
    ctx->state[4] = 0x510e527f; ctx->state[5] = 0x9b05688c;
    ctx->state[6] = 0x1f83d9ab; ctx->state[7] = 0x5be0cd19;
    ctx->bitcount = 0;
    ctx->buffer_len = 0;
}

static void sha256_update(SHA256_CTX* ctx, const uint8_t* data, size_t len) {
    for (size_t i = 0; i < len; i++) {
        ctx->buffer[ctx->buffer_len++] = data[i];
        ctx->bitcount += 8;
        if (ctx->buffer_len == SHA256_BLOCK_SIZE) {
            sha256_transform(ctx, ctx->buffer);
            ctx->buffer_len = 0;
        }
    }
}

static void sha256_final(SHA256_CTX* ctx, uint8_t* digest) {
    uint64_t bitcount = ctx->bitcount;
    ctx->buffer[ctx->buffer_len++] = 0x80;
    if (ctx->buffer_len > 56) {
        while (ctx->buffer_len < SHA256_BLOCK_SIZE)
            ctx->buffer[ctx->buffer_len++] = 0;
        sha256_transform(ctx, ctx->buffer);
        ctx->buffer_len = 0;
    }
    while (ctx->buffer_len < 56)
        ctx->buffer[ctx->buffer_len++] = 0;
    for (int i = 7; i >= 0; i--) {
        ctx->buffer[56 + i] = (uint8_t)(bitcount >> ((7 - i) * 8));
    }
    sha256_transform(ctx, ctx->buffer);
    for (int i = 0; i < 8; i++) {
        digest[i*4]   = (ctx->state[i] >> 24) & 0xFF;
        digest[i*4+1] = (ctx->state[i] >> 16) & 0xFF;
        digest[i*4+2] = (ctx->state[i] >> 8) & 0xFF;
        digest[i*4+3] = ctx->state[i] & 0xFF;
    }
}

CadenaSegura _syn_sha256_texto(CadenaSegura datos) {
    SHA256_CTX ctx;
    uint8_t digest[SHA256_DIGEST_SIZE];
    char hex[65];

    sha256_init(&ctx);
    sha256_update(&ctx, (const uint8_t*)datos.datos, (size_t)datos.longitud);
    sha256_final(&ctx, digest);

    for (int i = 0; i < SHA256_DIGEST_SIZE; i++) {
        sprintf(hex + i * 2, "%02x", digest[i]);
    }
    hex[64] = '\0';

    char* data = (char*)malloc(65);
    if (!data) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(data, hex, 65);
    return (CadenaSegura){ .longitud = 64, .datos = data };
}

// ============================================================
// std.http — HTTP Server (Minimalista, sincrono, single-thread)
// ============================================================

int _syn_servidor_escuchar(int puerto) {
    int fd = (int)socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return -1;

    int opt = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons((unsigned short)puerto);

    if (bind(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        _syn_cerrar_socket(fd);
        return -1;
    }
    if (listen(fd, 5) < 0) {
        _syn_cerrar_socket(fd);
        return -1;
    }
    return fd;
}

int _syn_servidor_aceptar(int fd_servidor) {
    struct sockaddr_in cliente;
    socklen_t tam = sizeof(cliente);
    return (int)accept(fd_servidor, (struct sockaddr*)&cliente, &tam);
}

// Lee una peticion HTTP completa (hasta \r\n\r\n + contenido opcional)
CadenaSegura _syn_http_leer_peticion(int fd_cliente) {
    char buf[4096];
    int total = 0;
    int n;

    while (total < (int)sizeof(buf) - 1) {
        n = (int)recv(fd_cliente, buf + total, (size_t)(sizeof(buf) - 1 - total), 0);
        if (n <= 0) break;
        total += n;
        buf[total] = '\0';
        // Check for end of headers
        if (total >= 4 && memcmp(buf + total - 4, "\r\n\r\n", 4) == 0)
            break;
    }
    if (total <= 0) return (CadenaSegura){ .longitud = 0, .datos = "" };

    char* data = (char*)malloc((size_t)(total + 1));
    if (!data) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(data, buf, (size_t)total);
    data[total] = '\0';
    return (CadenaSegura){ .longitud = total, .datos = data };
}

int _syn_http_enviar_respuesta(int fd_cliente, CadenaSegura respuesta) {
    int total = (int)send(fd_cliente, respuesta.datos, (size_t)respuesta.longitud, 0);
    return total;
}

void _syn_http_cerrar_cliente(int fd_cliente) {
    _syn_cerrar_socket(fd_cliente);
}

CadenaSegura _syn_http_respuesta_ok(int codigo, const char* tipo, const char* cuerpo, int lon) {
    char header[512];
    int hlen = snprintf(header, sizeof(header),
        "HTTP/1.1 %d OK\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %d\r\n"
        "Connection: close\r\n\r\n",
        codigo, tipo, lon);
    if (hlen < 0 || hlen >= (int)sizeof(header)) {
        return (CadenaSegura){ .longitud = 0, .datos = "" };
    }
    int total = hlen + lon;
    char* buf = (char*)malloc((size_t)(total + 1));
    if (!buf) return (CadenaSegura){ .longitud = 0, .datos = "" };
    memcpy(buf, header, (size_t)hlen);
    memcpy(buf + hlen, cuerpo, (size_t)lon);
    buf[total] = '\0';
    return (CadenaSegura){ .longitud = total, .datos = buf };
}
