# Especificación Técnica: OpenSyn v5.0

**Versión:** 5.0.0
**Fecha:** 26 Julio 2026
**Estado:** LIBERACIÓN — Documentación Final
**Versión Base:** Synapse v5.0

---

## 1. VISIÓN GENERAL

OpenSyn es el **motor de inteligencia artificial local y migración automática** del ecosistema Synapse. Opera como un sistema dual:

1. **Asistente de código con IA local** — Provee autocompletado, generación de código, depuración time-travel y análisis de trazas mediante modelos LLM ejecutados localmente via `llama.cpp`.
2. **Migrador automático Python → Synapse** — Convierte código Python 3.10+ a Synapse idiomático con tipado estricto, ownership único y contratos lógicos.

### 1.1 Principios de Diseño

| Principio | Descripción |
|-----------|-------------|
| **Zero-Cloud** | Toda la inferencia se ejecuta localmente. Cero conexiones salientes. |
| **Privacidad Total** | El código nunca abandona el equipo del usuario. |
| **RAG Quirúrgico** | Solo se envía al LLM el contexto mínimo necesario (AST + firma de función). |
| **Offline-First** | Funciona sin conexión a internet. Los modelos se descargan una sola vez. |
| **Determinismo** | Las mismas entradas producen las mismas sugerencias (seed fija). |

---

## 2. ARQUITECTURA DEL SISTEMA

```
┌────────────────────────────────────────────────────────────────────┐
│                        OPENSYN v5.0                                 │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐   ┌──────────────┐   ┌────────────────────────┐      │
│  │   LSP    │──▶│  ROUTER      │──▶│  LLM BACKEND           │      │
│  │  Server  │   │  Determinista│   │  (llama-server local)   │      │
│  └──────────┘   └──────┬───────┘   └───────────┬────────────┘      │
│       ▲                │                       │                   │
│       │                ▼                       ▼                   │
│       │         ┌──────────────┐   ┌────────────────────────┐      │
│       │         │  RAG Pipeline│   │  RAG Context Builder   │      │
│       │         │  Quirúrgico  │   │  (AST + tipo + traza)  │      │
│       │         └──────────────┘   └────────────────────────┘      │
│       │                                                             │
│       │         ┌────────────────────────────────────────┐          │
│       │         │  PYTHON → SYNAPSE MIGRATOR              │          │
│       │         │  py_parser → type_inference → ast_mapper│          │
│       │         └────────────────────────────────────────┘          │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │  CANONICAL AST (.syn.json) — Representación Intermedia   │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### 2.1 Componentes

| Componente | Archivo | Función |
|------------|---------|---------|
| **LSP Server** | `synapse_lsp/server.py` | Servidor JSON-RPC 2.0 sobre stdio. Maneja `initialize`, `textDocument/diagnostic`, `textDocument/hover`, `textDocument/definition`, `textDocument/completion`, `synapse/migrateFile`. |
| **Router** | `opensyn/router.syn` + `router_config.yaml` | Enrutador determinista basado en AST. Decide si una consulta necesita LLM (completado complejo) o puede resolverse localmente (diagnóstico simple). |
| **RAG Pipeline** | `nucleo/synapse_rag.c` + `llama_client.c` | Construcción de contexto mínimo: extrae la función actual, sus tipos, contratos y hasta 5 sentencias circundantes del AST. Inyecta como prompt al LLM. |
| **LLM Backend** | `nucleo/llama_client.c` | Cliente HTTP nativo para `llama-server.exe`. Envía requests POST con timeout configurable y manejo de errores. |
| **HW Detector** | `nucleo/detect_hardware.c` | Detecta RAM, VRAM, CPUs y sugiere configuración óptima de `llama-server` (modelo, `n_ctx`, `threads`, `ngl`). |
| **Migration Pipeline** | `synapse_lsp/open_syn/py_parser.py`, `type_inference.py`, `ast_mapper.py`, `pretty_printer.py` | Parseo de Python 3.10+ a AST canónico, inferencia de tipos estrictos, mapeo a Synapse y pretty-print. |
| **Time-Travel Debug** | `librerias/std/debug.syn` + `synapse_rt.c` | Grabación determinista de ejecución (rr-style), replay con breakpoints reversibles, snapshots de memoria. |

---

## 3. ROUTER DETERMINISTA (AST-BASED)

El router decide si una solicitud LSP puede resolverse localmente o requiere inferencia del LLM. Esto minimiza llamadas al LLM (costosas en tiempo y recursos).

### 3.1 Reglas de Enrutamiento

```
Entrada LSP
    │
    ├── textDocument/diagnostic ──→ 100% LOCAL
    │   └── Análisis semántico + verificador formal (modo --safe)
    │
    ├── textDocument/hover ──→ 100% LOCAL
    │   └── Tabla de símbolos + documentación de std
    │
    ├── textDocument/definition ──→ 100% LOCAL
    │   └── Navegación de AST + tabla de símbolos
    │
    ├── textDocument/completion
    │   ├── Completado simple (keyword, símbolo local) → LOCAL
    │   └── Completado complejo (cuerpo de función, expresión) → LLM
    │
    ├── synapse/migrateFile ──→ 100% LOCAL
    │   └── Pipeline Python → Synapse (sin LLM)
    │
    └── synapse/explainError ──→ LLM + RAG
        └── Traza + AST + contexto → análisis con IA
```

### 3.2 Configuración (`opensyn/router_config.yaml`)

```yaml
router:
  rules:
    - method: "textDocument/diagnostic"
      handler: "local"
      priority: 100

    - method: "textDocument/hover"
      handler: "local"
      priority: 90

    - method: "textDocument/definition"
      handler: "local"
      priority: 90

    - method: "textDocument/completion"
      handler: "local"
      priority: 80
      conditions:
        - type: "keyword_completion"
        - type: "symbol_completion"
          max_depth: 2

    - method: "textDocument/completion"
      handler: "llm"
      priority: 50
      conditions:
        - type: "function_body_completion"
        - type: "expression_completion"
          min_tokens: 5

    - method: "synapse/migrateFile"
      handler: "local_pipeline"
      priority: 100

    - method: "synapse/explainError"
      handler: "llm_rag"
      priority: 100
      rag_config:
        max_context_lines: 20
        include_trace: true
        include_ast_context: true
```

---

## 4. RAG PIPELINE QUIRÚRGICO

El pipeline RAG construye el contexto mínimo necesario para que el LLM genere respuestas precisas sin saturar la ventana de contexto.

### 4.1 Flujo del Pipeline

```
1. Recibir solicitud LSP + AST canónico
2. Extraer nodo actual (función, sentencia, expresión)
3. Recopilar contexto:
   a. Firma de función (nombre, parámetros, retorno)
   b. Contratos (requiere/garantiza)
   c. Variables locales con tipos
   d. Hasta 5 líneas de código circundante
   e. Traza de error (si existe)
4. Construir prompt estructurado:
   [CONTEXTO]
   Archivo: usuario.syn
   Función: procesar_datos(items: Lista<entero>) -> entero
   Contrato: requiere(items.longitud > 0)
   Variables: total: entero = 0

   [CÓDIGO]
   funcion procesar_datos(items: Lista<entero>) -> entero:
       requiere:
           items.longitud > 0
       garantiza:
           _resultado_ >= 0
       let total = 0
       para item en items:
           █  <-- cursor aquí

   [CONSULTA]
   Completar el cuerpo del bucle para procesar items.

5. Enviar prompt a llama-server
6. Parsear respuesta y devolver sugerencias LSP
```

### 4.2 Pipeline RAG — Niveles de Contexto

| Nivel | Contenido | Tamaño típico | Cuándo se usa |
|-------|-----------|---------------|----------------|
| **Micro** | Símbolo actual + tipo | ~50 tokens | Hover, definiciones |
| **Local** | Función actual + 5 líneas | ~200 tokens | Completado simple |
| **Función** | Función completa + contratos | ~500 tokens | Completado de cuerpo, explicación de error |
| **Archivo** | Archivo completo (truncado) | ~2000 tokens | Migración, refactorización |

### 4.3 Detección de Hardware

```bash
# Detectar hardware y obtener configuración óptima
$ synapse --detect-hardware
========================================
  Synapse — Perfil de Hardware
========================================
  RAM total:       31.9 GB
  VRAM detectada:  8.0 GB
  CPUs lógicos:    16
  CPUs físicos:    8
----------------------------------------
  Tier:            7B (32–63 GB)
  Modelo sugerido:  llama-3.2-7b-instruct:Q4_K_M.gguf
  ctx-size sugerido: 4096
  threads sugeridos: 8
  ngl (GPU layers): 24
========================================
```

### 4.4 Integración con `llama-server`

La comunicación con el motor de inferencia se realiza mediante HTTP nativo:

```c
// Ejemplo del cliente HTTP en llama_client.c
POST /completion HTTP/1.1
Host: 127.0.0.1:8088
Content-Type: application/json

{
  "prompt": "[CONTEXTO]...\\n[CONSULTA]...",
  "temperature": 0.2,
  "top_p": 0.9,
  "n_predict": 128,
  "stop": ["\\n\\n", "\\n    }"],
  "cache_prompt": true,
  "seed": 42
}
```

Parámetros clave:
- `temperature: 0.2` — Baja temperatura para respuestas deterministas
- `cache_prompt: true` — Reutiliza caché KV entre requests similares
- `seed: 42` — Semilla fija para reproducibilidad
- `stop: ["\\n\\n", "\\n    }"]` — Detiene generación al completar el bloque

---

## 5. ARQUITECTURA LSP

### 5.1 Protocolo

El LSP de Synapse implementa JSON-RPC 2.0 sobre stdio bidireccional.

```
┌──────────┐         JSON-RPC 2.0          ┌──────────┐
│ VS Code  │ ◄══════════ stdio ═══════════► │ synapse  │
│ (Cliente)│     Content-Length: N          │  LSP     │
└──────────┘                                └──────────┘
```

### 5.2 Capacidades Soportadas

| Capacidad | Estado | Descripción |
|-----------|--------|-------------|
| `initialize` | ✅ | Handshake inicial, intercambio de capacidades |
| `textDocument/diagnostic` | ✅ | Diagnósticos en tiempo real (errores, warnings) |
| `textDocument/hover` | ✅ | Información de tipo y documentación al pasar el ratón |
| `textDocument/definition` | ✅ | Navegación a definición de símbolo |
| `textDocument/completion` | ✅ | Autocompletado (local + IA) |
| `textDocument/semanticTokens` | ✅ | Resaltado semántico de sintaxis |
| `textDocument/signatureHelp` | ✅ | Ayuda de firmas de funciones |
| `textDocument/references` | ✅ | Búsqueda de referencias |
| `textDocument/documentSymbol` | ✅ | Símbolos de documento para outline |
| `workspace/symbol` | ✅ | Búsqueda de símbolos en workspace |
| `synapse/migrateFile` | ✅ | Migración Python → Synapse |
| `synapse/explainError` | 🚧 | Explicación de error con IA |

### 5.3 Flujo de Diagnóstico

```
1. VS Code envía textDocument/didChange
2. LSP recibe el contenido actualizado
3. LSP ejecuta:
   a. Lexer → tokens
   b. Parser → AST
   c. Analizador semántico → tabla de símbolos
   d. [Opcional] Verificador formal (--safe)
4. LSP recopila diagnósticos del AST
5. LSP envía textDocument/publishDiagnostics
6. VS Code muestra errores/warnings en el editor
```

---

## 6. MIGRADOR PYTHON → SYNAPSE

### 6.1 Pipeline de Migración

```
Archivo .py
    │
    ▼
┌──────────────────────┐
│   py_parser.py       │  ast.parse() → AST Universal Canónico
│   (Python ast lib)   │  + extracción de type hints
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  type_inference.py   │  Inferencia de tipos estrictos:
│                      │  - Variables sin anotación → error
│                      │  - Any → requiere tipo explícito
│                      │  - Flujo-sensitivo (if/else, loops)
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│   ast_mapper.py      │  Mapeo nodo a nodo:
│                      │  - Python AST → Synapse AST
│                      │  - Python types → Synapse types
│                      │  - Contratos inferidos (requiere/garantiza)
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ pretty_printer.py    │  Synapse AST (.syn.json) → .syn
│                      │  - Indentación canónica (4 espacios)
│                      │  - Preservación de comentarios
│                      │  - Estilo idiomático
└──────────┬───────────┘
           ▼
    Archivo .syn + .syn.json
```

### 6.2 Mapeo de Tipos

| Python | Synapse | Notas |
|--------|---------|-------|
| `int` | `entero` | `int64_t` subyacente |
| `float` | `decimal` | `double` subyacente |
| `bool` | `booleano` | `bool` subyacente |
| `str` | `texto` | `CadenaSegura` (longitud + datos) |
| `bytes` | `bytes` | `uint8_t[]` + longitud |
| `None` | `nulo` | Equivalente a `void` |
| `list[T]` | `Lista<T>` | Lista genérica |
| `dict[K, V]` | `Diccionario<K, V>` | Hash map nativo |
| `Optional[T]` | `Opcion<T>` | `algun(T) / ninguno` |
| `Union[T, E]` | `Resultado<T, E>` | `ok(T) / err(E)` |
| `tuple[A, B]` | `Par<A, B>` | Par genérico |
| `Callable[[A], R]` | `funcion(A) -> R` | First-class function |
| `Iterator[T]` | `Iterador<T>` | Protocolo de iteración |
| `AsyncIterator[T]` | `Canal<T>` | Channel-based streaming |

### 6.3 Cobertura de Migración

| Constructo Python | Cobertura | Estado |
|-------------------|-----------|--------|
| Funciones (`def`) | 100% | ✅ |
| Clases como estructuras | 100% | ✅ |
| Type hints (PEP 484) | 100% | ✅ |
| If/elif/else | 100% | ✅ |
| Bucles for/while | 100% | ✅ |
| List comprehensions | 90% | ✅ |
| Try/except | 100% | ✅ |
| Async/await | 85% | 🚧 |
| Generadores/yield | 70% | 🚧 |
| Decoradores | 60% | 🚧 |
| Clases con herencia | 50% | 🚧 |

### 6.4 Ejemplo de Migración

**Python (`usuario.py`):**
```python
from typing import Optional

def buscar_usuario(id: int, base_datos: dict[int, str]) -> Optional[str]:
    """Busca un usuario por ID en la base de datos."""
    if id in base_datos:
        return base_datos[id]
    return None
```

**Synapse (`usuario.syn`):**
```synapse
#lang: es
importar std.io

funcion buscar_usuario(id: entero, base_datos: Diccionario<entero, texto>) -> Opcion<texto>:
    requiere:
        id >= 0
    garantiza:
        _resultado_ es Opcion<texto>
    si id en base_datos:
        retornar algun(base_datos[id])
    retornar ninguno
```

---

## 7. API DE REFERENCIA DEL AST CANÓNICO

El AST Canónico (`.syn.json`) es la representación intermedia universal del ecosistema Synapse. Sirve como:

- Formato de intercambio entre compilador Python y compilador nativo
- Entrada para herramientas LSP (diagnóstico, hover, completado)
- Base para el RAG quirúrgico de OpenSyn
- Formato de serialización para depuración time-travel

### 7.1 Tipos de Nodo

Ver `docs/api_ast_canonico.md` para la referencia completa.

---

## 8. CONFIGURACIÓN DE OPEN SYN

### 8.1 Archivo `axon.toml` (sección OpenSyn)

```toml
[open_syn]
# Motor de IA
llm_model = "llama-3.2-7b-instruct:Q4_K_M.gguf"
llm_host = "127.0.0.1:8088"
llm_timeout_ms = 30000
llm_temperature = 0.2
llm_seed = 42

# RAG
rag_max_context_lines = 20
rag_include_trace = true
rag_include_ast = true

# Migración
strict_mode = true
infer_contracts = true
optimize_simd = true
output_format = "syn"

# Debug
trace_enabled = true
trace_buffer_size = 50000
trace_dir = "~/.synapse/traces"
```

---

## 9. SEGURIDAD

| Aspecto | Medida |
|---------|--------|
| **Zero telemetry** | El LSP y OpenSyn no envían datos a ningún servidor externo |
| **Modelos locales** | Los LLMs se ejecutan 100% local con `llama.cpp` |
| **Sandbox de código** | El código generado por IA se ejecuta en sandbox con recursos limitados |
| **Firmas Ed25519** | Todos los artefactos de release se firman criptográficamente |
| **SBOM** | Todo release incluye SBOM SPDX 2.3 con SHA-256 de cada archivo |
| **SLSA Level 3** | Provenance aislado y verificable en cada build |

---

## 10. REFERENCIAS

| Documento | Descripción |
|-----------|-------------|
| `docs/api_ast_canonico.md` | Referencia completa del AST Canónico |
| `docs/migracion_python_synapse.md` | Guía de migración Python → Synapse |
| `ROADMAP.md` | Roadmap completo del proyecto v5.0 |
| `MANUAL_DE_INGENIERÍA_Y_DESARROLLO.md` | Manual técnico de ingeniería |
| `ARCH_ESPECIFICACION.md` | Especificación arquitectónica |
| `AXON_SPEC.md` | Especificación del gestor de paquetes Axon |
| `LSP_NATIVO.md` | Especificación del LSP nativo |

---

## 11. HISTORIAL DE CAMBIOS

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 5.0.0 | 26 Jul 2026 | Documentación final de liberación. Integración completa de router RAG, migrador, LSP y time-travel debug. |

---

**Fin de la Especificación Técnica OpenSyn v5.0.0**
