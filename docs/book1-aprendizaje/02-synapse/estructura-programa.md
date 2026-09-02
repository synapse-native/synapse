# Estructura de un Programa en Synapse

Todo programa Synapse comienza con un archivo `.syn`. Este capítulo explica
la estructura de un archivo, cómo se organizan los módulos, cómo se importan
dependencias y cuáles son las convenciones de formato.

---

## Archivo mínimo

El archivo más simple en Synapse contiene una función `principal`:

```synapse
funcion principal():
    imprimir("Hola, mundo")
```

Guárdalo como `hola.syn` y compílalo:

```
synapse build hola.syn
```

El compilador genera un ejecutable que imprime "Hola, mundo" y termina.

---

## Estructura de un archivo .syn

Un archivo Synapse tiene este orden:

```synapse
// 1. Comentarios al inicio del archivo
// Descripción del módulo

// 2. Imports
importar std.io
importar std.math

// 3. Constantes globales
constante MAXIMO_TAMANIO: entero = 1024

// 4. Registros y enums
registro Configuracion:
    host: texto
    puerto: entero

// 5. Funciones auxiliares
funcion privada validar(config: Configuracion) -> booleano:
    retornar config.puerto > 0

// 6. Función principal
funcion principal():
    variable config = Configuracion { host: "localhost", puerto: 8080 }
    si validar(config):
        imprimir("Configuración válida")
```

---

## Comentarios

### Comentarios de línea

```synapse
// Esto es un comentario de línea
variable x = 10  // Comentario al final de la línea
```

### Comentarios de bloque

```synapse
/*
 Este es un comentario
 que abarca múltiples líneas.
 Útil para explicar algoritmos complejos.
*/
funcion compleja():
    // ...
```

### Comentarios de documentación

```synapse
/// Calcula la raíz cuadrada de un número.
///
/// Parámetros:
///   x - El número no negativo
///
/// Retorna:
///   La raíz cuadrada de x
///
/// Errores:
///   Panics si x es negativo
funcion raiz_cuadrada(x: decimal) -> decimal:
    requiere: x >= 0.0
    retornar x.raiz()
```

---

## Imports

### Importar un módulo completo

```synapse
importar std.io

funcion ejemplo():
    std.io.imprimir("Usando el módulo io")
```

### Importar elementos específicos

```synapse
importar std.io.imprimir
importar std.math.{raiz, potencia}

funcion ejemplo():
    imprimir(raiz(16.0))  // 4.0
    imprimir(potencia(2.0, 10.0))  // 1024.0
```

### Importar con alias

```synapse
importar std.io as io
importar std.math as m

funcion ejemplo():
    io.imprimir(m.raiz(25.0))
```

---

## Módulos

Cada archivo `.syn` es un módulo. El nombre del archivo es el nombre del
módulo:

```
proyecto/
├── main.syn          // módulo principal
├── utils/
│   ├── math.syn      // módulo utils.math
│   └── string.syn    // módulo utils.string
└── models/
    └── usuario.syn   // módulo models.usuario
```

### Visibilidad

```synapse
// utils/math.syn

// Pública: accesible desde otros módulos
funcion publica sumar(a: entero, b: entero) -> entero: a + b

// Privada: solo accesible dentro de este módulo
funcion privada validar(x: entero) -> booleano: x >= 0

// Registro público
registro publico Punto:
    x: decimal
    y: decimal

// Constante pública
constante publico PI: decimal = 3.14159265358979
```

### Uso desde otros módulos

```synapse
// main.syn
importar utils.math

funcion principal():
    variable suma = utils.math.sumar(3, 4)
    variable punto = utils.math.Punto { x: 1.0, y: 2.0 }
    imprimir(suma)
```

---

## Función principal

La función `principal` es el punto de entrada del programa. No toma
parámetros y no retorna valor:

```synapse
funcion principal():
    // Todo el código de inicio va aquí
    variable args = argumentos_linea_comandos()
    procesar(args)
```

### Acceso a argumentos de línea de comandos

```synapse
funcion principal():
    variable args = argumentos_linea_comandos()
    si args.longitud < 2:
        imprimir("Uso: programa <archivo>")
        salir(1)

    variable archivo = args[1]
    procesar_archivo(archivo)
```

---

## Indentación y formato

Synapse usa indentación para definir bloques. La convención es:

- **4 espacios** por nivel de indentación (no tabs)
- **Una línea en blanco** entre funciones
- **Espacios alrededor** de operadores

```synapse
// Bien formateado
funcion ejemplo():
    variable x = 10
    si x > 5:
        imprimir("Mayor")
    sino:
        imprimir("Menor")

// Mal formateado
funcion ejemplo():
variable x = 10
si x>5:
imprimir("Mayor")
sino:
imprimir("Menor")
```

El formateador `synapse fmt` aplica estas convenciones automáticamente.

---

## Registros (estructuras)

```synapse
registro Animal:
    nombre: texto
    especie: texto
    edad: entero

registro Mascota:
    duenio: texto
    animal: Animal
    vacunada: booleano

funcion ejemplo():
    variable mascota = Mascota {
        duenio: "Carlos",
        animal: Animal { nombre: "Luna", especie: "Gato", edad: 3 },
        vacunada: verdadero
    }
    imprimir(mascota.animal.nombre)  // Luna
```

---

## Enums (variantes)

```synapse
registro Estado:
    variante Pendiente
    variante EnProgreso(porcentaje: decimal)
    variante Completado(fecha: texto)
    variante Fallido(razon: texto)

funcion mostrar_estado(estado: Estado):
    coincidir estado:
        caso Pendiente:
            imprimir("Pendiente")
        caso EnProgreso(p):
            imprimir("En progreso: ", p, "%")
        caso Completado(f):
            imprimir("Completado el ", f)
        caso Fallido(r):
            imprimir("Falló: ", r)
```

---

## Resumen

| Elemento            | Convención                                    |
|---------------------|-----------------------------------------------|
| Archivos            | `nombre_modulo.syn`                           |
| Funciones           | `camelCase` (ej: `mi_funcion`)                |
| Registros           | `PascalCase` (ej: `MiRegistro`)               |
| Constantes          | `SCREAMING_SNAKE_CASE` (ej: `MAXIMO_VALOR`)   |
| Imports             | `importar ruta.modulo`                         |
| Indentación         | 4 espacios                                    |
| Comentarios         | `//` para línea, `/* */` para bloque          |

La estructura de un programa Synapse está diseñada para ser legible y
organizada. El compilador no tolera ambigüedades, y las convenciones
facilitan el trabajo en equipo.
