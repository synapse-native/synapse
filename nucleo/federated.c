// federated.c — Runtime de Aprendizaje Federado (FedAvg + Ed25519 + cluster)
// ======================================================================
// Implementa el algoritmo de promediado federado (Federated Averaging) 
// sobre la red de nodos del clúster Synapse (M8.x).
//
// Flujo FedAvg por ronda:
//   1. Coordinador distribuye pesos globales a workers
//   2. Cada worker entrena localmente (fine-tuning LoRA o destilación)
//   3. Workers firman gradientes con Ed25519 y los envían al coordinador
//   4. Coordinador verifica firmas, agrega por FedAvg ponderado
//   5. Coordinador actualiza pesos globales
//
// Zero-telemetry: firmas Ed25519, sin exposición de datos privados.
// ======================================================================

#include "federated.h"
#include "synapse_rt_types.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// Extern declarations for real Ed25519 functions from synapse_rt.c
extern int cluster_verificar_firma(CadenaSegura mensaje, CadenaSegura firma_hex,
                                    CadenaSegura clave_publica_hex);
extern CadenaSegura cluster_firmar_mensaje(CadenaSegura mensaje,
                                            CadenaSegura clave_privada_hex);

// ============================================================
// Helpers internos
// ============================================================

static float frand(float min, float max) {
    return min + (max - min) * ((float)rand() / (float)RAND_MAX);
}

// Genera una firma Ed25519 real para un payload de gradientes
// Utiliza cluster_firmar_mensaje() de synapse_rt.c (TweetNaCl backend)
static void _generar_firma_real(const float* grad, int n,
                                 const char* sk_hex, char* firma_out) {
    if (!grad || n <= 0 || !sk_hex || !firma_out) {
        firma_out[0] = '\0';
        return;
    }
    // Build message: raw gradient bytes
    CadenaSegura msg = { .longitud = n * (int)sizeof(float),
                         .datos = (const char*)grad };
    CadenaSegura sk = { .longitud = (int)strlen(sk_hex),
                         .datos = sk_hex };
    CadenaSegura firma = cluster_firmar_mensaje(msg, sk);
    if (firma.datos && firma.longitud > 0) {
        int copy_len = firma.longitud < FED_HEX_SIG_LEN - 1
                       ? firma.longitud : FED_HEX_SIG_LEN - 1;
        memcpy(firma_out, firma.datos, (size_t)copy_len);
        firma_out[copy_len] = '\0';
        free((void*)firma.datos);
    } else {
        firma_out[0] = '\0';
    }
}

// Verifica firma Ed25519 real usando cluster_verificar_firma() de synapse_rt.c
// Retorna 0 si la firma es válida, -1 si es inválida
static int _verificar_firma_real(const float* grad, int n,
                                  const char* firma_hex,
                                  const char* pubkey_hex) {
    if (!grad || n <= 0 || !firma_hex || !pubkey_hex) return -1;
    if (strlen(firma_hex) < 128 || strlen(pubkey_hex) < 64) return -1;

    // Build message: raw gradient bytes
    CadenaSegura msg = { .longitud = n * (int)sizeof(float),
                         .datos = (const char*)grad };
    CadenaSegura firma = { .longitud = (int)strlen(firma_hex),
                            .datos = firma_hex };
    CadenaSegura pk = { .longitud = (int)strlen(pubkey_hex),
                         .datos = pubkey_hex };
    return cluster_verificar_firma(msg, firma, pk);
}

// Busca un worker por ID
static int _buscar_worker(FEDSession* sesion, const char* id) {
    if (!sesion || !id) return -1;
    for (int i = 0; i < sesion->num_workers; i++) {
        if (strcmp(sesion->workers[i].id, id) == 0) return i;
    }
    return -1;
}

// ============================================================
// API pública
// ============================================================

FEDSession* fed_iniciar(const float* pesos_iniciales, int num_pesos,
                         const FedConfig* config) {
    if (num_pesos <= 0 || num_pesos > FED_MAX_WEIGHTS) return NULL;

    FEDSession* sesion = (FEDSession*)calloc(1, sizeof(FEDSession));
    if (!sesion) return NULL;

    // Configuración
    if (config) {
        sesion->config = *config;
    } else {
        sesion->config.num_rounds = 10;
        sesion->config.aggregate_mode = FED_AGGREGATE_AVG;
        sesion->config.learning_rate = 0.001f;
        sesion->config.client_fraction = 1.0f;
        sesion->config.timeout_ms = FED_TIMEOUT_MS;
        sesion->config.min_workers = FED_MIN_WORKERS;
        sesion->config.use_ed25519 = 1;
        sesion->config.use_compression = 0;
    }

    // Pesos globales
    sesion->num_pesos = num_pesos;
    sesion->pesos_globales = (float*)calloc((size_t)num_pesos, sizeof(float));
    if (!sesion->pesos_globales) { free(sesion); return NULL; }

    if (pesos_iniciales) {
        memcpy(sesion->pesos_globales, pesos_iniciales,
               (size_t)num_pesos * sizeof(float));
    }

    // Buffer de agregación
    sesion->buffer_agregacion = (float*)calloc((size_t)num_pesos, sizeof(float));
    if (!sesion->buffer_agregacion) {
        free(sesion->pesos_globales); free(sesion); return NULL;
    }

    sesion->ronda_actual = 0;
    sesion->estado = 0;
    sesion->perdida_global = 0.0f;
    sesion->mejor_perdida = 1e10f;
    sesion->ft_contexto = NULL;
    sesion->kd_contexto = NULL;

    // Claves Ed25519 simuladas
    snprintf(sesion->clave_publica_hex, FED_HEX_KEY_LEN,
             "fed_pub_%016lx", (unsigned long)(uintptr_t)sesion);
    snprintf(sesion->clave_privada_hex, FED_HEX_KEY_LEN,
             "fed_priv_%016lx", (unsigned long)(uintptr_t)sesion);

    srand((unsigned int)time(NULL));
    return sesion;
}

int fed_registrar_worker(FEDSession* sesion, const char* id, const char* ip,
                          int puerto, const char* pubkey_hex, float peso) {
    if (!sesion || !id || !ip) return -1;
    if (sesion->num_workers >= FED_MAX_WORKERS) return -1;
    if (_buscar_worker(sesion, id) >= 0) return -1;  // ID duplicado

    FedWorker* w = &sesion->workers[sesion->num_workers];
    strncpy(w->id, id, FED_NAME_MAX - 1);
    w->id[FED_NAME_MAX - 1] = '\0';
    strncpy(w->ip, ip, 63);
    w->ip[63] = '\0';
    w->puerto = puerto;
    if (pubkey_hex) {
        strncpy(w->pubkey_hex, pubkey_hex, FED_HEX_KEY_LEN - 1);
        w->pubkey_hex[FED_HEX_KEY_LEN - 1] = '\0';
    }
    w->peso = (peso > 0.0f) ? peso : 1.0f;
    w->estado = FED_WORKER_IDLE;
    w->ultimo_latido = (int64_t)time(NULL);
    w->gradientes_recibidos = NULL;
    w->num_gradientes = 0;

    sesion->num_workers++;
    return sesion->num_workers - 1;
}

int fed_eliminar_worker(FEDSession* sesion, const char* id) {
    if (!sesion || !id) return -1;
    int idx = _buscar_worker(sesion, id);
    if (idx < 0) return -1;

    free(sesion->workers[idx].gradientes_recibidos);

    // Desplazar workers restantes
    for (int i = idx; i < sesion->num_workers - 1; i++) {
        sesion->workers[i] = sesion->workers[i + 1];
    }
    sesion->num_workers--;
    return 0;
}

int fed_distribuir_pesos(FEDSession* sesion) {
    if (!sesion || !sesion->pesos_globales) return -1;

    int enviados = 0;
    for (int i = 0; i < sesion->num_workers; i++) {
        FedWorker* w = &sesion->workers[i];
        if (w->estado != FED_WORKER_TIMEOUT && w->estado != FED_WORKER_FAILED) {
            w->estado = FED_WORKER_TRAINING;
            // En producción: enviar pesos por UDP via cluster_enviar/recibir
            // Simulación: marcar como enviado
            enviados++;
        }
    }
    return enviados;
}

int fed_recibir_gradientes(FEDSession* sesion, const char* worker_id,
                            const float* gradientes, int num_grad,
                            const char* firma_hex) {
    if (!sesion || !worker_id || !gradientes) return -1;
    if (num_grad != sesion->num_pesos) return -1;

    int idx = _buscar_worker(sesion, worker_id);
    if (idx < 0) return -1;

    FedWorker* w = &sesion->workers[idx];

    // Verificar firma Ed25519 si está habilitado
    if (sesion->config.use_ed25519 && firma_hex) {
        int rc = fed_verificar_firma_gradiente(gradientes, num_grad,
                                                firma_hex, w->pubkey_hex,
                                                worker_id);
        if (rc != 0) return -1;  // Firma inválida
    }

    // Almacenar gradientes recibidos
    free(w->gradientes_recibidos);
    w->gradientes_recibidos = (float*)malloc((size_t)num_grad * sizeof(float));
    if (!w->gradientes_recibidos) return -1;
    memcpy(w->gradientes_recibidos, gradientes, (size_t)num_grad * sizeof(float));
    w->num_gradientes = num_grad;
    w->estado = FED_WORKER_SENT;
    w->ultimo_latido = (int64_t)time(NULL);

    return 0;
}

int fed_agregar_gradientes(FEDSession* sesion, const float* const* grad_workers,
                            const float* weights, int num_workers) {
    if (!sesion || !grad_workers || !weights) return -1;
    if (num_workers <= 0 || num_workers > sesion->num_workers) return -1;

    // Limpiar buffer de agregación
    memset(sesion->buffer_agregacion, 0,
           (size_t)sesion->num_pesos * sizeof(float));

    double peso_total = 0.0;
    int n = sesion->num_pesos;

    if (sesion->config.aggregate_mode == FED_AGGREGATE_AVG) {
        // FedAvg estándar: promedio simple
        for (int w = 0; w < num_workers; w++) {
            if (!grad_workers[w]) continue;
            float wgt = weights[w];
            peso_total += (double)wgt;
            for (int i = 0; i < n; i++) {
                sesion->buffer_agregacion[i] += grad_workers[w][i] * wgt;
            }
        }
    } else {
        // FedAvg ponderado por tamaño de dataset
        for (int w = 0; w < num_workers; w++) {
            if (!grad_workers[w]) continue;
            float wgt = weights[w];
            peso_total += (double)wgt;
            for (int i = 0; i < n; i++) {
                sesion->buffer_agregacion[i] += grad_workers[w][i] * wgt;
            }
        }
    }

    // Normalizar
    if (peso_total > 0.0) {
        double inv = 1.0 / peso_total;
        for (int i = 0; i < n; i++) {
            sesion->buffer_agregacion[i] = (float)((double)sesion->buffer_agregacion[i] * inv);
        }
    }

    // Actualizar pesos globales: w = w - lr * grad_promedio
    float lr = sesion->config.learning_rate;
    for (int i = 0; i < n; i++) {
        sesion->pesos_globales[i] -= lr * sesion->buffer_agregacion[i];
    }

    return 0;
}

float fed_ronda_fedavg(FEDSession* sesion) {
    if (!sesion) return -1.0f;
    if (sesion->num_workers < sesion->config.min_workers) return -1.0f;

    int n = sesion->num_pesos;
    int num_workers = sesion->num_workers;

    // 1. Distribuir pesos a workers
    int enviados = fed_distribuir_pesos(sesion);
    if (enviados <= 0) return -1.0f;

    // 2. Liberar buffers de gradientes de rondas anteriores
    for (int i = 0; i < num_workers; i++) {
        free(sesion->workers[i].gradientes_recibidos);
        sesion->workers[i].gradientes_recibidos = NULL;
        sesion->workers[i].num_gradientes = 0;
    }

    // 3. Simular entrenamiento local de workers
    // En producción: esperar respuesta UDP de cada worker
    // Aquí: generar gradientes sintéticos para workers activos
    int workers_respondieron = 0;
    float* grad_workers[FED_MAX_WORKERS];
    float weights[FED_MAX_WORKERS];
    float perdida_total = 0.0f;

    for (int i = 0; i < num_workers; i++) {
        FedWorker* w = &sesion->workers[i];
        if (w->estado != FED_WORKER_TRAINING) continue;

        // Alocar gradiente para este worker (única alocación: se usa en agregación)
        float* grad = (float*)malloc((size_t)n * sizeof(float));
        if (!grad) continue;

        // Gradiente simulado: ruido gaussiano con dirección hacia cero (minimización)
        float perdida_local = 0.0f;
        for (int j = 0; j < n; j++) {
            float g = frand(-0.01f, 0.01f);
            // Dirigir hacia convergencia: -0.001 * peso_actual
            g -= 0.001f * sesion->pesos_globales[j];
            grad[j] = g;
            perdida_local += g * g;
        }
        perdida_local = sqrtf(perdida_local / (float)n);

        // Firmar gradientes con Ed25519 real si está habilitado
        if (sesion->config.use_ed25519) {
            char firma[FED_HEX_SIG_LEN];
            _generar_firma_real(grad, n, sesion->clave_privada_hex, firma);
        }

        // Almacenar gradiente directamente en el worker (sin alocación duplicada)
        // Nota: en producción, los gradientes llegan por red y se almacenan aquí
        w->gradientes_recibidos = grad;  // Transferencia de ownership
        w->num_gradientes = n;
        w->estado = FED_WORKER_SENT;
        w->ultimo_latido = (int64_t)time(NULL);

        grad_workers[workers_respondieron] = grad;
        weights[workers_respondieron] = w->peso;
        perdida_total += perdida_local;
        workers_respondieron++;
    }

    if (workers_respondieron < sesion->config.min_workers) {
        for (int i = 0; i < workers_respondieron; i++) free(grad_workers[i]);
        return -1.0f;
    }

    // 3. Agregar gradientes vía FedAvg
    fed_agregar_gradientes(sesion, (const float* const*)grad_workers,
                            weights, workers_respondieron);

    // NOTA: No liberar grad_workers[i] — la memoria fue transferida a
    // w->gradientes_recibidos via ownership transfer en el bucle anterior.
    // El pre-loop al inicio de la próxima ronda (free(w->gradientes_recibidos))
    // se encarga de la limpieza.

    float perdida_promedio = perdida_total / (float)workers_respondieron;
    sesion->perdida_global = perdida_promedio;
    if (perdida_promedio < sesion->mejor_perdida) {
        sesion->mejor_perdida = perdida_promedio;
    }

    sesion->ronda_actual++;
    return perdida_promedio;
}

float fed_entrenar(FEDSession* sesion) {
    if (!sesion) return -1.0f;

    int rondas = sesion->config.num_rounds;
    float perdida_total = 0.0f;

    sesion->estado = 1;  // Entrenando

    for (int r = 0; r < rondas; r++) {
        float loss = fed_ronda_fedavg(sesion);
        if (loss < 0.0f) {
            // Manejar fallo: marcar workers timeouteados
            fed_manejar_timeouts(sesion, (int64_t)(time(NULL) * 1000));
            // Si aún hay suficientes workers, continuar
            int activos = 0;
            for (int i = 0; i < sesion->num_workers; i++) {
                if (sesion->workers[i].estado != FED_WORKER_TIMEOUT) activos++;
            }
            if (activos < sesion->config.min_workers) {
                sesion->estado = 2;
                return -1.0f;
            }
            loss = sesion->perdida_global;  // Usar última pérdida conocida
        }
        perdida_total += loss;
    }

    sesion->estado = 2;  // Completado
    return perdida_total / (float)rondas;
}

int fed_verificar_firma_gradiente(const float* gradientes, int num_grad,
                                   const char* firma_hex,
                                   const char* pubkey_hex,
                                   const char* worker_id) {
    if (!gradientes || !firma_hex || !pubkey_hex || !worker_id) return -1;
    if (num_grad <= 0) return -1;

    // Verificación Ed25519 real via cluster_verificar_firma() (TweetNaCl)
    return _verificar_firma_real(gradientes, num_grad,
                                  firma_hex, pubkey_hex);
}

int fed_manejar_timeouts(FEDSession* sesion, int64_t tiempo_actual_ms) {
    if (!sesion) return -1;

    int timeouteados = 0;
    for (int i = 0; i < sesion->num_workers; i++) {
        FedWorker* w = &sesion->workers[i];
        if (w->estado == FED_WORKER_TRAINING || w->estado == FED_WORKER_IDLE) {
            int64_t diff = tiempo_actual_ms - (int64_t)w->ultimo_latido * 1000;
            if (diff > (int64_t)sesion->config.timeout_ms) {
                w->estado = FED_WORKER_TIMEOUT;
                timeouteados++;
            }
        }
    }
    return timeouteados;
}

FedRoundProgress fed_obtener_progreso(FEDSession* sesion) {
    FedRoundProgress prog = {0};
    if (!sesion) return prog;

    prog.ronda_actual = sesion->ronda_actual;
    prog.perdida_promedio = sesion->perdida_global;

    for (int i = 0; i < sesion->num_workers; i++) {
        if (sesion->workers[i].estado == FED_WORKER_SENT) {
            prog.workers_activos++;
        } else if (sesion->workers[i].estado == FED_WORKER_TIMEOUT) {
            prog.workers_timeout++;
        }
    }

    return prog;
}

FEDEstadisticas fed_obtener_estadisticas(FEDSession* sesion) {
    FEDEstadisticas stats = {0};
    if (!sesion) return stats;

    stats.num_workers_registrados = sesion->num_workers;
    stats.rondas_completadas = sesion->ronda_actual;
    stats.perdida_global_actual = sesion->perdida_global;
    stats.perdida_global_mejor = sesion->mejor_perdida;

    int activos = 0;
    for (int i = 0; i < sesion->num_workers; i++) {
        if (sesion->workers[i].estado != FED_WORKER_TIMEOUT) activos++;
    }
    stats.num_workers_activos = activos;

    if (sesion->ronda_actual > 0) {
        stats.tasa_participacion = (float)activos / (float)sesion->num_workers;
    }

    return stats;
}

int fed_guardar(const FEDSession* sesion, const char* ruta) {
    if (!sesion || !ruta) return -1;

    FILE* f = fopen(ruta, "wb");
    if (!f) return -1;

    uint32_t magic = FED_MAGIC_HEADER;
    uint32_t version = FED_VERSION;
    fwrite(&magic, sizeof(magic), 1, f);
    fwrite(&version, sizeof(version), 1, f);
    fwrite(&sesion->config, sizeof(FedConfig), 1, f);

    uint32_t nw = (uint32_t)sesion->num_workers;
    fwrite(&nw, sizeof(nw), 1, f);
    for (uint32_t i = 0; i < nw; i++) {
        fwrite(&sesion->workers[i], sizeof(FedWorker), 1, f);
    }

    uint32_t np = (uint32_t)sesion->num_pesos;
    fwrite(&np, sizeof(np), 1, f);
    fwrite(sesion->pesos_globales, sizeof(float), np, f);

    uint32_t ronda = (uint32_t)sesion->ronda_actual;
    fwrite(&ronda, sizeof(ronda), 1, f);
    fwrite(&sesion->perdida_global, sizeof(float), 1, f);
    fwrite(&sesion->mejor_perdida, sizeof(float), 1, f);

    fclose(f);
    return 0;
}

int fed_cargar(FEDSession* sesion, const char* ruta) {
    if (!sesion || !ruta) return -1;

    FILE* f = fopen(ruta, "rb");
    if (!f) return -1;

    uint32_t magic, version;
    if (fread(&magic, sizeof(magic), 1, f) != 1 || magic != FED_MAGIC_HEADER) {
        fclose(f); return -1;
    }
    if (fread(&version, sizeof(version), 1, f) != 1 || version > FED_VERSION) {
        fclose(f); return -1;
    }
    if (fread(&sesion->config, sizeof(FedConfig), 1, f) != 1) {
        fclose(f); return -1;
    }

    uint32_t nw = 0;
    if (fread(&nw, sizeof(nw), 1, f) != 1 || nw > FED_MAX_WORKERS) {
        fclose(f); return -1;
    }
    for (uint32_t i = 0; i < nw; i++) {
        if (fread(&sesion->workers[i], sizeof(FedWorker), 1, f) != 1) {
            fclose(f); return -1;
        }
        sesion->workers[i].gradientes_recibidos = NULL;
        sesion->workers[i].num_gradientes = 0;
    }
    sesion->num_workers = (int)nw;

    uint32_t np = 0;
    if (fread(&np, sizeof(np), 1, f) != 1 || np > FED_MAX_WEIGHTS) {
        fclose(f); return -1;
    }
    free(sesion->pesos_globales);
    free(sesion->buffer_agregacion);
    sesion->num_pesos = (int)np;
    sesion->pesos_globales = (float*)malloc((size_t)np * sizeof(float));
    sesion->buffer_agregacion = (float*)calloc((size_t)np, sizeof(float));
    if (!sesion->pesos_globales || !sesion->buffer_agregacion) {
        fclose(f); return -1;
    }
    if (fread(sesion->pesos_globales, sizeof(float), np, f) != np) {
        fclose(f); return -1;
    }

    uint32_t ronda;
    fread(&ronda, sizeof(ronda), 1, f);
    sesion->ronda_actual = (int)ronda;
    fread(&sesion->perdida_global, sizeof(float), 1, f);
    fread(&sesion->mejor_perdida, sizeof(float), 1, f);

    fclose(f);
    return 0;
}

void fed_cerrar(FEDSession* sesion) {
    if (!sesion) return;

    for (int i = 0; i < sesion->num_workers; i++) {
        free(sesion->workers[i].gradientes_recibidos);
    }

    free(sesion->pesos_globales);
    free(sesion->buffer_agregacion);
    free(sesion);
}

// ============================================================
// Wrappers _syn_fed_* para enlace con std.federated
// ============================================================

void* _syn_fed_iniciar(const float* pesos, int n, float lr, int rounds) {
    FedConfig cfg;
    cfg.num_rounds = (rounds > 0) ? rounds : 10;
    cfg.aggregate_mode = FED_AGGREGATE_AVG;
    cfg.learning_rate = (lr > 0.0f) ? lr : 0.001f;
    cfg.client_fraction = 1.0f;
    cfg.timeout_ms = FED_TIMEOUT_MS;
    cfg.min_workers = FED_MIN_WORKERS;
    cfg.use_ed25519 = 1;
    cfg.use_compression = 0;
    return fed_iniciar(pesos, n, &cfg);
}

void _syn_fed_cerrar(void* sesion) {
    fed_cerrar((FEDSession*)sesion);
}

int _syn_fed_registrar_worker(void* sesion, const char* id, const char* ip,
                               int puerto, const char* pubkey, float peso) {
    return fed_registrar_worker((FEDSession*)sesion, id, ip, puerto, pubkey, peso);
}

int _syn_fed_eliminar_worker(void* sesion, const char* id) {
    return fed_eliminar_worker((FEDSession*)sesion, id);
}

float _syn_fed_ronda_fedavg(void* sesion) {
    return fed_ronda_fedavg((FEDSession*)sesion);
}

float _syn_fed_entrenar(void* sesion) {
    return fed_entrenar((FEDSession*)sesion);
}

int _syn_fed_guardar(void* sesion, const char* ruta) {
    return fed_guardar((const FEDSession*)sesion, ruta);
}

int _syn_fed_cargar(void* sesion, const char* ruta) {
    return fed_cargar((FEDSession*)sesion, ruta);
}

int _syn_fed_verificar_firma(const float* grad, int n,
                              const char* firma, const char* pubkey,
                              const char* worker_id) {
    return fed_verificar_firma_gradiente(grad, n, firma, pubkey, worker_id);
}
