# Control de Flujo en Syquex

Este capítulo cubre las constructuras de control de flujo en Syquex: condicionales, bucles y patrones de iteración. Aprenderás a dirigir la ejecución de tu programa de manera clara y expresiva.

Syquex ofrece sintaxis moderna y legible para el control de flujo, con verificación estática de exhaustividad.

<!-- cumple Manual 3 §7 -->

## 1. Condicionales: `si`, `sino si`, `sino`

```syquex
si edad >= 18:
    io.escribir_linea("Mayor de edad")
sino si edad >= 13:
    io.escribir_linea("Adolescente")
sino:
    io.escribir_linea("Menor")
```

### `si` como expresión

```syquex
let categoria = si edad >= 18: "adulto" sino: "menor"
```

### Operador ternario implícito

```syquex
let descuento = si cliente_vip: 0.20 sino: 0.05
```

## 2. Bucles

### Bucle `mientras`

```syquex
let i = 0
mientras i < 10:
    io.escribir_linea("Iteración " + i.texto())
    i = i + 1
```

### Bucle `para` con rango

```syquex
// Sintaxis estilo Syquex
para i = 0 .. 10:
    io.escribir_linea("Número: " + i.texto())

// Con paso
para i = 0 .. 100 paso 5:
    io.escribir_linea("Múltiplo de 5: " + i.texto())
```

### Bucle `para en` (iteración sobre colecciones)

```syquex
// Iterar sobre una lista
let lista = [1, 2, 3, 4, 5]
para elemento en lista:
    io.escribir_linea("Elemento: " + elemento.texto())

// Iterar sobre un rango
para i en 0..10:
    io.escribir_linea("i = " + i.texto())

// Iterar sobre un mapa
para clave, valor en mapa:
    io.escribir_linea(clave + " = " + valor.texto())
```

## 3. `coincidir` y Pattern Matching

El pattern matching en Syquex es exhaustivo (Manual 3 §5.4):

```syquex
funcion clasificar(valor: entero) -> texto:
    coincidir valor:
        caso 0:
            retornar "cero"
        caso n si n > 0:
            retornar "positivo"
        caso n si n < 0:
            retornar "negativo"
```

### Pattern Matching con ADTs (`Resultado` y `Opcion`)

```syquex
funcion dividir(a: decimal, b: decimal) -> Resultado<decimal, texto>:
    si b == 0.0:
        retornar err("División por cero")
    retornar ok(a / b)

funcion main():
    let resultado = dividir(10.0, 0.0)
    coincidir resultado:
        caso ok(valor):
            io.escribir_linea("Resultado: " + valor.texto())
        caso err(mensaje):
            io.escribir_linea("Error: " + mensaje)
```

### Patterns con guardias

```syquex
coincidir edad:
    caso e si e < 13: "niño"
    caso e si e < 18: "adolescente"
    caso e si e < 65: "adulto"
    caso _: "adulto mayor"
```

### Wildcard (`_`)

El patrón `_` coincide con cualquier valor (fallback):

```syquex
coincidir estado:
    caso "activo": io.escribir_linea("✓")
    caso "inactivo": io.escribir_linea("✗")
    caso _: io.escribir_linea("?")
```

## 4. Expresiones de Control

Todas las construcciones de control son expresiones que retornan un valor:

```syquex
let resultado = si condicion:
    valor_positivo
sino:
    valor_negativo

// Útil para asignaciones condicionales
```

## 5. Control de Bucles

### `romper` y `continuar`

```syquex
para i en 1..20:
    si i % 3 == 0:
        continuar  // Salta a la siguiente iteración
    
    si i > 10:
        romper  // Sale del bucle
    
    io.escribir_linea(i.texto())
```

### `retornar` temprano

```syquex
funcion buscar(lista: Lista<entero>, objetivo: entero) -> entero:
    para i en 0..lista.len():
        si lista[i] == objetivo:
            retornar i
    retornar -1
```

## 6. Manejo de Errores con `intentar` / `atrapar`

```syquex
funcion operacion_riesgosa() -> Resultado<nulo, texto>:
    intentar:
        let archivo = abrir("datos.txt")
        let contenido = archivo.leer()
        // ...
    atrapar e:
        retornar err("Error en operación riesgosa: " + e)
    retornar ok()
```

### Propagación con `?`

```syquex
funcion calcular() -> Resultado<decimal, texto>:
    let a = leer_numero("a")?
    let b = leer_numero("b")?
    retornar ok(a / b)
```

## 7. Bloques `inseguro` (Modo Sistema)

```syquex
funcion acceso_memoria_directa(ptr: puntero):
    inseguro:
        // Operaciones de memoria manual
        ptr[0] = 42
```

## Ejemplo Completo

```syquex
#lang: es

importar lib.io

funcion clasificar_numero(n: entero) -> texto:
    coincidir n:
        caso 0: "cero"
        caso x si x > 0: "positivo"
        caso _: "negativo"

funcion principal():
    let numeros = [5, -3, 0, 12, -8]
    
    para n en numeros:
        io.escribir_linea(
            n.texto() + " es " + clasificar_numero(n)
        )
```

## Referencias

- **Manual 3 §3**: Gramática formal (EBNF) incluyendo sentencias de control
- **Manual 3 §5.4**: Tipos algebraicos `Resultado` y `Opcion`
- **Manual 3 §7**: Manejo de errores
- **Manual 2 §2**: Palabras reservadas multi-idioma

// cumple Manual 3 §7
