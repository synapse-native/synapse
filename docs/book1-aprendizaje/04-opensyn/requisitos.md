# Requisitos de Hardware de OpenSyn

Este capítulo lista los requisitos del sistema para ejecutar OpenSyn, incluyendo hardware, software y dependencias. Aprenderás a preparar tu entorno antes de la instalación.

Cumplir con los requisitos garantiza una experiencia óptima con OpenSyn.

<!-- cumple Manual 7 §1.1 -->

## 1. Requisitos de Hardware

### 1.1. GPU (Recomendado)

OpenSyn puede funcionar con o sin GPU. Sin embargo, una GPU permite:

- Velocidades de inferencia significativamente más rápidas
- Capacidad de usar modelos más grandes
- Reducción en el uso de RAM

#### GPUs Soportadas

| Fabricante | GPU | VRAM Mínima | Comentarios |
|-----------|-----|-------------|-------------|
| NVIDIA | RTX 3060 | 4 GB | Mínimo recomendado para modelos 7B |
| NVIDIA | RTX 3070/4060 | 8 GB | Recomendado para modelos 7B Q5 |
| NVIDIA | RTX 3080/4070 | 12 GB | Ideal para modelos 13B |
| NVIDIA | RTX 4090 | 24 GB | Máximo rendimiento |
| AMD | RX 6000+ | 8 GB | Soporte limitado (Vulkan) |
| Apple | M1/M2 | 8 GB | Memoria unificada |
| Apple | M2 Pro/Max | 16-32 GB | Óptimo para modelos grandes |

#### Requisitos de NVIDIA

- **CUDA:** Versión 11.8 o superior
- **Driver:** 525.0+ o superior
- **cuDNN:** Versión 8.x

#### Instalación de Drivers (Linux)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nvidia-driver-535 nvidia-cuda-toolkit

# Fedora
sudo dnf install akmod-nvidia xorg-x11-drv-nvidia-cuda

# Verificar instalación
nvidia-smi
```

#### Instalación de Drivers (Windows)

```powershell
# Usar Chocolatey
choco install nvidia-driver nvidia-cuda

# O descargar desde nvidia.com
```

### 1.2. CPU

| Requisito | Mínimo | Recomendado |
|-----------|--------|-------------|
| Núcleos | 4 | 8+ |
| Instrucciones | AVX2 | AVX2 + AVX-512 |
| Arquitectura | x86_64, ARM64 | - |

### 1.3. Memoria RAM

| Modelo | VRAM | RAM Mínima | RAM Recomendada |
|--------|------|------------|-----------------|
| 1.3B | < 1 GB | 8 GB | 16 GB |
| 7B | 4-8 GB | 16 GB | 32 GB |
| 13B | 8-12 GB | 16 GB | 32 GB |
| 34B | 12-18 GB | 32 GB | 64 GB |

### 1.4. Almacenamiento

| Necesidad | Mínimo | Recomendado |
|----------|--------|-------------|
| Almacenamiento total | 20 GB | 50 GB |
| Tipo | SSD recomendado | NVMe SSD |
| Velocidad de lectura | 500 MB/s | 3 GB/s+ |

## 2. Requisitos de Software

### 2.1. Sistemas Operativos Soportados

| Sistema | Versión | Soporte GPU | Comentarios |
|---------|---------|-------------|-------------|
| **Linux** | Ubuntu 20.04+, Debian 11+, Fedora 36+ | ✅ | Completo |
| **macOS** | 10.15+ (Intel), 11+ (Apple Silicon) | ✅ (Metal) | Completo |
| **Windows** | 10, 11 (con WSL2) | ✅ | Recomendado WSL2 |
| **Windows** | 10, 11 (nativo) | Limitado | Requiere MinGW |

### 2.2. Dependencias del Sistema

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y \
    build-essential \
    cmake \
    git \
    python3 \
    python3-pip \
    curl \
    wget \
    libssl-dev \
    zlib1g-dev
```

#### macOS

```bash
# Xcode Command Line Tools
xcode-select --install

# Homebrew
brew install cmake python git curl
```

#### Windows (WSL2)

```powershell
# Instalar WSL2
wsl --install

# Dentro de WSL2
sudo apt update
sudo apt install -y build-essential cmake python3 git
```

### 2.3. Dependencias de Python

```bash
pip install -r requirements.txt

# Requisitos principales:
# numpy>=1.24.0
# requests>=2.31.0
# pyyaml>=6.0
# pathlib>=1.0
```

## 3. Verificación de Compatibilidad

### 3.1. Script de Detección

```bash
opensyn detect-hardware
```

Salida de ejemplo:
```
🔍 Detectando hardware...

CPU: AMD Ryzen 7 5800X (8 núcleos, 16 hilos)
RAM: 32.0 GB (DDR4-3200)
GPU: NVIDIA GeForce RTX 3070 (8.0 GB VRAM)
  - CUDA: 12.2
  - Driver: 535.183.05
OS: Ubuntu 22.04.4 LTS (x86_64)
SSD: 1.5 TB (NVMe, 3.5 GB/s lectura)

✅ Hardware compatible
✅ GPU detectada y funcional
✅ VRAM suficiente para modelos 7B

💡 Recomendación: CodeLlama 7B (Q5_K_M)
```

### 3.2. Verificación Manual

#### Comprobar CPU (Linux)

```bash
lscpu
# Verificar: avx2 (debe mostrar "avx2")
```

#### Comprobar GPU (NVIDIA)

```bash
nvidia-smi
# Verificar: CUDA Version, GPU-Util
```

#### Comprobar Memoria

```bash
free -h
# Verificar: Mem available >= 16GB para modelos 13B+
```

#### Comprobar Almacenamiento

```bash
df -h /
# Verificar: espacio disponible >= 20GB
```

## 4. Modelos Recomendados por Hardware

| VRAM | Modelo Recomendado | Calidad | Velocidad |
|------|-------------------|---------|-----------|
| < 4 GB | DeepSeek Coder 1.3B | Media | ⚡⚡⚡⚡ |
| 4-6 GB | CodeLlama 7B (Q4_K_M) | Alta | ⚡⚡⚡ |
| 6-8 GB | CodeLlama 7B (Q5_K_M) | Muy Alta | ⚡⚡ |
| 8-12 GB | CodeLlama 13B (Q4_K_M) | Muy Alta | ⚡ |
| 12-18 GB | CodeLlama 34B (Q4_K_M) | Máxima | ⚡ |
| > 18 GB | CodeLlama 34B (FP16) | Máxima | ⚡ |

### Sin GPU (CPU only)

```bash
# Configuración para CPU
opensyn config --set modelo.n_gpu_layers=0
opensyn config --set modelo.temperature=0.2

# Modelo recomendado: DeepSeek Coder 1.3B
opensyn model --download deepseek-coder-1.3b-Q4_K_M
```

## 5. Configuración de VRAM

### Autoajuste de Capas GPU

```bash
# Configurar número de capas en GPU (automático)
opensyn config --auto-gpu-layers

# Configuración manual
opensyn config --set modelo.n_gpu_layers=30
```

### Umbrales de VRAM

| Uso VRAM | Estado | Acción |
|---------|--------|--------|
| < 50% | Óptimo | Sin acción necesaria |
| 50-80% | Normal | Funciona normalmente |
| 80-90% | Elevado | Considerar modelo más pequeño |
| > 90% | Crítico | Reducir capas GPU o cambiar modelo |

## 6. Requisitos Específicos por Sistema

### Windows (nativo)

```powershell
# Requerimientos adicionales:
# - Visual Studio 2022 (Build Tools)
# - Windows SDK 10.0.19041+
# - WSL2 recomendado para rendimiento

# Verificar:
systeminfo | findstr "OS Name"
where cmake
python --version
```

### Apple Silicon (M1/M2)

```bash
# OpenSyn usa Metal Performance Shaders (MPS)
# No requiere CUDA

# Verificar:
system_profiler SPDisplaysDataType | grep "Apple M"
```

### Docker (entorno aislado)

```dockerfile
FROM synquex/base:latest

# Verificar GPU (si GPU passthrough)
RUN nvidia-smi

# Configurar entorno
ENV OPENSYN_MODEL_DIR=/models
ENV OPENSYN_CONFIG_DIR=/config
```

## 7. Benchmark de Hardware

### Medición de Rendimiento

```bash
opensyn benchmark --model codellama-7b-Q4_K_M

# Resultados:
# Inferencia: 23.4 tokens/s
# Latencia p95: 1.2s
# VRAM usada: 5.2 GB
```

### Comparativa de Modelos

```bash
opensyn benchmark --compare deepseek-coder-1.3b, codellama-7b, codellama-13b
```

## 8. Resolución de Problemas de Hardware

### GPU No Detectada

1. Verificar drivers instalados
2. Reiniciar el sistema después de instalar drivers
3. Comprobar permisos del usuario
4. Verificar CUDA_VISIBLE_DEVICES

### VRAM Insuficiente

```bash
# Reducir capas GPU
opensyn config --set modelo.n_gpu_layers=20

# Usar modelo más pequeño
opensyn model --download deepseek-coder-1.3b-Q4_K_M
```

### Memoria RAM Limitada

```bash
# Limitar uso de memoria
opensyn config --set recurso.max_memoria="12GB"
opensyn config --set modelo.n_threads=4  # Reducir hilos
```

## 9. Certificaciones de Hardware

| Hardware | Estado | Notas |
|----------|--------|-------|
| NVIDIA RTX 3060-4090 | ✅ Certificado | Soporte completo CUDA |
| NVIDIA A100/H100 | ✅ Certificado | Servidor, excelente rendimiento |
| AMD RX 6000+ | ⚠️ Beta | Soporte Vulkan limitado |
| Apple M1/M2 | ✅ Certificado | Metal, rendimiento excelente |
| CPU Intel/AMD | ✅ Soportado | Sin aceleración GPU |

## 10. Requisitos de Red

### Sin conexión (Air-gapped)

```toml
[privacy]
modo_airgap = true
almacenar_feedback = false
cache_local = false
```

### Modelos offline

```bash
# Descargar modelos en una máquina con internet
opensyn model --download codellama-7b-Q4_K_M

# Transferir a USB
# Importar en máquina aislada
opensyn model --import codellama-7b-Q4_K_M.gguf
```

## Referencias

- **Manual 7 §1.1**: ¿Qué es OpenSyn? (características de hardware)
- **Manual 7 §2.5**: Instalador y detección de hardware
- **Manual 7 §3.1**: Modelos y VRAM necesaria
- **Manual 9 §5.2**: Tabla de selección de modelos

// cumple Manual 7 §3.1
