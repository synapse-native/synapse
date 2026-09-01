# Modelos de IA en OpenSyn

Este capítulo describe los modelos de inteligencia artificial utilizados por OpenSyn. Aprenderás sobre los diferentes modelos disponibles, sus capacidades y cuándo usar cada uno.

OpenSyn utiliza modelos de vanguardia para generar código, explicar programas y asistir en el desarrollo.

<!-- cumple Manual 7 §3.1 -->

## 1. Modelos Soportados

OpenSyn soporta modelos en formato **GGUF** (cuantizados) de las siguientes familias:

### Tabla de Modelos

| Modelo | Tamaño | Cuantización | VRAM necesaria | Bueno para |
|--------|--------|--------------|----------------|------------|
| DeepSeek Coder 1.3B | 1.3B | Q4_K_M | < 4 GB | Código básico, autocompletado |
| CodeLlama 7B | 7B | Q4_K_M | 4-6 GB | Código general, explicaciones |
| CodeLlama 7B | 7B | Q5_K_M | 6-8 GB | Código de alta calidad |
| CodeLlama 13B | 13B | Q4_K_M | 8-12 GB | Código complejo, razonamiento |
| CodeLlama 34B | 34B | Q4_K_M | 12-18 GB | Tareas avanzadas, depuración |
| Synapse‑Fine‑tuned | 7B | Q4_K_M | 4-6 GB | Especializado en Synapse/Syquex |

## 2. Selección Automática Basada en Hardware

El instalador de OpenSyn detecta automáticamente tu hardware y selecciona el modelo apropiado:

### Reglas de Selección

```syquex
// Del instalador (Manual 7 §2.5)
funcion seleccionar_modelo(hw: HardwareInfo) -> ModeloInfo:
    let modelos = modelos_toml_leer()  // Desde modelos.toml
    
    si hw.vram_total < 4 * 1024 * 1024 * 1024:
        retornar modelos["deepseek-coder-1.3b-Q4_K_M"]
    
    si hw.vram_total < 6 * 1024 * 1024 * 1024:
        retornar modelos["codellama-7b-Q4_K_M"]
    
    si hw.vram_total < 12 * 1024 * 1024 * 1024:
        retornar modelos["codellama-13b-Q4_K_M"]
    
    retornar modelos["codellama-34b-Q4_K_M"]
```

### VRAM Necesaria por Modelo

| GPU | VRAM Disponible | Modelo Recomendado |
|-----|-----------------|-------------------|
| Sin GPU | N/A | DeepSeek Coder 1.3B |
| NVIDIA GTX 1050/1650 | 4 GB | DeepSeek Coder 1.3B |
| NVIDIA GTX 1660/RTX 3060 | 6 GB | CodeLlama 7B (Q4_K_M) |
| NVIDIA RTX 3070/4060 | 8 GB | CodeLlama 7B (Q5_K_M) |
| NVIDIA RTX 3080/4070 | 12 GB | CodeLlama 13B (Q4_K_M) |
| NVIDIA RTX 4090 | 24 GB | CodeLlama 34B (Q4_K_M) |
| Apple M1/M2 | 8 GB unificado | CodeLlama 7B (Q4_K_M) |
| Apple M2 Pro/Max | 16-32 GB | CodeLlama 13B (Q4_K_M) |

## 3. Niveles de Cuantización

La cuantización reduce el tamaño del modelo y acelera la inferencia:

| Nivel | Precisión | Tamaño relativo | Calidad | Recomendado para |
|-------|-----------|-----------------|---------|------------------|
| Q2_K | 2 bits | 10% | Baja | Hardware muy limitado |
| Q3_K | 3 bits | 15% | Media-baja | RAM < 4 GB |
| Q4_K_M | 4 bits | 25% | Media-alta | 4-8 GB VRAM |
| Q5_K_M | 5 bits | 30% | Alta | 8-12 GB VRAM |
| Q6_K | 6 bits | 35% | Muy alta | 12-16 GB VRAM |
| FP16 | 16 bits | 100% | Original | GPU de alta gama |

### Implementación en C

```c
// opensyn/quantization.h
int quantize_model(const char* input_path, const char* output_path, int quant_type);
// quant_type: Q4_K_M, Q5_K_M, Q6_K, etc.
```

## 4. Fine-Tuning y Adaptación

OpenSyn permite fine-tunar modelos con datos propios para mejorar la precisión:

### LoRA (Low-Rank Adaptation)

```c
// opensyn/fine_tuning.h
typedef struct {
    float** lora_a;      // Matrices A (rank r)
    float** lora_b;      // Matrices B (rank r)
    int rank;            // Rango (típicamente 4, 8, 16)
    int num_layers;      // Número de capas a adaptar
} LoRALayer;

LoRALayer* lora_init(float** base_weights, int num_layers, int rank, float alpha);
void lora_forward(LoRALayer* layer, float* input, float* output);
void lora_update(LoRALayer* layer, float* gradient, float lr);
```

### Dataset de Fine-Tuning

```jsonl
{"instruction": "Escribe una función en Synapse que sume dos números.", "output": "funcion sumar(a: int, b: int) -> int:\n    retornar a + b"}
{"instruction": "Define una estructura 'Persona' con nombre y edad en Syquex.", "output": "estructura Persona:\n    nombre: texto\n    edad: entero\n    crear(nombre, edad):\n        self.nombre = nombre\n        self.edad = edad"}
```

### Pipeline de Fine-Tuning

1. Cargar el modelo base (ej. CodeLlama 7B GGUF)
2. Inicializar LoRA con rango `r=8` y `alpha=16`
3. Iterar sobre el dataset durante 3 épocas
4. Actualizar solo las matrices LoRA (el modelo base permanece congelado)
5. Guardar matrices LoRA en `.lora`
6. Para inferencia: combinar modelo base y LoRA en tiempo real

### Comando de Fine-Tuning

```bash
# Fine-tunear con un dataset
opensyn finetune --dataset dataset.jsonl --epochs 3 --rank 8

# Aplicar LoRA a un modelo existente
opensyn finetune --apply-lora modelo.gguf lora_weights.lora
```

## 5. Descarga e Instalación de Modelos

### Listar Modelos Disponibles

```bash
opensyn model --available
```

### Descargar un Modelo

```bash
# Descargar modelo por nombre
opensyn model --download codellama-7b-Q4_K_M

# Descargar con verificación automática
opensyn model --download --verify codellama-7b-Q4_K_M

# Descargar a directorio específico
opensyn model --download codellama-7b-Q4_K_M --output-dir ~/models
```

### Verificar Integridad

```bash
# Verificar SHA-256
opensyn model --verify codellama-7b-Q4_K_M.gguf

# Verificar firma Ed25519
opensyn verify --model codellama-7b-Q4_K_M.gguf
```

### Información del Modelo

```bash
opensyn model --info codellama-7b-Q4_K_M.gguf
# Muestra: tamaño, arquitectura, cuantización, hash SHA-256
```

## 6. Selección de Modelo Según Uso

### Para Generación de Código

- **Mejor calidad:** CodeLlama 13B Q5_K_M
- **Equilibrio:** CodeLlama 7B Q4_K_M
- **Velocidad:** DeepSeek Coder 1.3B Q4_K_M

### Para Explicaciones

- **Detalle:** CodeLlama 13B
- **Resumen:** DeepSeek Coder 1.3B

### Para Transpilación

- **Precisión:** Synapse-Fine-tuned 7B
- **Velocidad:** CodeLlama 7B

### Para Refactorización

- **Calidad:** CodeLlama 13B Q5_K_M
- **Velocidad:** CodeLlama 7B Q4_K_M

## 7. Configuración por Tipo de Tarea

```toml
[modelos]
# Modelo principal (generación de código)
principal = "codellama-7b-Q4_K_M"

# Modelo para explicaciones (más detallado)
explicacion = "codellama-13b-Q4_K_M"

# Modelo para autocompletado (más rápido)
autocomplete = "deepseek-coder-1.3b-Q4_K_M"

# Modelo fine-tuneado para Synapse/Syquex
synapse_ft = "synapse-fine-tuned-7b-Q4_K_M"

[router]
# Selección automática basada en instrucción
generate = "principal"
explain = "explicacion"
complete = "autocomplete"
refactor = "principal"
transpile = "synapse_ft"
```

## 8. Rendimiento de Inferencia

### Parámetros de Generación

```toml
[generacion]
temperature = 0.3      # 0.0 = determinista, 1.0 = creativo
max_tokens = 2048      # Límite de tokens generados
top_k = 40             # Nucleus sampling
top_p = 0.95           # Nucleus sampling
repetition_penalty = 1.1  # Penalizar repeticiones
```

### Optimización de Hardware

```bash
# Especificar número de hilos
opensyn status --set-threads 8

# Usar GPU (si está disponible)
opensyn model --set-gpu-layers 30

# Forzar CPU (para hardware con poca VRAM)
opensyn model --set-gpu-layers 0
```

## Referencias

- **Manual 7 §3.1**: Modelos soportados y tabla de VRAM
- **Manual 7 §3.2**: Fine-tuning con LoRA
- **Manual 7 §3.3**: Niveles de cuantización
- **Manual 7 §6.2**: Configuración del modelo
- **Manual 9 §5.2**: Tabla de selección de modelos según VRAM

// cumple Manual 7 §3
