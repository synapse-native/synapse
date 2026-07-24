// llama_client.h — Cliente HTTP nativo para llama.cpp server (API nativa /completion, /slot_save, /slot_restore, /embedding)
// Parte del núcleo Synapse LSP nativo — C99, Windows (WinHTTP) / POSIX (sockets)

#ifndef LLAMA_CLIENT_H
#define LLAMA_CLIENT_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Configuración por defecto
#define LLAMA_DEFAULT_HOST "127.0.0.1"
#define LLAMA_DEFAULT_PORT 8088
#define LLAMA_TIMEOUT_MS 30000

// Tipos opacos
typedef struct LlamaClient LlamaClient;

// Respuesta genérica de la API nativa llama.cpp
typedef struct {
    int es_ok;              // 1 = éxito, 0 = error
    char* respuesta;        // Texto generado / contenido (debe liberarse con llama_libre_respuesta)
    char* error;            // Mensaje de error si es_ok == 0
    int codigo_http;        // Código de estado HTTP
} LlamaRespuesta;

// Respuesta para /slot_save
typedef struct {
    int es_ok;
    char* slot_id;          // ID del slot guardado (debe liberarse)
    char* error;
    int codigo_http;
} LlamaSlotSaveRespuesta;

// Respuesta para /slot_restore
typedef struct {
    int es_ok;
    char* respuesta;        // Texto generado tras restaurar
    char* error;
    int codigo_http;
} LlamaSlotRestoreRespuesta;

// Respuesta para /embedding
typedef struct {
    int es_ok;
    float* embeddings;      // Array de floats (debe liberarse con llama_libre_embedding)
    int embedding_count;    // Número de embeddings
    int embedding_dim;      // Dimensión de cada embedding
    char* error;
    int codigo_http;
} LlamaEmbeddingRespuesta;

// Inicializa la librería HTTP (WSAStartup en Windows)
int llama_inicializar_red(void);

// Limpia recursos globales HTTP (WSACleanup en Windows)
void llama_cerrar_red(void);

// Crea un nuevo cliente para conectar a llama-server
LlamaClient* llama_cliente_crear(const char* host, int puerto);

// Destruye el cliente y libera memoria
void llama_cliente_destruir(LlamaClient* cliente);

// === ENDPOINT /completion ===
// Envía petición de generación a /completion (stream: false)
// Payload JSON estricto: {"prompt":"...", "n_predict":128, "temperature":0.7, "stop":["\n\n\n"]}
// prompt_ensamblado: prompt completo con [CONTEXTO_ARCHIVO], [LINEA_ACTUAL], [DIAGNOSTICOS]
// n_predict: máximo tokens a generar (default 128)
// temperature: temperatura de sampling (default 0.7)
// stop: array de strings de parada (ej: {"\n\n\n", "```"}), NULL para default
// stop_count: número de elementos en stop
LlamaRespuesta llama_generar(LlamaClient* cliente, const char* prompt_ensamblado,
                              int n_predict, double temperature,
                              const char** stop, int stop_count);

// Libera memoria de una respuesta de generación
void llama_libre_respuesta(LlamaRespuesta* resp);

// === ENDPOINT /slot_save ===
// Guarda el estado actual del slot (KV cache) en el servidor
// slot: índice del slot a guardar (0-based)
// Retorna slot_id que puede usarse para restaurar
LlamaSlotSaveRespuesta llama_slot_guardar(LlamaClient* cliente, int slot);

// Libera memoria de respuesta slot_save
void llama_libre_slot_save(LlamaSlotSaveRespuesta* resp);

// === ENDPOINT /slot_restore ===
// Restaura un slot previamente guardado
// slot: índice del slot a restaurar (0-based)
// slot_id: ID retornado por llama_slot_guardar
// prompt_ensamblado: prompt para continuar generación tras restaurar
// n_predict, temperature, stop, stop_count: parámetros de generación
LlamaSlotRestoreRespuesta llama_slot_restaurar(LlamaClient* cliente, int slot, const char* slot_id,
                                                const char* prompt_ensamblado,
                                                int n_predict, double temperature,
                                                const char** stop, int stop_count);

// Libera memoria de respuesta slot_restore
void llama_libre_slot_restore(LlamaSlotRestoreRespuesta* resp);

// === ENDPOINT /embedding ===
// Obtiene embeddings para el texto dado
// input: texto a embeddear (puede ser múltiples strings separados por \n para batch)
// Retorna array de floats [embedding_count x embedding_dim]
LlamaEmbeddingRespuesta llama_embedding(LlamaClient* cliente, const char* input);

// Libera memoria de respuesta embedding
void llama_libre_embedding(LlamaEmbeddingRespuesta* resp);

// Verifica si llama-server está corriendo y accesible (GET /health)
int llama_verificar_disponible(LlamaClient* cliente);

// Obtiene propiedades del modelo cargado (GET /props) — caller libera
char* llama_obtener_props(LlamaClient* cliente);

#ifdef __cplusplus
}
#endif

#endif // LLAMA_CLIENT_H