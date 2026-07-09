# Diseño del Servidor LSP para Synapse

## 1. Arquitectura General

El servidor LSP de Synapse es un **proceso daemon** que se comunica con el editor
a través de **stdin/stdout** usando el protocolo **JSON-RPC 2.0** sobre el
formato de cabecera `Content-Length` (LSP estándar de Microsoft).

```
Editor (VS Code, Neovim, etc.)
  │  envía JSON-RPC por stdin
  ▼
synapse --lsp
  ├── Bucle daemon: leer cabecera → leer cuerpo JSON → enrutar → escribir respuesta
  ├── Por cada textDocument/didChange:
  │    1. Recibe el texto completo del archivo
  │    2. Ejecuta Lexer + Parser + Analizador Semántico
  │    3. Convierte errores a objetos Diagnostic de LSP
  │    4. Envía textDocument/publishDiagnostics
  └── Maneja initialize, shutdown, exit
```

**Regla de Oro del LSP:** El servidor nunca invoca `sys.exit()`. Nunca deja que
una excepción del compilador suba al hilo principal. Toda excepción se captura,
se formatea como `textDocument/publishDiagnostics` (o como `window/showMessage`
si es estructural) y se continúa escuchando la próxima petición.

---

## 2. Mapeo de Errores Internos a Diagnostics LSP

### 2.1 Formato del objeto Diagnostic LSP

```typescript
interface Diagnostic {
  range: Range;
  severity?: DiagnosticSeverity;
  code?: string | number;
  source?: string;
  message: string;
}
```

### 2.2 Conversión de coordenadas (Synapse → LSP)

| Sistema    | Líneas        | Columnas      |
|------------|---------------|---------------|
| Synapse    | **1-based**   | **0-based**   |
| LSP        | **0-based**   | **0-based**   |

**Reglas de conversión:**

```
LSP_linea   = Synapse_linea - 1
LSP_columna = Synapse_columna        (Synapse ya usa 0-based en columnas)
```

### 2.3 Mapeo de ErrorCodes a DiagnosticSeverity

| ErrorCodes                                       | Severidad LSP |
|--------------------------------------------------|---------------|
| ERR_SYNTAX_*, ERR_LEX_*, ERR_CANONICAL_FORMAT   | Error (1)     |
| ERR_SEM_*                                        | Error (1)     |
| ERR_LANG_*, ERR_INDENT_*                         | Error (1)     |
| ERR_FILE_NOT_FOUND                               | Error (1)     |

Todos los errores de Synapse se tratan como `DiagnosticSeverity.Error = 1`
porque el compilador aborta ante cualquier error. En el futuro se podrán
distinguir warnings de errores.

### 2.4 Esquema exacto del objeto Diagnostic generado

```json
{
  "range": {
    "start": { "line": <synapse_linea-1>, "character": <synapse_columna> },
    "end":   { "line": <synapse_linea-1>, "character": <synapse_columna+1> }
  },
  "severity": 1,
  "code": "<ErrorCode.name>",
  "codeDescription": { "href": "" },
  "source": "synapse",
  "message": "<mensaje formateado>"
}
```

**Notas:**
- `range` usa `end.character = start.character + 1` para resaltar al menos
  un carácter. Sin esta regla, editores como VS Code no muestran el subrayado.
- `code` es el nombre del enum `ErrorCodes` (ej. `ERR_SEM_VAR_NO_DECLARADA`).
- `message` es el texto traducido ya formateado por `DiagnosticManager`.

---

## 3. Mapeo por Fase del Compilador

### 3.1 Lexer (`lexer.py`)

| Error interno                      | Código LSP                  | Rango                                |
|-----------------------------------|------------------------------|--------------------------------------|
| Carácter inesperado `@`          | `ERR_LEX_CHAR_UNEXPECTED`   | línea del char, columna del char     |
| Cadena sin cerrar                | `ERR_STRING_UNCLOSED`        | línea de apertura, columna 0         |
| Error genérico de lexer          | `ERR_LEX`                    | línea/columna del token fallido      |

### 3.2 Parser (`parser.py`)

| Error interno                       | Código LSP                   | Rango                                |
|-------------------------------------|------------------------------|--------------------------------------|
| Se esperaba X, se encontró Y        | `ERR_SYNTAX_EXPECTED_TOKEN`  | línea/columna de Y                   |
| Token inesperado tras expresión     | `ERR_SYNTAX_UNEXPECTED_TOKEN`| línea/columna del token               |
| Expresión inesperada               | `ERR_SYNTAX_UNEXPECTED_EXPR` | línea/columna de la expresión         |
| Se esperaba nueva línea             | `ERR_SYNTAX_EXPECTED_NEWLINE`| línea/columna del token actual        |
| Indentación inválida                | `ERR_INDENT_INVALID`         | línea 0, columna 0                   |
| Indentación inconsistente           | `ERR_INDENT_INCONSISTENT`    | línea 0, columna 0                   |

### 3.3 Analizador Semántico (`analizador_semantico.py`)

| Error interno                      | Código LSP                        | Rango                                |
|------------------------------------|-----------------------------------|--------------------------------------|
| Variable no declarada              | `ERR_SEM_VAR_NO_DECLARADA`       | línea/columna del identificador      |
| Tipo incompatible                  | `ERR_SEM_TIPO_INCOMPATIBLE`      | línea/columna de la operación        |
| Tipo de retorno incorrecto         | `ERR_SEM_TIPO_RETORNO`            | línea/columna del `return`           |
| Función no definida                | `ERR_SEM_FUNC_NO_DEFINIDA`        | línea/columna de la llamada          |
| Redefinición en mismo ámbito       | `ERR_SEM_REDEFINICION`            | línea/columna de la segunda definición |
| Argumentos inválidos               | `ERR_SEM_ARGUMENTOS_INVALIDOS`    | línea/columna de la llamada          |
| Estructura no definida             | `ERR_SEM_ESTRUCTURA_NO_DEFINIDA`  | línea/columna del nombre             |
| Campo no existe                    | `ERR_SEM_CAMPO_NO_EXISTE`         | línea/columna del acceso              |

---

## 4. Métodos LSP Soportados (Fase 4a)

| Método                             | Implementado | Descripción                          |
|------------------------------------|-------------|--------------------------------------|
| `initialize`                       | ✅          | Negociación de capacidades           |
| `initialized`                      | ✅          | Confirmación del editor              |
| `textDocument/didOpen`             | ✅          | Diagnóstico al abrir                 |
| `textDocument/didChange`           | ✅          | Diagnóstico al editar                |
| `textDocument/didSave`             | ✅          | Diagnóstico al guardar               |
| `textDocument/didClose`            | ✅          | Limpiar diagnostics del documento    |
| `shutdown`                         | ✅          | Apagado ordenado                     |
| `exit`                             | ✅          | Salida del proceso                   |

### Capacidades declaradas en `initialize`:

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

`textDocumentSync.change = 1` significa modo **Full** — el editor envía el
contenido completo del archivo en cada cambio (no parches incrementales).
Esto simplifica la implementación.

### 5. Formato de Cabecera

```
Content-Length: <n>\r\n\r\n
```

El servidor lee byte a byte hasta encontrar `\r\n\r\n`, extrae `n` como entero,
lee exactamente `n` bytes del cuerpo JSON, y procesa el mensaje.

Si la línea de cabecera no comienza con `Content-Length:`, se ignora (por
robustez ante posibles cabeceras adicionales). Si no se recibe una línea
`Content-Length` en los primeros 4096 bytes, el servidor cierra la conexión
con un error de protocolo.