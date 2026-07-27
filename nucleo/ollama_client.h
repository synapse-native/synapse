// ollama_client.h — Cliente HTTP nativo para Ollama API
// Interfaz mínima para el servidor LSP Synapse
// Foundation — Implementación separada en synapse_llama_client.c (si aplica)

#ifndef OLLAMA_CLIENT_H
#define OLLAMA_CLIENT_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================
// Tipos de datos
// ============================================================

typedef struct OllamaCliente {
    char host[256];
    int puerto;
    char modelo[256];
    int socket_fd;
    int conectado;
} OllamaCliente;

typedef struct OllamaRespuesta {
    int es_ok;
    char* respuesta;       // Texto de la respuesta (debe liberarse con ollama_libre_respuesta)
    char* error;           // Mensaje de error (parte de la misma asignación)
} OllamaRespuesta;

// ============================================================
// Funciones de ciclo de vida
// ============================================================

// Inicializa el subsistema de red (Winsock en Windows)
void ollama_inicializar_red(void);

// Crea un cliente Ollama conectado a host:puerto con el modelo especificado
OllamaCliente* ollama_cliente_crear(const char* host, int puerto, const char* modelo);

// Destruye un cliente y libera sus recursos
void ollama_cliente_destruir(OllamaCliente* cliente);

// ============================================================
// Funciones de inferencia
// ============================================================

// Genera una respuesta para el prompt dado
// Retorna una estructura OllamaRespuesta con la respuesta o error
OllamaRespuesta ollama_generar(OllamaCliente* cliente, const char* prompt);

// ============================================================
// Funciones de limpieza
// ============================================================

// Libera la memoria de una respuesta Ollama
void ollama_libre_respuesta(OllamaRespuesta* resp);

#ifdef __cplusplus
}
#endif

#endif // OLLAMA_CLIENT_H
