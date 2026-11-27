// FASE 24 — Test de Math (Manual 3 §12.1)
// TDD: este test ES la especificación. Si las funciones _syn_*
// no existen, el test NO compila — eso es correcto.
//
// Manual 3 §12.1: lib/math.syq — Matemáticas y estadísticas
// Comando: pytest tests/syquex/test_math.py -v
// Criterio: precisión razonable para funciones de punto flotante

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include "synapse_rt_types.h"
#include "runtime/core/math.h"

static int passed = 0;
static int failed = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { printf("  [FAIL] %s\n", msg); failed++; } \
    else { printf("  [PASS] %s\n", msg); passed++; } \
} while(0)

#define EPSILON 0.001f
#define APPROX_EQ(a, b) ((float)fabs((double)((a) - (b))) < EPSILON)

int main(void) {
    setbuf(stdout, NULL);

    // === 1. Potencia ===
    printf("=== 1. Potencia ===\n");
    CHECK(APPROX_EQ(_syn_potencia(2.0f, 10.0f), 1024.0f), "potencia(2,10) == 1024");
    CHECK(APPROX_EQ(_syn_potencia(3.0f, 3.0f), 27.0f), "potencia(3,3) == 27");
    CHECK(APPROX_EQ(_syn_potencia(5.0f, 0.0f), 1.0f), "potencia(5,0) == 1");
    CHECK(APPROX_EQ(_syn_potencia(2.0f, -1.0f), 0.5f), "potencia(2,-1) == 0.5");

    // === 2. Raíz cuadrada ===
    printf("=== 2. Raiz cuadrada ===\n");
    CHECK(APPROX_EQ(_syn_sqrt(4.0f), 2.0f), "sqrt(4) == 2");
    CHECK(APPROX_EQ(_syn_sqrt(9.0f), 3.0f), "sqrt(9) == 3");
    CHECK(APPROX_EQ(_syn_sqrt(0.0f), 0.0f), "sqrt(0) == 0");
    CHECK(APPROX_EQ(_syn_sqrt(2.0f), 1.414f), "sqrt(2) ~ 1.414");

    // === 3. Seno ===
    printf("=== 3. Seno ===\n");
    CHECK(APPROX_EQ(_syn_sen(0.0f), 0.0f), "sen(0) == 0");
    CHECK(APPROX_EQ(_syn_sen(1.5708f), 1.0f), "sen(pi/2) ~ 1");

    // === 4. Coseno ===
    printf("=== 4. Coseno ===\n");
    CHECK(APPROX_EQ(_syn_cos(0.0f), 1.0f), "cos(0) == 1");
    CHECK(APPROX_EQ(_syn_cos(3.14159f), -1.0f), "cos(pi) ~ -1");

    // === 5. Tangente ===
    printf("=== 5. Tangente ===\n");
    CHECK(APPROX_EQ(_syn_tan(0.0f), 0.0f), "tan(0) == 0");
    CHECK(APPROX_EQ(_syn_tan(0.7854f), 1.0f), "tan(pi/4) ~ 1");

    // === 6. Redondeo ===
    printf("=== 6. Redondeo ===\n");
    CHECK(_syn_round(1.5f) == 2, "round(1.5) == 2");
    CHECK(_syn_round(1.4f) == 1, "round(1.4) == 1");
    CHECK(_syn_round(-1.5f) == -2, "round(-1.5) == -2");
    CHECK(_syn_round(0.0f) == 0, "round(0) == 0");

    // === 7. Techo ===
    printf("=== 7. Techo ===\n");
    CHECK(_syn_ceil(1.1f) == 2, "ceil(1.1) == 2");
    CHECK(_syn_ceil(2.0f) == 2, "ceil(2.0) == 2");
    CHECK(_syn_ceil(-1.1f) == -1, "ceil(-1.1) == -1");

    // === 8. Piso ===
    printf("=== 8. Piso ===\n");
    CHECK(_syn_floor(1.9f) == 1, "floor(1.9) == 1");
    CHECK(_syn_floor(2.0f) == 2, "floor(2.0) == 2");
    CHECK(_syn_floor(-1.1f) == -2, "floor(-1.1) == -2");

    // === 9. Logaritmo natural ===
    printf("=== 9. Logaritmo natural ===\n");
    CHECK(APPROX_EQ(_syn_log(1.0f), 0.0f), "log(1) == 0");
    CHECK(APPROX_EQ(_syn_log(2.71828f), 1.0f), "log(e) ~ 1");
    CHECK(APPROX_EQ(_syn_log(10.0f), 2.3026f), "log(10) ~ 2.3026");

    printf("\n=== RESULTADO: %d passed, %d failed ===\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
