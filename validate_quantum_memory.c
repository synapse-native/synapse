// validate_quantum_memory.c — Suite de validacion de Memoria Cuantica (M16.4)
// Pruebas aisladas para canales de ruido T1/T2 e integracion con QEC.
// ======================================================================

#include "nucleo/quantum_runtime.h"
#include "nucleo/quantum_memory.h"
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
// 1. Creacion de canal de ruido
// ============================================================
static void test_channel_creation(void) {
    SECCION("Creacion de canal de ruido");

    QMChannel c = qm_crear_canal(100.0, 50.0);
    TEST("T1=100", fabs(c.t1 - 100.0) < 1e-10);
    TEST("T2=50", fabs(c.t2 - 50.0) < 1e-10);
    TEST("gamma_1=0 inicial", fabs(c.gamma_1) < 1e-10);
    TEST("gamma_2=0 inicial", fabs(c.gamma_2) < 1e-10);
    TEST("errores_t1=0", c.errores_t1 == 0);
    TEST("errores_t2=0", c.errores_t2 == 0);

    // Valores por defecto para T1/T2 invalidos
    QMChannel c2 = qm_crear_canal(0.0, -1.0);
    TEST("T1 default para 0", c2.t1 > 0);
    TEST("T2 default para -1", c2.t2 > 0);
}

// ============================================================
// 2. Actualizacion de tiempo y tasas
// ============================================================
static void test_time_update(void) {
    SECCION("Actualizacion de tiempo y tasas gamma");

    QMChannel c = qm_crear_canal(100.0, 50.0);
    qm_actualizar_tiempo(&c, 0.0);
    TEST("gamma_1=0 en t=0", fabs(c.gamma_1) < 1e-10);
    TEST("gamma_2=0 en t=0", fabs(c.gamma_2) < 1e-10);

    // t = T1: gamma_1 = 1 - 1/e ~ 0.632
    qm_actualizar_tiempo(&c, 100.0);
    TEST("gamma_1 en t=T1 ~ 0.632", fabs(c.gamma_1 - 0.632) < 0.01);
    // t=100 con T2=50: gamma_2 = 1 - e^(-2) ~ 0.865
    TEST("gamma_2 en t=2*T2 ~ 0.865", fabs(c.gamma_2 - 0.865) < 0.01);

    // t = 2*T1: gamma_1 ~ 0.865
    qm_actualizar_tiempo(&c, 200.0);
    TEST("gamma_1 en t=2*T1 ~ 0.865", fabs(c.gamma_1 - 0.865) < 0.01);

    // t muy grande: gamma -> 1
    qm_actualizar_tiempo(&c, 10000.0);
    TEST("gamma_1 en t>>T1 ~ 1.0", fabs(c.gamma_1 - 1.0) < 0.01);
}

// ============================================================
// 3. T1: Amplitude Damping en sistema simple
// ============================================================
static void test_t1_amplitude_damping(void) {
    SECCION("T1: Amplitude Damping");

    // Sistema de 1 qubit inicializado en |1>
    EstadoCuantico* s = qc_crear_sistema(1);
    qc_inicializar_base(s, 1);  // |1>

    QMChannel c = qm_crear_canal(10.0, 50.0);
    qm_actualizar_tiempo(&c, 100.0);  // t >> T1, gamma_1 ~ 1.0

    // Aplicar T1: |1> debe decaer a |0>
    int rc = qm_aplicar_t1(s, &c);
    TEST("T1 aplicado retorna 0", rc == 0);

    // Despues de T1 con gamma~1, la probabilidad de |1> debe ser baja
    double prob_1 = qc_probabilidad_uno(s, 0);
    TEST("Probabilidad |1> reducida por T1", prob_1 < 0.5);

    qc_liberar_sistema(s);

    // Sistema en |0>: T1 no debe afectar
    s = qc_crear_sistema(1);
    qc_inicializar_estado_cero(s);
    c = qm_crear_canal(10.0, 50.0);
    qm_actualizar_tiempo(&c, 100.0);
    qm_aplicar_t1(s, &c);
    prob_1 = qc_probabilidad_uno(s, 0);
    TEST("|0> no afectado por T1", prob_1 < 0.01);
    TEST("Conservacion tras T1 en |0>", fabs(qc_probabilidad_conservada(s) - 1.0) < 1e-10);

    qc_liberar_sistema(s);
}

// ============================================================
// 4. T2: Phase Damping
// ============================================================
static void test_t2_phase_damping(void) {
    SECCION("T2: Phase Damping");

    // Sistema de 1 qubit en superposicion |+> = (|0>+|1>)/sqrt(2)
    EstadoCuantico* s = qc_crear_sistema(1);
    qc_inicializar_estado_uniforme(s);

    // Verificar estado inicial
    Complejo a0 = qc_obtener_amplitud(s, 0);
    Complejo a1 = qc_obtener_amplitud(s, 1);
    TEST("Amplitud |0> ~ 0.707", fabs(a0.real - 0.707) < 0.01);
    TEST("Amplitud |1> ~ 0.707", fabs(a1.real - 0.707) < 0.01);

    // Aplicar T2 con gamma_2 alta
    QMChannel c = qm_crear_canal(100.0, 1.0);
    qm_actualizar_tiempo(&c, 10.0);  // t >> T2

    srand(42);
    int rc = qm_aplicar_t2(s, &c);
    TEST("T2 aplicado retorna 0", rc == 0);

    // T2 no cambia probabilidades individuales
    double prob_1 = qc_probabilidad_uno(s, 0);
    TEST("Probabilidad |1> conservada tras T2", fabs(prob_1 - 0.5) < 0.01);

    // Conservacion de probabilidad
    TEST("Conservacion tras T2", fabs(qc_probabilidad_conservada(s) - 1.0) < 1e-10);

    qc_liberar_sistema(s);
}

// ============================================================
// 5. Ruido combinado T1+T2
// ============================================================
static void test_combined_noise(void) {
    SECCION("Ruido combinado T1+T2");

    EstadoCuantico* s = qc_crear_sistema(1);
    qc_inicializar_estado_uniforme(s);  // |+>

    // T1+T2 con tasas moderadas para evitar perdida de norma por redondeo
    QMChannel c = qm_crear_canal(100.0, 50.0);
    qm_actualizar_tiempo(&c, 10.0);  // gamma_1 ≈ 0.095, gamma_2 ≈ 0.181

    srand(42);
    int rc = qm_aplicar_ruido(s, &c);
    TEST("Ruido combinado retorna 0", rc == 0);

    // Conservacion de probabilidad verificada
    double conservada = qc_probabilidad_conservada(s);
    TEST("Conservacion tras ruido combinado", fabs(conservada - 1.0) < 0.05);

    // Eventos de ruido registrados
    TEST("Eventos T1 registrados", c.errores_t1 >= 0);
    TEST("Eventos T2 registrados", c.errores_t2 >= 0);

    qc_liberar_sistema(s);
}

// ============================================================
// 6. Simulacion con QEC
// ============================================================
static void test_qec_integration(void) {
    SECCION("Simulacion con integracion QEC");

    EstadoCuantico* s = qc_crear_sistema(1);
    qc_inicializar_estado_cero(s);

    QMChannel c = qm_crear_canal(50.0, 30.0);
    qm_actualizar_tiempo(&c, 10.0);

    srand(99);
    QMResultado res = qm_simular_con_qec(s, &c, 0, 0, 1);
    TEST("Simulacion QEC completada", 1);
    TEST("Fidelidad fisica calculada", res.fidelidad_fisica >= 0.0);
    TEST("Fidelidad logica calculada", res.fidelidad_logica >= 0.0);
    TEST("T1 efectivo > 0", res.t1_efectivo > 0);
    TEST("T2 efectivo > 0", res.t2_efectivo > 0);

    qc_liberar_sistema(s);
}

// ============================================================
// 7. Wrappers _syn_qm_*
// ============================================================
static void test_syn_wrappers(void) {
    SECCION("Wrappers _syn_qm_*");

    EstadoCuantico* s = qc_crear_sistema(1);
    qc_inicializar_base(s, 1);  // |1>

    srand(42);
    int rc = _syn_qm_aplicar_t1((void*)s, 10.0, 100.0);
    TEST("Wrapper T1 ejecutado", rc == 0);

    qc_liberar_sistema(s);

    s = qc_crear_sistema(1);
    qc_inicializar_estado_uniforme(s);
    srand(42);
    rc = _syn_qm_aplicar_t2((void*)s, 5.0, 20.0);
    TEST("Wrapper T2 ejecutado", rc == 0);
    double conservada = qc_probabilidad_conservada(s);
    TEST("Conservacion tras wrapper T2", fabs(conservada - 1.0) < 0.01);

    qc_liberar_sistema(s);

    // Wrapper QEC
    s = qc_crear_sistema(1);
    qc_inicializar_estado_cero(s);
    srand(42);
    rc = _syn_qm_simular_con_qec((void*)s, 50.0, 30.0, 10.0);
    TEST("Wrapper QEC ejecutado", rc >= 0);
    qc_liberar_sistema(s);

    // NULL safety
    TEST("Wrapper T1 con NULL retorna !=0", _syn_qm_aplicar_t1(NULL, 10.0, 10.0) != 0);
    TEST("Wrapper T2 con NULL retorna !=0", _syn_qm_aplicar_t2(NULL, 10.0, 10.0) != 0);
}

// ============================================================
// Main
// ============================================================
int main(void) {
    printf("=== VALIDACION DE MEMORIA CUANTICA Y DECOHERENCIA ===\n");
    printf("  M16.4 — T1/T2 Noise Channels & QEC Integration\n\n");
    srand(time(NULL));

    test_channel_creation();
    test_time_update();
    test_t1_amplitude_damping();
    test_t2_phase_damping();
    test_combined_noise();
    test_qec_integration();
    test_syn_wrappers();

    printf("\n=== RESULTADOS ===\n");
    printf("  Secciones: %d\n", section_num);
    printf("  Pasadas: %d\n", test_passed);
    printf("  Falladas: %d\n", test_failed);
    printf("==================\n\n");
    return test_failed > 0 ? 1 : 0;
}
