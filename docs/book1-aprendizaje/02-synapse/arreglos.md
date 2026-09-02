# Arreglos en Synapse

Synapse ofrece dos tipos de colecciones principales: arreglos de tamaño fijo
y listas dinámicas. Ambos son tipados y seguros en memoria.

## Arreglos Fijos [T; N]

Los arreglos fijos tienen un tamaño determinado en tiempo de compilación.
Se declaran con la sintaxis `[tipo; tamaño]`.

```synapse
// Declaración
let numeros: [entero; 5] = [1, 2, 3, 4, 5]
let letras: [caracter; 3] = ['a', 'b', 'c']
let ceros: [flotante; 10] = [0.0; 10] // Inicializar todos con 0

// Acceso por índice (0-based)
let primero = numeros[0]   // 1
let ultimo = numeros[4]     // 5
numeros[2] = 100            // Modificar valor

// Longitud (comptime)
let len = numeros.longitud() // 5

// Iterar
for valor in numeros {
    log("{valor}")
}

// Iterar con índice
for i in 0..numeros.longitud() {
    log("numeros[{i}] = {numeros[i]}")
}

// Desestructurar
let [a, b, c, ..resto] = numeros
log("a={a}, b={b}, c={c}, resto={resto}")
```

## Inicialización Avanzada de Arreglos

```synapse
// Arreglo con expresión de inicialización
let cuadrados: [entero; 5] = [para i in 0..5 { i * i }]

// Arreglo con condición
let impares: [entero; 5] = [
    para i in 0..10 {
        if i % 2 != 0 { i }
    }
]

// Arreglo multidimensional
let matriz: [[entero; 3]; 3] = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]
let elemento = matriz[1][2] // 6

// Copia de arreglos (copia en stack)
let original = [1, 2, 3]
let copia = original
copia[0] = 99
log("Original: {original[0]}") // Sigue siendo 1
log("Copia: {copia[0]}")       // 99
```

## Listas Dinámicas

Las listas crecen y encogen en tiempo de ejecución. Se declaran con `Lista<T>`.

```synapse
// Crear lista
let lista = Lista::nueva()
let con_capacidad = Lista::con_capacidad(100)

// Con datos iniciales
let numeros = Lista::desde([1, 2, 3, 4, 5])

// Agregar elementos
lista.agregar(42)
lista.agregar(99)
lista.insertar(0, 7) // Insertar en índice 0

// Acceso
let primero = numeros[0]
let ultimo = numeros[numeros.longitud() - 1]

// Modificar
numeros[2] = 100

// Eliminar
let eliminado = numeros.eliminar(2)      // Por índice
let valor = numeros.eliminar_valor(100)  // Por valor

// Buscar
let indice = numeros.indice_de(100) // -1 si no existe
let contiene = numeros.contiene(42)  // true/false

// Longitud
let len = numeros.longitud()
let esta_vacia = numeros.esta_vacia()
```

## Operaciones con Listas

```synapse
let lista = [3, 1, 4, 1, 5, 9, 2, 6]

// Ordenar
lista.ordenar()                  // Ascendente
lista.ordenar(|a, b| b - a)     // Descendente

// Invertir
lista.invertir()

// Mezclar aleatoriamente
lista.mezclar()

// Filtrar
let mayores = lista.filtrar(|x| x > 3) // [4, 5, 9, 6]

// Mapear
let duplicados = lista.mapear(|x| x * 2) // [6, 2, 8, 2, 10, 18, 4, 12]

// Reducir
let suma = lista.reducir(0, |acc, x| acc + x) // 31

// Encontrar
let primero_par = lista.encontrar(|x| x % 2 == 0) // 4

// Verificar todos
let todos_positivos = lista.todos(|x| x > 0) // true

// Existe
let existe_mayor_8 = existe(lista, |x| x > 8) // true

// Tomar/dejar
let primeros_3 = lista.tomar(3)     // [3, 1, 4]
let restos = lista.dejar(3)          // [1, 5, 9, 2, 6]

// Aplanar
let anidada = [[1, 2], [3, 4], [5, 6]]
let plana = anidada.aplanar() // [1, 2, 3, 4, 5, 6]
```

## Mapas (Diccionarios)

Los mapas asocian claves con valores. Se declaran con `Mapa<K, V>`.

```synapse
let edades = Mapa::nuevo()
edades["Ana"] = 25
edades["Bob"] = 30
edades["Carol"] = 22

// Acceso
let edad_ana = edades["Ana"]       // 25
let existe = edades.contiene("Bob") // true

// Eliminar
edades.eliminar("Bob")

// Iterar
for (clave, valor) in edades {
    log("{clave}: {valor}")
}

// Claves y valores
let claves = edades.claves()
let valores = edades.valores()

// Mapa con inicialización
let precios = Mapa::desde({
    "manzana" => 1.50,
    "naranja" => 2.00,
    "plátano" => 0.75
})
```

## Tuplas

Las tuplas agrupan valores de diferentes tipos con tamaño fijo:

```synapse
// Declaración
let par: (entero, cadena) = (42, "respuesta")
let triplet: (flotante, entero, caracter) = (3.14, 7, 'x')

// Acceso
let val = par.0  // 42
let txt = par.1  // "respuesta"

// Desestructurar
let (num, texto) = par

// Tupla vacía (unidad)
let unidad: () = ()
```
