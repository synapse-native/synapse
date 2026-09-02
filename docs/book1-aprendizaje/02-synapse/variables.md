# Variables en Synapse

Las variables son la base de todo programa. En Synapse, la declaración de
variables está ligada al sistema de tipos estático y al modelo de ownership,
lo que garantiza que cada valor sea utilizado de forma segura.

---

## Declaración de variables

Synapse ofrece dos formas de declarar variables:

### Con la palabra clave `variable`

```synapse
variable x: entero = 10
variable nombre: texto = "Synapse"
variable pi: decimal = 3.14159
variable activo: booleano = verdadero
variable inicial: caracter = 'A'
```

La anotación de tipo es explícita después de los dos puntos. El compilador
verifica que el valor asignado sea compatible con el tipo declarado.

### Con la palabra clave `let` (inferencia de tipos)

```synapse
let x = 10              // inferido como entero
let nombre = "Synapse"  // inferido como texto
let pi = 3.14159        // inferido como decimal
let activo = verdadero  // inferido como booleano
```

`let` es equivalente a `variable` pero delega la inferencia de tipos al
compilador. Usa `let` cuando el tipo es evidente y `variable` cuando
quieres explícidad.

---

## Tipos de datos primitivos

| Tipo        | Tamaño    | Rango / Descripción                    | Ejemplo                  |
|-------------|-----------|----------------------------------------|--------------------------|
| `entero`    | 64 bits   | -2^63 a 2^63 - 1                      | `variable x: entero = 42` |
| `decimal`   | 64 bits   | Punto flotante doble precisión         | `variable pi: decimal = 3.14` |
| `booleano`  | 1 bit     | `verdadero` o `falso`                  | `variable ok: booleano = verdadero` |
| `texto`     | Variable  | UTF-8, inmutable después de creación   | `variable s: texto = "hola"` |
| `caracter`  | 32 bits   | Un solo Unicode                        | `variable c: caracter = 'Z'` |
| `nulo`      | 0 bits    | Ausencia de valor                      | `variable vacio: nulo = nada` |

### Tipo tensor (arreglo estático)

```synapse
variable numeros: tensor[5] entero = [1, 2, 3, 4, 5]
variable matriz: tensor[3][3] decimal = [
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0]
]
```

Los tensores tienen tamaño fijo en compilación. Para colecciones dinámicas,
usa `lista` de la biblioteca estándar.

---

## Mutabilidad

Las variables en Synapse son **inmutables por defecto**. Para modificarlas,
debes usar la palabra clave `mutable`:

```synapse
// Inmutable: no se puede reasignar
let x = 10
// x = 20  // Error de compilación

// Mutable: se puede reasignar
mutable x = 10
x = 20  // Válido

// Mutable con tipo explícito
mutable contador: entero = 0
contador += 1
```

La inmutabilidad por defecto es una decisión de diseño: el código inmutable
es más fácil de razonar, depurar y paralelizar.

---

## Constantes

Las constantes son valores que no pueden cambiar después de su definición.
Se declaran con `constante`:

```synapse
constante PI: decimal = 3.14159265358979
constante MAXIMO_INTENTOS: entero = 3
constante VERSION: texto = "1.0.0"
constante PREFIJO_USUARIO: caracter = '@'
```

Las constantes deben tener un valor conocido en tiempo de compilación.
El compilador las reemplaza directamente en el código generado, similar
a los `#define` de C pero con tipos seguros.

---

## Ámbito de variables

Las variables tienen ámbito limitado al bloque donde se declaran:

```synapse
funcion ejemplo():
    variable x = 10
    si x > 5:
        variable y = x * 2  // y solo existe aquí
        imprimir(y)
    // Error: y no está en ámbito
    // imprimir(y)
```

Las variables declaradas en un bloque `si`, `mientras`, `para` o `coincidir`
solo existen dentro de ese bloque.

---

## Ámbito de blocks con `{}`

```synapse
funcion calcular() -> entero:
    variable resultado = 0
    {
        variable datos: tensor[3] entero = [10, 20, 30]
        para d en datos:
            resultado += d
    }  // datos se libera aquí
    retornar resultado  // resultado = 60
```

El bloque `{}` crea un scope separado. Las variables dentro se liberan al
salir del bloque, lo cual es útil para controlar la lifetime de recursos.

---

## Conversión de tipos

Synapse no realiza conversiones implícitas. Debes ser explícito:

```synapse
variable entero_val: entero = 42
variable decimal_val: decimal = entero_val.para_decimal()  // 42.0
variable texto_val: texto = entero_val.para_texto()        // "42"

variable pi: decimal = 3.14
variable entero_pi: entero = pi.para_entero()  // 3 (trunca, no redondea)

variable num_texto: texto = "100"
variable num: entero = num_texto.para_entero()  // 100
```

Las conversiones son métodos explícitos. Esto evita errores sutiles como
truncamiento accidental o pérdida de precisión.

---

## Desestructuración

Synapse permite desestructurar tensores y registros:

```synapse
registro Persona:
    nombre: texto
    edad: entero

funcion ejemplo():
    // Desestructuración de tensor
    variable [a, b, c] = [1, 2, 3]
    imprimir(a, b, c)  // 1 2 3

    // Desestructuración de registro
    variable persona = Persona { nombre: "Ana", edad: 30 }
    variable Persona { nombre, edad } = persona
    imprimir(nombre, edad)  // Ana 30
```

---

## Resumen

| Concepto          | Sintaxis                              | Mutabilidad     |
|-------------------|---------------------------------------|-----------------|
| Variable          | `variable x: tipo = valor`            | Inmutable       |
| Variable mutable  | `mutable x: tipo = valor`             | Mutable         |
| Inferencia        | `let x = valor`                       | Inmutable       |
| Constante         | `constante X: tipo = valor`           | Inmutable       |
| Tensor            | `variable t: tensor[N] tipo = [...]` | Contenido mutable |

Las reglas de Synapse sobre variables están diseñadas para que el compilador
pueda verificar la seguridad de memoria en tiempo de compilación, eliminando
categorías enteras de bugs antes de que el código se ejecute.
