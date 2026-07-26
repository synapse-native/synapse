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
extern void cerrar(Canal canal);
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
extern void cerrar_canal(CanalConcurrencia* canal);
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

int assert_verdadero(int condicion, CadenaSegura nombre);
int assert_falso(int condicion, CadenaSegura nombre);
int assert_igual(int actual, int esperado, CadenaSegura nombre);
int assert_diferente(int actual, int esperado, CadenaSegura nombre);
int principal(void);

int assert_verdadero(int condicion, CadenaSegura nombre) {
    if (condicion) {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("  [PASS] "), .datos = "  [PASS] " }, nombre));
        int _ret_18 = 0;
        return _ret_18;
    }
    escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("  [FAIL] "), .datos = "  [FAIL] " }, nombre));
    int _ret_20 = 1;
    return _ret_20;
}

int assert_falso(int condicion, CadenaSegura nombre) {
    if ((!condicion)) {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("  [PASS] "), .datos = "  [PASS] " }, nombre));
        int _ret_25 = 0;
        return _ret_25;
    }
    escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("  [FAIL] "), .datos = "  [FAIL] " }, nombre));
    int _ret_27 = 1;
    return _ret_27;
}

int assert_igual(int actual, int esperado, CadenaSegura nombre) {
    if ((actual == esperado)) {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("  [PASS] "), .datos = "  [PASS] " }, nombre));
        int _ret_32 = 0;
        return _ret_32;
    }
    CadenaSegura a_str = entero_a_texto(actual);
    CadenaSegura e_str = entero_a_texto(esperado);
    CadenaSegura msg = concat(concat(concat(concat((CadenaSegura){ .longitud = (int)strlen("  [FAIL] "), .datos = "  [FAIL] " }, nombre), (CadenaSegura){ .longitud = (int)strlen(" — esperado: "), .datos = " — esperado: " }), e_str), concat((CadenaSegura){ .longitud = (int)strlen(", actual: "), .datos = ", actual: " }, a_str));
    escribir_linea(msg);
    int _ret_37 = 1;
    _syn_texto_liberar(msg);
    _syn_texto_liberar(e_str);
    _syn_texto_liberar(a_str);
    return _ret_37;
}

int assert_diferente(int actual, int esperado, CadenaSegura nombre) {
    if ((actual != esperado)) {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("  [PASS] "), .datos = "  [PASS] " }, nombre));
        int _ret_42 = 0;
        return _ret_42;
    }
    escribir_linea(concat(concat((CadenaSegura){ .longitud = (int)strlen("  [FAIL] "), .datos = "  [FAIL] " }, nombre), (CadenaSegura){ .longitud = (int)strlen(" — no debía ser igual"), .datos = " — no debía ser igual" }));
    int _ret_44 = 1;
    return _ret_44;
}

int principal(void) {
    int fallos;
    int contador;
    int resultado;
    int resultado2;
    _simd_detectar();
    fallos = 0;
    escribir_linea((CadenaSegura){ .longitud = (int)strlen("[TEST] test_core_math — Pruebas aritméticas básicas"), .datos = "[TEST] test_core_math — Pruebas aritméticas básicas" });
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    fallos = (fallos + assert_igual((1 + 1), 2, (CadenaSegura){ .longitud = (int)strlen("1 + 1 == 2"), .datos = "1 + 1 == 2" }));
    fallos = (fallos + assert_igual((5 - 3), 2, (CadenaSegura){ .longitud = (int)strlen("5 - 3 == 2"), .datos = "5 - 3 == 2" }));
    fallos = (fallos + assert_igual((4 * 3), 12, (CadenaSegura){ .longitud = (int)strlen("4 * 3 == 12"), .datos = "4 * 3 == 12" }));
    fallos = (fallos + assert_igual((10 / 2), 5, (CadenaSegura){ .longitud = (int)strlen("10 / 2 == 5"), .datos = "10 / 2 == 5" }));
    fallos = (fallos + assert_igual(((1 + 2) * 3), 9, (CadenaSegura){ .longitud = (int)strlen("(1 + 2) * 3 == 9"), .datos = "(1 + 2) * 3 == 9" }));
    fallos = (fallos + assert_igual(((-5) + 3), (-2), (CadenaSegura){ .longitud = (int)strlen("-5 + 3 == -2"), .datos = "-5 + 3 == -2" }));
    fallos = (fallos + assert_igual(((-5) * (-2)), 10, (CadenaSegura){ .longitud = (int)strlen("-5 * -2 == 10"), .datos = "-5 * -2 == 10" }));
    fallos = (fallos + assert_igual((5 - 10), (-5), (CadenaSegura){ .longitud = (int)strlen("5 - 10 == -5"), .datos = "5 - 10 == -5" }));
    fallos = (fallos + assert_igual((0 + 0), 0, (CadenaSegura){ .longitud = (int)strlen("0 + 0 == 0"), .datos = "0 + 0 == 0" }));
    fallos = (fallos + assert_igual((5 * 0), 0, (CadenaSegura){ .longitud = (int)strlen("5 * 0 == 0"), .datos = "5 * 0 == 0" }));
    fallos = (fallos + assert_igual((0 / 1), 0, (CadenaSegura){ .longitud = (int)strlen("0 / 1 == 0"), .datos = "0 / 1 == 0" }));
    fallos = (fallos + assert_verdadero((3 > 2), (CadenaSegura){ .longitud = (int)strlen("3 > 2"), .datos = "3 > 2" }));
    fallos = (fallos + assert_verdadero((2 < 3), (CadenaSegura){ .longitud = (int)strlen("2 < 3"), .datos = "2 < 3" }));
    fallos = (fallos + assert_verdadero((3 >= 3), (CadenaSegura){ .longitud = (int)strlen("3 >= 3"), .datos = "3 >= 3" }));
    fallos = (fallos + assert_verdadero((4 <= 5), (CadenaSegura){ .longitud = (int)strlen("4 <= 5"), .datos = "4 <= 5" }));
    fallos = (fallos + assert_falso((3 > 5), (CadenaSegura){ .longitud = (int)strlen("3 > 5 es falso"), .datos = "3 > 5 es falso" }));
    fallos = (fallos + assert_falso((2 == 3), (CadenaSegura){ .longitud = (int)strlen("2 == 3 es falso"), .datos = "2 == 3 es falso" }));
    fallos = (fallos + assert_diferente(2, 3, (CadenaSegura){ .longitud = (int)strlen("2 != 3"), .datos = "2 != 3" }));
    fallos = (fallos + assert_verdadero(1, (CadenaSegura){ .longitud = (int)strlen("verdadero es verdadero"), .datos = "verdadero es verdadero" }));
    fallos = (fallos + assert_falso(0, (CadenaSegura){ .longitud = (int)strlen("falso es falso"), .datos = "falso es falso" }));
    fallos = (fallos + assert_verdadero((!0), (CadenaSegura){ .longitud = (int)strlen("no falso es verdadero"), .datos = "no falso es verdadero" }));
    fallos = (fallos + assert_falso((!1), (CadenaSegura){ .longitud = (int)strlen("no verdadero es falso"), .datos = "no verdadero es falso" }));
    contador = 0;
    while ((contador < 3)) {
        contador = (contador + 1);
    }
    fallos = (fallos + assert_igual(contador, 3, (CadenaSegura){ .longitud = (int)strlen("mientras: contador llega a 3"), .datos = "mientras: contador llega a 3" }));
    resultado = 0;
    if ((10 > 5)) {
        resultado = 1;
    }
    else {
        resultado = 2;
    }
    fallos = (fallos + assert_igual(resultado, 1, (CadenaSegura){ .longitud = (int)strlen("si: rama correcta (10 > 5)"), .datos = "si: rama correcta (10 > 5)" }));
    resultado2 = 0;
    if ((3 > 10)) {
        resultado2 = 1;
    }
    else {
        resultado2 = 2;
    }
    fallos = (fallos + assert_igual(resultado2, 2, (CadenaSegura){ .longitud = (int)strlen("si: rama sino correcta (3 > 10)"), .datos = "si: rama sino correcta (3 > 10)" }));
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    if ((fallos == 0)) {
        escribir_linea((CadenaSegura){ .longitud = (int)strlen("  [OK] Todos los tests pasaron."), .datos = "  [OK] Todos los tests pasaron." });
    }
    else {
        escribir_linea(concat((CadenaSegura){ .longitud = (int)strlen("  [FAIL] "), .datos = "  [FAIL] " }, entero_a_texto(fallos)));
    }
    escribir_linea((CadenaSegura){ .longitud = (int)strlen(""), .datos = "" });
    int _ret_76 = fallos;
    return _ret_76;
}

int main(int argc, char** argv) {
    _g_argc = argc;
    _g_argv = argv;
    pool_init(POOL_BLOQUES, TAMANO_BLOQUE);
    return principal();
    synapse_esperar_hilos();
    pool_destroy();
    return 0;
}