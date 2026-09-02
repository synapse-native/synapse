# Contexto Estático en OpenSyn

Este capítulo explica cómo OpenSyn maneja el contexto estático del proyecto: archivos, configuración y estructura. Aprenderás a configurar y optimizar el contexto para mejores resultados.

El contexto estático permite a OpenSyn entender la estructura y convenciones de tu proyecto.

<!-- cumple Manual 7 §2.3 -->

## 1. Inyección de Reglas de Sintaxis

OpenSyn **no** necesita un modelo fine-tuneado. En su lugar, inyecta un bloque de "Reglas de Sintaxis" en el **System Prompt** de cada consulta. Este bloque contiene la gramática esencial, el modelo de memoria y ejemplos de Synapse/Syquex.

### Plantilla del System Prompt

```
[SYSTEM]
Eres un experto en programación. Conoces Python, JavaScript, C, Rust y otros lenguajes.
Ahora te voy a enseñar dos lenguajes nuevos: **Synapse** (bajo nivel, sistemas) y **Syquex** (alto nivel, productividad).

# REGLAS DE SYNAPSE (Sintaxis Estricta)
- Funciones: `funcion nombre(parametros) -> tipo:`
- Variables: `let nombre = valor`
- Condicional: `si condicion:`
- Bucle: `mientras condicion:`
- Retorno con transferencia de ownership (move): `retornar -> variable`
- Concurrencia: `lanzar funcion()`
- Canales: `Canal<T>` y `canal <- valor`, `valor = canal ->`
- Tensores: `tensor(filas, columnas)`

# REGLAS DE SYQUEX (Sintaxis Flexible y Automática)
- Funciones: `funcion nombre(parametros) -> tipo:`
- Estructuras: `estructura Nombre: campo: tipo`
- Métodos: `metodo nombre(parametros) -> tipo:`
- Constructores: `crear(parametros):`
- Manejo de Errores: `Resultado<T, E>` y operador `?` (propaga errores).
- Concurrencia: `lanzar funcion()`
- Canales: `Canal<T>(capacidad)`
- Importar módulos: `importar lib.modulo`

Ahora responde a la siguiente instrucción en el lenguaje que te pida (Synapse o Syquex).
Genera SOLO el código, sin explicaciones adicionales.
```

## 2. Extracción de Contexto del AST

El RAG extrae información del AST del archivo actual:

### Información Extraída

| Tipo de Información | Fuente | Uso |
|---------------------|--------|-----|
| Nombres de funciones | AST `FuncionDef` | Referencias cruzadas |
| Tipos de datos | AST tipo | Verificación de tipos |
| Variables locales | AST `let` | Contexto de uso |
| Comentarios | Lexer/Parser | Documentación generada |
| Estructura de control | AST `si`/`para`/`coincidir` | Lógica comprendida |
| Imports/exports | AST `importar`/`@export` | Alcance del proyecto |
| Diagnósticos | LSP | Errores conocidos |

### Ejemplo de Serialización AST

```json
{
  "tipo": "FuncionDef",
  "nombre": "calcular_factorial",
  "parametros": [
    {"nombre": "n", "tipo": "entero"}
  ],
  "tipo_retorno": "entero",
  "contratos": null,
  "cuerpo": {
    "tipo": "Bloque",
    "sentencias": [
      {
        "tipo": "CondicionalSi",
        "condicion": "n <= 1",
        "cuerpo_si": "retornar 1"
      },
      {
        "tipo": "Retornar",
        "valor": "n * calcular_factorial(n - 1)"
      }
    ]
  }
}
```

## 3. Contexto de Archivo y Líneas Circundantes

### Configuración de Contexto

```toml
[rag]
contexto_lineas = 5     # Líneas antes/después del cursor
max_prompt_tokens = 1200  # 30% de n_ctx
max_generation_tokens = 2880  # 70% de n_ctx
```

### Extracción de Líneas

```c
// Estructura RagContext (C)
typedef struct {
    char* archivo;              // Ruta del archivo
    char* contenido;            // Líneas extraídas (texto)
    int linea_inicio;           // Línea de inicio del contexto
    int linea_fin;              // Línea de fin del contexto
    char* nodo_ast;             // Representación JSON del AST
    char** diagnosticos;        // Diagnósticos activos
    int num_diagnosticos;
    char* idioma;               // "es", "en", "fr", "pt"
    char* instruccion;          // Instrucción del usuario
} RagContext;
```

## 4. Negociación de n_ctx (Context Window)

### Política de Tokens

El RAG negocia el tamaño del contexto (`n_ctx`) con el modelo:

1. Lee `n_ctx` del modelo (por defecto 4096)
2. Reserva el **30% para el prompt** y el **70% para generación**
3. Si el prompt excede el 30%, se trunca priorizando:
   - Las líneas más cercanas al cursor
   - Los diagnósticos más relevantes (errores sobre warnings)
   - El nodo AST actual sobre el código circundante

### Truncamiento Inteligente

```c
PromptInfo rag_construir_prompt(RagContext* ctx, int n_ctx) {
    size_t max_prompt = n_ctx * 0.30;
    size_t max_generation = n_ctx * 0.70;
    
    // Priorizar contexto
    char* prompt = construir_prompt(
        system_rules,      // 15% del prompt
        file_location,     // 5%
        ast_actual,        // 25% - Prioridad alta
        diagnosticos,      // 10% - Errores prioritarios
        lineas_cercanas    // 45% - Prioridad variable
    );
    
    return (PromptInfo){
        .prompt_completo = prompt,
        .prompt_tokens = contar_tokens(prompt),
        .max_prompt_tokens = max_prompt,
        .max_generation_tokens = max_generation
    };
}
```

## 5. Archivos de Contexto Personalizados

Puedes añadir archivos de contexto personalizados:

```toml
[rag]
# Archivos adicionales a incluir en el contexto
context_files = [
    "docs/guia_estilo.md",
    "CONTRIBUTING.md",
    ".cursorrules"
]

# Exclusiones (archivos no relevantes)
exclude_patterns = [
    "*.log",
    "node_modules/",
    ".git/",
    "build/",
    "dist/"
]
```

### `.cursorrules` de Proyecto

```text
# Reglas para el proyecto Synapse
- Siempre usar #lang: es en archivos .syq
- Las funciones deben tener contratos requiere/garantiza
- Usar ownership explícito en Synapse
- Preferir composición sobre herencia en Syquex
```

## 6. Contexto por Tipo de Instrucción

El contexto puede variar según la instrucción del usuario:

```toml
[rag.instrucciones]
"explicar" = {
    lineas_contexto = 10,
    incluir_comentarios = true,
    nivel_detalle = "alto"
}

"generar" = {
    lineas_contexto = 5,
    incluir_comentarios = true,
    incluir_imports = true
}

"refactorizar" = {
    lineas_contexto = 15,
    incluir_diagnosticos = true,
    incluir_dependencias = true
}
```

## 7. Optimización del Prompt

### Compresión de Contexto

```syquex
// El RAG puede resumir código redundante
// Antes:
let codigo_largo = """
funcion configuracion_compleja():
    // 100 líneas de configuración...
"""

// En el prompt, el RAG genera:
// "configuración compleja con 100 líneas"
```

### Priorización de Símbolos

```c
// Los símbolos usados en las últimas 3 líneas tienen prioridad
// sobre símbolos definidos en líneas anteriores
typedef struct {
    char** priority_symbols;  // Símbolos del cursor + 2 líneas
    char** context_symbols;   // Símbolos del archivo actual
    char** project_symbols;   // Símbolos del proyecto (imports)
} SymbolPriority;
```

## 8. Configuración de Hardware

### Autoajuste Basado en VRAM

```toml
[rag]
# Ajuste automático según hardware
auto_ajustar = true

# Límites manuales
max_prompt_tokens = 2000
max_generation_tokens = 2048

# Para modelos pequeños (<4GB VRAM)
small_model_optimization = true
```

## 9. Ejemplo de Prompt Completo

```text
[SYSTEM]
Eres un experto en programación...

[CONTEXT]
Archivo: /proyecto/api.syq
Idioma: es
Líneas: 10 a 15
```syquex
funcion procesar_pedido(pedido: Pedido) -> Resultado<Factura, Error>:
    let items_validados = pedido.items.filtrar(lambda i: i.cantidad > 0)
    // cursor está aquí
```
Diagnósticos: ERR_SEM_TIPO_INCOMPATIBLE en línea 12

[INSTRUCCIÓN]
Completa la función procesar_pedido que valide items y genere una factura.
```

## Referencias

- **Manual 7 §2.3**: Pipeline RAG y negociación de n_ctx
- **Manual 7 §5.3**: Tipos de memoria especiales
- **Manual 2 §7**: Serialización del AST
- **Manual 8 §1**: LSP y diagnósticos

// cumple Manual 7 §2.3
