// quantization.c — Cuantización de modelos GGUF (FP32/FP16 → INT8/INT4)
// =========================================================================
// Implementa la transformación de pesos de alta precisión a formatos
// eficientes para ejecución en hardware limitado. Zero-telemetry.
//
// Formatos:
//   INT8:  simétrico por bloque de 64 elementos, escala por bloque
//   INT4:  simétrico por bloque de 32 elementos, empaquetado 2 por byte
//   FP16:  media precisión IEEE 754
// =========================================================================

#include "quantization.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// ============================================================
// Helpers internos
// ============================================================

// Encode FP32 a FP16 (rango: ±65504, precisión: ~3.3 decimal digits)
static uint16_t fp32_a_fp16(float v) {
    uint32_t bits;
    memcpy(&bits, &v, sizeof(bits));
    uint32_t sign = (bits >> 16) & 0x8000;
    int32_t exp = ((bits >> 23) & 0xFF) - 127 + 15;
    uint32_t mant = bits & 0x007FFFFF;

    if (exp <= 0) {
        // Subnormal/subrango
        if (exp < -10) return (uint16_t)sign;
        mant = (mant | 0x00800000) >> (1 - exp);
        return (uint16_t)(sign | (mant >> 13));
    }
    if (exp >= 31) {
        // Infinito o NaN
        if (mant) return (uint16_t)(sign | 0x7E00 | (mant >> 13));
        return (uint16_t)(sign | 0x7C00);
    }
    return (uint16_t)(sign | ((uint32_t)exp << 10) | (mant >> 13));
}

// Decode FP16 a FP32
static float fp16_a_fp32(uint16_t h) {
    uint32_t sign = ((uint32_t)h & 0x8000) << 16;
    int32_t exp = ((h >> 10) & 0x1F) - 15 + 127;
    uint32_t mant = (uint32_t)(h & 0x03FF) << 13;

    if (exp <= 0) {
        if (exp < -10) {
            uint32_t r = sign;
            float out;
            memcpy(&out, &r, sizeof(out));
            return out;
        }
        mant = (mant | 0x3C000000) >> (1 - exp);
    } else if (exp >= 255) {
        if (mant) {
            uint32_t r = sign | 0x7F800000 | mant;
            float out;
            memcpy(&out, &r, sizeof(out));
            return out;
        }
        uint32_t r = sign | 0x7F800000;
        float out;
        memcpy(&out, &r, sizeof(out));
        return out;
    }
    uint32_t r = sign | ((uint32_t)exp << 23) | mant;
    float out;
    memcpy(&out, &r, sizeof(out));
    return out;
}

// Cuantización INT8 por bloque: encuentra escala óptima
static float _bloque_escala_int8(const float* datos, int n) {
    float max_abs = 0.0f;
    for (int i = 0; i < n; i++) {
        float a = fabsf(datos[i]);
        if (a > max_abs) max_abs = a;
    }
    return (max_abs > 1e-10f) ? max_abs / 127.0f : 1e-10f;
}

// Cuantización INT4 por bloque: encuentra escala óptima
static float _bloque_escala_int4(const float* datos, int n) {
    float max_abs = 0.0f;
    for (int i = 0; i < n; i++) {
        float a = fabsf(datos[i]);
        if (a > max_abs) max_abs = a;
    }
    return (max_abs > 1e-10f) ? max_abs / 7.0f : 1e-10f;
}

// ============================================================
// API pública
// ============================================================

QSession* qt_iniciar(const QConfig* config) {
    QSession* sesion = (QSession*)calloc(1, sizeof(QSession));
    if (!sesion) return NULL;

    if (config) {
        sesion->config = *config;
    } else {
        sesion->config.formato_destino = QT_FORMAT_INT8;
        sesion->config.calibrar = 0;
        sesion->config.block_size = 64;
        sesion->config.error_max_permil = 0.01f;
        sesion->config.num_calib_ejemplos = 0;
    }

    sesion->reduccion_peso_estimada = 1.0f;
    return sesion;
}

int qt_agregar_tensor(QSession* sesion, const float* datos,
                       int filas, int columnas, const char* nombre) {
    if (!sesion || !datos || filas <= 0 || columnas <= 0) return -1;
    if (sesion->num_tensores >= QT_MAX_TENSORS) return -1;

    QTensor* t = &sesion->tensores[sesion->num_tensores];
    int n = filas * columnas;

    // Configurar header
    t->header.filas = filas;
    t->header.columnas = columnas;
    t->header.formato = QT_FORMAT_FP32;
    t->header.escala = 1.0f;
    t->header.tamano_bytes = n * (int)sizeof(float);
    if (nombre) {
        strncpy(t->header.nombre, nombre, 63);
        t->header.nombre[63] = '\0';
    } else {
        snprintf(t->header.nombre, 64, "tensor_%d", sesion->num_tensores);
    }

    // Copiar datos FP32 al session
    t->datos_fp32 = (float*)malloc((size_t)n * sizeof(float));
    if (!t->datos_fp32) return -1;
    memcpy(t->datos_fp32, datos, (size_t)n * sizeof(float));
    t->datos_fp32_actualizado = 1;

    // Por ahora datos cuantizados = NULL (se llena en cuantización)
    t->datos = NULL;

    sesion->peso_original_bytes += (int64_t)n * (int64_t)sizeof(float);

    int idx = sesion->num_tensores;
    sesion->num_tensores++;
    return idx;
}

int qt_cuantizar_tensor(QSession* sesion, int idx_tensor) {
    if (!sesion || idx_tensor < 0 || idx_tensor >= sesion->num_tensores) return -1;

    QTensor* t = &sesion->tensores[idx_tensor];
    if (!t->datos_fp32) return -1;

    int filas = t->header.filas;
    int columnas = t->header.columnas;
    int n = filas * columnas;
    int formato = sesion->config.formato_destino;
    int block_size = sesion->config.block_size;

    // Calcular tamaño de bloques
    int num_bloques = (n + block_size - 1) / block_size;

    if (formato == QT_FORMAT_INT8) {
        // INT8: 1 byte por elemento + 4 bytes de escala por bloque
        int tamano = n * (int)sizeof(int8_t) + num_bloques * (int)sizeof(float);
        t->datos = (uint8_t*)calloc(1, (size_t)tamano + 16);
        if (!t->datos) return -1;

        int8_t* q_data = (int8_t*)t->datos;
        float* scales = (float*)((uint8_t*)t->datos + (size_t)n * sizeof(int8_t));
        t->header.escala = 0.0f;
        float error_max_ctx = 0.0f;

        for (int b = 0; b < num_bloques; b++) {
            int start = b * block_size;
            int end = (start + block_size < n) ? start + block_size : n;
            int blk_n = end - start;

            float scale = _bloque_escala_int8(&t->datos_fp32[start], blk_n);
            scales[b] = scale;

            for (int i = start; i < end; i++) {
                int8_t qv = (int8_t)(t->datos_fp32[i] / scale);
                if (qv < -127) qv = -127;
                q_data[i] = qv;

                // Acumular error
                float reconst = qv * scale;
                float err = fabsf(reconst - t->datos_fp32[i]);
                if (err > error_max_ctx) error_max_ctx = err;
            }
        }

        sesion->error_maximo = error_max_ctx;
        t->header.formato = QT_FORMAT_INT8;
        t->header.tamano_bytes = tamano;
        sesion->peso_cuantizado_bytes += tamano;

    } else if (formato == QT_FORMAT_INT4) {
        // INT4: 2 elementos por byte + 4 bytes de escala por bloque
        int n_bytes = (n + 1) / 2;
        int tamano = n_bytes * (int)sizeof(uint8_t) + num_bloques * (int)sizeof(float);
        t->datos = (uint8_t*)calloc(1, (size_t)tamano + 16);
        if (!t->datos) return -1;

        uint8_t* q_data = (uint8_t*)t->datos;
        float* scales = (float*)((uint8_t*)t->datos + (size_t)n_bytes);
        float error_max_ctx = 0.0f;

        for (int b = 0; b < num_bloques; b++) {
            int start = b * block_size;
            int end = (start + block_size < n) ? start + block_size : n;
            int blk_n = end - start;

            float scale = _bloque_escala_int4(&t->datos_fp32[start], blk_n);
            scales[b] = scale;

            for (int i = start; i < end; i++) {
                int qv = (int)(t->datos_fp32[i] / scale);
                if (qv > 7) qv = 7;
                if (qv < -7) qv = -7;
                uint8_t qv4 = (uint8_t)(qv & 0xF);  // Keep lower 4 bits

                // Pack: even indices in high nibble, odd in low
                int byte_idx = i / 2;
                if (i % 2 == 0) {
                    q_data[byte_idx] = (q_data[byte_idx] & 0x0F) | (qv4 << 4);
                } else {
                    q_data[byte_idx] = (q_data[byte_idx] & 0xF0) | qv4;
                }

                // Acumular error (usar qv, no int4_qv)
                float reconst = (float)qv * scale;
                float err = fabsf(reconst - t->datos_fp32[i]);
                if (err > error_max_ctx) error_max_ctx = err;
            }
        }

        sesion->error_maximo = error_max_ctx;
        t->header.formato = QT_FORMAT_INT4;
        t->header.tamano_bytes = tamano;
        sesion->peso_cuantizado_bytes += tamano;

    } else if (formato == QT_FORMAT_FP16) {
        // FP16: 2 bytes por elemento
        int tamano = n * (int)sizeof(uint16_t);
        t->datos = (uint8_t*)malloc((size_t)tamano);
        if (!t->datos) return -1;

        uint16_t* fp16 = (uint16_t*)t->datos;
        for (int i = 0; i < n; i++) {
            fp16[i] = fp32_a_fp16(t->datos_fp32[i]);
        }

        t->header.formato = QT_FORMAT_FP16;
        t->header.tamano_bytes = tamano;
        sesion->peso_cuantizado_bytes += tamano;
    }

    t->datos_fp32_actualizado = 0;
    return 0;
}

int qt_cuantizar_todos(QSession* sesion) {
    if (!sesion) return -1;
    int count = 0;
    for (int i = 0; i < sesion->num_tensores; i++) {
        if (qt_cuantizar_tensor(sesion, i) == 0) count++;
    }
    return count;
}

float* qt_descuantizar_tensor(QSession* sesion, int idx_tensor) {
    if (!sesion || idx_tensor < 0 || idx_tensor >= sesion->num_tensores) return NULL;
    QTensor* t = &sesion->tensores[idx_tensor];

    if (t->datos_fp32 && t->datos_fp32_actualizado) {
        return t->datos_fp32;
    }

    int n = t->header.filas * t->header.columnas;
    int block_size = sesion->config.block_size;

    if (!t->datos_fp32) {
        t->datos_fp32 = (float*)calloc((size_t)n, sizeof(float));
        if (!t->datos_fp32) return NULL;
    }

    if (t->header.formato == QT_FORMAT_FP32) {
        // Ya está en FP32
        t->datos_fp32_actualizado = 1;
        return t->datos_fp32;
    }

    int num_bloques = (n + block_size - 1) / block_size;

    if (t->header.formato == QT_FORMAT_FP16) {
        uint16_t* fp16 = (uint16_t*)t->datos;
        for (int i = 0; i < n; i++) {
            t->datos_fp32[i] = fp16_a_fp32(fp16[i]);
        }
    } else if (t->header.formato == QT_FORMAT_INT8) {
        int8_t* q_data = (int8_t*)t->datos;
        float* scales = (float*)((uint8_t*)t->datos + (size_t)n * sizeof(int8_t));
        for (int b = 0; b < num_bloques; b++) {
            int start = b * block_size;
            int end = (start + block_size < n) ? start + block_size : n;
            float scale = scales[b];
            for (int i = start; i < end; i++) {
                t->datos_fp32[i] = q_data[i] * scale;
            }
        }
    } else if (t->header.formato == QT_FORMAT_INT4) {
        int n_bytes = (n + 1) / 2;
        uint8_t* q_data = (uint8_t*)t->datos;
        float* scales = (float*)((uint8_t*)t->datos + (size_t)n_bytes);
        for (int b = 0; b < num_bloques; b++) {
            int start = b * block_size;
            int end = (start + block_size < n) ? start + block_size : n;
            float scale = scales[b];
            for (int i = start; i < end; i++) {
                int byte_idx = i / 2;
                int qv;
                if (i % 2 == 0) {
                    qv = (q_data[byte_idx] >> 4) & 0x0F;
                } else {
                    qv = q_data[byte_idx] & 0x0F;
                }
                // Extend sign from 4 bits
                if (qv & 0x08) qv |= 0xFFFFFFF0;
                t->datos_fp32[i] = (float)qv * scale;
            }
        }
    }

    t->datos_fp32_actualizado = 1;
    return t->datos_fp32;
}

void qt_fp16_a_fp32(const uint16_t* src, float* dst, int n) {
    if (!src || !dst) return;
    for (int i = 0; i < n; i++) dst[i] = fp16_a_fp32(src[i]);
}

void qt_fp32_a_fp16(const float* src, uint16_t* dst, int n) {
    if (!src || !dst) return;
    for (int i = 0; i < n; i++) dst[i] = fp32_a_fp16(src[i]);
}

float qt_calcular_error(QSession* sesion, int idx_tensor) {
    if (!sesion || idx_tensor < 0 || idx_tensor >= sesion->num_tensores) return -1.0f;
    QTensor* t = &sesion->tensores[idx_tensor];
    if (!t->datos_fp32 || !t->datos) return -1.0f;

    int n = t->header.filas * t->header.columnas;

    // Hacer una copia de los datos FP32 originales antes de descuantizar
    // (qt_descuantizar_tensor puede sobreescribir datos_fp32)
    float* original = (float*)malloc((size_t)n * sizeof(float));
    if (!original) return -1.0f;
    memcpy(original, t->datos_fp32, (size_t)n * sizeof(float));

    float* reconst = qt_descuantizar_tensor(sesion, idx_tensor);
    if (!reconst) {
        free(original);
        return -1.0f;
    }

    double mse = 0.0;
    for (int i = 0; i < n; i++) {
        double err = (double)original[i] - (double)reconst[i];
        mse += err * err;
    }
    mse /= (double)n;

    // Calcular error promedio relativo
    double max_abs = 0.0;
    for (int i = 0; i < n; i++) {
        double a = fabs((double)original[i]);
        if (a > max_abs) max_abs = a;
    }

    free(original);

    if (max_abs < 1e-10) return 0.0f;
    return (float)(sqrt(mse) / max_abs);
}

int qt_guardar(QSession* sesion, const char* ruta) {
    if (!sesion || !ruta) return -1;

    FILE* f = fopen(ruta, "wb");
    if (!f) return -1;

    // Calcular tamaño total
    int64_t total_bytes = 4 + 4 + sizeof(QConfig) + 4; // magic + version + config + num
    for (int i = 0; i < sesion->num_tensores; i++) {
        total_bytes += sizeof(QTensorHeader) + sesion->tensores[i].header.tamano_bytes;
    }

    // Escribir cabecera
    uint32_t magic = QT_MAGIC_HEADER;
    uint32_t version = QT_VERSION;
    fwrite(&magic, sizeof(magic), 1, f);
    fwrite(&version, sizeof(version), 1, f);
    fwrite(&sesion->config, sizeof(QConfig), 1, f);

    uint32_t num = (uint32_t)sesion->num_tensores;
    fwrite(&num, sizeof(num), 1, f);

    // Escribir tensores
    for (int i = 0; i < sesion->num_tensores; i++) {
        QTensor* t = &sesion->tensores[i];
        fwrite(&t->header, sizeof(QTensorHeader), 1, f);
        if (t->datos && t->header.tamano_bytes > 0) {
            fwrite(t->datos, 1, (size_t)t->header.tamano_bytes, f);
        }
    }

    fclose(f);
    return 0;
}

int qt_cargar(QSession* sesion, const char* ruta) {
    if (!sesion || !ruta) return -1;

    FILE* f = fopen(ruta, "rb");
    if (!f) return -1;

    uint32_t magic, version;
    if (fread(&magic, sizeof(magic), 1, f) != 1 || magic != QT_MAGIC_HEADER) {
        fclose(f); return -1;
    }
    if (fread(&version, sizeof(version), 1, f) != 1 || version > QT_VERSION) {
        fclose(f); return -1;
    }
    if (fread(&sesion->config, sizeof(QConfig), 1, f) != 1) {
        fclose(f); return -1;
    }

    uint32_t num = 0;
    if (fread(&num, sizeof(num), 1, f) != 1 || num > QT_MAX_TENSORS) {
        fclose(f); return -1;
    }

    for (uint32_t i = 0; i < num; i++) {
        QTensor* t = &sesion->tensores[sesion->num_tensores];
        if (fread(&t->header, sizeof(QTensorHeader), 1, f) != 1) {
            fclose(f); return -1;
        }

        if (t->header.tamano_bytes > 0) {
            t->datos = malloc((size_t)t->header.tamano_bytes);
            if (!t->datos || fread(t->datos, 1, (size_t)t->header.tamano_bytes, f) != (size_t)t->header.tamano_bytes) {
                fclose(f); return -1;
            }
        }

        sesion->num_tensores++;
        sesion->peso_cuantizado_bytes += t->header.tamano_bytes;
    }

    fclose(f);
    return 0;
}

void qt_cerrar(QSession* sesion) {
    if (!sesion) return;
    for (int i = 0; i < sesion->num_tensores; i++) {
        free(sesion->tensores[i].datos);
        free(sesion->tensores[i].datos_fp32);
    }
    free(sesion);
}

// ============================================================
// Inferencia cuantizada
// ============================================================

float qt_producto_punto_int8(const int8_t* a, float escala_a,
                              const float* b, int n) {
    if (!a || !b || n <= 0) return 0.0f;
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        sum += (double)a[i] * (double)b[i];
    }
    return (float)(sum * (double)escala_a);
}

float qt_producto_punto_int4(const uint8_t* a, float escala_a,
                              const float* b, int n) {
    if (!a || !b || n <= 0) return 0.0f;
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        int byte_idx = i / 2;
        int qv;
        if (i % 2 == 0) {
            qv = (a[byte_idx] >> 4) & 0x0F;
        } else {
            qv = a[byte_idx] & 0x0F;
        }
        if (qv & 0x08) qv |= 0xFFFFFFF0;
        sum += (double)qv * (double)b[i];
    }
    return (float)(sum * (double)escala_a);
}

// ============================================================
// Integración RAG
// ============================================================

int qt_seleccionar_formato(int ram_mb) {
    if (ram_mb <= 0) return QT_FORMAT_INT8;  // Default seguro
    if (ram_mb >= 65536) return QT_FORMAT_FP16;  // 64GB+ → FP16
    if (ram_mb >= 16384) return QT_FORMAT_INT8;  // 16GB+ → INT8
    if (ram_mb >= 4096) return QT_FORMAT_INT4;   // 4GB+ → INT4
    return QT_FORMAT_INT4;  // < 4GB → INT4 forzado
}

float qt_estimar_tamano_modelo(int num_params_millones, int formato) {
    float bytes_por_param;
    switch (formato) {
        case QT_FORMAT_FP32: bytes_por_param = 4.0f; break;
        case QT_FORMAT_FP16: bytes_por_param = 2.0f; break;
        case QT_FORMAT_INT8: bytes_por_param = 1.0f; break;
        case QT_FORMAT_INT4: bytes_por_param = 0.5f; break;
        default: bytes_por_param = 4.0f;
    }
    return (float)num_params_millones * bytes_por_param / 1024.0f;  // MB
}

float qt_reduccion_formato(int formato) {
    switch (formato) {
        case QT_FORMAT_FP32: return 0.0f;    // 0% reducción
        case QT_FORMAT_FP16: return 0.5f;    // 50% reducción
        case QT_FORMAT_INT8: return 0.75f;   // 75% reducción
        case QT_FORMAT_INT4: return 0.875f;  // 87.5% reducción
        default: return 0.0f;
    }
}

QTEstadisticas qt_obtener_estadisticas(QSession* sesion) {
    QTEstadisticas stats = {0};
    if (!sesion) return stats;

    stats.num_tensores = sesion->num_tensores;
    stats.peso_original_bytes = sesion->peso_original_bytes;
    stats.peso_cuantizado_bytes = sesion->peso_cuantizado_bytes;
    stats.error_promedio = sesion->error_promedio;
    stats.error_maximo = sesion->error_maximo;
    stats.formato_usado = sesion->config.formato_destino;

    if (sesion->peso_original_bytes > 0) {
        stats.reduccion_porcentaje = 100.0f * (1.0f - (float)sesion->peso_cuantizado_bytes /
                                           (float)sesion->peso_original_bytes);
    }

    return stats;
}

// ============================================================
// Wrappers _syn_qt_* para enlace con std.modelo
// ============================================================

void* _syn_qt_iniciar(int formato, int block_size) {
    QConfig cfg;
    cfg.formato_destino = formato;
    cfg.calibrar = 0;
    cfg.block_size = (block_size > 0) ? block_size : QT_BLOCK_SIZE_INT8;
    cfg.error_max_permil = 0.01f;
    cfg.num_calib_ejemplos = 0;
    return qt_iniciar(&cfg);
}

int _syn_qt_agregar_tensor(void* sesion, const float* datos,
                            int filas, int columnas, const char* nombre) {
    return qt_agregar_tensor((QSession*)sesion, datos, filas, columnas, nombre);
}

int _syn_qt_cuantizar_tensor(void* sesion, int idx) {
    return qt_cuantizar_tensor((QSession*)sesion, idx);
}

int _syn_qt_cuantizar_todos(void* sesion) {
    return qt_cuantizar_todos((QSession*)sesion);
}

float* _syn_qt_descuantizar_tensor(void* sesion, int idx) {
    return qt_descuantizar_tensor((QSession*)sesion, idx);
}

void _syn_qt_fp16_a_fp32(const uint16_t* src, float* dst, int n) {
    qt_fp16_a_fp32(src, dst, n);
}

void _syn_qt_fp32_a_fp16(const float* src, uint16_t* dst, int n) {
    qt_fp32_a_fp16(src, dst, n);
}

int _syn_qt_guardar(void* sesion, const char* ruta) {
    return qt_guardar((QSession*)sesion, ruta);
}

int _syn_qt_cargar(void* sesion, const char* ruta) {
    return qt_cargar((QSession*)sesion, ruta);
}

void _syn_qt_cerrar(void* sesion) {
    qt_cerrar((QSession*)sesion);
}

int _syn_qt_seleccionar_formato(int ram_mb) {
    return qt_seleccionar_formato(ram_mb);
}

float _syn_qt_estimar_tamano_modelo(int params_m, int formato) {
    return qt_estimar_tamano_modelo(params_m, formato);
}
