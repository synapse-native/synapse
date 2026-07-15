// synapse_rt.c — Runtime precompilado para Synapse
// Compilar una sola vez: gcc -c synapse_rt.c -o synapse_rt.o
// Linkear: gcc programa.c synapse_rt.o -o programa -lpthread

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
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
  #include <sys/mman.h>
  #include <fcntl.h>
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
    if (strcmp(ruta.datos, "librerias/std/modelo.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_MODELO; _c.virtual_len = (int)strlen(LIB_MODELO); _c.es_valido = 1; return _c; }
    if (strcmp(ruta.datos, "librerias/std/oraculo.syn") == 0) { _c.es_virtual = 1; _c.virtual_data = LIB_ORACULO; _c.virtual_len = (int)strlen(LIB_ORACULO); _c.es_valido = 1; return _c; }
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
    r.es_mapeado = 0;
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
    r.es_mapeado = 0;
    r.datos = _pool_malloc(r.filas * r.columnas * sizeof(float));
    for (int _i = 0; _i < r.filas * r.columnas; _i++) {
        r.datos[_i] = a.datos[_i] + b.datos[_i];
    }
    if (!a.es_mapeado) { pool_free(a.datos); }
    if (!b.es_mapeado) { pool_free(b.datos); }
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
    r.es_mapeado = 0;
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
    if (!a.es_mapeado) { pool_free(a.datos); }
    if (!b.es_mapeado) { pool_free(b.datos); }
    return r;
}

Tensor relu(Tensor a) {
    Tensor r;
    r.filas = a.filas;
    r.columnas = a.columnas;
    r.es_mapeado = 0;
    r.datos = _pool_malloc(a.filas * a.columnas * sizeof(float));
    for (int _i = 0; _i < a.filas * a.columnas; _i++) {
        r.datos[_i] = (a.datos[_i] > 0) ? a.datos[_i] : 0.0f;
    }
    if (!a.es_mapeado) { pool_free(a.datos); }
    return r;
}

// --- std.tensor (cache-optimized) ---
void _syn_llenar_tensor_constante(Tensor t, float valor) {
    for (int _i = 0; _i < (int)(t.filas * t.columnas); _i++) {
        t.datos[_i] = valor;
    }
}

Tensor _syn_multiplicar_matrices(Tensor a, Tensor b) {
    if (a.columnas != b.filas) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: dimensiones incompatibles en multiplicar_matrices()\n");
        return (Tensor){ .filas = 0, .columnas = 0, .datos = NULL };
    }
    Tensor r;
    r.filas = a.filas;
    r.columnas = b.columnas;
    r.es_mapeado = 0;
    r.datos = (float*)_pool_malloc(r.filas * r.columnas * sizeof(float));
    memset(r.datos, 0, r.filas * r.columnas * sizeof(float));
    for (int _i = 0; _i < (int)r.filas; _i++) {
        for (int _k = 0; _k < (int)a.columnas; _k++) {
            float _a_ik = a.datos[_i * a.columnas + _k];
            for (int _j = 0; _j < (int)r.columnas; _j++) {
                r.datos[_i * r.columnas + _j] += _a_ik * b.datos[_k * b.columnas + _j];
            }
        }
    }
    if (!a.es_mapeado) { pool_free(a.datos); }
    if (!b.es_mapeado) { pool_free(b.datos); }
    return r;
}

// --- std.tensor (Transformer primitives) ---
// extraer_fila: copia una fila de tabla_embeddings(indice_token, :) hacia salida(1, :)
void _syn_extraer_fila(Tensor salida, Tensor tabla_embeddings, int indice_token) {
    if (indice_token < 0 || indice_token >= (int)tabla_embeddings.filas) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: indice_token %d fuera de rango [0, %u)\n",
                indice_token, tabla_embeddings.filas);
        return;
    }
    uint32_t n = salida.columnas;
    float* src = tabla_embeddings.datos + indice_token * tabla_embeddings.columnas;
    memcpy(salida.datos, src, n * sizeof(float));
}

// rmsnorm: salida[i] = entrada[i] / sqrt(mean(entrada^2) + epsilon) * peso_normalizacion[i]
void _syn_rmsnorm(Tensor salida, Tensor entrada, Tensor peso_normalizacion, float epsilon) {
    uint32_t n = entrada.columnas;
    float suma_cuadrados = 0.0f;
    for (uint32_t _i = 0; _i < n; _i++) {
        float v = entrada.datos[_i];
        suma_cuadrados += v * v;
    }
    float rms = sqrtf(suma_cuadrados / (float)n + epsilon);
    for (uint32_t _i = 0; _i < n; _i++) {
        salida.datos[_i] = (entrada.datos[_i] / rms) * peso_normalizacion.datos[_i];
    }
}

// silu (Swish): salida[i] = entrada[i] / (1 + exp(-entrada[i]))
void _syn_silu(Tensor salida, Tensor entrada) {
    uint32_t n = entrada.columnas;
    for (uint32_t _i = 0; _i < n; _i++) {
        float x = entrada.datos[_i];
        salida.datos[_i] = x / (1.0f + expf(-x));
    }
}

// --- std.tensor (Attention primitives) ---
// rope: aplica Rotary Position Embedding in-place sobre un tensor 1D (1xN)
void _syn_rope(Tensor tensor, int posicion_token, int head_dim, float theta_base) {
    uint32_t n = tensor.columnas;
    if (head_dim > (int)n) head_dim = (int)n;
    for (int _i = 0; _i < head_dim; _i += 2) {
        float freq = 1.0f / powf(theta_base, (float)_i / (float)head_dim);
        float cos_v = cosf((float)posicion_token * freq);
        float sin_v = sinf((float)posicion_token * freq);
        float x0 = tensor.datos[_i];
        float x1 = tensor.datos[_i + 1];
        tensor.datos[_i]     = x0 * cos_v - x1 * sin_v;
        tensor.datos[_i + 1] = x0 * sin_v + x1 * cos_v;
    }
}

// softmax_escalado: aplica softmax con factor de escala sobre cada fila (estabilidad: resta max)
void _syn_softmax_escalado(Tensor tensor, float factor_escala) {
    uint32_t filas = tensor.filas;
    uint32_t cols = tensor.columnas;
    for (uint32_t _f = 0; _f < filas; _f++) {
        float* fila = tensor.datos + _f * cols;
        float max_val = -1e30f;
        for (uint32_t _c = 0; _c < cols; _c++) {
            float v = fila[_c] * factor_escala;
            if (v > max_val) max_val = v;
        }
        float suma = 0.0f;
        for (uint32_t _c = 0; _c < cols; _c++) {
            float e = expf(fila[_c] * factor_escala - max_val);
            fila[_c] = e;
            suma += e;
        }
        if (suma > 0.0f) {
            for (uint32_t _c = 0; _c < cols; _c++) {
                fila[_c] /= suma;
            }
        }
    }
}

// multiplicar_matrices_transpuesta_b: C = A * B^T  (zero-copy, B se lee transpuesto)
void _syn_multiplicar_matrices_transpuesta_b(Tensor a, Tensor b, Tensor salida) {
    uint32_t M = a.filas;
    uint32_t K = a.columnas;  // tambien = b.columnas (B sin transponer)
    uint32_t N = b.filas;     // resultado = M x N
    for (uint32_t _i = 0; _i < M; _i++) {
        for (uint32_t _j = 0; _j < N; _j++) {
            float _sum = 0.0f;
            for (uint32_t _k = 0; _k < K; _k++) {
                _sum += a.datos[_i * K + _k] * b.datos[_j * K + _k];
            }
            salida.datos[_i * N + _j] = _sum;
        }
    }
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
    _bloque.es_mapeado = 0;
    _bloque.datos = _pool_malloc(tamano);
    return _bloque;
}

void libera(Tensor bloque) {
    if (bloque.datos && !bloque.es_mapeado) {
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

// --- std.ai (GGUF Reader / Memory Mapping) ---
#define MEM_ALIGN 32
#define HASH_TAM 256
#define MAX_METADATOS 128

// GGML tensor types
#define GGML_TYPE_F32  0
#define GGML_TYPE_F16  1
#define GGML_TYPE_Q4_0 2
#define GGML_TYPE_Q4_1 3
#define GGML_TYPE_Q5_0 6
#define GGML_TYPE_Q5_1 7
#define GGML_TYPE_Q8_0 8

typedef struct TensorInfo {
    char* nombre;
    int n_dimensiones;
    uint64_t dimensiones[4];
    int tipo;
    uint64_t offset;
} TensorInfo;

typedef struct EntradaHash {
    uint32_t indice_tensor;
    struct EntradaHash* siguiente;
} EntradaHash;

typedef struct {
    char* clave;
    char* valor;
} ParMetadato;

#define MAX_ARRAY_METADATOS 32

typedef struct {
    char* clave;
    int tipo_elemento;
    int cantidad;
    uint64_t data_pos;    // offset in mmap where element storage starts
} ArrayMetaEntry;

typedef struct InternalData {
    void* mmap_ptr;
    int64_t tamano_mmap;
    uint64_t tensor_data_base_offset;
    int cantidad_tensores;
    TensorInfo* tensores;
    EntradaHash* tabla_hash[HASH_TAM];
    int cantidad_metadatos;
    ParMetadato metadatos[MAX_METADATOS];
    char* architecture;
    ArrayMetaEntry arrays[MAX_ARRAY_METADATOS];
    int cantidad_arrays;
} InternalData;

typedef struct GGUF_Contexto {
    int es_valido;
    int version;
    int cantidad_tensores;
    void* datos_mmap;
    int tamano_total;
    int tamano_mmap;
    void* handle_plataforma;
    void* handle_archivo;
    void* datos_internos;
} GGUF_Contexto;

static uint32_t fnv1a_hash(const char* str) {
    uint32_t h = 2166136261u;
    while (*str) {
        h ^= (unsigned char)*str++;
        h *= 16777619u;
    }
    return h;
}

static char* gguf_read_string(const unsigned char* base, int64_t size, uint64_t* pos) {
    if ((int64_t)(*pos + 8) > size) return NULL;
    uint64_t len = *(const uint64_t*)(base + *pos);
    *pos += 8;
    if ((int64_t)(*pos + len) > size) return NULL;
    char* s = (char*)malloc((size_t)(len + 1));
    if (!s) return NULL;
    memcpy(s, base + *pos, (size_t)len);
    s[len] = '\0';
    *pos += len;
    return s;
}

// Read a GGUF value and return its string representation (malloc'd).
// Returns NULL if unsupported; caller must free.
static char* gguf_value_as_string(const unsigned char* base, int64_t size, uint64_t* pos, uint32_t val_type) {
    char buf[128];
    switch (val_type) {
        case 0: case 1: { // UINT8, INT8
            if ((int64_t)(*pos + 1) > size) return NULL;
            int v = (int)base[*pos];
            *pos += 1;
            snprintf(buf, sizeof(buf), "%d", v);
            return strdup(buf);
        }
        case 2: case 3: { // UINT16, INT16
            if ((int64_t)(*pos + 2) > size) return NULL;
            int v = (int)(*(const uint16_t*)(base + *pos));
            *pos += 2;
            snprintf(buf, sizeof(buf), "%d", v);
            return strdup(buf);
        }
        case 4: case 5: { // UINT32, INT32
            if ((int64_t)(*pos + 4) > size) return NULL;
            int v = (int)(*(const uint32_t*)(base + *pos));
            *pos += 4;
            snprintf(buf, sizeof(buf), "%d", v);
            return strdup(buf);
        }
        case 6: { // FLOAT32
            if ((int64_t)(*pos + 4) > size) return NULL;
            float v = *(const float*)(base + *pos);
            *pos += 4;
            snprintf(buf, sizeof(buf), "%g", v);
            return strdup(buf);
        }
        case 7: { // BOOL
            if ((int64_t)(*pos + 1) > size) return NULL;
            int v = base[*pos] ? 1 : 0;
            *pos += 1;
            return strdup(v ? "true" : "false");
        }
        case 8: { // STRING
            return gguf_read_string(base, size, pos);
        }
        case 10: case 11: { // UINT64, INT64
            if ((int64_t)(*pos + 8) > size) return NULL;
            long long v = (long long)(*(const uint64_t*)(base + *pos));
            *pos += 8;
            snprintf(buf, sizeof(buf), "%lld", v);
            return strdup(buf);
        }
        case 12: { // FLOAT64
            if ((int64_t)(*pos + 8) > size) return NULL;
            double v = *(const double*)(base + *pos);
            *pos += 8;
            snprintf(buf, sizeof(buf), "%g", v);
            return strdup(buf);
        }
        default:
            // ARRAY (9) and unknown types: return NULL (caller handles skip)
            return NULL;
    }
}

#ifdef _WIN32
static void* _syn_mmap_archivo(const char* ruta, int64_t* out_tamano,
                                void** out_handle_plat, void** out_handle_arch) {
    HANDLE hFile = CreateFileA(ruta, GENERIC_READ, FILE_SHARE_READ, NULL,
                                OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hFile == INVALID_HANDLE_VALUE) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: CreateFileA fallo\n");
        return NULL;
    }
    LARGE_INTEGER li;
    GetFileSizeEx(hFile, &li);
    *out_tamano = li.QuadPart;

    HANDLE hMapping = CreateFileMappingA(hFile, NULL, PAGE_READONLY, 0, 0, NULL);
    if (!hMapping) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: CreateFileMappingA fallo\n");
        CloseHandle(hFile);
        return NULL;
    }
    void* ptr = MapViewOfFile(hMapping, FILE_MAP_READ, 0, 0, 0);
    if (!ptr) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: MapViewOfFile fallo\n");
        CloseHandle(hMapping);
        CloseHandle(hFile);
        return NULL;
    }
    *out_handle_plat = hMapping;
    *out_handle_arch = hFile;
    return ptr;
}

static void _syn_munmap_archivo(void* ptr, int64_t tamano,
                                 void* handle_plat, void* handle_arch) {
    (void)tamano;
    if (ptr) UnmapViewOfFile(ptr);
    if (handle_plat) CloseHandle(handle_plat);
    if (handle_arch) CloseHandle(handle_arch);
}
#else
static void* _syn_mmap_archivo(const char* ruta, int64_t* out_tamano,
                                void** out_handle_plat, void** out_handle_arch) {
    int fd = open(ruta, O_RDONLY);
    if (fd < 0) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: open fallo\n");
        return NULL;
    }
    struct stat st;
    if (fstat(fd, &st) < 0) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: fstat fallo\n");
        close(fd);
        return NULL;
    }
    *out_tamano = (int64_t)st.st_size;

    void* ptr = mmap(NULL, (size_t)st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);
    if (ptr == MAP_FAILED) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: mmap fallo\n");
        *out_tamano = 0;
        return NULL;
    }
    *out_handle_plat = NULL;
    *out_handle_arch = NULL;
    return ptr;
}

static void _syn_munmap_archivo(void* ptr, int64_t tamano,
                                 void* handle_plat, void* handle_arch) {
    (void)handle_plat;
    (void)handle_arch;
    if (ptr && tamano > 0) munmap(ptr, (size_t)tamano);
}
#endif

GGUF_Contexto _syn_gguf_abrir(CadenaSegura ruta) {
    GGUF_Contexto ctx;
    memset(&ctx, 0, sizeof(ctx));

    if (ruta.datos == NULL || ruta.longitud <= 0) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: Ruta de archivo invalida\n");
        return ctx;
    }

    char* fname = (char*)malloc((size_t)(ruta.longitud + 1));
    if (!fname) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: Error de memoria al abrir archivo\n");
        return ctx;
    }
    memcpy(fname, ruta.datos, (size_t)ruta.longitud);
    fname[ruta.longitud] = '\0';

    int64_t tamano_mmap = 0;
    void* h_plat = NULL;
    void* h_arch = NULL;
    void* mmap_ptr = _syn_mmap_archivo(fname, &tamano_mmap, &h_plat, &h_arch);
    free(fname);

    if (!mmap_ptr) {
        return ctx;
    }

    if (tamano_mmap < 24) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: Archivo demasiado pequeno\n");
        _syn_munmap_archivo(mmap_ptr, tamano_mmap, h_plat, h_arch);
        return ctx;
    }

    const unsigned char* base = (const unsigned char*)mmap_ptr;
    uint64_t pos = 0;

    // Magic: "GGUF"
    if (base[0] != 'G' || base[1] != 'G' || base[2] != 'U' || base[3] != 'F') {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: Magic GGUF invalido\n");
        _syn_munmap_archivo(mmap_ptr, tamano_mmap, h_plat, h_arch);
        return ctx;
    }
    pos += 4;

    // Version (uint32_t LE)
    uint32_t version_le = *(const uint32_t*)(base + pos);
    pos += 4;

    // Tensor count (uint64_t LE)
    uint64_t tensor_count = *(const uint64_t*)(base + pos);
    pos += 8;

    // Metadata KV count (uint64_t LE)
    uint64_t kv_count = *(const uint64_t*)(base + pos);
    pos += 8;

    // Allocate internal data
    InternalData* idata = (InternalData*)malloc(sizeof(InternalData));
    memset(idata, 0, sizeof(InternalData));
    idata->mmap_ptr = mmap_ptr;
    idata->tamano_mmap = tamano_mmap;
    idata->cantidad_tensores = (int)tensor_count;
    idata->tensores = (TensorInfo*)calloc((size_t)(tensor_count > 0 ? tensor_count : 1), sizeof(TensorInfo));

    // Parse & store metadata KV pairs
    int meta_idx = 0;
    for (uint64_t i = 0; i < kv_count && meta_idx < MAX_METADATOS; i++) {
        if ((int64_t)(pos + 8) > tamano_mmap) goto error;
        uint64_t key_len = *(const uint64_t*)(base + pos);
        pos += 8;
        if ((int64_t)(pos + key_len) > tamano_mmap) goto error;
        // Read key as C string
        char* clave = (char*)malloc((size_t)(key_len + 1));
        memcpy(clave, base + pos, (size_t)key_len);
        clave[key_len] = '\0';
        pos += key_len;
        if ((int64_t)(pos + 4) > tamano_mmap) goto error;
        uint32_t val_type = *(const uint32_t*)(base + pos);
        pos += 4;
        // Read value as string
        uint64_t save_pos = pos;
        char* valor = gguf_value_as_string(base, tamano_mmap, &pos, val_type);
        // If we couldn't convert, restore pos and skip
        if (!valor) {
            pos = save_pos;
            switch (val_type) {
                case 9: { // ARRAY
                    if ((int64_t)(pos + 4) > tamano_mmap) { free(clave); goto error; }
                    uint32_t elem_type = *(const uint32_t*)(base + pos);
                    pos += 4;
                    if ((int64_t)(pos + 8) > tamano_mmap) { free(clave); goto error; }
                    uint64_t arr_len = *(const uint64_t*)(base + pos);
                    pos += 8;
                    // Store array metadata for later access (tokens, scores, merges)
                    if (idata->cantidad_arrays < MAX_ARRAY_METADATOS) {
                        idata->arrays[idata->cantidad_arrays].clave = strdup(clave);
                        idata->arrays[idata->cantidad_arrays].tipo_elemento = (int)elem_type;
                        idata->arrays[idata->cantidad_arrays].cantidad = (int)arr_len;
                        idata->arrays[idata->cantidad_arrays].data_pos = pos;
                        idata->cantidad_arrays++;
                    }
                    for (uint64_t j = 0; j < arr_len; j++) {
                        if ((int64_t)(pos + 1) > tamano_mmap) { free(clave); goto error; }
                        uint64_t e_size = 0;
                        switch (elem_type) {
                            case 0: case 1: case 7: e_size = 1; break;
                            case 2: case 3: e_size = 2; break;
                            case 4: case 5: case 6: e_size = 4; break;
                            case 10: case 11: case 12: e_size = 8; break;
                            case 8:
                                if ((int64_t)(pos + 8) > tamano_mmap) { free(clave); goto error; }
                                e_size = 8 + *(const uint64_t*)(base + pos);
                                break;
                            default: { free(clave); goto error; }
                        }
                        if ((int64_t)(pos + e_size) > tamano_mmap) { free(clave); goto error; }
                        pos += e_size;
                    }
                    valor = strdup("<ARRAY>");
                    break;
                }
                default:
                    free(clave);
                    goto error;
            }
        }
        // Store metadata
        idata->metadatos[meta_idx].clave = clave;
        idata->metadatos[meta_idx].valor = valor;
        // Check if this is the architecture key
        if (clave && strcmp(clave, "general.architecture") == 0 && valor) {
            free(idata->architecture);
            idata->architecture = strdup(valor);
        }
        meta_idx++;
    }
    idata->cantidad_metadatos = meta_idx;

    // Read tensor infos
    for (uint64_t i = 0; i < tensor_count; i++) {
        TensorInfo* ti = &idata->tensores[i];

        if ((int64_t)(pos + 8) > tamano_mmap) goto error;
        uint64_t name_len = *(const uint64_t*)(base + pos);
        pos += 8;

        if ((int64_t)(pos + name_len) > tamano_mmap) goto error;
        ti->nombre = (char*)malloc((size_t)(name_len + 1));
        memcpy(ti->nombre, base + pos, (size_t)name_len);
        ti->nombre[name_len] = '\0';
        pos += name_len;

        if ((int64_t)(pos + 4) > tamano_mmap) goto error;
        ti->n_dimensiones = (int)(*(const uint32_t*)(base + pos));
        pos += 4;

        int ndims = ti->n_dimensiones < 4 ? ti->n_dimensiones : 4;
        for (int d = 0; d < ndims; d++) {
            if ((int64_t)(pos + 8) > tamano_mmap) goto error;
            ti->dimensiones[d] = *(const uint64_t*)(base + pos);
            pos += 8;
        }
        for (int d = ndims; d < ti->n_dimensiones; d++) {
            if ((int64_t)(pos + 8) > tamano_mmap) goto error;
            pos += 8;
        }

        if ((int64_t)(pos + 4) > tamano_mmap) goto error;
        ti->tipo = (int)(*(const uint32_t*)(base + pos));
        pos += 4;

        if ((int64_t)(pos + 8) > tamano_mmap) goto error;
        ti->offset = *(const uint64_t*)(base + pos);
        pos += 8;
    }

    // Build hash table from tensor names
    for (int i = 0; i < (int)tensor_count; i++) {
        uint32_t h = fnv1a_hash(idata->tensores[i].nombre) & (HASH_TAM - 1);
        EntradaHash* entry = (EntradaHash*)malloc(sizeof(EntradaHash));
        if (!entry) goto error;
        entry->indice_tensor = (uint32_t)i;
        entry->siguiente = idata->tabla_hash[h];
        idata->tabla_hash[h] = entry;
    }

    // Calculate aligned tensor data base offset
    uint64_t data_base = (pos + MEM_ALIGN - 1) & ~(uint64_t)(MEM_ALIGN - 1);
    idata->tensor_data_base_offset = data_base;

    // Fill context
    ctx.es_valido = 1;
    ctx.version = (int)version_le;
    ctx.cantidad_tensores = (int)tensor_count;
    ctx.datos_mmap = mmap_ptr;
    ctx.tamano_total = (int)tamano_mmap;
    ctx.tamano_mmap = (int)tamano_mmap;
    ctx.handle_plataforma = h_plat;
    ctx.handle_archivo = h_arch;
    ctx.datos_internos = idata;

    return ctx;

error:
    fprintf(stderr, "ESCAPA_DEL_ALCANCE: Error de parseo GGUF\n");
    if (idata) {
        if (idata->tensores) {
            for (int i = 0; i < idata->cantidad_tensores; i++) {
                free(idata->tensores[i].nombre);
            }
            free(idata->tensores);
        }
        for (int i = 0; i < HASH_TAM; i++) {
            EntradaHash* e = idata->tabla_hash[i];
            while (e) {
                EntradaHash* next = e->siguiente;
                free(e);
                e = next;
            }
        }
        for (int i = 0; i < idata->cantidad_metadatos; i++) {
            free(idata->metadatos[i].clave);
            free(idata->metadatos[i].valor);
        }
        free(idata->architecture);
        free(idata);
    }
    _syn_munmap_archivo(mmap_ptr, tamano_mmap, h_plat, h_arch);
    return ctx;
}

void _syn_gguf_cerrar(void* datos_mmap, int tamano_mmap,
                       void* handle_plataforma, void* handle_archivo) {
    _syn_munmap_archivo(datos_mmap, (int64_t)tamano_mmap,
                         handle_plataforma, handle_archivo);
}

void _syn_gguf_cerrar_contex(GGUF_Contexto ctx) {
    if (ctx.datos_internos) {
        InternalData* idata = (InternalData*)ctx.datos_internos;
        if (idata->tensores) {
            for (int i = 0; i < idata->cantidad_tensores; i++) {
                free(idata->tensores[i].nombre);
            }
            free(idata->tensores);
        }
        for (int i = 0; i < HASH_TAM; i++) {
            EntradaHash* e = idata->tabla_hash[i];
            while (e) {
                EntradaHash* next = e->siguiente;
                free(e);
                e = next;
            }
        }
        for (int i = 0; i < idata->cantidad_metadatos; i++) {
            free(idata->metadatos[i].clave);
            free(idata->metadatos[i].valor);
        }
        for (int i = 0; i < idata->cantidad_arrays; i++) {
            free(idata->arrays[i].clave);
        }
        free(idata->architecture);
        free(idata);
    }
    _syn_munmap_archivo(ctx.datos_mmap, (int64_t)ctx.tamano_mmap,
                         ctx.handle_plataforma, ctx.handle_archivo);
}

static ArrayMetaEntry* _gguf_buscar_arreglo(void* datos_internos, const char* clave) {
    if (!datos_internos || !clave) return NULL;
    InternalData* idata = (InternalData*)datos_internos;
    for (int i = 0; i < idata->cantidad_arrays; i++) {
        if (strcmp(idata->arrays[i].clave, clave) == 0) {
            return &idata->arrays[i];
        }
    }
    return NULL;
}

static int _gguf_leer_elemento_string(const unsigned char* base, int64_t size, uint64_t* pos, char** out, int max_len) {
    if ((int64_t)(*pos + 8) > size) return -1;
    uint64_t slen = *(const uint64_t*)(base + *pos);
    *pos += 8;
    if ((int64_t)(*pos + slen) > size) return -1;
    int len = (int)slen;
    if (max_len > 0 && len > max_len) len = max_len;
    *out = (char*)malloc((size_t)(len + 1));
    if (!*out) return -1;
    memcpy(*out, base + *pos, (size_t)len);
    (*out)[len] = '\0';
    *pos += slen;
    return len;
}

// --- GGUF Array accessor functions (used by model loader) ---

int _syn_gguf_arreglo_cantidad(void* datos_internos, const char* clave) {
    ArrayMetaEntry* arr = _gguf_buscar_arreglo(datos_internos, clave);
    return arr ? arr->cantidad : -1;
}

int _syn_gguf_arreglo_tipo(void* datos_internos, const char* clave) {
    ArrayMetaEntry* arr = _gguf_buscar_arreglo(datos_internos, clave);
    return arr ? arr->tipo_elemento : -1;
}

CadenaSegura _syn_gguf_arreglo_string(void* datos_internos, const char* clave, int indice) {
    CadenaSegura result = {0, NULL};
    ArrayMetaEntry* arr = _gguf_buscar_arreglo(datos_internos, clave);
    if (!arr || arr->tipo_elemento != 8 || indice < 0 || indice >= arr->cantidad) return result;
    InternalData* idata = (InternalData*)datos_internos;
    const unsigned char* base = (const unsigned char*)idata->mmap_ptr;
    uint64_t pos = arr->data_pos;
    for (int i = 0; i < indice; i++) {
        uint64_t e_size = 0;
        if ((int64_t)(pos + 8) > idata->tamano_mmap) return result;
        e_size = 8 + *(const uint64_t*)(base + pos);
        if ((int64_t)(pos + e_size) > idata->tamano_mmap) return result;
        pos += e_size;
    }
    char* out = NULL;
    int len = _gguf_leer_elemento_string(base, idata->tamano_mmap, &pos, &out, 0);
    if (len < 0) return result;
    result.longitud = len;
    result.datos = out;
    return result;
}

float _syn_gguf_arreglo_float(void* datos_internos, const char* clave, int indice) {
    ArrayMetaEntry* arr = _gguf_buscar_arreglo(datos_internos, clave);
    if (!arr || indice < 0 || indice >= arr->cantidad) return 0.0f;
    if (arr->tipo_elemento != 6) return 0.0f; // FLOAT32
    InternalData* idata = (InternalData*)datos_internos;
    const unsigned char* base = (const unsigned char*)idata->mmap_ptr;
    uint64_t pos = arr->data_pos;
    const int elem_size = 4;
    pos += (uint64_t)indice * elem_size;
    if ((int64_t)(pos + 4) > idata->tamano_mmap) return 0.0f;
    return *(const float*)(base + pos);
}

int _syn_gguf_arreglo_int(void* datos_internos, const char* clave, int indice) {
    ArrayMetaEntry* arr = _gguf_buscar_arreglo(datos_internos, clave);
    if (!arr || indice < 0 || indice >= arr->cantidad) return 0;
    InternalData* idata = (InternalData*)datos_internos;
    const unsigned char* base = (const unsigned char*)idata->mmap_ptr;
    uint64_t pos = arr->data_pos;
    int elem_size = 0;
    switch (arr->tipo_elemento) {
        case 0: case 1: case 7: elem_size = 1; break;
        case 2: case 3: elem_size = 2; break;
        case 4: case 5: case 6: elem_size = 4; break;
        case 10: case 11: case 12: elem_size = 8; break;
        default: return 0;
    }
    pos += (uint64_t)indice * elem_size;
    if ((int64_t)(pos + elem_size) > idata->tamano_mmap) return 0;
    switch (arr->tipo_elemento) {
        case 0: case 7: return (int)base[pos];
        case 1: return (int)(*(const int8_t*)(base + pos));
        case 2: return (int)(*(const uint16_t*)(base + pos));
        case 3: return (int)(*(const int16_t*)(base + pos));
        case 4: return (int)(*(const uint32_t*)(base + pos));
        case 5: return (int)(*(const int32_t*)(base + pos));
        case 6: return 0; // floats not representable as int
        case 10: return (int)(*(const uint64_t*)(base + pos));
        case 11: return (int)(*(const int64_t*)(base + pos));
        case 12: return (int)(*(const float*)(base + pos)); // float16 treated as 32 in GGUF
        default: return 0;
    }
}

Tensor _syn_gguf_obtener_tensor(void* datos_internos, CadenaSegura nombre) {
    Tensor t;
    memset(&t, 0, sizeof(t));

    if (!datos_internos || nombre.datos == NULL || nombre.longitud <= 0) {
        return t;
    }

    InternalData* idata = (InternalData*)datos_internos;

    char* name_str = (char*)malloc((size_t)(nombre.longitud + 1));
    memcpy(name_str, nombre.datos, (size_t)nombre.longitud);
    name_str[nombre.longitud] = '\0';

    // O(1) hash table lookup
    uint32_t h = fnv1a_hash(name_str) & (HASH_TAM - 1);
    EntradaHash* entry = idata->tabla_hash[h];
    while (entry) {
        TensorInfo* ti = &idata->tensores[entry->indice_tensor];
        if (strcmp(name_str, ti->nombre) == 0) {
            free(name_str);
            // Validate type: only F32 supported
            if (ti->tipo != GGML_TYPE_F32) {
                fprintf(stderr, "ESCAPA_DEL_ALCANCE: Tipo de tensor no soportado "
                        "(tipo=%d, solo F32=0 soportado en esta version)\n", ti->tipo);
                return t;
            }
            if (ti->n_dimensiones >= 2) {
                t.filas = (int)ti->dimensiones[ti->n_dimensiones - 2];
                t.columnas = (int)ti->dimensiones[ti->n_dimensiones - 1];
            } else if (ti->n_dimensiones == 1) {
                t.filas = 1;
                t.columnas = (int)ti->dimensiones[0];
            }
            t.datos = (float*)((unsigned char*)idata->mmap_ptr + idata->tensor_data_base_offset + ti->offset);
            t.es_mapeado = 1;
            return t;
        }
        entry = entry->siguiente;
    }

    free(name_str);
    return t;
}

// Devuelve el valor del metadato como texto, o texto vacio si no existe.
// El puntero apunta a memoria interna (no liberar).
CadenaSegura _syn_gguf_obtener_metadato(void* datos_internos, CadenaSegura clave) {
    if (!datos_internos || clave.datos == NULL || clave.longitud <= 0) {
        return (CadenaSegura){0, ""};
    }
    InternalData* idata = (InternalData*)datos_internos;
    char* key_str = (char*)malloc((size_t)(clave.longitud + 1));
    if (!key_str) return (CadenaSegura){0, ""};
    memcpy(key_str, clave.datos, (size_t)clave.longitud);
    key_str[clave.longitud] = '\0';
    CadenaSegura result = (CadenaSegura){0, ""};
    for (int i = 0; i < idata->cantidad_metadatos; i++) {
        if (strcmp(idata->metadatos[i].clave, key_str) == 0 && idata->metadatos[i].valor) {
            result = (CadenaSegura){.longitud = (int)strlen(idata->metadatos[i].valor), .datos = strdup(idata->metadatos[i].valor)};
            break;
        }
    }
    free(key_str);
    return result;
}

CadenaSegura _syn_gguf_obtener_arquitectura(void* datos_internos) {
    if (!datos_internos) return (CadenaSegura){0, ""};
    InternalData* idata = (InternalData*)datos_internos;
    if (idata->architecture) {
        return (CadenaSegura){.longitud = (int)strlen(idata->architecture), .datos = strdup(idata->architecture)};
    }
    return (CadenaSegura){0, ""};
}

int _syn_leer_byte_desde(void* base, int desplazamiento) {
    return (int)((unsigned char*)base)[desplazamiento];
}

float _syn_sumar_elementos(Tensor t) {
    float suma = 0.0f;
    for (int i = 0; i < (int)(t.filas * t.columnas); i++) {
        suma += t.datos[i];
    }
    return suma;
}

void _syn_fijar_elemento(Tensor t, int indice, float valor) {
    if (t.datos && indice >= 0 && indice < (t.filas * t.columnas)) {
        t.datos[indice] = valor;
    }
}

int _syn_argmax(Tensor t) {
    if (t.datos == NULL || (t.filas * t.columnas) <= 0) return -1;
    int mejor = 0;
    float max_val = t.datos[0];
    int total = t.filas * t.columnas;
    for (int i = 1; i < total; i++) {
        if (t.datos[i] > max_val) {
            max_val = t.datos[i];
            mejor = i;
        }
    }
    return mejor;
}

int _syn_vocab_tamano(void* datos_internos) {
    if (!datos_internos) return 0;
    InternalData* idata = (InternalData*)datos_internos;
    for (int i = 0; i < idata->cantidad_metadatos; i++) {
        if (strcmp(idata->metadatos[i].clave, "vocab_size") == 0 && idata->metadatos[i].valor) {
            return atoi(idata->metadatos[i].valor);
        }
    }
    return 0;
}

CadenaSegura _syn_decodificar_token(void* datos_internos, int token_id) {
    if (!datos_internos || token_id < 0) return (CadenaSegura){0, ""};
    InternalData* idata = (InternalData*)datos_internos;
    char clave[64];
    snprintf(clave, sizeof(clave), "vocab.%d", token_id);
    for (int i = 0; i < idata->cantidad_metadatos; i++) {
        if (strcmp(idata->metadatos[i].clave, clave) == 0 && idata->metadatos[i].valor) {
            return (CadenaSegura){.longitud = (int)strlen(idata->metadatos[i].valor), .datos = strdup(idata->metadatos[i].valor)};
        }
    }
    return (CadenaSegura){0, ""};
}

int _syn_ejecutar_comando(CadenaSegura cmd) {
    if (cmd.datos == NULL || cmd.longitud <= 0) return -1;
    char* cstr = (char*)malloc((size_t)(cmd.longitud + 1));
    if (!cstr) return -1;
    memcpy(cstr, cmd.datos, (size_t)cmd.longitud);
    cstr[cmd.longitud] = '\0';
    int r = system(cstr);
    free(cstr);
    return r;
}

static char* _syn_leer_archivo_como_texto(const char* ruta) {
    FILE* f = fopen(ruta, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    rewind(f);
    if (sz <= 0) { fclose(f); return NULL; }
    char* buf = (char*)malloc((size_t)(sz + 1));
    if (!buf) { fclose(f); return NULL; }
    size_t n = fread(buf, 1, (size_t)sz, f);
    fclose(f);
    buf[n] = '\0';
    return buf;
}

int _syn_escribir_archivo(CadenaSegura ruta, CadenaSegura contenido) {
    if (ruta.datos == NULL || ruta.longitud <= 0) return -1;
    char* ruta_c = (char*)malloc((size_t)(ruta.longitud + 1));
    if (!ruta_c) return -1;
    memcpy(ruta_c, ruta.datos, (size_t)ruta.longitud);
    ruta_c[ruta.longitud] = '\0';
    FILE* f = fopen(ruta_c, "wb");
    if (!f) { free(ruta_c); return -1; }
    if (contenido.datos && contenido.longitud > 0) {
        fwrite(contenido.datos, 1, (size_t)contenido.longitud, f);
    }
    fclose(f);
    free(ruta_c);
    return 0;
}

CadenaSegura _syn_leer_archivo(CadenaSegura ruta) {
    if (ruta.datos == NULL || ruta.longitud <= 0) return (CadenaSegura){0, ""};
    char* ruta_c = (char*)malloc((size_t)(ruta.longitud + 1));
    if (!ruta_c) return (CadenaSegura){0, ""};
    memcpy(ruta_c, ruta.datos, (size_t)ruta.longitud);
    ruta_c[ruta.longitud] = '\0';
    char* contenido = _syn_leer_archivo_como_texto(ruta_c);
    free(ruta_c);
    if (!contenido) return (CadenaSegura){0, ""};
    CadenaSegura res = {.longitud = (int)strlen(contenido), .datos = contenido};
    return res;
}

// ============================================================================
// Phase 8: Model Inference Engine (ModeloContexto)
// ============================================================================

// --- Helper: read metadata value as int ---
static int _meta_entero(void* datos_internos, const char* clave) {
    if (!datos_internos || !clave) return 0;
    InternalData* idata = (InternalData*)datos_internos;
    for (int i = 0; i < idata->cantidad_metadatos; i++) {
        if (idata->metadatos[i].clave && idata->metadatos[i].valor &&
            strcmp(idata->metadatos[i].clave, clave) == 0) {
            return atoi(idata->metadatos[i].valor);
        }
    }
    return 0;
}

static float _meta_decimal(void* datos_internos, const char* clave, float por_defecto) {
    if (!datos_internos || !clave) return por_defecto;
    InternalData* idata = (InternalData*)datos_internos;
    for (int i = 0; i < idata->cantidad_metadatos; i++) {
        if (idata->metadatos[i].clave && idata->metadatos[i].valor &&
            strcmp(idata->metadatos[i].clave, clave) == 0) {
            return (float)atof(idata->metadatos[i].valor);
        }
    }
    return por_defecto;
}

// Convenience macro for building CadenaSegura from a string literal
#define CS(s) ((CadenaSegura){ .longitud = (int)(sizeof(s) - 1), .datos = (s) })

// --- BPE Tokenizer ---

typedef struct {
    int first;
    int second;
    int result;
} BpeMerge;

typedef struct BpeContext {
    int vocab_size;
    char** tokens;          // [vocab_size] token strings
    int num_merges;
    BpeMerge* merges;       // merge rules (sorted by first,second for bsearch)
    int bos_id;
    int eos_id;
} BpeContext;

static int _bpe_merge_cmp(const void* a, const void* b) {
    const BpeMerge* ma = (const BpeMerge*)a;
    const BpeMerge* mb = (const BpeMerge*)b;
    if (ma->first != mb->first) return ma->first - mb->first;
    return ma->second - mb->second;
}

// Look up pair (first, second) in sorted merges; returns result token ID or -1
static int _bpe_buscar_fusion(BpeMerge* merges, int num_merges, int first, int second) {
    BpeMerge key;
    key.first = first;
    key.second = second;
    key.result = -1;
    BpeMerge* found = (BpeMerge*)bsearch(&key, merges, (size_t)num_merges, sizeof(BpeMerge), _bpe_merge_cmp);
    return found ? found->result : -1;
}

// Load tokenizer data from GGUF arrays into a BpeContext
// Caller must free with _bpe_liberar
static BpeContext* _bpe_crear_desde_gguf(void* datos_internos) {
    BpeContext* bpe = (BpeContext*)calloc(1, sizeof(BpeContext));
    if (!bpe) return NULL;

    InternalData* id = (InternalData*)datos_internos;

    // Read vocab size
    int vs = _syn_gguf_arreglo_cantidad(datos_internos, "tokenizer.ggml.tokens");
    if (vs <= 0) {
        // Fallback: try metadata vocab_size
        vs = _syn_vocab_tamano(datos_internos);
        if (vs <= 0) { free(bpe); return NULL; }
        // Create minimal token list from metadata
        bpe->vocab_size = vs;
        bpe->tokens = (char**)calloc((size_t)vs, sizeof(char*));
        for (int i = 0; i < vs; i++) {
            char k[64]; snprintf(k, sizeof(k), "vocab.%d", i);
            for (int j = 0; j < id->cantidad_metadatos; j++) {
                if (id->metadatos[j].clave && id->metadatos[j].valor && strcmp(id->metadatos[j].clave, k) == 0) {
                    bpe->tokens[i] = strdup(id->metadatos[j].valor);
                    break;
                }
            }
            if (!bpe->tokens[i]) {
                char fallback[16]; snprintf(fallback, sizeof(fallback), "[%d]", i);
                bpe->tokens[i] = strdup(fallback);
            }
        }
    } else {
        bpe->vocab_size = vs;
        bpe->tokens = (char**)calloc((size_t)vs, sizeof(char*));
        for (int i = 0; i < vs; i++) {
            CadenaSegura cs = _syn_gguf_arreglo_string(datos_internos, "tokenizer.ggml.tokens", i);
            if (cs.datos) {
                bpe->tokens[i] = (char*)cs.datos; // transfer ownership
            } else {
                char fallback[16]; snprintf(fallback, sizeof(fallback), "[%d]", i);
                bpe->tokens[i] = strdup(fallback);
            }
        }
    }

    // Read merges
    int n_merges = _syn_gguf_arreglo_cantidad(datos_internos, "tokenizer.ggml.merges");
    if (n_merges > 0) {
        bpe->num_merges = n_merges;
        bpe->merges = (BpeMerge*)calloc((size_t)n_merges, sizeof(BpeMerge));

        for (int i = 0; i < n_merges; i++) {
            CadenaSegura ms = _syn_gguf_arreglo_string(datos_internos, "tokenizer.ggml.merges", i);
            if (!ms.datos) continue;

            char* merge_str = (char*)ms.datos;
            char* space = strchr(merge_str, ' ');
            if (!space) { free(merge_str); continue; }

            int first_len = (int)(space - merge_str);
            int second_len = ms.longitud - first_len - 1;
            char* second_start = space + 1;

            int first_id = -1, second_id = -1;
            for (int j = 0; j < vs; j++) {
                if (!bpe->tokens[j]) continue;
                int tlen = (int)strlen(bpe->tokens[j]);
                if (first_id < 0 && tlen == first_len && strncmp(bpe->tokens[j], merge_str, first_len) == 0) {
                    first_id = j;
                }
                if (second_id < 0 && tlen == second_len && strncmp(bpe->tokens[j], second_start, second_len) == 0) {
                    second_id = j;
                }
                if (first_id >= 0 && second_id >= 0) break;
            }

            if (first_id >= 0 && second_id >= 0) {
                bpe->merges[i].first = first_id;
                bpe->merges[i].second = second_id;
            }
            free(merge_str);
        }

        // Determine result token IDs: the merge at index i corresponds to token ID
        // which is the first token whose text is equal to the merge result.
        // In standard BPE, merges are ordered, and the result ID is base_vocab + i.
        // We need to figure out the base vocab size (tokens not produced by merges).
        // Simplest: result ID = index in token list that is not a base character.
        // Actually: we scan tokens from 0..vs-1, and for each merge i, we look for
        // a token whose text contains the concatenation of the two parts.
        // But this is complex. For simplicity, we assume result = base_vocab + i,
        // where base_vocab is the first token index not in {bytes 0..255} or similar.
        
        // More robust: find the first token ID that is not used as a base byte token.
        // For GPT-2 BPE, bytes 0-255 are the base, so merges produce tokens 256+.
        // For SentencePiece, the base might be all single-character tokens.
        // We'll set result = vs - n_merges + i for now (common pattern).
        int base_tokens = vs - n_merges;
        if (base_tokens < 0) base_tokens = 256; // fallback
        for (int i = 0; i < n_merges; i++) {
            bpe->merges[i].result = base_tokens + i;
        }

        // Sort merges by (first, second) for binary search
        qsort(bpe->merges, (size_t)n_merges, sizeof(BpeMerge), _bpe_merge_cmp);
    }

    // Read BOS/EOS from metadata
    bpe->bos_id = 1;  // default
    bpe->eos_id = 2;  // default
    for (int i = 0; i < id->cantidad_metadatos; i++) {
        if (id->metadatos[i].clave && id->metadatos[i].valor) {
            if (strcmp(id->metadatos[i].clave, "tokenizer.ggml.bos_id") == 0)
                bpe->bos_id = atoi(id->metadatos[i].valor);
            else if (strcmp(id->metadatos[i].clave, "tokenizer.ggml.eos_id") == 0)
                bpe->eos_id = atoi(id->metadatos[i].valor);
        }
    }

    return bpe;
}

static void _bpe_liberar(BpeContext* bpe) {
    if (!bpe) return;
    if (bpe->tokens) {
        for (int i = 0; i < bpe->vocab_size; i++) free(bpe->tokens[i]);
        free(bpe->tokens);
    }
    free(bpe->merges);
    free(bpe);
}

// --- BPE encoding helpers ---

// Maximum symbols in a single word being encoded
#define BPE_MAX_SYMBOLS 256

// Linear scan: find merge with smallest rank for a pair
// Returns result token ID or -1 if not mergeable
// Sets *out_rank to the merge rank (index in merge list)
static int _bpe_mejor_fusion(BpeContext* bpe, int first, int second, int* out_rank) {
    if (out_rank) *out_rank = -1;
    int best_rank = bpe->num_merges; // larger than any real rank
    int best_result = -1;
    for (int i = 0; i < bpe->num_merges; i++) {
        if (bpe->merges[i].first == first && bpe->merges[i].second == second) {
            // Check if this merge has a better (smaller) rank
            // Rank is implicitly the index i in standard BPE
            if (i < best_rank) {
                best_rank = i;
                best_result = bpe->merges[i].result;
            }
        }
    }
    if (out_rank) *out_rank = (best_result >= 0) ? best_rank : -1;
    return best_result;
}

// BPE-encode a single word (text with length len)
// Returns malloc'd array of token IDs; *out_len set to number of tokens
static int* _bpe_codificar_palabra(BpeContext* bpe, const char* text, int len, int* out_len) {
    *out_len = 0;
    if (len <= 0) return NULL;

    int syms[BPE_MAX_SYMBOLS];
    int n_syms = 0;

    // Phase 1: map characters to base token IDs
    // Try direct byte lookup first (tokens 0-255 for byte-level BPE)
    for (int i = 0; i < len && n_syms < BPE_MAX_SYMBOLS; i++) {
        unsigned char byte = (unsigned char)text[i];
        if (byte < (unsigned int)bpe->vocab_size && bpe->tokens[byte]) {
            const char* tok_str = bpe->tokens[byte];
            if ((int)strlen(tok_str) == 1 && (unsigned char)tok_str[0] == byte) {
                syms[n_syms++] = byte;
                continue;
            }
        }
        char ch[2] = { text[i], '\0' };
        int found = 0;
        for (int j = 0; j < bpe->vocab_size; j++) {
            if (bpe->tokens[j] && strcmp(bpe->tokens[j], ch) == 0) {
                syms[n_syms++] = j;
                found = 1;
                break;
            }
        }
        if (!found) {
            syms[n_syms++] = 0; // UNK fallback
        }
    }
    if (n_syms == 0) { *out_len = 0; return NULL; }

    // Phase 2: iteratively apply BPE merges (find pair with smallest rank each time)
    while (n_syms > 1) {
        int best_pos = -1;
        int best_rank = bpe->num_merges;
        int best_result = -1;

        for (int i = 0; i < n_syms - 1; i++) {
            int rank = -1;
            int r = _bpe_mejor_fusion(bpe, syms[i], syms[i+1], &rank);
            if (r >= 0 && rank >= 0 && rank < best_rank) {
                best_rank = rank;
                best_result = r;
                best_pos = i;
            }
        }

        if (best_pos < 0) break;

        int new_syms[BPE_MAX_SYMBOLS];
        int new_n = 0;
        for (int i = 0; i < n_syms; ) {
            if (i == best_pos) {
                new_syms[new_n++] = best_result;
                i += 2;
            } else {
                new_syms[new_n++] = syms[i];
                i++;
            }
        }
        n_syms = new_n;
        memcpy(syms, new_syms, (size_t)n_syms * sizeof(int));
    }

    int* result = (int*)malloc((size_t)n_syms * sizeof(int));
    if (!result) { *out_len = 0; return NULL; }
    memcpy(result, syms, (size_t)n_syms * sizeof(int));
    *out_len = n_syms;
    return result;
}

// Split text into words (by whitespace) and BPE-encode each
// Returns malloc'd array of all token IDs; *out_len set
static int* _bpe_codificar_texto(BpeContext* bpe, const char* text, int len, int* out_len) {
    *out_len = 0;
    if (!bpe || !text || len <= 0) return NULL;

    // Simple pre-tokenize: split on whitespace
    // Collect all token IDs in a dynamic array
    int capacity = 64;
    int* all_ids = (int*)malloc((size_t)capacity * sizeof(int));
    int total = 0;

    int i = 0;
    while (i < len) {
        // Skip whitespace
        while (i < len && (text[i] == ' ' || text[i] == '\t' || text[i] == '\n' || text[i] == '\r')) i++;
        if (i >= len) break;

        // Find word end
        int start = i;
        while (i < len && text[i] != ' ' && text[i] != '\t' && text[i] != '\n' && text[i] != '\r') i++;

        // Also split on punctuation (GPT-2 style)
        // For each contiguous segment of the same "type" (letter, digit, punct)
        int wpos = start;
        while (wpos < i) {
            int wstart = wpos;
            char first_c = text[wpos];
            int is_letter = (first_c >= 'a' && first_c <= 'z') || (first_c >= 'A' && first_c <= 'Z');
            int is_digit = (first_c >= '0' && first_c <= '9');
            int is_punct = !is_letter && !is_digit && first_c != ' ';

            // GPT-2 additionally prepends space to non-first words
            // For simplicity, encode directly
            wpos++;
            while (wpos < i) {
                char c = text[wpos];
                int c_letter = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
                int c_digit = (c >= '0' && c <= '9');
                int c_punct = !c_letter && !c_digit && c != ' ';
                if (is_letter && c_letter) { wpos++; continue; }
                if (is_digit && c_digit) { wpos++; continue; }
                if (is_punct && c_punct) { wpos++; continue; }
                break;
            }

            int word_len = wpos - wstart;
            int n_ids = 0;
            int* ids = _bpe_codificar_palabra(bpe, text + wstart, word_len, &n_ids);
            if (ids) {
                // Extend all_ids
                if (total + n_ids > capacity) {
                    capacity = (total + n_ids) * 2;
                    int* tmp = (int*)realloc(all_ids, (size_t)capacity * sizeof(int));
                    if (!tmp) { free(ids); free(all_ids); *out_len = 0; return NULL; }
                    all_ids = tmp;
                }
                memcpy(all_ids + total, ids, (size_t)n_ids * sizeof(int));
                total += n_ids;
                free(ids);
            }
        }
    }

    if (total == 0) { free(all_ids); *out_len = 0; return NULL; }

    *out_len = total;
    return all_ids;
}

// --- ModeloContexto (inference state) ---

#define MODELO_MAX_LAYERS 256
#define MODELO_MAX_SEQ_LEN 4096
#define MODELO_MAX_EMBD 8192
#define MODELO_MAX_FF 32768
#define MODELO_MAX_HEADS 128

typedef struct ModeloContexto {
    void* datos_internos;          // GGUF InternalData*
    void* datos_mmap;
    int tamano_mmap;
    void* handle_plataforma;
    void* handle_archivo;

    int n_layers;
    int n_heads;
    int n_kv_heads;
    int n_embd;
    int n_ff;
    int head_dim;
    float rope_theta;
    int max_seq_len;
    int vocab_size;
    char arch_name[64];

    int n_past;

    float* w_hidden;
    float* w_attn_norm;
    float* w_ffn_norm;
    float* w_q;
    float* w_k;
    float* w_v;
    float* w_attn_out;
    float* w_gate;
    float* w_up;
    float* w_down;
    float* w_scores;

    float* k_cache;
    float* v_cache;
    int kvc_capa_stride;
    int kvc_cabeza_stride;
    int kvc_pos_stride;

    BpeContext* bpe;
    int* ultima_codificacion;
    int ultima_codificacion_len;
} ModeloContexto;

static ModeloContexto* _mc_crear(void) {
    ModeloContexto* mc = (ModeloContexto*)calloc(1, sizeof(ModeloContexto));
    if (!mc) return NULL;
    mc->rope_theta = 10000.0f;
    mc->max_seq_len = MODELO_MAX_SEQ_LEN;

    mc->w_hidden    = (float*)malloc(MODELO_MAX_EMBD * sizeof(float));
    mc->w_attn_norm = (float*)malloc(MODELO_MAX_EMBD * sizeof(float));
    mc->w_ffn_norm  = (float*)malloc(MODELO_MAX_EMBD * sizeof(float));
    mc->w_q         = (float*)malloc(MODELO_MAX_HEADS * 128 * sizeof(float));
    mc->w_k         = (float*)malloc(MODELO_MAX_HEADS * 128 * sizeof(float));
    mc->w_v         = (float*)malloc(MODELO_MAX_HEADS * 128 * sizeof(float));
    mc->w_attn_out  = (float*)malloc(MODELO_MAX_EMBD * sizeof(float));
    mc->w_gate      = (float*)malloc(MODELO_MAX_FF * sizeof(float));
    mc->w_up        = (float*)malloc(MODELO_MAX_FF * sizeof(float));
    mc->w_down      = (float*)malloc(MODELO_MAX_EMBD * sizeof(float));
    mc->w_scores    = (float*)malloc(MODELO_MAX_HEADS * MODELO_MAX_SEQ_LEN * sizeof(float));

    if (!mc->w_hidden || !mc->w_attn_norm || !mc->w_ffn_norm ||
        !mc->w_q || !mc->w_k || !mc->w_v || !mc->w_attn_out ||
        !mc->w_gate || !mc->w_up || !mc->w_down || !mc->w_scores) {
        free(mc->w_hidden); free(mc->w_attn_norm); free(mc->w_ffn_norm);
        free(mc->w_q); free(mc->w_k); free(mc->w_v); free(mc->w_attn_out);
        free(mc->w_gate); free(mc->w_up); free(mc->w_down); free(mc->w_scores);
        free(mc); return NULL;
    }
    return mc;
}

static void _mc_destruir(ModeloContexto* mc) {
    if (!mc) return;
    free(mc->w_hidden); free(mc->w_attn_norm); free(mc->w_ffn_norm);
    free(mc->w_q); free(mc->w_k); free(mc->w_v); free(mc->w_attn_out);
    free(mc->w_gate); free(mc->w_up); free(mc->w_down); free(mc->w_scores);
    free(mc->k_cache); free(mc->v_cache);
    free(mc->ultima_codificacion);
    _bpe_liberar(mc->bpe);
    mc->bpe = NULL;
    if (mc->datos_internos) {
        InternalData* id = (InternalData*)mc->datos_internos;
        if (id->tensores) {
            for (int i = 0; i < id->cantidad_tensores; i++) free(id->tensores[i].nombre);
            free(id->tensores);
        }
        for (int i = 0; i < HASH_TAM; i++) {
            EntradaHash* e = id->tabla_hash[i];
            while (e) { EntradaHash* n = e->siguiente; free(e); e = n; }
        }
        for (int i = 0; i < id->cantidad_metadatos; i++) {
            free(id->metadatos[i].clave);
            free(id->metadatos[i].valor);
        }
        free(id->architecture);
        free(id);
    }
    _syn_munmap_archivo(mc->datos_mmap, (int64_t)mc->tamano_mmap,
                         mc->handle_plataforma, mc->handle_archivo);
    free(mc);
}

static Tensor _vista_tensor(float* datos, int filas, int columnas) {
    Tensor t = { .filas = (uint32_t)filas, .columnas = (uint32_t)columnas, .datos = datos, .es_mapeado = 1 };
    return t;
}

static int _kvc_inicializar(ModeloContexto* mc) {
    if (mc->n_layers <= 0 || mc->n_kv_heads <= 0 || mc->head_dim <= 0 || mc->max_seq_len <= 0) return -1;
    mc->kvc_capa_stride = mc->n_kv_heads * mc->max_seq_len * mc->head_dim;
    mc->kvc_cabeza_stride = mc->max_seq_len * mc->head_dim;
    mc->kvc_pos_stride = mc->head_dim;
    int total = mc->n_layers * mc->kvc_capa_stride;
    mc->k_cache = (float*)calloc((size_t)total, sizeof(float));
    mc->v_cache = (float*)calloc((size_t)total, sizeof(float));
    return (!mc->k_cache || !mc->v_cache) ? -1 : 0;
}

static void _kvc_guardar(ModeloContexto* mc, int capa, const float* k, const float* v) {
    int lo = capa * mc->kvc_capa_stride;
    int po = mc->n_past * mc->kvc_pos_stride;
    for (int h = 0; h < mc->n_kv_heads; h++) {
        int ho = h * mc->kvc_cabeza_stride;
        memcpy(mc->k_cache + lo + ho + po, k + h * mc->head_dim, (size_t)mc->head_dim * sizeof(float));
        memcpy(mc->v_cache + lo + ho + po, v + h * mc->head_dim, (size_t)mc->head_dim * sizeof(float));
    }
}

static Tensor _kvc_vista(ModeloContexto* mc, float* cache, int capa, int head) {
    return _vista_tensor(cache + capa * mc->kvc_capa_stride + head * mc->kvc_cabeza_stride,
                         mc->n_past, mc->head_dim);
}

static void _rope_mh(float* data, int n_heads, int hd, int pos, float theta) {
    for (int h = 0; h < n_heads; h++) {
        int off = h * hd;
        for (int i = 0; i < hd; i += 2) {
            float f = 1.0f / powf(theta, (float)i / (float)hd);
            float c = cosf((float)pos * f), s = sinf((float)pos * f);
            float x0 = data[off + i], x1 = data[off + i + 1];
            data[off + i] = x0 * c - x1 * s;
            data[off + i + 1] = x0 * s + x1 * c;
        }
    }
}

#define TENSOR(n) _syn_gguf_obtener_tensor(mc->datos_internos, CS(n))
static Tensor _modelo_evaluar_token(ModeloContexto* mc, int token_id) {
    Tensor logits = { .filas = 1, .columnas = (uint32_t)mc->vocab_size, .datos = NULL, .es_mapeado = 0 };
    int E = mc->n_embd, H = mc->n_heads, KH = mc->n_kv_heads, HD = mc->head_dim;
    int FF = mc->n_ff, NP = mc->n_past, NL = mc->n_layers;

    Tensor w_emb = TENSOR("token_embd.weight");
    Tensor w_out = TENSOR("output.weight");
    Tensor w_out_norm = TENSOR("output_norm.weight");
    if (!w_emb.datos) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: token_embd.weight NO ENCONTRADO\n"); return logits; }
    if (!w_out.datos) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: output.weight NO ENCONTRADO\n"); return logits; }

    Tensor hid = _vista_tensor(mc->w_hidden, 1, E);
    _syn_extraer_fila(hid, w_emb, token_id);

    char name[128];
    for (int l = 0; l < NL; l++) {
        snprintf(name, sizeof(name), "blk.%d.attn_norm.weight", l);
        Tensor w_an = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.attn_q.weight", l);
        Tensor w_q = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.attn_k.weight", l);
        Tensor w_k = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.attn_v.weight", l);
        Tensor w_v = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.attn_output.weight", l);
        Tensor w_ao = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.ffn_norm.weight", l);
        Tensor w_fn = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.ffn_gate.weight", l);
        Tensor w_gg = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.ffn_down.weight", l);
        Tensor w_fd = TENSOR(name);
        snprintf(name, sizeof(name), "blk.%d.ffn_up.weight", l);
        Tensor w_fu = TENSOR(name);

        if (!w_an.datos || !w_q.datos) continue;

        // Pre-attention norm
        Tensor an = _vista_tensor(mc->w_attn_norm, 1, E);
        _syn_rmsnorm(an, hid, w_an, 1e-5f);

        // Q/K/V projections
        Tensor qp = _vista_tensor(mc->w_q, 1, H * HD);
        _syn_multiplicar_matrices_transpuesta_b(an, w_q, qp);
        Tensor kp = _vista_tensor(mc->w_k, 1, KH * HD);
        _syn_multiplicar_matrices_transpuesta_b(an, w_k, kp);
        Tensor vp = _vista_tensor(mc->w_v, 1, KH * HD);
        _syn_multiplicar_matrices_transpuesta_b(an, w_v, vp);

        // RoPE
        _rope_mh(mc->w_q, H, HD, NP, mc->rope_theta);
        _rope_mh(mc->w_k, KH, HD, NP, mc->rope_theta);

        // KV cache store
        _kvc_guardar(mc, l, mc->w_k, mc->w_v);

        // Attention
        int G = H / KH;
        float iscale = 1.0f / sqrtf((float)HD);
        memset(mc->w_attn_out, 0, (size_t)E * sizeof(float));

        for (int g = 0; g < G; g++) {
            for (int hk = 0; hk < KH; hk++) {
                int hq = g * KH + hk;
                Tensor kch = _kvc_vista(mc, mc->k_cache, l, hk);
                Tensor vch = _kvc_vista(mc, mc->v_cache, l, hk);

                // scores[0..NP] = Q[hq] @ K_cache[hk]^T  (dot product)
                for (int p = 0; p < NP; p++) {
                    float s = 0;
                    for (int d = 0; d < HD; d++) s += mc->w_q[hq * HD + d] * kch.datos[p * HD + d];
                    mc->w_scores[hq * mc->max_seq_len + p] = s * iscale;
                }

                // softmax
                float mx = -1e30f;
                for (int p = 0; p < NP; p++) { float v = mc->w_scores[hq * mc->max_seq_len + p]; if (v > mx) mx = v; }
                float se = 0;
                for (int p = 0; p < NP; p++) { float e = expf(mc->w_scores[hq * mc->max_seq_len + p] - mx); mc->w_scores[hq * mc->max_seq_len + p] = e; se += e; }
                if (se > 0) for (int p = 0; p < NP; p++) mc->w_scores[hq * mc->max_seq_len + p] /= se;

                // weighted V sum
                for (int d = 0; d < HD; d++) {
                    float sv = 0;
                    for (int p = 0; p < NP; p++) sv += mc->w_scores[hq * mc->max_seq_len + p] * vch.datos[p * HD + d];
                    mc->w_attn_out[hq * HD + d] = sv;
                }
            }
        }

        // Output projection
        Tensor ao = _vista_tensor(mc->w_attn_out, 1, E);
        Tensor aop = _vista_tensor(mc->w_attn_out, 1, E);
        _syn_multiplicar_matrices_transpuesta_b(ao, w_ao, aop);
        for (int i = 0; i < E; i++) mc->w_hidden[i] += mc->w_attn_out[i];

        // Pre-FFN norm
        Tensor fn = _vista_tensor(mc->w_ffn_norm, 1, E);
        _syn_rmsnorm(fn, hid, w_fn, 1e-5f);

        // Gate and up projections
        Tensor gp = _vista_tensor(mc->w_gate, 1, FF);
        _syn_multiplicar_matrices_transpuesta_b(fn, w_gg, gp);
        Tensor up = _vista_tensor(mc->w_up, 1, FF);
        _syn_multiplicar_matrices_transpuesta_b(fn, w_fu, up);
        _syn_silu(gp, gp);
        for (int i = 0; i < FF; i++) mc->w_down[i] = mc->w_gate[i] * mc->w_up[i];

        // Down projection
        Tensor gu = _vista_tensor(mc->w_down, 1, FF);
        Tensor dp = _vista_tensor(mc->w_down, 1, E);
        _syn_multiplicar_matrices_transpuesta_b(gu, w_fd, dp);
        for (int i = 0; i < E; i++) mc->w_hidden[i] += mc->w_down[i];
    }

    // Final norm
    _syn_rmsnorm(hid, hid, w_out_norm, 1e-5f);

    // LM head (logits = hidden @ output.T)
    logits.datos = (float*)malloc((size_t)mc->vocab_size * sizeof(float));
    if (!logits.datos) return logits;
    logits.filas = 1; logits.columnas = (uint32_t)mc->vocab_size;
    for (int j = 0; j < mc->vocab_size; j++) {
        float s = 0;
        for (int k = 0; k < E; k++) s += mc->w_hidden[k] * w_out.datos[j * (uint32_t)E + k];
        logits.datos[j] = s;
    }
    return logits;
}
#undef TENSOR

// --- Sampling ---

static int _sample_argmax(const float* logits, int vs) {
    int b = 0; float mv = logits[0];
    for (int i = 1; i < vs; i++) { if (logits[i] > mv) { mv = logits[i]; b = i; } }
    return b;
}

static int _sample_multinomial(const float* logits, int vs, float temp) {
    if (temp <= 0.0f) return _sample_argmax(logits, vs);
    float it = 1.0f / temp, mx = -1e30f;
    for (int i = 0; i < vs; i++) if (logits[i] > mx) mx = logits[i];
    float* probs = (float*)malloc((size_t)vs * sizeof(float));
    if (!probs) return _sample_argmax(logits, vs);
    float sum = 0;
    for (int i = 0; i < vs; i++) { float p = expf((logits[i] - mx) * it); probs[i] = p; sum += p; }
    if (sum <= 0) { free(probs); return _sample_argmax(logits, vs); }
    for (int i = 0; i < vs; i++) probs[i] /= sum;
    float r = (float)rand() / (float)RAND_MAX, cum = 0;
    for (int i = 0; i < vs; i++) { cum += probs[i]; if (r <= cum) { free(probs); return i; } }
    free(probs); return vs - 1;
}

static void _filtro_top_k(float* logits, int vs, int k) {
    if (k <= 0 || k >= vs) return;
    float* sorted = (float*)malloc((size_t)vs * sizeof(float));
    if (!sorted) return;
    memcpy(sorted, logits, (size_t)vs * sizeof(float));
    for (int i = 0; i < k; i++) { int mi = i; for (int j = i+1; j < vs; j++) if (sorted[j] > sorted[mi]) mi = j; float t = sorted[i]; sorted[i] = sorted[mi]; sorted[mi] = t; }
    float thr = sorted[k-1]; free(sorted);
    for (int i = 0; i < vs; i++) if (logits[i] < thr) logits[i] = -1e30f;
}

static void _filtro_top_p(float* logits, int vs, float p) {
    if (p <= 0.0f || p >= 1.0f) return;
    typedef struct { float v; int i; } PV;
    PV* pa = (PV*)malloc((size_t)vs * sizeof(PV));
    if (!pa) return;
    for (int i = 0; i < vs; i++) { pa[i].v = logits[i]; pa[i].i = i; }
    for (int i = 0; i < vs-1; i++) for (int j = i+1; j < vs; j++) if (pa[j].v > pa[i].v) { PV t = pa[i]; pa[i] = pa[j]; pa[j] = t; }
    float mx = pa[0].v, se = 0;
    for (int i = 0; i < vs; i++) { float e = expf(pa[i].v - mx); pa[i].v = e; se += e; }
    float cum = 0; int cut = vs;
    for (int i = 0; i < vs; i++) { cum += pa[i].v / se; if (cum > p) { cut = i+1; break; } }
    for (int i = cut; i < vs; i++) logits[pa[i].i] = -1e30f;
    free(pa);
}

// --- Public API ---

void* _syn_modelo_cargar(CadenaSegura ruta) {
    GGUF_Contexto gc = _syn_gguf_abrir(ruta);
    if (!gc.es_valido) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: No se pudo abrir modelo GGUF\n"); return NULL; }
    InternalData* id = (InternalData*)gc.datos_internos;
    if (!id || !id->architecture) { _syn_gguf_cerrar_contex(gc); fprintf(stderr, "ESCAPA_DEL_ALCANCE: Modelo sin arquitectura\n"); return NULL; }

    ModeloContexto* mc = _mc_crear();
    if (!mc) { _syn_gguf_cerrar_contex(gc); return NULL; }

    mc->datos_internos = id;
    mc->datos_mmap = gc.datos_mmap;
    mc->tamano_mmap = gc.tamano_mmap;
    mc->handle_plataforma = gc.handle_plataforma;
    mc->handle_archivo = gc.handle_archivo;
    strncpy(mc->arch_name, id->architecture, sizeof(mc->arch_name)-1);

    char* ap = id->architecture;
    char mk[128];
    snprintf(mk, sizeof(mk), "%s.block_count", ap);              mc->n_layers = _meta_entero(id, mk);
    snprintf(mk, sizeof(mk), "%s.attention.head_count", ap);     mc->n_heads = _meta_entero(id, mk);
    snprintf(mk, sizeof(mk), "%s.attention.head_count_kv", ap); mc->n_kv_heads = _meta_entero(id, mk);
    if (mc->n_kv_heads <= 0) mc->n_kv_heads = mc->n_heads;
    snprintf(mk, sizeof(mk), "%s.embedding_length", ap);         mc->n_embd = _meta_entero(id, mk);
    snprintf(mk, sizeof(mk), "%s.feed_forward_length", ap);      mc->n_ff = _meta_entero(id, mk);
    snprintf(mk, sizeof(mk), "%s.rope.freq_base", ap);           mc->rope_theta = _meta_decimal(id, mk, 10000.0f);
    snprintf(mk, sizeof(mk), "%s.context_length", ap);           mc->max_seq_len = _meta_entero(id, mk);
    if (mc->max_seq_len <= 0 || mc->max_seq_len > MODELO_MAX_SEQ_LEN) mc->max_seq_len = MODELO_MAX_SEQ_LEN;
    mc->vocab_size = _syn_vocab_tamano(id);
    mc->head_dim = mc->n_embd / mc->n_heads;

    if (mc->n_layers <= 0 || mc->n_heads <= 0 || mc->n_embd <= 0 || mc->n_ff <= 0 || mc->vocab_size <= 0 ||
        mc->n_embd > MODELO_MAX_EMBD || mc->n_ff > MODELO_MAX_FF ||
        mc->n_heads > MODELO_MAX_HEADS || mc->head_dim > 128 || mc->n_layers > MODELO_MAX_LAYERS) {
        fprintf(stderr, "ESCAPA_DEL_ALCANCE: Parametros de modelo invalidos o demasiado grandes\n");
        _mc_destruir(mc); return NULL;
    }
    if (_kvc_inicializar(mc) != 0) { _mc_destruir(mc); fprintf(stderr, "ESCAPA_DEL_ALCANCE: Error KV cache\n"); return NULL; }

    // Load tokenizer
    mc->bpe = _bpe_crear_desde_gguf(id);
    if (!mc->bpe) {
        fprintf(stderr, "AVISO: No se pudo cargar tokenizer BPE\n");
    }

    mc->n_past = 0;
    return mc;
}

void _syn_modelo_cerrar(void* ctx) { _mc_destruir((ModeloContexto*)ctx); }

Tensor _syn_modelo_evaluar(void* ctx, int token_id) {
    if (!ctx) return (Tensor){0,0,NULL,0};
    ModeloContexto* mc = (ModeloContexto*)ctx;
    if (mc->n_past >= mc->max_seq_len) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: max seq len\n"); return (Tensor){0,0,NULL,0}; }
    Tensor logits = _modelo_evaluar_token(mc, token_id);
    mc->n_past++;
    return logits;
}

int _syn_modelo_generar(void* ctx, int token_id, float temperature, int top_k, float top_p) {
    if (!ctx) return -1;
    Tensor logits = _syn_modelo_evaluar(ctx, token_id);
    if (!logits.datos || logits.columnas <= 0) return -1;
    int vs = (int)logits.columnas;
    float* lc = (float*)malloc((size_t)vs * sizeof(float));
    if (!lc) { free(logits.datos); return -1; }
    memcpy(lc, logits.datos, (size_t)vs * sizeof(float));
    free(logits.datos);
    if (top_k > 0) _filtro_top_k(lc, vs, top_k);
    if (top_p > 0.0f && top_p < 1.0f) _filtro_top_p(lc, vs, top_p);
    int tok = _sample_multinomial(lc, vs, temperature);
    free(lc);
    return tok;
}

int _syn_modelo_n_past(void* ctx) { return ctx ? ((ModeloContexto*)ctx)->n_past : 0; }

void _syn_modelo_reiniciar(void* ctx) {
    if (!ctx) return;
    ModeloContexto* mc = (ModeloContexto*)ctx;
    mc->n_past = 0;
    if (mc->k_cache) memset(mc->k_cache, 0, (size_t)(mc->n_layers * mc->kvc_capa_stride) * sizeof(float));
    if (mc->v_cache) memset(mc->v_cache, 0, (size_t)(mc->n_layers * mc->kvc_capa_stride) * sizeof(float));
}

// Convenience: decode a token given a model context (extracts datos_internos)
CadenaSegura _syn_modelo_decodificar_token(void* ctx, int token_id) {
    if (!ctx) return (CadenaSegura){0, ""};
    ModeloContexto* mc = (ModeloContexto*)ctx;
    // Prefer BPE token table
    if (mc->bpe && token_id >= 0 && token_id < mc->bpe->vocab_size && mc->bpe->tokens[token_id]) {
        return (CadenaSegura){.longitud = (int)strlen(mc->bpe->tokens[token_id]), .datos = strdup(mc->bpe->tokens[token_id])};
    }
    return _syn_decodificar_token(mc->datos_internos, token_id);
}

int _syn_modelo_vocab_tamano(void* ctx) {
    if (!ctx) return 0;
    ModeloContexto* mc = (ModeloContexto*)ctx;
    if (mc->bpe) return mc->bpe->vocab_size;
    return _syn_vocab_tamano(mc->datos_internos);
}

// Encode text using BPE tokenizer from model context
// Result cached in model context; subsequent calls to _syn_modelo_codificar_obtener retrieve tokens
// Returns token count (0 if error or no BPE available)
int _syn_modelo_codificar_contar(void* ctx, CadenaSegura texto) {
    if (!ctx || !texto.datos || texto.longitud <= 0) return 0;
    ModeloContexto* mc = (ModeloContexto*)ctx;
    if (!mc->bpe) return 0;

    // Free previous encoding
    free(mc->ultima_codificacion);
    mc->ultima_codificacion = NULL;
    mc->ultima_codificacion_len = 0;

    // Convert to null-terminated
    char* cstr = (char*)malloc((size_t)(texto.longitud + 1));
    if (!cstr) return 0;
    memcpy(cstr, texto.datos, (size_t)texto.longitud);
    cstr[texto.longitud] = '\0';

    int out_len = 0;
    int* ids = _bpe_codificar_texto(mc->bpe, cstr, texto.longitud, &out_len);
    free(cstr);

    if (ids) {
        mc->ultima_codificacion = ids;
        mc->ultima_codificacion_len = out_len;
    }
    return mc->ultima_codificacion_len;
}

// Get token ID at index from the last encoding (must call _syn_modelo_codificar_contar first)
// Returns token ID or -1 if index out of range
int _syn_modelo_codificar_obtener(void* ctx, int indice) {
    if (!ctx) return -1;
    ModeloContexto* mc = (ModeloContexto*)ctx;
    if (!mc->ultima_codificacion || indice < 0 || indice >= mc->ultima_codificacion_len) return -1;
    return mc->ultima_codificacion[indice];
}

// --- Oracle: end-to-end text generation from prompt ---

// Generate text from a prompt auto-regressively.
// Returns malloc'd string of generated text (caller must free with _syn_texto_liberar).
// Stops at EOS token or max_tokens.
CadenaSegura _syn_modelo_generar_texto(void* ctx, CadenaSegura prompt, int max_tokens, float temperature, int top_k, float top_p) {
    if (!ctx || !prompt.datos || prompt.longitud <= 0) return (CadenaSegura){0, NULL};
    ModeloContexto* mc = (ModeloContexto*)ctx;
    if (!mc->bpe) return (CadenaSegura){0, NULL};

    // Encode prompt
    int n_prompt = _syn_modelo_codificar_contar(ctx, prompt);
    if (n_prompt <= 0) return (CadenaSegura){0, NULL};

    // Prompt processing: feed each token
    _syn_modelo_reiniciar(ctx);
    for (int i = 0; i < n_prompt; i++) {
        int tok = _syn_modelo_codificar_obtener(ctx, i);
        if (tok < 0) break;
        Tensor logits = _syn_modelo_evaluar(ctx, tok);
        if (!logits.datos) break;
        free(logits.datos);
    }

    // Auto-regressive generation
    int last_tok = 0;
    // Start with a pre-allocated output buffer
    int out_cap = 256;
    int out_len = 0;
    char* out_buf = (char*)malloc((size_t)out_cap);
    if (!out_buf) return (CadenaSegura){0, NULL};
    out_buf[0] = '\0';

    for (int i = 0; i < max_tokens; i++) {
        last_tok = _syn_modelo_generar(ctx, last_tok, temperature, top_k, top_p);
        if (last_tok < 0 || last_tok == mc->bpe->eos_id) break;

        // Decode token
        CadenaSegura tok_str = _syn_modelo_decodificar_token(ctx, last_tok);
        if (!tok_str.datos) continue;

        // Append to output buffer; handle escaping for special chars
        // Replace </s> and similar control tokens with empty
        int skip = 0;
        if (tok_str.longitud == 1 && (unsigned char)tok_str.datos[0] < 32) skip = 1;
        if (!skip && tok_str.longitud > 0) {
            // Grow buffer if needed
            if ((size_t)(out_len + tok_str.longitud + 1) > (size_t)out_cap) {
                out_cap = (out_len + tok_str.longitud + 1) * 2;
                char* tmp = (char*)realloc(out_buf, (size_t)out_cap);
                if (!tmp) { free(out_buf); free((void*)tok_str.datos); return (CadenaSegura){0, NULL}; }
                out_buf = tmp;
            }
            memcpy(out_buf + out_len, tok_str.datos, (size_t)tok_str.longitud);
            out_len += tok_str.longitud;
            out_buf[out_len] = '\0';
        }
        free((void*)tok_str.datos);
    }

    if (out_len == 0) { free(out_buf); return (CadenaSegura){0, NULL}; }
    return (CadenaSegura){ .longitud = out_len, .datos = out_buf };
}

// --- Oracle: in-process Synapse compilation via helper script ---

// State for last compilation result
static char* _cached_codigo_c = NULL;
static char* _cached_error_comp = NULL;
static int _cached_error_linea = 0;

// Free cached compilation state
static void _liberar_cache_compilacion(void) {
    free(_cached_codigo_c); _cached_codigo_c = NULL;
    free(_cached_error_comp); _cached_error_comp = NULL;
    _cached_error_linea = 0;
}

// Simple JSON string value extractor: finds "key":"value" or "key": "value" 
// Returns malloc'd string or NULL if not found
static char* _json_extract_string(const char* json, const char* key) {
    if (!json || !key) return NULL;
    // Build search pattern: "key":
    char* pattern = (char*)malloc((size_t)(strlen(key) + 5));
    if (!pattern) return NULL;
    sprintf(pattern, "\"%s\"", key);
    char* start = strstr(json, pattern);
    free(pattern);
    if (!start) return NULL;
    start = strchr(start + strlen(key) + 2, '"');
    if (!start) return NULL;
    start++; // skip opening quote
    char* end = strchr(start, '"');
    if (!end) return NULL;
    int len = (int)(end - start);
    if (len <= 0) return NULL;
    char* val = (char*)malloc((size_t)(len + 1));
    if (!val) return NULL;
    memcpy(val, start, (size_t)len);
    val[len] = '\0';
    // Unescape JSON strings
    // Handle \n, \t, \", \\ etc.
    char* src = val;
    char* dst = val;
    while (*src) {
        if (*src == '\\' && *(src+1)) {
            src++;
            switch (*src) {
                case 'n': *dst++ = '\n'; break;
                case 't': *dst++ = '\t'; break;
                case 'r': *dst++ = '\r'; break;
                case '"': *dst++ = '"'; break;
                case '\\': *dst++ = '\\'; break;
                default: *dst++ = '\\'; *dst++ = *src; break;
            }
        } else {
            *dst++ = *src;
        }
        src++;
    }
    *dst = '\0';
    return val;
}

// Extract boolean value from JSON: "key":true or "key": false
static int _json_extract_bool(const char* json, const char* key) {
    if (!json || !key) return 0;
    char* pattern = (char*)malloc((size_t)(strlen(key) + 10));
    if (!pattern) return 0;
    sprintf(pattern, "\"%s\": true", key);
    int found = (strstr(json, pattern) != NULL);
    if (!found) {
        sprintf(pattern, "\"%s\":true", key);
        found = (strstr(json, pattern) != NULL);
    }
    free(pattern);
    return found;
}

// Extract integer from JSON: "key":123
static int _json_extract_int(const char* json, const char* key) {
    if (!json || !key) return 0;
    char* pattern = (char*)malloc((size_t)(strlen(key) + 5));
    if (!pattern) return 0;
    sprintf(pattern, "\"%s\"", key);
    char* start = strstr(json, pattern);
    free(pattern);
    if (!start) return 0;
    start = strchr(start, ':');
    if (!start) return 0;
    start++;
    while (*start == ' ') start++;
    if (*start < '0' || *start > '9') return 0;
    return atoi(start);
}

// Compile Synapse source code and store result in cached state.
// Returns 0 on success (generated C code available via _syn_obtener_codigo_generado),
// or -1 on error (error info via _syn_obtener_error_compilacion / _syn_obtener_linea_error).
int _syn_compilar_codigo(CadenaSegura fuente) {
    _liberar_cache_compilacion();
    if (!fuente.datos || fuente.longitud <= 0) {
        _cached_error_comp = strdup("Fuente vacia");
        return -1;
    }

    // Write source to temp file
    const char* temp_syn = "oraculo_temp.syn";
    FILE* f = fopen(temp_syn, "wb");
    if (!f) { _cached_error_comp = strdup("No se pudo crear archivo temporal"); return -1; }
    fwrite(fuente.datos, 1, (size_t)fuente.longitud, f);
    fclose(f);

    // Build command: python _compilar_helper.py oraculo_temp.syn
    // Use _popen on Windows, popen on Unix
    char cmd[512];
    snprintf(cmd, sizeof(cmd), "py -3 _compilar_helper.py \"%s\" 2>nul", temp_syn);

    FILE* pipe = _popen(cmd, "r");
    if (!pipe) {
        _cached_error_comp = strdup("No se pudo ejecutar compilador");
        remove(temp_syn);
        return -1;
    }

    // Read all output
    char json_buf[65536];
    size_t json_len = 0;
    char line[4096];
    while (fgets(line, sizeof(line), pipe)) {
        size_t llen = strlen(line);
        if (json_len + llen < sizeof(json_buf) - 1) {
            memcpy(json_buf + json_len, line, llen);
            json_len += llen;
        }
    }
    json_buf[json_len] = '\0';
    _pclose(pipe);
    remove(temp_syn);

    if (json_len == 0) {
        _cached_error_comp = strdup("Sin respuesta del compilador");
        return -1;
    }

    // Parse JSON response
    int exito = _json_extract_bool(json_buf, "exito");
    if (exito) {
        _cached_codigo_c = _json_extract_string(json_buf, "codigo_c");
        if (!_cached_codigo_c) {
            _cached_error_comp = strdup("Respuesta JSON mal formada");
            return -1;
        }
        return 0;
    } else {
        // Extract first error
        _cached_error_comp = _json_extract_string(json_buf, "mensaje");
        _cached_error_linea = _json_extract_int(json_buf, "linea");
        // If the above fails (array of errors), try simpler extraction
        if (!_cached_error_comp) {
            // Fallback: extract from first error object in array
            char* err_start = strstr(json_buf, "\"mensaje\"");
            if (err_start) {
                // Find the value after "mensaje":
                char* val_start = strchr(err_start, ':');
                if (val_start) {
                    val_start++;
                    while (*val_start == ' ') val_start++;
                    if (*val_start == '"') {
                        val_start++;
                        char* val_end = strchr(val_start, '"');
                        if (val_end) {
                            int elen = (int)(val_end - val_start);
                            _cached_error_comp = (char*)malloc((size_t)(elen + 1));
                            if (_cached_error_comp) {
                                memcpy(_cached_error_comp, val_start, (size_t)elen);
                                _cached_error_comp[elen] = '\0';
                            }
                        }
                    }
                }
            }
            // Try to extract line number
            _cached_error_linea = _json_extract_int(json_buf, "linea");
        }
        if (!_cached_error_comp) _cached_error_comp = strdup("Error de compilacion desconocido");
        return -1;
    }
}

// Get the generated C code from the last successful compilation
CadenaSegura _syn_obtener_codigo_generado(void) {
    if (!_cached_codigo_c) return (CadenaSegura){0, ""};
    return (CadenaSegura){ .longitud = (int)strlen(_cached_codigo_c), .datos = strdup(_cached_codigo_c) };
}

// Get the error message from the last failed compilation
CadenaSegura _syn_obtener_error_compilacion(void) {
    if (!_cached_error_comp) return (CadenaSegura){0, ""};
    return (CadenaSegura){ .longitud = (int)strlen(_cached_error_comp), .datos = strdup(_cached_error_comp) };
}

// Get the error line number from the last failed compilation
int _syn_obtener_linea_error(void) {
    return _cached_error_linea;
}

// --- Oracle: extract code block from model output ---

// Extract the first Synapse code block from text (between ```synapse and ``` or just ``` ... ```)
// Returns malloc'd string or NULL if no code block found
CadenaSegura _syn_extraer_bloque_codigo(CadenaSegura texto) {
    if (!texto.datos || texto.longitud <= 0) return (CadenaSegura){0, NULL};

    // Convert to null-terminated for easier parsing
    char* cstr = (char*)malloc((size_t)(texto.longitud + 1));
    if (!cstr) return (CadenaSegura){0, NULL};
    memcpy(cstr, texto.datos, (size_t)texto.longitud);
    cstr[texto.longitud] = '\0';

    char* start = NULL;
    char* end = NULL;

    // Try ```synapse ... ``` first, then ``` ... ```
    char* markers[] = {"```synapse", "```", "```Synapse", "```sinaptico", NULL};
    for (int i = 0; markers[i]; i++) {
        start = strstr(cstr, markers[i]);
        if (start) {
            start += strlen(markers[i]);
            // Skip whitespace/newline after marker
            while (*start == ' ' || *start == '\t' || *start == '\n' || *start == '\r') start++;
            end = strstr(start, "```");
            if (end) break;
        }
    }

    if (!start || !end) {
        // No code block found; try to use the whole text (strip leading/trailing whitespace)
        start = cstr;
        while (*start == ' ' || *start == '\t' || *start == '\n' || *start == '\r') start++;
        if (*start == '\0') { free(cstr); return (CadenaSegura){0, NULL}; }
        end = cstr + texto.longitud;
        // Trim trailing whitespace
        while (end > start && (*(end-1) == ' ' || *(end-1) == '\t' || *(end-1) == '\n' || *(end-1) == '\r')) end--;
        if (end <= start) { free(cstr); return (CadenaSegura){0, NULL}; }
    }

    int len = (int)(end - start);
    char* code = (char*)malloc((size_t)(len + 1));
    if (!code) { free(cstr); return (CadenaSegura){0, NULL}; }
    memcpy(code, start, (size_t)len);
    code[len] = '\0';
    free(cstr);
    return (CadenaSegura){ .longitud = len, .datos = code };
}
