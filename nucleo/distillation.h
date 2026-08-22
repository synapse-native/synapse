// distillation.h — Destilación de conocimiento (Knowledge Distillation) para modelos GGUF
// ================================================================================
// Implementa compresión de modelos grandes (teacher) a modelos pequeños (student)
// mediante Knowledge Distillation: minimizar KL divergence entre distribuciones
// de logits del teacher y del student, combinado con pérdida de hard labels.
//
// Integración:
//   - fine_tuning.h: reusa cross_entropy_loss, LoRA adapters para student
//   - quantization.h: conecta con qt_cuantizar_tensor para student cuantizado
//
// Zero-telemetry: todo el proceso es local y soberano.
// ================================================================================

#ifndef DISTILLATION_H
#define DISTILLATION_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// Constantes
// ============================================================

#define KD_MAX_STUDENT_LAYERS 64        // Máximo de capas del student
#define KD_MAX_DATASET 1024             // Máximo de ejemplos de destilación
#define KD_MAX_SEQ_LEN 512              // Longitud máxima de secuencia
#define KD_TEMPERATURE_DEFAULT 4.0f     // Temperatura por defecto para soft targets
#define KD_ALPHA_DEFAULT 0.5f           // Peso de pérdida soft vs hard (0.5 = 50% soft)
#define KD_MAGIC_HEADER 0x4B444953      // "KDIS" — Distillation session magic
#define KD_VERSION 2                    // R80: v2 añade num_logits por par en persistencia

// ============================================================
// Tipos de datos
// ============================================================

// Configuración de destilación
typedef struct {
    float temperature;           // Temperatura T: softmax(logits / T)
    float alpha;                 // Peso soft loss: L = alpha * L_soft + (1-alpha) * L_hard
    int num_epochs;              // Número de épocas de destilación
    int batch_size;              // Tamaño del batch
    float learning_rate;         // Learning rate para el student
    float weight_decay;          // Weight decay para regularización
    char ruta_teacher[256];      // Ruta al modelo teacher (.gguf)
    char ruta_student[256];      // Ruta al modelo student (.gguf)
    int vocab_size;              // Tamaño del vocabulario (para logits)
    int student_hidden_dim;      // Dimensión oculta del student (para mapeo de capas)
    int teacher_hidden_dim;      // Dimensión oculta del teacher (para mapeo de capas)
} KDConfig;

// Par de logits (teacher + student) para un token
typedef struct {
    float* logits_teacher;       // Logits del teacher [num_logits]
    float* logits_student;       // Logits del student [num_logits]
    int target_id;               // Token objetivo (ground truth)
    float peso;                  // Peso del ejemplo
    int num_logits;              // R80: longitud real de este par (0 = legacy: usar config.vocab_size)
} KDLogitPair;

// Dataset de destilación (pares de logits precomputados)
typedef struct {
    KDLogitPair pares[KD_MAX_DATASET];
    int num_pares;
    int vocab_size;
} KDDataset;

// Estadísticas de la sesión de destilación
typedef struct {
    float perdida_soft;          // Pérdida soft (KL divergence)
    float perdida_hard;          // Pérdida hard (cross-entropy)
    float perdida_total;         // Pérdida combinada
    float temperatura_usada;     // Temperatura de la sesión
    float alpha_usado;           // Alpha usado
    int pasos_ejecutados;
    int num_ejemplos_procesados;
    float reduccion_estimada;    // Reducción de tamaño teacher→student
} KDEstadisticas;

// Sesión de destilación
typedef struct {
    KDConfig config;
    KDDataset dataset;
    void* teacher_ctx;           // Contexto del teacher (de std.modelo)
    void* student_ctx;           // Contexto del student (de std.modelo)
    void* ft_sesion_student;     // Sesión LoRA para fine-tuning del student
    float perdida_soft_actual;
    float perdida_hard_actual;
    float perdida_total_actual;
    int paso_actual;
    int estado;                  // 0 = init, 1 = destilando, 2 = completado
} KDSession;

// ============================================================
// API de Destilación
// ============================================================

// Inicializa una sesión de destilación
// Retorna: puntero a KDSession, NULL en error
KDSession* kd_iniciar(const KDConfig* config);

// Añade un par de logits (teacher + student) para un token
// Los arrays deben tener config.vocab_size elementos (contrato legacy)
// Retorna: índice del par agregado, -1 en error
int kd_agregar_par(KDSession* sesion, const float* logits_t,
                    const float* logits_s, int target_id, float peso);

// R80 (F12-2, opción b del Arquitecto): variante con longitud EXPLÍCITA.
// Copia exactamente n elementos de cada array — no depende de config.vocab_size.
// Retorna: índice del par agregado, -1 en error
int kd_agregar_par_n(KDSession* sesion, const float* logits_t,
                      const float* logits_s, int n, int target_id, float peso);

// Computa KL divergence entre dos distribuciones de probabilidad
// KL(P||Q) = sum(P_i * log(P_i / Q_i))
// softmax_p: logits de teacher (aplicará softmax interno)
// softmax_q: logits de student (aplicará softmax interno)
// n: tamaño del vocabulario
// temperature: temperatura para softmax
// Retorna: KL divergence, -1.0f en error
float kd_divergencia_kl(const float* logits_p, const float* logits_q,
                         int n, float temperature);

// Computa la pérdida combinada soft + hard para un par de logits
// L = alpha * T^2 * KL(softmax(p/T) || softmax(q/T)) + (1-alpha) * CE(q, target)
// Retorna: pérdida combinada, -1.0f en error
float kd_perdida_combinada(const float* logits_teacher,
                            const float* logits_student,
                            int target_id, int vocab_size,
                            float temperature, float alpha);

// Ejecuta un paso de destilación sobre el dataset completo
// Retorna: pérdida total promedio, -1.0f en error
float kd_paso_destilacion(KDSession* sesion);

// Ejecuta destilación completa sobre el dataset
// Retorna: pérdida total promedio final, -1.0f en error
float kd_destilar(KDSession* sesion);

// Aplica reducción de capas: mapea pesos del teacher al student
// usando interpolación lineal para capas ocultas de diferente dimensión
// Retorna: 0 en éxito, -1 en error
int kd_reducir_capas(KDSession* sesion, const float* pesos_teacher,
                      int num_capas_teacher, int dim_teacher,
                      float* pesos_student, int num_capas_student, int dim_student);

// Evalúa la calidad de la destilación (perdida en un ejemplo sin entrenar)
// Retorna: pérdida combinada, -1.0f en error
float kd_evaluar(KDSession* sesion, const float* logits_t,
                  const float* logits_s, int target_id);

// Guarda el estado de destilación a un archivo binario
// Formato: [KD_MAGIC][KD_VERSION][KDConfig][KDEstadisticas][num_pares][logits...]
// Retorna: 0 en éxito, -1 en error
int kd_guardar(const KDSession* sesion, const char* ruta);

// Carga el estado de destilación desde un archivo binario
// Retorna: 0 en éxito, -1 en error
int kd_cargar(KDSession* sesion, const char* ruta);

// Cierra la sesión y libera toda la memoria
void kd_cerrar(KDSession* sesion);

// ============================================================
// Integración con cuantización (quantization.h)
// ============================================================

// Estima la reducción de tamaño después de destilación + cuantización
// Retorna: factor de reducción (ej: 4.0 = 4x más pequeño)
float kd_estimar_reduccion(int params_teacher_millones, int params_student_millones,
                            int formato_cuantizacion);

// ============================================================
// Estadísticas
// ============================================================

// Obtiene estadísticas de la sesión de destilación
KDEstadisticas kd_obtener_estadisticas(KDSession* sesion);

// Obtiene la pérdida total actual
float kd_perdida_actual(KDSession* sesion);

// Obtiene el paso actual
int kd_paso_actual(KDSession* sesion);

#ifdef __cplusplus
}
#endif

#endif // DISTILLATION_H
