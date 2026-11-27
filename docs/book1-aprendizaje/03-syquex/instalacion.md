# Instalación de Syquex

Esta guía te ayuda a instalar Syquex en diferentes sistemas operativos. Syquex forma parte del ecosistema Synapse y comparte el mismo compilador y toolchain.

<!-- cumple Manual 3 §1.1 -->

## 1. Prerrequisitos

### Sistema Operativo

Syquex está disponible para:
- **Linux** (Ubuntu 20.04+, Debian 11+, Fedora 36+)
- **macOS** (10.15+ o macOS 11+)
- **Windows** (10/11 con WSL2 o nativo)

### Dependencias del Sistema

| Dependencia | Versión mínima | Propósito |
|-------------|----------------|-----------|
| GCC | 9.0+ | Compilación a C |
| Clang | 10.0+ | Alternativa a GCC |
| Python | 3.8+ | Build script (main.py) |
| Git | 2.20+ | Clonar repositorio |
| Make | 3.98+ | Automatización de builds |

### Verificación de Dependencias

```bash
gcc --version     # 9.0+
python --version  # 3.8+
git --version     # 2.20+
make --version    # 3.98+
```

## 2. Instalación en Linux

### Opción A: Instalación desde el repositorio oficial

```bash
# Clonar el repositorio (incluye Synapse + Syquex)
git clone https://github.com/synapse-dev/synapse.git
cd synapse

# Compilar el toolchain S1
python main.py --bootstrap

# Verificar instalación
python main.py --version
```

### Opción B: Instalación vía gestor de paquetes

```bash
# En Ubuntu/Debian (cuando esté disponible)
apt install synapse-lang
```

## 3. Instalación en macOS

```bash
# Requiere Homebrew
brew install gcc python@3.12 git make

# Clonar e instalar
git clone https://github.com/synapse-dev/synapse.git
cd synapse
python main.py --bootstrap
```

### Notas para Apple Silicon (M1/M2)

El compilador detecta automáticamente la arquitectura ARM64 y optimiza el código generado. No se requiere configuración adicional.

## 4. Instalación en Windows

### Opción A: WSL2 (Recomendado)

```bash
# En WSL2 (Ubuntu)
wsl --install
wsl
# Luego seguir las instrucciones de Linux
```

### Opción B: PowerShell con MinGW

```powershell
# Instalar MinGW-w64 para GCC
choco install mingw
# Instalar Python
choco install python
# Clonar e instalar
git clone https://github.com/synapse-dev/synapse.git
cd synapse
python main.py --bootstrap
```

## 5. Verificación de la Instalación

Después de instalar, verifica que todo funcione:

```bash
# Verificar versión del compilador
python main.py --version

# Compilar un programa de prueba
python main.py ejemplo.syq

# Ejecutar el binario generado
./ejemplo.exe  # o ./ejemplo en Linux/macOS
```

### Programa de Prueba

Crea `hola.syq`:

```syquex
#lang: es

importar lib.io

funcion principal():
    io.escribir_linea("¡Hola desde Syquex!")
```

Compílalo y ejecútalo:

```bash
python main.py hola.syq
./hola.exe
```

Deberías ver: `¡Hola desde Syquex!`

## 6. Configuración del Entorno (opcional)

### Variables de Entorno

```bash
export SYNAPSE_HOME="$HOME/.synapse"        # Directorio de configuración
export SYNAPSE_MODEL_PATH="/ruta/a/model.gguf" # Modelo de IA para OpenSyn
```

### Editor de Código

- **VS Code**: Extensión oficial "synapse-lang" (syntax highlighting, IntelliSense)
- **Vim**: Plugin synapse-vim
- **Emacs**: Modo synapse en melpa

## 7. Actualización

```bash
cd synapse
git pull origin main
python main.py --bootstrap --rebuild
```

## Problemas Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `ERR_LEX_MISSING_LANG` | Falta `#lang: es` en línea 1 | Agrega la directiva de idioma |
| `gcc: command not found` | GCC no instalado | Instala GCC 9.0+ |
| `UnicodeDecodeError` | Archivo con codificación incorrecta | Asegúrate de usar UTF-8 sin BOM |

## Referencias

- **Manual 1 §1**: Instalación del ecosistema
- **Manual 3 §1**: Directiva de idioma y codificación
- **Manual 7 §2**: Configuración de OpenSyn

// cumple Manual 3 §1
