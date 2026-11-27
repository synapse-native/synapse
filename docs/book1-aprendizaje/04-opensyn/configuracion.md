# Configuración de OpenSyn

Este capítulo cubre las opciones de configuración de OpenSyn. Aprenderás a personalizar el comportamiento del asistente según tus preferencias y necesidades específicas.

Una buena configuración mejora significativamente la experiencia de uso.

<!-- cumple Manual 7 §6.2 -->

## 1. Archivo de Configuración

OpenSyn se configura mediante el archivo `~/.opensyn/config.toml`:

```toml
[general]
idioma = "es"
editor = "vscode"
validacion_automatica = true
```

## 2. Configuración del Modelo

### Selección de Modelo

```toml
[modelo]
nombre = "codellama-7b-Q4_K_M"
ruta = "~/.opensyn/models/codellama-7b-Q4_K_M.gguf"
n_ctx = 4096            # Tamaño de contexto (tokens)
n_threads = 8           # Número de hilos CPU
n_gpu_layers = 30       # Capas en GPU (0 = solo CPU)
temperature = 0.3       # 0.0 = determinista, 1.0 = creativo
max_tokens = 2048       # Tokens máximos de salida
```

### Multiples Modelos

```toml
[modelos]
principal = "codellama-7b-Q4_K_M"
respuesta = "deepseek-coder-1.3b-Q4_K_M"
explicacion = "codellama-13b-Q4_K_M"

[router]
# Usar modelo específico según el tipo de instrucción
"generar_codigo" = "principal"
"explicar" = "explicacion"
"recomendar" = "respuesta"
```

## 3. Configuración del Servidor

```toml
[server]
puerto = 8088           # Puerto del servidor llama-server
host = "127.0.0.1"      # Solo localhost (recomendado)
timeout = 30            # Timeout en segundos
reintentos = 3          # Número de reintentos
```

## 4. Configuración del Pipeline RAG

```toml
[rag]
contexto_lineas = 5     # Líneas antes/después del cursor
max_prompt_tokens = 1200  # Máximo tokens para el prompt (30% de n_ctx)
max_generation_tokens = 2880  # Máximo tokens para generación (70%)
```

## 5. Configuración de Privacidad

```toml
[privacy]
telemetría = false              # Desactivar telemetría
almacenar_feedback = false      # No guardar datos de feedback
cache_local = true              # Usar caché local
max_cache_size = 100            # Máximo 100 entradas en caché
modo_airgap = false             # Sin conexión a internet
```

## 6. Configuración de Rendimiento

```toml
[rendimiento]
# Límites de recursos
max_cpu_percent = 80
max_memoria = "8GB"
max_concurrent = 4              # Inferencias simultáneas

# Optimización de GPU
gpu_accelerado = true
precision = "f16"                 # fp16, bf16, q8_0
```

## 7. Configuración de Personalización

### Prompts del Sistema Personalizados

```toml
[prompts]
# Sobrescribir el system prompt base
system_custom = """
Eres un experto en desarrollo fullstack.
Prefieres usar arquitectura hexagonal.
Siempre usa tests.
"""

# Prompt para explicaciones
explain_style = "detallado"  # "breve", "detallado", "ejemplos"
```

### Reglas de Validación Personalizadas

```toml
[validacion]
# Archivos a excluir del contexto RAG
exclude_patterns = ["*.log", "node_modules/", ".git/"]

# Extensiones soportadas
supported_extensions = [".syq", ".syn", ".c", ".h", ".py", ".js"]

# Tiempo máximo de compilación (segundos)
compile_timeout = 10
```

## 8. Configuración por Proyecto

Puedes tener configuraciones específicas por proyecto usando un archivo `.opensyn.toml` en la raíz del proyecto:

```toml
# .opensyn.toml en proyecto_synapse/
[general]
idioma = "es"

[modelo]
nombre = "synapse-fine-tuned-7b"
# Usar modelo fine-tuneado para este proyecto

[prompts]
project_context = """
Este es un proyecto de Synapse v8.1.0.
Sigue las convenciones del proyecto:
- Usar #lang: es en todos los archivos
- Las funciones deben tener contratos requiere/garantiza
- Respeta el ownership explícito
"""
```

## 9. Variables de Entorno

También puedes configurar OpenSyn mediante variables de entorno:

```bash
export OPENSYN_MODEL="codellama-7b-Q4_K_M"
export OPENSYN_PORT=8088
export OPENSYN_TEMPERATURE=0.3
export OPENSYN_LANGUAGE="es"
export OPENSYN_CACHE_DIR="/tmp/opensyn_cache"
```

## 10. Configuración por Línea de Comandos

```bash
# Sobrescribir configuración temporalmente
opensyn generate "función" --model deepseek-coder-1.3b --temp 0.7

# Especificar directorio de config
opensyn status --config-dir ~/custom_config

# Ver configuración actual
opensyn config --show

# Validar configuración
opensyn config --validate
```

## 11. Preset de Configuración

### Preset: Máxima Calidad

```toml
# ~/.opensyn/presets/calidad_maxima.toml
[modelo]
nombre = "codellama-13b-Q5_K_M"
n_ctx = 8192
temperature = 0.2
max_tokens = 4096
```

```bash
opensyn generate "función" --preset calidad_maxima
```

### Preset: Máxima Velocidad

```toml
# ~/.opensyn/presets/velocidad_maxima.toml
[modelo]
nombre = "deepseek-coder-1.3b-Q4_K_M"
n_ctx = 2048
temperature = 0.3
max_tokens = 512
```

```bash
opensyn generate "función" --preset velocidad_maxima
```

## 12. Personalización Avanzada

### Plugins y Extensiones

```toml
[plugins]
# Plugin para análisis de código personalizado
analysis_plugin = "plugins/custom_analysis.py"

# Plugin para generación en lenguaje específico
generator_plugins = ["plugins/python_extras.py"]
```

### Hooks de Ciclo de Vida

```toml
[hooks]
# Antes de generar código
on_before_generate = "~/.opensyn/hooks/before_generate.sh"

# Después de compilar
on_after_compile = "~/.opensyn/hooks/after_compile.sh"

# Antes de mostrar al usuario
on_result_ready = "~/.opensyn/hooks/on_result.sh"
```

## 13. Verificación de Configuración

```bash
# Ver configuración actual
opensyn config --show

# Validar sintaxis
opensyn config --validate

# Ver configuración efectiva (incluyendo defaults)
opensyn config --effective

# Comparar con valores por defecto
opensyn config --diff-defaults
```

## Referencias

- **Manual 7 §6.2**: Archivo de configuración (`config.toml`)
- **Manual 7 §3.1**: Modelos soportados
- **Manual 7 §6.1**: Instalación de OpenSyn
- **Manual 8 §4.2**: CLI con flag `--check`

// cumple Manual 7 §6.2
