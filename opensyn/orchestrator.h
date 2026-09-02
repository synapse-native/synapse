/*
 * opensyn/orchestrator.h - Orquestador de ciclo de vida de llama-server
 * Manual 7 §2.1: Gestion del ciclo de vida del servidor de inferencia
 * cumple Manual 7 2.1
 * cumple Manual 7 2.2
 */
#ifndef ORCHESTRATOR_H
#define ORCHESTRATOR_H

#include <signal.h>

typedef struct {
    char* model_path;           /* Ruta al modelo GGUF */
    int port;                   /* Puerto del servidor (8088 por defecto) */
    int n_threads;              /* Numero de hilos de CPU */
    int n_gpu_layers;           /* Capas a cargar en GPU */
    int n_ctx;                  /* Tamano de contexto (tokens) */
    int batch_size;             /* Tamano de lote para inferencia */
    float temperature;          /* Temperatura por defecto (0.3) */
    pid_t server_pid;           /* PID del proceso llama-server */
} OrchestratorConfig;

int orquestrador_iniciar(OrchestratorConfig* config);
int orchestrator_apagar();
int orchestrator_verificar_estado();

/* Shutdown hooks POSIX */
void shutdown_handler(int sig);

/* Shutdown hooks Windows */
#ifdef _WIN32
#include <windows.h>
BOOL WINAPI ConsoleHandler(DWORD dwCtrlType);
#endif

#endif /* ORCHESTRATOR_H */
