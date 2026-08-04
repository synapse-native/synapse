# MANUAL 7: OPENSYN – ASISTENTE DE IA LOCAL

**Archivo:** `07_OPENSYN_ASISTENTE_IA.md`  
**Versión:** 8.1.0-industrial  
**Propósito:** Especificar la arquitectura, funcionalidad e implementación de OpenSyn, el asistente de inteligencia artificial local del ecosistema Synapse. OpenSyn actúa como un «Copilot» para desarrolladores, proporcionando explicaciones de código, generación automática, autocompletado contextual, refactorización asistida, corrección de errores, transpilación entre lenguajes y generación automática de bindings a librerías C. Todo ello ejecutándose completamente local, sin telemetría y con total soberanía del usuario.

---

## 1. VISIÓN GENERAL DE OPENSYN

### 1.1. ¿Qué es OpenSyn?

OpenSyn es el **asistente de inteligencia artificial local** del ecosistema Synapse. Es el equivalente a un «Copilot» o «OpenCode» pero con las siguientes características distintivas:

- **Completamente local:** Los modelos se descargan y ejecutan en el hardware del usuario. No hay dependencia de la nube.
- **Multilenguaje:** Soporta Synapse, Syquex, Python, JavaScript, C, C++, Rust, Go, y más.
- **Aprendizaje de Synapse:** OpenSyn conoce Synapse y Syquex de forma nativa mediante **inyección de contexto estático** (ver sección 2.3) y, opcionalmente, mediante fine‑tuning.
- **Cero telemetría:** No envía datos a ningún servidor externo.
- **Integración profunda:** Se comunica con el LSP para acceder al AST, diagnósticos y contexto del código.
- **Transpilación:** Puede convertir código Python a Syquex, y código C a Synapse/Syquex.
- **Generación de bindings:** Puede leer cabeceras C y generar wrappers en Syquex automáticamente.
- **Fine‑tuning y adaptación:** Permite ajustar modelos con datos propios para mejorar la precisión en dominios específicos.
- **Instalación de un solo clic:** Detecta hardware, descarga el modelo adecuado y configura todo automáticamente.
- **Validación automática y bucle de corrección:** El código generado se valida con el compilador real; si falla, OpenSyn lo corrige hasta 3 veces (ver sección 6.3).

### 1.2. Público Objetivo

- Desarrolladores que quieren asistencia de código sin depender de la nube (privacidad, seguridad).
- Equipos que trabajan en entornos aislados (sin acceso a internet).
- Educadores y estudiantes que aprenden Synapse/Syquex.
- Empresas con políticas de datos estrictas (banca, salud, legal).
- Desarrolladores hispanohablantes (OpenSyn responde en español).

### 1.3. Diferencias con OpenCode / GitHub Copilot

| Característica | OpenCode / Copilot | OpenSyn |
|----------------|-------------------|---------|
| **Local / Nube** | Nube (depende de internet) | Local (sin dependencia de red) |
| **Telemetría** | Sí (datos de uso) | No |
| **Modelos** | Modelos propietarios | Modelos open‑source (CodeLlama, DeepSeek Coder) |
| **Fine‑tuning** | No (solo los modelos de la empresa) | Sí (el usuario puede fine‑tunear) |
| **Transpilación** | No | Sí (Python → Syquex, C → Synapse) |
| **Bindings automáticos** | No | Sí (C → Syquex) |
| **Idioma** | Inglés (principalmente) | Multilingüe (español, inglés, etc.) |
| **Costo** | Suscripción | Gratuito (con modelos open‑source) |
| **Validación de código** | No | Sí (compilador real, bucle de corrección) |

---

## 2. ARQUITECTURA DE OPENSYN

OpenSyn se compone de varios módulos interconectados, escritos en Synapse y C, que trabajan juntos para proporcionar la asistencia de IA.

```
┌─────────────────────────────────────────────────────────────────────┐
│                       ARQUITECTURA OPENSYN                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    ORQUESTADOR (orchestrator.c)             │   │
│  │  - Ciclo de vida de llama-server (inicio, monitoreo, apagado)│   │
│  │  - Shutdown hooks (atexit, señales)                         │   │
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
│  │  - Inyección de contexto estático (reglas de Synapse/Syquex)│   │
│  │  - Construcción de prompt (system + contexto + instrucción) │   │
│  │  - Gestión de n_ctx (30% contexto, 70% generación)         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              ENRUTADOR (router.syn)                         │   │
│  │  - Decidir qué modelo usar (codec, instruct, etc.)         │   │
│  │  - Formatear la respuesta (extraer código, etc.)           │   │
│  │  - Iniciar el bucle de corrección (si el código falla)    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │               INSTALADOR (installer.syn)                    │   │
│  │  - Detección de hardware (std.os)                          │   │
│  │  - Selección de modelo (Q4, Q5, según VRAM)                │   │
│  │  - Descarga y verificación (SHA‑256)                       │   │
│  │  - Configuración de llama-server                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1. Orquestador (`orchestrator.c`)

El orquestador es un proceso en C que gestiona el ciclo de vida del servidor de inferencia (`llama-server`). Se ejecuta en segundo plano y se comunica con el LSP mediante un socket local.

**Funcionalidades:**
- **Inicio:** Verifica si `llama-server` está ejecutándose en el puerto configurado (por defecto 8088). Si no, lo inicia con los parámetros adecuados.
- **Monitoreo:** Comprueba periódicamente que el servidor está vivo (heartbeat). Si falla, lo reinicia.
- **Apagado:** Cuando el editor se cierra (o el LSP termina), el orquestador envía una señal de terminación al servidor y espera su finalización (shutdown hooks).
- **Recuperación:** Si el servidor falla, se reinicia automáticamente con los mismos parámetros.

**Estructura de datos (C):**

```c
// opensyn/orchestrator.h
typedef struct {
    char* model_path;           // Ruta al modelo GGUF
    int port;                   // Puerto del servidor (8088 por defecto)
    int n_threads;              // Número de hilos de CPU
    int n_gpu_layers;           // Capas a cargar en GPU
    int n_ctx;                  // Tamaño de contexto (tokens)
    int batch_size;             // Tamaño de lote para inferencia
    float temperature;          // Temperatura por defecto (0.3)
    pid_t server_pid;           // PID del proceso llama-server
} OrchestratorConfig;

int orchestrator_iniciar(OrchestratorConfig* config);
int orchestrator_apagar();
int orchestrator_verificar_estado();
```

**Shutdown hooks (POSIX):**
```c
void shutdown_handler(int sig) {
    orchestrator_apagar();
    exit(0);
}

signal(SIGINT, shutdown_handler);
signal(SIGTERM, shutdown_handler);
```

**Shutdown hooks (Windows):**
```c
BOOL WINAPI ConsoleHandler(DWORD dwCtrlType) {
    orchestrator_apagar();
    return TRUE;
}
```

### 2.2. Cliente HTTP (`llama_client.c`)

El cliente HTTP se encarga de enviar prompts al servidor de inferencia y recibir respuestas. Soporta timeouts, reintentos y manejo de errores.

**API:**
```c
// opensyn/llama_client.h
typedef struct {
    char* host;                 // "127.0.0.1"
    int port;                   // 8088
    int timeout_seconds;        // 30
    bool connected;
} LlamaClient;

LlamaClient* llama_client_crear(const char* host, int port, int timeout);
int llama_client_completion(LlamaClient* client, const char* prompt, int max_tokens, float temperature, char** response);
int llama_client_completion_stream(LlamaClient* client, const char* prompt, int max_tokens, float temperature, void (*callback)(const char* chunk));
void llama_client_destruir(LlamaClient* client);
```

**Flujo de `llama_client_completion`:**
1. Construir el JSON de la petición:
   ```json
   {
     "prompt": "...",
     "temperature": 0.3,
     "max_tokens": 2048,
     "stop": ["```", "\n\n"]
   }
   ```
2. Enviar un POST a `http://127.0.0.1:8088/completion` con el JSON.
3. Esperar la respuesta (con timeout).
4. Extraer el campo `content` o `completion` de la respuesta JSON.
5. Retornar la respuesta como string.

### 2.3. Pipeline RAG (`synapse_rag.c`)

El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn. Extrae el contexto más relevante del código fuente para construir un prompt eficiente y preciso.

**Flujo:**

1. **Obtener contexto del LSP:** El LSP envía al RAG:
   - El nodo AST actual (función, estructura, bloque, etc.).
   - Las líneas de código alrededor del cursor (5 antes, 5 después).
   - Los diagnósticos activos (errores, warnings) para ese fragmento.
   - Metadatos: archivo, línea, columna, idioma (`#lang:`), versión del compilador.

2. **Extraer información del AST:** El RAG recorre el AST y extrae:
   - Nombres de funciones y variables.
   - Tipos de datos.
   - Comentarios cercanos.
   - Estructura del control de flujo.

3. **Construir el prompt con inyección de contexto estático:**  
   OpenSyn **no** necesita un modelo fine‑tuneado. En su lugar, inyecta un bloque de "Reglas de Sintaxis" en el **System Prompt** de cada consulta. Este bloque contiene la gramática esencial, el modelo de memoria y ejemplos de Synapse/Syquex. El prompt se genera con la siguiente plantilla (en el idioma del usuario):

```
[SYSTEM]
Eres un experto en programación. Conoces Python, JavaScript, C, Rust y otros lenguajes.
Ahora te voy a enseñar dos lenguajes nuevos: **Synapse** (bajo nivel, sistemas) y **Syquex** (alto nivel, productividad).

# REGLAS DE SYNAPSE (Sintaxis Estricta)
- Funciones: `funcion nombre(parametros) -> tipo:`
- Variables: `let nombre = valor`
- Condicional: `si condicion:`
- Bucle: `mientras condicion:`
- Retorno con transferencia de ownership (move): `retornar -> variable`
- Concurrencia: `lanzar funcion()`
- Canales: `Canal<T>` y `canal <- valor`, `valor = canal ->`
- Tensores: `tensor(filas, columnas)`
- Ejemplo: `funcion sumar(a: int, b: int) -> int: retornar a + b`

# REGLAS DE SYQUEX (Sintaxis Flexible y Automática)
- Funciones: `funcion nombre(parametros) -> tipo:`
- Estructuras: `estructura Nombre: campo: tipo`
- Métodos: `metodo nombre(parametros) -> tipo:`
- Constructores: `crear(parametros):`
- Manejo de Errores: `Resultado<T, E>` y operador `?` (propaga errores).
- Concurrencia: `lanzar funcion()`
- Canales: `Canal<T>(capacidad)`
- Importar módulos: `importar lib.modulo`
- Ejemplo: `funcion saludar(nombre: texto) -> texto: retornar "Hola, " + nombre`

Ahora, responde a la siguiente instrucción en el lenguaje que te pida (Synapse o Syquex). Genera SOLO el código, sin explicaciones adicionales.

[CONTEXT]
Archivo: {archivo}
Idioma: {idioma}
Líneas: {linea_inicio} a {linea_fin}

```{idioma}
{lineas_codigo}
```

Diagnósticos activos:
{diagnosticos}

[INSTRUCCIÓN]
{instruccion_usuario}
```

4. **Negociación de n_ctx:** El RAG lee el `n_ctx` del modelo (por defecto 4096). Reserva el 30% para el prompt y el 70% para la generación. Si el prompt excede el 30%, se trunca priorizando:
   - Las líneas más cercanas al cursor.
   - Los diagnósticos más relevantes (errores sobre warnings).
   - El nodo AST actual sobre el código circundante.

5. **Invocación del modelo:** El prompt se envía al cliente HTTP (`llama_client.c`). Los parámetros de generación son:
   - `temperature`: 0.3 (determinista, pero con cierta creatividad).
   - `max_tokens`: `clamp(n_ctx * 0.7, 64, 2048)`.
   - `stop`: `["```", "\n\n"]`.

6. **Procesamiento de la respuesta:** El router (ver sección 2.4) procesa la respuesta para extraer el código (si lo hay), validarlo con el compilador, y mostrarlo al usuario.

**Estructura de datos (C):**

```c
// opensyn/synapse_rag.h
typedef struct {
    char* archivo;
    char* contenido;                // Líneas extraídas (texto)
    int linea_inicio;
    int linea_fin;
    char* nodo_ast;                 // Representación JSON del AST
    char** diagnosticos;
    int num_diagnosticos;
    char* idioma;                   // "es", "en", "fr", "pt"
    char* instruccion;              // "Explica", "Completa", "Corrige", etc.
} RagContext;

typedef struct {
    char* prompt_completo;
    size_t prompt_tokens;
    size_t max_prompt_tokens;       // 30% de n_ctx
    size_t max_generation_tokens;   // 70% de n_ctx
} PromptInfo;

PromptInfo rag_construir_prompt(RagContext* ctx, int n_ctx);
char* rag_extraer_codigo(const char* respuesta);
int rag_validar_codigo(const char* codigo, const char* idioma);  // Usa el compilador para validar
```

### 2.4. Enrutador (`router.syn`)

El router está escrito en Synapse y actúa como el cerebro de alto nivel de OpenSyn. Decide qué modelo usar y cómo procesar la respuesta.

**Funcionalidades:**
- **Selección de modelo:** Si el usuario tiene múltiples modelos (ej. uno para código, uno para chat), el router decide cuál usar según la instrucción.
- **Formateo de respuesta:** Extrae el código de la respuesta del modelo (usando expresiones regulares o parseo de bloques), lo valida con el compilador, y lo muestra.
- **Manejo de errores:** Si el modelo genera código inválido, el router puede pedirle que lo corrija (modo auto‑recuperación).

**Ejemplo de router en Synapse:**
```synapse
// opensyn/router.syn
importar std.io
importar std.json
importar std.regex

funcion procesar_respuesta(respuesta_json: texto) -> Resultado<RespuestaProcesada, texto>:
    let datos = json.parsear(respuesta_json)?
    let contenido = datos.content
    
    // Extraer bloques de código entre ```synapse``` o ```syquex```
    let bloques = regex.buscar("```(synapse|syquex)\\n(.*?)\\n```", contenido)
    si bloques.len() == 0:
        // No hay código, retornar solo el texto
        retornar ok(RespuestaProcesada(texto: contenido, codigo: nulo))
    sino:
        // Validar el primer bloque de código con el compilador
        let codigo = bloques[0].grupo(2)
        let idioma = bloques[0].grupo(1)
        let es_valido = validar_codigo(codigo, idioma)
        si no es_valido:
            // Si el código es inválido, pedir corrección
            retornar err("El código generado no es válido en " + idioma)
        retornar ok(RespuestaProcesada(texto: contenido, codigo: codigo))
```

### 2.5. Instalador (`installer.syn`)

El instalador de OpenSyn es un script en Synapse que se ejecuta la primera vez que el usuario activa OpenSyn. Detecta hardware, selecciona y descarga el modelo apropiado.

**Flujo:**
1. **Detección de hardware:** Usa `std.os` para obtener:
   - RAM total y libre.
   - VRAM total y disponible (GPU NVIDIA, AMD, Apple).
   - Número de núcleos de CPU.
   - Sistema operativo y arquitectura.

2. **Selección de modelo:** Según la VRAM disponible, selecciona una cuantización:
   - `< 4 GB` → `deepseek-coder-1.3b-Q4_K_M.gguf` (~1 GB)
   - `4-6 GB` → `codellama-7b-Q4_K_M.gguf` (~4 GB)
   - `6-8 GB` → `codellama-7b-Q5_K_M.gguf` (~5 GB)
   - `8-12 GB` → `codellama-13b-Q4_K_M.gguf` (~7 GB)
   - `> 12 GB` → `codellama-34b-Q4_K_M.gguf` (~18 GB)

3. **Descarga del modelo:** Descarga el modelo desde Hugging Face o Axon Hub, verificando su integridad mediante SHA‑256.

4. **Configuración:** Escribe un archivo `~/.opensyn/config.toml` con la ruta del modelo, número de hilos, capas GPU, tamaño de contexto, etc.

5. **Prueba de humo:** Ejecuta una inferencia simple (ej. "Di hola") para verificar que todo funciona.

```synapse
// opensyn/installer.syn
importar std.os
importar std.net
importar std.io
importar std.hash

funcion detectar_hardware() -> HardwareInfo:
    retornar HardwareInfo(
        ram_total: os.memoria_total(),
        vram_total: os.vram_total(),
        cpu_nucleos: os.cpu_nucleos(),
        arquitectura: os.arquitectura()
    )

funcion seleccionar_modelo(hw: HardwareInfo) -> ModeloInfo:
    si hw.vram_total < 4 * 1024 * 1024 * 1024:
        retornar ModeloInfo(nombre: "deepseek-coder-1.3b-Q4_K_M", url: "...", sha256: "...", tamano: 1.1)
    si hw.vram_total < 6 * 1024 * 1024 * 1024:
        retornar ModeloInfo(nombre: "codellama-7b-Q4_K_M", url: "...", sha256: "...", tamano: 4.0)
    // ... más casos

funcion descargar_modelo(info: ModeloInfo) -> Resultado<texto, texto>:
    let ruta = os.home() + "/.opensyn/models/" + info.nombre + ".gguf"
    si os.existe_archivo(ruta):
        let hash = hash.sha256_archivo(ruta)
        si hash == info.sha256:
            io.escribir_linea("Modelo ya descargado y verificado")
            retornar ok(ruta)
    // Descargar
    io.escribir_linea("Descargando modelo (", info.tamano, " GB)...")
    net.descargar(info.url, ruta)?
    // Verificar
    let hash = hash.sha256_archivo(ruta)
    si hash != info.sha256:
        os.eliminar(ruta)
        retornar err("Checksum incorrecto")
    retornar ok(ruta)

funcion principal() -> Resultado<nulo, texto>:
    let hw = detectar_hardware()
    let modelo = seleccionar_modelo(hw)
    let ruta_modelo = descargar_modelo(modelo)?
    // Configurar llama-server
    configurar_servidor(ruta_modelo, hw)
    io.escribir_linea("✅ OpenSyn instalado correctamente")
    retornar ok()
```

---

## 3. MODELOS DE IA Y GESTIÓN

### 3.1. Modelos Soportados

OpenSyn soporta modelos en formato **GGUF** (cuantizados) de las siguientes familias:

| Modelo | Tamaño | Cuantización | VRAM necesaria | Bueno para |
|--------|--------|--------------|----------------|------------|
| DeepSeek Coder 1.3B | 1.3B | Q4_K_M | < 4 GB | Código básico, autocompletado |
| CodeLlama 7B | 7B | Q4_K_M | 4‑6 GB | Código general, explicaciones |
| CodeLlama 7B | 7B | Q5_K_M | 6‑8 GB | Código de alta calidad |
| CodeLlama 13B | 13B | Q4_K_M | 8‑12 GB | Código complejo, razonamiento |
| CodeLlama 34B | 34B | Q4_K_M | 12‑18 GB | Tareas avanzadas, depuración |
| Synapse‑Fine‑tuned | 7B | Q4_K_M | 4‑6 GB | Especializado en Synapse/Syquex (opcional) |

### 3.2. Fine‑tuning y Adaptación

OpenSyn permite fine‑tunar modelos con datos propios para mejorar la precisión en dominios específicos (ej. código de una empresa). El fine‑tuning utiliza **LoRA** (Low‑Rank Adaptation), que es eficiente en memoria. Sin embargo, **no es necesario para el funcionamiento básico**: el sistema de inyección de contexto estático (sección 2.3) ya proporciona un conocimiento suficiente para la mayoría de los casos.

**Estructura de datos para LoRA (C):**

```c
// opensyn/fine_tuning.h
typedef struct {
    float** lora_a;     // Matrices A (rank r)
    float** lora_b;     // Matrices B (rank r)
    int rank;           // Rango de LoRA (típicamente 4, 8, 16)
    int num_layers;     // Número de capas a adaptar
} LoRALayer;

typedef struct {
    LoRALayer* layers;
    int num_layers;
    float learning_rate;
    int epochs;
    float lora_alpha;   // Factor de escala (típicamente 16)
} LoRAConfig;

LoRALayer* lora_init(float** base_weights, int num_layers, int rank, float alpha);
void lora_forward(LoRALayer* layer, float* input, float* output);
void lora_update(LoRALayer* layer, float* gradient, float lr);
```

**Dataset de fine‑tuning:** El dataset se compone de pares `(instrucción, salida)` extraídos de:
- Código fuente de la biblioteca estándar (`std/*.syn`, `lib/*.syq`).
- Ejemplos de la carpeta `examples/`.
- Documentación de los manuales.
- Correcciones de errores comunes (feedback de usuarios).

**Formato del dataset (JSONL):**
```json
{"instruction": "Escribe una función en Synapse que sume dos números.", "output": "funcion sumar(a: int, b: int) -> int:\n    retornar a + b"}
{"instruction": "Define una estructura 'Persona' con nombre y edad en Syquex.", "output": "estructura Persona:\n    nombre: texto\n    edad: entero\n    crear(nombre, edad):\n        self.nombre = nombre\n        self.edad = edad"}
```

**Pipeline de fine‑tuning:**
1. Cargar el modelo base (ej. CodeLlama 7B GGUF).
2. Inicializar LoRA con un rango `r=8` y `alpha=16`.
3. Iterar sobre el dataset durante 3 épocas.
4. Actualizar solo las matrices LoRA (el modelo base permanece congelado).
5. Guardar las matrices LoRA en un archivo `.lora`.
6. Para inferencia, cargar el modelo base y las matrices LoRA, y combinarlas en tiempo de ejecución.

### 3.3. Cuantización de Modelos

OpenSyn utiliza cuantización para reducir el tamaño de los modelos y acelerar la inferencia. Los niveles soportados son:

| Nivel | Precisión | Tamaño relativo | Calidad | Recomendado para |
|-------|-----------|-----------------|---------|------------------|
| Q2_K | 2 bits | 10% | Baja | Hardware muy limitado |
| Q3_K | 3 bits | 15% | Media‑baja | RAM < 4 GB |
| Q4_K_M | 4 bits | 25% | Media‑alta | 4‑8 GB VRAM |
| Q5_K_M | 5 bits | 30% | Alta | 8‑12 GB VRAM |
| Q6_K | 6 bits | 35% | Muy alta | 12‑16 GB VRAM |
| FP16 | 16 bits | 100% | Original | GPU de alta gama |

**Implementación en C:**
```c
// opensyn/quantization.h
int quantize_model(const char* input_path, const char* output_path, int quant_type);
```

`quant_type` puede ser: `Q4_K_M`, `Q5_K_M`, `Q6_K`, etc. La función utiliza las funciones de `llama.cpp` para la cuantización.

---

## 4. INTEGRACIÓN CON EL LSP Y EL COMPILADOR

### 4.1. Comandos Personalizados del LSP

El LSP expone comandos personalizados que invocan OpenSyn:

| Comando | Descripción |
|---------|-------------|
| `synapse/aiStatus` | Devuelve el estado del servidor de inferencia (modelo cargado, uso de VRAM, etc.). |
| `synapse/aiExplain` | Explica el código seleccionado o bajo el cursor. |
| `synapse/aiComplete` | Completa el código que el usuario está escribiendo. |
| `synapse/aiFix` | Sugiere correcciones para errores de compilación. |
| `synapse/aiTranspile` | Transpila código Python a Syquex, o C a Synapse. |
| `synapse/aiBindings` | Genera bindings Syquex a partir de una cabecera C. |

**Esquemas JSON:**

**`synapse/aiExplain` (petición):**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "synapse/aiExplain",
  "params": {
    "textDocument": { "uri": "file:///proyecto/main.syq" },
    "position": { "line": 5, "character": 10 },
    "selection": null  // o un rango
  }
}
```

**`synapse/aiExplain` (respuesta):**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "explicacion": "Esta función calcula el factorial de n usando recursión...",
    "codigo_relacionado": null
  }
}
```

**`synapse/aiComplete` (petición):**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "synapse/aiComplete",
  "params": {
    "textDocument": { "uri": "file:///proyecto/main.syq" },
    "position": { "line": 8, "character": 4 },
    "context": "funcion factorial(n: entero) -> entero:\n    "
  }
}
```

**`synapse/aiComplete` (respuesta):**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "completions": [
      {
        "texto": "si n <= 1:\n    retornar 1\nsino:\n    retornar n * factorial(n - 1)",
        "tipo": "linea",
        "rango": { "start": { "line": 8, "character": 4 }, "end": { "line": 8, "character": 4 } }
      }
    ]
  }
}
```

**`synapse/aiFix` (petición):**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "synapse/aiFix",
  "params": {
    "textDocument": { "uri": "file:///proyecto/main.syq" },
    "diagnostic": {
      "code": "ERR_SEM_TIPO_INCOMPATIBLE",
      "message": "No se puede sumar texto y entero",
      "range": { "start": { "line": 3, "character": 8 }, "end": { "line": 3, "character": 15 } }
    }
  }
}
```

**`synapse/aiFix` (respuesta):**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "sugerencia": "Convierte el texto a entero usando 'texto_a_entero()'",
    "codigo_corregido": "resultado = texto_a_entero(\"42\") + 1"
  }
}
```

### 4.2. Flujo de una Petición de IA con Validación

El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3). No se limita a ser un proxy pasivo.

**Flujo completo:**

1. El usuario ejecuta un comando en VS Code (ej. "Explicar código" o "Completar código").
2. El cliente LSP envía una petición JSON‑RPC al LSP con el método correspondiente.
3. El LSP recibe la petición y la reenvía al orquestador de OpenSyn (via socket local en `localhost:8088` o similar).
4. El orquestador invoca el pipeline RAG (`synapse_rag.c`) para construir el prompt, incluyendo el contexto estático de reglas.
5. El prompt se envía al servidor de inferencia (`llama-server`) mediante el cliente HTTP (`llama_client.c`).
6. El servidor genera una respuesta.
7. La respuesta se procesa (router) para extraer el código (si lo hay).
8. **Validación (paso crítico):** El LSP toma el código generado y ejecuta el compilador de Synapse/Syquex en modo `--check` (solo validación, sin generar binario). Esto se hace mediante el CLI `synapse check --no-emit <archivo>`.
9. **Si compila:** El LSP devuelve el código al editor como sugerencia.
10. **Si falla:** El LSP captura el error (stderr del compilador) y repite el proceso (hasta 3 intentos), añadiendo el error al prompt para que OpenSyn lo corrija.
11. **Fallo definitivo:** Si después de 3 intentos el código no compila, el LSP devuelve el último código generado y los errores al editor, mostrando un mensaje de "No se pudo generar código válido automáticamente. Intenta ajustar la instrucción."

### 4.3. Manejo de Errores y Timeouts

- Si el servidor de inferencia no responde en 30 segundos, el LSP devuelve un error al usuario.
- Si el modelo no está cargado, el LSP devuelve un mensaje indicando que debe descargarse.
- Si el código generado es inválido y se agotan los intentos, el LSP muestra un mensaje y ofrece regenerar (o pedir ayuda al usuario).

---

## 5. GENERACIÓN DE BINDINGS Y TRANSPILACIÓN

### 5.1. Transpilación Python → Syquex

**Comando:**
```bash
opensyn ai transpile --from python script.py --to syquex
```

**Mapeo de conceptos Python → Syquex:**

| Python | Syquex |
|--------|--------|
| `def` | `funcion` |
| `class` | `estructura` |
| `self` | `self` |
| `__init__` | `crear` |
| `list` | `Lista` |
| `dict` | `Mapa` |
| `try/except` | `intentar/atrapar` o `Resultado` |
| `with` | `usar` (si existe) o `delegar` |
| `async/await` | `lanzar` + `escuchar` |
| `raise` | `retornar err(...)` |
| `return` | `retornar ok(...)` / `retornar` |

**Ejemplo de transpilación:**

**Python:**
```python
def procesar_datos(datos):
    resultado = []
    for item in datos:
        if item > 10:
            resultado.append(item * 2)
    return resultado
```

**Syquex generado:**
```syquex
funcion procesar_datos(datos: Lista<entero>) -> Lista<entero>:
    let resultado = Lista<entero>()
    para item en datos:
        si item > 10:
            resultado.agregar(item * 2)
    retornar resultado
```

### 5.2. Generación de Bindings C → Syquex

**Comando:**
```bash
opensyn ai bindings --header libcurl.h --output lib/curl.syq
```

**Ejemplo de cabecera C (`libcurl.h`):**
```c
typedef struct CURL CURL;
CURL* curl_easy_init();
void curl_easy_cleanup(CURL* curl);
CURLcode curl_easy_setopt(CURL* curl, CURLoption option, ...);
CURLcode curl_easy_perform(CURL* curl);
```

**Syquex generado (`lib/curl.syq`):**
```syquex
// Bindings generados automáticamente para libcurl
externo estructura CURL

externo funcion curl_easy_init() -> &CURL
externo funcion curl_easy_cleanup(curl: &CURL) -> nulo
externo funcion curl_easy_setopt(curl: &CURL, option: entero, ...) -> entero
externo funcion curl_easy_perform(curl: &CURL) -> entero

// Wrapper de alto nivel
funcion http_get(url: texto) -> Resultado<texto, texto>:
    let curl = curl_easy_init()
    si curl == nulo:
        retornar err("Error al inicializar libcurl")
    // Configurar opciones...
    let codigo = curl_easy_perform(curl)
    curl_easy_cleanup(curl)
    si codigo != 0:
        retornar err("Error en petición HTTP")
    // ... obtener respuesta (usando callback de escritura)
    retornar ok(respuesta)
```

### 5.3. Generación de Bindings para Otros Lenguajes

OpenSyn también genera bindings para Python, TypeScript, Java y otros lenguajes a partir de las exportaciones (`@export`).

**Ejemplo de `@export` en Syquex:**
```syquex
@export(python) funcion calcular_iva(monto: decimal, porcentaje: decimal) -> decimal
```

**Bindings Python generados:**
```python
import ctypes
import os

lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__), "libsynapse.so"))

calcular_iva = lib.calcular_iva
calcular_iva.argtypes = [ctypes.c_double, ctypes.c_double]
calcular_iva.restype = ctypes.c_double

def calcular_iva_python(monto, porcentaje):
    return calcular_iva(monto, porcentaje)
```

---

## 6. INSTALACIÓN Y CONFIGURACIÓN DE OPENSYN

### 6.1. Instalación de un solo clic

El instalador de OpenSyn es parte del instalador unificado del ecosistema (Manual 9). Pasos:

1. El usuario descarga el instalador desde GitHub Releases.
2. Ejecuta el instalador (en Windows, Linux o macOS).
3. El instalador pregunta: "¿Instalar solo Synapse o Synapse + OpenSyn?".
4. Si elige OpenSyn, se ejecuta `opensyn/installer.syn` que:
   - Detecta hardware.
   - Selecciona y descarga el modelo apropiado.
   - Configura el servidor de inferencia.
   - Instala la extensión VS Code (opcional).
5. Al finalizar, se ejecuta una prueba de humo.

### 6.2. Archivo de Configuración (`~/.opensyn/config.toml`)

```toml
[general]
idioma = "es"
editor = "vscode"

[modelo]
nombre = "codellama-7b-Q4_K_M"
ruta = "~/.opensyn/models/codellama-7b-Q4_K_M.gguf"
n_ctx = 4096
n_threads = 8
n_gpu_layers = 30

[server]
puerto = 8088
host = "127.0.0.1"
timeout = 30

[rag]
contexto_lineas = 5
max_prompt_tokens = 1200

[generacion]
temperature = 0.3
max_tokens = 2048
```

### 6.3. Bucle de Corrección Automática (3 Intentos)

Dado que OpenSyn no es perfecto y puede generar código con errores sintácticos o semánticos, se implementa un **bucle de validación y corrección automática** orquestado por el LSP (ver sección 4.2). Este bucle asegura que el código generado cumpla con las reglas del compilador.

**Flujo detallado:**

1. **Generación inicial (intento 1):** OpenSyn genera código basado en la instrucción y el contexto.
2. **Validación:** El LSP pasa el código al compilador de Synapse/Syquex en modo `--check` (solo validación, sin generar binario). Este modo es activado con el flag `--no-emit` (o similar) que debe estar implementado en el CLI de Synapse.
3. **Si compila:** Se muestra al usuario. Fin del proceso.
4. **Si falla:** El compilador devuelve el error exacto (línea, columna, mensaje) a través de su salida de error estándar. El LSP:
   - Construye un nuevo prompt añadiendo: *"El código anterior tiene el siguiente error: {mensaje_error}. Por favor, corrígelo."*
   - Reenvía el prompt a OpenSyn (intento 2).
5. **Repetición:** Se repiten los pasos 2 y 3 para el intento 2. Si vuelve a fallar, se hace un intento 3.
6. **Fallo definitivo:** Si el tercer intento falla, el LSP muestra el último código generado y los errores al usuario, con un mensaje: *"No se pudo generar código válido automáticamente. Intenta ajustar la instrucción o corrige manualmente."*

**Mecanismo de Feedback Humano:**
- Cuando el usuario corrige el código manualmente (después de un fallo), OpenSyn guarda el par `(instrucción, código_corregido)` en `~/.opensyn/feedback.jsonl`.
- Este archivo se utiliza para mejorar los ejemplos en el contexto estático (sección 2.3) en futuras versiones del instalador o mediante re‑entrenamiento opcional.

**Nota de implementación:** El flag `--check` debe ser añadido al CLI de Synapse (Fase 27 del roadmap) para permitir esta validación sin generar archivos `.o` o `.exe`, agilizando el proceso.

### 6.4. Comandos CLI de OpenSyn

| Comando | Descripción |
|---------|-------------|
| `opensyn status` | Muestra el estado de OpenSyn (modelo cargado, uso de VRAM). |
| `opensyn download <modelo>` | Descarga un modelo específico. |
| `opensyn finetune --dataset dataset.jsonl` | Fine‑tuna el modelo actual con un dataset. |
| `opensyn bindings --header header.h` | Genera bindings Syquex desde una cabecera C. |
| `opensyn transpile --from python script.py` | Transpila Python a Syquex. |

---

## 7. PRUEBAS Y VALIDACIÓN

### 7.1. Pruebas Unitarias

| Test | Comando | Criterio |
|------|---------|----------|
| Detección de hardware | `pytest tests/opensyn/test_detect_hardware.py -v` | 100% pass |
| Descarga de modelos | `pytest tests/opensyn/test_download.py -v` | 100% pass (con modelo de prueba) |
| Inferencia básica | `pytest tests/opensyn/test_inference.py -v` | Respuesta no vacía |
| Pipeline RAG (contexto estático) | `pytest tests/opensyn/test_rag.py -v` | Prompt incluye las reglas de Synapse/Syquex |
| Transpilación Python → Syquex | `pytest tests/opensyn/test_transpile.py -v` | Código generado compila |
| Bindings C → Syquex | `pytest tests/opensyn/test_bindings.py -v` | Bindings generados y compilan |
| Comandos LSP (aiExplain, aiComplete) | `pytest tests/integration/test_ai_commands.py -v` | 100% pass |
| Bucle de corrección (3 intentos) | `pytest tests/integration/test_ai_correction.py -v` | El código se corrige exitosamente en ≤3 intentos |

### 7.2. Pruebas de Rendimiento

- **Latencia de inferencia:** < 1s para prompts cortos (modelo 7B en GPU).
- **Throughput:** > 100 tokens/s en GPU.
- **Uso de VRAM:** < 6 GB para modelo 7B Q4_K_M.
- **Tiempo de instalación:** < 10 minutos (incluyendo descarga).

### 7.3. Pruebas de Privacidad y Seguridad

- **Cero telemetría:** Verificado con monitoreo de red (sin conexiones salientes).
- **Modelos firmados:** Todos los modelos descargados se verifican con SHA‑256.
- **Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos.

---

## 8. EJEMPLO COMPLETO DE FLUJO DE IA (CON VALIDACIÓN)

**Escenario:** El usuario está escribiendo una función en Syquex y pide que se complete una función de suma.

**Código actual (`main.syq`):**
```syquex
funcion sumar
```

**Acción:** El usuario ejecuta "Synapse: Generar código con IA" (solicita `aiComplete`).

**Flujo:**

1. El LSP envía una petición `synapse/aiComplete` con el contexto (el fragmento `funcion sumar`).
2. El pipeline RAG construye el prompt con:
   - System Prompt: las reglas de Synapse/Syquex (sección 2.3).
   - Contexto: el fragmento de código.
   - Instrucción: "Completa la función sumar en Syquex."
3. OpenSyn genera el código (intento 1):
   ```syquex
   funcion sumar(a: int, b: int) -> int:
       retornar a + b
   ```
4. El LSP valida con `synapse check --no-emit` (compila correctamente).
5. El LSP muestra el código al usuario.

**Segundo escenario:** El usuario pide una función más compleja y la IA genera código con un error.

**Código generado (intento 1):**
```syquex
funcion dividir(a: int, b: int) -> int:
    retornar a / b
```
**Validación:** El compilador falla porque no hay verificación de división por cero (error de tipo o contrato). El error: `ERR_SEM_TIPO_INCOMPATIBLE` o similar.

**Acción del LSP:** Captura el error, construye un nuevo prompt: *"El código anterior tiene el siguiente error: 'División por cero no manejada'. Por favor, corrígelo."* y envía a OpenSyn (intento 2).

**Código generado (intento 2):**
```syquex
funcion dividir(a: int, b: int) -> Resultado<int, texto>:
    si b == 0:
        retornar err("División por cero")
    retornar ok(a / b)
```
**Validación:** Compila correctamente. El LSP muestra el código.

---

## 9. SIGUIENTES PASOS

Con OpenSyn completamente especificado, el siguiente manual (Manual 8) se centrará en las **Herramientas de Desarrollo**: el LSP nativo, la extensión VS Code, el debugger y el CLI unificado. El Manual 8 debe actualizarse para reflejar la integración del bucle de corrección y el flag `--check` en el CLI.

---

*Este manual proporciona la especificación completa de OpenSyn, el asistente de IA local del ecosistema, incluyendo el sistema de inyección de contexto estático, el bucle de validación automática y la corrección de código. La implementación debe seguir estos lineamientos para garantizar una asistencia de código eficiente, precisa, privada y multilingüe.*

**Fin del Manual 7**