# Funciones en Syquex

Este capítulo explora la definición y uso de funciones en Syquex. Aprenderás sobre parámetros, valores de retorno, funciones anidadas y closures.

Las funciones en Syquex son de primera clase, permitiendo patrones funcionales y composición灵活.

<!-- cumple Manual 3 §7 -->

## 1. Definición Básica de Funciones

```syquex
funcion saludar(nombre: texto):
    io.escribir_linea("¡Hola, " + nombre + "!")
```

### Sintaxis

```ebnf
funcion ::= "funcion" IDENTIFICADOR "(" [ parametros ] ")" [ "->" tipo ] [ contratos ] ":" NEWLINE INDENT bloque DEDENT
         | IDENTIFICADOR "(" [ parametros ] ")" "=" expresion
```

## 2. Parámetros

### Parámetros Posicionales

```syquex
funcion sumar(a: entero, b: entero) -> entero:
    retornar a + b
```

### Valores por Defecto

```syquex
funcion saludar(nombre: texto, saludo: texto = "Hola"):
    io.escribir_linea(saludo + ", " + nombre + "!")
```

### Parámetros Variádicos

Syquex soporta argumentos variables mediante listas:

```syquex
importar lib.lista

funcion sumar_todos(numeros: Lista<entero>) -> entero:
    retornar numeros.sumar()
```

## 3. Valores de Retorno

### Función que retorna un valor

```syquex
funcion cuadrado(x: entero) -> entero:
    retornar x * x
```

### Función de una sola expresión

```syquex
funcion doble(x) = x * 2  // Sintaxis de expresión única
```

### Sin valor de retorno (`nulo`)

```syquex
funcion saludar(nombre: texto):
    io.escribir_linea("¡Hola, " + nombre + "!")
    // Implícitamente retorna nulo
```

## 4. Funciones de Orden Superior (Higher-Order Functions)

Las funciones son valores de primera clase:

```syquex
funcion aplicar(fn, valor):
    retornar fn(valor)

funcion cuadrado(x) = x * x

let resultado = aplicar(cuadrado, 5)  // resultado = 25
```

## 5. Lambdas y Closures

### Sintaxis de Lambda (Arrow Function)

```syquex
let doble = lambda x: x * 2
let suma = lambda a, b: a + b
```

### Closures

Las funciones capturan su entorno léxico:

```syquex
funcion crear_contador() -> funcion():
    let contador = 0
    
    funcion interna():
        contador = contador + 1
        retornar contador
    
    retornar interna

let contador = crear_contador()
log(contador())  // 1
log(contador())  // 2
log(contador())  // 3
```

## 6. Funciones Anidadas

```syquex
funcion calcular(a: entero, b: entero) -> entero:
    funcion validar(x: entero):
        si x < 0:
            retornar err("Valor negativo")
        retornar ok(x)
    
    // Usar función anidada
    let result_a = validar(a)?
    retornar result_a + b
```

## 7. Recursión

```syquex
funcion factorial(n: entero) -> entero:
    si n <= 1:
        retornar 1
    retornar n * factorial(n - 1)
```

### Recursión de Cola (Tail Recursion)

El optimizador de Syquex detecta y optimiza la recursión de cola:

```syquex
funcion factorial_aux(n: entero, acc: entero) -> entero:
    si n <= 1:
        retornar acc
    retornar factorial_aux(n - 1, n * acc)

funcion factorial(n: entero) -> entero:
    retornar factorial_aux(n, 1)
```

## 8. Contratos Lógicos (`requiere` / `garantiza`)

Las funciones pueden especificar contratos (Manual 2 §5):

```syquex
funcion dividir(a: entero, b: entero) -> entero:
    requiere:
        b != 0
    garantiza:
        _resultado_ * b + (a % b) == a
    retornar a / b
```

En `release` mode, las aserciones se eliminan (costo cero). En `--safe` mode, se usa verificación formal.

## 9. Funciones Externas (FFI)

```syquex
externo funcion strlen(s: &texto) -> entero

funcion longitud(s: texto) -> entero:
    retornar strlen(&s)  // El compilador maneja el marshaling
```

## 10. Exportación (`@export`)

```syquex
@export(python) funcion procesar(data: Lista<Decimal>) -> Resultado<Decimal, Texto>

@export(typescript) estructura Usuario:
    nombre: Texto
    edad: Entero
```

## Ejemplo Completo

```syquex
#lang: es

funcion fibonacci(n: entero) -> entero:
    si n <= 1:
        retornar n
    retornar fibonacci(n - 1) + fibonacci(n - 2)

funcion principal():
    let nums = [1, 2, 3, 4, 5]
    let cuadrados = nums.map(lambda x: x * x)
    let pares = cuadrados.filtrar(lambda x: x % 2 == 0)
    
    io.escribir_linea("Cuadrados pares: " + pares.texto())
    io.escribir_linea("Fibonacci(10) = " + fibonacci(10).texto())
```

## Referencias

- **Manual 3 §6.1-6.3**: Definición de funciones y parámetros
- **Manual 3 §7**: Manejo de errores con `Resultado` y operador `?`
- **Manual 2 §5**: Contratos lógicos `requiere`/`garantiza`

// cumple Manual 3 §7
