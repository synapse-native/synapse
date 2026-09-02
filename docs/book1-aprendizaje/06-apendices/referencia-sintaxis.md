# Referencia Rápida de Sintaxis

Este apéndice contiene una referencia completa de la sintaxis de Synapse y Syquex. Incluye todas las constructuras del lenguaje, operadores y convenciones de forma concisa y consultable.

Úsalo como guía rápida cuando necesites recordar la sintaxis correcta.

<!-- cumple Manual 2 §2, Manual 3 §3 -->

## 1. Sintaxis de Variables y Tipos

### Synapse (Bajo nivel)

```synapse
#lang: es

// Declaración de variables
let nombre = "Ana"
let edad: entero = 28
constante PI: decimal = 3.14159

// Tipos primitivos
let entero_val: entero = 42
let decimal_val: decimal = 3.14
let texto_val: texto = "Hola"
let bool_val: booleano = verdadero
let char_val: caracter = 'a'

// Ownership explícito
let poseedor: entero = 100
let nuevo_poseedor -> entero = poseedor  // move
// poseedor ya no es válido aquí

// Préstamos
let inmutable: &entero = &poseedor
let mutable: &mut entero = &mut poseedor
```

### Syquex (Alto nivel)

```syquex
#lang: es

// Declaración de variables (memoria automática)
let nombre = "Ana"
let edad = 28
constante PI = 3.14159

// Anotación de tipos (opcional)
let texto: texto = "Hola"
let numero: entero = 42

// Tipos primitivos
let i: entero = 42
let f: decimal = 3.14
let s: texto = "Hola"
let b: booleano = verdadero
let c: caracter = 'a'

// Colecciones
let lista: Lista<entero> = [1, 2, 3]
let mapa: Mapa<texto, entero> = {"a": 1}
```

## 2. Funciones

### Synapse

```synapse
funcion sumar(a: entero, b: entero) -> entero:
    requiere:
        a > 0
        b > 0
    garantiza:
        _resultado_ == a + b
    retornar a + b

// Función pública
@export(python) funcion externa(x: entero) -> entero:
    retornar x * 2
```

### Syquex

```syquex
// Función básica
funcion sumar(a: entero, b: entero) -> entero:
    retornar a + b

// Función de una expresión
funcion doble(x) = x * 2

// Función con valores por defecto
funcion saludar(nombre: texto, saludo: texto = "Hola"):
    retornar saludo + ", " + nombre

// Función pública
@export(python) funcion externa(x: entero) -> entero:
    retornar x * 2

// Lambda
let cuadrado = lambda x: x * x
```

## 3. Control de Flujo

### Condicionales

```synapse
// Synapse
si edad >= 18:
    log("Mayor de edad")
sino si edad >= 13:
    log("Adolescente")
sino:
    log("Menor")
```

```syquex
// Syquex
si edad >= 18:
    io.escribir_linea("Mayor de edad")
sino si edad >= 13:
    io.escribir_linea("Adolescente")
sino:
    io.escribir_linea("Menor")

// Como expresión
let categoria = si edad >= 18: "adulto" sino: "menor"
```

### Bucles

```synapse
// Synapse - para con rango
para i = 0 mientras i < 10:
    log(i)

// Synapse - mientras
mientras x < 100:
    x = x + 1
```

```syquex
// Syquex - para con rango
para i = 0 .. 10:
    io.escribir_linea(i)

// Syquex - con paso
para i = 0 .. 100 paso 5:
    io.escribir_linea(i)

// Syquex - para en (iteración)
para item en lista:
    io.escribir_linea(item)

// Syquex - mientras
mientras x < 100:
    x = x + 1

// Control
romper      // Salir del bucle
continuar   // Siguiente iteración
```

### Pattern Matching

```syquex
coincidir resultado:
    caso ok(valor):
        log("Éxito: ", valor)
    caso err(e):
        log("Error: ", e)
    caso ninguno:
        log("Sin valor")
    caso _:
        log("Otro caso")
```

## 4. Estructuras de Datos

### Synapse

```synapse
estructura Persona:
    nombre: texto
    edad: entero
    activo: booleano
```

### Syquex

```syquex
// Estructura con constructor y métodos
estructura Persona:
    nombre: texto
    edad: entero
    activo: booleano = verdadero
    
    crear(nombre: texto, edad: entero):
        self.nombre = nombre
        self.edad = edad
    
    metodo saludar() -> texto:
        retornar "Hola, soy " + self.nombre
    
    metodo cumpleaños():
        self.edad = self.edad + 1
```

### Tipos Algebraicos (ADT)

```synapse
// Synapse
tipo Resultado<T, E> = ok(T) | err(E)
tipo Opcion<T> = algun(T) | ninguno
```

```syquex
// Syquex - mismo tipo
tipo Resultado<T, E> = ok(T) | err(E)
tipo Opcion<T> = algun(T) | ninguno
```

## 5. Manejo de Errores

### Synapse

```synapse
funcion procesar() -> Resultado<entero, texto>:
    si error:
        retornar err("Algo salió mal")
    retornar ok(42)

// Uso
coincidir resultado:
    caso ok(v): log(v)
    caso err(e): log("Error: ", e)
```

### Syquex

```syquex
funcion procesar() -> Resultado<entero, texto>:
    si error:
        retornar err("Algo salió mal")
    retornar ok(42)

// Propagación con ?
funcion calcular() -> Resultado<decimal, texto>:
    let a = leer_numero()?
    let b = leer_numero()?
    retornar ok(a / b)

// try/catch
funcion operacion() -> Resultado<nulo, texto>:
    intentar:
        // código riesgoso
    atrapar e:
        retornar err(e)
    retornar ok()
```

## 6. Concurrencia

### Synapse

```synapse
// Crear hilo
lanzar trabajador(datos)

// Enviar a canal
canal <- valor

// Recibir de canal
valor = canal ->

// Escuchar canal
escuchar canal:
    let msg = canal ->
    log(msg)
```

### Syquex

```syquex
// Crear fibra
lanzar trabajador(datos)

// Enviar a canal
canal <- valor

// Recibir de canal
valor = canal ->

// Escuchar canal
escuchar canal:
    let msg = canal ->
    io.escribir_linea(msg)

// Async/await
async funcion fetch():
    let resp = await http.get(url)
    retornar resp
```

## 7. Operadores

### Aritméticos

| Operador | Descripción | Ejemplo |
|----------|-------------|---------|
| `+` | Suma | `a + b` |
| `-` | Resta | `a - b` |
| `*` | Multiplicación | `a * b` |
| `/` | División | `a / b` |
| `%` | Módulo | `a % b` |

### Relacionales

| Operador | Descripción | Ejemplo |
|----------|-------------|---------|
| `==` | Igual | `a == b` |
| `!=` | Diferente | `a != b` |
| `<` | Menor que | `a < b` |
| `>` | Mayor que | `a > b` |
| `<=` | Menor o igual | `a <= b` |
| `>=` | Mayor o igual | `a >= b` |

### Lógicos

| Operador | Descripción | Ejemplo |
|----------|-------------|---------|
| `y` / `and` | Y lógico | `a y b` |
| `o` / `or` | O lógico | `a o b` |
| `no` / `not` | Negación | `no a` |

### Especiales

| Operador | Descripción | Ejemplo |
|----------|-------------|---------|
| `?` | Propagación de error | `resultado?` |
| `->` | Transferencia de ownership | `retornar -> x` |
| `&` | Préstamo inmutable | `&x` |
| `&mut` | Préstamo mutable | `&mut x` |
| `<-` | Enviar a canal | `canal <- valor` |
| `->` (canal) | Recibir de canal | `valor = canal ->` |

## 8. Directivas y Palabras Clave

### Directivas de Archivo

```synapse
#lang: es    // Idioma del archivo (obligatorio)
#lang: en    // Inglés
#lang: fr    // Francés
#lang: pt    // Portugués
```

### Modificadores

| Modificador | Descripción | Ejemplo |
|-------------|-------------|---------|
| `@export` | Exportar para FFI | `@export(python) funcion f()` |
| `externo` | Función externa (C) | `externo funcion strlen(...)` |
| `constante` | Constante | `constante PI = 3.14` |
| `estatico` | Variable estática | `estatico contador: entero = 0` |
| `inseguro` | Bloque unsafe | `inseguro: ...` |

### Palabras Reservadas Comunes

| Synapse | Syquex | Significado |
|---------|--------|-------------|
| `funcion` | `funcion` | Definir función |
| `estructura` | `estructura` | Definir estructura |
| `constante` | `constante` | Constante |
| `si` / `sino` | `si` / `sino` | Condicional |
| `mientras` | `mientras` | Bucle while |
| `para` | `para` | Bucle for |
| `retornar` | `retornar` | Return |
| `lanzar` | `lanzar` | Crear hilo/fibra |
| `escuchar` | `escuchar` | Listen (canal) |
| `coincidir` | `coincidir` | Pattern matching |
| `intentar` / `atrapar` | `intentar` / `atrapar` | Try/catch |
| `importar` | `importar` | Importar módulo |
| `requiere` / `garantiza` | `requiere` / `garantiza` | Contratos |
| `let` | `let` | Variable local |
| `tipo` | `tipo` | Tipo algebraico |
| `enum` | `enumeracion` | Enumeración |
| `metodo` | `metodo` | Método |
| `crear` | `crear` | Constructor |

## 9. Comentarios

```synapse
// Comentario de una línea
/* Comentario
   de múltiples
   líneas */
/* Comentario
   /* anidado */
   */
```

## 10. Imports y Exports

```syquex
// Importar
importar lib.io
importar lib.web
importar synapse.audio

// Alias
importar lib.io como io

// Exportar
@export(python) funcion f() -> entero:
    retornar 42

@export(typescript) estructura Usuario:
    nombre: texto
    edad: entero
```

## Referencias

- **Manual 2 §1-2**: Sintaxis y gramática EBNF de Synapse
- **Manual 2 §3**: Tabla de palabras reservadas
- **Manual 3 §1-3**: Sintaxis y gramática EBNF de Syquex
- **Manual 3 §4**: Palabras reservadas de Syquex

// cumple Manual 2 §2
