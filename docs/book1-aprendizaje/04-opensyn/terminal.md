# OpenSyn en Terminal

Este capítulo cubre el uso de OpenSyn desde la línea de comandos. Aprenderás a ejecutar comandos, interactuar con el asistente y automatizar tareas desde la terminal.

OpenSyn está disponible tanto como extensión de editor como herramienta CLI.

<!-- cumple Manual 7 §6.4 -->

## 1. Instalación de la CLI

### Verificar instalación

```bash
opensyn --version
```

Salida esperada:
```
OpenSyn v8.1.0-industrial
Modelo: codellama-7b-Q4_K_M
```

### Añadir al PATH

```bash
# En Linux/macOS
export PATH="$HOME/.opensyn/bin:$PATH"

# En Windows (PowerShell)
$env:PATH += ";$env:USERPROFILE\.opensyn\bin"
```

## 2. Estado y Diagnóstico

### Ver estado completo

```bash
opensyn status --detailed
```

Salida:
```
========================================
   ESTADO DE OPENSYN
========================================
Servidor: ✅ Conectado (localhost:8088)
Modelo: codellama-7b-Q5_K_M
Tamaño: 4.2 GB
VRAM: 6.1 GB / 8 GB
CPU: 8 hilos activos
Contexto: 4096 tokens
Temperature: 0.3

Última inferencia: 1.2s
Cache: 45 entradas
```

### Verificar conexión

```bash
opensyn ping
# Salida: PONG (latencia: 23ms)
```

## 3. Generación de Código

### Generar desde descripción natural

```bash
# Generar función en Syquex
opensyn generate --lang syquex "función que ordene una lista de enteros"

# Generar función en Synapse
opensyn generate --lang synapse "función que sume dos números"

# Generar con nivel de detalle
opensyn generate --detail high "API REST completa para gestionar usuarios"
```

### Opciones de generación

```bash
opensyn generate [OPCIONES] "instrucción"

OPCIONES:
  --lang LANG        Lenguaje objetivo (syquex, synapse, python, c)
  --detail LEVEL     Nivel de detalle (low, medium, high)
  --output ARCHIVO   Guardar en archivo
  --no-validate      Saltar validación con compilador
  --model MODELO     Usar modelo específico
  --temp FLOAT       Temperatura (0.0-1.0)
  --max-tokens N     Tokens máximos de salida
  --json             Salida en formato JSON
```

### Ejemplos prácticos

```bash
# Generar estructura
opensyn generate --lang syquex --output usuario.syq \
  "estructura Usuario con nombre, email, edad y método saludar()"

# Generar script de automatización
opensyn generate --lang syquex \
  "script que procese un CSV y genere un reporte JSON"

# Generar función con contratos (Synapse)
opensyn generate --lang synapse \
  "función en Synapse que valide un email con contrato requiere/garantiza"
```

## 4. Explicación de Código

### Explicar archivo

```bash
opensyn explain archivo.syq
opensyn explain archivo.syq --detail high
opensyn explain archivo.syq --format markdown
```

### Explicar desde stdin

```bash
echo 'funcion factorial(n: entero) -> entero: si n <= 1: retornar 1 retornar n * factorial(n - 1)' \
  | opensyn explain --lang syquex
```

### Explicar con preguntas

```bash
opensyn explain --ask "¿Qué hace el patrón matching en este código?" archivo.syq
```

## 5. Corrección de Errores

### Corregir error bajo el cursor (LSP)

```bash
# El LSP detecta errores de compilación y ofrece corrección
# Desde terminal, puedes validar y corregir:

opensyn check archivo.syq              # Solo validar
opensyn fix archivo.syq                 # Corregir automáticamente
opensyn fix --errors "ERR_SEM_*" archivo.syq  # Corregir errores específicos
```

### Validación con el compilador real

```bash
# El flag --check valida sin generar binario
python main.py --check archivo.syq

# Salida:
# ✅ Análisis léxico: OK
# ✅ Análisis sintáctico: OK
# ✅ Análisis semántico: OK
# ✅ Contratos: OK
# ✅ Ownership: OK
```

## 6. Transpilación

### Python → Syquex

```bash
# Transpilar archivo Python
opensyn transpile --from python script.py --to syquex

# Guardar salida
opensyn transpile --from python script.py --to syquex --output script.syq

# Transpilar con verificación
opensyn transpile --from python script.py --to syquex --validate
```

### C → Synapse

```bash
opensyn transpile --from c codigo.c --to synapse
opensyn transpile --from c codigo.c --to synapse --output codigo.syn
```

### Ver mapeo de tipos

```bash
opensyn transpile --help-mapping
```

Salida:
```
Mapeo Python → Syquex:
  def → funcion
  class → estructura
  self → self
  __init__ → crear
  list → Lista
  dict → Mapa
  try/except → intentar/atrapar o Resultado
```

## 7. Generación de Bindings

### C → Syquex

```bash
# Generar bindings desde header C
opensyn bindings --header libcurl.h --output lib/curl.syq

# Especificar lenguaje objetivo
opensyn bindings --header sqlite3.h --lang syquex --output sqlite.syq

# Con opción de generar wrappers de alto nivel
opensyn bindings --header libcurl.h --lang syquex --wrappers --output curl.syq
```

### Ver bindings generados

```bash
opensyn bindings --header ejemplo.h --preview
# Muestra el código generado sin escribirlo a disco
```

## 8. Modo Interactivo (REPL)

### Iniciar REPL

```bash
opensyn repl
```

### Comandos en REPL

```text
OpenSyn REPL v8.1.0 (es)  Tipo de ayuda para comandos disponibles.

>>> # Generar código
>>> generate "función que sume"
>>> 
funcion sumar(a: entero, b: entero) -> entero:
    retornar a + b

>>> # Explicar código
>>> explain "estructura Persona: nombre: texto"
>>>
Estructura Persona con un campo de texto 'nombre'

>>> # Transpilar
>>> transpile python "print('Hola')"
>>>
io.escribir_linea("Hola")

>>> exit
```

## 9. Automatización y Scripting

### Script de generación por lotes

```bash
#!/bin/bash
# generate_all.sh

archivos=(
    "validar_email"
    "parsear_json"
    "calcular_media"
)

for archivo in "${archivos[@]}"; do
    opensyn generate --lang syquex --output "${archivo}.syq" \
        "función Syquex que ${archivo}"
    
    # Validar generación
    python main.py --check "${archivo}.syq"
done

echo "Generación completada: ${#archivos[@]} archivos"
```

### Hook de Git pre-commit

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Validar archivos modificados con Synapse
for file in $(git diff --cached --name-only --diff-filter=ACM "*.syq" "*.syn"); do
    echo "Validando: $file"
    python main.py --check "$file"
    if [ $? -ne 0 ]; then
        echo "❌ Error de compilación en $file"
        exit 1
    fi
done

# Generar completions con OpenSyn para archivos nuevos
for file in $(git diff --cached --name-only --diff-filter=A "*.syq"); do
    opensyn generate --lang syquex --output "$file" \
        "Completa la implementación de $file"
done
```

## 10. Configuración desde Terminal

### Ver configuración

```bash
opensyn config --show
```

### Modificar configuración

```bash
# Cambiar modelo
opensyn config --set modelo.nombre="codellama-13b-Q4_K_M"

# Cambiar temperatura
opensyn config --set generacion.temperature=0.5

# Ver configuración efectiva
opensyn config --effective
```

### Exportar/Importar configuración

```bash
# Exportar configuración
opensyn config --export > mi_config.toml

# Importar configuración
opensyn config --import mi_config.toml
```

## 11. Comandos de Administración

### Gestión de modelos

```bash
# Listar modelos descargados
opensyn model --list

# Descargar nuevo modelo
opensyn model --download deepseek-coder-1.3b-Q4_K_M

# Eliminar modelo
opensyn model --remove deepseek-coder-1.3b-Q4_K_M

# Actualizar modelo
opensyn model --update codellama-7b-Q4_K_M
```

### Reiniciar servidor

```bash
opensyn server --restart
opensyn server --stop
opensyn server --start
```

## 12. Uso Avanzado

### Pipes y redirección

```bash
# Generar y validar en un pipeline
opensyn generate "función factorial" --lang syquex --output factorial.syq
python main.py --check factorial.syq && echo "✅ Válido"

# Generar documentación
opensyn explain archivo.syq --format markdown > documentacion.md

# Transpilar múltiples archivos
find . -name "*.py" -exec opensyn transpile --from python {} --to syquex --output {}.syq \;
```

### Integración con make

```makefile
# Makefile
.PHONY: build docs test

build:
	python main.py app.syq -o app.exe

docs:
	opensyn explain app.syq --format markdown > docs/api.md

test:
	opensyn generate --lang syquex "tests unitarios para $(MODULE)" --output tests/test_$(MODULE).syq
	python main.py --check tests/test_$(MODULE).syq

ai-complete:
	opensyn generate "Completa la función siguiente" --lang syquex
```

## Referencias

- **Manual 7 §6.4**: Comandos CLI de OpenSyn
- **Manual 7 §4.2**: Flujo de validación con compilador
- **Manual 8 §1**: CLI unificado de Synapse
- **Manual 7 §6.3**: Bucle de corrección automática

// cumple Manual 7 §6.4
