# Lifetimes en Synapse

Los lifetimes (tiempos de vida) son las reglas que determinan cuánto
"vive" una referencia. El compilador verifica automáticamente que cada
referencia apunte a un dato que sigue existiendo. Este capítulo explica
cómo funcionan las anotaciones de lifetime y cuándo son necesarias.

---

## ¿Por qué existen los lifetimes?

Sin lifetimes, podrías crear una referencia a memoria que ya fue liberada:

```synapse
// Sin lifetimes, esto sería peligroso:
funcion ejemplo() -> &texto:
    variable local = "hola"
    retornar &local  // ERROR: 'local' se libera al salir
    // La referencia apuntaría a memoria liberada
```

El compilador detecta esto automáticamente y produce un error de compilación.
Los lifetimes son la anotación explícita que le dice al compilador la
relación de duración entre referencias y los datos a los que apuntan.

---

## Anotaciones de lifetime

### Sintaxis básica

```synapse
funcion mas_largo<'a>(a: &'a texto, b: &'a texto) -> &'a texto:
    si a.longitud >= b.longitud:
        retornar a
    retornar b
```

El parámetro `'a` es un parámetro de lifetime. Indica que las referencias
`a` y `b` viven al menos tanto como el valor de retorno.

### Sin anotaciones (inferencia)

En muchos casos, el compilador puede inferir los lifetimes:

```synapse
// El compilador infiere los lifetimes automáticamente
funcion mas_largo(a: &texto, b: &texto) -> &texto:
    si a.longitud >= b.longitud:
        retornar a
    retornar b
```

Las anotaciones explícitas solo son necesarias cuando hay ambigüedad.

---

## Reglas de lifetime

### Regla 1: Las referencias no pueden vivir más que los datos

```synapse
funcion ejemplo() -> &texto:
    // Error: la referencia sobrevive a los datos
    // variable resultado: &texto
    // {
    //     variable local = "temporal"
    //     resultado = &local
    // }  // local se libera aquí
    // retornar resultado  // ERROR: resultado apunta a memoria liberada

    // Correcto: retornar el valor, no una referencia
    variable local = "temporal"
    retornar local
```

### Regla 2: Las referencias deben ser válidas durante todo su uso

```synapse
funcion ejemplo():
    variable referencia: &entero
    {
        variable datos = 42
        referencia = &datos
        imprimir(referencia)  // OK: datos sigue existiendo
    }
    // Error: datos se liberó, referencia ya no es válida
    // imprimir(referencia)
```

### Regla 3: No puedes prestar mut si hay referencias inmutables activas

```synapse
funcion ejemplo():
    variable datos = [1, 2, 3]
    variable ref1 = &datos       // inmutable
    variable ref2 = &datos       // otra inmutable (OK)
    // Error: no puedes prestar mut con referencias inmutables activas
    // variable ref3 = &mut datos
    imprimir(ref1[0], ref2[0])
    // ref1 y ref2 deben terminar antes de prestar mut
    variable ref3 = &mut datos
    ref3[0] = 99
```

---

## Lifetimes en estructuras

Cuando una estructura contiene referencias, necesita parámetros de lifetime:

```synapse
registro Busqueda<'a>:
    texto_original: &'a texto
    resultados: tensor[10] &'a texto
    cantidad: entero

funcion buscar<'a>(fuente: &'a texto, patron: &texto) -> Busqueda<'a>:
    variable resultados: tensor[10] &texto
    variable count = 0
    // ... lógica de búsqueda
    retornar Busqueda {
        texto_original: fuente,
        resultados: resultados,
        cantidad: count
    }
```

El lifetime `'a` indica que la estructura `Busqueda` no puede vivir más
que el texto al que referencia.

---

## Lifetime estático

Un lifetime `'estatico` dura durante toda la ejecución del programa.
Los literales de texto tienen lifetime estático:

```synapse
// Los literales de texto son 'static
variable texto: &texto = "hola mundo"  // lifetime 'static

funcion ejemplo() -> &texto:
    retornar "retorno un literal"  // OK: 'static lifetime
```

### Cuándo usar `'static`

```synapse
// Errores con lifetime estático
constante ERROR_SERVIDOR: texto = "Error de servidor"

funcion obtener_error() -> &texto:
    retornar &ERROR_SERVIDOR  // OK: 'static

// Datos generados dinámicamente NO son 'static
funcion peligrosa() -> &texto:
    // variable local = "temporal"
    // retornar &local  // ERROR: no es 'static
    retornar "OK"  // OK: literal es 'static
```

---

## Errores comunes de lifetime

### Error: referencia a variable local

```synapse
// Error típico y su corrección
funcion incorrecta() -> &texto:
    variable resultado = "procesado"
    // retornar &resultado  // ERROR

funcion correcta() -> texto:
    variable resultado = "procesado"
    retornar resultado  // OK: retorna owned value
```

### Error: referencia sobrevive al dato

```synapse
funcion ejemplo():
    variable referencia: &tensor[&] entero
    {
        variable datos = [1, 2, 3]
        referencia = &datos
    }
    // Error: datos se liberó
    // imprimir(referencia)

    // Correcto: usar los datos dentro del scope
    {
        variable datos = [1, 2, 3]
        referencia = &datos
        imprimir(referencia[0])  // OK dentro del scope
    }
```

### Error: retorno de referencia a datos temporales

```synapse
// Error
// funcion procesar() -> &texto:
//     variable temp = texto.concat("a", "b")
//     retornar &temp  // ERROR: temp se libera

// Correcto: retornar owned value
funcion procesar() -> texto:
    variable temp = texto.concat("a", "b")
    retornar temp
```

---

## Ejemplo práctico: buffer de búsqueda

```synapse
registro Buffer<'a>:
    datos: &'a tensor[&] entero
    capacidad: entero
    posicion: entero

impl<'a> Buffer<'a>:
    funcion nuevo(datos: &'a tensor[&] entero) -> Buffer<'a>:
        retornar Buffer {
            datos: datos,
            capacidad: datos.longitud,
            posicion: 0
        }

    funcion siguiente(&mut self) -> opcional(&'a entero):
        si self.posicion >= self.capacidad:
            retornar nada
        variable resultado = &self.datos[self.posicion]
        self.posicion += 1
        retornar opcion(resultado)

funcion ejemplo():
    variable numeros = [10, 20, 30, 40, 50]
    variable buffer = Buffer.nuevo(&numeros)

    // Iterar sobre el buffer
    mientras buffer.posicion < buffer.capacidad:
        variable siguiente = buffer.siguiente()
        si siguiente.es_algo():
            imprimir(siguiente.valor())
```

---

## Lifetimes y genéricos

Los lifetimes pueden combinarse con parámetros de tipo:

```synapse
funcion primer_elemento<'a, T>( datos: &'a tensor[&] T) -> &'a T:
    retornar &datos[0]

funcion ejemplo():
    variable enteros = [1, 2, 3]
    variable texto = ["a", "b", "c"]

    variable primero_entero = primer_elemento(&enteros)
    variable primero_texto = primer_elemento(&texto)

    imprimir(primero_entero)  // 1
    imprimir(primero_texto)   // a
```

---

## Resumen

| Concepto            | Descripción                                           |
|---------------------|-------------------------------------------------------|
| `'a`                | Parámetro de lifetime genérico                        |
| `'static`           | Lifetime que dura toda la ejecución del programa      |
| Inferencia          | El compilador deduce lifetimes cuando es posible      |
| Referencia local    | Error: no puedes retornar referencia a variable local |
| Exclusividad        | No puedes mezclar mutable e inmutable simultáneamente |

Los lifetimes son la herramienta que hace posible el borrowing seguro en
Synapse. La mayoría de las veces el compilador los infiere automáticamente;
solo necesitas anotarlos explícitamente en funciones públicas complejas
y estructuras con referencias. Cuando el compilador te pide una anotación
de lifetime, es porque hay una relación de duración que necesita verificarse.
