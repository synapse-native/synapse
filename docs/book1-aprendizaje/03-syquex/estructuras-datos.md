# Estructuras de Datos en Syquex

Este capítulo presenta las estructuras de datos integradas en Syquex: listas, diccionarios, conjuntos y tuplas. Aprenderás a elegir la estructura adecuada para cada caso de uso.

Syquex proporciona colecciones potentes y flexibles para organizar y procesar datos.

<!-- cumple Manual 3 §5.2 -->

## 1. Listas (`Lista<T>`)

Las listas son colecciones dinámicas ordenadas de elementos del mismo tipo.

### Creación

```syquex
// Lista vacía
let lista = Lista<entero>()

// Lista con elementos
let numeros = [1, 2, 3, 4, 5]

// Lista de strings
let nombres = ["Ana", "Beto", "Carlos"]
```

### Operaciones Principales

| Operación | Descripción | Ejemplo |
|-----------|-------------|--------|
| `len()` | Número de elementos | `numeros.len()` → 5 |
| `agregar(x)` | Añadir elemento al final | `numeros.agregar(6)` |
| `insertar(i, x)` | Insertar en posición | `numeros.insertar(0, 0)` |
| `eliminar(i)` | Eliminar por índice | `numeros.eliminar(2)` |
| `pop()` | Extraer último elemento | `let x = numeros.pop()` |
| `mapear(fn)` | Transformar elementos | `numeros.mapear(lambda x: x * 2)` |
| `filtrar(fn)` | Filtrar elementos | `numeros.filtrar(lambda x: x > 3)` |
| `reducir(fn, init)` | Reducir a un valor | `numeros.reducir(lambda a, b: a + b, 0)` |
| `iterar()` | Iterador | `para x en numeros.iterar()` |

### Ejemplo Completo

```syquex
let numeros = [1, 2, 3, 4, 5]

// Filtrar pares, multiplicar por 10, sumar
let resultado = numeros
    .filtrar(lambda x: x % 2 == 0)
    .mapear(lambda x: x * 10)
    .reducir(lambda acc, x: acc + x, 0)

io.escribir_linea("Resultado: " + resultado.texto())  // 60
```

## 2. Mapas (`Mapa<K,V>`)

Los mapas son diccionarios asociativos (hash maps).

### Creación

```syquex
// Mapa vacío
let mapa = Mapa<texto, entero>()

// Mapa con elementos
let edades = {
    "Ana": 28,
    "Beto": 35,
    "Carlos": 42
}
```

### Operaciones Principales

| Operación | Descripción | Ejemplo |
|-----------|-------------|--------|
| `len()` | Número de pares | `edades.len()` → 3 |
| `[k]` | Acceder valor | `edades["Ana"]` → 28 |
| `[k] = v` | Asignar valor | `edades["Ana"] = 29` |
| `contiene(k)` | Verificar clave | `edades.contiene("Ana")` → true |
| `keys()` | Lista de claves | `edades.keys()` |
| `values()` | Lista de valores | `edades.values()` |
| `items()` | Lista de pares | `edades.items()` |

### Iteración

```syquex
para clave, valor en edades.items():
    io.escribir_linea(clave + " tiene " + valor.texto() + " años")
```

## 3. Conjuntos (`Conjunto<T>`)

Los conjuntos almacenan elementos únicos sin orden garantizado.

### Creación

```syquex
let conjunto = Conjunto<entero>()  // Importado de lib/conjuntos.syq
conjunto.agregar(1)
conjunto.agregar(2)
conjunto.agregar(1)  // No se duplica
```

### Operaciones

| Operación | Descripción |
|-----------|-------------|
| `agregar(x)` | Añadir elemento |
| `contiene(x)` | Verificar existencia |
| `union(otro)` | Unión de conjuntos |
| `interseccion(otro)` | Intersección |
| `diferencia(otro)` | Diferencia |

## 4. Tuplas (`Tupla<T1, T2, ...>`)

Las tuplas agrupan valores de diferentes tipos:

```syquex
let persona = ("Ana", 28, verdadero)  // (texto, entero, booleano)

// Acceso por posición
io.escribir_linea(persona[0])  // "Ana"
```

### Desestructuración

```syquex
let (nombre, edad, activo) = persona
io.escribir_linea(nombre + " tiene " + edad.texto() + " años")
```

## 5. Rangos

Los rangos representan secuencias numéricas:

```syquex
// Rango inclusivo
para i en 1..=10:  // 1 a 10 inclusive
    log(i)

// Rango excluyente
para i en 1..<10:  // 1 a 9 (excluye 10)
    log(i)
```

## 6. Operaciones Funcionales Comunes

Todas las colecciones soportan operaciones funcionales:

```syquex
let datos = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

// Cadena de operaciones
let resultado = datos
    .filtrar(lambda x: x % 2 == 0)      // [2, 4, 6, 8, 10]
    .mapear(lambda x: x * x)            // [4, 16, 36, 64, 100]
    .filtrar(lambda x: x > 20)          // [36, 64, 100]
    .reducir(lambda acc, x: acc + x, 0) // 200

io.escribir_linea("Resultado: " + resultado.texto())
```

## Ejemplo Completo

```syquex
#lang: es

importar lib.io
importar lib.lista

funcion principal():
    // Lista de estudiantes
    let estudiantes = ["Ana", "Beto", "Carlos", "Diana"]
    
    // Mapa de calificaciones
    let calificaciones = Mapa<texto, Lista<entero>>()
    calificaciones["Ana"] = [95, 88, 92]
    calificaciones["Beto"] = [78, 85, 80]
    
    // Calcular promedios
    para nombre en estudiantes:
        let notas = calificaciones[nombre]
        let promedio = notas.reducir(lambda acc, x: acc + x, 0) / notas.len()
        io.escribir_linea(nombre + ": " + promedio.texto())

// Referencias
- Manual 3 §5.2: Tipos de colecciones nativas (Lista, Mapa)
- Manual 2 §4.3: Tipos compuestos
