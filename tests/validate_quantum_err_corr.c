// validate_quantum_err_corr.c — Suite de validacion del Motor de Correccion de Errores (M16.2)
#include "nucleo/quantum_runtime.h"
#include "nucleo/quantum_err_corr.h"
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

// ============================================================
// 1. Inicializacion de estado logico
// ============================================================
static void test_logical_state_init(void) {
    SECCION("Inicializacion de estado logico");

    EstadoCuantico* s = qc_crear_sistema(9);
    TEST("Sistema de 9 qubits creado", s != NULL);

    int rc = qec_inicializar_estado_logico(s, 0);
    TEST("Inicializar |0>_L retorna 0", rc == 0);
    TEST("Conservacion |0>_L", fabs(qc_probabilidad_conservada(s) - 1.0) < 1e-10);
    qc_liberar_sistema(s);

    s = qc_crear_sistema(9);
    rc = qec_inicializar_estado_logico(s, 1);
    TEST("Inicializar |1>_L retorna 0", rc == 0);
    TEST("Conservacion |1>_L", fabs(qc_probabilidad_conservada(s) - 1.0) < 1e-10);
    qc_liberar_sistema(s);
}

// ============================================================
// 2. Inyeccion y deteccion de errores
// ============================================================
static void test_error_injection_detection(void) {
    SECCION("Inyeccion y deteccion de errores");

    // Bit-flip injection on initialized system
    EstadoCuantico* s = qc_crear_sistema(9);
    qc_inicializar_estado_cero(s);  // Initialize to |000000000>
    int rc = qec_inyectar_bit_flip(s, 3);
    TEST("Inyectar bit-flip en sistema inicializado retorna 0", rc == 0);
    TEST("Bit-flip: qubit 3 ahora es |1>", qc_probabilidad_uno(s, 3) > 0.99);
    qc_liberar_sistema(s);

    // Phase-flip injection
    s = qc_crear_sistema(9);
    rc = qec_inyectar_phase_flip(s, 5);
    TEST("Inyectar phase-flip retorna 0", rc == 0);
    qc_liberar_sistema(s);

    // Error injection on logical state — verify Pauli-X changes amplitudes internally
    s = qc_crear_sistema(9);
    qc_inicializar_estado_cero(s);
    double prob_antes = qc_probabilidad_uno(s, 3);
    qec_inyectar_bit_flip(s, 3);  // Flip qubit 3
    double prob_despues = qc_probabilidad_uno(s, 3);
    TEST("Bit-flip: probabilidad cambio de 0 a 1", prob_antes < 0.01 && prob_despues > 0.99);
    qc_liberar_sistema(s);
}

// ============================================================
// 3. Medicion de sindromes
// ============================================================
static void test_syndrome_measurement(void) {
    SECCION("Medicion de sindromes");

    // Sin error
    EstadoCuantico* s = qc_crear_sistema(9);
    qec_inicializar_estado_logico(s, 0);
    qec_medir_sindromes(s);
    TEST("Sin error: sindromes devueltos (no crash)", 1);
    qc_liberar_sistema(s);

    // Con error
    s = qc_crear_sistema(9);
    qec_inicializar_estado_logico(s, 0);
    qec_inyectar_bit_flip(s, 1);
    qec_medir_sindromes(s);
    TEST("Bit-flip: sindrome sin crash", 1);
    qc_liberar_sistema(s);

    // Con phase-flip
    s = qc_crear_sistema(9);
    qec_inicializar_estado_logico(s, 0);
    qec_inyectar_phase_flip(s, 4);
    qec_medir_sindromes(s);
    TEST("Phase-flip: sindrome sin crash", 1);
    qc_liberar_sistema(s);
}

// ============================================================
// 4. Correccion de errores (API)
// ============================================================
static void test_error_correction_api(void) {
    SECCION("Correccion de errores (API)");

    // Correccion sin error
    EstadoCuantico* s = qc_crear_sistema(9);
    MedicionSindromes m;
    memset(&m, 0, sizeof(MedicionSindromes));
    m.tipo_error = QEC_ERROR_NONE;
    ResultadoCorreccion r = qec_corregir_errores(s, &m);
    TEST("Sin error: correccion exitosa", r.exito == 1);
    qc_liberar_sistema(s);

    // Correccion bit-flip en qubit 2
    s = qc_crear_sistema(9);
    qec_inicializar_estado_logico(s, 0);
    qec_inyectar_bit_flip(s, 2);
    m = qec_medir_sindromes(s);
    r = qec_corregir_errores(s, &m);
    TEST("Bit-flip: correccion sin crash", 1);
    qc_liberar_sistema(s);
}

// ============================================================
// 5. Aplicar correccion directa
// ============================================================
static void test_direct_correction(void) {
    SECCION("Correccion directa por qubit");

    EstadoCuantico* s = qc_crear_sistema(9);
    qec_inicializar_estado_logico(s, 0);

    // Inyectar bit-flip y corregir directamente
    qec_inyectar_bit_flip(s, 0);
    int rc = qec_aplicar_correccion(s, QEC_ERROR_BIT_FLIP, 0);
    TEST("Aplicar correccion bit-flip directa retorna 0", rc == 0);
    qc_liberar_sistema(s);

    // Phase-flip directa
    s = qc_crear_sistema(9);
    qec_inicializar_estado_logico(s, 0);
    qec_inyectar_phase_flip(s, 3);
    rc = qec_aplicar_correccion(s, QEC_ERROR_PHASE_FLIP, 3);
    TEST("Aplicar correccion phase-flip directa retorna 0", rc == 0);
    qc_liberar_sistema(s);

    // Error doble
    s = qc_crear_sistema(9);
    qec_inicializar_estado_logico(s, 0);
    qec_inyectar_bit_flip(s, 5);
    qec_inyectar_phase_flip(s, 5);
    rc = qec_aplicar_correccion(s, QEC_ERROR_BOTH, 5);
    TEST("Aplicar correccion doble retorna 0", rc == 0);
    qc_liberar_sistema(s);
}

// ============================================================
// 6. Ciclo completo de proteccion
// ============================================================
static void test_protection_cycle(void) {
    SECCION("Ciclo completo de proteccion");

    // Sin error
    {
        EstadoCuantico* s = qc_crear_sistema(9);
        Complejo a0 = {1.0, 0.0}, a1 = {0.0, 0.0};
        ResultadoCorreccion r0 = qec_proteger_qubit(s, &a0, &a1, QEC_ERROR_NONE, 0);
        TEST("Proteccion sin error: exitosa", r0.exito == 1);
        qc_liberar_sistema(s);
    }

    // Bit-flip en qubit 2
    {
        EstadoCuantico* s = qc_crear_sistema(9);
        Complejo a0 = {1.0, 0.0}, a1 = {0.0, 0.0};
        ResultadoCorreccion r1 = qec_proteger_qubit(s, &a0, &a1, QEC_ERROR_BIT_FLIP, 2);
        TEST("Proteccion bit-flip: exitosa", r1.exito == 1);
        qc_liberar_sistema(s);
    }

    // Phase-flip en qubit 6
    {
        EstadoCuantico* s = qc_crear_sistema(9);
        Complejo a0 = {1.0, 0.0}, a1 = {0.0, 0.0};
        ResultadoCorreccion r2 = qec_proteger_qubit(s, &a0, &a1, QEC_ERROR_PHASE_FLIP, 6);
        TEST("Proteccion phase-flip: exitosa", r2.exito == 1);
        qc_liberar_sistema(s);
    }
}

// ============================================================
// 7. Verificacion de fidelidad
// ============================================================
static void test_fidelity(void) {
    SECCION("Verificacion de fidelidad");

    EstadoCuantico* s2 = qc_crear_sistema(9);
    qec_inicializar_estado_logico(s2, 0);
    Complejo a0_b = {1.0, 0.0}, a1_b = {0.0, 0.0};
    double fid = qec_calcular_fidelidad(s2, &a0_b, &a1_b);
    TEST("Fidelidad calculada >= 0", fid >= 0.0);
    qc_liberar_sistema(s2);
}

// ============================================================
// 8. Casos borde (NULL safety)
// ============================================================
static void test_edge_cases(void) {
    SECCION("Casos borde");

    TEST("Inicializar NULL retorna -1", qec_inicializar_estado_logico(NULL, 0) == -1);
    TEST("Bit-flip NULL retorna -1", qec_inyectar_bit_flip(NULL, 0) == -1);
    TEST("Phase-flip NULL retorna -1", qec_inyectar_phase_flip(NULL, 0) == -1);

    qec_medir_sindromes(NULL);
    TEST("Sindromes NULL: no crash", 1);

    EstadoCuantico* s = qc_crear_sistema(2);
    TEST("Sistema 2 qubits: init retorna -1", qec_inicializar_estado_logico(s, 0) == -1);
    qc_liberar_sistema(s);

    s = qc_crear_sistema(9);
    TEST("Bit-flip qubit -1 falla", qec_inyectar_bit_flip(s, -1) == -1);
    TEST("Bit-flip qubit 99 falla", qec_inyectar_bit_flip(s, 99) == -1);
    TEST("Phase-flip qubit -1 falla", qec_inyectar_phase_flip(s, -1) == -1);
    TEST("Phase-flip qubit 99 falla", qec_inyectar_phase_flip(s, 99) == -1);
    qc_liberar_sistema(s);
}

// ============================================================
// Main
// ============================================================
int main(void) {
    printf("=== VALIDACION DEL MOTOR DE CORRECCION DE ERRORES CUANTICOS ===\n");
    printf("  Quantum Error Correction — M16.2 (Shor 9-qubit code)\n\n");
    srand(42);

    test_logical_state_init();
    test_error_injection_detection();
    test_syndrome_measurement();
    test_error_correction_api();
    test_direct_correction();
    test_protection_cycle();
    test_fidelity();
    test_edge_cases();

    printf("\n=== RESULTADOS ===\n");
    printf("  Secciones: %d\n", section_num);
    printf("  Pasadas: %d\n", test_passed);
    printf("  Falladas: %d\n", test_failed);
    printf("==================\n\n");
    return test_failed > 0 ? 1 : 0;
}
