# Control de Flujo en Synapse

El control de flujo determina qué código se ejecuta y en qué orden. Synapse
ofrece construcciones familiares con la seguridad del sistema de tipos y
ownership integrado.

---

## Condicional: si / sino

```synapse
variable edad = 25

si edad >= 18:
    imprimir("Mayor de edad")
sino si edad >= 13:
    imprimir("Adolescente")
sino:
    imprimir("Niño")
```

### Expresión condicional

`si` puede usarse como expresión que retorna un valor:

```synapse
variable estado = si edad >= 18 { "adulto" } sino { "menor" }

// Equivalente a un ternario pero más legible
variable max = si a > b { a } sino { b }
```

---

## Bucle: mientras

```synapse
mutable contador = 0
mientras contador < 10:
    imprimir(contador)
    contador += 1
```

### Con condición compuesta

```synapse
mutable intentos = 0
mutable conectado = falso

mientras !conectado && intentos < 3:
    conectado = intentar_conectar()
    intentos += 1

si !conectado:
    error("No se pudo conectar después de 3 intentos")
```

---

## Bucle: para

### Rango numérico

```synapse
// Rango 0..9 (excluyente superior)
para i en 0..10:
    imprimir(i)

// Rango inclusivo
para i en 0..=10:
    imprimir(i)  // imprime 0, 1, 2, ..., 10

// Rango descendente
para i en 10..=0:
    imprimir(i)  // imprime 10, 9, 8, ..., 0
```

### Iterar sobre un tensor

```synapse
variable frutas = ["manzana", "pera", "uva"]

para fruta en frutas:
    imprimir(fruta)

// Con índice
para i en 0..frutas.longitud:
    imprimir(i, ": ", frutas[i])
```

### Iterar sobre un registro

```synapse
registro Persona:
    nombre: texto
    edad: entero

variable personas = [
    Persona { nombre: "Ana", edad: 30 },
    Persona { nombre: "Luis", edad: 25 }
]

para p en personas:
    imprimir(p.nombre, " tiene ", p.edad, " años")
```

---

## Romper y siguiente

### `romper` (break)

Sale del bucle más interno:

```synapse
para i en 0..100:
    si i == 5:
        romper
    imprimir(i)
// Imprime: 0, 1, 2, 3, 4
```

### `siguiente` (continue)

Salta a la siguiente iteración:

```synapse
para i en 0..10:
    si i % 2 == 0:
        siguiente
    imprimir(i)  // solo impares: 1, 3, 5, 7, 9
```

---

## Etiquetas de bucle

Para romper bucles anidados, usa etiquetas:

```synapse
externo: para i en 0..10:
    interno: para j en 0..10:
        si i * j > 20:
            romper externo  // sale del bucle externo
        imprimir(i, j)
```

---

## Ejemplos prácticos

### Buscar un elemento

```synapse
funcion buscar(datos: tensor[&] entero, objetivo: entero) -> opcional(entero):
    para i en 0..datos.longitud:
        si datos[i] == objetivo:
            retornar opcion(i)
    retornar nada

funcion ejemplo():
    variable nums = [10, 20, 30, 40, 50]
    variable resultado = buscar(nums, 30)
    si resultado.es_algo():
        imprimir("Encontrado en índice: ", resultado.valor())
    sino:
        imprimir("No encontrado")
```

### Validar entrada de usuario

```synapse
funcion leer_edad() -> entero:
    mutable edad_valida = falso
    mutable edad = 0

    mientras !edad_valida:
        imprimir("Ingrese su edad:")
        variable entrada = leer_linea()
        edad = entrada.para_entero_opcional()

        si edad.es_algo() && edad.valor() > 0 && edad.valor() < 150:
            edad_valida = verdadero
        sino:
            imprimir("Edad inválida. Intente de nuevo.")

    retornar edad.valor()
```

### Procesar datos con filtro

```synapse
funcion filtrar_pares(datos: tensor[&] entero) -> lista(entero):
    variable resultado: lista(entero) = []
    para d en datos:
        si d % 2 == 0:
            resultado.agregar(d)
    retornar resultado

funcion ejemplo():
    variable original = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    variable pares = filtrar_pares(original)
    // pares = [2, 4, 6, 8, 10]
```

### Tabla de multiplicar

```synapse
funcion tabla_multiplicar(n: entero):
    requiere: n > 0
    para i en 1..=10:
        imprimir(n, " x ", i, " = ", n * i)

funcion ejemplo():
    tabla_multiplicar(7)
    // 7 x 1 = 7
    // 7 x 2 = 14
    // ...
    // 7 x 10 = 70
```

### Contar palabras

```synapse
funcion contar_palabras(texto: texto) -> entero:
    mutable contador = 0
    mutable en_palabra = falso

    para c en texto.caracteres():
        si c == ' ' || c == '\n' || c == '\t':
            en_palabra = falso
        sino si !en_palabra:
            contador += 1
            en_palabra = verdadero

    retornar contador

funcion ejemplo():
    variable texto = "Hola mundo desde Synapse"
    imprimir("Palabras: ", contar_palabras(texto))  // 4
```

---

## Resumen

| Construcción   | Uso                                    | Ejemplo                          |
|----------------|----------------------------------------|----------------------------------|
| `si`           | Decisión simple                        | `si x > 0: ...`                  |
| `sino`         | Rama alternativa                       | `sino: ...`                      |
| `mientras`     | Bucle con condición                    | `mientras x < 10: ...`          |
| `para`         | Iteración sobre rango o colección      | `para i en 0..10: ...`           |
| `romper`       | Salir del bucle                        | `romper`                          |
| `siguiente`    | Saltar iteración                       | `siguiente`                       |
| `romper etiq`  | Salir de bucle anidado                 | `romper externo`                  |

Las construcciones de control en Synapse son familares pero están diseñadas
para funcionar correctamente con el sistema de ownership. Las variables
capturadas en closures y callbacks mantienen sus garantías de seguridad.
