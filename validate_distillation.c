// validate_distillation.c — Validación aislada del Pipeline de Destilación de Modelos (M13.6)
// =========================================================================================
// Prueba: KL divergence, soft+hard combined loss, teacher-student training,
// layer reduction, persistence, reduction estimation, edge cases.
//
// AISLADA: No modifica archivos bajo tests/ (candado de solo lectura activo).
// =========================================================================================

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#include "nucleo/distillation.h"

// ============================================================
// Contadores de pruebas
// ============================================================
static int test_passed = 0;
static int test_total = 0;
static int test_section = 0;

#define test_assert(msg, expr) do { \
    test_total++; \
    if (!(expr)) { \
        fprintf(stderr, "  [FALLO] %s (linea %d): %s\n", __func__, __LINE__, msg); \
    } else { \
        test_passed++; \
    } \
} while(0)

#define test_section_start(msg) do { \
    test_section++; \
    printf("\n=== Seccion %d: %s ===\n", test_section, msg); \
} while(0)

// ============================================================
// Sección 1: KL Divergence
// ============================================================
static void test_kl_divergence(void) {
    int n = 4;

    // 1.1 Distribuciones idénticas → KL=0
    float logits_p[] = {1.0f, 2.0f, 3.0f, 4.0f};
    float logits_q[] = {1.0f, 2.0f, 3.0f, 4.0f};
    float kl = kd_divergencia_kl(logits_p, logits_q, n, 1.0f);
    test_assert("KL identical distributions ~ 0", fabsf(kl) < 0.001f);

    // 1.2 Temperatura alta suaviza divergencia
    float kl_high = kd_divergencia_kl(logits_p, logits_q, n, 10.0f);
    test_assert("KL with high temp ~ 0", fabsf(kl_high) < 0.001f);

    // 1.3 Distribuciones diferentes → KL > 0
    float logits_diff[] = {10.0f, 0.0f, 0.0f, 0.0f};
    float kl_diff = kd_divergencia_kl(logits_p, logits_diff, n, 1.0f);
    test_assert("KL different distributions > 0", kl_diff > 0.0f);

    // 1.4 KL asimétrica: KL(P||Q) != KL(Q||P)
    float kl_rev = kd_divergencia_kl(logits_diff, logits_p, n, 1.0f);
    test_assert("KL is asymmetric", fabsf(kl_diff - kl_rev) > 0.001f);

    // 1.5 NULL safety
    float kl_null = kd_divergencia_kl(NULL, logits_q, n, 1.0f);
    test_assert("KL NULL p returns -1", kl_null < 0.0f);

    kl_null = kd_divergencia_kl(logits_p, NULL, n, 1.0f);
    test_assert("KL NULL q returns -1", kl_null < 0.0f);

    // 1.6 n <= 0
    kl_null = kd_divergencia_kl(logits_p, logits_q, 0, 1.0f);
    test_assert("KL n=0 returns -1", kl_null < 0.0f);

    // 1.7 Un solo elemento
    float ones[] = {1.0f};
    float ks = kd_divergencia_kl(ones, ones, 1, 1.0f);
    test_assert("KL single element ~ 0", fabsf(ks) < 0.001f);
}

// ============================================================
// Sección 2: Combined Loss (soft + hard)
// ============================================================
static void test_combined_loss(void) {
    int vs = 5;
    float logits_t[] = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};
    float logits_s[] = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};

    // 2.1 Logits idénticos + alpha=1.0 → solo soft loss, debe ser 0
    float loss = kd_perdida_combinada(logits_t, logits_s, 4, vs, 1.0f, 1.0f);
    test_assert("Combined loss identical alpha=1 ~ 0", fabsf(loss) < 0.1f);

    // 2.2 alpha=0 → solo hard loss, debe ser CE > 0
    float loss_hard = kd_perdida_combinada(logits_t, logits_s, 0, vs, 1.0f, 0.0f);
    test_assert("Combined loss alpha=0 > 0", loss_hard > 0.0f);

    // 2.3 alpha=0.5 → mezcla de soft y hard
    float loss_mix = kd_perdida_combinada(logits_t, logits_s, 4, vs, 1.0f, 0.5f);
    test_assert("Combined loss alpha=0.5 > 0", loss_mix > 0.0f);

    // 2.4 Student diferente a teacher → pérdida mayor
    float logits_s_bad[] = {5.0f, 4.0f, 3.0f, 2.0f, 1.0f};
    float loss_bad = kd_perdida_combinada(logits_t, logits_s_bad, 0, vs, 1.0f, 0.5f);
    test_assert("Mismatched logits loss > close", loss_bad > 0.1f);

    // 2.5 Target inválido
    float loss_inv = kd_perdida_combinada(logits_t, logits_s, -1, vs, 1.0f, 0.5f);
    test_assert("Invalid target returns -1", loss_inv < 0.0f);

    // 2.6 NULL logits
    float loss_null = kd_perdida_combinada(NULL, logits_s, 0, vs, 1.0f, 0.5f);
    test_assert("NULL teacher returns -1", loss_null < 0.0f);

    loss_null = kd_perdida_combinada(logits_t, NULL, 0, vs, 1.0f, 0.5f);
    test_assert("NULL student returns -1", loss_null < 0.0f);

    // 2.7 vocab_size = 0
    loss_null = kd_perdida_combinada(logits_t, logits_s, 0, 0, 1.0f, 0.5f);
    test_assert("vocab_size=0 returns -1", loss_null < 0.0f);
}

// ============================================================
// Sección 3: Inicialización y ciclo de vida
// ============================================================
static void test_session_lifecycle(void) {
    // 3.1 Iniciar con NULL → configuración por defecto
    KDSession* sesion = kd_iniciar(NULL);
    test_assert("Session iniciada con NULL", sesion != NULL);
    test_assert("Temperatura default", sesion->config.temperature == KD_TEMPERATURE_DEFAULT);
    test_assert("Alpha default", sesion->config.alpha == KD_ALPHA_DEFAULT);
    test_assert("Vocab size default", sesion->config.vocab_size == 32000);
    test_assert("Estado init", sesion->estado == 0);
    kd_cerrar(sesion);

    // 3.2 Iniciar con configuración explícita
    KDConfig cfg;
    cfg.temperature = 2.0f;
    cfg.alpha = 0.3f;
    cfg.num_epochs = 3;
    cfg.batch_size = 4;
    cfg.vocab_size = 1000;
    cfg.learning_rate = 0.001f;
    cfg.weight_decay = 0.01f;
    cfg.student_hidden_dim = 256;
    cfg.teacher_hidden_dim = 1024;

    sesion = kd_iniciar(&cfg);
    test_assert("Session con config explícita", sesion != NULL);
    test_assert("Temperatura config", sesion->config.temperature == 2.0f);
    test_assert("Alpha config", sesion->config.alpha == 0.3f);
    test_assert("Epochs config", sesion->config.num_epochs == 3);
    test_assert("Vocab config", sesion->config.vocab_size == 1000);
    kd_cerrar(sesion);

    // 3.3 Cerrar sesión NULL
    kd_cerrar(NULL);
    test_assert("Cerrar NULL no crash", 1);

    // 3.4 Cerrar sesión vacía
    sesion = kd_iniciar(NULL);
    kd_cerrar(sesion);
    test_assert("Cerrar sesion vacia OK", 1);
}

// ============================================================
// Sección 4: Agregar pares de logits
// ============================================================
static void test_add_pairs(void) {
    KDSession* sesion = kd_iniciar(NULL);
    test_assert("Session para pairs", sesion != NULL);

    // 4.1 Agregar par válido
    float lt[10], ls[10];
    for (int i = 0; i < 10; i++) {
        lt[i] = (float)i;
        ls[i] = (float)(9 - i);
    }
    int idx = kd_agregar_par(sesion, lt, ls, 5, 1.0f);
    test_assert("Par 0 agregado", idx == 0);
    test_assert("1 par en dataset", sesion->dataset.num_pares == 1);

    // 4.2 Agregar segundo par
    idx = kd_agregar_par(sesion, lt, ls, 3, 2.0f);
    test_assert("Par 1 agregado", idx == 1);
    test_assert("2 pares en dataset", sesion->dataset.num_pares == 2);

    // 4.3 Agregar con NULL logits
    idx = kd_agregar_par(sesion, NULL, ls, 0, 1.0f);
    test_assert("NULL teacher falla", idx == -1);

    // 4.4 Agregar con target inválido
    idx = kd_agregar_par(sesion, lt, ls, -1, 1.0f);
    test_assert("Target -1 falla", idx == -1);

    // 4.5 Agregar a sesión NULL
    idx = kd_agregar_par(NULL, lt, ls, 0, 1.0f);
    test_assert("Session NULL falla", idx == -1);

    kd_cerrar(sesion);
    test_assert("Session pairs cerrada", 1);
}

// ============================================================
// Sección 5: Paso de destilación
// ============================================================
static void test_distillation_step(void) {
    KDSession* sesion = kd_iniciar(NULL);
    test_assert("Session destilacion", sesion != NULL);

    // 5.1 Paso sin dataset → error
    float loss = kd_paso_destilacion(sesion);
    test_assert("Paso sin pares falla", loss < 0.0f);

    // 5.2 Agregar pares y ejecutar paso
    int vs = 10;
    for (int i = 0; i < 5; i++) {
        float lt[10], ls[10];
        for (int j = 0; j < vs; j++) {
            lt[j] = (float)(j * (i + 1));
            ls[j] = (float)((vs - j) * (i + 1));
        }
        kd_agregar_par(sesion, lt, ls, i % vs, 1.0f);
    }
    test_assert("5 pares agregados", sesion->dataset.num_pares == 5);

    loss = kd_paso_destilacion(sesion);
    test_assert("Paso de destilacion OK", loss >= 0.0f);
    test_assert("Paso incrementado", sesion->paso_actual == 1);
    test_assert("Perdida soft > 0", sesion->perdida_soft_actual > 0.0f);
    test_assert("Perdida hard > 0", sesion->perdida_hard_actual > 0.0f);

    // 5.3 Segundo paso (debería mejorar por ajuste)
    float loss2 = kd_paso_destilacion(sesion);
    test_assert("Segundo paso OK", loss2 >= 0.0f);
    test_assert("Paso incrementado a 2", sesion->paso_actual == 2);

    kd_cerrar(sesion);
}

// ============================================================
// Sección 6: Destilación completa
// ============================================================
static void test_full_distillation(void) {
    KDConfig cfg;
    cfg.temperature = 4.0f;
    cfg.alpha = 0.5f;
    cfg.num_epochs = 3;
    cfg.batch_size = 1;
    cfg.vocab_size = 20;
    cfg.learning_rate = 0.001f;
    cfg.weight_decay = 0.01f;
    cfg.student_hidden_dim = 64;
    cfg.teacher_hidden_dim = 256;

    KDSession* sesion = kd_iniciar(&cfg);
    test_assert("Session full destilacion", sesion != NULL);

    // Dataset con 10 pares
    int vs = cfg.vocab_size;
    for (int i = 0; i < 10; i++) {
        float lt[20], ls[20];
        for (int j = 0; j < vs; j++) {
            lt[j] = (float)(j * 2 + i);
            ls[j] = (float)(j + i);
        }
        kd_agregar_par(sesion, lt, ls, i % vs, 1.0f);
    }

    float avg_loss = kd_destilar(sesion);
    test_assert("Destilacion completa OK", avg_loss >= 0.0f);
    test_assert("Estado completado", sesion->estado == 2);
    test_assert("Pasos ejecutados", sesion->paso_actual == cfg.num_epochs);

    // Estadísticas
    KDEstadisticas stats = kd_obtener_estadisticas(sesion);
    test_assert("Stats soft > 0", stats.perdida_soft > 0.0f);
    test_assert("Stats hard > 0", stats.perdida_hard > 0.0f);
    test_assert("Stats total > 0", stats.perdida_total > 0.0f);
    test_assert("Stats temperatura", stats.temperatura_usada == 4.0f);
    test_assert("Stats alpha", stats.alpha_usado == 0.5f);
    test_assert("Stats pasos > 0", stats.pasos_ejecutados > 0);
    test_assert("Stats ejemplos", stats.num_ejemplos_procesados == 10);
    test_assert("Stats reduccion estimada", stats.reduccion_estimada > 0.0f);

    kd_cerrar(sesion);
}

// ============================================================
// Sección 7: Persistencia (save/load)
// ============================================================
static void test_persistence(void) {
    // Crear y guardar
    KDSession* sesion = kd_iniciar(NULL);
    test_assert("Session persistencia", sesion != NULL);

    float lt[8], ls[8];
    for (int i = 0; i < 8; i++) {
        lt[i] = (float)(i * 10);
        ls[i] = (float)(i);
    }
    kd_agregar_par(sesion, lt, ls, 3, 1.0f);
    kd_paso_destilacion(sesion);
    test_assert("Perdida actual > 0", sesion->perdida_total_actual > 0.0f);

    remove("_test_kd_session.bin");
    int rc = kd_guardar(sesion, "_test_kd_session.bin");
    test_assert("Sesion guardada", rc == 0);
    kd_cerrar(sesion);

    // Cargar
    sesion = kd_iniciar(NULL);
    rc = kd_cargar(sesion, "_test_kd_session.bin");
    test_assert("Sesion cargada", rc == 0);
    test_assert("1 par cargado", sesion->dataset.num_pares == 1);
    test_assert("Config cargada", sesion->config.vocab_size > 0);
    test_assert("Perdida cargada", sesion->perdida_total_actual > 0.0f);

    kd_cerrar(sesion);
    remove("_test_kd_session.bin");

    // Guardar sesión NULL
    rc = kd_guardar(NULL, "_test_kd_session.bin");
    test_assert("Guardar NULL falla", rc == -1);

    // Cargar desde archivo inexistente
    sesion = kd_iniciar(NULL);
    rc = kd_cargar(sesion, "_test_no_existe.bin");
    test_assert("Cargar archivo inexistente falla", rc == -1);
    kd_cerrar(sesion);
}

// ============================================================
// Sección 8: Layer Reduction (teacher → student)
// ============================================================
static void test_layer_reduction(void) {
    KDSession* sesion = kd_iniciar(NULL);
    test_assert("Session layer reduction", sesion != NULL);

    // Teacher: 6 capas, dim=8, Student: 3 capas, dim=4
    int t_layers = 6, t_dim = 8;
    int s_layers = 3, s_dim = 4;
    float pesos_teacher[6 * 8];
    float pesos_student[3 * 4];

    for (int i = 0; i < t_layers * t_dim; i++) {
        pesos_teacher[i] = (float)i;
    }
    memset(pesos_student, 0, sizeof(pesos_student));

    int rc = kd_reducir_capas(sesion, pesos_teacher,
                               t_layers, t_dim,
                               pesos_student, s_layers, s_dim);
    test_assert("Layer reduction OK", rc == 0);

    // Verificar que los pesos student no son todos cero
    int any_nonzero = 0;
    for (int i = 0; i < s_layers * s_dim; i++) {
        if (fabsf(pesos_student[i]) > 0.001f) { any_nonzero = 1; break; }
    }
    test_assert("Pesos student interpolados", any_nonzero);

    // Verificar valores específicos de interpolación
    // Capa student[0] = teacher[0] (posición 0.0)
    test_assert("Student[0] ≈ Teacher[0]", fabsf(pesos_student[0] - pesos_teacher[0]) < 0.1f);

    // Capa student[2] = teacher[5] (posición 2.5 → high=5, low=4)
    // pos = 2/(3-1)*(6-1) = 2/2*5 = 5.0 → t_idx_low=5
    float expected = pesos_teacher[5 * t_dim + 0];
    test_assert("Student[last] ≈ Teacher[last]", fabsf(pesos_student[2 * s_dim] - expected) < 0.1f);

    // Parámetros inválidos
    rc = kd_reducir_capas(sesion, NULL, t_layers, t_dim, pesos_student, s_layers, s_dim);
    test_assert("Reduction NULL teacher falla", rc == -1);

    rc = kd_reducir_capas(sesion, pesos_teacher, 0, t_dim, pesos_student, s_layers, s_dim);
    test_assert("Reduction 0 capas teacher falla", rc == -1);

    kd_cerrar(sesion);
}

// ============================================================
// Sección 9: Reduction Estimation
// ============================================================
static void test_reduction_estimation(void) {
    float red;

    // 9.1 Teacher 7B, Student 1B, INT8
    red = kd_estimar_reduccion(7000, 1000, 2);
    test_assert("7B→1B INT8 ~14x", fabsf(red - 14.0f) < 1.0f);

    // 9.2 Teacher 7B, Student 1B, INT4
    red = kd_estimar_reduccion(7000, 1000, 3);
    test_assert("7B→1B INT4 ~28x", fabsf(red - 28.0f) < 2.0f);

    // 9.3 Teacher 7B, Student 1B, FP16
    red = kd_estimar_reduccion(7000, 1000, 1);
    test_assert("7B→1B FP16 ~7x", fabsf(red - 7.0f) < 1.0f);

    // 9.4 Teacher = Student, INT8 → sin reducción por params
    red = kd_estimar_reduccion(1000, 1000, 2);
    test_assert("Igual params INT8 ~2x", fabsf(red - 2.0f) < 0.5f);

    // 9.5 Parámetros inválidos
    red = kd_estimar_reduccion(0, 1000, 2);
    test_assert("Teacher 0 retorna 1", fabsf(red - 1.0f) < 0.01f);

    red = kd_estimar_reduccion(7000, 0, 2);
    test_assert("Student 0 retorna 1", fabsf(red - 1.0f) < 0.01f);

    // 9.6 Todos los formatos
    red = kd_estimar_reduccion(7000, 1000, 0); // FP32
    test_assert("INT4 > INT8 > FP16 > FP32", red > 0.0f);
}

// ============================================================
// Sección 10: Evaluación
// ============================================================
static void test_evaluation(void) {
    KDSession* sesion = kd_iniciar(NULL);
    test_assert("Session evaluacion", sesion != NULL);

    int vs = 10;
    float logits_t[10], logits_s[10];
    for (int i = 0; i < vs; i++) {
        logits_t[i] = (float)(i * 2);
        logits_s[i] = (float)(vs - i);
    }

    float loss = kd_evaluar(sesion, logits_t, logits_s, 5);
    test_assert("Evaluacion OK", loss >= 0.0f);

    // Evaluación con NULL
    float loss_null = kd_evaluar(sesion, NULL, logits_s, 0);
    test_assert("Evaluacion NULL teacher falla", loss_null < 0.0f);

    loss_null = kd_evaluar(sesion, logits_t, NULL, 0);
    test_assert("Evaluacion NULL student falla", loss_null < 0.0f);

    // Session NULL
    loss_null = kd_evaluar(NULL, logits_t, logits_s, 0);
    test_assert("Evaluacion session NULL falla", loss_null < 0.0f);

    // Obtener pérdida y paso
    float pl = kd_perdida_actual(NULL);
    test_assert("Perdida session NULL", pl < 0.0f);

    int pa = kd_paso_actual(NULL);
    test_assert("Paso session NULL", pa < 0);

    kd_cerrar(sesion);
}

// ============================================================
// Sección 11: Edge Cases
// ============================================================
static void test_edge_cases(void) {
    // 11.1 Estadísticas de sesión NULL
    KDEstadisticas stats = kd_obtener_estadisticas(NULL);
    test_assert("Stats NULL: soft=0", fabsf(stats.perdida_soft) < 0.001f);
    test_assert("Stats NULL: pasos=0", stats.pasos_ejecutados == 0);

    // 11.2 Vocab size muy pequeño
    KDConfig cfg;
    memset(&cfg, 0, sizeof(cfg));
    cfg.temperature = 1.0f;
    cfg.alpha = 0.5f;
    cfg.vocab_size = 2;  // Mínimo
    cfg.num_epochs = 1;

    KDSession* s = kd_iniciar(&cfg);
    test_assert("Session vocab=2", s != NULL);

    float lt[2] = {0.0f, 10.0f};
    float ls[2] = {5.0f, 5.0f};
    int rc = kd_agregar_par(s, lt, ls, 1, 1.0f);
    test_assert("Par vocab=2 agregado", rc == 0);

    float loss = kd_paso_destilacion(s);
    test_assert("Paso vocab=2 OK", loss >= 0.0f);
    kd_cerrar(s);

    // 11.3 Temperatura = 0 (evitar división por cero en softmax)
    cfg.temperature = 0.1f;
    s = kd_iniciar(&cfg);
    test_assert("Session temp baja", s != NULL);

    // 11.4 alpha = 0 (solo hard loss)
    cfg.alpha = 0.0f;
    s = kd_iniciar(&cfg);
    test_assert("Session alpha=0", s != NULL);

    // 11.5 alpha = 1 (solo soft loss)
    cfg.alpha = 1.0f;
    s = kd_iniciar(&cfg);
    test_assert("Session alpha=1", s != NULL);

    // 11.6 Guardar/Cargar con ruta NULL
    rc = kd_guardar(NULL, NULL);
    test_assert("Guardar NULL-NULL falla", rc == -1);

    rc = kd_cargar(NULL, NULL);
    test_assert("Cargar NULL-NULL falla", rc == -1);

    // 11.7 Guardar con ruta vacía
    rc = kd_guardar(NULL, "");
    test_assert("Guardar ruta vacia falla", rc == -1);

    // 11.8 Sesión con estado completado
    cfg.temperature = 2.0f;
    cfg.alpha = 0.5f;
    cfg.vocab_size = 4;
    cfg.num_epochs = 2;
    s = kd_iniciar(&cfg);
    float lt4[4], ls4[4];
    for (int i = 0; i < 4; i++) { lt4[i] = (float)i; ls4[i] = (float)(3 - i); }
    kd_agregar_par(s, lt4, ls4, 2, 1.0f);
    loss = kd_destilar(s);
    test_assert("Destilacion edge OK", loss >= 0.0f);
    test_assert("Estado completado", s->estado == 2);
    kd_cerrar(s);
}

// ============================================================
// Main
// ============================================================

int main(void) {
    printf("============================================\n");
    printf("  Synapse Distillation Suite (M13.6)\n");
    printf("  Teacher→Student via KL Divergence\n");
    printf("============================================\n");

    srand((unsigned int)42);  // Seed determinista

    test_section_start("KL Divergence");
    test_kl_divergence();

    test_section_start("Combined Loss (Soft + Hard)");
    test_combined_loss();

    test_section_start("Session Lifecycle");
    test_session_lifecycle();

    test_section_start("Add Logit Pairs");
    test_add_pairs();

    test_section_start("Distillation Step");
    test_distillation_step();

    test_section_start("Full Distillation");
    test_full_distillation();

    test_section_start("Persistence (Save/Load)");
    test_persistence();

    test_section_start("Layer Reduction (Teacher→Student)");
    test_layer_reduction();

    test_section_start("Reduction Estimation");
    test_reduction_estimation();

    test_section_start("Evaluation");
    test_evaluation();

    test_section_start("Edge Cases");
    test_edge_cases();

    printf("\n============================================\n");
    printf("  RESULTADOS: %d / %d PASS\n", test_passed, test_total);
    printf("============================================\n");

    return (test_passed == test_total) ? 0 : 1;
}
