// quantization.h — Cuantización de modelos GGUF (FP16/FP32 → INT8/INT4)
// =========================================================================
// Implementa la transformación de pesos de modelos de lenguaje de alta
// precisión (FP32/FP16) a formatos de bajo consumo (INT8/INT4) para
// ejecución optimizada en hardware con recursos limitados.
//
// Formatos soportados:
//   Q_FORMAT_FP32   — Sin cuantización (32-bit float)
//   Q_FORMAT_FP16   — Media precisión (16-bit float)
//   Q_FORMAT_INT8   — Cuantización simétrica 8-bit
//   Q_FORMAT_INT4   — Cuantización simétrica 4-bit (packed)
//
// Zero-telemetry: todo el proceso es local y soberano.
// =========================================================================

#ifndef QUANTIZATION_H
#define QUANTIZATION_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// Constantes
// ============================================================

#define QT_MAGIC_HEADER 0x51544154   // "QTAT" — Quantized Tensor Archive
#define QT_MAX_TENSORS 1024           // Máximo tensores cuantizables
#define QT_BLOCK_SIZE_INT8 64         // Tamaño de bloque para INT8
#define QT_BLOCK_SIZE_INT4 32         // Tamaño de bloque para INT4
#define QT_CACHE_LINE 64              // Alineación a caché (64 bytes)
#define QT_VERSION 1                  // Versión del formato

// Formatos de cuantización
#define QT_FORMAT_FP32 0   // Float32 (sin cuantizar)
#define QT_FORMAT_FP16 1   // Float16
#define QT_FORMAT_INT8 2   // Int8 simétrico
#define QT_FORMAT_INT4 3   // Int4 simétrico (empaquetado)

// ============================================================
// Tipos de datos
// ============================================================

// Cabecera de tensor cuantizado (almacenamiento en bloque)
typedef struct {
    int32_t filas;
    int32_t columnas;
    int formato;            // QT_FORMAT_*
    float escala;           // Factor de escala (para INT8/INT4)
    int32_t offset;         // Offset de datos en el archivo/sesión
    int32_t tamano_bytes;   // Tamaño en bytes de los datos cuantizados
    char nombre[64];        // Nombre del tensor (ej: "token_embd.weight")
} QTensorHeader;

// Tensor cuantizado en memoria
typedef struct {
    QTensorHeader header;
    void* datos;            // Datos cuantizados (escala INT8 o packed INT4)
    float* datos_fp32;      // Cache descomprimida (FP32, opcional)
    int datos_fp32_actualizado;  // 1 si datos_fp32 refleja los cuantizados
} QTensor;

// Configuración de cuantización
typedef struct {
    int formato_destino;     // QT_FORMAT_INT8 o QT_FORMAT_INT4
    int calibrar;            // 1 = ejecutar calibración antes de cuantizar
    int block_size;          // Tamaño de bloque para cuantización por bloques
    float error_max_permil;  // Error máximo permitido (per mil, 0.01 = 1%)
    int num_calib_ejemplos;  // Número de ejemplos para calibración
} QConfig;

// Sesión de cuantización
typedef struct {
    QTensor tensores[QT_MAX_TENSORS];
    int num_tensores;
    QConfig config;
    float reduccion_peso_estimada;  // Reducción estimada (1.0 = 0%, 0.5 = 50%)
    int64_t peso_original_bytes;
    int64_t peso_cuantizado_bytes;
    float error_promedio;           // Error promedio de reconstrucción
    float error_maximo;             // Error máximo de reconstrucción
} QSession;

// ============================================================
// API de Cuantización
// ============================================================

// Inicializa una sesión de cuantización con configuración
QSession* qt_iniciar(const QConfig* config);

// Agrega un tensor FP32 a la sesión para cuantizar
// datos: puntero a datos float32, filas*columnas elementos
// Retorna: índice del tensor, -1 en error
int qt_agregar_tensor(QSession* sesion, const float* datos,
                       int filas, int columnas, const char* nombre);

// Cuantiza un tensor específico de FP32 al formato destino
// Retorna: 0 en éxito, -1 en error
int qt_cuantizar_tensor(QSession* sesion, int idx_tensor);

// Cuantiza todos los tensores en la sesión
// Retorna: número de tensores cuantizados, -1 en error
int qt_cuantizar_todos(QSession* sesion);

// Descuantiza un tensor (restaura a FP32)
// Retorna: puntero a float (datos_fp32 interno), NULL en error
float* qt_descuantizar_tensor(QSession* sesion, int idx_tensor);

// Convierte FP16 ↔ FP32 (útil para pesos en formato GGUF nativo)
void qt_fp16_a_fp32(const uint16_t* src, float* dst, int n);
void qt_fp32_a_fp16(const float* src, uint16_t* dst, int n);

// Calcula error de reconstrucción para un tensor cuantizado
// Retorna: error promedio (MSE), -1.0f en error
float qt_calcular_error(QSession* sesion, int idx_tensor);

// Guarda todos los tensores cuantizados a un archivo
// Formato: [QT_MAGIC][QT_VERSION][QConfig][num_tensores][tensor headers...][tensor data...]
// Retorna: 0 en éxito, -1 en error
int qt_guardar(QSession* sesion, const char* ruta);

// Carga tensores cuantizados desde un archivo
// Retorna: 0 en éxito, -1 en error
int qt_cargar(QSession* sesion, const char* ruta);

// Libera la memoria de la sesión
void qt_cerrar(QSession* sesion);

// ============================================================
// Inferencia cuantizada
// ============================================================

// Ejecuta producto punto entre un vector cuantizado (INT8) y uno FP32
// a: vector cuantizado INT8 [n], escala_a: escala de a
// b: vector FP32 [n]
// Retorna: producto punto como float
float qt_producto_punto_int8(const int8_t* a, float escala_a,
                              const float* b, int n);

// Ejecuta producto punto entre un vector cuantizado (INT4 packed) y uno FP32
// a: vector INT4 empaquetado [n/2 bytes], escala_a: escala de a
// b: vector FP32 [n]
// Retorna: producto punto como float
float qt_producto_punto_int4(const uint8_t* a, float escala_a,
                              const float* b, int n);

// ============================================================
// Integración con RAG (selección dinámica de formato)
// ============================================================

// Selecciona el formato de cuantización óptimo según memoria disponible
// ram_mb: MB de RAM disponibles
// Retorna: QT_FORMAT_*
int qt_seleccionar_formato(int ram_mb);

// Calcula el tamaño estimado en memoria de un modelo cuantizado
// Retorna: MB estimados
float qt_estimar_tamano_modelo(int num_params_millones, int formato);

// Retorna la reducción porcentual del formato respecto a FP32
// Ej: INT8 → 75% (1/4 del tamaño), INT4 → 87.5% (1/8)
float qt_reduccion_formato(int formato);

// ============================================================
// Estadísticas
// ============================================================

typedef struct {
    int num_tensores;
    int64_t peso_original_bytes;
    int64_t peso_cuantizado_bytes;
    float error_promedio;
    float error_maximo;
    int formato_usado;
    float reduccion_porcentaje;
} QTEstadisticas;

QTEstadisticas qt_obtener_estadisticas(QSession* sesion);

#ifdef __cplusplus
}
#endif

#endif // QUANTIZATION_H
