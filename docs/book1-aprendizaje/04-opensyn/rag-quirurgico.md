# RAG Quirúrgico en OpenSyn

Este capítulo presenta la técnica de RAG (Retrieval-Augmented Generation) quirúrgico en OpenSyn. Aprenderás cómo OpenSyn recupera contexto relevante de tu proyecto para generar respuestas más precisas.

RAG quirúrgico permite a OpenSyn entender tu código base y generar soluciones específicas para tu proyecto.

<!-- cumple Manual 7 §2.3 -->

## 1. ¿Qué es RAG Quirúrgico?

RAG Quirúrgico es una técnica donde OpenSyn:

1. **Recupera** el contexto más relevante del proyecto usando análisis AST y RAG ligero
2. **Inyecta** reglas de sintaxis estáticas (no requiere fine-tuning)
3. **Genera** código ajustado específicamente al contexto del proyecto
4. **Valida** con el compilador real antes de mostrar al usuario

La diferencia con RAG tradicional es que OpenSyn no busca en documentos enteros, sino que extrae **solo** las líneas y símbolos relevantes al cursor.

## 2. Extracción de Contexto

### Contexto del AST

El pipeline RAG (`synapse_rag.c`) extrae del AST:

```c
// RagContext estructura (C)
typedef struct {
    char* archivo;              // Ruta del archivo
    char* contenido;            // Líneas extraídas (texto)
    int linea_inicio;           // Línea de inicio del contexto
    int linea_fin;              // Línea de fin del contexto
    char* nodo_ast;             // Representación JSON del AST
    char** diagnosticos;        // Diagnósticos activos
    int num_diagnosticos;
    char* idioma;               // "es", "en", "fr", "pt"
    char* instruccion;          // "Explica", "Completa", "Corrige", etc.
} RagContext;
```

### Ventana de Contexto

```toml
[rag]
contexto_lineas = 5     # Líneas antes/después del cursor
max_prompt_tokens = 1200 # 30% de n_ctx
max_generation_tokens = 2880  # 70% de n_ctx
```

## 3. Indexación del Proyecto

### Índice Local Ligero

OpenSyn construye un índice local de tu proyecto:

```text
Índice del proyecto (.opensyn/index/):
  - symbols.db: Símbolos (funciones, estructuras, imports)
  - types.db: Tipos definidos por el usuario
  - calls.db: Grafo de llamadas
  - docs.db: Comentarios y documentación
```

### Actualización Incremental

```bash
# El índice se actualiza automáticamente al guardar
# Para forzar actualización:
opensyn index --rebuild
```

## 4. Recuperación de Contexto

### Prioridades de Recuperación

1. **Líneas circundantes al cursor** (5 líneas por defecto)
2. **Nodo AST actual** (función/estructura bajo el cursor)
3. **Diagnósticos activos** (errores y warnings)
4. **Símbolos importados** (imports del archivo)
5. **Símbolos definidos en el proyecto** (búsqueda en índice)

### Ejemplo de Contexto Recuperado

```text
[CONTEXT]
Archivo: /proyecto/api.syq
Idioma: es
Líneas: 45 a 50

```syquex
estructura Pedido:
    items: Lista<ItemPedido>
    total: decimal

    metodo agregar_item(item: ItemPedido):
        // cursor aquí - línea 49
```
```

## 5. Negociación de Tokens

### Distribución de Contexto

```
n_ctx = 4096 tokens

Prompt:
├── System Rules: ~15% (600 tokens)
├── File location: ~5% (200 tokens)
├── AST node: ~25% (1000 tokens)
├── Diagnostics: ~10% (400 tokens)
├── Surrounding lines: ~45% (1768 tokens)

Generation: 70% = 2880 tokens
```

### Truncamiento Inteligente

Cuando el contexto excede el límite:

```c
// Prioridades de truncamiento (en orden)
1. System rules - NUNCA truncar
2. AST actual - Prioridad máxima
3. Diagnósticos - Prioridad alta
4. Líneas circundantes - Prioridad variable
5. Símbolos del proyecto - Prioridad baja
```

## 6. RAG Quirúrgico vs Fine-Tuning

| Aspecto | RAG Quirúrgico | Fine-Tuning |
|--------|---------------|-------------|
| **Hardware** | Funciona con modelos base | Requiere GPU potente |
| **Tiempo de configuración** | Inmediato | Horas/días |
| **Actualizaciones** | Automáticas | Requiere re-entrenamiento |
| **Precisión** | Alta (con contexto) | Muy alta (especializado) |
| **Flexibilidad** | Alta (por proyecto) | Baja (modelo estático) |

## 7. Configuración de RAG Quirúrgico

### Parámetros Avanzados

```toml
[rag]
# Ancho de ventana de contexto
contexto_lineas = 8

# Profundidad del AST
profundidad_ast = 3

# Incluir diagnosticos
incluir_diagnosticos = true

# Incluir imports
incluir_imports = true

# Cache de símbolos (TTL en minutos)
cache_ttl = 30

# Tamaño máximo del índice
index_max_size = "500MB"

# Exclusiones
exclude_patterns = ["*.log", "build/", "node_modules/"]
```

### Contexto por Tipo de Instrucción

```toml
[rag.instrucciones]
"explicar" = {
    contexto_lineas = 15,
    incluir_comentarios = true,
    nivel_detalle = "alto"
}

"generar" = {
    contexto_lineas = 5,
    incluir_comentarios = true,
    incluir_imports = true
}

"corregir" = {
    contexto_lineas = 10,
    incluir_diagnosticos = true,
    incluir_dependencias = true
}
```

## 8. Uso con Comandos

### CLI

```bash
# Generar con contexto quirúrgico
opensyn generate --context-aware "función que procese items"

# Explicar con contexto del proyecto
opensyn explain --project-context archivo.syq

# Refactorizar con conocimiento del codebase
opensyn refactor --project-aware archivo.syq
```

### Atajos de Teclado

| Atajo | Acción | Contexto |
|-------|--------|----------|
| `Ctrl+Shift+E` | Explicar | Incluye AST + imports |
| `Ctrl+Shift+G` | Completar | Incluye símbolos del scope |
| `Ctrl+Shift+F` | Corregir | Incluye diagnósticos |
| `Ctrl+Shift+R` | Refactorizar | Incluye todo el proyecto |

## 9. Métricas de Eficacia

### Hit Rate

```bash
# Ver métricas de RAG
opensyn rag-stats

# Salida:
# Tokens de contexto reutilizados: 65%
# Símbolos relevantes encontrados: 23/25
# Diagnósticos incluidos: 8/8
# Compresión del prompt: 2.3x
```

### Optimización de Ventana

```toml
[rag.optimizacion]
# Modo adaptativo: ajusta el contexto según complejidad
auto_ajustar = true

# Reservar más tokens para generación
preferir_generacion = true

# Comprimir contexto redundante
comprimir_contexto = true
```

## 10. Casos de Uso Avanzados

### Búsqueda de Patrones en el Código

```bash
# Encontrar patrones similares en el proyecto
opensyn search --pattern "manejo de errores" --semantico
```

### Documentación Automática

```bash
# Generar documentación con contexto del proyecto
opensyn explain --format markdown --include-context archivo.syq > docs/archivo.md
```

### Tests de Regresión

```bash
# Verificar que el código generado no rompe tests existentes
opensyn generate "función" --run-tests
```

## Referencias

- **Manual 7 §2.3**: Pipeline RAG y negociación de n_ctx
- **Manual 7 §2.4**: Enrutador y procesamiento de respuestas
- **Manual 7 §6.1**: Instalación y configuración
- **Manual 8 §4**: Integración LSP y comandos

// cumple Manual 7 §2.3
