// dist_orchestrator.h — Orquestador de Entrenamiento Distribuido
// =================================================================
// Gestiona la asignación dinámica de workers del clúster (M8.x),
// la partición inteligente de datasets y la sincronización de modelos
// distribuidos. Integración nativa con fine_tuning.c (LoRA) y
// distillation.c (Knowledge Distillation).
//
// Arquitectura:
//   - OrchSession: sesión completa del orquestador
//   - OrchPartition: partición de dataset asignada a un worker
//   - OrchWorkerAssignment: asignación dinámica worker→partición
//   - Integración: fed_ronda_fedavg → ft_entrenar / kd_destilar
//
// Zero-telemetry: comunicación cifrada, soberanía de datos locales.
// =================================================================

#ifndef DIST_ORCHESTRATOR_H
#define DIST_ORCHESTRATOR_H

#include <stddef.h>
#include <stdint.h>
#include "fine_tuning.h"
#include "distillation.h"
#include "federated.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// Constantes
// ============================================================

#define ORCH_MAX_WORKERS 64             // Máximo workers asignables
#define ORCH_MAX_PARTITIONS 64          // Máximo particiones de dataset
#define ORCH_MAX_EPOCHS 1000           // Máximo épocas de entrenamiento
#define ORCH_NAME_MAX 64               // Longitud máxima de nombre
#define ORCH_MAGIC_HEADER 0x4F524348   // "ORCH" — Orchestrator magic
#define ORCH_VERSION 1                 // Versión del formato

// Modos de asignación de workers
#define ORCH_ASSIGN_ROUND_ROBIN 0      // Round-robin sobre workers
#define ORCH_ASSIGN_CAPACITY 1         // Por capacidad (peso del worker)
#define ORCH_ASSIGN_RANDOM 2           // Asignación aleatoria

// Modos de sincronización
#define ORCH_SYNC_SYNCHRONOUS 0        // Sincrónico (esperar todos)
#define ORCH_SYNC_ASYNCHRONOUS 1       // Asincrónico (no esperar)
#define ORCH_SYNC_SEMI_SYNC 2          // Semi-sincrónico (fracción)

// Estados del orquestador
#define ORCH_STATE_IDLE 0
#define ORCH_STATE_PARTITIONING 1
#define ORCH_STATE_ASSIGNING 2
#define ORCH_STATE_TRAINING 3
#define ORCH_STATE_AGGREGATING 4
#define ORCH_STATE_COMPLETED 5
#define ORCH_STATE_FAILED 6

// Estrategias de recuperación de fallos
#define ORCH_FAILOVER_RETRY 0          // Reintentar en mismo worker
#define ORCH_FAILOVER_REDISTRIBUTE 1   // Redistribuir a otros workers
#define ORCH_FAILOVER_IGNORE 2         // Ignorar datos perdidos

// ============================================================
// Tipos de datos
// ============================================================

// Partición de dataset
typedef struct {
    int inicio_idx;               // Índice de inicio en el dataset global
    int num_ejemplos;             // Número de ejemplos en la partición
    int* indices_globales;        // Mapeo a índices globales del dataset
    float peso;                   // Peso relativo de la partición
    char worker_asignado[ORCH_NAME_MAX];  // Worker asignado (o vacío)
} OrchPartition;

// Asignación de worker
typedef struct {
    char worker_id[ORCH_NAME_MAX];
    OrchPartition particion;
    int estado;                   // 0=pendiente, 1=en_curso, 2=completado, 3=fallo
    float perdida_local;
    int num_pasos_ejecutados;
    int64_t tiempo_inicio_ms;
    int64_t tiempo_fin_ms;
    int reintentos;               // Número de reintentos
} OrchWorkerAssignment;

// Configuración del orquestador
typedef struct {
    int assign_mode;              // ORCH_ASSIGN_*
    int sync_mode;                // ORCH_SYNC_*
    int failover_strategy;        // ORCH_FAILOVER_*
    int max_retries;              // Máximo reintentos por worker
    float sync_fraction;          // Para semi-síncrono (0.0-1.0)
    float learning_rate;          // Learning rate global
    int num_epochs;               // Épocas de entrenamiento
    int num_partitions;           // Número de particiones a crear
    int dataset_size;             // Tamaño total del dataset
    float client_fraction;        // Fracción de workers a usar
} OrchConfig;

// Estadísticas del orquestador
typedef struct {
    int num_workers_asignados;
    int num_particiones_creadas;
    int epocas_completadas;
    float perdida_promedio;
    float tiempo_promedio_por_epoch_ms;
    int total_reintentos;
    int workers_fallados;
    float tasa_exito_asignacion;  // 0.0-1.0
} ORCHEstadisticas;

// Progreso del orquestador
typedef struct {
    int estado;                   // ORCH_STATE_*
    int epoca_actual;
    int workers_completados;
    int workers_pendientes;
    int workers_fallados;
    float perdida_actual;
    float progreso_porcentaje;    // 0.0-100.0
} OrchProgress;

// Sesión del orquestador distribuido
typedef struct {
    OrchConfig config;
    OrchWorkerAssignment assignments[ORCH_MAX_WORKERS];
    int num_assignments;
    OrchPartition particiones[ORCH_MAX_PARTITIONS];
    int num_particiones;
    int epoca_actual;
    int estado;                   // ORCH_STATE_*
    float perdida_global;
    float mejor_perdida;
    FEDSession* fed_sesion;      // Sesión federada (M14.1)
    FTSession* ft_sesion;        // Sesión fine-tuning LoRA
    KDSession* kd_sesion;        // Sesión destilación
    void* worker_contextos[ORCH_MAX_WORKERS]; // Contextos de workers (opcional)
} OrchSession;

// ============================================================
// API del Orquestador Distribuido
// ============================================================

// Inicializa el orquestador con configuración
// Retorna: puntero a OrchSession, NULL en error
OrchSession* orch_iniciar(const OrchConfig* config);

// Particiona el dataset global en bloques para distribución
// Retorna: número de particiones creadas, -1 en error
int orch_crear_particiones(OrchSession* sesion, int dataset_size,
                            const float* pesos_ejemplos);

// Asigna workers a particiones según el modo configurado
// Retorna: número de asignaciones creadas, -1 en error
int orch_asignar_workers(OrchSession* sesion, const char* const* worker_ids,
                          int num_workers, const float* capacidades);

// Obtiene la partición asignada a un worker específico
// Retorna: puntero a OrchPartition, NULL si no encontrado
OrchPartition* orch_obtener_particion(OrchSession* sesion, const char* worker_id);

// Ejecuta una época de entrenamiento distribuido
// coordina: FED → FT/KD → agregación
// Retorna: pérdida promedio de la época, -1.0f en error
float orch_ejecutar_epoch(OrchSession* sesion);

// Ejecuta entrenamiento distribuido completo (todas las épocas)
// Retorna: pérdida final, -1.0f en error
float orch_entrenar(OrchSession* sesion);

// Maneja fallo de un worker: reintenta o redistribuye según estrategia
// Retorna: 0 si recuperado, -1 si no recuperable
int orch_manejar_fallo(OrchSession* sesion, const char* worker_id);

// Redistribuye particiones de workers fallados a workers activos
// Retorna: número de particiones redistribuidas
int orch_redistribuir(OrchSession* sesion);

// Conecta el orquestador con una sesión federada (M14.1)
// Retorna: 0 en éxito, -1 en error
int orch_conectar_federated(OrchSession* sesion, FEDSession* fed);

// Conecta el orquestador con una sesión de fine-tuning LoRA
// Retorna: 0 en éxito, -1 en error
int orch_conectar_fine_tuning(OrchSession* sesion, FTSession* ft);

// Conecta el orquestador con una sesión de destilación
// Retorna: 0 en éxito, -1 en error
int orch_conectar_distillation(OrchSession* sesion, KDSession* kd);

// Obtiene progreso actual del orquestador
OrchProgress orch_obtener_progreso(OrchSession* sesion);

// Obtiene estadísticas del orquestador
ORCHEstadisticas orch_obtener_estadisticas(OrchSession* sesion);

// Guarda el estado del orquestador a archivo binario
// Formato: [ORCH_MAGIC][version][config][assignments][particiones][estado]
// Retorna: 0 en éxito, -1 en error
int orch_guardar(const OrchSession* sesion, const char* ruta);

// Carga el estado del orquestador desde archivo
// Retorna: 0 en éxito, -1 en error
int orch_cargar(OrchSession* sesion, const char* ruta);

// Cierra el orquestador y libera memoria
void orch_cerrar(OrchSession* sesion);

#ifdef __cplusplus
}
#endif

#endif // DIST_ORCHESTRATOR_H
