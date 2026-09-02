# Procesamiento de Datos en Syquex

Este capítulo explora técnicas de procesamiento de datos en Syquex: transformación, filtrado, agregación y más. Aprenderás a procesar colecciones de datos de forma declarativa y eficiente.

El procesamiento de datos es una de las fortalezas de Syquex, con soporte nativo para operaciones funcionales.

<!-- cumple Manual 3 §5.2 -->

## 1. Operaciones Funcionales sobre Listas

### `mapear` (Transformación)

```syquex
let numeros = [1, 2, 3, 4, 5]
let cuadrados = numeros.mapear(lambda x: x * x)
// [1, 4, 9, 16, 25]
```

### `filtrar` (Selección)

```syquex
let pares = numeros.filtrar(lambda x: x % 2 == 0)
// [2, 4]
```

### `reducir` / `fold` (Agregación)

```syquex
let suma = numeros.reducir(lambda acc, x: acc + x, 0)
// 15

let producto = numeros.reducir(lambda acc, x: acc * x, 1)
// 120
```

### `encontrar` (Búsqueda)

```syquex
let encontrado = numeros.encontrar(lambda x: x > 3)
// ok(4)

let no_encontrado = numeros.encontrar(lambda x: x > 100)
// ninguno
```

## 2. Operaciones sobre Mapas

### Transformación de Mapas

```syquex
let precios = {"manzana": 1.20, "banana": 0.80, "naranja": 1.50}

// Transformar valores
let con_iva = precios.cada_valor_mapear(lambda precio: precio * 1.21)
// {"manzana": 1.452, "banana": 0.968, "naranja": 1.815}

// Filtrar entradas
let economicos = precios.filtrar(lambda k, v: v < 1.0)
// {"banana": 0.80}
```

### Agrupación

```syquex
let ventas = [
    ("Ana", 100),
    ("Beto", 200),
    ("Ana", 150),
    ("Beto", 50)
]

let por_usuario = ventas.agrupar(lambda v: v[0])
// {"Ana": [("Ana", 100), ("Ana", 150)], "Beto": [("Beto", 200), ("Beto", 50)]}
```

## 3. Operaciones sobre Strings

```syquex
let texto = "  Hola Mundo  "

// Transformaciones
texto.trim()            // "Hola Mundo"
texto.mayusculas()      // "  HOLA MUNDO  "
texto.minusculas()      // "  hola mundo  "
texto.reemplazar("Mundo", "Syquex")

// División y unión
let palabras = texto.trim().dividir(" ")
// ["Hola", "Mundo"]

let joined = palabras.unir("-")
// "Hola-Mundo"

// Validación
si texto.contiene("Hola"):
    io.escribir_linea("Contiene Hola")
```

## 4. Procesamiento Asíncrono

### Streams

```syquex
async funcion leer_stream_datos(url: texto) -> Stream<entero>:
    let respuesta = await http.get(url)
    retornar respuesta.body.como_stream<entero>()

// Procesar stream con operaciones
let stream = await leer_stream_datos("https://api.ejemplo.com/numeros")

let resultado = stream
    .filtrar(lambda x: x > 0)
    .mapear(lambda x: x * 2)
    .tomar(10)  // Primeros 10 resultados
    .collect()  // Convertir a Lista
```

### Procesamiento en Paralelo

```syquex
async funcion procesar_lote(datos: Lista<entero>) -> Lista<entero>:
    retornar await datos
        .paralelo_mapear(4, async lambda x:
            // Cada elemento procesado en paralelo (4 workers)
            await proceso_intenso(x)
        )
        .filtrar(lambda x: x > 0)
```

## 5. Joins y Relaciones

```syquex
estructura Usuario:
    id: entero
    nombre: texto
    email: texto

estructura Pedido:
    id: entero
    usuario_id: entero
    total: decimal

let usuarios = [
    Usuario(1, "Ana", "ana@e.com"),
    Usuario(2, "Beto", "beto@e.com")
]

let pedidos = [
    Pedido(1, 1, 100.0),
    Pedido(2, 2, 250.0),
    Pedido(3, 1, 50.0)
]

// JOIN interno
let resultado = usuarios.join(pedidos, 
    lambda u: u.id,
    lambda p: p.usuario_id,
    lambda u, p: (u.nombre, p.total)
)
// [("Ana", 100.0), ("Beto", 250.0), ("Ana", 50.0)]
```

## 6. Agregaciones y Estadísticas

```syquex
let datos = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

let stats = datos.estadisticas()
io.escribir_linea("Promedio: " + stats.promedio.texto())
io.escribir_linea("Mínimo: " + stats.minimo.texto())
io.escribir_linea("Máximo: " + stats.maximo.texto())
io.escribir_linea("Desviación: " + stats.desviacion.texto())

// Agrupar y contar
let grupos = datos.agrupar(lambda x: si x < 50: "bajo" sino: "alto")
io.escribir_linea("Bajos: " + grupos["bajo"].len().texto())
io.escribir_linea("Altos: " + grupos["alto"].len().texto())
```

## 7. Operaciones con JSON

```syquex
importar lib.json

// Parsear JSON
let datos_json = '{"nombre": "Ana", "edad": 28, "skills": ["Python", "C"]}'
let usuario = datos_json.parse_json()
// usuario.nombre -> "Ana"
// usuario.skills[0] -> "Python"

// Serializar a JSON
let datos = {"producto": "Laptop", "precio": 999.99}
let json_str = datos.a_json(pretty: true)
```

## Ejemplo Completo

```syquex
#lang: es
importar lib.io
importar lib.lista

estructura Venta:
    fecha: texto
    producto: texto
    cantidad: entero
    precio_unitario: decimal

funcion principal():
    let ventas = [
        Venta("2024-01-15", "Laptop", 2, 999.99),
        Venta("2024-01-15", "Mouse", 10, 25.50),
        Venta("2024-01-16", "Laptop", 1, 999.99),
        Venta("2024-01-16", "Teclado", 5, 75.00)
    ]
    
    // Total por producto
    let por_producto = ventas
        .agrupar(lambda v: v.producto)
        .cada_valor_mapear(lambda ventas_lista:
            ventas_lista
                .mapear(lambda v: v.cantidad * v.precio_unitario)
                .reducir(lambda acc, total: acc + total, 0.0)
        )
    
    // Reporte
    io.escribir_linea("=== Ventas por Producto ===")
    para producto, total en por_producto.items():
        io.escribir_linea(producto + ": $" + total.texto())
```

## Referencias

- **Manual 3 §5.2**: Tipos de colecciones (Lista, Mapa)
- **Manual 3 §12.1**: Biblioteca estándar de módulos
- **Manual 2 §4.3**: Tipos compuestos

// cumple Manual 3 §5
