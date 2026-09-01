# Refactorizar con OpenSyn

Este capítulo explora cómo usar OpenSyn para refactorizar código existente de forma segura. Aprenderás a identificar oportunidades de mejora y aplicar transformaciones manteniendo la corrección.

Refactorizar con IA permite mejorar la calidad del código de forma más rápida y segura.

<!-- cumple Manual 7 §6.3 -->

## 1. Identificación de Oportunidades

OpenSyn detecta automáticamente patrones de código que pueden beneficiarse de refactorización:

### Problemas Detectados

| Tipo de Problema | Símbolo | Ejemplo |
|-----------------|---------|---------|
| Duplicación de código | ⚠️ | Funciones con lógica repetida |
| Complejidad alta | ⚠️ | Funciones > 50 líneas |
| Violación de principios | ⚠️ | Funciones que hacen demasiado |
| Código muerto | ⚠️ | Variables/funciones no usadas |
| Nombres poco descriptivos | ⚠️ | Variables como `x`, `temp` |
| Deep nesting | ⚠️ | Anidación > 3 niveles |

### Detección Visual

```syquex
// Antes - Sin refactorizar
funcion procesar_pedido(pedido: Pedido) -> Resultado<Factura, Texto>:
    si pedido.item.len() == 0:
        retornar err("Carrito vacío")
    
    let subtotal = 0.0
    para item en pedido.item:
        let precio = obtener_precio(item.id)
        let descuento = 0.0
        si item.cantidad > 10:
            descuento = precio * 0.1
        subtotal = subtotal + (precio * item.cantidad) - descuento
    
    let iva = subtotal * 0.21
    let total = subtotal + iva
    
    // 15 líneas más de lógica...
    
    retornar ok(Factura(subtotal, iva, total))
```

## 2. Transformaciones Disponibles

### Extract Method (Extraer Función)

```
Prompt: "Extrae la lógica de cálculo de descuentos a una función separada"
```

```syquex
// Después
funcion calcular_descuento(item: Item, precio: decimal) -> decimal:
    si item.cantidad > 10:
        retornar precio * 0.1
    retornar 0.0

funcion procesar_pedido(pedido: Pedido) -> Resultado<Factura, Texto>:
    si pedido.item.len() == 0:
        retornar err("Carrito vacío")
    
    let subtotal = pedido.item
        .mapear(lambda item: 
            let precio = obtener_precio(item.id)
            retornar (precio * item.cantidad) - calcular_descuento(item, precio)
        )
        .reducir(lambda acc, x: acc + x, 0.0)
    
    retornar ok(Factura(subtotal, subtotal * 0.21))
```

### Rename (Renombrar)

```
Prompt: "Renombra 'pedido' a 'orden_compra' en esta función"
```

### Extract Variable

```
Prompt: "Extrae 'subtotal * 0.21' como variable 'iva'"
```

### Inline Method

```
Prompt: "Inlined la función obtener_nombre_completo() que solo retorna nombre + apellido"
```

## 3. Refactorización Segura

### Bucle de Validación

1. **Generación:** OpenSyn propone el refactoring
2. **Validación:** El LSP compila con `synapse check --no-emit`
3. **Tests:** Se ejecutan los tests existentes
4. **Diff:** Se muestra el cambio propuesto
5. **Confirmación:** El usuario acepta o rechaza

```bash
# Workflow de refactorización
opensyn refactor archivo.syq --type extract-function
# → Genera cambio propuesto
# → Valida con compilador
# → Ejecuta tests
# → Muestra diff
# → Pregunta: ¿Aplicar cambios? [Y/n]
```

### Prevenir Regresiones

```syquex
// OpenSyn mantiene compatibilidad de API
// Antes del refactoring:
funcion calcular_total(items: Lista<Item>) -> decimal

// El refactoring no puede cambiar:
// - La firma de la función (parametros/retorno)
// - El comportamiento observables
// - Las interfaces públicas
```

## 4. Tipos de Refactoring

### Organizacionales

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| Extract Function | Sacar código a función nueva | `calcular_iva()` |
| Inline Function | Incorporar función simple | Eliminar wrapper innecesario |
| Move Method | Mover método a otra estructura | Mover lógica de `Pedido` a `Factura` |
| Rename | Renombrar entidad | `temp` → `temperatura_actual` |
| Extract Variable | Convertir expresión en variable | `precio * cantidad` → `subtotal` |

### Estructurales

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| Extract Class | Dividir estructura grande | `Pedido` → `Pedido` + `Pago` |
| Move Field | Mover campo entre estructuras | `direccion` de `Usuario` a `Direccion` |
| Hide Delegate | Simplificar acceso indirecto | `pedido.get_cliente().get_nombre()` → `pedido.nombre_cliente()` |

### Lógicos

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| Replace Magic Number | Reemplazar constantes mágicas | `3.14159` → `constante PI` |
| Introduce Parameter Object | Agrupar parámetros | `(name, email, phone)` → `Contacto` |
| Replace Conditional with Polymorphism | Reemplazar condicionales con métodos virtuales | `switch tipo` → `metodo virtual` |

## 5. Refactoring con Contexto del Proyecto

OpenSyn utiliza el contexto del proyecto para sugerir refactorings:

```syquex
// En un proyecto con múltiples funciones de validación:
funcion validar_email(email: texto) -> booleano: ...
funcion validar_telefono(tel: texto) -> booleano: ...
funcion validar_direccion(dir: texto) -> booleano: ...

// OpenSyn sugiere:
// "Patrón detectado: funciones de validación similares"
// "Sugerencia: Crear una estructura Validator con métodos"
```

## 6. Configuración de Refactorización

```jsonc
// .vscode/settings.json
{
    "synapse.opensyn.refactorStyle": "safe",  // "safe" | "aggressive"
    "synapse.opensyn.autoValidate": true,
    "synapse.opensyn.runTests": true,
    "synapse.opensyn.maxRetries": 3
}
```

### Opciones de Refactorización

```bash
opensyn refactor [OPCIONES] archivo.syq

OPCIONES:
  --type TIPO       Tipo de refactoring (extract, inline, rename, etc.)
  --prompt TEXTO    Instrucción de refactoring
  --validate        Validar con compilador
  --run-tests       Ejecutar tests después
  --dry-run         Mostrar cambios sin aplicar
  --diff            Mostrar diff de cambios
```

## 7. Mejores Prácticas

### 1. Refactorizar en Pequeños Pasos

```text
❌ No: "Refactoriza toda esta clase"
✅ Sí: "Extrae la función calcular_total a un método separado"
```

### 2. Especifica el Alcance

```text
# Especifica el alcance exacto
"Refactoriza solo la función procesar_pedido, no tocar validar_email"
```

### 3. Usa Prompts Descriptivos

```text
# Bueno
"Extrae la lógica de cálculo de impuestos a una función separada, 
manteniendo la misma interfaz de la función original"

# Mejor
"Extrae el cálculo de 'subtotal * 0.21' como función obtener_iva(subtotal) -> decimal"
```

## 8. Seguimiento de Cambios

### Historial de Refactorizaciones

```bash
# Ver historial de refactorings aplicados
opensyn refactor --history

# Mostrar diff de un refactoring específico
opensyn refactor --show 2024-01-15-001
```

### Integración con Git

```bash
# El refactoring se aplica como un commit separado
opensyn refactor archivo.syq --prompt "..." --commit "refactor: extraer función calcular_iva"
```

## 9. Limitaciones

- No refactoriza código que no compila (debe estar primero válido)
- No puede cambiar APIs públicas sin confirmación explícita
- El refactoring conserva el comportamiento, no cambia funcionalidad
- No refactoriza código de bibliotecas externas

## 10. Ejemplo Completo

```syquex
# Antes
funcion calcular_precio_final(precio_base: decimal, categoria: texto, envio: booleano) -> decimal:
    let descuento = 0.0
    si categoria == "PREMIUM":
        descuento = precio_base * 0.15
    sino si categoria == "VIP":
        descuento = precio_base * 0.10
    sino si categoria == "NORMAL":
        descuento = precio_base * 0.05
    
    let precio_con_descuento = precio_base - descuento
    
    let impuesto = 0.0
    si categoria == "PREMIUM":
        impuesto = precio_con_descuento * 0.21
    sino si categoria == "VIP":
        impuesto = precio_con_descuento * 0.10
    sino:
        impuesto = precio_con_descuento * 0.21
    
    let total = precio_con_descuento + impuesto
    si envio:
        total = total + 10.0
    
    retornar total

# Prompt: "Refactoriza para eliminar condicionales duplicadas usando una estructura de categorías"
```

```syquex
# Después
estructura Categoria:
    nombre: texto
    descuento: decimal
    impuesto: decimal

constante CATEGORIAS = Mapa<texto, Categoria>(
    "PREMIUM": Categoria("PREMIUM", 0.15, 0.21),
    "VIP": Categoria("VIP", 0.10, 0.10),
    "NORMAL": Categoria("NORMAL", 0.05, 0.21)
)

funcion calcular_precio_final(precio_base: decimal, categoria: texto, envio: booleano) -> decimal:
    let cat = CATEGORIAS.obtener(categoria).desenvolver_o(Categoria("NORMAL", 0.0, 0.21))
    let precio_con_descuento = precio_base * (1.0 - cat.descuento)
    let total = precio_con_descuento * (1.0 + cat.impuesto)
    si envio:
        total = total + 10.0
    retornar total
```

## Referencias

- **Manual 7 §6.3**: Bucle de corrección automática
- **Manual 7 §4.2**: Validación con compilador real
- **Manual 7 §5.1**: Mapeo de conceptos y patrones
- **Manual 2 §2**: Gramática EBNF de Synapse
- **Manual 3 §6**: OOP en Syquex

// cumple Manual 7 §6.3
