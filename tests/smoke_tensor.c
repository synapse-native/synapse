// salida_metal.c - Generado por Synapse Compilador
// Lenguaje: Synapse v1.0 (#lang: es)
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <string.h>
#include <assert.h>

typedef struct { int longitud; const char* datos; } CadenaSegura;

typedef struct { uint32_t filas; uint32_t columnas; float* datos; int es_mapeado; } Tensor;

typedef struct { FILE* stream; int es_valido; int es_virtual; const char* virtual_data; int virtual_len; } Canal;

#define nulo ((void*)0)
#define verdadero 1
#define falso 0

// --- OO AST node types ---
struct Token;
struct Nodo;
struct ListaNodo;
struct Programa;
struct Identificador;
struct LiteralNumero;
struct LiteralCadena;
struct OpBinaria;
struct OpUnaria;
struct LlamadaFuncion;
struct ExprAccesoCampo;
struct AsignacionVariable;
struct AsignacionCampo;
struct SentenciaSi;
struct SentenciaMientras;
struct SentenciaRetornar;
struct SentenciaExpr;
struct LogLlamada;
struct Parametro;
struct ListaParametro;
struct DefinicionFuncion;
struct DefinicionEstructura;
struct SentenciaRomper;
struct SentenciaSiguiente;
struct SentenciaLanzar;
struct SentenciaRecuperar;
struct SentenciaEscuchar;
struct ExprTensor;
struct ExprIndice;
struct ArgumentoTransferido;
struct SentenciaImportar;
struct ImportarC;
struct DeclaracionExterna;
struct DeclaracionVariable;
struct BloqueInseguro;
struct ExprObtenerDireccion;
struct ExprDereferencia;

typedef struct Token { int tipo; CadenaSegura lexema; int linea; int columna; } Token;
typedef struct Nodo { CadenaSegura tipo; } Nodo;
typedef struct ListaNodo { struct Nodo* cabeza; struct ListaNodo* cola; } ListaNodo;
typedef struct Programa { CadenaSegura tipo; struct ListaNodo* sentencias; } Programa;

#define POOL_BLOQUES 64
#define TAMANO_BLOQUE 4096

#define _GEN_TMP_SIZE (4096)
#include "librerias/embedded_libs.h"

char _gen_tmp_buf[4096];

char _G_emit_buf[1048576];
int _G_emit_pos = 0;
FILE* _G_fp = NULL;

extern int _G_indent;

const char* _G_mt(const char* st);
void _G_vest(struct DefinicionEstructura* n);

#define TAG_OK 0
#define TAG_ERR 1
#define TAG_ALGUNO 0
#define TAG_NINGUNO 1

// --- Helpers de serialización primitiva ---
static inline void* _synapse_box_int(int v) { return (void*)(intptr_t)v; }
static inline int _synapse_unbox_int(void* p) { return (int)(intptr_t)p; }
static inline void* _synapse_box_float(float v) {
    float* _p = (float*)malloc(sizeof(float));
    if (!_p) { fprintf(stderr, "ESCAPA_DEL_ALCANCE: malloc fallo\\n"); exit(1); }
    *_p = v;
    return (void*)_p;
}
static inline float _synapse_unbox_float(void* p) {
    float _v = *(float*)p;
    free(p);
    return _v;
}

extern void pool_init(uint32_t total_blocks, uint32_t block_size);
extern void pool_free(void* ptr);
extern void* pool_alloc(size_t size);
extern void pool_destroy(void);
extern void escribir(CadenaSegura contenido);
extern void escribir_linea(CadenaSegura contenido);
extern CadenaSegura leer_linea(void);
extern Canal abrir(CadenaSegura ruta, CadenaSegura modo);
extern CadenaSegura leer(Canal canal);
extern void cerrar_archivo(Canal canal);
extern Tensor crear_tensor(int filas, int columnas);
extern Tensor suma_tensor(Tensor a, Tensor b);
extern Tensor producto_punto(Tensor a, Tensor b);
extern Tensor relu(Tensor a);
extern Tensor reserva(int tamano);
extern void libera(Tensor bloque);
extern Tensor suma(Tensor a, Tensor b);
extern Tensor producto(Tensor a, Tensor b);
extern int texto_a_entero(CadenaSegura str);
extern float texto_a_decimal(CadenaSegura str);
extern CadenaSegura decimal_a_texto(float n);
extern CadenaSegura entero_a_texto(int n);
extern void synapse_lanzar_hilo(void* (*fn)(void*), void* arg);
extern void synapse_esperar_hilos(void);
extern void _syn_texto_liberar(CadenaSegura s);

typedef struct { int es_ok; union {
void* ok_valor; const char* err_mensaje;
} datos; } Resultado_T;
typedef struct CanalConcurrencia CanalConcurrencia;
extern CanalConcurrencia* canal_crear(uint32_t capacidad);
extern void canal_enviar(CanalConcurrencia* canal, void* paquete);
extern void* canal_recibir(CanalConcurrencia* canal);
extern void canal_destruir(CanalConcurrencia* canal);
extern void cerrar(CanalConcurrencia* canal);
// --- Deteccion SIMD unificada (delegada al runtime synapse_rt.o) ---
extern void _simd_detectar(void);

// --- Contratos (requiere/garantiza) ---
#ifdef SYNAPSE_RELEASE
#define assert_contrato(expr, msg) ((void)0)
#else
#define assert_contrato(expr, msg) \
    do { if (!(expr)) { \
        fprintf(stderr, "CONTRATO: %s en %%s:%%d\\n", \
                msg, __FILE__, __LINE__); \
        exit(1); }} while(0)
#endif

int _g_argc;
char** _g_argv;
int _argc() { return _g_argc; }

CadenaSegura _argv(int i) {
    if (i < 0 || i >= _g_argc) return (CadenaSegura){0, ""};
    return (CadenaSegura){ .longitud = (int)strlen(_g_argv[i]), .datos = _g_argv[i] };
}

void salir(int codigo) { exit(codigo); }

CadenaSegura concat(CadenaSegura a, CadenaSegura b) {
    int _tl = a.longitud + b.longitud;
    char* _buf = (char*)malloc(_tl + 1);
    if (!_buf) { fprintf(stderr,"Error: malloc fallo en concat()\\n"); exit(1); }
    memcpy(_buf, a.datos, a.longitud);
    memcpy(_buf + a.longitud, b.datos, b.longitud);
    _buf[_tl] = 0;
    return (CadenaSegura){_tl, _buf};
}

int ahora_ms(void);
void dormir_ms(int ms);
void llenar_tensor_constante(Tensor t, float valor);
Tensor multiplicar_matrices(Tensor a, Tensor b);
void extraer_fila(Tensor salida, Tensor tabla_embeddings, int indice_token);
void rmsnorm(Tensor salida, Tensor entrada, Tensor peso_normalizacion, float epsilon);
void silu(Tensor salida, Tensor entrada);
void rope(Tensor tensor, int posicion_token, int head_dim, float theta_base);
void softmax_escalado(Tensor tensor, float factor_escala);
void multiplicar_matrices_transpuesta_b(Tensor a, Tensor b, Tensor salida);
void fijar_elemento(Tensor t, int indice, float valor);
int simd_disponible(void);
CadenaSegura simd_tipo(void);
Tensor simd_multiplicar_matrices(Tensor a, Tensor b);
void simd_rmsnorm(Tensor salida, Tensor entrada, Tensor peso_normalizacion, float epsilon);
void simd_silu(Tensor salida, Tensor entrada);
void simd_softmax_escalado(Tensor tensor, float factor_escala);
void simd_llenar_tensor_constante(Tensor t, float valor);
void simd_multiplicar_matrices_transpuesta_b(Tensor a, Tensor b, Tensor salida);
int validar_resultado(Tensor esperado, Tensor obtenido, CadenaSegura nombre);
void principal(void);

extern int _syn_ahora_ms(void);
extern void _syn_dormir_ms(int ms);
int ahora_ms(void) {
    int _ret_15 = _syn_ahora_ms();
    return _ret_15;
}

void dormir_ms(int ms) {
    _syn_dormir_ms(ms);
    return;
}

extern void _syn_llenar_tensor_constante(Tensor t, float valor);
extern Tensor _syn_multiplicar_matrices(Tensor a, Tensor b);
extern void _syn_extraer_fila(Tensor salida, Tensor tabla_embeddings, int indice_token);
extern void _syn_rmsnorm(Tensor salida, Tensor entrada, Tensor peso_normalizacion, float epsilon);
extern void _syn_silu(Tensor salida, Tensor entrada);
extern void _syn_rope(Tensor tensor, int posicion_token, int head_dim, float theta_base);
extern void _syn_softmax_escalado(Tensor tensor, float factor_escala);
extern void _syn_multiplicar_matrices_transpuesta_b(Tensor a, Tensor b, Tensor salida);
extern void _syn_fijar_elemento(Tensor t, int indice, float valor);
void llenar_tensor_constante(Tensor t, float valor) {
    _syn_llenar_tensor_constante(t, valor);
    return;
}

Tensor multiplicar_matrices(Tensor a, Tensor b) {
    Tensor _ret_28 = _syn_multiplicar_matrices(a, b);
    return _ret_28;
}

void extraer_fila(Tensor salida, Tensor tabla_embeddings, int indice_token) {
    _syn_extraer_fila(salida, tabla_embeddings, indice_token);
    return;
}

void rmsnorm(Tensor salida, Tensor entrada, Tensor peso_normalizacion, float epsilon) {
    _syn_rmsnorm(salida, entrada, peso_normalizacion, epsilon);
    return;
}

void silu(Tensor salida, Tensor entrada) {
    _syn_silu(salida, entrada);
    return;
}

void rope(Tensor tensor, int posicion_token, int head_dim, float theta_base) {
    _syn_rope(tensor, posicion_token, head_dim, theta_base);
    return;
}

void softmax_escalado(Tensor tensor, float factor_escala) {
    _syn_softmax_escalado(tensor, factor_escala);
    return;
}

void multiplicar_matrices_transpuesta_b(Tensor a, Tensor b, Tensor salida) {
    _syn_multiplicar_matrices_transpuesta_b(a, b, salida);
    return;
}

void fijar_elemento(Tensor t, int indice, float valor) {
    _syn_fijar_elemento(t, indice, valor);
    return;
}

extern int _syn_simd_disponible(void);
extern CadenaSegura _syn_simd_tipo(void);
extern Tensor _syn_simd_multiplicar_matrices(Tensor a, Tensor b);
extern void _syn_simd_rmsnorm(Tensor salida, Tensor entrada, Tensor peso_normalizacion, float epsilon);
extern void _syn_simd_silu(Tensor salida, Tensor entrada);
extern void _syn_simd_softmax_escalado(Tensor tensor, float factor_escala);
extern void _syn_simd_llenar_tensor_constante(Tensor t, float valor);
extern void _syn_simd_multiplicar_matrices_transpuesta_b(Tensor a, Tensor b, Tensor salida);
int simd_disponible(void) {
    int _ret_32 = (_syn_simd_disponible() == 1);
    return _ret_32;
}

CadenaSegura simd_tipo(void) {
    CadenaSegura _ret_35 = _syn_simd_tipo();
    return _ret_35;
}

Tensor simd_multiplicar_matrices(Tensor a, Tensor b) {
    Tensor _ret_38 = _syn_simd_multiplicar_matrices(a, b);
    return _ret_38;
}

void simd_rmsnorm(Tensor salida, Tensor entrada, Tensor peso_normalizacion, float epsilon) {
    _syn_simd_rmsnorm(salida, entrada, peso_normalizacion, epsilon);
    return;
}

void simd_silu(Tensor salida, Tensor entrada) {
    _syn_simd_silu(salida, entrada);
    return;
}

void simd_softmax_escalado(Tensor tensor, float factor_escala) {
    _syn_simd_softmax_escalado(tensor, factor_escala);
    return;
}

void simd_llenar_tensor_constante(Tensor t, float valor) {
    _syn_simd_llenar_tensor_constante(t, valor);
    return;
}

void simd_multiplicar_matrices_transpuesta_b(Tensor a, Tensor b, Tensor salida) {
    _syn_simd_multiplicar_matrices_transpuesta_b(a, b, salida);
    return;
}

#define DIM (256)
#define ITERACIONES (5)
#define TOLERANCIA (0.001f)
int validar_resultado(Tensor esperado, Tensor obtenido, CadenaSegura nombre) {
    int idx;
    int diff;
    if (((esperado.filas != obtenido.filas) || (esperado.columnas != obtenido.columnas))) {
        printf("%s %s %s\
", (CadenaSegura){ .longitud = (int)strlen("ERROR: "), .datos = "ERROR: " }.datos, nombre.datos, (CadenaSegura){ .longitud = (int)strlen(" - dimensiones diferentes"), .datos = " - dimensiones diferentes" }.datos);
        int _ret_24 = 1;
        return _ret_24;
    }
    int fila = 0;
    int col = 0;
    while ((fila < esperado.filas)) {
        col = 0;
        while ((col < esperado.columnas)) {
            idx = ((fila * esperado.columnas) + col);
            diff = (esperado.datos[idx] - obtenido.datos[idx]);
            if ((diff < 0)) {
                diff = (-diff);
            }
            if ((diff > TOLERANCIA)) {
                printf("%s %s %s %d %s %p %s %p %s %d %s %d\
", (CadenaSegura){ .longitud = (int)strlen("ERROR: "), .datos = "ERROR: " }.datos, nombre.datos, (CadenaSegura){ .longitud = (int)strlen(" - diff="), .datos = " - diff=" }.datos, diff, (CadenaSegura){ .longitud = (int)strlen(" en ["), .datos = " en [" }.datos, fila, (CadenaSegura){ .longitud = (int)strlen(","), .datos = "," }.datos, col, (CadenaSegura){ .longitud = (int)strlen("]: "), .datos = "]: " }.datos, esperado.datos[idx], (CadenaSegura){ .longitud = (int)strlen(" vs "), .datos = " vs " }.datos, obtenido.datos[idx]);
                int _ret_36 = 1;
                return _ret_36;
            }
            col = (col + 1);
        }
        fila = (fila + 1);
    }
    int _ret_39 = 0;
    return _ret_39;
}

void principal(void) {
    Tensor a;
    Tensor b;
    int inicio;
    Tensor c;
    int fin;
    int diff;
    Tensor a2;
    Tensor b2;
    Tensor c2;
    Tensor a_val;
    Tensor b_val;
    Tensor c_ref;
    Tensor a_val2;
    Tensor b_val2;
    Tensor c_simd;
    int err;
    int speedup_x100;
    int entero_part;
    int dec_part;
    _simd_detectar();
    printf("%s\
", (CadenaSegura){ .longitud = (int)strlen("=== Benchmark Tensorial: Escalar vs SIMD ==="), .datos = "=== Benchmark Tensorial: Escalar vs SIMD ===" }.datos);
    printf("%s %d %s %d %s %d\
", (CadenaSegura){ .longitud = (int)strlen("Dimension: "), .datos = "Dimension: " }.datos, DIM, (CadenaSegura){ .longitud = (int)strlen("x"), .datos = "x" }.datos, DIM, (CadenaSegura){ .longitud = (int)strlen(" | Iteraciones: "), .datos = " | Iteraciones: " }.datos, ITERACIONES);
    printf("%s %p %s %s %s\
", (CadenaSegura){ .longitud = (int)strlen("SIMD disponible: "), .datos = "SIMD disponible: " }.datos, simd_disponible(), (CadenaSegura){ .longitud = (int)strlen(" ("), .datos = " (" }.datos, simd_tipo().datos, (CadenaSegura){ .longitud = (int)strlen(")"), .datos = ")" }.datos);
    printf("%s\
", (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }.datos);
    printf("%s\
", (CadenaSegura){ .longitud = (int)strlen("--- Benchmark: multiplicar_matrices (ESCALAR) ---"), .datos = "--- Benchmark: multiplicar_matrices (ESCALAR) ---" }.datos);
    int tiempo_escalar = 9999999;
    int i = 0;
    while ((i < ITERACIONES)) {
        a = crear_tensor(DIM, DIM);
        b = crear_tensor(DIM, DIM);
        llenar_tensor_constante(a, 1.0f);
        llenar_tensor_constante(b, 2.0f);
        inicio = ahora_ms();
        c = multiplicar_matrices(a, b);
        fin = ahora_ms();
        diff = (fin - inicio);
        printf("%s %p %s %p %s\
", (CadenaSegura){ .longitud = (int)strlen("  Iteracion "), .datos = "  Iteracion " }.datos, (i + 1), (CadenaSegura){ .longitud = (int)strlen(": "), .datos = ": " }.datos, diff, (CadenaSegura){ .longitud = (int)strlen(" ms"), .datos = " ms" }.datos);
        if ((diff < tiempo_escalar)) {
            tiempo_escalar = diff;
        }
        i = (i + 1);
    }
    printf("%s %p %s\
", (CadenaSegura){ .longitud = (int)strlen("Mejor tiempo ESCALAR: "), .datos = "Mejor tiempo ESCALAR: " }.datos, tiempo_escalar, (CadenaSegura){ .longitud = (int)strlen(" ms"), .datos = " ms" }.datos);
    printf("%s\
", (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }.datos);
    printf("%s\
", (CadenaSegura){ .longitud = (int)strlen("--- Benchmark: simd_multiplicar_matrices (SIMD) ---"), .datos = "--- Benchmark: simd_multiplicar_matrices (SIMD) ---" }.datos);
    int tiempo_simd = 9999999;
    i = 0;
    while ((i < ITERACIONES)) {
        a2 = crear_tensor(DIM, DIM);
        b2 = crear_tensor(DIM, DIM);
        llenar_tensor_constante(a2, 1.0f);
        llenar_tensor_constante(b2, 2.0f);
        inicio = ahora_ms();
        c2 = simd_multiplicar_matrices(a2, b2);
        fin = ahora_ms();
        diff = (fin - inicio);
        printf("%s %p %s %p %s\
", (CadenaSegura){ .longitud = (int)strlen("  Iteracion "), .datos = "  Iteracion " }.datos, (i + 1), (CadenaSegura){ .longitud = (int)strlen(": "), .datos = ": " }.datos, diff, (CadenaSegura){ .longitud = (int)strlen(" ms"), .datos = " ms" }.datos);
        if ((diff < tiempo_simd)) {
            tiempo_simd = diff;
        }
        i = (i + 1);
    }
    printf("%s %p %s\
", (CadenaSegura){ .longitud = (int)strlen("Mejor tiempo SIMD: "), .datos = "Mejor tiempo SIMD: " }.datos, tiempo_simd, (CadenaSegura){ .longitud = (int)strlen(" ms"), .datos = " ms" }.datos);
    printf("%s\
", (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }.datos);
    printf("%s\
", (CadenaSegura){ .longitud = (int)strlen("--- Validacion de resultados ---"), .datos = "--- Validacion de resultados ---" }.datos);
    a_val = crear_tensor(DIM, DIM);
    b_val = crear_tensor(DIM, DIM);
    llenar_tensor_constante(a_val, 1.0f);
    llenar_tensor_constante(b_val, 2.0f);
    c_ref = multiplicar_matrices(a_val, b_val);
    a_val2 = crear_tensor(DIM, DIM);
    b_val2 = crear_tensor(DIM, DIM);
    llenar_tensor_constante(a_val2, 1.0f);
    llenar_tensor_constante(b_val2, 2.0f);
    c_simd = simd_multiplicar_matrices(a_val2, b_val2);
    err = validar_resultado(c_ref, c_simd, (CadenaSegura){ .longitud = (int)strlen("simd_multiplicar_matrices"), .datos = "simd_multiplicar_matrices" });
    if ((err == 0)) {
        printf("%s\
", (CadenaSegura){ .longitud = (int)strlen("Resultados: CORRECTOS (coinciden escalar y SIMD)"), .datos = "Resultados: CORRECTOS (coinciden escalar y SIMD)" }.datos);
    }
    else {
        printf("%s\
", (CadenaSegura){ .longitud = (int)strlen("ERROR: Resultados NO coinciden!"), .datos = "ERROR: Resultados NO coinciden!" }.datos);
    }
    printf("%s\
", (CadenaSegura){ .longitud = (int)strlen(""), .datos = "" }.datos);
    printf("%s\
", (CadenaSegura){ .longitud = (int)strlen("=== RESULTADOS ==="), .datos = "=== RESULTADOS ===" }.datos);
    printf("%s %p %s\
", (CadenaSegura){ .longitud = (int)strlen("Escalar (mejor): "), .datos = "Escalar (mejor): " }.datos, tiempo_escalar, (CadenaSegura){ .longitud = (int)strlen(" ms"), .datos = " ms" }.datos);
    printf("%s %p %s\
", (CadenaSegura){ .longitud = (int)strlen("SIMD    (mejor): "), .datos = "SIMD    (mejor): " }.datos, tiempo_simd, (CadenaSegura){ .longitud = (int)strlen(" ms"), .datos = " ms" }.datos);
    if (((tiempo_simd < tiempo_escalar) && (tiempo_simd > 0))) {
        speedup_x100 = ((tiempo_escalar * 100) / tiempo_simd);
        entero_part = (speedup_x100 / 100);
        dec_part = (speedup_x100 - (entero_part * 100));
        printf("%s %d %s %d %s\
", (CadenaSegura){ .longitud = (int)strlen("Speedup: "), .datos = "Speedup: " }.datos, entero_part, (CadenaSegura){ .longitud = (int)strlen("."), .datos = "." }.datos, dec_part, (CadenaSegura){ .longitud = (int)strlen("x mas rapido"), .datos = "x mas rapido" }.datos);
    }
    else {
        printf("%s\
", (CadenaSegura){ .longitud = (int)strlen("Speedup: N/A (SIMD no disponible o no mas rapido)"), .datos = "Speedup: N/A (SIMD no disponible o no mas rapido)" }.datos);
    }
    printf("%s\
", (CadenaSegura){ .longitud = (int)strlen("=== Fin del Benchmark ==="), .datos = "=== Fin del Benchmark ===" }.datos);
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    principal();
    synapse_esperar_hilos();
    pool_destroy();
    return 0;
}