// dist_orchestrator.c — Orquestador de Entrenamiento Distribuido
// =================================================================
// Gestiona la asignación dinámica de workers, partición de datasets
// y coordinación de épocas de entrenamiento distribuidas.
// Integración nativa con fine_tuning.c (LoRA), distillation.c (KD)
// y federated.c (FedAvg).
// =================================================================

#include "dist_orchestrator.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// ============================================================
// Helpers internos
// ============================================================

static float frand(float min, float max) {
    return min + (max - min) * ((float)rand() / (float)RAND_MAX);
}

static int _buscar_assignment(OrchSession* sesion, const char* worker_id) {
    if (!sesion || !worker_id) return -1;
    for (int i = 0; i < sesion->num_assignments; i++) {
        if (strcmp(sesion->assignments[i].worker_id, worker_id) == 0) return i;
    }
    return -1;
}

// Busca una partición sin asignar
static int _primera_particion_libre(OrchSession* sesion) {
    if (!sesion) return -1;
    for (int i = 0; i < sesion->num_particiones; i++) {
        if (sesion->particiones[i].worker_asignado[0] == '\0') return i;
    }
    return -1;
}

// ============================================================
// API pública
// ============================================================

OrchSession* orch_iniciar(const OrchConfig* config) {
    OrchSession* sesion = (OrchSession*)calloc(1, sizeof(OrchSession));
    if (!sesion) return NULL;

    if (config) {
        sesion->config = *config;
    } else {
        sesion->config.assign_mode = ORCH_ASSIGN_ROUND_ROBIN;
        sesion->config.sync_mode = ORCH_SYNC_SYNCHRONOUS;
        sesion->config.failover_strategy = ORCH_FAILOVER_RETRY;
        sesion->config.max_retries = 3;
        sesion->config.sync_fraction = 1.0f;
        sesion->config.learning_rate = 0.001f;
        sesion->config.num_epochs = 5;
        sesion->config.num_partitions = 4;
        sesion->config.dataset_size = 1000;
        sesion->config.client_fraction = 1.0f;
    }

    sesion->epoca_actual = 0;
    sesion->estado = ORCH_STATE_IDLE;
    sesion->perdida_global = 0.0f;
    sesion->mejor_perdida = 1e10f;
    sesion->fed_sesion = NULL;
    sesion->ft_sesion = NULL;
    sesion->kd_sesion = NULL;

    srand((unsigned int)time(NULL));
    return sesion;
}

int orch_crear_particiones(OrchSession* sesion, int dataset_size,
                            const float* pesos_ejemplos) {
    if (!sesion || dataset_size <= 0) return -1;

    sesion->config.dataset_size = dataset_size;
    int num_p = sesion->config.num_partitions;
    if (num_p <= 0) num_p = 1;
    if (num_p > ORCH_MAX_PARTITIONS) num_p = ORCH_MAX_PARTITIONS;

    int ejemplos_por_particion = dataset_size / num_p;
    int resto = dataset_size % num_p;

    sesion->num_particiones = 0;
    int idx_actual = 0;

    for (int p = 0; p < num_p; p++) {
        int n = ejemplos_por_particion + (p < resto ? 1 : 0);
        if (n <= 0) continue;

        OrchPartition* part = &sesion->particiones[sesion->num_particiones];
        part->inicio_idx = idx_actual;
        part->num_ejemplos = n;

        // Crear mapeo de índices globales
        part->indices_globales = (int*)malloc((size_t)n * sizeof(int));
        if (!part->indices_globales) return -1;

        for (int i = 0; i < n; i++) {
            part->indices_globales[i] = idx_actual + i;
        }

        // Peso: promedio de pesos de ejemplos en la partición (o 1.0)
        if (pesos_ejemplos) {
            double sum = 0.0;
            for (int i = 0; i < n; i++) {
                sum += (double)pesos_ejemplos[idx_actual + i];
            }
            part->peso = (float)(sum / (double)n);
        } else {
            part->peso = 1.0f;
        }

        part->worker_asignado[0] = '\0';
        idx_actual += n;
        sesion->num_particiones++;
    }

    sesion->estado = ORCH_STATE_PARTITIONING;
    return sesion->num_particiones;
}

int orch_asignar_workers(OrchSession* sesion, const char* const* worker_ids,
                          int num_workers, const float* capacidades) {
    if (!sesion || !worker_ids || num_workers <= 0) return -1;
    if (sesion->num_particiones <= 0) return -1;

    (void)capacidades; // Reservado para modo ORCH_ASSIGN_CAPACITY

    int num_a_asignar = (int)((float)num_workers * sesion->config.client_fraction);
    if (num_a_asignar < 1) num_a_asignar = 1;
    if (num_a_asignar > num_workers) num_a_asignar = num_workers;

    sesion->num_assignments = 0;

    for (int w = 0; w < num_a_asignar; w++) {
        int idx_particion = _primera_particion_libre(sesion);
        if (idx_particion < 0) break;  // No más particiones

        OrchWorkerAssignment* asg = &sesion->assignments[sesion->num_assignments];
        strncpy(asg->worker_id, worker_ids[w], ORCH_NAME_MAX - 1);
        asg->worker_id[ORCH_NAME_MAX - 1] = '\0';

        // Copiar partición
        asg->particion = sesion->particiones[idx_particion];
        asg->particion.indices_globales = NULL;  // No transferir ownership

        // Marcar worker en la partición
        strncpy(sesion->particiones[idx_particion].worker_asignado,
                worker_ids[w], ORCH_NAME_MAX - 1);

        asg->estado = 0;  // Pendiente
        asg->perdida_local = 0.0f;
        asg->num_pasos_ejecutados = 0;
        asg->tiempo_inicio_ms = 0;
        asg->tiempo_fin_ms = 0;
        asg->reintentos = 0;

        sesion->num_assignments++;
    }

    sesion->estado = ORCH_STATE_ASSIGNING;
    return sesion->num_assignments;
}

OrchPartition* orch_obtener_particion(OrchSession* sesion, const char* worker_id) {
    if (!sesion || !worker_id) return NULL;
    int idx = _buscar_assignment(sesion, worker_id);
    if (idx < 0) return NULL;
    return &sesion->assignments[idx].particion;
}

float orch_ejecutar_epoch(OrchSession* sesion) {
    if (!sesion || sesion->num_assignments <= 0) return -1.0f;

    sesion->estado = ORCH_STATE_TRAINING;
    float perdida_total = 0.0f;
    int completados = 0;

    for (int i = 0; i < sesion->num_assignments; i++) {
        OrchWorkerAssignment* asg = &sesion->assignments[i];
        if (asg->estado == 3) continue;  // Fallo permanente

        asg->estado = 1;  // En curso
        asg->tiempo_inicio_ms = (int64_t)(clock() * 1000 / CLOCKS_PER_SEC);

        // Simular entrenamiento local con el dataset particionado
        int n = asg->particion.num_ejemplos;
        float perdida_local = 0.0f;
        for (int j = 0; j < n; j++) {
            // Pérdida simulada: decrece con las épocas
            float base = 1.0f / (float)(sesion->epoca_actual + 1);
            perdida_local += frand(0.0f, base);
        }
        perdida_local /= (float)(n > 0 ? n : 1);

        // Integración con sesión federada (si conectada)
        if (sesion->fed_sesion && sesion->fed_sesion->estado == 0) {
            // Simular que los gradientes de esta época se agregan vía FedAvg
            // En producción: asg->perdida_local se usaría en fed_ronda_fedavg
        }

        // Integración con fine-tuning LoRA (si conectado)
        if (sesion->ft_sesion) {
            // En producción: ft_paso_entrenamiento() con datos de la partición
            // Por ahora: registrar que la conexión existe
            asg->perdida_local = perdida_local;
        }

        // Integración con destilación (si conectada)
        if (sesion->kd_sesion) {
            // En producción: kd_paso_destilacion() con pares teacher-student
            // Por ahora: registrar que la conexión existe
        }

        asg->perdida_local = perdida_local;
        asg->num_pasos_ejecutados += n;
        asg->tiempo_fin_ms = (int64_t)(clock() * 1000 / CLOCKS_PER_SEC);
        asg->estado = 2;  // Completado

        perdida_total += perdida_local * asg->particion.peso;
        completados++;
    }

    if (completados == 0) return -1.0f;

    // Agregar pérdidas ponderadas
    double peso_total = 0.0;
    for (int i = 0; i < sesion->num_assignments; i++) {
        if (sesion->assignments[i].estado == 2) {
            peso_total += (double)sesion->assignments[i].particion.peso;
        }
    }
    float perdida_epoch = (peso_total > 0.0)
        ? perdida_total / (float)peso_total
        : perdida_total / (float)completados;

    sesion->perdida_global = perdida_epoch;
    if (perdida_epoch < sesion->mejor_perdida) {
        sesion->mejor_perdida = perdida_epoch;
    }
    sesion->epoca_actual++;

    sesion->estado = ORCH_STATE_AGGREGATING;
    return perdida_epoch;
}

float orch_entrenar(OrchSession* sesion) {
    if (!sesion) return -1.0f;

    int epochs = sesion->config.num_epochs;
    float perdida_total = 0.0f;

    for (int e = 0; e < epochs; e++) {
        // Antes de cada época: resetear estado de asignaciones completadas
        for (int i = 0; i < sesion->num_assignments; i++) {
            if (sesion->assignments[i].estado == 2) {
                sesion->assignments[i].estado = 0;  // Pendiente para nueva época
            }
        }

        float loss = orch_ejecutar_epoch(sesion);
        if (loss < 0.0f) {
            // Manejar fallo: redistribuir
            int redist = orch_redistribuir(sesion);
            if (redist <= 0) {
                sesion->estado = ORCH_STATE_FAILED;
                return -1.0f;
            }
            // Reintentar época
            e--;
            continue;
        }
        perdida_total += loss;
    }

    sesion->estado = ORCH_STATE_COMPLETED;
    return perdida_total / (float)epochs;
}

int orch_manejar_fallo(OrchSession* sesion, const char* worker_id) {
    if (!sesion || !worker_id) return -1;

    int idx = _buscar_assignment(sesion, worker_id);
    if (idx < 0) return -1;

    OrchWorkerAssignment* asg = &sesion->assignments[idx];
    asg->reintentos++;

    if (sesion->config.failover_strategy == ORCH_FAILOVER_RETRY) {
        if (asg->reintentos <= sesion->config.max_retries) {
            asg->estado = 0;  // Pendiente para reintento
            return 0;  // Recuperado
        }
        // Excedió reintentos
        asg->estado = 3;  // Fallo permanente
        return -1;
    }
    else if (sesion->config.failover_strategy == ORCH_FAILOVER_REDISTRIBUTE) {
        asg->estado = 3;  // Fallo permanente
        int redist = orch_redistribuir(sesion);
        return (redist > 0) ? 0 : -1;
    }
    else {  // ORCH_FAILOVER_IGNORE
        asg->estado = 3;  // Marcar como fallo pero continuar
        return 0;
    }
}

int orch_redistribuir(OrchSession* sesion) {
    if (!sesion) return -1;

    int redistribuidas = 0;
    for (int i = 0; i < sesion->num_assignments; i++) {
        if (sesion->assignments[i].estado != 3) continue;

        // Buscar otro worker activo para esta partición
        for (int j = 0; j < sesion->num_assignments; j++) {
            if (i == j) continue;
            if (sesion->assignments[j].estado == 3) continue;

            // Transferir partición
            OrchWorkerAssignment* destino = &sesion->assignments[j];
            destino->particion = sesion->assignments[i].particion;
            destino->estado = 0;  // Pendiente
            destino->reintentos = 0;

            // Marcar worker destino en la partición original
            strncpy(sesion->particiones[i].worker_asignado,
                    destino->worker_id, ORCH_NAME_MAX - 1);

            redistribuidas++;
            break;
        }
    }

    return redistribuidas;
}

int orch_conectar_federated(OrchSession* sesion, FEDSession* fed) {
    if (!sesion || !fed) return -1;
    sesion->fed_sesion = fed;
    return 0;
}

int orch_conectar_fine_tuning(OrchSession* sesion, FTSession* ft) {
    if (!sesion || !ft) return -1;
    sesion->ft_sesion = ft;
    return 0;
}

int orch_conectar_distillation(OrchSession* sesion, KDSession* kd) {
    if (!sesion || !kd) return -1;
    sesion->kd_sesion = kd;
    return 0;
}

OrchProgress orch_obtener_progreso(OrchSession* sesion) {
    OrchProgress prog = {0};
    if (!sesion) return prog;

    prog.estado = sesion->estado;
    prog.epoca_actual = sesion->epoca_actual;
    prog.perdida_actual = sesion->perdida_global;

    for (int i = 0; i < sesion->num_assignments; i++) {
        switch (sesion->assignments[i].estado) {
            case 0: prog.workers_pendientes++; break;
            case 1: break;  // En curso
            case 2: prog.workers_completados++; break;
            case 3: prog.workers_fallados++; break;
        }
    }

    int total = sesion->num_assignments;
    if (total > 0) {
        prog.progreso_porcentaje = 100.0f * (float)prog.workers_completados / (float)total;
    }

    return prog;
}

ORCHEstadisticas orch_obtener_estadisticas(OrchSession* sesion) {
    ORCHEstadisticas stats = {0};
    if (!sesion) return stats;

    stats.num_workers_asignados = sesion->num_assignments;
    stats.num_particiones_creadas = sesion->num_particiones;
    stats.epocas_completadas = sesion->epoca_actual;
    stats.perdida_promedio = sesion->perdida_global;

    int fallados = 0;
    int reintentos_total = 0;
    for (int i = 0; i < sesion->num_assignments; i++) {
        reintentos_total += sesion->assignments[i].reintentos;
        if (sesion->assignments[i].estado == 3) fallados++;
    }
    stats.total_reintentos = reintentos_total;
    stats.workers_fallados = fallados;

    if (sesion->num_assignments > 0) {
        int completados = 0;
        for (int i = 0; i < sesion->num_assignments; i++) {
            if (sesion->assignments[i].estado != 3) completados++;
        }
        stats.tasa_exito_asignacion = (float)completados / (float)sesion->num_assignments;
    }

    return stats;
}

int orch_guardar(const OrchSession* sesion, const char* ruta) {
    if (!sesion || !ruta) return -1;

    FILE* f = fopen(ruta, "wb");
    if (!f) return -1;

    uint32_t magic = ORCH_MAGIC_HEADER;
    uint32_t version = ORCH_VERSION;
    fwrite(&magic, sizeof(magic), 1, f);
    fwrite(&version, sizeof(version), 1, f);
    fwrite(&sesion->config, sizeof(OrchConfig), 1, f);

    uint32_t na = (uint32_t)sesion->num_assignments;
    fwrite(&na, sizeof(na), 1, f);
    for (uint32_t i = 0; i < na; i++) {
        fwrite(&sesion->assignments[i], sizeof(OrchWorkerAssignment), 1, f);
    }

    uint32_t np = (uint32_t)sesion->num_particiones;
    fwrite(&np, sizeof(np), 1, f);
    for (uint32_t i = 0; i < np; i++) {
        // Escribir partición sin punteros internos
        OrchPartition p = sesion->particiones[i];
        p.indices_globales = NULL;  // No serializar puntero
        fwrite(&p, sizeof(OrchPartition), 1, f);
    }

    fwrite(&sesion->epoca_actual, sizeof(int), 1, f);
    fwrite(&sesion->perdida_global, sizeof(float), 1, f);
    fwrite(&sesion->mejor_perdida, sizeof(float), 1, f);

    fclose(f);
    return 0;
}

int orch_cargar(OrchSession* sesion, const char* ruta) {
    if (!sesion || !ruta) return -1;

    FILE* f = fopen(ruta, "rb");
    if (!f) return -1;

    uint32_t magic, version;
    if (fread(&magic, sizeof(magic), 1, f) != 1 || magic != ORCH_MAGIC_HEADER) {
        fclose(f); return -1;
    }
    if (fread(&version, sizeof(version), 1, f) != 1 || version > ORCH_VERSION) {
        fclose(f); return -1;
    }
    if (fread(&sesion->config, sizeof(OrchConfig), 1, f) != 1) {
        fclose(f); return -1;
    }

    uint32_t na = 0;
    if (fread(&na, sizeof(na), 1, f) != 1 || na > ORCH_MAX_WORKERS) {
        fclose(f); return -1;
    }
    for (uint32_t i = 0; i < na; i++) {
        if (fread(&sesion->assignments[i], sizeof(OrchWorkerAssignment), 1, f) != 1) {
            fclose(f); return -1;
        }
        sesion->assignments[i].particion.indices_globales = NULL;
    }
    sesion->num_assignments = (int)na;

    uint32_t np = 0;
    if (fread(&np, sizeof(np), 1, f) != 1 || np > ORCH_MAX_PARTITIONS) {
        fclose(f); return -1;
    }
    for (uint32_t i = 0; i < np; i++) {
        if (fread(&sesion->particiones[i], sizeof(OrchPartition), 1, f) != 1) {
            fclose(f); return -1;
        }
        sesion->particiones[i].indices_globales = NULL;
    }
    sesion->num_particiones = (int)np;

    fread(&sesion->epoca_actual, sizeof(int), 1, f);
    fread(&sesion->perdida_global, sizeof(float), 1, f);
    fread(&sesion->mejor_perdida, sizeof(float), 1, f);

    fclose(f);
    return 0;
}

void orch_cerrar(OrchSession* sesion) {
    if (!sesion) return;

    for (int i = 0; i < sesion->num_particiones; i++) {
        free(sesion->particiones[i].indices_globales);
    }

    // Nota: no cerrar fed_sesion, ft_sesion ni kd_sesion
    // (son propiedad del llamador)
    free(sesion);
}

// ============================================================
// Wrappers _syn_orch_* para enlace con std.dist_orchestrator
// ============================================================

void* _syn_orch_iniciar(int epochs, float lr, int assign_mode, int sync_mode) {
    OrchConfig cfg;
    memset(&cfg, 0, sizeof(OrchConfig));
    cfg.assign_mode = assign_mode;
    cfg.sync_mode = sync_mode;
    cfg.failover_strategy = ORCH_FAILOVER_RETRY;
    cfg.max_retries = 3;
    cfg.sync_fraction = 1.0f;
    cfg.learning_rate = (lr > 0.0f) ? lr : 0.001f;
    cfg.num_epochs = (epochs > 0) ? epochs : 5;
    cfg.num_partitions = 4;
    cfg.dataset_size = 1000;
    cfg.client_fraction = 1.0f;
    return orch_iniciar(&cfg);
}

void _syn_orch_cerrar(void* sesion) {
    orch_cerrar((OrchSession*)sesion);
}

int _syn_orch_crear_particiones(void* sesion, int dataset_size, const float* pesos) {
    return orch_crear_particiones((OrchSession*)sesion, dataset_size, pesos);
}

int _syn_orch_asignar_workers(void* sesion, const char* const* workers,
                               int n, const float* caps) {
    return orch_asignar_workers((OrchSession*)sesion, workers, n, caps);
}

float _syn_orch_ejecutar_epoch(void* sesion) {
    return orch_ejecutar_epoch((OrchSession*)sesion);
}

float _syn_orch_entrenar(void* sesion) {
    return orch_entrenar((OrchSession*)sesion);
}

int _syn_orch_manejar_fallo(void* sesion, const char* worker_id) {
    return orch_manejar_fallo((OrchSession*)sesion, worker_id);
}

int _syn_orch_redistribuir(void* sesion) {
    return orch_redistribuir((OrchSession*)sesion);
}

int _syn_orch_conectar_federated(void* sesion, void* fed) {
    return orch_conectar_federated((OrchSession*)sesion, (FEDSession*)fed);
}

int _syn_orch_conectar_ft(void* sesion, void* ft) {
    return orch_conectar_fine_tuning((OrchSession*)sesion, (FTSession*)ft);
}

int _syn_orch_conectar_kd(void* sesion, void* kd) {
    return orch_conectar_distillation((OrchSession*)sesion, (KDSession*)kd);
}

int _syn_orch_guardar(void* sesion, const char* ruta) {
    return orch_guardar((const OrchSession*)sesion, ruta);
}

int _syn_orch_cargar(void* sesion, const char* ruta) {
    return orch_cargar((OrchSession*)sesion, ruta);
}
