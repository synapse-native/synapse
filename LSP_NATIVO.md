# Synapse: Servidor LSP Nativo v2.2.0

> **Documento:** `LSP_NATIVO.md`
> **Versión:** 2.2.0 — PRODUCTION-READY
> **Última actualización:** 24 Julio 2026

---

## 1. Arquitectura General

El servidor LSP de Synapse es un **proceso daemon** compilado a código nativo
que se comunica con el editor a través de **stdin/stdout** usando el protocolo
**JSON-RPC 2.0** sobre cabeceras `Content-Length`.

```
Editor (VS Code, Neovim, etc.)
  │  envía JSON-RPC por stdin
  ▼
synapse_lsp.exe / test_lsp_bin.exe
  ├── Bucle daemon: leer cabecera → leer cuerpo JSON → enrutar → escribir respuesta
  ├── Por cada textDocument/didChange:
  │    1. Recibe el texto completo del archivo
  │    2. Ejecuta Lexer + Parser + Analizador Semántico
  │    3. Convierte errores a objetos Diagnostic de LSP
  │    4. Envía textDocument/publishDiagnostics
  └── Maneja initialize, shutdown, exit
```

**Regla de Oro:** El servidor nunca invoca `exit()`. Nunca permite que una
excepción del compilador suba al hilo principal.

---

## 2. Binarios Disponibles

| Binario | Ruta | Tamaño | Propósito |
|---------|------|--------|-----------|
| `test_lsp_bin.exe` | Raíz del proyecto | ~909 KB | Desarrollo: compilado desde `nucleo/lsp.syn` |
| `nucleo/lsp_test.exe` | `nucleo/` | ~727 KB | Alternativo (compilación previa) |
| `build/bin/synapse_lsp.exe` | `build/bin/` | Variable | Release empaquetado |

### 2.1 Compilación

```bash
# Desde nucleo/lsp.syn:
python main.py -o test_lsp_bin.exe nucleo/lsp.syn
# → gcc: 0 errores, binario generado
```

---

## 3. Métodos LSP Soportados

| Método | Estado | Descripción |
|--------|--------|-------------|
| `initialize` | ✅ | Negociación de capacidades |
| `initialized` | ✅ | Confirmación del editor |
| `textDocument/didOpen` | ✅ | Diagnóstico al abrir archivo |
| `textDocument/didChange` | ✅ | Diagnóstico en tiempo real |
| `textDocument/didSave` | ✅ | Diagnóstico al guardar |
| `textDocument/didClose` | ✅ | Limpiar diagnostics del documento |
| `shutdown` | ✅ | Apagado ordenado |
| `exit` | ✅ | Salida del proceso |
| `synapse/aiStatus` | ✅ | Consultar disponibilidad de IA local |
| `synapse/aiExplain` | ✅ | Explicar código con IA |
| `synapse/aiComplete` | ✅ | Generar código con IA |

---

## 4. Formato de Cabecera

```
Content-Length: <n>\r\n\r\n
```

El servidor lee byte a byte hasta `\r\n\r\n`, extrae `n`, lee exactamente `n` bytes
del cuerpo JSON, y procesa el mensaje.

---

## 5. Capacidades Declaradas (initialize)

```json
{
    "capabilities": {
        "textDocumentSync": {
            "openClose": true,
            "change": 1,
            "save": { "includeText": true }
        }
    }
}
```

`textDocumentSync.change = 1` = modo **Full** (envío completo del documento en cada cambio).

---

## 6. Mapeo de Errores a Diagnostics LSP

### 6.1 Conversión de Coordenadas

| Sistema | Líneas | Columnas |
|---------|--------|----------|
| Synapse | **1-based** | **0-based** |
| LSP | **0-based** | **0-based** |

```
LSP_linea   = Synapse_linea - 1
LSP_columna = Synapse_columna        (Sin cambio)
```

### 6.2 Formato del Diagnostic

```json
{
    "range": {
        "start": { "line": <syn_linea-1>, "character": <syn_columna> },
        "end":   { "line": <syn_linea-1>, "character": <syn_columna+1> }
    },
    "severity": 1,
    "code": "<ErrorCode.name>",
    "source": "synapse",
    "message": "<mensaje formateado>"
}
```

### 6.3 Mapeo por Fase

| Fase | Código LSP | Severidad |
|------|-----------|-----------|
| **Lexer** | `ERR_LEX_CHAR_UNEXPECTED`, `ERR_STRING_UNCLOSED` | Error (1) |
| **Parser** | `ERR_SYNTAX_EXPECTED_TOKEN`, `ERR_SYNTAX_UNEXPECTED_TOKEN` | Error (1) |
| **Parser** | `ERR_INDENT_INVALID`, `ERR_INDENT_INCONSISTENT` | Error (1) |
| **Semántico** | `ERR_SEM_VAR_NO_DECLARADA`, `ERR_SEM_TIPO_INCOMPATIBLE` | Error (1) |
| **Semántico** | `ERR_SEM_FUNC_NO_DEFINIDA`, `ERR_SEM_REDEFINICION` | Error (1) |
| **Semántico** | `ERR_SEM_ESTRUCTURA_NO_DEFINIDA`, `ERR_SEM_CAMPO_NO_EXISTE` | Error (1) |

---

## 7. Integración con VS Code

### 7.1 Extensión

El cliente LSP se implementa en `vscode-synapse/extension.js`.

**Activación:**
- Se activa al abrir archivos `.syn`
- Detecta automáticamente el binario LSP nativo
- Sin dependencia de Python (a diferencia de versiones anteriores)

### 7.2 Auto-detección del Binario

```javascript
// Orden de búsqueda:
// 1. test_lsp_bin.exe            (proyecto raíz)
// 2. nucleo/lsp_test.exe         (subdirectorio)
// 3. build/bin/synapse_lsp.exe   (release)
// 4. Configuración: synapse.lsp.nativeBinary (manual)
```

### 7.3 Configuración

| Clave | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `synapse.lsp.nativeBinary` | `string` | `""` | Ruta personalizada al binario LSP |
| `synapse.lsp.enabled` | `bool` | `true` | Habilitar/deshabilitar LSP |
| `synapse.trace.server` | `enum` | `"off"` | Traza comunicación (`off`, `messages`, `verbose`) |

### 7.4 Comandos Registrados

| Comando | Descripción |
|---------|-------------|
| `synapse.aiStatus` | Verificar disponibilidad de IA local (Ollama) |
| `synapse.aiExplain` | Explicar código seleccionado con IA local |
| `synapse.aiComplete` | Generar código Synapse con IA local |

---

## 8. Integración con IA Local (Ollama)

### 8.1 Arquitectura

```
VS Code → synapse_lsp.exe (LSP) → Ollama (localhost:11434)
                                     ├── phi3:mini
                                     ├── llama3.2
                                     └── otros modelos GGUF
```

### 8.2 Puente LSP-IA

El módulo `synapse_lsp/llm_bridge.py` implementa el puente:

| Función | Método LSP | Descripción |
|---------|-----------|-------------|
| `generar_completado()` | `synapse/aiComplete` | Genera código desde descripción |
| `explicar_codigo()` | `synapse/aiExplain` | Explica código seleccionado |
| `sugerir_correccion()` | — | Sugiere correcciones para errores |

### 8.3 API Ollama

```python
POST http://localhost:11434/api/generate
{
    "model": "phi3:mini",
    "prompt": "...",
    "stream": false,
    "options": { "temperature": 0.7 }
}
```

### 8.4 Requisitos

- **Opcional:** Ollama instalado y ejecutándose en `localhost:11434`
- **Modelos recomendados:** `phi3:mini`, `llama3.2`
- **Opt-In:** La IA local es 100% opt-in. Sin IA, el LSP funciona igual.

---

## 9. Pruebas de Integración

### 9.1 Tests Unitarios (Python)

```bash
pytest tests/integration/test_lsp_native.py -v
```

```python
test_lsp_initialize              ✅ PASSED
test_lsp_diagnostics_syntax_error ✅ PASSED
test_lsp_diagnostics_clean       ✅ PASSED
test_lsp_unknown_method          ✅ PASSED
test_lsp_shutdown                ✅ PASSED
```

### 9.2 Test de Diagnóstico en Tiempo Real

El LSP envía `textDocument/publishDiagnostics` en cada cambio del documento.
Los errores se muestran como subrayados en rojo en el editor.

### 9.3 Prueba Manual

```bash
# Iniciar servidor LSP desde terminal:
echo -e "Content-Length: 57\r\n\r\n{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{}}" | test_lsp_bin.exe
```

---

## 10. Evolución del LSP

### Fase 12 (Completada)
- Servidor JSON-RPC fortalecido (Python)
- Puente de IA local (Ollama, Phi-3)
- `synapse_lsp/server.py` → 3 nuevos métodos: hover, codeAction

### Fase 13 (Completada — v2.0)
- **Binario nativo** compilado desde `nucleo/lsp.syn`
- **Sin dependencia Python** en el pipeline LSP
- **5/5 tests pasan** — initialize, diagnostics, shutdown
- **Auto-detección** del binario en la extensión VS Code
- **Comandos IA** integrados vía LSP extendido (`synapse/aiStatus`, etc.)

### Fase 14 (Completada)
- Reset de estado global por request LSP (`#lang` validation)
- Pipeline nativa reentrante (285 tests, 0 xfails)

---

## 11. Resolución de Problemas

### Síntoma: La extensión VS Code no se activa
**Causa:** No encuentra el binario LSP nativo.
**Solución:** Asegurar que `test_lsp_bin.exe` o `synapse_lsp.exe` exista en la raíz.

### Síntoma: No hay diagnósticos ni subrayados en rojo
**Causa:** El servidor LSP no se inició.
**Solución:** Verificar `synapse.lsp.enabled = true` en la configuración VS Code.

### Síntoma: Los comandos IA muestran "Ollama no detectado"
**Causa:** Ollama no está ejecutándose.
**Solución:** Instalar e iniciar Ollama: `ollama serve` + `ollama pull phi3:mini`.
