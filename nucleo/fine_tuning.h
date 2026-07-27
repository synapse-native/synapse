// fine_tuning.h — Fine-tuning local para modelos GGUF vía LoRA/AdaLoRA
// =========================================================================
// Implementa ajuste ligero (fine-tuning) de modelos de lenguaje locales
// usando adaptadores de bajo rango (LoRA). Todo el proceso es local,
// soberano y sin telemetría.
//
// Arquitectura:
//   - LoRAAdapter: parámetros A y B para una capa específica
//   - LoRASession: sesión completa de fine-tuning con múltiples adaptadores
//   - ft_entrenar_paso: un paso de entrenamiento (forward + backward LoRA)
//   - ft_guardar_pesos / ft_cargar_pesos: persistencia de adaptadores
// =========================================================================

#ifndef FINE_TUNING_H
#define FINE_TUNING_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// Constantes
// ============================================================

#define FT_MAX_LAYERS 256         // Máximo de capas adaptables
#define FT_RANK_DEFAULT 8         // Rango LoRA por defecto
#define FT_ALPHA_DEFAULT 16.0f    // Escala LoRA por defecto
#define FT_LR_DEFAULT 0.0001f     // Learning rate por defecto
#define FT_MAX_DATASET 1024       // Máximo de ejemplos en dataset local
#define FT_MAX_SEQ_LEN 512        // Longitud máxima de secuencia de entrenamiento
#define FT_ADAPTER_MAGIC 0x4C4F5241  // "LORA" magic header

// Tipos de capa para LoRA
#define FT_LAYER_ATTN_Q 0   // Attention query projection
#define FT_LAYER_ATTN_K 1   // Attention key projection
#define FT_LAYER_ATTN_V 2   // Attention value projection
#define FT_LAYER_ATTN_O 3   // Attention output projection
#define FT_LAYER_FFN_GATE 4 // FFN gate projection
#define FT_LAYER_FFN_UP 5   // FFN up projection
#define FT_LAYER_FFN_DOWN 6 // FFN down projection

// ============================================================
// Estructuras de datos
// ============================================================

// Adaptador LoRA para una capa: Delta_W = alpha * B @ A / rank
typedef struct {
    int capa_idx;             // Índice de capa del transformer
    int tipo_capa;            // FT_LAYER_ATTN_Q, etc.
    int rank;                 // Rango de la descomposición
    float alpha;              // Factor de escala
    float* A;                 // Matriz A: [rank x dim_in]
    float* B;                 // Matriz B: [dim_out x rank]
    int dim_in;               // Dimensión de entrada
    int dim_out;              // Dimensión de salida
    int activo;               // 1 = activo, 0 = inactivo
} LoRAAdapter;

// Configuración de fine-tuning
typedef struct {
    float learning_rate;
    int rank;
    float alpha;
    int num_epochs;
    int batch_size;
    float weight_decay;
    float grad_clip_norm;     // 0.0 = sin clipping
} FTConfig;

// Par de entrada-salida para entrenamiento
typedef struct {
    int* tokens_entrada;      // Secuencia de tokens de entrada
    int len_entrada;          // Longitud de la secuencia de entrada
    int* tokens_salida;       // Secuencia de tokens objetivo
    int len_salida;           // Longitud de la secuencia objetivo
    float peso;               // Peso del ejemplo (1.0 por defecto)
} FTEjemplo;

// Dataset local para fine-tuning
typedef struct {
    FTEjemplo ejemplos[FT_MAX_DATASET];
    int num_ejemplos;
} FTDataset;

// Sesión completa de fine-tuning
typedef struct {
    LoRAAdapter adaptadores[FT_MAX_LAYERS];
    int num_adaptadores;
    FTConfig config;
    FTDataset dataset;
    void* modelo_ctx;         // Contexto del modelo base (de std.modelo)
    int estado;               // 0 = inicializado, 1 = entrenando, 2 = entrenado
    float perdida_actual;     // Pérdida del último paso
    int paso_actual;          // Contador de pasos de entrenamiento
    float* grad_buffer;       // Buffer temporal para gradientes
    int grad_buffer_size;
} FTSession;

// ============================================================
// API de Fine-Tuning
// ============================================================

// Inicializa una sesión de fine-tuning con configuración por defecto
// Retorna: puntero a FTSession, NULL en error
FTSession* ft_iniciar(void* modelo_ctx, const FTConfig* config);

// Añade un adaptador LoRA para una capa específica
// Retorna: 0 en éxito, -1 en error
int ft_agregar_adaptador(FTSession* sesion, int capa_idx, int tipo_capa,
                           int rank, float alpha, int dim_in, int dim_out);

// Añade un ejemplo al dataset de entrenamiento
// Retorna: 0 en éxito, -1 en error
int ft_agregar_ejemplo(FTSession* sesion, const int* tokens_in, int len_in,
                        const int* tokens_out, int len_out, float peso);

// Ejecuta un paso de entrenamiento (forward + backward LoRA + actualización)
// Retorna: valor de pérdida después del paso, -1.0f en error
float ft_paso_entrenamiento(FTSession* sesion);

// Ejecuta entrenamiento completo (todos los ejemplos, todas las épocas)
// Retorna: pérdida promedio final, -1.0f en error
float ft_entrenar(FTSession* sesion);

// Evalúa la pérdida en un ejemplo sin actualizar pesos
// Retorna: valor de pérdida, -1.0f en error
float ft_evaluar_perdida(FTSession* sesion, const FTEjemplo* ejemplo);

// Guarda los pesos de los adaptadores LoRA a un archivo binario
// Formato: [FT_ADAPTER_MAGIC][num_adaptadores][cada adaptador: capa, tipo, rank, alpha, dim_in, dim_out, A[], B[]]
// Retorna: 0 en éxito, -1 en error
int ft_guardar_pesos(const FTSession* sesion, const char* ruta);

// Carga pesos de adaptadores desde un archivo binario y los agrega a la sesión
// Retorna: 0 en éxito, -1 en error
int ft_cargar_pesos(FTSession* sesion, const char* ruta);

// Aplica los adaptadores LoRA a la inferencia del modelo base
// Nota: modifica temporalmente las proyecciones del modelo para incluir Delta_W
// Retorna: 0 en éxito, -1 en error
int ft_aplicar_adaptadores(FTSession* sesion);

// Remueve los adaptadores LoRA (restaura el modelo base original)
void ft_remover_adaptadores(FTSession* sesion);

// Cierra la sesión y libera toda la memoria asociada
void ft_cerrar(FTSession* sesion);

// ============================================================
// Funciones de integración RAG
// ============================================================

// Estructura para resultados de búsqueda RAG potenciada por fine-tuning
typedef struct {
    char* texto_chunk;
    float puntuacion_base;     // Similitud coseno original
    float puntuacion_ajustada; // Puntuación después de ajuste por fine-tuning
    int linea_inicio;
    int linea_fin;
    char tipo_nodo[64];
} FTResultadoRAG;

// Obtiene la pérdida actual de la sesión
float ft_perdida_actual(FTSession* sesion);

// Obtiene el número de pasos de entrenamiento realizados
int ft_paso_actual(FTSession* sesion);

// Estadísticas de la sesión
typedef struct {
    int num_adaptadores;
    int num_ejemplos;
    float perdida_promedio;
    int pasos_ejecutados;
    float learning_rate;
    int rank_loRA;
} FTEstadisticas;

FTEstadisticas ft_obtener_estadisticas(FTSession* sesion);

#ifdef __cplusplus
}
#endif

#endif // FINE_TUNING_H
