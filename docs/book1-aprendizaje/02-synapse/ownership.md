# Ownership en Synapse

Ownership es el concepto central del modelo de memoria de Synapse. Cada valor
tiene un único dueño, y cuando ese dueño sale de ámbito, el valor se libera
automáticamente. Esto elimina la necesidad de un garbage collector y previene
errores comunes como double-free y use-after-free.

---

## Las tres reglas de ownership

1. **Cada valor tiene un único dueño.**
2. **Solo puede haber un dueño a la vez.**
3. **Cuando el dueño sale de ámbito, el valor se libera.**

```synapse
funcion ejemplo():
    variable texto = "hola"  // 'texto' es el dueño del valor "hola"
    // La función termina; 'texto' sale de ámbito; el valor se libera
```

---

## Movimiento (move)

Cuando asignas un valor a otra variable o lo pasas a una función, el ownership
se **transfiere**. La variable original ya no es válida:

```synapse
funcion ejemplo():
    variable a = [1, 2, 3]  // 'a' es dueño del tensor
    variable b = a           // ownership se mueve a 'b'

    // Error de compilación: 'a' ya no es válido
    // imprimir(a)

    imprimir(b)  // OK: 'b' es el dueño actual
```

Esto es diferente a C o Python, donde ambas variables apuntarían al mismo
objeto. En Synapse, la transferencia es explícita y el compilador protege
contra uso indebido.

### Movimiento en funciones

```synapse
funcion procesar(datos: tensor[3] entero) -> entero:
    variable total = 0
    para d en datos:
        total += d
    retornar total

funcion ejemplo():
    variable numeros = [10, 20, 30]
    variable suma = procesar(numeros)  // ownership de 'numeros' se mueve

    // Error: 'numeros' fue movido
    // imprimir(numeros)

    imprimir(suma)  // 60
```

---

## Clonación (clone)

Si necesitas que dos variables tengan valores independientes, usa `clonar()`:

```synapse
funcion ejemplo():
    variable original = [1, 2, 3]
    variable copia = original.clonar()  // copia profunda

    // Ambas son válidas y son independientes
    original[0] = 99
    imprimir(original)  // [99, 2, 3]
    imprimir(copia)     // [1, 2, 3]
```

### Cuándo clonar

Clonar es útil cuando:
- Necesitas preservar el valor original después de pasarlo a una función
- Quieres trabajar con una copia sin afectar el original
- Estás construyendo estructuras de datos inmutables

```synapse
funcion usar_y_conservar(datos: tensor[&] entero):
    variable copia = datos.clonar()
    procesar(copia)
    // 'datos' sigue válido porque solo clonamos

funcion ejemplo():
    variable info = [10, 20, 30]
    usar_y_conservar(&info)
    imprimir(info)  // OK: info sigue existiendo
```

---

## Copy types

Algunos tipos son **copy**: se copian automáticamente al asignarlos, sin
necesidad de `clonar()`. Esto incluye:

- `entero`
- `decimal`
- `booleano`
- `caracter`
- Tensores pequeños de tipos copy

```synapse
funcion ejemplo():
    variable x = 42
    variable y = x  // y es una copia, no un movimiento

    // Ambas son válidas
    imprimir(x)  // 42
    imprimir(y)  // 42
```

Los tipos copy son siempre valores pequeños de tamaño fijo que el procesador
puede copiar en un solo ciclo. Los tipos heap-allocated (texto, listas,
tensores grandes) no son copy y deben ser movidos o clonados explícitamente.

---

## ownership y tensors

Los tensores de tipo fijo se mueven como cualquier otro valor:

```synapse
funcion ejemplo():
    variable numeros = [1, 2, 3, 4, 5]
    variable suma = sumar_numeros(numeros)  // movimiento

    // numeros ya no es válido
    // numeros[0] = 99  // Error de compilación

    imprimir(suma)  // 15

funcion sumar_numeros(nums: tensor[5] entero) -> entero:
    variable total = 0
    para n en nums:
        total += n
    retornar total
```

### Tensores como borrowing

Para pasar un tensor sin moverlo, usa referencia:

```synapse
funcion imprimir_numeros(nums: tensor[&] entero):
    para n en nums:
        imprimir(n)

funcion ejemplo():
    variable numeros = [1, 2, 3, 4, 5]
    imprimir_numeros(&numeros)  // préstamo inmutable
    imprimir_numeros(&numeros)  // OK: sigue válido
    imprimir(numeros)           // OK: sigue válido
```

---

## ownership y registros

Los registros se mueven por defecto. Para clonarlos, implementa `clonar()`:

```synapse
registro Persona:
    nombre: texto
    edad: entero

funcion ejemplo():
    variable a = Persona { nombre: "Ana", edad: 30 }
    variable b = a  // movimiento

    // a ya no es válido
    // imprimir(a.nombre)  // Error

    imprimir(b.nombre)  // Ana
```

### Clonación de registros

```synapse
registro Persona:
    nombre: texto
    edad: entero

    funcion clonar() -> Persona:
        retornar Persona {
            nombre: self.nombre.clonar(),
            edad: self.edad
        }

funcion ejemplo():
    variable a = Persona { nombre: "Ana", edad: 30 }
    variable b = a.clonar()

    // Ambas son válidas
    imprimir(a.nombre)  // Ana
    imprimir(b.nombre)  // Ana
```

---

## ownership y función principal

La función principal es el dueño inicial de todo:

```synapse
funcion principal():
    variable archivo = abrir_archivo("datos.syn")
    variable datos = leer_archivo(archivo)
    procesar(datos)
    // 'datos' se libera aquí
    // 'archivo' se libera aquí (cerrado automáticamente)
```

---

## Resumen

| Concepto     | Descripción                                         | Ejemplo                      |
|--------------|-----------------------------------------------------|------------------------------|
| Ownership    | Un dueño único por valor                            | `variable a = [1, 2, 3]`     |
| Move         | Transferir ownership                                | `variable b = a`             |
| Clone        | Copia profunda explícita                            | `variable b = a.clonar()`    |
| Copy types   | Tipos que se copian automáticamente                | `variable y = x` (enteros)   |
| Drop         | Liberación automática al salir de ámbito            | Implícito al final de scope  |

Ownership es lo que permite a Synapse ofrecer seguridad de memoria sin garbage
collector. Las reglas son simples pero el compilador las verifica
estrictamente, eliminando categorías enteras de bugs en tiempo de compilación.
