// smoke_tensor_runner.c — Benchmark runner: Escalar vs SIMD matrix multiply
// Compilar: gcc -O2 -msse -msse3 -mavx tests/smoke_tensor_runner.c synapse_rt.o -o tests/smoke_tensor.exe -lm -lpthread
// Ejecutar: tests/smoke_tensor.exe
//
// NOTA: Esta es la implementación C del benchmark definido en tests/smoke_tensor.syn

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/time.h>
#endif

// Type definitions (must match synapse_rt.c)
typedef struct { int longitud; const char* datos; } CadenaSegura;
typedef struct { uint32_t filas; uint32_t columnas; float* datos; int es_mapeado; } Tensor;

// Runtime function declarations
extern Tensor crear_tensor(int filas, int columnas);
extern void _syn_llenar_tensor_constante(Tensor t, float valor);
extern Tensor _syn_multiplicar_matrices(Tensor a, Tensor b);
extern Tensor _syn_simd_multiplicar_matrices(Tensor a, Tensor b);
extern int _syn_simd_disponible(void);
extern const char* _syn_simd_tipo(void);
extern CadenaSegura entero_a_texto(int n);
extern CadenaSegura decimal_a_texto(float n);

#ifdef _WIN32
static double now_sec(void) {
    LARGE_INTEGER freq, pc;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&pc);
    return (double)pc.QuadPart / (double)freq.QuadPart;
}
#else
static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}
#endif

#define DIM 256
#define ITERACIONES 5
#define TOLERANCIA 1e-5f

static int validar_resultado(Tensor esperado, Tensor obtenido, const char* nombre) {
    if (esperado.filas != obtenido.filas || esperado.columnas != obtenido.columnas) {
        printf("ERROR: %s - dimensiones diferentes (%ux%u vs %ux%u)\n",
               nombre, esperado.filas, esperado.columnas,
               obtenido.filas, obtenido.columnas);
        return 1;
    }
    uint32_t n = esperado.filas * esperado.columnas;
    for (uint32_t i = 0; i < n; i++) {
        float diff = esperado.datos[i] - obtenido.datos[i];
        if (diff < 0) diff = -diff;
        if (diff > TOLERANCIA) {
            printf("ERROR: %s - diferencia en [%u]: %f vs %f\n",
                   nombre, i, esperado.datos[i], obtenido.datos[i]);
            return 1;
        }
    }
    return 0;
}

int main(void) {
    printf("=== Benchmark Tensorial: Escalar vs SIMD ===\n");
    printf("Dimension: %dx%d | Iteraciones: %d\n", DIM, DIM, ITERACIONES);
    printf("SIMD disponible: %d (%s)\n", _syn_simd_disponible(), _syn_simd_tipo());
    printf("\n");

    // --- Benchmark Escalar ---
    // NOTA: multiplicar_matrices CONSUME ownership de los tensores de entrada
    // (pool_free(a.datos)). Por lo tanto, debemos recrearlos en cada iteracion.
    printf("--- Benchmark: multiplicar_matrices (ESCALAR) ---\n");
    double mejor_escalar = 1e30;
    for (int i = 0; i < ITERACIONES; i++) {
        Tensor a = crear_tensor(DIM, DIM);
        Tensor b = crear_tensor(DIM, DIM);
        _syn_llenar_tensor_constante(a, 1.0f);
        _syn_llenar_tensor_constante(b, 2.0f);

        double t0 = now_sec();
        Tensor c = _syn_multiplicar_matrices(a, b);
        double t1 = now_sec();
        double ms = (t1 - t0) * 1000.0;
        printf("  Iteracion %d: %.2f ms\n", i + 1, ms);
        if (ms < mejor_escalar) mejor_escalar = ms;
    }
    printf("Mejor tiempo ESCALAR: %.2f ms\n", mejor_escalar);
    printf("\n");

    // --- Benchmark SIMD ---
    printf("--- Benchmark: simd_multiplicar_matrices (SIMD) ---\n");
    double mejor_simd = 1e30;
    for (int i = 0; i < ITERACIONES; i++) {
        Tensor a_simd = crear_tensor(DIM, DIM);
        Tensor b_simd = crear_tensor(DIM, DIM);
        _syn_llenar_tensor_constante(a_simd, 1.0f);
        _syn_llenar_tensor_constante(b_simd, 2.0f);

        double t0 = now_sec();
        Tensor c2 = _syn_simd_multiplicar_matrices(a_simd, b_simd);
        double t1 = now_sec();
        double ms = (t1 - t0) * 1000.0;
        printf("  Iteracion %d: %.2f ms\n", i + 1, ms);
        if (ms < mejor_simd) mejor_simd = ms;
    }
    printf("Mejor tiempo SIMD: %.2f ms\n", mejor_simd);
    printf("\n");

    // --- Validacion ---
    // Validation run (fresh matrices for each, since both consume ownership)
    printf("--- Validacion de resultados ---\n");
    int err = 0;
    {
        Tensor a_ref = crear_tensor(DIM, DIM);
        Tensor b_ref = crear_tensor(DIM, DIM);
        _syn_llenar_tensor_constante(a_ref, 1.0f);
        _syn_llenar_tensor_constante(b_ref, 2.0f);
        Tensor cref = _syn_multiplicar_matrices(a_ref, b_ref);

        Tensor a_simd = crear_tensor(DIM, DIM);
        Tensor b_simd = crear_tensor(DIM, DIM);
        _syn_llenar_tensor_constante(a_simd, 1.0f);
        _syn_llenar_tensor_constante(b_simd, 2.0f);
        Tensor csimd = _syn_simd_multiplicar_matrices(a_simd, b_simd);

        err = validar_resultado(cref, csimd, "simd_multiplicar_matrices");
    }
    if (err == 0) {
        printf("Resultados: CORRECTOS (coinciden escalar y SIMD)\n");
    } else {
        printf("ERROR: Resultados NO coinciden!\n");
    }
    printf("\n");

    // --- Reporte ---
    printf("=== RESULTADOS ===\n");
    printf("Escalar (mejor): %.2f ms\n", mejor_escalar);
    printf("SIMD    (mejor): %.2f ms\n", mejor_simd);

    if (mejor_simd < mejor_escalar && mejor_simd > 0) {
        double speedup = mejor_escalar / mejor_simd;
        printf("Speedup: %.2fx mas rapido\n", speedup);
    } else {
        printf("Speedup: N/A (SIMD no disponible o no mas rapido)\n");
    }
    printf("=== Fin del Benchmark ===\n");

    return 0;
}
