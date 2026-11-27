# Borrowing en Synapse

Borrowing (préstamo) te permite referenciar un valor sin tomar ownership.
Esto es esencial para pasar datos a funciones sin moverlos, y para
construir estructuras de datos que referencian otros valores.

---

## Referencias inmutables (&)

Una referencia inmutable permite leer un valor sin modificarlo. Puedes
tener múltiples referencias inmutables simultáneamente:

```synapse
funcion imprimir_longitud(texto: &texto) -> entero:
    retornar texto.longitud

funcion ejemplo():
    variable nombre = "Synapse"
    variable len1 = imprimir_longitud(&nombre)  // préstamo inmutable
    variable len2 = imprimir_longitud(&nombre)  // otro préstamo inmutable

    // Ambas referencias son válidas simultáneamente
    imprimir(len1)  // 7
    imprimir(len2)  // 7
    imprimir(nombre)  // "Synapse" sigue válido
```

### Múltiples referencias inmutables

```synapse
funcion sumar(a: &tensor[&] entero, b: &tensor[&] entero) -> entero:
    variable total = 0
    para i en 0..a.longitud:
        total += a[i] + b[i]
    retornar total

funcion ejemplo():
    variable v1 = [1, 2, 3]
    variable v2 = [4, 5, 6]
    // Ambas referencias coexisten porque son inmutables
    variable resultado = sumar(&v1, &v2)  // 21
    imprimir(resultado)
```

---

## Referencias mutables (&mut)

Una referencia mutable permite modificar el valor prestado. Solo puede
haber **una** referencia mutable a la vez, y no puede coexistir con
referencias inmutables:

```synapse
funcion incrementar(valor: &mut entero):
    valor += 1

funcion ejemplo():
    variable contador = 10
    incrementar(&mut contador)  // préstamo mutable
    imprimir(contador)  // 11
```

### Regla de exclusividad

```synapse
funcion ejemplo():
    variable datos = [1, 2, 3]

    // Error: no puedes tener inmutable y mutable a la vez
    // variable ref1 = &datos       // inmutable
    // variable ref2 = &mut datos   // mutable
    // imprimir(ref1[0])
    // ref2[0] = 99

    // Correcto: una a la vez
    variable ref1 = &datos
    imprimir(ref1[0])  // 1
    // ref1 sale de ámbito aquí

    variable ref2 = &mut datos
    ref2[0] = 99
    // ref2 se usa y termina aquí
```

---

## Reglas de borrowing

### Regla 1: No más de una referencia mutable a la vez

```synapse
funcion ejemplo():
    variable x = 10

    // Esto compila correctamente:
    variable r1 = &mut x
    r1 += 5
    // r1 ya no se usa después de esta línea

    variable r2 = &mut x
    r2 += 5
    imprimir(x)  // 20
```

### Regla 2: Las referencias mutables no pueden coexistir con inmutables

```synapse
funcion ejemplo():
    variable datos = [1, 2, 3, 4, 5]

    // Esto es válido porque no hay overlapping
    variable suma = sumar_todo(&datos)  // préstamo inmutable
    // suma ya no usa la referencia

    invertir(&mut datos)  // préstamo mutable
    imprimir(datos)  // [5, 4, 3, 2, 1]

funcion sumar_todo(datos: &tensor[&] entero) -> entero:
    variable total = 0
    para d en datos:
        total += d
    retornar total

funcion invertir(datos: &mut tensor[&] entero):
    variable i = 0
    variable j = datos.longitud - 1
    mientras i < j:
        intercambiar(&mut datos[i], &mut datos[j])
        i += 1
        j -= 1
```

### Regla 3: Las referencias deben ser válidas durante todo su uso

```synapse
funcion ejemplo() -> &texto:
    variable local = "hola"
    // Error: no puedes retornar una referencia a una variable local
    // La variable se libera al salir de la función
    // retornar &local

    // Correcto: retornar owned value
    retornar local
```

---

## Borrowing con funciones

### Pasar datos sin mover

```synapse
funcion procesar(datos: &tensor[&] entero):
    para d en datos:
        imprimir(d)

funcion ejemplo():
    variable numeros = [10, 20, 30, 40, 50]
    procesar(&numeros)  // préstamo inmutable
    procesar(&numeros)  // puedo llamar de nuevo
    imprimir(numeros)   // sigue válido
```

### Modificar datos desde una función

```synapse
funcion duplicar(datos: &mut tensor[&] entero):
    para i en 0..datos.longitud:
        datos[i] *= 2

funcion ejemplo():
    variable numeros = [1, 2, 3, 4, 5]
    duplicar(&mut numeros)
    imprimir(numeros)  // [2, 4, 6, 8, 10]
```

### Mezclar inmutables y mutables

```synapse
funcion estadisticas(datos: &tensor[&] decimal) -> registro:
    variable suma = 0.0
    variable minimo = datos[0]
    variable maximo = datos[0]

    para d en datos:
        suma += d
        si d < minimo:
            minimo = d
        si d > maximo:
            maximo = d

    retornar Estadisticas {
        promedio: suma / datos.longitud,
        minimo: minimo,
        maximo: maximo
    }

funcion ejemplo():
    variable valores = [3.14, 1.59, 2.65, 3.58, 9.79]
    variable stats = estadisticas(&valores)
    imprimir("Promedio: ", stats.promedio)
    imprimir("Mínimo: ", stats.minimo)
    imprimir("Máximo: ", stats.maximo)
```

---

## Borrowing y campos de registros

```synapse
registro Servidor:
    nombre: texto
    activo: booleano
    conexiones: entero

funcion estado(servidor: &Servidor) -> texto:
    si servidor.activo:
        retornar "Activo (" + servidor.conexiones.para_texto() + " conexiones)"
    retornar "Inactivo"

funcion activar(servidor: &mut Servidor):
    servidor.activo = verdadero

funcion ejemplo():
    variable srv = Servidor {
        nombre: "web-01",
        activo: falso,
        conexiones: 0
    }

    // Préstamo inmutable para leer
    imprimir(estado(&srv))  // "Inactivo"

    // Préstamo mutable para modificar
    activar(&mut srv)

    imprimir(estado(&srv))  // "Activo (0 conexiones)"
```

---

## Errores comunes de borrowing

### Error: usar después de prestar mut

```synapse
funcion ejemplo():
    variable datos = [1, 2, 3]
    variable ref = &mut datos
    ref[0] = 99
    // Error: datos fue prestado mut, no puedes usarlo
    // hasta que ref salga de ámbito
    // imprimir(datos)
    ref = &mut datos  // ref se reasigna, el anterior termina
    imprimir(datos)  // OK: ref ya no está activo
```

### Error: prestar mut dos veces

```synapse
funcion ejemplo():
    variable datos = [1, 2, 3]
    // Error: no puedes tener dos referencias mutables
    // variable r1 = &mut datos
    // variable r2 = &mut datos
    // r1[0] = 99
    // r2[0] = 88

    // Correcto: una a la vez
    variable r1 = &mut datos
    r1[0] = 99
    // r1 sale de ámbito
    variable r2 = &mut datos
    r2[0] = 88
```

### Error: retornar referencia local

```synapse
// Error
// funcion peligrosa() -> &texto:
//     variable local = "temporal"
//     retornar &local  // local se libera aquí

// Correcto: retornar owned value
funcion segura() -> texto:
    variable local = "temporal"
    retornar local
```

---

## Resumen

| Tipo de préstamo | Sintaxis        | Regla                                         |
|------------------|-----------------|-----------------------------------------------|
| Inmutable        | `&valor`        | Múltiples permitidas, no modifican            |
| Mutable          | `&mut valor`    | Una sola, exclusiva, puede modificar           |
| Campo            | `&mut registro.campo` | Presta solo el campo, no el registro  |

Borrowing es la herramienta que te permite usar datos de forma eficiente
sin transferir ownership. Las reglas de exclusividad previenen data races
en tiempo de compilación, lo cual es particularmente valioso en código
concurrente.
