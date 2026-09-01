# Coincidencia de Patrones (coincidir)

`coincidir` es la herramienta de coincidencia de patrones de Synapse. Es
similar a `switch` en C pero con soporte para patrones, desestructuración
y verificación exhaustiva. El compilador verifica que todos los casos posibles
estén cubiertos.

---

## Sintaxis básica

```synapse
variable dia = "lunes"

coincidir dia:
    caso "lunes":
        imprimir("Inicio de semana")
    caso "viernes":
        imprimir("Casi fin de semana")
    caso "sabado" | "domingo":
        imprimir("Fin de semana")
    otro:
        imprimir("Día laboral")
```

El bloque `otro` captura cualquier valor no coincidente. Es equivalente a
un `default` pero con nombre más expresivo.

---

## Cases con valores

### Coincidencia exacta

```synapse
variable color = "rojo"

coincidir color:
    caso "rojo":
        imprimir("Detener")
    caso "amarillo":
        imprimir("Precaución")
    caso "verde":
        imprimir("Avanzar")
```

### Múltiples valores por caso

```synapse
variable mes = 8

coincidir mes:
    caso 12 | 1 | 2:
        imprimir("Invierno")
    caso 3 | 4 | 5:
        imprimir("Primavera")
    caso 6 | 7 | 8:
        imprimir("Verano")
    caso 9 | 10 | 11:
        imprimir("Otoño")
```

---

## Patrones con valores

### Coincidencia con rangos

```synapse
variable nota = 85

coincidir nota:
    caso 90..=100:
        imprimir("Sobresaliente")
    caso 80..89:
        imprimir("Notable")
    caso 70..79:
        imprimir("Bien")
    caso 60..69:
        imprimir("Suficiente")
    caso 0..59:
        imprimir("Insuficiente")
    otro:
        imprimir("Nota inválida")
```

### Coincidencia con guardias

```synapse
variable edad = 25

coincidir edad:
    caso n si n < 0:
        imprimir("Edad inválida")
    caso n si n < 13:
        imprimir("Niño")
    caso n si n < 18:
        imprimir("Adolescente")
    caso n si n < 65:
        imprimir("Adulto")
    otro:
        imprimir("Adulto mayor")
```

---

## Cases con `ok` y `err`

`coincidir` se integra naturalmente con el tipo `resultado(T, E)`:

```synapse
funcion dividir(a: decimal, b: decimal) -> resultado(decimal, texto):
    si b == 0.0:
        retornar err("División por cero")
    retornar ok(a / b)

funcion ejemplo():
    variable resultado = dividir(10.0, 3.0)
    coincidir resultado:
        caso ok(valor):
            imprimir("Resultado: ", valor)
        caso err(mensaje):
            imprimir("Error: ", mensaje)
```

### Con tipos de error diferentes

```synapse
registro ErrorRed:
    codigo: entero
    mensaje: texto

registro ErrorIO:
    archivo: texto
    razon: texto

funcion conectar(url: texto) -> resultado(conexion, texto):
    // ...
    retornar err("No se pudo conectar")

funcion ejemplo():
    variable r = conectar("https://api.ejemplo.com")
    coincidir r:
        caso ok(conexion):
            imprimir("Conectado a: ", conexion.url)
        caso err(msg):
            imprimir("Error de conexión: ", msg)
```

---

## Wildcard _

El wildcard `_` coincide con cualquier valor sin capturarlo:

```synapse
variable codigo = 404

coincidir codigo:
    caso 200:
        imprimir("OK")
    caso 301:
        imprimir("Redirección")
    caso 404:
        imprimir("No encontrado")
    caso _:
        imprimir("Código desconocido: ", codigo)
```

### `_` en patrones compuestos

```synapse
variable respuesta = [200, "OK", 1.5]

coincidir respuesta:
    caso [200, _, _]:
        imprimir("Respuesta exitosa")
    caso [404, _, _]:
        imprimir("No encontrado")
    caso [c, msg, _] si c >= 500:
        imprimir("Error del servidor: ", msg)
    caso _:
        imprimir("Respuesta inesperada")
```

---

## Patrones exhaustivos

El compilador verifica que todos los valores posibles estén cubiertos.
Si falta un caso, produce un error de compilación:

```synapse
registro Color:
    variante Rojo
    variante Verde
    variante Azul

variable c = Color.Rojo

// Error de compilación: falta el caso Azul
// coincidir c:
//     caso Rojo:
//         imprimir("Rojo")
//     caso Verde:
//         imprimir("Verde")

// Correcto: todos los casos cubiertos
coincidir c:
    caso Rojo:
        imprimir("Rojo")
    caso Verde:
        imprimir("Verde")
    caso Azul:
        imprimir("Azul")
```

Esto garantiza que si agregas un nuevo variante al registro, el compilador
te avisa en todos los lugares que debes actualizar.

---

## `coincidir` como expresión

`coincidir` puede retornar un valor:

```synapse
variable tipo = "entero"

variable tamaño = coincidir tipo:
    caso "byte"     -> 1
    caso "entero"   -> 8
    caso "decimal"  -> 8
    caso "booleano" -> 1
    caso _          -> 0

imprimir("Tamaño: ", tamaño, " bytes")  // 8
```

---

## Desestructuración

### Registros

```synapse
registro Punto:
    x: decimal
    y: decimal

variable p = Punto { x: 3.0, y: 4.0 }

coincidir p:
    caso Punto { x: 0.0, y: 0.0 }:
        imprimir("Origen")
    caso Punto { x: _, y: 0.0 }:
        imprimir("Sobre eje X")
    caso Punto { x: 0.0, y: _ }:
        imprimir("Sobre eje Y")
    caso Punto { x, y }:
        imprimir("Punto general: ", x, ", ", y)
```

### Tensores

```synapse
variable punto = [3.0, 4.0]

coincidir punto:
    caso [0.0, 0.0]:
        imprimir("Origen")
    caso [x, 0.0]:
        imprimir("Sobre eje X en ", x)
    caso [0.0, y]:
        imprimir("Sobre eje Y en ", y)
    caso [x, y]:
        imprimir("Punto: ", x, ", ", y)
```

---

## Ejemplo práctico: parser de comandos

```synapse
registro Comando:
    variante Salir
    variante Guardar(archivo: texto)
    variante Buscar(texto: texto, sensibilidad: booleano)
    variante Configurar(clave: texto, valor: texto)

funcion ejecutar(comando: Comando):
    coincidir comando:
        caso Salir:
            imprimir("Saliendo del programa...")
        caso Guardar(archivo):
            imprimir("Guardando en: ", archivo)
        caso Buscar(texto, verdadero):
            imprimir("Buscando (case-sensitive): ", texto)
        caso Buscar(texto, falso):
            imprimir("Buscando (case-insensitive): ", texto)
        caso Configurar(clave, valor):
            imprimir("Config: ", clave, " = ", valor)

funcion ejemplo():
    ejecutar(Guardar("documento.syn"))
    ejecutar(Buscar("funcion", falso))
    ejecutar(Configurar("tema", "oscuro"))
    ejecutar(Salir)
```

---

## Resumen

| Patrón              | Ejemplo                              | Descripción                    |
|---------------------|--------------------------------------|--------------------------------|
| Valor exacto        | `caso 42:`                           | Coincidencia literal           |
| Múltiples valores   | `caso 1 \| 2 \| 3:`                 | OR lógico                      |
| Rango               | `caso 10..20:`                       | Rango inclusivo                |
| Guardia             | `caso n si n > 0:`                   | Condición adicional            |
| Wildcard            | `caso _:`                            | Cualquier valor                |
| Ok/Err              | `caso ok(v):`                        | Resultado exitoso              |
| Desestructuración   | `caso Punto { x, y }:`              | Extraer campos                 |

`coincidir` es una de las construcciones más poderosas de Synapse. La
verificación exhaustiva elimina bugs por casos no manejados, y la
integración con registros y resultados facilita el manejo de errores.
