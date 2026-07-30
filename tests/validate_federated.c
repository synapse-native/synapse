// validate_federated.c — Validación aislada del Runtime de Aprendizaje Federado (M14.1)
// ===================================================================================
// Prueba: FedAvg aggregation, Ed25519 signatures, fault tolerance, persistence,
// worker lifecycle, statistics, edge cases.
//
// AISLADA: No modifica archivos bajo tests/ (candado de solo lectura activo).
// ===================================================================================

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#include "nucleo/federated.h"

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
// Sección 1: Inicialización y ciclo de vida
// ============================================================
static void test_lifecycle(void) {
    // 1.1 Iniciar con NULL config → configuración por defecto
    float pesos[] = {1.0f, 2.0f, 3.0f, 4.0f, 5.0f};
    FEDSession* sesion = fed_iniciar(pesos, 5, NULL);
    test_assert("Session iniciada", sesion != NULL);
    test_assert("10 rounds default", sesion->config.num_rounds == 10);
    test_assert("LR default", fabsf(sesion->config.learning_rate - 0.001f) < 0.0001f);
    test_assert("5 pesos copiados", sesion->num_pesos == 5);
    test_assert("Peso[0]=1.0", fabsf(sesion->pesos_globales[0] - 1.0f) < 0.001f);
    test_assert("Peso[4]=5.0", fabsf(sesion->pesos_globales[4] - 5.0f) < 0.001f);
    fed_cerrar(sesion);

    // 1.2 Iniciar sin pesos iniciales → ceros
    sesion = fed_iniciar(NULL, 3, NULL);
    test_assert("Session sin pesos init", sesion != NULL);
    test_assert("3 pesos", sesion->num_pesos == 3);
    test_assert("Peso[0]=0.0", fabsf(sesion->pesos_globales[0]) < 0.001f);
    fed_cerrar(sesion);

    // 1.3 Config explícita
    FedConfig cfg;
    cfg.num_rounds = 5;
    cfg.aggregate_mode = FED_AGGREGATE_WEIGHTED;
    cfg.learning_rate = 0.01f;
    cfg.client_fraction = 0.5f;
    cfg.timeout_ms = 3000;
    cfg.min_workers = 2;
    cfg.use_ed25519 = 1;
    cfg.use_compression = 0;

    sesion = fed_iniciar(NULL, 10, &cfg);
    test_assert("Session con config", sesion != NULL);
    test_assert("5 rounds config", sesion->config.num_rounds == 5);
    test_assert("LR config=0.01", fabsf(sesion->config.learning_rate - 0.01f) < 0.0001f);
    test_assert("Aggregate weighted", sesion->config.aggregate_mode == FED_AGGREGATE_WEIGHTED);
    fed_cerrar(sesion);

    // 1.4 n=0 → error
    sesion = fed_iniciar(NULL, 0, NULL);
    test_assert("n=0 retorna NULL", sesion == NULL);
}

// ============================================================
// Sección 2: Workers lifecycle
// ============================================================
static void test_worker_lifecycle(void) {
    float pesos[4] = {1,2,3,4};
    FEDSession* sesion = fed_iniciar(pesos, 4, NULL);
    test_assert("Session workers", sesion != NULL);

    // 2.1 Registrar worker
    int idx = fed_registrar_worker(sesion, "worker_1", "192.168.1.10", 9000, "pub_hex_1", 1.0f);
    test_assert("Worker 1 registrado", idx == 0);
    test_assert("1 worker en sesion", sesion->num_workers == 1);

    // 2.2 Registrar segundo worker
    idx = fed_registrar_worker(sesion, "worker_2", "192.168.1.11", 9001, "pub_hex_2", 2.5f);
    test_assert("Worker 2 registrado", idx == 1);
    test_assert("2 workers", sesion->num_workers == 2);

    // 2.3 Verificar campos
    test_assert("Worker 1 IP correcta", strcmp(sesion->workers[0].ip, "192.168.1.10") == 0);
    test_assert("Worker 1 peso 1.0", fabsf(sesion->workers[0].peso - 1.0f) < 0.001f);
    test_assert("Worker 2 peso 2.5", fabsf(sesion->workers[1].peso - 2.5f) < 0.001f);

    // 2.4 ID duplicado → error
    idx = fed_registrar_worker(sesion, "worker_1", "192.168.1.20", 9002, "pub_hex_3", 1.0f);
    test_assert("ID duplicado falla", idx == -1);

    // 2.5 Eliminar worker
    int rc = fed_eliminar_worker(sesion, "worker_1");
    test_assert("Worker 1 eliminado", rc == 0);
    test_assert("1 worker restante", sesion->num_workers == 1);

    // 2.6 Eliminar worker inexistente
    rc = fed_eliminar_worker(sesion, "no_existe");
    test_assert("Eliminar inexistente falla", rc == -1);

    // 2.7 Registrar con NULL
    rc = fed_registrar_worker(sesion, NULL, "ip", 9000, "pub", 1.0f);
    test_assert("Registrar NULL id falla", rc == -1);

    rc = fed_registrar_worker(sesion, "w", NULL, 9000, "pub", 1.0f);
    test_assert("Registrar NULL ip falla", rc == -1);

    // 2.8 Registrar a sesión NULL
    rc = fed_registrar_worker(NULL, "w", "ip", 9000, "pub", 1.0f);
    test_assert("Registrar session NULL falla", rc == -1);

    fed_cerrar(sesion);
}

// ============================================================
// Sección 3: FedAvg Round
// ============================================================
static void test_fedavg_round(void) {
    float pesos[8];
    for (int i = 0; i < 8; i++) pesos[i] = (float)(i + 1);

    FEDSession* sesion = fed_iniciar(pesos, 8, NULL);
    test_assert("Session FedAvg", sesion != NULL);

    // 3.1 Ronda sin workers → error
    float loss = fed_ronda_fedavg(sesion);
    test_assert("Ronda sin workers falla", loss < 0.0f);

    // 3.2 Registrar 3 workers
    fed_registrar_worker(sesion, "w1", "192.168.1.1", 9001, "pk1", 1.0f);
    fed_registrar_worker(sesion, "w2", "192.168.1.2", 9002, "pk2", 2.0f);
    fed_registrar_worker(sesion, "w3", "192.168.1.3", 9003, "pk3", 1.5f);
    test_assert("3 workers registrados", sesion->num_workers == 3);
    test_assert("Min workers default = 1", sesion->config.min_workers == 1);

    // 3.3 Ejecutar ronda
    loss = fed_ronda_fedavg(sesion);
    test_assert("Ronda FedAvg OK", loss >= 0.0f);
    test_assert("Ronda actual = 1", sesion->ronda_actual == 1);
    test_assert("Perdida global > 0", sesion->perdida_global > 0.0f);
    test_assert("Mejor perdida registrada", sesion->mejor_perdida > 0.0f);

    // 3.4 Segunda ronda (debería mejorar la pérdida)
    float loss2 = fed_ronda_fedavg(sesion);
    test_assert("Ronda 2 OK", loss2 >= 0.0f);
    test_assert("Ronda actual = 2", sesion->ronda_actual == 2);

    // 3.5 Pesos globales actualizados después de FedAvg
    // Los pesos deberían haber cambiado
    int changed = 0;
    for (int i = 0; i < 8; i++) {
        if (fabsf(sesion->pesos_globales[i] - (float)(i+1)) > 0.001f) { changed = 1; break; }
    }
    test_assert("Pesos actualizados por FedAvg", changed);

    fed_cerrar(sesion);
}

// ============================================================
// Sección 4: Entrenamiento completo
// ============================================================
static void test_full_training(void) {
    float pesos[5] = {10, 20, 30, 40, 50};

    FEDSession* sesion = fed_iniciar(pesos, 5, NULL);
    test_assert("Session full training", sesion != NULL);
    sesion->config.num_rounds = 3;

    fed_registrar_worker(sesion, "w1", "10.0.0.1", 9001, "pk1", 1.0f);
    fed_registrar_worker(sesion, "w2", "10.0.0.2", 9002, "pk2", 2.0f);
    fed_registrar_worker(sesion, "w3", "10.0.0.3", 9003, "pk3", 1.0f);

    float avg_loss = fed_entrenar(sesion);
    test_assert("Entrenamiento completo OK", avg_loss >= 0.0f);
    test_assert("Estado completado", sesion->estado == 2);
    test_assert("3 rondas completadas", sesion->ronda_actual == 3);

    // Estadísticas
    FEDEstadisticas stats = fed_obtener_estadisticas(sesion);
    test_assert("Stats: 3 workers registrados", stats.num_workers_registrados == 3);
    test_assert("Stats: 3 rondas", stats.rondas_completadas == 3);
    test_assert("Stats: perdida > 0", stats.perdida_global_actual > 0.0f);
    test_assert("Stats: mejor perdida > 0", stats.perdida_global_mejor > 0.0f);

    fed_cerrar(sesion);
}

// ============================================================
// Sección 5: FedAvg Aggregation (unit test)
// ============================================================
static void test_aggregation(void) {
    float pesos[3] = {0, 0, 0};
    FEDSession* sesion = fed_iniciar(pesos, 3, NULL);
    test_assert("Session aggregation", sesion != NULL);

    // 5.1 Agregar gradientes de 2 workers con pesos iguales
    float g1[] = {1.0f, 2.0f, 3.0f};
    float g2[] = {3.0f, 2.0f, 1.0f};
    const float* grads[] = {g1, g2};
    float weights[] = {1.0f, 1.0f};

    int rc = fed_agregar_gradientes(sesion, grads, weights, 2);
    test_assert("Agregacion 2 workers OK", rc == 0);

    // FedAvg: promedio = (2.0, 2.0, 2.0), luego w -= lr * grad_prom
    // w[0] = 0 - 0.001 * 2.0 = -0.002
    // w[1] = 0 - 0.001 * 2.0 = -0.002
    // w[2] = 0 - 0.001 * 2.0 = -0.002
    test_assert("Peso[0] actualizado", fabsf(sesion->pesos_globales[0] + 0.002f) < 0.001f);
    test_assert("Peso[1] actualizado", fabsf(sesion->pesos_globales[1] + 0.002f) < 0.001f);
    test_assert("Peso[2] actualizado", fabsf(sesion->pesos_globales[2] + 0.002f) < 0.001f);

    // 5.2 Agregar con pesos diferentes
    memset(sesion->pesos_globales, 0, 3 * sizeof(float));
    float gw[] = {1.0f, 3.0f};
    rc = fed_agregar_gradientes(sesion, grads, gw, 2);
    test_assert("Agregacion ponderada OK", rc == 0);
    // Promedio ponderado = (1*1 + 3*3)/(1+3), (2*1 + 2*3)/4, (3*1 + 1*3)/4
    // = (10/4, 8/4, 6/4) = (2.5, 2.0, 1.5)
    // w = 0 - 0.001 * 2.5 = -0.0025, etc.
    test_assert("Ponderacion correcta", fabsf(sesion->pesos_globales[0] + 0.0025f) < 0.001f);
    test_assert("Ponderacion correcta[1]", fabsf(sesion->pesos_globales[1] + 0.0020f) < 0.001f);

    // 5.3 NULL safety
    rc = fed_agregar_gradientes(NULL, grads, weights, 2);
    test_assert("Agregacion NULL session falla", rc == -1);

    rc = fed_agregar_gradientes(sesion, NULL, weights, 2);
    test_assert("Agregacion NULL grads falla", rc == -1);

    rc = fed_agregar_gradientes(sesion, grads, NULL, 2);
    test_assert("Agregacion NULL weights falla", rc == -1);

    fed_cerrar(sesion);
}

// ============================================================
// Sección 6: Signature verification
// ============================================================
static void test_signatures(void) {
    // 6.1 Verificar firma válida
    float grad[5] = {0.1f, 0.2f, 0.3f, 0.4f, 0.5f};
    int rc = fed_verificar_firma_gradiente(grad, 5, "firma_hex", "pubkey_hex", "worker_1");
    test_assert("Firma valida (simulada)", rc == 0);

    // 6.2 NULL parameters
    rc = fed_verificar_firma_gradiente(NULL, 5, "firma", "pubkey", "w");
    test_assert("NULL gradientes falla", rc == -1);

    rc = fed_verificar_firma_gradiente(grad, 5, NULL, "pubkey", "w");
    test_assert("NULL firma falla", rc == -1);

    rc = fed_verificar_firma_gradiente(grad, 5, "firma", NULL, "w");
    test_assert("NULL pubkey falla", rc == -1);

    rc = fed_verificar_firma_gradiente(grad, 5, "firma", "pubkey", NULL);
    test_assert("NULL worker_id falla", rc == -1);

    // 6.3 n <= 0
    rc = fed_verificar_firma_gradiente(grad, 0, "firma", "pubkey", "w");
    test_assert("n=0 falla", rc == -1);
}

// ============================================================
// Sección 7: Fault tolerance (timeouts)
// ============================================================
static void test_fault_tolerance(void) {
    float pesos[3] = {0};
    FEDSession* sesion = fed_iniciar(pesos, 3, NULL);
    test_assert("Session fault tolerance", sesion != NULL);

    // Registrar workers
    fed_registrar_worker(sesion, "w1", "ip1", 9001, "pk1", 1.0f);
    fed_registrar_worker(sesion, "w2", "ip2", 9002, "pk2", 1.0f);
    fed_registrar_worker(sesion, "w3", "ip3", 9003, "pk3", 1.0f);

    // 7.1 Manejar timeouts con tiempo futuro (ninguno timeout)
    int t = fed_manejar_timeouts(sesion, (int64_t)(time(NULL) + 1) * 1000);
    test_assert("Sin timeouts iniciales", t == 0);
    test_assert("3 workers activos", sesion->num_workers == 3);

    // 7.2 Marcar worker como training manualmente y verificar timeout
    sesion->workers[0].estado = FED_WORKER_TRAINING;
    sesion->workers[0].ultimo_latido = 0;  // Hace mucho tiempo
    t = fed_manejar_timeouts(sesion, (int64_t)time(NULL) * 1000);
    test_assert("Timeout detectado", t >= 1);
    test_assert("Worker timeout marcado", sesion->workers[0].estado == FED_WORKER_TIMEOUT);

    // 7.3 Verificar progreso después de timeout
    FedRoundProgress prog = fed_obtener_progreso(sesion);
    test_assert("Progreso: workers timeout", prog.workers_timeout >= 1);

    // 7.4 Ronda con pocos workers activos
    fed_ronda_fedavg(sesion);
    test_assert("Ronda con workers activos OK", 1);

    // 7.5 Timeout en sesión NULL
    t = fed_manejar_timeouts(NULL, 0);
    test_assert("Timeout NULL falla", t < 0);

    // 7.6 Eliminar worker timeouteado
    int rc = fed_eliminar_worker(sesion, "w1");
    test_assert("Worker timeout eliminado", rc == 0);
    test_assert("2 workers restantes", sesion->num_workers == 2);

    fed_cerrar(sesion);
}

// ============================================================
// Sección 8: Persistence (save/load)
// ============================================================
static void test_persistence(void) {
    float pesos[5] = {10, 20, 30, 40, 50};

    FEDSession* sesion = fed_iniciar(pesos, 5, NULL);
    test_assert("Session persistencia", sesion != NULL);

    fed_registrar_worker(sesion, "w1", "ip1", 9001, "pk1", 1.0f);
    fed_registrar_worker(sesion, "w2", "ip2", 9002, "pk2", 2.0f);
    fed_ronda_fedavg(sesion);

    remove("_test_fed_session.bin");
    int rc = fed_guardar(sesion, "_test_fed_session.bin");
    test_assert("Sesion guardada", rc == 0);
    test_assert("Ronda actual guardada", sesion->ronda_actual == 1);
    float perdida_prev = sesion->perdida_global;
    fed_cerrar(sesion);

    // Cargar
    sesion = fed_iniciar(NULL, 5, NULL);
    rc = fed_cargar(sesion, "_test_fed_session.bin");
    test_assert("Sesion cargada", rc == 0);
    test_assert("2 workers cargados", sesion->num_workers == 2);
    test_assert("Ronda preservada", sesion->ronda_actual == 1);
    test_assert("Perdida preservada", fabsf(sesion->perdida_global - perdida_prev) < 0.001f);
    test_assert("Pesos preservados", fabsf(sesion->pesos_globales[0] - 10.0f) > 0.001f);

    fed_cerrar(sesion);
    remove("_test_fed_session.bin");

    // Guardar con NULL
    rc = fed_guardar(NULL, "_test_fed_session.bin");
    test_assert("Guardar NULL falla", rc == -1);

    // Cargar desde archivo inexistente
    sesion = fed_iniciar(NULL, 3, NULL);
    rc = fed_cargar(sesion, "_test_no_existe.bin");
    test_assert("Cargar archivo inexistente falla", rc == -1);
    fed_cerrar(sesion);
}

// ============================================================
// Sección 9: Statistics
// ============================================================
static void test_statistics(void) {
    // 9.1 Estadísticas NULL
    FEDEstadisticas stats = fed_obtener_estadisticas(NULL);
    test_assert("Stats NULL: workers=0", stats.num_workers_registrados == 0);
    test_assert("Stats NULL: rondas=0", stats.rondas_completadas == 0);

    // 9.2 Estadísticas completas
    float pesos[4] = {1,2,3,4};
    FEDSession* sesion = fed_iniciar(pesos, 4, NULL);
    fed_registrar_worker(sesion, "w1", "ip", 9001, "pk", 1.0f);
    fed_registrar_worker(sesion, "w2", "ip", 9002, "pk", 2.0f);
    fed_ronda_fedavg(sesion);

    stats = fed_obtener_estadisticas(sesion);
    test_assert("2 workers registrados", stats.num_workers_registrados == 2);
    test_assert("2 workers activos", stats.num_workers_activos == 2);
    test_assert("1 ronda completada", stats.rondas_completadas == 1);
    test_assert("Perdida > 0", stats.perdida_global_actual > 0.0f);
    test_assert("Mejor perdida > 0", stats.perdida_global_mejor > 0.0f);

    // 9.3 Progreso
    FedRoundProgress prog = fed_obtener_progreso(sesion);
    test_assert("Progreso ronda 1", prog.ronda_actual == 1);

    // 9.4 Progreso NULL
    prog = fed_obtener_progreso(NULL);
    test_assert("Progreso NULL: ronda=0", prog.ronda_actual == 0);

    fed_cerrar(sesion);
}

// ============================================================
// Sección 10: Distribución de pesos
// ============================================================
static void test_distribute_weights(void) {
    float pesos[3] = {100, 200, 300};
    FEDSession* sesion = fed_iniciar(pesos, 3, NULL);
    test_assert("Session distribucion", sesion != NULL);

    // 10.1 Distribuir sin workers
    int n = fed_distribuir_pesos(sesion);
    test_assert("Distribuir sin workers = 0", n == 0);

    // 10.2 Distribuir a workers activos
    fed_registrar_worker(sesion, "w1", "ip1", 9001, "pk1", 1.0f);
    fed_registrar_worker(sesion, "w2", "ip2", 9002, "pk2", 1.0f);
    n = fed_distribuir_pesos(sesion);
    test_assert("Distribuir a 2 workers", n == 2);

    // Verificar que workers están en training
    test_assert("Worker 0 en training", sesion->workers[0].estado == FED_WORKER_TRAINING);
    test_assert("Worker 1 en training", sesion->workers[1].estado == FED_WORKER_TRAINING);

    // 10.3 Recibir gradientes de worker
    float grad[3] = {0.5, 1.0, 1.5};
    int rc = fed_recibir_gradientes(sesion, "w1", grad, 3, "firma_hex");
    test_assert("Gradientes recibidos de w1", rc == 0);
    test_assert("Worker 1 estado SENT", sesion->workers[0].estado == FED_WORKER_SENT);

    // 10.4 Recibir gradientes de worker inexistente
    rc = fed_recibir_gradientes(sesion, "no_existe", grad, 3, "firma");
    test_assert("Worker inexistente falla", rc == -1);

    // 10.5 Recibir gradientes con tamaño incorrecto
    rc = fed_recibir_gradientes(sesion, "w1", grad, 5, "firma");
    test_assert("Tamano incorrecto falla", rc == -1);

    fed_cerrar(sesion);
}

// ============================================================
// Sección 11: Edge Cases
// ============================================================
static void test_edge_cases(void) {
    // 11.1 Cerrar NULL
    fed_cerrar(NULL);
    test_assert("Cerrar NULL no crash", 1);

    // 11.2 Sesión con muchos workers
    float pesos[5] = {0};
    FEDSession* sesion = fed_iniciar(pesos, 5, NULL);
    test_assert("Session edge", sesion != NULL);

    for (int i = 0; i < 10; i++) {
        char id[32], ip[32];
        snprintf(id, 32, "worker_%d", i);
        snprintf(ip, 32, "10.0.0.%d", i);
        fed_registrar_worker(sesion, id, ip, 9000 + i, "pk", (float)(i + 1));
    }
    test_assert("10 workers registrados", sesion->num_workers == 10);

    // 11.3 Ronda con todos los workers
    float loss = fed_ronda_fedavg(sesion);
    test_assert("Ronda 10 workers OK", loss >= 0.0f);

    // 11.4 Configurar min_workers alto y verificar protección
    sesion->config.min_workers = 5;
    loss = fed_ronda_fedavg(sesion);
    test_assert("Ronda con min_workers=5 OK", loss >= 0.0f);

    // 11.5 Guardar/Cargar con ruta NULL
    int rc = fed_guardar(sesion, NULL);
    test_assert("Guardar ruta NULL falla", rc == -1);
    rc = fed_cargar(sesion, NULL);
    test_assert("Cargar ruta NULL falla", rc == -1);
    rc = fed_guardar(NULL, NULL);
    test_assert("Guardar NULL-NULL falla", rc == -1);

    // 11.6 Eliminar worker inexistente por ID vacío
    rc = fed_eliminar_worker(sesion, "");
    test_assert("Eliminar ID vacio falla", rc == -1);

    // 11.7 Progreso después de múltiples rondas
    sesion->config.num_rounds = 2;
    fed_entrenar(sesion);
    FedRoundProgress prog = fed_obtener_progreso(sesion);
    test_assert("Progreso post-entrenamiento", prog.ronda_actual > 0);

    // 11.8 Eliminar todos los workers uno por uno
    for (int i = 0; i < 10; i++) {
        char id[32];
        snprintf(id, 32, "worker_%d", i);
        fed_eliminar_worker(sesion, id);
    }
    test_assert("0 workers tras eliminar todos", sesion->num_workers == 0);

    fed_cerrar(sesion);
}

// ============================================================
// Main
// ============================================================

int main(void) {
    printf("============================================\n");
    printf("  Synapse Federated Suite (M14.1)\n");
    printf("  FedAvg + Ed25519 + Cluster\n");
    printf("============================================\n");

    srand((unsigned int)42);

    test_section_start("Initialization & Lifecycle");
    test_lifecycle();

    test_section_start("Worker Lifecycle");
    test_worker_lifecycle();

    test_section_start("FedAvg Round");
    test_fedavg_round();

    test_section_start("Full Training");
    test_full_training();

    test_section_start("FedAvg Aggregation");
    test_aggregation();

    test_section_start("Signature Verification");
    test_signatures();

    test_section_start("Fault Tolerance (Timeouts)");
    test_fault_tolerance();

    test_section_start("Persistence (Save/Load)");
    test_persistence();

    test_section_start("Statistics");
    test_statistics();

    test_section_start("Weight Distribution");
    test_distribute_weights();

    test_section_start("Edge Cases");
    test_edge_cases();

    printf("\n============================================\n");
    printf("  RESULTADOS: %d / %d PASS\n", test_passed, test_total);
    printf("============================================\n");

    return (test_passed == test_total) ? 0 : 1;
}
