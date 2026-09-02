# Async/Await en Syquex

Este capítulo cubre la programación asíncrona en Syquex usando `async` y `await`. Aprenderás a escribir código no bloqueante que maneje miles de operaciones concurrentes de eficiente.

Async/await es la forma moderna de manejar operaciones de E/S en Syquex.

<!-- cumple Manual 3 §8 -->

## 1. Fundamentos

### Sintaxis Async/Await

```syquex
async funcion fetch_datos(url: texto) -> Resultado<texto, texto>:
    intentar:
        let respuesta = await http.get(url)
        retornar ok(respuesta.cuerpo)
    atrapar e:
        retornar err("Error: " + e)

// Llamar a la función async
funcion principal():
    let resultado = await fetch_datos("https://api.ejemplo.com/datos")
    coincidir resultado:
        caso ok(datos):
            io.escribir_linea(datos)
        caso err(e):
            io.escribir_linea(e)
```

## 2. Concurrencia con Fibras

Syquex hereda el modelo de fibras de Synapse (Manual 3 §8.1):

```syquex
funcion trabajador(id: entero, canal: Canal<texto>):
    canal <- "Trabajador " + id.texto() + " completado"

funcion principal():
    let c = Canal<texto>(10)
    
    // Lanzar múltiples fibras concurrentes
    lanzar trabajador(1, c)
    lanzar trabajador(2, c)
    lanzar trabajador(3, c)
    
    // Escuchar respuestas
    para i en 1..3:
        escuchar c:
            let msg = c ->
            io.escribir_linea(msg)
```

## 3. Async/Await con Fibras

```syquex
async funcion procesar_archivo(ruta: texto) -> Lista<texto>:
    let archivo = await fs.abrir(ruta)
    let contenido = await archivo.leer_lines()
    retornar contenido

async funcion main():
    // Ejecución concurrente
    let resultados = await Promise.all([
        procesar_archivo("file1.txt"),
        procesar_archivo("file2.txt"),
        procesar_archivo("file3.txt")
    ])
    
    para datos en resultados:
        io.escribir_linea("Procesado: " + datos.len().texto() + " líneas")

// Iniciar la ejecución async
await main()
```

## 4. Canales y Comunicación

```syquex
async funcion productor(canal: Canal<entero>):
    para i en 1..100:
        await sleep(100)  // 100ms
        canal <- i

async funcion consumidor(canal: Canal<entero>):
    escuchar canal:
        let valor = canal ->
        io.escribir_linea("Recibido: " + valor.texto())

funcion principal():
    let canal = Canal<entero>(10)
    lanzar productor(canal)
    lanzar consumidor(canal)
```

## 5. Manejo de Errores Async

```syquex
async funcion operacion_riesgosa():
    intentar:
        return await api.call()
    atrapar e:
        return err(e)

async funcion principal():
    let resultado = await operacion_riesgosa()
    retornar resultado
```

## 6. Timeout y Cancelación

```syquex
let futuro = async funcion_lenta()
let resultado = await Timeout(5000, futuro)  // 5 segundos de timeout

coincidir resultado:
    caso ok(valor): "Completado: " + valor.texto()
    caso err("timeout"): "Operación agotada en tiempo"
```

## 7. Streams y Transformaciones

```syquex
async funcion stream_datos(url: texto) -> Stream<decimal>:
    let respuesta = await http.get(url)
    retornar respuesta.body.como_stream()
        .mapear(lambda x: x.decimal())
        .filtrar(lambda x: x > 0)

// Consumir el stream
para valor en await stream_datos("https://api.ejemplo.com/ventas"):
    io.escribir_linea("Venta: " + valor.texto())
```

## Referencias

- **Manual 3 §8**: Concurrencia y comunicación en Syquex
- **Manual 2 §1**: Concurrencia con canales y fibras
- **Manual 3 §7**: Manejo de errores con `Resultado` y `?`

// cumple Manual 3 §8
