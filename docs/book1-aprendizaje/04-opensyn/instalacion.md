# Instalación de OpenSyn

Este capítulo guía el proceso de instalación de OpenSyn paso a paso. Aprenderás a instalar, configurar y verificar que el asistente funciona correctamente en tu sistema.

Una instalación exitosa es el primer paso para aprovechar OpenSyn.

<!-- cumple Manual 7 §6.1 -->

## 1. Requisitos de Hardware

### Requisitos Mínimos

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| **CPU** | 4 núcleos | 8 núcleos |
| **RAM** | 8 GB | 16 GB |
| **GPU** | No requerida | NVIDIA RTX 3060+ |
| **VRAM** | 4 GB (si GPU) | 8 GB (si GPU) |
| **Almacenamiento** | 10 GB libre | 20 GB libre |

### Compatibilidad

- **Linux:** Ubuntu 20.04+, Debian 11+, Fedora 36+
- **macOS:** 10.15+ (Intel) o macOS 11+ (Apple Silicon)
- **Windows:** 10/11 (requiere WSL2 o MinGW)
- **GPU NVIDIA:** CUDA 11.8+ (para aceleración GPU)

## 2. Instalación desde el Instalador Oficial

### Opción 1: Instalador Unificado (Recomendado)

El instalador unificado de Synapse incluye la opción de instalar OpenSyn:

1. Descarga el instalador desde [GitHub Releases](https://github.com/synapse-dev/synapse/releases)
2. Ejecuta el instalador
3. Selecciona "Instalar Synapse + OpenSyn"
4. El instalador detecta tu hardware automáticamente

### Opción 2: Instalación desde el Código Fuente

```bash
# Clonar el repositorio
git clone https://github.com/synapse-dev/synapse.git
cd synapse

# Compilar el toolchain (S1)
python main.py --bootstrap

# Instalar OpenSyn
python main.py --install-opensyn
```

### Opción 3: Gestor de Paquetes

```bash
# En Linux (cuando esté disponible)
apt install synapse-opensyn  # Debian/Ubuntu
dnf install synapse-opensyn  # Fedora
```

## 3. Detectar Hardware

El instalador de OpenSyn detecta tu hardware automáticamente:

```syquex
// Del instalador (Manual 7 §2.5)
funcion detectar_hardware() -> HardwareInfo:
    retornar HardwareInfo(
        ram_total: os.memoria_total(),
        vram_total: os.vram_total(),
        cpu_nucleos: os.cpu_nucleos(),
        arquitectura: os.arquitectura()
    )
```

### Comando de detección

```bash
opensyn detect-hardware
```

Salida:
```
Hardware Detectado:
  CPU: AMD Ryzen 7 5800X (8 núcleos)
  RAM: 32 GB
  GPU: NVIDIA RTX 3070 (8 GB VRAM)
  OS: Linux x86_64
  Recomendación: CodeLlama 7B (Q5_K_M)
```

## 4. Selección y Descarga del Modelo

### Selección Automática

El instalador selecciona el modelo según tu VRAM:

```syquex
funcion seleccionar_modelo(hw: HardwareInfo) -> ModeloInfo:
    let modelos = modelos_toml_leer()  // Desde modelos.toml
    si hw.vram_total < 4 * 1024 * 1024 * 1024:
        retornar modelos["deepseek-coder-1.3b-Q4_K_M"]
    si hw.vram_total < 6 * 1024 * 1024 * 1024:
        retornar modelos["codellama-7b-Q4_K_M"]
    // ... más casos
```

### Selección Manual

```bash
# Listar modelos disponibles
opensyn model --available

# Descargar modelo específico
opensyn model --download codellama-7b-Q5_K_M
```

## 5. Verificación de Integridad

### SHA-256

```bash
opensyn model --verify codellama-7b-Q5_K_M.gguf
```

### Firma Ed25519

```bash
opensyn verify --model codellama-7b-Q5_K_M.gguf
```

## 6. Configuración Inicial

Después de la instalación, se crea el archivo de configuración:

```toml
# ~/.opensyn/config.toml
[general]
idioma = "es"
editor = "vscode"

[modelo]
nombre = "codellama-7b-Q5_K_M"
ruta = "~/.opensyn/models/codellama-7b-Q5_K_M.gguf"
n_ctx = 4096
n_threads = 8
n_gpu_layers = 30
temperature = 0.3

[server]
puerto = 8088
host = "127.0.0.1"
timeout = 30
```

## 7. Prueba de Humo

El instalador ejecuta una prueba de humo para verificar:

1. El modelo se carga correctamente
2. El servidor de inferencia responde
3. Una inferencia simple funciona

```bash
opensyn status
```

Salida esperada:
```
Estado: ✅ Listo
Modelo: codellama-7b-Q5_K_M
VRAM: 6.2 GB / 8 GB
Inferencia: Funcionando
```

## 8. Verificación Final

### Compilar y ejecutar un programa de prueba

```syquex
#lang: es
importar lib.io

funcion principal():
    io.escribir_linea("OpenSyn está listo!")
```

```bash
python main.py hola.syq
./hola.exe  # Debería imprimir "OpenSyn está listo!"
```

### Probar comandos de OpenSyn

```bash
# Generar código
opensyn generate "función que calcule el factorial en Syquex"

# Explicar código
opensyn explain hola.syq
```

## 9. Solución de Problemas Comunes

### Error: No se detecta GPU

```text
Problema: OpenSyn instala modelo en CPU solamente
Solución: Instalar drivers NVIDIA y CUDA
  Ubuntu: sudo apt install nvidia-driver nvidia-cuda-toolkit
  Windows: Instalar NVIDIA Driver + CUDA desde nvidia.com
  macOS: OpenSyn usa Metal (no requiere CUDA)
```

### Error: VRAM insuficiente

```text
Problema: El modelo no cabe en VRAM
Solución: Descargar una versión más cuantizada
  opensyn model --download deepseek-coder-1.3b-Q4_K_M
  Configurar n_gpu_layers = 0 (usar solo CPU)
```

### Error: Modelo corrupto

```text
Problema: El modelo descargado está corrupto
Solución: Verificar y re-descargar
  opensyn verify --model modelo.gguf
  # Si falla:
  opensyn model --download --force modelo
```

## 10. Configuración del Editor

### VS Code

```bash
# Instalar extensión
code --install-extension synapse.opensyn
```

### Vim

```vim
Plug 'synapse-dev/vim-syquex'
```

### Emacs

```elisp
(use-package synapse-mode
  :ensure t)
```

## Referencias

- **Manual 7 §6.1**: Instalación de un solo clic
- **Manual 7 §2.5**: Instalador y detección de hardware
- **Manual 7 §6.2**: Configuración del modelo
- **Manual 7 §7.1**: Pruebas de instalación

// cumple Manual 7 §6.1
