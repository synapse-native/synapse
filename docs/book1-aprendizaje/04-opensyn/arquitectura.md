# Arquitectura Local de OpenSyn

Este capítulo describe la arquitectura interna de OpenSyn, el asistente de desarrollo con IA del ecosistema Synapse. Aprenderás sobre los componentes principales, el flujo de datos y cómo OpenSyn procesa las solicitudes del usuario.

OpenSyn está diseñado para integrarse de forma transparente en tu flujo de trabajo, potenciando tu productividad con inteligencia artificial.

<!-- cumple Manual 7 §2 -->

## 1. Componentes Principales

OpenSyn se compone de varios módulos interconectados que trabajan juntos para proporcionar asistencia de IA:

### 1.1. Orquestador (`orchestrator.c`)

El orquestador es un proceso en C que gestiona el ciclo de vida del servidor de inferencia (`llama-server`).

**Funcionalidades:**
- **Inicio:** Verifica si `llama-server` está ejecutándose en el puerto configurado (8088 por defecto). Si no, lo inicia con los parámetros adecuados.
- **Monitoreo:** Comprueba periódicamente que el servidor está activo (heartbeat). Si falla, lo reinicia.
- **Apagado:** Cuando el editor se cierra, envía una señal de terminación al servidor.
- **Recuperación:** Si el servidor falla, se reinicia automáticamente.

**Configuración (`OrchestratorConfig`):**

```c
typedef struct {
    char* model_path;      // Ruta al modelo GGUF
    int port;              // Puerto del servidor (8088 por defecto)
    int n_threads;         // Número de hilos de CPU
    int n_gpu_layers;      // Capas a cargar en GPU
    int n_ctx;             // Tamaño de contexto (tokens)
    int batch_size;        // Tamaño de lote para inferencia
    float temperature;     // Temperatura por defecto (0.3)
    pid_t server_pid;      // PID del proceso llama-server
} OrchestratorConfig;
```

### 1.2. Cliente HTTP (`llama_client.c`)

El cliente HTTP envía prompts al servidor de inferencia y recibe respuestas.

**API C:**
```c
typedef struct {
    char* host;            // "127.0.0.1"
    int port;              // 8088
    int timeout_seconds;   // 30
    bool connected;
} LlamaClient;
```

**Flujo de `llama_client_completion`:**
1. Construir el JSON de la petición con `prompt`, `temperature`, `max_tokens`, `stop`
2. Enviar POST a `http://127.0.0.1:8088/completion`
3. Esperar respuesta con timeout
4. Extraer el campo `content` de la respuesta JSON

### 1.3. Pipeline RAG (`synapse_rag.c`)

El pipeline RAG es el cerebro de OpenSyn. Extrae contexto relevante del código fuente para construir un prompt eficiente.

**Flujo de Procesamiento:**
1. **Obtener contexto del LSP:** nodo AST, líneas circundantes, diagnósticos, metadatos
2. **Extraer información del AST:** nombres, tipos, comentarios, estructura de control
3. **Construir prompt con contexto estático:** inyección de reglas de Synapse/Syquex
4. **Negociación de n_ctx:** 30% para el prompt, 70% para generación
5. **Invocación del modelo:** temperature=0.3, stop=["```", "\n\n"]
6. **Procesamiento de respuesta:** extraer código, validar, mostrar al usuario

### 1.4. Enrutador (`router.syn`)

El router está escrito en Synapse y decide qué modelo usar y cómo procesar la respuesta.

**Funcionalidades:**
- **Selección de modelo:** según la instrucción del usuario
- **Formateo de respuesta:** extrae código entre bloques ``````
- **Manejo de errores:** si el código es inválido, solicita corrección

### 1.5. Instalador (`installer.syn`)

El instalador detecta hardware, selecciona y descarga el modelo apropiado.

**Flujo:**
1. Detección de hardware (RAM, VRAM, CPU, OS)
2. Selección de modelo según VRAM disponible
3. Descarga del modelo con verificación SHA-256
4. Configuración de llama-server
5. Prueba de humo

## 2. Arquitectura de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                       ARQUITECTURA OPENSYN                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    ORQUESTADOR (orchestrator.c)             │   │
│  │  - Ciclo de vida de llama-server                           │   │
│  │  - Shutdown hooks (atexit, señales)                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                CLIENTE HTTP (llama_client.c)                │   │
│  │  - Envío de prompts a /completion                          │   │
│  │  - Manejo de timeouts, reintentos                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  PIPELINE RAG (synapse_rag.c)               │   │
│  │  - Extracción de contexto (AST, líneas circundantes)       │   │
│  │  - Inyección de contexto estático                          │   │
│  │  - Construcción de prompt                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              ENRUTADOR (router.syn)                         │   │
│  │  - Decidir qué modelo usar                                 │   │
│  │  - Formatear la respuesta                                  │   │
│  │  - Iniciar el bucle de corrección                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │               INSTALADOR (installer.syn)                    │   │
│  │  - Detección de hardware                                   │   │
│  │  - Selección de modelo                                     │   │
│  │  - Descarga y verificación                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 3. Comunicación entre Componentes

### Protocolo Socket Local

El LSP se comunica con el orquestador mediante un socket local:
- **Address:** `localhost:8088` (configurable)
- **Protocolo:** JSON sobre TCP
- **Mensajes:** Solicitudes de generación, respuestas con código y metadatos

### Estructura de Mensajes

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "synapse/aiComplete",
  "params": {
    "textDocument": { "uri": "file:///proyecto/main.syq" },
    "position": { "line": 5, "character": 10 },
    "context": "codigo circundante"
  }
}
```

## 4. Integración con el LSP

OpenSyn se integra profundamente con el Language Server Protocol:

| Comando LSP | Descripción |
|-------------|-------------|
| `synapse/aiStatus` | Estado del servidor de inferencia |
| `synapse/aiExplain` | Explicar código seleccionado |
| `synapse/aiComplete` | Completar código |
| `synapse/aiFix` | Sugerir correcciones |
| `synapse/aiTranspile` | Transpilar entre lenguajes |
| `synapse/aiBindings` | Generar bindings C → Syquex |

## 5. Seguridad y Privacidad

- **Cero telemetría:** No se envía ningún dato a servidores externos
- **Modelos locales:** Todo procesamiento ocurre en el hardware del usuario
- **Verificación de integridad:** Modelos descargados verificados con SHA-256
- **Sandboxing:** El servidor de inferencia corre con permisos mínimos

## Referencias

- **Manual 7 §2.1-2.5**: Componentes detallados del orquestador, cliente HTTP, RAG, router e instalador
- **Manual 7 §6.1**: Instalación de un solo clic
- **Manual 8 §4**: Sistema de comandos del LSP

// cumple Manual 7 §2
