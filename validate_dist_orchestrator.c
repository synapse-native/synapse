// validate_dist_orchestrator.c — Validación aislada del Orquestador de Entrenamiento Distribuido (M14.2)
// =====================================================================================================
// Prueba: dataset partitioning, worker assignment, epoch coordination, fault recovery,
// persistencia, integración con federated/fine-tuning/distillation, edge cases.
//
// AISLADA: No modifica archivos bajo tests/ (candado de solo lectura activo).
// =====================================================================================================

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#include "nucleo/dist_orchestrator.h"

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
    OrchSession* sesion = orch_iniciar(NULL);
    test_assert("Session iniciada default", sesion != NULL);
    test_assert("5 epochs default", sesion->config.num_epochs == 5);
    test_assert("LR default", fabsf(sesion->config.learning_rate - 0.001f) < 0.0001f);
    test_assert("Estado IDLE", sesion->estado == ORCH_STATE_IDLE);
    test_assert("0 epocas", sesion->epoca_actual == 0);
    test_assert("0 asignaciones", sesion->num_assignments == 0);
    test_assert("0 particiones", sesion->num_particiones == 0);
    orch_cerrar(sesion);

    // Config explícita
    OrchConfig cfg;
    cfg.assign_mode = ORCH_ASSIGN_CAPACITY;
    cfg.sync_mode = ORCH_SYNC_ASYNCHRONOUS;
    cfg.failover_strategy = ORCH_FAILOVER_REDISTRIBUTE;
    cfg.max_retries = 5;
    cfg.sync_fraction = 0.5f;
    cfg.learning_rate = 0.01f;
    cfg.num_epochs = 10;
    cfg.num_partitions = 8;
    cfg.dataset_size = 5000;
    cfg.client_fraction = 0.8f;

    sesion = orch_iniciar(&cfg);
    test_assert("Session config explicita", sesion != NULL);
    test_assert("10 epochs config", sesion->config.num_epochs == 10);
    test_assert("LR=0.01 config", fabsf(sesion->config.learning_rate - 0.01f) < 0.0001f);
    test_assert("Assign CAPACITY", sesion->config.assign_mode == ORCH_ASSIGN_CAPACITY);
    orch_cerrar(sesion);

    // Cerrar NULL
    orch_cerrar(NULL);
    test_assert("Cerrar NULL no crash", 1);
}

// ============================================================
// Sección 2: Partición de dataset
// ============================================================
static void test_partitioning(void) {
    OrchSession* sesion = orch_iniciar(NULL);
    test_assert("Session partition", sesion != NULL);

    // 2.1 Particionar 1000 ejemplos en 4 partes
    int n = orch_crear_particiones(sesion, 1000, NULL);
    test_assert("4 particiones creadas", n == 4);
    test_assert("Particiones en sesion", sesion->num_particiones == 4);
    test_assert("Estado PARTITIONING", sesion->estado == ORCH_STATE_PARTITIONING);

    // Verificar distribución (1000/4 = 250 cada una)
    test_assert("Particion 0: 250 ejemplos", sesion->particiones[0].num_ejemplos == 250);
    test_assert("Particion 1: 250 ejemplos", sesion->particiones[1].num_ejemplos == 250);
    test_assert("Particion 2: 250 ejemplos", sesion->particiones[2].num_ejemplos == 250);
    test_assert("Particion 3: 250 ejemplos", sesion->particiones[3].num_ejemplos == 250);

    // Índices
    test_assert("Particion 0 inicio=0", sesion->particiones[0].inicio_idx == 0);
    test_assert("Particion 1 inicio=250", sesion->particiones[1].inicio_idx == 250);
    test_assert("Particion 3 inicio=750", sesion->particiones[3].inicio_idx == 750);

    // Pesos por defecto = 1.0
    test_assert("Peso default", fabsf(sesion->particiones[0].peso - 1.0f) < 0.001f);

    // Worker no asignado aún
    test_assert("Worker no asignado", sesion->particiones[0].worker_asignado[0] == '\0');

    // Índices globales creados
    test_assert("Indices globales OK", sesion->particiones[0].indices_globales != NULL);
    test_assert("Indice[0]=0", sesion->particiones[0].indices_globales[0] == 0);

    orch_cerrar(sesion);

    // 2.2 Dataset con resto
    sesion = orch_iniciar(NULL);
    sesion->config.num_partitions = 3;
    n = orch_crear_particiones(sesion, 10, NULL);
    test_assert("3 particiones (10/3)", n == 3);
    // 10/3 = 3, resto 1 → [4, 3, 3]
    test_assert("Particion 0: 4 ejemplos", sesion->particiones[0].num_ejemplos == 4);
    test_assert("Particion 1: 3 ejemplos", sesion->particiones[1].num_ejemplos == 3);
    test_assert("Particion 2: 3 ejemplos", sesion->particiones[2].num_ejemplos == 3);
    orch_cerrar(sesion);

    // 2.3 Dataset inválido
    sesion = orch_iniciar(NULL);
    n = orch_crear_particiones(sesion, 0, NULL);
    test_assert("Dataset 0 falla", n < 0);
    n = orch_crear_particiones(NULL, 100, NULL);
    test_assert("Session NULL falla", n < 0);
    orch_cerrar(sesion);
}

// ============================================================
// Sección 3: Asignación de workers a particiones
// ============================================================
static void test_worker_assignment(void) {
    OrchSession* sesion = orch_iniciar(NULL);
    test_assert("Session assignment", sesion != NULL);
    orch_crear_particiones(sesion, 100, NULL);

    // 3.1 Asignar 3 workers a 4 particiones (round-robin)
    const char* workers[] = {"w1", "w2", "w3"};
    float caps[] = {1.0f, 2.0f, 1.5f};
    int n = orch_asignar_workers(sesion, workers, 3, caps);
    test_assert("3 workers asignados", n == 3);
    test_assert("Estado ASSIGNING", sesion->estado == ORCH_STATE_ASSIGNING);

    test_assert("Worker w1 asignado", strcmp(sesion->assignments[0].worker_id, "w1") == 0);
    test_assert("Worker w2 asignado", strcmp(sesion->assignments[1].worker_id, "w2") == 0);
    test_assert("Worker w3 asignado", strcmp(sesion->assignments[2].worker_id, "w3") == 0);

    // 3.2 Verificar partición obtenida por worker
    OrchPartition* part = orch_obtener_particion(sesion, "w1");
    test_assert("Particion de w1 encontrada", part != NULL);
    test_assert("w1 tiene 25 ejemplos", part->num_ejemplos == 25);

    part = orch_obtener_particion(sesion, "w3");
    test_assert("Particion de w3 encontrada", part != NULL);

    // Worker inexistente
    part = orch_obtener_particion(sesion, "no_existe");
    test_assert("Worker inexistente NULL", part == NULL);

    // 3.3 Asignación con params inválidos
    n = orch_asignar_workers(NULL, workers, 3, caps);
    test_assert("Session NULL falla", n < 0);

    n = orch_asignar_workers(sesion, NULL, 3, caps);
    test_assert("Workers NULL falla", n < 0);

    n = orch_asignar_workers(sesion, workers, 0, caps);
    test_assert("n=0 falla", n < 0);

    // 3.4 Sin particiones creadas
    OrchSession* sesion2 = orch_iniciar(NULL);
    n = orch_asignar_workers(sesion2, workers, 3, caps);
    test_assert("Sin particiones falla", n < 0);
    orch_cerrar(sesion2);

    orch_cerrar(sesion);
}

// ============================================================
// Sección 4: Ejecución de época
// ============================================================
static void test_epoch_execution(void) {
    OrchSession* sesion = orch_iniciar(NULL);
    test_assert("Session epoch", sesion != NULL);

    // 4.1 Época sin asignaciones
    float loss = orch_ejecutar_epoch(sesion);
    test_assert("Epoch sin asignaciones falla", loss < 0.0f);

    // 4.2 Configurar y ejecutar época
    orch_crear_particiones(sesion, 200, NULL);
    const char* workers[] = {"w1", "w2"};
    float caps[] = {1.0f, 2.0f};
    orch_asignar_workers(sesion, workers, 2, caps);

    loss = orch_ejecutar_epoch(sesion);
    test_assert("Epoch ejecutada OK", loss >= 0.0f);
    test_assert("1 epoca completada", sesion->epoca_actual == 1);
    test_assert("Perdida global > 0", sesion->perdida_global > 0.0f);
    test_assert("Estado AGGREGATING", sesion->estado == ORCH_STATE_AGGREGATING);

    // 4.3 Verificar asignaciones completadas
    test_assert("w1 completado", sesion->assignments[0].estado == 2);
    test_assert("w2 completado", sesion->assignments[1].estado == 2);
    test_assert("w1 pasos > 0", sesion->assignments[0].num_pasos_ejecutados > 0);

    // 4.4 Segunda época
    // Resetear asignaciones
    for (int i = 0; i < sesion->num_assignments; i++) {
        sesion->assignments[i].estado = 0;
    }
    loss = orch_ejecutar_epoch(sesion);
    test_assert("Epoch 2 OK", loss >= 0.0f);
    test_assert("2 epocas", sesion->epoca_actual == 2);

    orch_cerrar(sesion);
}

// ============================================================
// Sección 5: Entrenamiento completo
// ============================================================
static void test_full_training(void) {
    OrchConfig cfg;
    cfg.assign_mode = ORCH_ASSIGN_ROUND_ROBIN;
    cfg.sync_mode = ORCH_SYNC_SYNCHRONOUS;
    cfg.failover_strategy = ORCH_FAILOVER_RETRY;
    cfg.max_retries = 3;
    cfg.sync_fraction = 1.0f;
    cfg.learning_rate = 0.001f;
    cfg.num_epochs = 3;
    cfg.num_partitions = 4;
    cfg.dataset_size = 400;
    cfg.client_fraction = 1.0f;

    OrchSession* sesion = orch_iniciar(&cfg);
    test_assert("Session full training", sesion != NULL);

    orch_crear_particiones(sesion, 400, NULL);
    const char* workers[] = {"w1", "w2", "w3"};
    float caps[] = {1.0f, 2.0f, 1.0f};
    orch_asignar_workers(sesion, workers, 3, caps);

    float avg_loss = orch_entrenar(sesion);
    test_assert("Entrenamiento completo OK", avg_loss >= 0.0f);
    test_assert("Estado COMPLETED", sesion->estado == ORCH_STATE_COMPLETED);
    test_assert("3 epocas", sesion->epoca_actual == 3);

    // Estadísticas
    ORCHEstadisticas stats = orch_obtener_estadisticas(sesion);
    test_assert("Stats: 3 workers", stats.num_workers_asignados == 3);
    test_assert("Stats: 4 particiones", stats.num_particiones_creadas == 4);
    test_assert("Stats: 3 epocas", stats.epocas_completadas == 3);
    test_assert("Stats: perdida > 0", stats.perdida_promedio > 0.0f);

    // Progreso
    OrchProgress prog = orch_obtener_progreso(sesion);
    test_assert("Progreso COMPLETED", prog.estado == ORCH_STATE_COMPLETED);
    test_assert("Progreso 3 epocas", prog.epoca_actual == 3);

    orch_cerrar(sesion);
}

// ============================================================
// Sección 6: Fault tolerance
// ============================================================
static void test_fault_tolerance(void) {
    OrchSession* sesion = orch_iniciar(NULL);
    test_assert("Session fault tolerance", sesion != NULL);

    orch_crear_particiones(sesion, 100, NULL);
    const char* workers[] = {"w1", "w2"};
    float caps[] = {1.0f, 1.0f};
    orch_asignar_workers(sesion, workers, 2, caps);

    // 6.1 Manejar fallo de worker inexistente
    int rc = orch_manejar_fallo(sesion, "no_existe");
    test_assert("Fallo worker inexistente", rc < 0);

    // 6.2 Fallo con RETRY strategy
    test_assert("w1 estado pendiente", sesion->assignments[0].estado == 0);

    // Fallar w1 y verificar reintento
    rc = orch_manejar_fallo(sesion, "w1");
    test_assert("Fallo w1 manejado (retry)", rc == 0);
    test_assert("w1 pendiente para retry", sesion->assignments[0].estado == 0);
    test_assert("w1 reintentos=1", sesion->assignments[0].reintentos == 1);

    // Fallar w1 múltiples veces hasta exceder max_retries
    rc = orch_manejar_fallo(sesion, "w1");
    rc = orch_manejar_fallo(sesion, "w1");
    rc = orch_manejar_fallo(sesion, "w1");
    test_assert("w1 fallo permanente", sesion->assignments[0].estado == 3);

    // 6.3 Redistribución
    // Cambiar estrategia a REDISTRIBUTE y probar
    sesion->config.failover_strategy = ORCH_FAILOVER_REDISTRIBUTE;
    rc = orch_manejar_fallo(sesion, "w2");
    test_assert("Fallo w2 - redistribuir", rc == 0);

    int redist = orch_redistribuir(sesion);
    test_assert("Redistribucion ejecutada", redist >= 0);

    // 6.4 Fallo con IGNORE strategy
    sesion->config.failover_strategy = ORCH_FAILOVER_IGNORE;
    rc = orch_manejar_fallo(sesion, "w1");
    test_assert("Fallo w1 - ignore", rc == 0);

    // 6.5 Fallo en sesión NULL
    rc = orch_manejar_fallo(NULL, "w1");
    test_assert("Fallo NULL sesion", rc < 0);

    orch_cerrar(sesion);
}

// ============================================================
// Sección 7: Integración con Federated / Fine-Tuning / Distillation
// ============================================================
static void test_integration(void) {
    OrchSession* sesion = orch_iniciar(NULL);
    test_assert("Session integracion", sesion != NULL);

    // 7.1 Conectar federated
    float pesos[5] = {1,2,3,4,5};
    FEDSession* fed = fed_iniciar(pesos, 5, NULL);
    int rc = orch_conectar_federated(sesion, fed);
    test_assert("Federated conectado", rc == 0);
    test_assert("fed_sesion asignado", sesion->fed_sesion == fed);

    // 7.2 Conectar fine-tuning
    FTConfig ft_cfg;
    memset(&ft_cfg, 0, sizeof(ft_cfg));
    ft_cfg.learning_rate = 0.001f;
    ft_cfg.rank = 8;
    ft_cfg.alpha = 16.0f;
    ft_cfg.num_epochs = 1;
    FTSession* ft = ft_iniciar(NULL, &ft_cfg);
    rc = orch_conectar_fine_tuning(sesion, ft);
    test_assert("Fine-tuning conectado", rc == 0);
    test_assert("ft_sesion asignado", sesion->ft_sesion == ft);

    // 7.3 Conectar destilación
    KDSession* kd = kd_iniciar(NULL);
    rc = orch_conectar_distillation(sesion, kd);
    test_assert("Destilacion conectada", rc == 0);
    test_assert("kd_sesion asignado", sesion->kd_sesion == kd);

    // 7.4 Conexiones con NULL
    rc = orch_conectar_federated(NULL, fed);
    test_assert("Federated session NULL falla", rc < 0);

    rc = orch_conectar_federated(sesion, NULL);
    test_assert("Federated NULL falla", rc < 0);

    rc = orch_conectar_fine_tuning(NULL, ft);
    test_assert("FT session NULL falla", rc < 0);

    rc = orch_conectar_distillation(NULL, kd);
    test_assert("KD session NULL falla", rc < 0);

    // Limpiar
    ft_cerrar(ft);
    kd_cerrar(kd);
    fed_cerrar(fed);
    orch_cerrar(sesion);
}

// ============================================================
// Sección 8: Persistencia (save/load)
// ============================================================
static void test_persistence(void) {
    OrchSession* sesion = orch_iniciar(NULL);
    test_assert("Session persistencia", sesion != NULL);
    sesion->config.num_epochs = 4;

    orch_crear_particiones(sesion, 200, NULL);
    const char* workers[] = {"w1", "w2"};
    float caps[] = {1.0f, 1.0f};
    orch_asignar_workers(sesion, workers, 2, caps);
    orch_ejecutar_epoch(sesion);

    float perdida_prev = sesion->perdida_global;
    int epoca_prev = sesion->epoca_actual;

    remove("_test_orch_session.bin");
    int rc = orch_guardar(sesion, "_test_orch_session.bin");
    test_assert("Sesion guardada", rc == 0);
    orch_cerrar(sesion);

    // Cargar
    sesion = orch_iniciar(NULL);
    rc = orch_cargar(sesion, "_test_orch_session.bin");
    test_assert("Sesion cargada", rc == 0);
    test_assert("2 asignaciones cargadas", sesion->num_assignments == 2);
    test_assert("4 particiones cargadas", sesion->num_particiones == 4);
    test_assert("Epoca preservada", sesion->epoca_actual == epoca_prev);
    test_assert("Perdida preservada", fabsf(sesion->perdida_global - perdida_prev) < 0.001f);

    orch_cerrar(sesion);
    remove("_test_orch_session.bin");

    // Guardar NULL
    rc = orch_guardar(NULL, "_test_orch_session.bin");
    test_assert("Guardar NULL falla", rc == -1);

    // Cargar archivo inexistente
    sesion = orch_iniciar(NULL);
    rc = orch_cargar(sesion, "_test_no_existe.bin");
    test_assert("Cargar inexistente falla", rc == -1);
    orch_cerrar(sesion);
}

// ============================================================
// Sección 9: Estadísticas y progreso
// ============================================================
static void test_stats(void) {
    // 9.1 Estadísticas NULL
    ORCHEstadisticas stats = orch_obtener_estadisticas(NULL);
    test_assert("Stats NULL workers=0", stats.num_workers_asignados == 0);
    test_assert("Stats NULL particiones=0", stats.num_particiones_creadas == 0);

    // 9.2 Progreso NULL
    OrchProgress prog = orch_obtener_progreso(NULL);
    test_assert("Progreso NULL estado=0", prog.estado == 0);

    // 9.3 Estadísticas completas
    OrchSession* sesion = orch_iniciar(NULL);
    orch_crear_particiones(sesion, 100, NULL);
    const char* workers[] = {"w1", "w2"};
    float caps[] = {1.0f, 1.0f};
    orch_asignar_workers(sesion, workers, 2, caps);
    orch_ejecutar_epoch(sesion);

    stats = orch_obtener_estadisticas(sesion);
    test_assert("Stats 2 workers", stats.num_workers_asignados == 2);
    test_assert("Stats 4 particiones", stats.num_particiones_creadas == 4);
    test_assert("Stats 1 epoca", stats.epocas_completadas == 1);
    test_assert("Stats perdida > 0", stats.perdida_promedio > 0.0f);
    test_assert("Stats exito > 0", stats.tasa_exito_asignacion > 0.0f);

    prog = orch_obtener_progreso(sesion);
    test_assert("Progreso epoca 1", prog.epoca_actual == 1);
    test_assert("Progreso workers completados >= 1", prog.workers_completados >= 1);

    orch_cerrar(sesion);
}

// ============================================================
// Sección 10: Edge cases
// ============================================================
static void test_edge_cases(void) {
    // 10.1 Cerrar NULL
    orch_cerrar(NULL);
    test_assert("Cerrar NULL no crash", 1);

    // 10.2 Dataset con 1 ejemplo
    OrchSession* sesion = orch_iniciar(NULL);
    sesion->config.num_partitions = 1;
    int n = orch_crear_particiones(sesion, 1, NULL);
    test_assert("Dataset 1 ejemplo = 1 particion", n == 1);
    test_assert("Particion 1 elemento", sesion->particiones[0].num_ejemplos == 1);
    orch_cerrar(sesion);

    // 10.3 Workers sin particiones suficientes
    sesion = orch_iniciar(NULL);
    sesion->config.num_partitions = 2;
    orch_crear_particiones(sesion, 100, NULL);
    const char* workers[] = {"w1", "w2", "w3", "w4", "w5"};
    float caps[] = {1,1,1,1,1};
    n = orch_asignar_workers(sesion, workers, 5, caps);
    test_assert("Max 2 workers asignados (solo 2 particiones)", n == 2);
    orch_cerrar(sesion);

    // 10.4 Época después de fallo de todos los workers
    sesion = orch_iniciar(NULL);
    orch_crear_particiones(sesion, 50, NULL);
    const char* workers2[] = {"w1"};
    float caps2[] = {1.0f};
    orch_asignar_workers(sesion, workers2, 1, caps2);

    // Marcar worker como fallado permanente
    sesion->assignments[0].estado = 3;

    float loss = orch_ejecutar_epoch(sesion);
    test_assert("Epoch con todos fallados", loss < 0.0f);
    orch_cerrar(sesion);

    // 10.5 Redistribución sin workers activos
    sesion = orch_iniciar(NULL);
    orch_crear_particiones(sesion, 50, NULL);
    orch_asignar_workers(sesion, workers2, 1, caps2);
    sesion->assignments[0].estado = 3;
    n = orch_redistribuir(sesion);
    test_assert("Redistribuir sin workers activos = 0", n == 0);
    orch_cerrar(sesion);

    // 10.6 Particionar sin session
    n = orch_crear_particiones(NULL, 100, NULL);
    test_assert("Crear particiones NULL falla", n < 0);

    // 10.7 Redistribuir con NULL
    n = orch_redistribuir(NULL);
    test_assert("Redistribuir NULL falla", n < 0);

    // 10.8 Guardar/Cargar con ruta NULL
    sesion = orch_iniciar(NULL);
    int rc = orch_guardar(sesion, NULL);
    test_assert("Guardar ruta NULL falla", rc == -1);
    rc = orch_cargar(sesion, NULL);
    test_assert("Cargar ruta NULL falla", rc == -1);
    orch_cerrar(sesion);
}

// ============================================================
// Main
// ============================================================

int main(void) {
    printf("================================================\n");
    printf("  Synapse Distributed Orchestrator Suite (M14.2)\n");
    printf("  Dataset Partitioning + Dynamic Assignment\n");
    printf("================================================\n");

    srand((unsigned int)42);

    test_section_start("Initialization & Lifecycle");
    test_lifecycle();

    test_section_start("Dataset Partitioning");
    test_partitioning();

    test_section_start("Worker Assignment");
    test_worker_assignment();

    test_section_start("Epoch Execution");
    test_epoch_execution();

    test_section_start("Full Training");
    test_full_training();

    test_section_start("Fault Tolerance");
    test_fault_tolerance();

    test_section_start("Integration (Federated + FT + KD)");
    test_integration();

    test_section_start("Persistence (Save/Load)");
    test_persistence();

    test_section_start("Statistics & Progress");
    test_stats();

    test_section_start("Edge Cases");
    test_edge_cases();

    printf("\n================================================\n");
    printf("  RESULTADOS: %d / %d PASS\n", test_passed, test_total);
    printf("================================================\n");

    return (test_passed == test_total) ? 0 : 1;
}
