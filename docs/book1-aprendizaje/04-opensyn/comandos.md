# Comandos Principales de OpenSyn

Este capítulo lista y describe todos los comandos disponibles en OpenSyn. Aprenderás a usar cada comando para generar código, explicar programas, refactorizar y más.

Conocer los comandos te permite aprovechar al máximo las capacidades de OpenSyn.

<!-- cumple Manual 7 §6.4 -->

## 1. Comandos de CLI

### Estado y Información

```bash
# Ver estado de OpenSyn (modelo cargado, uso de VRAM)
opensyn status

# Ver información del modelo actual
opensyn model --info

# Listar modelos descargados
opensyn model --list

# Verificar versión
opensyn --version
```

### Comandos de Generación

```bash
# Generar código a partir de una descripción
opensyn generate "función que sume dos números en Syquex"

# Generar código en un lenguaje específico
opensyn generate --lang syquex "API REST para gestionar usuarios"
opensyn generate --lang synapse "función que sume dos números"

# Guardar salida en un archivo
opensyn generate --output suma.syq "función que sume dos números"
```

### Comandos de Explicación

```bash
# Explicar un archivo
opensyn explain archivo.syq

# Explicar un fragmento de código
opensyn explain --code "funcion factorial(n: entero) -> entero:" --lang syquex

# Explicar con nivel de detalle
opensyn explain --detail high archivo.syq
```

### Comandos de Refactorización

```bash
# Refactorizar un archivo
opensyn refactor archivo.syq --prompt "haz la función más eficiente"

# Aplicar un refactoring específico
opensyn refactor --type extract-function archivo.syq

# Ver sugerencias de mejora
opensyn refactor --suggest archivo.syq
```

### Transpilación

```bash
# Transpilar Python a Syquex
opensyn transpile --from python script.py --to syquex

# Transpilar C a Synapse
opensyn transpile --from c codigo.c --to synapse

# Transpilar con opciones
opensyn transpile --from python script.py --to syquex --output resultado.syq
```

### Generación de Bindings

```bash
# Generar bindings Syquex desde cabecera C
opensyn bindings --header libcurl.h --output lib/curl.syq

# Generar bindings para otros lenguajes
opensyn bindings --header api.h --lang python
opensyn bindings --header api.h --lang typescript

# Especificar tipo de binding
opensyn bindings --header api.h --type c-to-syquex --output bindings.syq
```

### Modelos

```bash
# Listar modelos disponibles para descargar
opensyn model --available

# Descargar un modelo
opensyn model --download codellama-7b-Q4_K_M

# Verificar integridad de un modelo
opensyn model --verify codellama-7b-Q4_K_M.gguf

# Eliminar un modelo
opensyn model --remove deepseek-coder-1.3b-Q4_K_M
```

## 2. Comandos del LSP (Editor)

Estos comandos se ejecutan desde el editor (VS Code) mediante el LSP:

### `synapse/aiStatus`

Verifica el estado del servidor de inferencia:

```json
{
  "method": "synapse/aiStatus",
  "result": {
    "estado": "listo",
    "modelo": "codellama-7b-Q4_K_M",
    "vram_usada": "4.2 GB",
    "vram_total": "8 GB",
    "temperature": 0.3
  }
}
```

### `synapse/aiExplain`

Explica el código seleccionado o bajo el cursor:

```json
{
  "method": "synapse/aiExplain",
  "params": {
    "textDocument": { "uri": "file:///proyecto/main.syq" },
    "position": { "line": 5, "character": 10 }
  },
  "result": {
    "explicacion": "Esta función calcula el factorial usando recursión...",
    "codigo_relacionado": null
  }
}
```

### `synapse/aiComplete`

Completa código que el usuario está escribiendo:

```json
{
  "method": "synapse/aiComplete",
  "params": {
    "textDocument": { "uri": "file:///proyecto/main.syq" },
    "position": { "line": 8, "character": 4 },
    "context": "funcion sumar("
  },
  "result": {
    "completions": [
      {
        "texto": "a: entero, b: entero) -> entero:\n    retornar a + b",
        "tipo": "funcion",
        "rango": { "start": {"line": 8, "character": 4}, "end": {"line": 8, "character": 4} }
      }
    ]
  }
}
```

### `synapse/aiFix`

Sugiere correcciones para errores de compilación:

```json
{
  "method": "synapse/aiFix",
  "params": {
    "textDocument": { "uri": "file:///proyecto/main.syq" },
    "diagnostic": {
      "code": "ERR_SEM_TIPO_INCOMPATIBLE",
      "message": "No se puede sumar texto y entero"
    }
  },
  "result": {
    "sugerencia": "Convierte el texto a entero usando 'entero()'",
    "codigo_corregido": "resultado = entero(texto_numero) + 1"
  }
}
```

### `synapse/aiTranspile`

Transpila código entre lenguajes:

```json
{
  "method": "synapse/aiTranspile",
  "params": {
    "textDocument": { "uri": "file:///proyecto/script.py" },
    "from": "python",
    "to": "syquex"
  },
  "result": {
    "codigo": "funcion procesar_datos(datos: Lista<entero>) -> Lista<entero>:\n    ..."
  }
}
```

### `synapse/aiBindings`

Genera bindings Syquex desde una cabecera C:

```json
{
  "method": "synapse/aiBindings",
  "params": {
    "textDocument": { "uri": "file:///proyecto/libcurl.h" }
  },
  "result": {
    "codigo": "// Bindings generados para libcurl\n...",
    "archivo_salida": "bindings/curl.syq"
  }
}
```

## 3. Atajos de Teclado (VS Code)

| Atajo | Comando | Descripción |
|-------|---------|-------------|
| `Ctrl+Shift+E` | `synapse.aiExplain` | Explicar código seleccionado |
| `Ctrl+Shift+G` | `synapse.aiGenerate` | Generar código |
| `Ctrl+Shift+F` | `synapse.aiFix` | Corregir error bajo el cursor |
| `Ctrl+Shift+R` | `synapse.aiRefactor` | Refactorizar código |
| `Ctrl+Shift+T` | `synapse.aiTranspile` | Transpilar archivo |

## 4. Argumentos Globables

```bash
# Modo verbose (más información)
opensyn generate "función" --verbose

# Salida JSON
opensyn generate "función" --json

# Sin validación (para pruebas rápidas)
opensyn generate "función" --no-validate

# Prompt personalizado
opensyn generate --prompt "Escribe una función que..." 
```

## 5. Configuración de Comandos

Los comandos pueden configurarse en `~/.opensyn/config.toml`:

```toml
[comandos]
# Timeout por defecto (segundos)
timeout = 30

# Número máximo de reintentos
max_reintentos = 3

# Modo de validación
validacion = true  # Usa el compilador real para validar

# Idioma por defecto
idioma = "es"

# Editor preferido
editor = "vscode"
```

## 6. Uso Práctico

### Generar una función

```bash
$ opensyn generate "función en Syquex que valide un email"
```

Salida:
```syquex
funcion validar_email(email: texto) -> booleano:
    let patron = "^[^@]+@[^@]+\\.[^@]+$"
    retornar regex.coincidir(email, patron)
```

### Transpilar código

```bash
$ opensyn transpile --from python ejemplo.py --to syquex
# Salida: ejemplo.syq (código transpilado)
```

### Generar bindings

```bash
$ opensyn bindings --header sqlite3.h --output lib/sqlite.syq
# Salida: lib/sqlite.syq (bindings Syquex para SQLite)
```

## Referencias

- **Manual 7 §6.4**: Comandos CLI de OpenSyn
- **Manual 7 §6.3**: Bucle de corrección automática
- **Manual 7 §4.1**: Comandos personalizados del LSP
- **Manual 8 §1**: CLI unificado de Synapse

// cumple Manual 7 §6.4
