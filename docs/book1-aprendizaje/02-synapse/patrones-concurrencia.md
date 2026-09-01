# Patrones de Concurrencia en Synapse

Los patrones de concurrencia son soluciones reutilizables para problemas
comunes de programación paralela. Synapse facilita estos patrones mediante
fibras y canales tipados.

## Productor-Consumidor

El patrón más básico: un productor genera datos y un consumidor los procesa.
Los canales actúan como buffer entre ambos.

```synapse
fn productor_consumidor() {
    let canal = Canal::nuevo()

    // Productor: genera datos
    lanzar {
        para i in 0..100 {
            let dato = generar_dato(i)
            canal <- enviar(dato)
        }
        canal <- enviar(Fin::de()) // Señal de fin
    }

    // Consumidor: procesa datos
    loop {
        escuchar canal: recibir => dato {
            match dato {
                Fin::de() => break,
                _ => procesar(dato)
            }
        }
    }
    log("Consumidor terminado")
}
```

## Fan-Out / Fan-In

Un productor envía trabajo a múltiples workers (fan-out) y los resultados
se agregan en un único canal (fan-in):

```synapse
fn fan_out_fan_in(datos: Lista<entero>) {
    let entrada = Canal::nuevo()
    let salida = Canal::nuevo()
    let num_workers = 4

    // Fan-out: lanzar workers
    para _ in 0..num_workers {
        lanzar {
            loop {
                escuchar entrada: recibir => dato {
                    if dato es Fin { break }
                    let resultado = procesar(dato)
                    salida <- enviar(resultado)
                }
            }
        }
    }

    // Enviar trabajo
    para d in datos {
        entrada <- enviar(d)
    }

    // Señalar fin a workers
    para _ in 0..num_workers {
        entrada <- enviar(Fin::de())
    }

    // Fan-in: recoger resultados
    let resultados = Lista::nueva()
    para _ in 0..datos.longitud() {
        escuchar salida: recibir => r {
            resultados.agregar(r)
        }
    }

    log("Procesados: {resultados.longitud()} elementos")
}
```

## Pipeline

Un patrón de tubería donde cada etapa procesa datos y pasa el resultado
a la siguiente. Ideal para transformaciones secuenciales:

```synapse
fn pipeline() {
    let canal_1 = Canal::nuevo()
    let canal_2 = Canal::nuevo()
    let canal_salida = Canal::nuevo()

    // Etapa 1: Lectura
    lanzar {
        loop {
            escuchar canal_1: recibir => linea {
                if linea es Fin { break }
                let tokens = parsear(linea)
                canal_2 <- enviar(tokens)
            }
        }
    }

    // Etapa 2: Transformación
    lanzar {
        loop {
            escuchar canal_2: recibir => tokens {
                if tokens es Fin { break }
                let transformado = transformar(tokens)
                canal_salida <- enviar(transformado)
            }
        }
    }

    // Alimentar pipeline
    let lineas = leer_archivo("datos.txt")
    for linea in lineas {
        canal_1 <- enviar(linea)
    }

    // Recoger resultados
    let resultados = Lista::nueva()
    loop {
        escuchar canal_salida: recibir => resultado {
            if resultado es Fin { break }
            resultados.agregar(resultado)
        }
    }

    log("Pipeline completado: {resultados.longitud()} resultados")
}
```

## Worker Pool

Un grupo fijo de workers que comparten una cola de trabajo. Útil cuando
el número de tareas es dinámico:

```synapse
fn worker_pool(num_workers: entero) {
    let cola = Canal::nueva()
    let resultados = Canal::nuevo()

    // Lanzar pool de workers
    para id in 0..num_workers {
        lanzar {
            worker(id, cola, resultados)
        }
    }

    // Enviar tareas
    para tarea in generar_tareas() {
        cola <- enviar(tarea)
    }

    // Cerrar cola
    para _ in 0..num_workers {
        cola <- enviar(Fin::de())
    }

    // Recoger resultados
    let total = 0
    para _ in 0..num_workers {
        escuchar resultados: recibir => r {
            total += r
        }
    }
    log("Total procesado: {total}")
}

fn worker(id: entero, cola: Canal<Tarea>, salida: Canal<entero>) {
    loop {
        escuchar cola: recibir => tarea {
            if tarea es Fin { break }
            let resultado = ejecutar(tarea)
            salida <- enviar(resultado)
        }
    }
    log("Worker {id} terminado")
}
```

## Patrón de Señalización

Una fibras espera una condición que otra fibras notifica:

```synapse
fn senalizacion() {
    let evento = Canal::nuevo()

    // Esperador
    lanzar {
        log("Esperando evento...")
        escuchar evento: recibir => msg {
            log("Recibido: {msg}")
        }
    }

    // Notificador
    lanzar {
        dormir(milisegundos: 1000)
        evento <- enviar("¡Listo!")
    }

    esperar_todas()
}
```

## Consideraciones

- **Capacidad de canales**: Los canales bloquean al emisor si están llenos.
  Use `Canal::con_capacidad(n)` para buffers.
- **Cancelación**: Use contextos de cancelación para detener fibras
  limpiamente.
- **Deadlock**: Evite enviar y recibir en la misma fibras sin otra
  fibras que provea el dato.
