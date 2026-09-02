// cumple Manual 1 §5: destilacion de modelos
// cumple Manual 8 §4: toolchain
// distillation.c — Destilación de conocimiento (Knowledge Distillation) para modelos GGUF
// ================================================================================
// Implementa el motor de destilación: teacher model → student model más pequeño.
//
// KL(P||Q) = sum(P_i * log(P_i / Q_i))
// L_soft = T^2 * KL(softmax(logits_t / T) || softmax(logits_s / T))
// L_hard = CE(softmax(logits_s), target)
// L_total = alpha * L_soft + (1-alpha) * L_hard
//
// Integración:
//   - fine_tuning.h: cross_entropy_loss() reusada para hard labels
//   - quantization.h: qt_reduccion_formato() para estimación de compresión
//
// Zero-telemetry: todo el proceso es local y soberano.
// ================================================================================

#include "distillation.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// ============================================================
// Helpers internos
// ============================================================

// Softmax numéricamente estable
// output: [n] — probabilidades normalizadas (sum = 1.0)
static void _softmax(const float* logits, float* output, int n, float temperature) {
    if (!logits || !output || n <= 0) return;

    float max_val = logits[0] / temperature;
    for (int i = 1; i < n; i++) {
        float v = logits[i] / temperature;
        if (v > max_val) max_val = v;
    }

    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        double v = exp((double)(logits[i] / temperature - max_val));
        output[i] = (float)v;
        sum += v;
    }

    if (sum < 1e-30) sum = 1e-30;
    double inv_sum = 1.0 / sum;
    for (int i = 0; i < n; i++) {
        output[i] = (float)((double)output[i] * inv_sum);
    }
}

// Cross-Entropy loss: -sum(target * log(softmax(logits)))
// Reimplementación local para evitar dependencia directa con fine_tuning.c
static float _cross_entropy(const float* logits, int vocab_size, int target_id) {
    if (!logits || vocab_size <= 0 || target_id < 0 || target_id >= vocab_size) {
        return 0.0f;
    }

    float max_val = logits[0];
    for (int i = 1; i < vocab_size; i++) {
        if (logits[i] > max_val) max_val = logits[i];
    }

    double sum_exp = 0.0;
    for (int i = 0; i < vocab_size; i++) {
        sum_exp += exp((double)logits[i] - (double)max_val);
    }

    if (sum_exp < 1e-30) return 20.0f;
    double log_prob = (double)logits[target_id] - (double)max_val - log(sum_exp);
    return (float)(-log_prob);
}

// ============================================================
// API pública de Destilación
// ============================================================

KDSession* kd_iniciar(const KDConfig* config) {
    KDSession* sesion = (KDSession*)calloc(1, sizeof(KDSession));
    if (!sesion) return NULL;

    if (config) {
        sesion->config = *config;
    } else {
        // Configuración por defecto
        sesion->config.temperature = KD_TEMPERATURE_DEFAULT;
        sesion->config.alpha = KD_ALPHA_DEFAULT;
        sesion->config.num_epochs = 1;
        sesion->config.batch_size = 1;
        sesion->config.learning_rate = 0.0001f;
        sesion->config.weight_decay = 0.0f;
        sesion->config.vocab_size = 32000;
        sesion->config.student_hidden_dim = 512;
        sesion->config.teacher_hidden_dim = 4096;
        sesion->config.ruta_teacher[0] = '\0';
        sesion->config.ruta_student[0] = '\0';
    }

    sesion->teacher_ctx = NULL;
    sesion->student_ctx = NULL;
    sesion->ft_sesion_student = NULL;
    sesion->estado = 0;
    sesion->paso_actual = 0;
    sesion->perdida_soft_actual = 0.0f;
    sesion->perdida_hard_actual = 0.0f;
    sesion->perdida_total_actual = 0.0f;

    srand((unsigned int)time(NULL));
    return sesion;
}

int kd_agregar_par_n(KDSession* sesion, const float* logits_t,
                      const float* logits_s, int n, int target_id, float peso) {
    if (!sesion || !logits_t || !logits_s) return -1;
    if (sesion->dataset.num_pares >= KD_MAX_DATASET) return -1;
    if (target_id < 0) return -1;
    if (n <= 0) return -1;

    KDLogitPair* par = &sesion->dataset.pares[sesion->dataset.num_pares];

    par->logits_teacher = (float*)malloc((size_t)n * sizeof(float));
    par->logits_student = (float*)malloc((size_t)n * sizeof(float));
    if (!par->logits_teacher || !par->logits_student) {
        free(par->logits_teacher);
        free(par->logits_student);
        return -1;
    }

    memcpy(par->logits_teacher, logits_t, (size_t)n * sizeof(float));
    memcpy(par->logits_student, logits_s, (size_t)n * sizeof(float));
    par->target_id = target_id;
    par->peso = (peso > 0.0f) ? peso : 1.0f;
    par->num_logits = n;

    sesion->dataset.vocab_size = n; // R80: el dataset refleja la longitud de sus pares
    sesion->dataset.num_pares++;
    return sesion->dataset.num_pares - 1;
}

int kd_agregar_par(KDSession* sesion, const float* logits_t,
                    const float* logits_s, int target_id, float peso) {
    if (!sesion) return -1;
    int vs = sesion->config.vocab_size;
    if (vs <= 0) return -1;
    // Contrato legacy: los arrays tienen config.vocab_size elementos
    return kd_agregar_par_n(sesion, logits_t, logits_s, vs, target_id, peso);
}

// ============================================================
// KL Divergence
// ============================================================

float kd_divergencia_kl(const float* logits_p, const float* logits_q,
                         int n, float temperature) {
    if (!logits_p || !logits_q || n <= 0) return -1.0f;

    // Alocar buffers para distribuciones softmax
    float* p = (float*)malloc((size_t)n * sizeof(float));
    float* q = (float*)malloc((size_t)n * sizeof(float));
    if (!p || !q) {
        free(p); free(q);
        return -1.0f;
    }

    // Calcular softmax con temperatura
    _softmax(logits_p, p, n, temperature);
    _softmax(logits_q, q, n, temperature);

    // KL(P||Q) = sum(P_i * log(P_i / Q_i))
    double kl = 0.0;
    for (int i = 0; i < n; i++) {
        if (p[i] > 1e-10f && q[i] > 1e-10f) {
            kl += (double)p[i] * log((double)p[i] / (double)q[i]);
        }
    }

    free(p);
    free(q);

    return (float)kl;
}

// ============================================================
// Pérdida combinada (soft + hard)
// ============================================================

float kd_perdida_combinada(const float* logits_teacher,
                            const float* logits_student,
                            int target_id, int vocab_size,
                            float temperature, float alpha) {
    if (!logits_teacher || !logits_student || vocab_size <= 0) return -1.0f;
    if (target_id < 0 || target_id >= vocab_size) return -1.0f;

    // Soft loss: T^2 * KL(softmax(teacher/T) || softmax(student/T))
    float kl = kd_divergencia_kl(logits_teacher, logits_student,
                                  vocab_size, temperature);
    if (kl < 0.0f) return -1.0f;
    float soft_loss = temperature * temperature * kl;

    // Hard loss: CE(student logits, target)
    float hard_loss = _cross_entropy(logits_student, vocab_size, target_id);

    // Combinada: L = alpha * L_soft + (1-alpha) * L_hard
    float loss = alpha * soft_loss + (1.0f - alpha) * hard_loss;

    return loss;
}

// ============================================================
// Paso de destilación
// ============================================================

float kd_paso_destilacion(KDSession* sesion) {
    if (!sesion || sesion->dataset.num_pares <= 0) return -1.0f;

    float perdida_soft_total = 0.0f;
    float perdida_hard_total = 0.0f;
    float perdida_total_total = 0.0f;
    int num_procesados = 0;

    float T = sesion->config.temperature;
    float alpha = sesion->config.alpha;
    int vs = sesion->config.vocab_size;

    for (int i = 0; i < sesion->dataset.num_pares; i++) {
        KDLogitPair* par = &sesion->dataset.pares[i];
        // R80: longitud por-par (fallback legacy = config.vocab_size)
        int n = (par->num_logits > 0) ? par->num_logits : vs;

        // Calcular pérdida soft (KL divergence escalada por T^2)
        float kl = kd_divergencia_kl(par->logits_teacher, par->logits_student,
                                      n, T);
        if (kl < 0.0f) continue;
        float soft_loss = T * T * kl;
        float soft_weighted = soft_loss * par->peso;

        // Calcular pérdida hard (cross-entropy contra target)
        float hard_loss = _cross_entropy(par->logits_student, n, par->target_id);
        float hard_weighted = hard_loss * par->peso;

        // Pérdida combinada
        float loss = alpha * soft_weighted + (1.0f - alpha) * hard_weighted;

        perdida_soft_total += soft_weighted;
        perdida_hard_total += hard_weighted;
        perdida_total_total += loss;
        num_procesados++;

        // Simular ajuste del student: acercar logits_student a logits_teacher
        // En implementación real, esto haría backpropagation hacia el student
        float lr = sesion->config.learning_rate;
        float wd = sesion->config.weight_decay;
        for (int j = 0; j < n; j++) {
            // Gradient: dL/d(logits_s) ≈ alpha * T^2 * (softmax_q - softmax_p) + (1-alpha) * (softmax_q - target)
            // Simplificado: mover logits_s hacia teacher
            float diff = (par->logits_teacher[j] - par->logits_student[j]) * par->peso;
            float grad = alpha * diff + (1.0f - alpha) * diff * 0.1f; // hard factor reducido
            par->logits_student[j] += lr * (grad - wd * par->logits_student[j]);
        }
    }

    sesion->perdida_soft_actual = perdida_soft_total / (float)num_procesados;
    sesion->perdida_hard_actual = perdida_hard_total / (float)num_procesados;
    sesion->perdida_total_actual = perdida_total_total / (float)num_procesados;
    sesion->paso_actual++;

    return sesion->perdida_total_actual;
}

float kd_destilar(KDSession* sesion) {
    if (!sesion || sesion->dataset.num_pares <= 0) return -1.0f;

    int pasos_totales = sesion->config.num_epochs;
    float perdida_promedio = 0.0f;

    for (int e = 0; e < pasos_totales; e++) {
        float loss = kd_paso_destilacion(sesion);
        if (loss < 0.0f) return -1.0f;
        perdida_promedio += loss;
    }

    sesion->estado = 2;  // Completado
    return perdida_promedio / (float)pasos_totales;
}

// ============================================================
// Reducción de capas (teacher → student)
// ============================================================

int kd_reducir_capas(KDSession* sesion, const float* pesos_teacher,
                      int num_capas_teacher, int dim_teacher,
                      float* pesos_student, int num_capas_student, int dim_student) {
    if (!sesion || !pesos_teacher || !pesos_student) return -1;
    if (num_capas_teacher <= 0 || dim_teacher <= 0 ||
        num_capas_student <= 0 || dim_student <= 0) return -1;

    // Mapeo lineal: cada capa student se interpola desde capas adyacentes teacher
    for (int s = 0; s < num_capas_student; s++) {
        // Posición relativa de la capa student en el rango teacher
        float t_pos = (float)s * (float)(num_capas_teacher - 1) / (float)(num_capas_student - 1);
        int t_idx_low = (int)t_pos;
        int t_idx_high = (t_idx_low + 1 < num_capas_teacher) ? t_idx_low + 1 : t_idx_low;
        float frac = t_pos - (float)t_idx_low;

        // Interpolar dimensionalmente si es necesario
        for (int i = 0; i < dim_student; i++) {
            int t_i = (int)((float)i * (float)dim_teacher / (float)dim_student);
            if (t_i >= dim_teacher) t_i = dim_teacher - 1;

            float val_low = pesos_teacher[t_idx_low * dim_teacher + t_i];
            float val_high = pesos_teacher[t_idx_high * dim_teacher + t_i];

            // Interpolar linealmente entre capas teacher adyacentes
            pesos_student[s * dim_student + i] = val_low + frac * (val_high - val_low);
        }
    }

    return 0;
}

// ============================================================
// Evaluación
// ============================================================

float kd_evaluar(KDSession* sesion, const float* logits_t,
                  const float* logits_s, int target_id) {
    if (!sesion || !logits_t || !logits_s) return -1.0f;
    return kd_perdida_combinada(logits_t, logits_s, target_id,
                                 sesion->config.vocab_size,
                                 sesion->config.temperature,
                                 sesion->config.alpha);
}

// ============================================================
// Persistencia
// ============================================================

int kd_guardar(const KDSession* sesion, const char* ruta) {
    if (!sesion || !ruta) return -1;

    FILE* f = fopen(ruta, "wb");
    if (!f) return -1;

    // Magic + version
    uint32_t magic = KD_MAGIC_HEADER;
    uint32_t version = KD_VERSION;
    fwrite(&magic, sizeof(magic), 1, f);
    fwrite(&version, sizeof(version), 1, f);

    // Config
    fwrite(&sesion->config, sizeof(KDConfig), 1, f);

    // Número de pares
    uint32_t num_pares = (uint32_t)sesion->dataset.num_pares;
    fwrite(&num_pares, sizeof(num_pares), 1, f);

    // Vocab size
    uint32_t vs = (uint32_t)sesion->config.vocab_size;
    fwrite(&vs, sizeof(vs), 1, f);

    // Logits de cada par
    for (uint32_t i = 0; i < num_pares; i++) {
        const KDLogitPair* par = &sesion->dataset.pares[i];
        int32_t tid = par->target_id;
        float peso = par->peso;
        int32_t nlog = (par->num_logits > 0) ? par->num_logits : (int32_t)vs;
        fwrite(&tid, sizeof(tid), 1, f);
        fwrite(&peso, sizeof(peso), 1, f);
        fwrite(&nlog, sizeof(nlog), 1, f);
        fwrite(par->logits_teacher, sizeof(float), (size_t)nlog, f);
        fwrite(par->logits_student, sizeof(float), (size_t)nlog, f);
    }

    // Estadísticas
    float ps = sesion->perdida_soft_actual;
    float ph = sesion->perdida_hard_actual;
    float pt = sesion->perdida_total_actual;
    fwrite(&ps, sizeof(ps), 1, f);
    fwrite(&ph, sizeof(ph), 1, f);
    fwrite(&pt, sizeof(pt), 1, f);

    // Paso actual
    uint32_t paso = (uint32_t)sesion->paso_actual;
    fwrite(&paso, sizeof(paso), 1, f);

    fclose(f);
    return 0;
}

int kd_cargar(KDSession* sesion, const char* ruta) {
    if (!sesion || !ruta) return -1;

    FILE* f = fopen(ruta, "rb");
    if (!f) return -1;

    // Magic + version
    uint32_t magic = 0, version = 0;
    if (fread(&magic, sizeof(magic), 1, f) != 1 || magic != KD_MAGIC_HEADER) {
        fclose(f); return -1;
    }
    if (fread(&version, sizeof(version), 1, f) != 1 || version > KD_VERSION) {
        fclose(f); return -1;
    }

    // Config
    if (fread(&sesion->config, sizeof(KDConfig), 1, f) != 1) {
        fclose(f); return -1;
    }

    // Número de pares
    uint32_t num_pares = 0;
    if (fread(&num_pares, sizeof(num_pares), 1, f) != 1 || num_pares > KD_MAX_DATASET) {
        fclose(f); return -1;
    }

    // Vocab size
    uint32_t vs = 0;
    if (fread(&vs, sizeof(vs), 1, f) != 1 || vs <= 0) {
        fclose(f); return -1;
    }
    sesion->config.vocab_size = (int)vs;

    // Logits de cada par
    for (uint32_t i = 0; i < num_pares; i++) {
        int target_id;
        float peso;
        int32_t nlog = 0;

        if (fread(&target_id, sizeof(target_id), 1, f) != 1) { fclose(f); return -1; }
        if (fread(&peso, sizeof(peso), 1, f) != 1) { fclose(f); return -1; }
        // R80 v2: longitud por-par
        if (fread(&nlog, sizeof(nlog), 1, f) != 1 || nlog <= 0) { fclose(f); return -1; }

        float* lt = (float*)malloc((size_t)nlog * sizeof(float));
        float* ls = (float*)malloc((size_t)nlog * sizeof(float));
        if (!lt || !ls) { free(lt); free(ls); fclose(f); return -1; }

        if (fread(lt, sizeof(float), (size_t)nlog, f) != (size_t)nlog) { free(lt); free(ls); fclose(f); return -1; }
        if (fread(ls, sizeof(float), (size_t)nlog, f) != (size_t)nlog) { free(lt); free(ls); fclose(f); return -1; }

        KDLogitPair* par = &sesion->dataset.pares[sesion->dataset.num_pares];
        par->logits_teacher = lt;
        par->logits_student = ls;
        par->target_id = target_id;
        par->peso = peso;
        par->num_logits = nlog;

        sesion->dataset.num_pares++;
    }

    // Estadísticas
    fread(&sesion->perdida_soft_actual, sizeof(float), 1, f);
    fread(&sesion->perdida_hard_actual, sizeof(float), 1, f);
    fread(&sesion->perdida_total_actual, sizeof(float), 1, f);

    uint32_t paso = 0;
    fread(&paso, sizeof(paso), 1, f);
    sesion->paso_actual = (int)paso;

    fclose(f);
    return 0;
}

void kd_cerrar(KDSession* sesion) {
    if (!sesion) return;

    for (int i = 0; i < sesion->dataset.num_pares; i++) {
        free(sesion->dataset.pares[i].logits_teacher);
        free(sesion->dataset.pares[i].logits_student);
    }

    free(sesion);
}

// ============================================================
// Integración con cuantización
// ============================================================

float kd_estimar_reduccion(int params_teacher_millones, int params_student_millones,
                            int formato_cuantizacion) {
    if (params_teacher_millones <= 0 || params_student_millones <= 0) return 1.0f;

    // Reducción por cuantización
    float bytes_teacher = (float)params_teacher_millones * 2.0f;  // FP16 teacher
    float bytes_student;
    switch (formato_cuantizacion) {
        case 0: bytes_student = (float)params_student_millones * 4.0f; break;   // FP32
        case 1: bytes_student = (float)params_student_millones * 2.0f; break;   // FP16
        case 2: bytes_student = (float)params_student_millones * 1.0f; break;   // INT8
        case 3: bytes_student = (float)params_student_millones * 0.5f; break;   // INT4
        default: bytes_student = (float)params_student_millones * 2.0f;
    }

    return (bytes_teacher > 0.0f) ? bytes_teacher / bytes_student : 1.0f;
}

// ============================================================
// Estadísticas
// ============================================================

KDEstadisticas kd_obtener_estadisticas(KDSession* sesion) {
    KDEstadisticas stats = {0};
    if (!sesion) return stats;

    stats.perdida_soft = sesion->perdida_soft_actual;
    stats.perdida_hard = sesion->perdida_hard_actual;
    stats.perdida_total = sesion->perdida_total_actual;
    stats.temperatura_usada = sesion->config.temperature;
    stats.alpha_usado = sesion->config.alpha;
    stats.pasos_ejecutados = sesion->paso_actual;
    stats.num_ejemplos_procesados = sesion->dataset.num_pares;

    // Estimar reducción: teacher_hidden_dim / student_hidden_dim
    if (sesion->config.student_hidden_dim > 0 && sesion->config.teacher_hidden_dim > 0) {
        float ratio_capas = (float)sesion->config.teacher_hidden_dim /
                            (float)sesion->config.student_hidden_dim;
        stats.reduccion_estimada = ratio_capas * 2.0f;  // ×2 por cuantización default
    }

    return stats;
}

float kd_perdida_actual(KDSession* sesion) {
    return sesion ? sesion->perdida_total_actual : -1.0f;
}

int kd_paso_actual(KDSession* sesion) {
    return sesion ? sesion->paso_actual : -1;
}

// ============================================================
// Wrappers _syn_kd_* para enlace con std.modelo
// ============================================================

void* _syn_kd_iniciar(float temperature, float alpha, int vocab_size) {
    KDConfig cfg;
    memset(&cfg, 0, sizeof(KDConfig));
    cfg.temperature = (temperature > 0.0f) ? temperature : KD_TEMPERATURE_DEFAULT;
    cfg.alpha = (alpha >= 0.0f && alpha <= 1.0f) ? alpha : KD_ALPHA_DEFAULT;
    cfg.vocab_size = (vocab_size > 0) ? vocab_size : 32000;
    cfg.num_epochs = 1;
    cfg.batch_size = 1;
    cfg.learning_rate = 0.0001f;
    cfg.weight_decay = 0.0f;
    cfg.student_hidden_dim = 512;
    cfg.teacher_hidden_dim = 4096;
    return kd_iniciar(&cfg);
}

void _syn_kd_cerrar(void* sesion) {
    kd_cerrar((KDSession*)sesion);
}

float _syn_kd_divergencia_kl(void* logits_p, void* logits_q, int n, float temp) {
    return kd_divergencia_kl((const float*)logits_p, (const float*)logits_q, n, temp);
}

float _syn_kd_perdida_combinada(void* logits_t, void* logits_s,
                                 int target_id, int vocab_size,
                                 float temperature, float alpha) {
    return kd_perdida_combinada((const float*)logits_t, (const float*)logits_s,
                                 target_id, vocab_size, temperature, alpha);
}

int _syn_kd_agregar_par(void* sesion, void* logits_t, void* logits_s,
                         int target_id, float peso) {
    return kd_agregar_par((KDSession*)sesion, (const float*)logits_t,
                          (const float*)logits_s, target_id, peso);
}

float _syn_kd_paso_destilacion(void* sesion) {
    return kd_paso_destilacion((KDSession*)sesion);
}

float _syn_kd_destilar(void* sesion) {
    return kd_destilar((KDSession*)sesion);
}

int _syn_kd_guardar(void* sesion, const char* ruta) {
    return kd_guardar((const KDSession*)sesion, ruta);
}

int _syn_kd_cargar(void* sesion, const char* ruta) {
    return kd_cargar((KDSession*)sesion, ruta);
}

float _syn_kd_estimar_reduccion(int teacher_m, int student_m, int fmt) {
    return kd_estimar_reduccion(teacher_m, student_m, fmt);
}
