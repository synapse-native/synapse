# Cadenas en Synapse

Las cadenas en Synapse son secuencias de caracteres UTF-8 inmutables.
Se escriben entre comillas dobles y soportan secuencias de escape.

## Declaración y Literales

```synapse
let nombre = "Synapse"
let saludo = "¡Hola, mundo!"
let vacia = ""
let con_escape = "Línea nueva\n\tTabulación"
let ruta = "C:\\usuarios\\datos"
let hex = "\x41\x42\x43" // "ABC"
```

## Operaciones Básicas

```synapse
let texto = "Programación en Synapse"

// Longitud en bytes
let bytes = texto.longitud()
log("Bytes: {bytes}")

// Longitud en caracteres
let chars = texto.caracteres()
log("Caracteres: {chars}")

// Concatenación
let completo = texto + " es divertido"
let repetido = "*".repetir(10)

// Subcadenas
let sub = texto.subcadena(0, 12) // "Programación"
let desde = texto.desde(18)      // "Synapse"

// Mayúsculas y minúsculas
let mayus = texto.mayusculas()
let minus = texto.minusculas()
```

## Búsqueda

```synapse
let texto = "El gato duerme en el sofá"

// Contiene
if texto.contiene("gato") {
    log("Encontrado")
}

// Posición de una subcadena
let pos = texto.indice_de("duerme") // 7
let no_existe = texto.indice_de("perro") // -1

// Última aparición
let ultimo = texto.ultimo_indice_de("el") // 17

// Empieza/termina con
let es_prefijo = texto.empieza_con("El")   // true
let es_sufijo = texto.termina_con("sofá") // true

// Contar ocurrencias
let cuenta = texto.contar("el") // 2
```

## Transformaciones

```synapse
let original = "  Hola Mundo  "

// Eliminar espacios
let limpio = original.recortar()        // "Hola Mundo"
let izq = original.recortar_izquierda() // "Hola Mundo  "
let der = original.recortar_derecha()   // "  Hola Mundo"

// Reemplazar
let resultado = texto.reemplazar("mundo", "planeta")

// Dividir
let partes = "a,b,c".dividir(",") // ["a", "b", "c"]
let lineas = "l1\nl2\nl3".dividir("\n")

// Unir
let unido = partes.unir(" - ") // "a - b - c"

// Invertir
let invertido = "abcde".invertir() // "edcba"
```

## Conversión con Otros Tipos

```synapse
// Entero a cadena
let num = 42
let num_str = num.a_cadena() // "42"
let num_hex = num.a_hex()    // "2a"
let num_bin = num.a_binario() // "101010"

// Decimal a cadena
let pi = 3.14159
let pi_str = pi.a_cadena()        // "3.14159"
let pi_fmt = pi.a_cadena(decimales: 2) // "3.14"

// Cadena a entero
let entero = "123".a_entero()       // 123
let entero_hex = "ff".a_entero(base: 16) // 255
let entero_fail = "abc".a_entero()  // error

// Cadena a decimal
let dec = "3.14".a_decimal() // 3.14

// Booleano a cadena
let verdadero = verdadero.a_cadena() // "verdadero"
let falso = falso.a_cadena()         // "falso"
```

## Manejo UTF-8

Las cadenas en Synapse son UTF-8 por lo que soportan caracteres internacionales:

```synapse
let emoji = "🚀"
log("Bytes: {emoji.longitud()}")  // 4 bytes
log("Caracteres: {emoji.caracteres()}") // 1 carácter

let acento = "ñ"
let chinese = "你好"
let arabic = "مرحبا"

// Iterar por caracteres
for caracter in "Synapse".caracteres() {
    log("{caracter}")
}

// Acceder por índice de carácter
let primer_car = "Hola"[0] // 'H'
let tercero = "Hola"[2]    // 'l'

// Combinaciones de caracteres
let combinado = "café" + " ☕"
```

## Formato de Cadenas

```synapse
let nombre = "Ana"
let edad = 25

// Interpolación
let mensaje = "Hola {nombre}, tienes {edad} años"

// Formateo con especificadores
let precio = 19.99
let fmt1 = "Precio: ${precio:.2f}"
let fmt2 = "Hex: {42:x}"
let fmt3 = "Bin: {42:b}"

// Repetir y rellenar
let linea = "=".repetir(40)
let centrado = "Título".centrar(20, ' ')
let relleno = "42".rellenar_izquierda(5, '0') // "00042"
```

## Comparación

```synapse
let a = "abc"
let b = "abd"
let c = "abc"

// Igualdad
assert que (a == c)
assert que (a != b)

// Orden lexicográfico
assert que (a < b)  // true, 'c' < 'd'
assert que (b > a)  // true

// Comparación sin distinción de mayúsculas
let ignorar = "Synapse".igual_a("synapse") // false
let normalizar = "Synapse".normalizar().igual_a("synapse".normalizar()) // true
```
