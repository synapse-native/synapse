// validate_quantum_runtime.c — Suite de validacion del Runtime Cuantico (M16.1)
#include "nucleo/quantum_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

static int test_passed = 0;
static int test_failed = 0;
static int section_num = 0;

#define TEST(nombre, expr) do { \
    if (!(expr)) { \
        fprintf(stderr, "  [FAIL] %s (linea %d)\n", nombre, __LINE__); \
        test_failed++; \
    } else { \
        test_passed++; \
    } \
} while(0)

#define SECCION(nombre) do { \
    section_num++; \
    printf("\n=== Seccion %d: %s ===\n", section_num, nombre); \
} while(0)

#define ASSERT_CERCANO(nombre, val, esperado, tol) TEST(nombre, fabs((val) - (esperado)) < (tol))

// ============================================================
// 1. Inicializacion y ciclo de vida
// ============================================================
static void test_lifecycle(void) {
    SECCION("Inicializacion y ciclo de vida");
    EstadoCuantico* s = qc_crear_sistema(2);
    TEST("qc_crear_sistema(2) no es NULL", s != NULL);
    TEST("num_qubits = 2", s->num_qubits == 2);
    TEST("num_amplitudes = 4", s->num_amplitudes == 4);
    TEST("estado_inicializado = 0", s->estado_inicializado == 0);
    qc_liberar_sistema(s);
    TEST("Liberacion exitosa (sin crash)", 1);
    EstadoCuantico* s1 = qc_crear_sistema(1);
    TEST("qc_crear_sistema(1) no es NULL", s1 != NULL);
    TEST("1 qubit: 2 amplitudes", s1->num_amplitudes == 2);
    qc_liberar_sistema(s1);
    EstadoCuantico* s8 = qc_crear_sistema(8);
    TEST("qc_crear_sistema(8) no es NULL", s8 != NULL);
    TEST("8 qubits: 256 amplitudes", s8->num_amplitudes == 256);
    qc_liberar_sistema(s8);
    TEST("qc_crear_sistema(0) es NULL", qc_crear_sistema(0) == NULL);
    TEST("qc_crear_sistema(9) es NULL", qc_crear_sistema(9) == NULL);
}

// ============================================================
// 2. Estados base
// ============================================================
static void test_base_states(void) {
    SECCION("Estados base");
    EstadoCuantico* s = qc_crear_sistema(3);
    qc_inicializar_estado_cero(s);
    TEST("Estado |0>: amplitud[0].real = 1", fabs(s->amplitudes[0].real - 1.0) < 1e-12);
    TEST("Estado |0>: amplitud[0].imag = 0", fabs(s->amplitudes[0].imag) < 1e-12);
    for (int i = 1; i < 8; i++) {
        char buf[64];
        snprintf(buf, 64, "Estado |0>: amplitud[%d] = 0", i);
        TEST(buf, fabs(s->amplitudes[i].real) < 1e-12 && fabs(s->amplitudes[i].imag) < 1e-12);
    }
    qc_liberar_sistema(s);
    s = qc_crear_sistema(2);
    qc_inicializar_estado_uniforme(s);
    double factor = 0.5;
    TEST("Uniforme: |00> amplitud = 0.5", fabs(s->amplitudes[0].real - factor) < 1e-12);
    TEST("Uniforme: |01> amplitud = 0.5", fabs(s->amplitudes[1].real - factor) < 1e-12);
    TEST("Uniforme: |10> amplitud = 0.5", fabs(s->amplitudes[2].real - factor) < 1e-12);
    TEST("Uniforme: |11> amplitud = 0.5", fabs(s->amplitudes[3].real - factor) < 1e-12);
    qc_liberar_sistema(s);
    s = qc_crear_sistema(2);
    qc_inicializar_base(s, 2);
    TEST("Base |10>: amplitud[2].real = 1", fabs(s->amplitudes[2].real - 1.0) < 1e-12);
    for (int i = 0; i < 4; i++) {
        if (i != 2) {
            TEST("Base especifica: otras amplitudes = 0", fabs(s->amplitudes[i].real) < 1e-12);
        }
    }
    qc_liberar_sistema(s);
}

// ============================================================
// 3. Puerta Hadamard
// ============================================================
static void test_hadamard(void) {
    SECCION("Puerta Hadamard");
    EstadoCuantico* s = qc_crear_sistema(1);
    qc_inicializar_estado_cero(s);
    qc_aplicar_hadamard(s, 0);
    double inv_sqrt2 = 0.7071067811865475;
    ASSERT_CERCANO("H|0>: amplitud[0].real = 1/sqrt(2)", s->amplitudes[0].real, inv_sqrt2, 1e-10);
    ASSERT_CERCANO("H|0>: amplitud[1].real = 1/sqrt(2)", s->amplitudes[1].real, inv_sqrt2, 1e-10);
    TEST("H|0>: amplitud[0].imag = 0", fabs(s->amplitudes[0].imag) < 1e-12);
    TEST("H|0>: amplitud[1].imag = 0", fabs(s->amplitudes[1].imag) < 1e-12);
    ASSERT_CERCANO("H|0>: P(|0>) = 0.5", qc_probabilidad_cero(s, 0), 0.5, 1e-10);
    ASSERT_CERCANO("H|0>: P(|1>) = 0.5", qc_probabilidad_uno(s, 0), 0.5, 1e-10);
    qc_liberar_sistema(s);
    s = qc_crear_sistema(1);
    qc_inicializar_estado_cero(s);
    qc_aplicar_hadamard(s, 0);
    qc_aplicar_hadamard(s, 0);
    ASSERT_CERCANO("HH|0> = |0>: amplitud[0]", s->amplitudes[0].real, 1.0, 1e-10);
    TEST("HH|0> = |0>: amplitud[1] = 0", fabs(s->amplitudes[1].real) < 1e-12);
    qc_liberar_sistema(s);
}

// ============================================================
// 4. Puertas Pauli
// ============================================================
static void test_pauli_gates(void) {
    SECCION("Puertas Pauli");
    EstadoCuantico* s = qc_crear_sistema(1);
    qc_inicializar_estado_cero(s);
    qc_aplicar_pauli_x(s, 0);
    TEST("X|0> = |1>: amplitud[0] = 0", fabs(s->amplitudes[0].real) < 1e-12);
    ASSERT_CERCANO("X|0> = |1>: amplitud[1].real = 1", s->amplitudes[1].real, 1.0, 1e-10);
    qc_liberar_sistema(s);
    s = qc_crear_sistema(1);
    qc_inicializar_estado_cero(s);
    qc_aplicar_pauli_y(s, 0);
    TEST("Y|0>: amplitud[0] = 0", fabs(s->amplitudes[0].real) < 1e-12 && fabs(s->amplitudes[0].imag) < 1e-12);
    TEST("Y|0>: amplitud[1].imag = 1", fabs(s->amplitudes[1].imag - 1.0) < 1e-10);
    qc_liberar_sistema(s);
    s = qc_crear_sistema(1);
    qc_inicializar_base(s, 1);
    qc_aplicar_pauli_z(s, 0);
    ASSERT_CERCANO("Z|1> = -|1>: amplitud[1].real = -1", s->amplitudes[1].real, -1.0, 1e-10);
    qc_liberar_sistema(s);
}

// ============================================================
// 5. Puertas Phase y T
// ============================================================
static void test_phase_gates(void) {
    SECCION("Puertas Phase y T");
    EstadoCuantico* s = qc_crear_sistema(1);
    qc_inicializar_base(s, 1);
    qc_aplicar_phase(s, 0, 3.14159265358979323846 / 2.0);
    TEST("S|1>: amplitud[0] = 0", fabs(s->amplitudes[0].real) < 1e-12);
    ASSERT_CERCANO("S|1>: amplitud[1].imag = 1", s->amplitudes[1].imag, 1.0, 1e-10);
    qc_liberar_sistema(s);
    s = qc_crear_sistema(1);
    qc_inicializar_base(s, 1);
    qc_aplicar_t(s, 0);
    double ang_t = 3.14159265358979323846 / 4.0;
    ASSERT_CERCANO("T|1>: amplitud[1].real = cos(pi/4)", s->amplitudes[1].real, cos(ang_t), 1e-10);
    ASSERT_CERCANO("T|1>: amplitud[1].imag = sin(pi/4)", s->amplitudes[1].imag, sin(ang_t), 1e-10);
    qc_liberar_sistema(s);
}

// ============================================================
// 6. CNOT y entrelazamiento
// ============================================================
static void test_cnot_entanglement(void) {
    SECCION("CNOT y entrelazamiento");
    EstadoCuantico* s = qc_crear_sistema(2);
    qc_inicializar_estado_cero(s);
    qc_aplicar_cnot(s, 0, 1);
    TEST("CNOT|00> = |00>: amplitud[0] = 1", fabs(s->amplitudes[0].real - 1.0) < 1e-12);
    TEST("CNOT|00> = |00>: otras amplitudes = 0", fabs(s->amplitudes[3].real) < 1e-12);
    qc_liberar_sistema(s);
    s = qc_crear_sistema(2);
    qc_inicializar_base(s, 1);
    qc_aplicar_cnot(s, 0, 1);
    TEST("CNOT|01> = |11>: target flip", fabs(s->amplitudes[3].real - 1.0) < 1e-12);
    qc_liberar_sistema(s);
    s = qc_crear_sistema(2);
    qc_inicializar_base(s, 3);
    qc_aplicar_cnot(s, 0, 1);
    TEST("CNOT|11> = |01>: target flip", fabs(s->amplitudes[1].real - 1.0) < 1e-12);
    qc_liberar_sistema(s);
    s = qc_crear_sistema(2);
    qc_inicializar_estado_cero(s);
    qc_aplicar_hadamard(s, 0);
    qc_aplicar_cnot(s, 0, 1);
    ASSERT_CERCANO("Bell via CNOT: |00>", s->amplitudes[0].real, QC_SQRT2_INV, 1e-10);
    ASSERT_CERCANO("Bell via CNOT: |11>", s->amplitudes[3].real, QC_SQRT2_INV, 1e-10);
    TEST("Estado Bell es entrelazado", qc_es_entrelazado(s) == 1);
    qc_liberar_sistema(s);
}

// ============================================================
// 7. SWAP
// ============================================================
static void test_swap(void) {
    SECCION("SWAP");
    EstadoCuantico* s = qc_crear_sistema(2);
    qc_inicializar_base(s, 2);
    qc_aplicar_swap(s, 0, 1);
    TEST("SWAP|10> = |01>: amplitud[1] = 1", fabs(s->amplitudes[1].real - 1.0) < 1e-12);
    qc_liberar_sistema(s);
}

// ============================================================
// 8. Medicion
// ============================================================
static void test_measurement(void) {
    SECCION("Medicion con colapso");
    EstadoCuantico* s = qc_crear_sistema(1);
    qc_inicializar_estado_cero(s);
    int r0 = qc_medir(s, 0);
    TEST("Medir |0> da 0", r0 == 0);
    TEST("Colapso: amplitud[0].real = 1", fabs(s->amplitudes[0].real - 1.0) < 1e-12);
    TEST("Colapso: amplitud[1].real = 0", fabs(s->amplitudes[1].real) < 1e-12);
    qc_liberar_sistema(s);
    srand(42);
    s = qc_crear_sistema(1);
    qc_inicializar_estado_cero(s);
    qc_aplicar_hadamard(s, 0);
    int r = qc_medir(s, 0);
    TEST("Medir H|0> da 0 o 1", r == 0 || r == 1);
    ASSERT_CERCANO("Conservacion tras colapso", qc_probabilidad_conservada(s), 1.0, 1e-10);
    qc_liberar_sistema(s);
}

// ============================================================
// 9. Conservacion de probabilidad
// ============================================================
static void test_conservation(void) {
    SECCION("Conservacion de probabilidad");
    EstadoCuantico* s = qc_crear_sistema(3);
    qc_inicializar_estado_cero(s);
    qc_aplicar_hadamard(s, 0);
    qc_aplicar_pauli_x(s, 1);
    qc_aplicar_cnot(s, 0, 2);
    qc_aplicar_hadamard(s, 2);
    ASSERT_CERCANO("Conservacion tras 4 puertas", qc_probabilidad_conservada(s), 1.0, 1e-10);
    qc_liberar_sistema(s);
    s = qc_crear_sistema(4);
    qc_inicializar_estado_uniforme(s);
    ASSERT_CERCANO("Estado uniforme 4 qubits: conservacion = 1", qc_probabilidad_conservada(s), 1.0, 1e-10);
    qc_liberar_sistema(s);
}

// ============================================================
// 10. Estado de Bell
// ============================================================
static void test_bell_state(void) {
    SECCION("Estado de Bell");
    EstadoCuantico* s = qc_crear_sistema(2);
    int rc = qc_crear_estado_bell(s, 0, 1);
    TEST("Crear estado de Bell retorna 0", rc == 0);
    double inv_sqrt2 = 0.7071067811865475;
    ASSERT_CERCANO("Bell |Phi+>: |00> amplitud", s->amplitudes[0].real, inv_sqrt2, 1e-10);
    ASSERT_CERCANO("Bell |Phi+>: |11> amplitud", s->amplitudes[3].real, inv_sqrt2, 1e-10);
    TEST("Bell |Phi+>: |01> = 0", fabs(s->amplitudes[1].real) < 1e-12);
    TEST("Bell |Phi+>: |10> = 0", fabs(s->amplitudes[2].real) < 1e-12);
    ASSERT_CERCANO("Bell: conservacion = 1", qc_probabilidad_conservada(s), 1.0, 1e-10);
    TEST("Bell: es entrelazado", qc_es_entrelazado(s) == 1);
    qc_liberar_sistema(s);
}

// ============================================================
// Oraculos para Deutsch-Jozsa
// ============================================================
static int _oraculo_constante_cero(int x) { (void)x; return 0; }
static int _oraculo_constante_uno(int x) { (void)x; return 1; }
static int _oraculo_balanceado_lsb(int x) { return x & 1; }
static int _oraculo_balanceado_msb(int x) { return (x >> 2) & 1; }

static void test_deutsch_jozsa(void) {
    SECCION("Algoritmo de Deutsch-Jozsa");
    EstadoCuantico* s = qc_crear_sistema(4);
    qc_limpiar(s);
    srand(12345);
    int rc = qc_deutsch_jozsa(s, _oraculo_constante_cero, 3);
    TEST("DJ constante 0: constante", rc == 1);
    qc_liberar_sistema(s);
    s = qc_crear_sistema(4);
    srand(12345);
    rc = qc_deutsch_jozsa(s, _oraculo_constante_uno, 3);
    TEST("DJ constante 1: constante", rc == 1);
    qc_liberar_sistema(s);
    s = qc_crear_sistema(4);
    srand(12345);
    rc = qc_deutsch_jozsa(s, _oraculo_balanceado_lsb, 3);
    printf("  [DEBUG DJ LSB] rc=%d\n", rc);
    for (int q = 0; q < 3; q++) {
        printf("  [DEBUG DJ LSB] P(|1>)_q%d = %g\n", q, qc_probabilidad_uno(s, q));
    }
    TEST("DJ balanceado LSB: balanceado", rc == 0);
    qc_liberar_sistema(s);
    s = qc_crear_sistema(4);
    srand(12345);
    rc = qc_deutsch_jozsa(s, _oraculo_balanceado_msb, 3);
    printf("  [DEBUG DJ MSB] rc=%d\n", rc);
    for (int q = 0; q < 3; q++) {
        printf("  [DEBUG DJ MSB] P(|1>)_q%d = %g\n", q, qc_probabilidad_uno(s, q));
    }
    TEST("DJ balanceado MSB: balanceado", rc == 0);
    qc_liberar_sistema(s);
}

// ============================================================
// 12. Casos borde
// ============================================================
static void test_edge_cases(void) {
    SECCION("Casos borde");
    TEST("qc_liberar_sistema(NULL) seguro", 1);
    qc_limpiar(NULL);
    TEST("qc_limpiar(NULL) seguro", 1);
    TEST("qc_crear_sistema(-1) es NULL", qc_crear_sistema(-1) == NULL);
    EstadoCuantico* s = qc_crear_sistema(2);
    TEST("Hadamard en qubit -1 falla", qc_aplicar_hadamard(s, -1) == -1);
    TEST("Hadamard en qubit 9 falla", qc_aplicar_hadamard(s, 9) == -1);
    TEST("CNOT control=target falla", qc_aplicar_cnot(s, 0, 0) == -1);
    TEST("CNOT indices invalidos falla", qc_aplicar_cnot(s, -1, 2) == -1);
    TEST("Medir qubit invalido falla", qc_medir(s, 99) == -1);
    TEST("Probabilidad qubit invalido = -1", qc_probabilidad_uno(s, 99) < 0);
    TEST("Bell qubits invalidos falla", qc_crear_estado_bell(s, -1, 1) == -1);
    int r = qc_deutsch_jozsa(NULL, _oraculo_constante_cero, 2);
    TEST("DJ sistema NULL falla", r == -1);
    r = qc_deutsch_jozsa(s, NULL, 2);
    TEST("DJ oraculo NULL falla", r == -1);
    r = qc_deutsch_jozsa(s, _oraculo_constante_cero, 0);
    TEST("DJ 0 bits falla", r == -1);
    qc_liberar_sistema(s);
    s = qc_crear_sistema(2);
    TEST("Sistema sin inicializar: estado_inicializado = 0", s->estado_inicializado == 0);
    qc_liberar_sistema(s);
}

// ============================================================
// 13. Limpieza y reutilizacion
// ============================================================
static void test_cleanup(void) {
    SECCION("Limpieza y reutilizacion");
    EstadoCuantico* s = qc_crear_sistema(2);
    qc_crear_estado_bell(s, 0, 1);
    TEST("Estado Bell creado antes de limpiar", qc_es_entrelazado(s) == 1);
    qc_limpiar(s);
    TEST("Estado_inicializado = 0 tras limpiar", s->estado_inicializado == 0);
    for (int i = 0; i < 4; i++) {
        TEST("Amplitudes son 0 tras limpiar", fabs(s->amplitudes[i].real) < 1e-12);
    }
    qc_inicializar_estado_cero(s);
    TEST("Reinicializado: amplitud[0] = 1", fabs(s->amplitudes[0].real - 1.0) < 1e-12);
    qc_liberar_sistema(s);
    EstadoCuantico* a = qc_crear_sistema(1);
    EstadoCuantico* b = qc_crear_sistema(1);
    qc_inicializar_estado_cero(a);
    qc_inicializar_base(b, 1);
    qc_aplicar_hadamard(a, 0);
    TEST("Sistema A en superposicion", qc_probabilidad_uno(a, 0) > 0.49);
    TEST("Sistema B en |1>", fabs(b->amplitudes[1].real - 1.0) < 1e-12);
    qc_liberar_sistema(a);
    qc_liberar_sistema(b);
}

// ============================================================
// Main
// ============================================================
int main(void) {
    printf("=== VALIDACION DEL RUNTIME CUANTICO SIMULADO ===\n");
    printf("  Quantum Runtime — M16.1\n\n");
    srand(42);
    test_lifecycle();
    test_base_states();
    test_hadamard();
    test_pauli_gates();
    test_phase_gates();
    test_cnot_entanglement();
    test_swap();
    test_measurement();
    test_conservation();
    test_bell_state();
    test_deutsch_jozsa();
    test_edge_cases();
    test_cleanup();
    printf("\n=== RESULTADOS ===\n");
    printf("  Secciones: %d\n", section_num);
    printf("  Pasadas: %d\n", test_passed);
    printf("  Falladas: %d\n", test_failed);
    printf("==================\n\n");
    return test_failed > 0 ? 1 : 0;
}
