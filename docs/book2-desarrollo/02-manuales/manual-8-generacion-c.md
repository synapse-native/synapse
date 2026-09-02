# MANUAL 8: HERRAMIENTAS DE DESARROLLO

**Archivo:** `08_HERRAMIENTAS_DESARROLLO.md`  
**Versión:** 8.2.0-industrial  
**Propósito:** Especificar el conjunto de herramientas de desarrollo del ecosistema Synapse/Syquex: el servidor LSP nativo (`synapse_lsp`), la extensión para VS Code, el debugger (time‑travel y reversible), el CLI unificado (`synapse`), y la integración con OpenSyn para asistencia de IA en el editor. Este manual cubre la experiencia de desarrollo completa, desde la edición de código hasta la depuración y despliegue, incluyendo el bucle de validación y corrección automática de código generado por IA.

---

## 1. ARQUITECTURA DEL LSP NATIVO

### 1.1. Visión General

El **Language Server Protocol (LSP)** es un binario independiente (`synapse_lsp.exe` en Windows, `synapse_lsp` en Unix) que se comunica con el editor a través de la entrada/salida estándar (`stdin`/`stdout`) usando **JSON‑RPC 2.0** con cabeceras `Content-Length`.

**Flujo de comunicación:**
```
Editor (VS Code)  →  STDIN  →  synapse_lsp.exe  →  STDOUT  →  Editor
```

El LSP es **nativo**, **sin telemetría** y **sin dependencias externas** (excepto el binario `synapse.exe` para compilar y analizar código). Soporta Synapse (`.syn`) y Syquex (`.syq`) de forma transparente.

### 1.2. Protocolo de Cabecera

El LSP lee cabeceras HTTP‑like de la entrada estándar. Cada mensaje comienza con una cabecera `Content-Length:` seguida del tamaño del cuerpo JSON.

```c
// nucleo/lsp.syn (extracto)
funcion leer_cabecera() -> entero:
    buffer = texto("")
    content_length = -1
    mientras verdadero:
        linea = leer_linea_stdin()
        si linea == "":
            romper
        si linea.comienza_con("Content-Length:"):
            content_length = entero(linea.despues_de(":"))
        si linea == "" o linea == "\r\n":
            romper
    retornar content_length
```

Si el LSP no puede leer una cabecera válida (ej. `Content-Length` ausente), emite un error y termina.

### 1.3. Ciclo de Vida del LSP

1. **Inicialización**: El editor envía `initialize` con las capacidades del cliente. El LSP responde con sus capacidades (soporte para Synapse, Syquex, OpenSyn, etc.).
2. **Confirmación**: `initialized` confirma que la negociación ha terminado.
3. **Apertura de documentos**: `textDocument/didOpen` notifica al LSP sobre un archivo abierto. El LSP analiza el archivo (usando el compilador) y envía diagnostics.
4. **Cambios**: `textDocument/didChange` notifica cambios incrementales o full. El LSP re‑analiza y actualiza diagnostics.
5. **Cierre**: `textDocument/didClose` limpia diagnostics y libera recursos.
6. **Solicitudes de usuario**: `textDocument/hover`, `textDocument/definition`, `textDocument/completion`, etc.
7. **Comandos IA**: `synapse/aiStatus`, `synapse/aiExplain`, `synapse/aiComplete`, `synapse/aiFix`, `synapse/aiTranspile`, `synapse/aiBindings`.
8. **Finalización**: el LSP se cierra cuando el editor cierra la conexión.

### 1.4. Métodos LSP Soportados

| Método | ID | Descripción |
|--------|----|-------------|
| `initialize` | ✅ | Negocia capacidades (idioma, características). |
| `initialized` | ✅ | Confirmación de inicialización. |
| `textDocument/didOpen` | ✅ | Envía diagnostics al abrir un archivo. |
| `textDocument/didChange` | ✅ | Re‑analiza en cada cambio (full o incremental). |
| `textDocument/didClose` | ✅ | Limpia diagnostics. |
| `textDocument/hover` | ✅ | Muestra información sobre el símbolo bajo el cursor. |
| `textDocument/definition` | ✅ | Navega a la definición del símbolo. |
| `textDocument/completion` | ✅ | Autocompletado de símbolos y palabras clave. |
| `textDocument/codeAction` | ✅ | Sugiere correcciones rápidas (refactorización). |
| `textDocument/formatting` | ✅ | Formatea el código según las reglas de estilo. |
| `textDocument/signatureHelp` | ✅ | Muestra la firma de la función mientras se escribe. |
| `workspace/didChangeConfiguration` | ✅ | Cambia la configuración del LSP (ej. idioma, flags). |
| `synapse/aiStatus` | ✅ | Extensión: estado de IA local (modelo cargado, uso de recursos). |
| `synapse/aiExplain` | ✅ | Extensión: explica el código seleccionado. |
| `synapse/aiComplete` | ✅ | Extensión: genera código basado en el contexto. |
| `synapse/aiFix` | ✅ | Extensión: sugiere correcciones para errores. |
| `synapse/aiTranspile` | ✅ | Extensión: transpila código Python a Syquex, o C a Synapse. |
| `synapse/aiBindings` | ✅ | Extensión: genera bindings Syquex desde cabecera C. |

### 1.5. Mapeo de Coordenadas

Synapse/Syquex internamente usan **líneas 1‑based** y **columnas 0‑based**. El protocolo LSP exige líneas 0‑based y columnas 0‑based.

```
lsp_line = synapse_line - 1
lsp_character = synapse_columna
```

### 1.6. Formato de Diagnostics

Cada diagnostic incluye:

```json
{
  "range": {
    "start": { "line": 4, "character": 10 },
    "end": { "line": 4, "character": 11 }
  },
  "severity": 1,           // 1: Error, 2: Warning, 3: Info, 4: Hint
  "code": "ERR_SEM_VAR_NO_DECLARADA",
  "source": "synapse",
  "message": "Variable 'x' no declarada en este ámbito.",
  "relatedInformation": [] // Opcional
}
```

**Manejo de errores de sintaxis:** El LSP nunca debe llamar a `exit()` en caso de error de sintaxis. Captura, formatea y envía diagnostics. Si el parser encuentra errores, el LSP:
1. Captura el error y lo convierte en un diagnostic.
2. No interrumpe el análisis; intenta sincronizar y continuar.
3. Envía todos los diagnostics acumulados al editor.

### 1.7. Funciones de utilidad para el LSP

El LSP requiere manipulación de cadenas (parsing de JSON, construcción de respuestas) y lectura binaria de stdin. Para ello, se especifican las siguientes funciones:

#### 1.7.1. Lectura binaria de stdin

El protocolo LSP exige leer **exactamente N bytes** del cuerpo del mensaje, independientemente de que contenga `\n`. La función `leer_linea()` (que lee hasta `\n`) es insuficiente y rompe el parsing de JSON.

```synapse
// nucleo/lsp.syn
funcion leer_bytes(cantidad: entero) -> Resultado<texto, texto>:
    // Lee exactamente 'cantidad' bytes desde stdin.
    // Retorna ok(texto) con los bytes leídos, o err("EOF") si no hay suficientes datos.
    let buffer = reserva(cantidad + 1)
    let leidos = 0
    mientras leidos < cantidad:
        let leido = externo fread(buffer + leidos, 1, cantidad - leidos, stdin)
        si leido <= 0:
            liberar(buffer)
            retornar err("EOF")
        leidos = leidos + leido
    buffer[cantidad] = '\0'
    retornar ok(texto_desde_c(buffer))
```

**Flujo de lectura de un mensaje LSP (actualizado):**

```synapse
// nucleo/lsp.syn
funcion leer_mensaje_lsp() -> Resultado<texto, texto>:
    let content_length = -1
    mientras verdadero:
        let linea = leer_linea_stdin()
        si linea == "":
            romper
        si linea.comienza_con("Content-Length:"):
            content_length = entero(linea.despues_de(":"))
    si content_length <= 0:
        retornar err("Content-Length inválido")
    let cuerpo = leer_bytes(content_length)?
    retornar ok(cuerpo)
```

#### 1.7.2. Construcción de JSON sin `snprintf`

Synapse no tiene `snprintf` nativo. Para construir respuestas JSON dinámicas, se usa un **String Builder** basado en el tipo `texto` y el operador de concatenación `+`, junto con `a_texto()` para convertir números.

```synapse
// nucleo/lsp.syn
funcion construir_respuesta_json(id: entero, resultado: texto) -> texto:
    let json = "{\"jsonrpc\":\"2.0\",\"id\":" + a_texto(id) + ",\"result\":" + resultado + "}"
    retornar json

funcion construir_error_json(id: entero, codigo: entero, mensaje: texto) -> texto:
    let json = "{\"jsonrpc\":\"2.0\",\"id\":" + a_texto(id) + ",\"error\":{\"code\":" + a_texto(codigo) + ",\"message\":\"" + mensaje + "\"}}"
    retornar json
```

**Nota de seguridad:** Los strings JSON deben escaparse para evitar inyección. Se añade `escapar_json(texto) -> texto` que reemplaza `"` por `\"` y `\` por `\\`.

#### 1.7.3. Funciones de string (contiene, índice, reemplazar)

Las funciones `contiene`, `indice_de` y `reemplazar` se implementan como builtins en C y se exponen en Synapse:

**Runtime C (`runtime/core/string_utils.c`):**

| Función | Propósito |
|---------|-----------|
| `string_contiene(texto, subcadena) -> entero` | Verifica si una cadena contiene otra |
| `string_indice_de(texto, subcadena) -> entero` | Retorna la posición de la primera ocurrencia, o -1 |
| `string_reemplazar(texto, buscar, reemplazar) -> texto` | Reemplaza todas las ocurrencias |

**Bindings en Synapse:**

```synapse
// std/texto.syn
externo funcion contiene(texto: texto, subcadena: texto) -> entero
externo funcion indice_de(texto: texto, subcadena: texto) -> entero
externo funcion reemplazar(texto: texto, buscar: texto, reemplazar: texto) -> texto
```

#### 1.7.4. Resumen de funciones añadidas

| Función | Tipo | Archivo | Propósito |
|---------|------|---------|-----------|
| `leer_bytes(cantidad)` | Nueva | `nucleo/lsp.syn` | Lectura binaria exacta de stdin |
| `construir_respuesta_json(id, resultado)` | Nueva | `nucleo/lsp.syn` | Construcción de respuestas JSON-RPC |
| `construir_error_json(id, codigo, mensaje)` | Nueva | `nucleo/lsp.syn` | Construcción de errores JSON-RPC |
| `escapar_json(texto)` | Nueva | `nucleo/lsp.syn` | Escapado de strings JSON |
| `contiene(texto, subcadena)` | Builtin | `runtime/core/string_utils.c` | Verificación de subcadena |
| `indice_de(texto, subcadena)` | Builtin | `runtime/core/string_utils.c` | Búsqueda de primera ocurrencia |
| `reemplazar(texto, buscar, reemplazar)` | Builtin | `runtime/core/string_utils.c` | Reemplazo de todas las ocurrencias |

---

## 2. EXTENSIÓN VS CODE

### 2.1. Estructura de la Extensión

La extensión VS Code (`vscode-synapse`) es el cliente que conecta el editor con el LSP y proporciona la interfaz de usuario para OpenSyn.

```
vscode-synapse/
├── package.json          # Metadatos, comandos, dependencias
├── extension.js          # Punto de entrada (activación)
├── src/
│   ├── lsp_client.js     # Cliente LSP (JSON‑RPC sobre stdio)
│   ├── commands.js       # Comandos de la paleta
│   ├── ai_provider.js    # Integración con OpenSyn (IA)
│   └── status_bar.js     # Barra de estado (mostrar estado de la IA)
├── snippets/             # Snippets de código Synapse/Syquex
│   ├── synapse.json
│   └── syquex.json
└── syntaxes/             # Definición de sintaxis (TextMate)
    ├── synapse.tmLanguage.json
    └── syquex.tmLanguage.json
```

### 2.2. Activación y Detección del Binario

La extensión se activa cuando se abre un archivo `.syn` o `.syq`. Detecta el binario `synapse_lsp` en las siguientes ubicaciones (en orden):

1. `./node_modules/.bin/synapse_lsp`
2. `./nucleo/lsp_test.exe`
3. `./build/bin/synapse_lsp`
4. En el PATH del sistema (si `synapse` está instalado globalmente)

Si no se encuentra el binario, la extensión muestra un mensaje de error y ofrece descargarlo o instalarlo.

### 2.3. Comandos de la Paleta

La extensión registra los siguientes comandos:

- **Synapse: Verificar estado de IA local** → `synapse/aiStatus`
- **Synapse: Explicar código con IA local** → `synapse/aiExplain`
- **Synapse: Generar código con IA local** → `synapse/aiComplete`
- **Synapse: Corregir errores con IA** → `synapse/aiFix`
- **Synapse: Transpilar Python a Syquex** → `synapse/aiTranspile`
- **Synapse: Generar bindings C → Syquex** → `synapse/aiBindings`
- **Synapse: Formatear documento** → `synapse/format`
- **Synapse: Abrir documentación** → abre la documentación local o en línea.

### 2.4. Configuración

La extensión permite configurar:

```json
{
  "synapse.language": "es",            // Idioma de las palabras clave (es, en, fr, pt)
  "synapse.lsp.path": "",              // Ruta al binario LSP (override)
  "synapse.ai.enabled": true,          // Habilitar OpenSyn
  "synapse.ai.model": "codellama-7b-q4", // Nombre del modelo a usar
  "synapse.ai.serverPort": 8088,       // Puerto para llama-server
  "synapse.ai.maxTokens": 2048,        // Tokens máximos por respuesta
  "synapse.ai.temperature": 0.3,       // Temperatura de muestreo
  "synapse.ai.maxRetries": 3,          // Número máximo de intentos de corrección
  "synapse.debugger.enabled": true,    // Habilitar debugger
  "synapse.format.indentSize": 4,      // Tamaño de indentación
  "synapse.format.useTabs": false      // Usar tabs (false = espacios)
}
```

---

## 3. DEBUGGER (TIME‑TRAVEL Y REVERSIBLE)

### 3.1. Visión General

Synapse/Syquex incluye un debugger nativo que soporta **time‑travel debugging** (grabación y reproducción de la ejecución) y **breakpoints reversibles** (retroceder la ejecución). Esto es posible gracias al runtime determinista y al análisis de alcance.

**Características:**
- **Grabación de ejecución:** Registra el estado de las variables y el flujo de control.
- **Reversión:** Permite retroceder a un punto anterior de la ejecución.
- **Memory snapshots:** Captura el estado de la memoria en puntos específicos.
- **Breakpoints condicionales y reversibles.**
- **Integración con VS Code** (depuración visual).

### 3.2. Módulo `std.debug`

La biblioteca estándar proporciona un módulo `std.debug` para instrumentar código.

**Synapse:**
```synapse
importar std.debug

funcion principal() -> nulo:
    debug.iniciar_sesion()
    debug.marcar_punto("inicio")
    // Código...
    debug.marcar_punto("fin")
    debug.guardar_traza("ejecucion.trace")
```

**Syquex:**
```syquex
importar std.debug

funcion principal():
    debug.iniciar_sesion()
    debug.marcar_punto("inicio")
    // Código...
    debug.marcar_punto("fin")
    debug.guardar_traza("ejecucion.trace")
```

### 3.3. Estructura de Datos (C)

```c
// runtime/core/debug.h
#define MAX_EVENTOS 50000

typedef enum {
    DEBUG_EVENTO_LLAMADA,
    DEBUG_EVENTO_RETORNO,
    DEBUG_EVENTO_ASIGNACION,
    DEBUG_EVENTO_BREAKPOINT,
    DEBUG_EVENTO_SNAPSHOT
} DebugEvento;

typedef struct {
    DebugEvento tipo;
    int linea;
    char* archivo;
    char* funcion;
    void* contexto;         // Puntero al estado de la función
    size_t tamano_contexto;
    uint64_t timestamp;     // Ciclos de CPU
} DebugEvento;

typedef struct {
    DebugEvento* eventos;
    int num_eventos;
    int capacidad;
    bool grabando;
} DebugSesion;

typedef struct {
    void* memoria;
    size_t tamano;
    uint64_t timestamp;
} Snapshot;

void debug_iniciar_sesion();
void debug_marcar_punto(const char* nombre);
void debug_guardar_traza(const char* ruta);
void debug_cargar_traza(const char* ruta);
void debug_avanzar();
void debug_retroceder();
void debug_breakpoint(int linea);
```

### 3.4. Comandos del Debugger (CLI)

El CLI unificado (`synapse`) incluye comandos para depuración:

```bash
# Ejecutar con depuración
synapse run --debug programa.syq

# Cargar una traza guardada
synapse debug --load ejecucion.trace

# Avanzar un paso
synapse debug --step

# Retroceder un paso
synapse debug --reverse

# Ver snapshots
synapse debug --snapshots
```

### 3.5. Integración con VS Code

La extensión VS Code proporciona una interfaz visual para el debugger:

- **Controles:** Play, Pause, Step Forward, Step Backward, Restart.
- **Panel de variables:** Muestra el valor de las variables en el punto actual de la ejecución.
- **Línea de tiempo:** Visualización de la traza de ejecución (permite arrastrar a cualquier punto).
- **Breakpoints:** Click en el margen izquierdo del editor para establecer breakpoints.

---

## 4. CLI UNIFICADO (`synapse`)

El CLI unificado es el punto de entrada principal para todas las herramientas del ecosistema. Soporta Synapse, Syquex, Axon, OpenSyn y el debugger.

### 4.1. Comandos Principales

| Comando | Descripción |
|---------|-------------|
| `synapse build <archivo>` | Compila el archivo (`.syn` o `.syq`) a binario. |
| `synapse run <archivo>` | Ejecuta el archivo (modo interpretado o JIT para Syquex). |
| `synapse test` | Ejecuta la suite de pruebas del proyecto actual. |
| `synapse fetch` | Descarga dependencias (Axon). |
| `synapse opensyn <subcomando>` | Comandos de OpenSyn (status, download, finetune, bindings, transpile). |
| `synapse debug <subcomando>` | Comandos del debugger (load, step, reverse, snapshots). |
| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |
| `synapse init` | Crea un nuevo proyecto Synapse/Syquex (estructura básica). |

### 4.2. Flags Comunes

| Flag | Descripción |
|------|-------------|
| `--target` | `native`, `wasm`, `llvm` (por defecto `native`). |
| `--release` | Compila en modo release (optimizaciones). |
| `--debug` | Compila con información de depuración. |
| `--safe` | Activa verificación formal (ATP). |
| `--output` | Especifica el nombre del binario de salida. |
| `--verbose` | Muestra información detallada de la compilación. |
| **`--check`** / **`--no-emit`** | **Modo de validación:** Solo verifica la sintaxis y semántica, sin generar código de salida. Útil para el bucle de corrección de OpenSyn. |
| `--emit-ast` | Emite el AST en formato JSON (útil para depuración). |

**Ejemplos:**
```bash
# Compilar un programa Synapse en modo debug
synapse build --debug programa.syn

# Compilar un programa Syquex en modo release
synapse build --release app.syq --target wasm

# Validar código sin generar binario (para OpenSyn)
synapse check --no-emit temp.syq

# Ejecutar un programa Syquex con depuración
synapse run --debug script.syq

# Ejecutar tests
synapse test
```

### 4.3. Estructura de un Proyecto

El comando `synapse init` crea la siguiente estructura:

```
mi_proyecto/
├── src/
│   ├── main.syn (o main.syq)
│   └── ...
├── tests/
│   ├── test_*.syn
│   └── test_*.syq
├── lib/                # Dependencias locales
├── axon.toml           # Manifiesto del proyecto
└── axon.lock           # Lockfile de dependencias
```

### 4.4. Integración con Axon

El CLI unificado gestiona las dependencias a través de Axon:
- `synapse fetch` descarga las dependencias listadas en `axon.toml`.
- `synapse axon publish` publica un paquete en Axon Hub.
- `synapse axon verify` verifica firmas y hashes.

---

## 5. INTEGRACIÓN CON OPENSYN EN EL LSP (BUCLE DE VALIDACIÓN)

### 5.1. Comandos IA en el LSP

El LSP expone comandos personalizados que invocan OpenSyn (ver sección 1.4 para detalles de esquemas JSON). La implementación de estos comandos incorpora un **bucle de validación y corrección** de hasta 3 intentos, orquestado por el LSP, tal como se especifica en el Manual 7, sección 6.3.

### 5.2. Flujo de un Comando IA con Validación

1. El usuario ejecuta un comando en VS Code (ej. "Explicar código" o "Completar código").
2. El cliente LSP envía una petición JSON‑RPC al LSP con el método correspondiente.
3. El LSP recibe la petición y la reenvía al orquestador de OpenSyn (via socket local en `localhost:8088` o similar).
4. El orquestador invoca el pipeline RAG (`synapse_rag.c`) para construir el prompt, incluyendo el contexto estático de reglas (Manual 7, sección 2.3).
5. El prompt se envía al servidor de inferencia (`llama-server`) mediante el cliente HTTP (`llama_client.c`).
6. El servidor genera una respuesta.
7. La respuesta se procesa (router) para extraer el código (si lo hay).
8. **Validación (paso crítico):** El LSP toma el código generado y ejecuta el compilador de Synapse/Syquex en modo `--check` (usando el flag `--no-emit`). Esto se hace mediante el CLI `synapse check --no-emit <archivo>`.
9. **Si compila:** El LSP devuelve el código al editor como sugerencia.
10. **Si falla:** El LSP captura el error (stderr del compilador) y repite el proceso (hasta 3 intentos), añadiendo el error al prompt para que OpenSyn lo corrija. La instrucción adicional es: *"El código anterior tiene el siguiente error: {mensaje_error}. Por favor, corrígelo."*
11. **Fallo definitivo:** Si después de 3 intentos el código no compila, el LSP devuelve el último código generado y los errores al editor, mostrando un mensaje de "No se pudo generar código válido automáticamente. Intenta ajustar la instrucción."

### 5.3. Pipeline RAG en el LSP

El LSP puede invocar el pipeline RAG directamente (sin pasar por el orquestador) para respuestas rápidas. En este caso, el LSP se comunica directamente con `llama-server` usando `llama_client.c`.

**Estructura del contexto RAG (C):**
```c
// opensyn/synapse_rag.h
typedef struct {
    char* archivo;
    char* contenido;
    int linea_inicio;
    int linea_fin;
    char* nodo_ast;           // JSON del nodo AST actual
    char** diagnosticos;
    int num_diagnosticos;
    char* idioma;             // es, en, fr, pt
    char* instruccion;
} RagContext;

PromptInfo rag_construir_prompt(RagContext* ctx, int n_ctx);
```

### 5.4. Validación de Código Generado (Detalle)

Cuando OpenSyn genera código, el LSP lo valida automáticamente usando el compilador con el flag `--no-emit`. Si el código es válido, se muestra como sugerencia. Si no, se inicia el bucle de corrección descrito anteriormente. Este proceso asegura que el código generado por IA cumpla con las reglas del compilador antes de presentarse al usuario, reduciendo drásticamente la tasa de errores y mejorando la experiencia del desarrollador.

---

## 6. PRUEBAS OBLIGATORIAS PARA ESTA ETAPA

| Test | Comando | Criterio |
|------|---------|----------|
| LSP inicialización | `pytest tests/integration/test_lsp_native.py -v` | 5/5 PASS |
| Diagnostics en didOpen | `pytest tests/integration/test_lsp_diagnostics.py -v` | Errores mapeados correctamente |
| Autocompletado | `pytest tests/integration/test_lsp_completion.py -v` | Sugerencias correctas |
| Hover / Definition | `pytest tests/integration/test_lsp_hover.py -v` | Información precisa |
| Comandos IA (aiExplain) | `pytest tests/integration/test_ai_explain.py -v` | 100% pass |
| Comandos IA (aiComplete) | `pytest tests/integration/test_ai_complete.py -v` | Código generado compila (con bucle de corrección) |
| Comandos IA (aiFix) | `pytest tests/integration/test_ai_fix.py -v` | Corrección sugerida es válida |
| Bucle de corrección (3 intentos) | `pytest tests/integration/test_ai_correction.py -v` | El código se corrige exitosamente en ≤3 intentos |
| Flag `--check` del CLI | `pytest tests/integration/test_cli_check.py -v` | El flag funciona correctamente y no genera binario |
| Debugger (grabación) | `pytest tests/integration/test_debug_record.py -v` | Traza generada correctamente |
| Debugger (reversión) | `pytest tests/integration/test_debug_reverse.py -v` | Retroceso funciona |
| CLI unificado | `pytest tests/integration/test_cli.py -v` | 100% pass |

---

## 7. EJEMPLO DE FLUJO DE TRABAJO COMPLETO

**Escenario:** Un desarrollador está escribiendo una aplicación Syquex y necesita ayuda con una función, incluyendo validación automática del código generado.

1. **Abrir el proyecto en VS Code:** La extensión detecta el archivo `.syq` y activa el LSP.
2. **Escribir código:** El LSP proporciona autocompletado, diagnósticos en tiempo real, y hover.
3. **Pedir explicación:** El usuario selecciona una función y ejecuta "Synapse: Explicar código". OpenSyn genera una explicación (sin validación, ya que no hay código).
4. **Generar código:** El usuario ejecuta "Synapse: Generar código con IA". OpenSyn genera código (intento 1). El LSP valida con `synapse check --no-emit`. Si falla, se repite hasta 3 veces. Si compila, se muestra.
5. **Depurar:** El usuario establece un breakpoint y ejecuta `synapse run --debug app.syq`. El debugger se inicia y se detiene en el breakpoint.
6. **Time-travel:** El usuario retrocede en la ejecución para inspeccionar el estado anterior.
7. **Corregir error:** El usuario encuentra un error y ejecuta "Synapse: Corregir errores con IA". OpenSyn sugiere una corrección y el LSP la valida automáticamente.
8. **Transpilar:** El usuario tiene un script Python antiguo. Ejecuta "Synapse: Transpilar Python a Syquex" y obtiene el código equivalente en Syquex.
9. **Compilar y ejecutar:** El usuario compila la aplicación con `synapse build --release app.syq` y la ejecuta.

---

## 8. SIGUIENTES PASOS

Con las herramientas de desarrollo completas, el siguiente manual (Manual 9) se centrará en la **Instalación y Distribución** del ecosistema, incluyendo el instalador unificado y el sistema de actualización.

---

*Este manual proporciona la especificación completa de las herramientas de desarrollo del ecosistema Synapse/Syquex, incluyendo la integración con OpenSyn y el bucle de validación automática. La implementación debe seguir estos lineamientos para garantizar una experiencia de desarrollo fluida, productiva y segura.*

**Fin del Manual 8**