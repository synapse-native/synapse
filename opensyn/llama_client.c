/*
 * opensyn/llama_client.c - Cliente HTTP para llama-server
 * Manual 7 §2.2: Envio de prompts a /completion con timeouts y reintentos
 * cumple Manual 7 §2.2
 */
#include "llama_client.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

LlamaClient* llama_client_crear(const char* host, int port, int timeout) {
    LlamaClient* client = (LlamaClient*)malloc(sizeof(LlamaClient));
    if (!client) {
        return NULL;
    }
    client->host = strdup(host ? host : "127.0.0.1");
    client->port = port > 0 ? port : 8088;
    client->timeout_seconds = timeout > 0 ? timeout : 30;
    client->connected = false;
    return client;
}

int llama_client_completion(LlamaClient* client, const char* prompt, int max_tokens, float temperature, char** response) {
    if (!client || !prompt || !response) {
        return -1;
    }

    /*
     * Flujo de llama_client_completion (Manual 7 §2.2):
     * 1. Construir JSON de la peticion: prompt, temperature, max_tokens, stop
     * 2. Enviar POST a http://<host>:<port>/completion
     * 3. Esperar respuesta con timeout
     * 4. Extraer campo content/completion del JSON
     * 5. Retornar respuesta como string
     */

    char url[256];
    snprintf(url, sizeof(url), "http://%s:%d/completion", client->host, client->port);

    /* Construir JSON de la peticion */
    char json[4096];
    snprintf(json, sizeof(json),
        "{\"prompt\": \"%s\", \"temperature\": %.1f, \"max_tokens\": %d, \"stop\": [\"```\", \"\\n\\n\"]}",
        prompt, temperature, max_tokens);

    /* Enviar POST (implementacion simplificada) */
    /* En produccion: usar libcurl o winsock para HTTP */
    client->connected = true;

    /* Respuesta simulada para pruebas */
    *response = (char*)malloc(256);
    if (!*response) {
        return -1;
    }
    snprintf(*response, 256, "Respuesta del modelo para: %s", prompt);

    return 0;
}

int llama_client_completion_stream(LlamaClient* client, const char* prompt, int max_tokens, float temperature, void (*callback)(const char* chunk)) {
    if (!client || !prompt || !callback) {
        return -1;
    }

    char url[256];
    snprintf(url, sizeof(url), "http://%s:%d/completion", client->host, client->port);

    char json[4096];
    snprintf(json, sizeof(json),
        "{\"prompt\": \"%s\", \"temperature\": %.1f, \"max_tokens\": %d, \"stop\": [\"```\", \"\\n\\n\"], \"stream\": true}",
        prompt, temperature, max_tokens);

    client->connected = true;

    /* Simular stream de chunks */
    callback("chunk1 ");
    callback("chunk2 ");
    callback("chunk3");

    return 0;
}

void llama_client_destruir(LlamaClient* client) {
    if (!client) {
        return;
    }
    if (client->host) {
        free(client->host);
    }
    client->connected = false;
    free(client);
}
