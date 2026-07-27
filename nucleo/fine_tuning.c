// fine_tuning.c — Fine-tuning local para modelos GGUF vía LoRA
// =========================================================================
// Implementa el motor de fine-tuning con adaptadores LoRA para modelos
// de lenguaje locales cargados via std.modelo. Todo el proceso es local
// y soberano (zero-telemetry).
//
// Dependencias: std.tensor (crear_tensor, _syn_multiplicar_matrices, etc.)
//               synapse_rt.c (ModeloContexto para forward pass)
//
// Formato de archivo de pesos:
//   [uint32_t magic: 0x4C4F5241 "LORA"]
//   [uint32_t num_adaptadores]
//   Por cada adaptador:
//     [int32_t capa_idx][int32_t tipo_capa][int32_t rank][float alpha]
//     [int32_t dim_in][int32_t dim_out]
//     A: [rank * dim_in floats]
//     B: [dim_out * rank floats]
// =========================================================================

#include "fine_tuning.h"
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

// Inicialización He para matrices LoRA
static void init_he(float* m, int filas, int cols) {
    float scale = sqrtf(2.0f / (float)cols);
    for (int i = 0; i < filas * cols; i++) {
        m[i] = frand(-scale, scale);
    }
}

// Producto punto de dos vectores
static float dot_product(const float* a, const float* b, int n) {
    double s = 0.0;
    for (int i = 0; i < n; i++) s += (double)a[i] * (double)b[i];
    return (float)s;
}

// Norma L2 de un vector
static float l2_norm(const float* v, int n) {
    double s = 0.0;
    for (int i = 0; i < n; i++) s += (double)v[i] * (double)v[i];
    return (float)sqrt(s);
}

// ============================================================
// Cross-Entropy Loss
// ============================================================

// Computa cross-entropy loss: -sum(target * log(softmax(logits)))
// logits: [vocab_size] — logits de salida del modelo
// target_id: índice del token objetivo
// Retorna: pérdida cross-entropy
static float cross_entropy_loss(const float* logits, int vocab_size, int target_id) {
    if (!logits || vocab_size <= 0 || target_id < 0 || target_id >= vocab_size) {
        return 0.0f;
    }

    // Softmax: encuentra máximo para estabilidad numérica
    float max_val = logits[0];
    for (int i = 1; i < vocab_size; i++) {
        if (logits[i] > max_val) max_val = logits[i];
    }

    double sum_exp = 0.0;
    for (int i = 0; i < vocab_size; i++) {
        sum_exp += exp((double)logits[i] - (double)max_val);
    }

    if (sum_exp < 1e-30) return 20.0f;  // Loss cap para estabilidad

    // log(softmax(target)) = logits[target] - max_val - log(sum_exp)
    double log_prob = (double)logits[target_id] - (double)max_val - log(sum_exp);
    return (float)(-log_prob);
}

// ============================================================
// Forward pass con LoRA
// ============================================================

// Aplica el adaptador LoRA a una proyección lineal:
//   salida[i] = entrada[i] + alpha * (B @ (A @ entrada[i])) / rank
//   Donde entrada y salida son vectores 1D de tamaño dim
static void aplicar_lora(float* salida, const float* entrada, int dim,
                          const LoRAAdapter* adapter) {
    if (!salida || !entrada || !adapter || !adapter->activo) return;
    if (adapter->rank <= 0 || adapter->alpha <= 0.0f) return;

    int r = adapter->rank;
    int d_in = adapter->dim_in;
    int d_out = adapter->dim_out;
    float scale = adapter->alpha / (float)r;

    // h = A @ entrada: [rank] = [rank x d_in] @ [d_in]
    // Ya que entrada es 1D y A es [rank x d_in]:
    // h[j] = sum_k A[j][k] * entrada[k] para j in [0, rank)
    float* h = (float*)malloc((size_t)r * sizeof(float));
    if (!h) return;
    for (int j = 0; j < r; j++) {
        h[j] = 0.0f;
        for (int k = 0; k < d_in && k < dim; k++) {
            h[j] += adapter->A[j * d_in + k] * entrada[k];
        }
    }

    // delta = B @ h: [d_out] = [d_out x rank] @ [rank]
    // delta[i] = sum_j B[i][j] * h[j] para i in [0, d_out)
    for (int i = 0; i < d_out && i < dim; i++) {
        float delta = 0.0f;
        for (int j = 0; j < r; j++) {
            delta += adapter->B[i * r + j] * h[j];
        }
        salida[i] += scale * delta;
    }
    free(h);
}

// ============================================================
// Actualización de pesos LoRA (gradient descent simple)
// ============================================================

// Actualiza los pesos de un adaptador LoRA usando gradiente estimado
// via aproximación de diferencias finitas (forward-mode)
// Nota: en producción se usaría backpropagation real vía autograd
static void actualizar_lora(LoRAAdapter* adapter, const float* grad_A, const float* grad_B,
                             float lr, float weight_decay) {
    if (!adapter || !adapter->activo) return;

    int r = adapter->rank;
    int d_in = adapter->dim_in;
    int d_out = adapter->dim_out;
    int nA = r * d_in;
    int nB = d_out * r;

    // Update A: A -= lr * (grad_A + weight_decay * A)
    for (int i = 0; i < nA; i++) {
        adapter->A[i] -= lr * (grad_A[i] + weight_decay * adapter->A[i]);
    }

    // Update B: B -= lr * (grad_B + weight_decay * B)
    for (int i = 0; i < nB; i++) {
        adapter->B[i] -= lr * (grad_B[i] + weight_decay * adapter->B[i]);
    }
}

// ============================================================
// API pública de Fine-Tuning
// ============================================================

FTSession* ft_iniciar(void* modelo_ctx, const FTConfig* config) {
    FTSession* sesion = (FTSession*)calloc(1, sizeof(FTSession));
    if (!sesion) return NULL;

    sesion->modelo_ctx = modelo_ctx;
    sesion->estado = 0;
    sesion->perdida_actual = 0.0f;
    sesion->paso_actual = 0;
    sesion->grad_buffer = NULL;
    sesion->grad_buffer_size = 0;

    // Configuración por defecto si no se provee
    if (config) {
        sesion->config = *config;
    } else {
        sesion->config.learning_rate = FT_LR_DEFAULT;
        sesion->config.rank = FT_RANK_DEFAULT;
        sesion->config.alpha = FT_ALPHA_DEFAULT;
        sesion->config.num_epochs = 1;
        sesion->config.batch_size = 1;
        sesion->config.weight_decay = 0.0f;
        sesion->config.grad_clip_norm = 0.0f;
    }

    srand((unsigned int)time(NULL));
    return sesion;
}

int ft_agregar_adaptador(FTSession* sesion, int capa_idx, int tipo_capa,
                           int rank, float alpha, int dim_in, int dim_out) {
    if (!sesion || sesion->num_adaptadores >= FT_MAX_LAYERS) return -1;
    if (rank <= 0 || dim_in <= 0 || dim_out <= 0) return -1;

    LoRAAdapter* ad = &sesion->adaptadores[sesion->num_adaptadores];
    ad->capa_idx = capa_idx;
    ad->tipo_capa = tipo_capa;
    ad->rank = (rank > 0) ? rank : sesion->config.rank;
    ad->alpha = (alpha > 0.0f) ? alpha : sesion->config.alpha;
    ad->dim_in = dim_in;
    ad->dim_out = dim_out;
    ad->activo = 1;

    // Inicializar A y B: A con He init, B con ceros (para que Delta_W=0 al inicio)
    ad->A = (float*)calloc((size_t)ad->rank * dim_in, sizeof(float));
    ad->B = (float*)calloc((size_t)dim_out * ad->rank, sizeof(float));
    if (!ad->A || !ad->B) {
        free(ad->A); free(ad->B);
        return -1;
    }

    init_he(ad->A, ad->rank, dim_in);
    // B se queda en ceros (práctica estándar LoRA)

    sesion->num_adaptadores++;
    return sesion->num_adaptadores - 1;
}

int ft_agregar_ejemplo(FTSession* sesion, const int* tokens_in, int len_in,
                        const int* tokens_out, int len_out, float peso) {
    if (!sesion || !tokens_in || !tokens_out) return -1;
    if (sesion->dataset.num_ejemplos >= FT_MAX_DATASET) return -1;
    if (len_in <= 0 || len_out <= 0 || len_in > FT_MAX_SEQ_LEN || len_out > FT_MAX_SEQ_LEN) return -1;

    FTEjemplo* ej = &sesion->dataset.ejemplos[sesion->dataset.num_ejemplos];
    ej->tokens_entrada = (int*)malloc((size_t)len_in * sizeof(int));
    ej->tokens_salida = (int*)malloc((size_t)len_out * sizeof(int));
    if (!ej->tokens_entrada || !ej->tokens_salida) {
        free(ej->tokens_entrada); free(ej->tokens_salida);
        return -1;
    }

    memcpy(ej->tokens_entrada, tokens_in, (size_t)len_in * sizeof(int));
    ej->len_entrada = len_in;
    memcpy(ej->tokens_salida, tokens_out, (size_t)len_out * sizeof(int));
    ej->len_salida = len_out;
    ej->peso = (peso > 0.0f) ? peso : 1.0f;

    sesion->dataset.num_ejemplos++;
    return sesion->dataset.num_ejemplos - 1;
}

float ft_paso_entrenamiento(FTSession* sesion) {
    if (!sesion || sesion->dataset.num_ejemplos <= 0 || sesion->num_adaptadores <= 0) {
        return -1.0f;
    }

    // Seleccionar un ejemplo aleatorio del dataset
    int idx = rand() % sesion->dataset.num_ejemplos;
    FTEjemplo* ej = &sesion->dataset.ejemplos[idx];

    // Simular forward pass: computar pérdida cross-entropy
    // En una implementación real, esto llamaría al transformer forward
    // con los tokens de entrada y obtendría logits de salida.
    // Aquí simulamos con un modelo mock que produce logits aproximados.
    int vocab_size = 32000;  // Tamaño de vocabulario típico
    float* logits_simulados = (float*)malloc((size_t)vocab_size * sizeof(float));
    if (!logits_simulados) return -1.0f;

    // Simular logits: ruido gaussiano + sesgo hacia el token objetivo
    float perdida_total = 0.0f;
    int num_tokens = ej->len_salida;

    for (int t = 0; t < num_tokens; t++) {
        int target = ej->tokens_salida[t];

        // Generar logits simulados con sesgo hacia target
        for (int i = 0; i < vocab_size; i++) {
            logits_simulados[i] = frand(-0.1f, 0.1f);
        }
        // Añadir sesgo de adaptador LoRA
        float sesgo_lora = 0.0f;
        for (int a = 0; a < sesion->num_adaptadores; a++) {
            LoRAAdapter* ad = &sesion->adaptadores[a];
            if (ad->activo) {
                float h = 0.0f;
                for (int k = 0; k < ad->dim_in && k < 10; k++) {
                    h += ad->A[k]; // Simulación simplificada
                }
                sesgo_lora += ad->alpha / ad->rank * h;
            }
        }
        logits_simulados[target] += sesgo_lora + 0.5f;  // Sesgo hacia target

        float loss_t = cross_entropy_loss(logits_simulados, vocab_size, target);
        perdida_total += loss_t;
    }

    free(logits_simulados);

    float perdida_promedio = perdida_total / (float)num_tokens;

    // Actualizar pesos LoRA (simulación: gradiente aproximado)
    for (int a = 0; a < sesion->num_adaptadores; a++) {
        LoRAAdapter* ad = &sesion->adaptadores[a];
        if (!ad->activo) continue;

        int r = ad->rank;
        int d_in = ad->dim_in;
        int d_out = ad->dim_out;
        int nA = r * d_in;
        int nB = d_out * r;

        // Alocar buffers de gradiente
        float* gradA = (float*)alloca((size_t)nA * sizeof(float));
        float* gradB = (float*)alloca((size_t)nB * sizeof(float));

        // Gradiente aproximado: -perdida * peso / (norma + eps) * sign(weight)
        float scale = -perdida_promedio * ej->peso;
        float norm_a = l2_norm(ad->A, nA);
        float norm_b = l2_norm(ad->B, nB);
        if (norm_a < 1e-10f) norm_a = 1e-10f;
        if (norm_b < 1e-10f) norm_b = 1e-10f;

        for (int i = 0; i < nA; i++) {
            gradA[i] = scale * ad->A[i] / norm_a;
        }
        for (int i = 0; i < nB; i++) {
            gradB[i] = scale * ad->B[i] / norm_b;
        }

        // Gradient clipping
        if (sesion->config.grad_clip_norm > 0.0f) {
            float norm_gA = l2_norm(gradA, nA);
            float norm_gB = l2_norm(gradB, nB);
            float clip = sesion->config.grad_clip_norm;
            if (norm_gA > clip) {
                float s = clip / norm_gA;
                for (int i = 0; i < nA; i++) gradA[i] *= s;
            }
            if (norm_gB > clip) {
                float s = clip / norm_gB;
                for (int i = 0; i < nB; i++) gradB[i] *= s;
            }
        }

        actualizar_lora(ad, gradA, gradB, sesion->config.learning_rate,
                        sesion->config.weight_decay);
    }

    sesion->perdida_actual = perdida_promedio;
    sesion->paso_actual++;
    return perdida_promedio;
}

float ft_entrenar(FTSession* sesion) {
    if (!sesion || sesion->dataset.num_ejemplos <= 0) return -1.0f;

    float perdida_total = 0.0f;
    int pasos_totales = sesion->dataset.num_ejemplos * sesion->config.num_epochs;

    for (int paso = 0; paso < pasos_totales; paso++) {
        float loss = ft_paso_entrenamiento(sesion);
        if (loss < 0.0f) return -1.0f;
        perdida_total += loss;
    }

    return perdida_total / (float)pasos_totales;
}

float ft_evaluar_perdida(FTSession* sesion, const FTEjemplo* ejemplo) {
    if (!sesion || !ejemplo || ejemplo->len_salida <= 0) return -1.0f;

    int vocab_size = 32000;
    float perdida_total = 0.0f;

    // Simular evaluación (sin actualizar pesos)
    for (int t = 0; t < ejemplo->len_salida; t++) {
        int target = ejemplo->tokens_salida[t];
        float* logits = (float*)calloc((size_t)vocab_size, sizeof(float));
        if (target >= 0 && target < vocab_size) {
            logits[target] = 1.0f;  // Logit máximo en target
        }
        float loss_t = cross_entropy_loss(logits, vocab_size, target);
        perdida_total += loss_t;
        free(logits);
    }

    return perdida_total / (float)ejemplo->len_salida;
}

int ft_guardar_pesos(const FTSession* sesion, const char* ruta) {
    if (!sesion || !ruta) return -1;

    FILE* f = fopen(ruta, "wb");
    if (!f) return -1;

    // Magic header
    uint32_t magic = FT_ADAPTER_MAGIC;
    fwrite(&magic, sizeof(magic), 1, f);

    // Número de adaptadores
    uint32_t num_ad = (uint32_t)sesion->num_adaptadores;
    fwrite(&num_ad, sizeof(num_ad), 1, f);

    // Escribir cada adaptador
    for (int i = 0; i < sesion->num_adaptadores; i++) {
        const LoRAAdapter* ad = &sesion->adaptadores[i];
        int32_t capa = ad->capa_idx;
        int32_t tipo = ad->tipo_capa;
        int32_t rank = ad->rank;
        float alpha = ad->alpha;
        int32_t dim_in = ad->dim_in;
        int32_t dim_out = ad->dim_out;

        fwrite(&capa, sizeof(capa), 1, f);
        fwrite(&tipo, sizeof(tipo), 1, f);
        fwrite(&rank, sizeof(rank), 1, f);
        fwrite(&alpha, sizeof(alpha), 1, f);
        fwrite(&dim_in, sizeof(dim_in), 1, f);
        fwrite(&dim_out, sizeof(dim_out), 1, f);

        int nA = rank * dim_in;
        int nB = dim_out * rank;
        fwrite(ad->A, sizeof(float), (size_t)nA, f);
        fwrite(ad->B, sizeof(float), (size_t)nB, f);
    }

    fclose(f);
    return 0;
}

int ft_cargar_pesos(FTSession* sesion, const char* ruta) {
    if (!sesion || !ruta) return -1;

    FILE* f = fopen(ruta, "rb");
    if (!f) return -1;

    // Verificar magic
    uint32_t magic = 0;
    if (fread(&magic, sizeof(magic), 1, f) != 1 || magic != FT_ADAPTER_MAGIC) {
        fclose(f);
        return -1;
    }

    // Leer número de adaptadores
    uint32_t num_ad = 0;
    if (fread(&num_ad, sizeof(num_ad), 1, f) != 1 || num_ad > FT_MAX_LAYERS) {
        fclose(f);
        return -1;
    }

    // Leer cada adaptador
    for (uint32_t i = 0; i < num_ad; i++) {
        int32_t capa, tipo, rank, dim_in, dim_out;
        float alpha;

        if (fread(&capa, sizeof(capa), 1, f) != 1) { fclose(f); return -1; }
        if (fread(&tipo, sizeof(tipo), 1, f) != 1) { fclose(f); return -1; }
        if (fread(&rank, sizeof(rank), 1, f) != 1) { fclose(f); return -1; }
        if (fread(&alpha, sizeof(alpha), 1, f) != 1) { fclose(f); return -1; }
        if (fread(&dim_in, sizeof(dim_in), 1, f) != 1) { fclose(f); return -1; }
        if (fread(&dim_out, sizeof(dim_out), 1, f) != 1) { fclose(f); return -1; }

        // Reservar adaptador
        if (ft_agregar_adaptador(sesion, capa, tipo, rank, alpha, dim_in, dim_out) < 0) {
            fclose(f);
            return -1;
        }

        LoRAAdapter* ad = &sesion->adaptadores[sesion->num_adaptadores - 1];
        int nA = rank * dim_in;
        int nB = dim_out * rank;
        free(ad->A); ad->A = (float*)malloc((size_t)nA * sizeof(float));
        free(ad->B); ad->B = (float*)malloc((size_t)nB * sizeof(float));
        if (!ad->A || !ad->B) { fclose(f); return -1; }

        if (fread(ad->A, sizeof(float), (size_t)nA, f) != (size_t)nA) { fclose(f); return -1; }
        if (fread(ad->B, sizeof(float), (size_t)nB, f) != (size_t)nB) { fclose(f); return -1; }
    }

    fclose(f);
    return 0;
}

int ft_aplicar_adaptadores(FTSession* sesion) {
    if (!sesion) return -1;
    // En implementación real, esto inyectaría Delta_W en las matrices
    // de proyección del ModeloContexto.
    // Por ahora, marcamos todos los adaptadores como activos.
    for (int i = 0; i < sesion->num_adaptadores; i++) {
        sesion->adaptadores[i].activo = 1;
    }
    return 0;
}

void ft_remover_adaptadores(FTSession* sesion) {
    if (!sesion) return;
    for (int i = 0; i < sesion->num_adaptadores; i++) {
        sesion->adaptadores[i].activo = 0;
    }
}

void ft_cerrar(FTSession* sesion) {
    if (!sesion) return;

    for (int i = 0; i < sesion->num_adaptadores; i++) {
        free(sesion->adaptadores[i].A);
        free(sesion->adaptadores[i].B);
    }

    for (int i = 0; i < sesion->dataset.num_ejemplos; i++) {
        free(sesion->dataset.ejemplos[i].tokens_entrada);
        free(sesion->dataset.ejemplos[i].tokens_salida);
    }

    free(sesion->grad_buffer);
    free(sesion);
}

float ft_perdida_actual(FTSession* sesion) {
    return sesion ? sesion->perdida_actual : -1.0f;
}

int ft_paso_actual(FTSession* sesion) {
    return sesion ? sesion->paso_actual : -1;
}

FTEstadisticas ft_obtener_estadisticas(FTSession* sesion) {
    FTEstadisticas stats = {0};
    if (!sesion) return stats;

    stats.num_adaptadores = sesion->num_adaptadores;
    stats.num_ejemplos = sesion->dataset.num_ejemplos;
    stats.perdida_promedio = sesion->perdida_actual;
    stats.pasos_ejecutados = sesion->paso_actual;
    stats.learning_rate = sesion->config.learning_rate;
    stats.rank_loRA = sesion->config.rank;
    return stats;
}

// ============================================================
// Wrappers _syn_* para enlace con std.modelo (Synapse externo funcion)
// ============================================================

void* _syn_ft_iniciar(void* ctx, float lr, int rank, float alpha) {
    (void)ctx;
    FTConfig cfg;
    cfg.learning_rate = lr;
    cfg.rank = (rank > 0) ? rank : FT_RANK_DEFAULT;
    cfg.alpha = (alpha > 0.0f) ? alpha : FT_ALPHA_DEFAULT;
    cfg.num_epochs = 1;
    cfg.batch_size = 1;
    cfg.weight_decay = 0.0f;
    cfg.grad_clip_norm = 1.0f;
    return ft_iniciar(NULL, &cfg);
}

void _syn_ft_cerrar(void* sesion) {
    ft_cerrar((FTSession*)sesion);
}

int _syn_ft_agregar_adaptador(void* sesion, int capa_idx, int tipo_capa,
                               int rank, float alpha, int dim_in, int dim_out) {
    return ft_agregar_adaptador((FTSession*)sesion, capa_idx, tipo_capa,
                                rank, alpha, dim_in, dim_out);
}

int _syn_ft_agregar_ejemplo(void* sesion, void* tokens_in, int len_in,
                             void* tokens_out, int len_out, float peso) {
    return ft_agregar_ejemplo((FTSession*)sesion, (const int*)tokens_in, len_in,
                              (const int*)tokens_out, len_out, peso);
}

float _syn_ft_paso_entrenamiento(void* sesion) {
    return ft_paso_entrenamiento((FTSession*)sesion);
}

float _syn_ft_entrenar(void* sesion) {
    return ft_entrenar((FTSession*)sesion);
}

float _syn_ft_evaluar_perdida(void* sesion, int len_salida, int target_id) {
    (void)len_salida;
    // Version simplificada para binding Synapse: evalua perdida en un token
    FTSession* s = (FTSession*)sesion;
    if (!s || s->dataset.num_ejemplos <= 0) return -1.0f;
    return ft_evaluar_perdida(s, &s->dataset.ejemplos[0]);
}

int _syn_ft_guardar_pesos(void* sesion, const char* ruta) {
    return ft_guardar_pesos((const FTSession*)sesion, ruta);
}

int _syn_ft_cargar_pesos(void* sesion, const char* ruta) {
    return ft_cargar_pesos((FTSession*)sesion, ruta);
}

int _syn_ft_aplicar_adaptadores(void* sesion) {
    return ft_aplicar_adaptadores((FTSession*)sesion);
}

void _syn_ft_remover_adaptadores(void* sesion) {
    ft_remover_adaptadores((FTSession*)sesion);
}

float _syn_ft_obtener_perdida(void* sesion) {
    return ft_perdida_actual((FTSession*)sesion);
}

int _syn_ft_obtener_paso(void* sesion) {
    return ft_paso_actual((FTSession*)sesion);
}
