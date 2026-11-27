# Funciones en Synapse

Las funciones son bloques de construcción reutilizables. En Synapse, toda
función pública debe incluir contratos `requiere` y `garantiza` que documentan
sus Preconditions y postconditions. Esto permite que el compilador verifique
automáticamente que los contratos se cumplen.

---

## Definición básica

```synapse
funcion sumar(a: entero, b: entero) -> entero:
    retornar a + b
```

La sintaxis es: `funcion nombre(parametros) -> tipo_retorno:`

El cuerpo está indentado (4 espacios o 1 tabulador). El tipo de retorno es
obligatorio para funciones con más de una expresión.

---

## Funciones con contratos

Toda función pública debe incluir contratos `requiere` y `garantiza`:

```synapse
funcion division(a: decimal, b: decimal) -> decimal:
    requiere: b != 0.0
    garantiza: resultado == a / b

    retornar a / b
```

Los contratos se verifican en tiempo de compilación cuando es posible, y en
runtime cuando no. Si un contrato se viola, el programa se detiene con un
mensaje descriptivo.

### Contratos con valores de retorno

```synapse
funcion raiz_cuadrada(x: decimal) -> decimal:
    requiere: x >= 0.0
    garantiza: resultado >= 0.0
    garantiza: resultado * resultado == x  // aproximar si es necesario

    retornar x.raiz()
```

---

## Parámetros

### Parámetros posicionales

```synapse
funcion crear_usuario(nombre: texto, edad: entero, activo: booleano) -> registro:
    retornar Registro {
        nombre: nombre,
        edad: edad,
        activo: activo
    }
```

### Parámetros con valores por defecto

```synapse
funcion conectar(
    host: texto = "localhost",
    puerto: entero = 8080,
    timeout_ms: entero = 5000
) -> conexion:
    requiere: puerto > 0 && puerto <= 65535
    garantiza: resultado.conectado == verdadero

    retornar Conexion.nueva(host, puerto, timeout_ms)
```

### Llamada con argumentos nombrados

```synapse
// Todas estas formas son válidas
variable c1 = conectar("localhost", 8080, 5000)
variable c2 = conectar(puerto: 3000)
variable c3 = conectar(host: "192.168.1.1", timeout_ms: 10000)
```

---

## Valor de retorno

### Retorno explícito con `retornar`

```synapse
funcion absoluta(x: entero) -> entero:
    si x < 0:
        retornar -x
    retornar x
```

### Retorno implícito (funciones de una expresión)

```synapse
funcion doble(x: entero) -> entero: x * 2

funcion es_par(x: entero) -> booleano: x % 2 == 0

funcion saludo(nombre: texto) -> texto: "Hola, " + nombre
```

Las funciones de una expresión usan `:` en lugar de `:` y retornan el valor
de la expresión directamente. Son ideales para funciones simples y callbacks.

---

## Funciones sin retorno

```synapse
funcion imprimir_lista(elementos: tensor[&] texto):
    para elem en elementos:
        imprimir(elem)
```

Cuando no hay tipo de retorno, la función retorna `nulo` implícitamente.
El `-> nulo` es opcional y generalmente se omite.

---

## Recursión

Synapse soporta recursión directa y tail recursion optimization:

```synapse
// Recursión directa
funcion factorial(n: entero) -> entero:
    requiere: n >= 0
    garantiza: resultado >= 1

    si n <= 1:
        retornar 1
    retornar n * factorial(n - 1)
```

```synapse
// Tail recursion (optimizada por el compilador a un loop)
funcion fibonacci(n: entero) -> entero:
    requiere: n >= 0
    retornar fibonacci_aux(n, 0, 1)

funcion fibonacci_aux(n: entero, a: entero, b: entero) -> entero:
    si n == 0:
        retornar a
    si n == 1:
        retornar b
    retornar fibonacci_aux(n - 1, b, a + b)
```

---

## Funciones como valores

Las funciones en Synapse son primeros ciudadanos. Pueden pasarse como
parámetros y retornarse:

```synapse
funcion aplicar(f: funcion(entero) -> entero, x: entero) -> entero:
    retornar f(x)

funcion cuadrado(x: entero) -> entero: x * x
funcion cubo(x: entero) -> entero: x * x * x

funcion ejemplo():
    variable r1 = aplicar(cuadrado, 5)   // 25
    variable r2 = aplicar(cubo, 5)       // 125
```

### Closures

Las funciones lambda capturan variables de su ámbito:

```synapse
funcion crear_contador() -> funcion() -> entero:
    mutable contador = 0
    retornar lambda() -> entero:
        contador += 1
        retornar contador

funcion ejemplo():
    variable contar = crear_contador()
    imprimir(contar())  // 1
    imprimir(contar())  // 2
    imprimir(contar())  // 3
```

---

## Sobrecarga de funciones

Synapse permite sobrecarga por tipos de parámetros:

```synapse
funcion mostrar(x: entero) -> texto: x.para_texto()
funcion mostrar(x: decimal) -> texto: x.para_texto()
funcion mostrar(x: texto) -> texto: x

funcion ejemplo():
    imprimir(mostrar(42))       // "42"
    imprimir(mostrar(3.14))     // "3.14"
    imprimir(mostrar("hola"))   // "hola"
```

---

## Funciones genéricas

```synapse
funcion maximo<T>(a: T, b: T) -> T:
    si a > b:
        retornar a
    retornar b

funcion ejemplo():
    variable m1 = maximo(10, 20)       // 20
    variable m2 = maximo(3.14, 2.71)   // 3.14
    variable m3 = maximo("abc", "xyz") // "xyz"
```

El parámetro de tipo `T` se infiere en la llamada. El compilador verifica
que las operaciones del genérico (`>`) estén soportadas para el tipo concreto.

---

## Funciones públicas y privadas

```synapse
// Pública: accesible desde otros módulos
funcion publica calcular(x: entero) -> entero: x * 2

// Privada: solo accesible dentro de este módulo
funcion privada validar(x: entero) -> booleano: x > 0

funcion ejemplo():
    imprimir(calcular(10))   // 20
    imprimir(validar(10))    // verdadero (dentro del mismo módulo)
```

---

## Resumen

| Concepto               | Sintaxis                                                  |
|------------------------|-----------------------------------------------------------|
| Función básica         | `funcion nombre(p: tipo) -> tipo: cuerpo`                |
| Función expresión      | `funcion nombre(p: tipo) -> tipo: expresion`              |
| Contratos              | `requiere: condicion` / `garantiza: condicion`           |
| Parámetros por defecto | `parametro: tipo = valor`                                 |
| Genéricos              | `funcion nombre<T>(p: T) -> T:`                           |
| Closures               | `lambda(parametros) -> tipo: cuerpo`                      |
| Privada                | `funcion privada nombre(...)`                             |

Los contratos `requiere/garantiza` son la diferencia fundamental con otros
lenguajes: documentan las expectativas de forma verificable, no solo como
comentarios.
