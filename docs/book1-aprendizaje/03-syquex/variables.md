# Variables y Tipos en Syquex

Este capítulo cubre la declaración y uso de variables en Syquex. Aprenderás sobre tipos de datos, inferencia de tipos, mutabilidad y el alcance de las variables.

Syquex ofrece un equilibrio entre la flexibilidad de tipos dinámicos y la seguridad de tipos estáticos. El compilador infiere tipos automáticamente mediante el algoritmo Hindley-Milner, pero también permite anotaciones explícitas.

<!-- cumple Manual 3 §5 -->

## 1. Declaración de Variables

### Variable Mutable (mutabilidad por defecto)

En Syquex, las variables son **mutables por defecto**, a diferencia de Synapse:

```syquex
let contador = 0
contador = contador + 1  // ✓ Permite reassignación
```

### Variable Inmutable

Usando la palabra clave `constante`:

```syquex
constante PI = 3.14159
// PI = 3.14  // ✗ Error: no se puede modificar una constante
```

### Anotación de Tipos

Puedes anotar explícitamente el tipo de una variable:

```syquex
let nombre: texto = "Ana"
let edad: entero = 28
let activo: booleano = verdadero
```

## 2. Tipos de Datos Primitivos

Syquex comparte los mismos tipos primitivos que Synapse (Manual 2 §4):

| Tipo Sintáctico | Descripción | Tamaño | Ejemplo |
|----------------|-------------|--------|---------|
| `entero` / `int` | Entero con signo de 64 bits | 8 bytes | `let x: entero = 42` |
| `decimal` / `float` | Punto flotante doble precisión | 8 bytes | `let pi: decimal = 3.14` |
| `booleano` / `bool` | Booleano lógico | 1 byte | `let ok: booleano = verdadero` |
| `texto` / `string` | Cadena UTF-8 segura | 16 bytes | `let s: texto = "hola"` |
| `caracter` / `char` | Carácter UTF-8 | 1-4 bytes | `let c: char = 'a'` |
| `nulo` / `void` | Ausencia de valor | 0 bytes | `retornar nulo` |

## 3. Inferencia de Tipos (Hindley-Milner)

El compilador infiere tipos automáticamente:

```syquex
let x = 42              // Inferido como entero
let y = 3.14            // Inferido como decimal
let nombre = "Ana"      // Inferido como texto
let lista = [1, 2, 3]   // Inferido como Lista<entero>
```

### Inferencia Polimórfica

```syquex
funcion identidad(a):
    retornar a  // Tipo inferido: funcion(T) -> T

let num = identidad(42)     // T = entero
let str = identidad("hola") // T = texto
```

## 4. Tipos de Colecciones Nativos

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `Lista<T>` | Lista dinámica | `let l: Lista<entero> = [1, 2, 3]` |
| `Mapa<K,V>` | Diccionario hash | `let m: Mapa<texto, entero> = {"a": 1}` |
| `Canal<T>` | Canal de comunicación | `let c: Canal<texto> = Canal<texto>(10)` |

## 5. Tipos Especiales de Memoria

| Tipo | Propósito | Gestión |
|------|-----------|---------|
| `arena<T>` | Asigna en arena de ámbito | Automática (bump allocator) |
| `rc<T>` | Conteo de referencias no atómico | Manual (el compilador inyecta rc_inc/rc_dec) |
| `arc<T>` | Conteo de referencias atómico | Automática |
| `débil<T>` | Referencia débil | Automática |
| `&T` | Préstamo inmutable (solo FFI) | Verificación en compilación |

## 6. Tipos Booleanos y Nulos

```syquex
let verdadero_val = verdadero
let falso_val = falso
let nada = nulo
```

## 7. Alcance de Variables

Las variables siguen el scope de bloque:

```syquex
funcion ejemplo():
    let a = 1  // Visible dentro de ejemplo()
    
    si verdadero:
        let b = 2  // Visible solo dentro del bloque si
        log(a)     // ✓ a es visible
    
    log(a)  // ✓ a es visible
    // log(b)  // ✗ Error: b no está en scope
```

## 8. Mutabilidad Explícita (Modo Sistema)

En el modo sistema (FFI/integración con Synapse), Syquex soporta préstamos:

```syquex
funcion modificar_lista(lista: &mut Lista<entero>):
    lista.agregar(4)
```

## Ejemplo Completo

```syquex
#lang: es

importar lib.io

constante FORMATO_FECHA = "%d/%m/%Y"

funcion principal():
    let nombre: texto = "Ana Pérez"
    let edad = 28  // Inferido como entero
    let salario: decimal = 45000.50
    let activo = verdadero  // Inferido como booleano
    
    let calificaciones: Lista<decimal> = [9.5, 8.0, 7.5]
    let usuario: Mapa<texto, texto> = {"nombre": nombre, "role": "admin"}
    
    io.escribir_linea("Usuario: " + usuario["nombre"])
    io.escribir_linea("Promedio: " + calificaciones.promedio().texto())
```

## Referencias

- **Manual 3 §5.1**: Tipos primitivos
- **Manual 3 §5.2**: Tipos de colecciones
- **Manual 3 §5.3**: Tipos de memoria especiales
- **Manual 3 §5.4**: Tipos algebraicos `Resultado` y `Opcion`
- **Manual 2 §4**: Tipos primitivos de Synapse

// cumple Manual 3 §5
