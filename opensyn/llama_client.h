/*
 * opensyn/llama_client.h - Cliente HTTP para llama-server
 * Manual 7 §2.2
 * cumple Manual 7 §2.2
 */
#ifndef LLAMA_CLIENT_H
#define LLAMA_CLIENT_H

#include <stdbool.h>

typedef struct {
    char* host;                 /* "127.0.0.1" */
    int port;                   /* 8088 */
    int timeout_seconds;        /* 30 */
    bool connected;
} LlamaClient;

LlamaClient* llama_client_crear(const char* host, int port, int timeout);
int llama_client_completion(LlamaClient* client, const char* prompt, int max_tokens, float temperature, char** response);
int llama_client_completion_stream(LlamaClient* client, const char* prompt, int max_tokens, float temperature, void (*callback)(const char* chunk));
void llama_client_destruir(LlamaClient* client);

#endif /* LLAMA_CLIENT_H */
