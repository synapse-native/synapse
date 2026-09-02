# OpenSyn en VS Code

Este capítulo explica cómo integrar OpenSyn con Visual Studio Code. Aprenderás a instalar la extensión, configurarla y usar las funciones de IA directamente desde tu editor.

La integración con VS Code permite acceder a OpenSyn sin salir de tu entorno de desarrollo favorito.

<!-- cumple Manual 7 §4.1 -->

## 1. Instalación de la Extensión

### Desde Marketplace

```bash
# Instalar desde línea de comandos
code --install-extension synapse.opensyn
```

O busca "Synapse/OpenSyn" en la sección de extensiones de VS Code.

### Desde el instalador

Si instalaste OpenSyn con el instalador unificado, la extensión se instala automáticamente.

## 2. Configuración

### Configuración Inicial

La primera vez que abres VS Code después de instalar OpenSyn, la extensión:

1. Verifica que el servidor de inferencia está corriendo
2. Si no, inicia el orquestador automáticamente
3. Carga la configuración desde `~/.opensyn/config.toml`

### Archivo de Configuración VS Code

```jsonc
// .vscode/settings.json
{
    "synapse.opensyn.modelo": "codellama-7b-Q4_K_M",
    "synapse.opensyn.temperature": 0.3,
    "synapse.opensyn.maxTokens": 2048,
    "synapse.opensyn.language": "es",
    "synapse.opensyn.autoValidate": true,
    "synapse.opensyn.maxRetries": 3
}
```

### Configuración de Snippets

```jsonc
// .vscode/snippets/synapse.json
{
    "Función Synapse": {
        "prefix": "func",
        "body": [
            "funcion ${1:nombre}(${2:parametros}) -> ${3:tipo}:",
            "    ${4:retornar}",
            ""
        ],
        "description": "Función Synapse con contratos"
    },
    "Estructura Syquex": {
        "prefix": "struct",
        "body": [
            "estructura ${1:Nombre}:",
            "    ${2:campos}",
            "",
            "    crear(${3:parametros}):",
            "        self.${4:campo} = ${4:campo}",
            ""
        ],
        "description": "Estructura Syquex con constructor"
    }
}
```

## 3. Panel de OpenSyn

### Barra de Estado

La barra de estado muestra el estado de OpenSyn:

```
[🤖 OpenSyn: ✅ conectado] [Modelo: codellama-7b] [Temp: 0.3]
```

### Panel de Control

Accede al panel de OpenSyn desde `View → Command Palette → "OpenSyn: Panel de Control"`:

- Estado del servidor de inferencia
- Modelo cargado y uso de VRAM
- Historial de conversaciones
- Configuración rápida

## 4. Comandos Disponibles

### Comandos del Palette

| Comando | Descripción | Atajo por defecto |
|---------|-------------|-------------------|
| `OpenSyn: Explicar Código` | Explica el código seleccionado | `Ctrl+Shift+E` |
| `OpenSyn: Completar Código` | Completa el código bajo el cursor | `Ctrl+Shift+G` |
| `OpenSyn: Corregir Error` | Sugiere correcciones para errores | `Ctrl+Shift+F` |
| `OpenSyn: Refactorizar` | Refactoriza el código seleccionado | `Ctrl+Shift+R` |
| `OpenSyn: Transpilar` | Transpila entre lenguajes | `Ctrl+Shift+T` |
| `OpenSyn: Generar Bindings` | Genera bindings desde header C | `Ctrl+Shift+B` |
| `OpenSyn: Estado` | Ver estado de OpenSyn | - |
| `OpenSyn: Cambiar Modelo` | Seleccionar modelo de IA | - |

### Menú Contextual

Haz clic derecho en el código para acceder a:

- **OpenSyn: Explicar selección** — Explica el código seleccionado
- **OpenSyn: Completar** — Completa el código bajo el cursor
- **OpenSyn: Refactorizar → Renombrar** — Refactoriza con IA
- **OpenSyn: Refactorizar → Extraer función** — Extrae función con IA
- **OpenSyn: Transpilar → A Syquex** — Transpila a Syquex
- **OpenSyn: Transpilar → A Synapse** — Transpila a Synapse

## 5. Autocompletado Inteligente

OpenSyn proporciona autocompletado contextual que:

- Entiende el AST del archivo actual
- Considera los imports y símbolos definidos
- Sugiere código válido según la sintaxis Synapse/Syquex

```syquex
// Escribe "fun" y presiona Ctrl+Space
// OpenSyn sugiere:
// función sumar(a: entero, b: entero) -> entero:
//     retornar a + b
```

### Autocompletado con Validación

El código generado se valida automáticamente:

1. OpenSyn genera el código
2. El LSP valida con `synapse check --no-emit`
3. Si es válido, se muestra como sugerencia
4. Si falla, se activa el bucle de corrección

## 6. Explicación de Código

### Seleccionar texto y explicar

Selecciona cualquier fragmento de código y presiona `Ctrl+Shift+E`:

```syquex
funcion factorial(n: entero) -> entero:
    si n <= 1:
        retornar 1
    retornar n * factorial(n - 1)
```

OpenSyn mostrará:
> Esta función calcula el factorial de `n` usando recursión. Si `n` es menor o igual a 1, retorna 1 (caso base). De lo contrario, retorna `n` multiplicado por el factorial de `n-1` (caso recursivo).

## 7. Refactorización con IA

### Comandos de Refactorización

```syquex
// Antes: Código duplicado
funcion calcular_area_rectangulo(ancho: entero, alto: entero) -> entero:
    retornar ancho * alto

funcion calcular_perimetro_rectangulo(ancho: entero, alto: entero) -> entero:
    retornar 2 * (ancho + alto)

funcion calcular_diagonal_rectangulo(ancho: entero, alto: entero) -> decimal:
    retornar raiz_cuadrada(ancho * ancho + alto * alto)
```

Presiona `Ctrl+Shift+R` y pide:
> "Extrae una estructura Rectangulo con métodos area(), perimetro(), diagonal()"

```syquex
// Después: Refactorizado
estructura Rectangulo:
    ancho: entero
    alto: entero
    
    crear(ancho: entero, alto: entero):
        self.ancho = ancho
        self.alto = alto
    
    metodo area() -> entero:
        retornar self.ancho * self.alto
    
    metodo perimetro() -> entero:
        retornar 2 * (self.ancho + self.alto)
    
    metodo diagonal() -> decimal:
        retornar raiz_cuadrada(self.ancho * self.ancho + self.alto * self.alto)
```

## 8. Configuración de Atajos Personalizados

```jsonc
// .vscode/keybindings.json
[
    {
        "key": "ctrl+shift+e",
        "command": "synapse.aiExplain",
        "when": "editorTextFocus"
    },
    {
        "key": "ctrl+shift+g",
        "command": "synapse.aiComplete",
        "when": "editorTextFocus"
    },
    {
        "key": "ctrl+shift+f",
        "command": "synapse.aiFix",
        "when": "editorTextFocus"
    },
    {
        "key": "ctrl+shift+r",
        "command": "synapse.aiRefactor",
        "when": "editorTextFocus"
    }
]
```

## 9. Configuración de Modelo por Proyecto

```jsonc
// .vscode/settings.json (por proyecto)
{
    "synapse.opensyn.modelo": "synapse-fine-tuned-7b-Q4_K_M",
    "synapse.opensyn.language": "es",
    "synapse.opensyn.autoValidate": true,
    "synapse.opensyn.maxRetries": 3
}
```

## 10. Extension Packs

### Synapse Extension Pack

Instala el paquete completo:

```bash
code --install-extension synapse.synapse-pack
```

Incluye:
- Synapse Language Support
- OpenSyn AI Assistant
- Synapse Debugger
- Synapse Test Runner

## 11. Temas y Personalización

### Tema de Colores

OpenSyn respeta el tema de colores de VS Code. Para temas oscuros:

```jsonc
// .vscode/settings.json
{
    "workbench.colorTheme": "Synapse Dark",
    "synapse.opensyn.panelBackground": "#1e1e1e",
    "synapse.opensyn.panelBorder": "#454545"
}
```

### Personalizar Respuestas

```jsonc
{
    "synapse.opensyn.explainStyle": "detallado",  // "breve", "detallado", "ejemplos"
    "synapse.opensyn.fixStyle": "seguro",        // "seguro", "agresivo"
    "synapse.opensyn.completionMode": "aceptar"   // "aceptar", "mostrar", "insertar"
}
```

## 12. Diagnóstico y Solución de Problemas

### Ver Estado

```bash
# Ver estado desde VS Code
Ctrl+Shift+P → "OpenSyn: Estado"
```

### Logs de Diagnóstico

```bash
# Guardar logs para soporte
Ctrl+Shift+P → "OpenSyn: Guardar Diagnóstico"
```

### Reinicio del Servidor

```bash
# Reiniciar servidor de inferencia
Ctrl+Shift+P → "OpenSyn: Reiniciar Servidor"
```

## Referencias

- **Manual 7 §4.1**: Comandos personalizados del LSP
- **Manual 7 §6.1**: Instalación de OpenSyn
- **Manual 7 §6.2**: Configuración del modelo
- **Manual 8 §1**: Herramientas de desarrollo (VS Code, LSP)

// cumple Manual 7 §4.1
