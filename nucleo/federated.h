// federated.h — Runtime de Aprendizaje Federado (Federated Learning)
// ==================================================================
// Implementa el algoritmo FedAvg (Federated Averaging) para entrenamiento
// distribuido sobre la red de nodos Synapse (M8.x).
//
// Arquitectura:
//   - FedCoordinator: nodo coordinador que distribuye pesos y agrega gradientes
//   - FedWorker: nodo trabajador que entrena localmente y envía gradientes
//   - FedAvg: promediado ponderado de gradientes/pesos con firmas Ed25519
//   - Integración con fine_tuning.c (LoRA) y distillation.c (KD)
//
// Zero-telemetry: comunicación cifrada y firmada, sin exposición de datos.
// ==================================================================

#ifndef FEDERATED_H
#define FEDERATED_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// Constantes
// ============================================================

#define FED_MAX_WORKERS 64             // Máximo de nodos trabajadores
#define FED_MAX_WEIGHTS 1024*1024      // Máximo de pesos por ronda (~4MB de floats)
#define FED_NAME_MAX 64                // Longitud máxima de nombre de nodo
#define FED_HEX_KEY_LEN 128            // Longitud de clave hex (64 bytes * 2)
#define FED_HEX_SIG_LEN 128            // Longitud de firma hex (64 bytes * 2)
#define FED_MAGIC_HEADER 0x46454452    // "FEDR" — Federated session magic
#define FED_VERSION 1                  // Versión del formato
#define FED_TIMEOUT_MS 5000            // Timeout por defecto para workers (5s)
#define FED_MAX_ROUNDS 1000            // Máximo de rondas de entrenamiento
#define FED_MIN_WORKERS 1              // Mínimo de workers para FedAvg

// Estados del worker
#define FED_WORKER_IDLE 0
#define FED_WORKER_TRAINING 1
#define FED_WORKER_SENT 2
#define FED_WORKER_TIMEOUT 3
#define FED_WORKER_FAILED 4

// Modos de agregación
#define FED_AGGREGATE_AVG 0        // FedAvg estándar
#define FED_AGGREGATE_WEIGHTED 1   // FedAvg ponderado por tamaño de dataset

// ============================================================
// Tipos de datos
// ============================================================

// Configuración de una ronda federada
typedef struct {
    int num_rounds;               // Número de rondas de federated learning
    int aggregate_mode;           // FED_AGGREGATE_AVG o FED_AGGREGATE_WEIGHTED
    float learning_rate;          // Learning rate global
    float client_fraction;        // Fracción de workers a usar por ronda (0.0-1.0)
    int timeout_ms;               // Timeout por worker
    int min_workers;              // Mínimo de workers para continuar
    int use_ed25519;              // 1 = firmar gradientes con Ed25519
    int use_compression;          // 1 = comprimir pesos antes de transferencia
} FedConfig;

// Worker en el clúster federado
typedef struct {
    char id[FED_NAME_MAX];        // ID único del worker
    char ip[64];                  // Dirección IP
    int puerto;                   // Puerto UDP
    char pubkey_hex[FED_HEX_KEY_LEN]; // Clave pública Ed25519 (hex)
    int estado;                   // FED_WORKER_*
    float peso;                   // Peso del worker (ej: tamaño de dataset)
    int64_t ultimo_latido;        // Timestamp del último heartbeat
    float* gradientes_recibidos;  // Buffer de gradientes recibidos
    int num_gradientes;           // Número de gradientes en el buffer
} FedWorker;

// Progreso de una ronda
typedef struct {
    int ronda_actual;             // Ronda en curso
    int workers_activos;          // Workers que respondieron
    int workers_timeout;          // Workers que expiraron
    float perdida_promedio;       // Pérdida promedio de la ronda
    float precision_promedio;     // Precisión promedio
    float tiempo_ronda_ms;        // Tiempo de la ronda en ms
} FedRoundProgress;

// Estadísticas de la sesión federada
typedef struct {
    int num_workers_registrados;
    int num_workers_activos;
    int rondas_completadas;
    float perdida_global_actual;
    float perdida_global_mejor;
    float tasa_participacion;     // Participación promedio por ronda
    int total_gradientes_recibidos;
    int total_gradientes_firmados;
} FEDEstadisticas;

// Sesión de aprendizaje federado
typedef struct {
    FedConfig config;
    FedWorker workers[FED_MAX_WORKERS];
    int num_workers;
    float* pesos_globales;        // Pesos globales del modelo
    int num_pesos;                // Número de parámetros
    float* buffer_agregacion;     // Buffer para agregación de gradientes
    int ronda_actual;
    int estado;                   // 0=init, 1=entrenando, 2=completado
    float perdida_global;
    float mejor_perdida;
    char clave_privada_hex[FED_HEX_KEY_LEN];  // Clave privada Ed25519 del coordinador
    char clave_publica_hex[FED_HEX_KEY_LEN];  // Clave pública Ed25519
    void* ft_contexto;            // Contexto fine-tuning (opcional)
    void* kd_contexto;            // Contexto destilación (opcional)
} FEDSession;

// ============================================================
// API de Aprendizaje Federado
// ============================================================

// Inicializa una sesión federada
// pesos_iniciales: puntero a los pesos iniciales del modelo (NULL=ceros)
// num_pesos: número de parámetros
// config: configuración (NULL=defecto)
// Retorna: puntero a FEDSession, NULL en error
FEDSession* fed_iniciar(const float* pesos_iniciales, int num_pesos,
                         const FedConfig* config);

// Registra un worker en el clúster federado
// Retorna: 0 en éxito, -1 en error
int fed_registrar_worker(FEDSession* sesion, const char* id, const char* ip,
                          int puerto, const char* pubkey_hex, float peso);

// Elimina un worker del clúster
// Retorna: 0 en éxito, -1 en error
int fed_eliminar_worker(FEDSession* sesion, const char* id);

// Distribuye los pesos globales a todos los workers activos
// Retorna: número de workers que recibieron los pesos, -1 en error
int fed_distribuir_pesos(FEDSession* sesion);

// Recibe gradientes de un worker (simulado: genera gradientes sintéticos)
// Retorna: 0 en éxito, -1 en error
int fed_recibir_gradientes(FEDSession* sesion, const char* worker_id,
                            const float* gradientes, int num_grad,
                            const char* firma_hex);

// Ejecuta una ronda de FedAvg: distribuir → entrenar → agregar
// Retorna: pérdida promedio de la ronda, -1.0f en error
float fed_ronda_fedavg(FEDSession* sesion);

// Ejecuta FedAvg completo (todas las rondas)
// Retorna: pérdida final, -1.0f en error
float fed_entrenar(FEDSession* sesion);

// Agrega pesos de workers usando FedAvg ponderado
// weights: pesos de cada worker [num_workers]
// num_workers: número de workers que respondieron
// Retorna: 0 en éxito, -1 en error
int fed_agregar_gradientes(FEDSession* sesion, const float* const* grad_workers,
                            const float* weights, int num_workers);

// Verifica firma Ed25519 de un mensaje de gradiente
// Retorna: 0 si firma válida, -1 si inválida
int fed_verificar_firma_gradiente(const float* gradientes, int num_grad,
                                   const char* firma_hex, const char* pubkey_hex,
                                   const char* worker_id);

// Maneja timeout de workers: marca como timeout los que no respondieron
// Retorna: número de workers marcados como timeout
int fed_manejar_timeouts(FEDSession* sesion, int64_t tiempo_actual_ms);

// Obtiene el progreso de la ronda actual
FedRoundProgress fed_obtener_progreso(FEDSession* sesion);

// Obtiene estadísticas de la sesión
FEDEstadisticas fed_obtener_estadisticas(FEDSession* sesion);

// Guarda el estado federado a un archivo binario
// Formato: [FED_MAGIC][version][config][num_workers][workers][pesos_globales][estado]
// Retorna: 0 en éxito, -1 en error
int fed_guardar(const FEDSession* sesion, const char* ruta);

// Carga el estado federado desde un archivo
// Retorna: 0 en éxito, -1 en error
int fed_cargar(FEDSession* sesion, const char* ruta);

// Cierra la sesión y libera memoria
void fed_cerrar(FEDSession* sesion);

#ifdef __cplusplus
}
#endif

#endif // FEDERATED_H
