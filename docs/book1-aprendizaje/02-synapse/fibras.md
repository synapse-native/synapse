# Fibras en Synapse

Las fibras son procesos ultraligeros cooperativos que permiten concurrencia sin el
overhead de los hilos del sistema operativo. A diferencia de los hilos, las fibras
se gestionan en espacio de usuario y ceden el control de forma explícita.

## Fibras vs Hilos

| Característica | Hilos | Fibras |
|----------------|-------|--------|
| Gestión | Sistema operativo | Espacio de usuario |
| Conmutación | preemptiva | cooperativa |
| Coste de creación | Alto (~1MB pila) | Bajo (~4KB pila) |
| Conmutación | ~1000ns | ~10ns |
| Paralelismo real | Sí (multiprocesador) | No (un solo núcleo) |

Las fibras son ideales para E/S intensiva, servidores concurrentes y patrones
de productor-consumidor donde miles de tareas deben ejecutarse eficientemente.

## Crear Fibras con `lanzar`

La palabra clave `lanzar` crea una nueva fibras que comienza a ejecutarse de
forma concurrente. La fibras se ejecutan hasta que ceden el control
explícitamente o terminan.

```synapse
fn principal() {
    // Lanzar una fibras que imprime mensajes
    lanzar {
        proceso_a()
    }

    // Lanzar múltiples fibras
    para i en 0..4 {
        lanzar {
            trabajo_pesado(i)
        }
    }

    // Esperar a que todas terminen
    esperar_todas()
}

fn proceso_a() {
    log("Fibras A: iniciando")
    ceder() // Ceder control a otras fibras
    log("Fibras A: continuando después de ceder")
}

fn trabajo_pesado(id: entero) {
    log("Trabajo {id}: empezando")
    para i en 0..1000 {
        // Simular trabajo
    }
    log("Trabajo {id}: terminado")
}
```

## Esperar Fibras

Hay varias formas de esperar a que las fibras completen su ejecución:

```synapse
fn esperar_ejemplo() {
    // Esperar una fibras específica
    let resultado = esperar fibras_unica {
        calcular(42)
    }
    log("Resultado: {resultado}")

    // Esperar todas las fibras activas
    lanzar { tarea_1() }
    lanzar { tarea_2() }
    esperar_todas()

    // Esperar con tiempo límite
    con tiempo_limite(milisegundos: 5000) {
        esperar_todas()
    }
}
```

## Comunicación entre Fibras

Las fibras se comunican mediante canales, que son tuberías seguras para
el uso concurrente:

```synapse
fn comunicacion_fibras() {
    let canal = Canal::nuevo()

    // Productor
    lanzar {
        para i en 0..10 {
            canal <- enviar(i)
            log("Enviado: {i}")
        }
    }

    // Consumidor
    let suma = 0
    para _ en 0..10 {
        escuchar canal: recibir => valor {
            suma += valor
        }
    }
    log("Suma total: {suma}")
}
```

## Ejemplo: Procesador Paralelo de Imágenes

Este ejemplo divide una imagen en regiones y las procesa en paralelo:

```synapse
fn procesar_imagen(imagen: Imagen) {
    let ancho = imagen.ancho()
    let alto = imagen.alto()
    let num_workers = 4

    let canal_entrada = Canal::nuevo()
    let canal_salida = Canal::nuevo()

    // Lanzar workers
    para i in 0..num_workers {
        let inicio_y = (alto / num_workers) * i
        let fin_y = (alto / num_workers) * (i + 1)

        lanzar {
            procesar_region(
                imagen,
                0, inicio_y,
                ancho, fin_y,
                canal_entrada,
                canal_salida
            )
        }
    }

    // Enviar regiones a procesar
    para y in 0..alto {
        canal_entrada <- enviar(y)
    }

    // Recibir resultados
    let resultados = Lista::nueva()
    para _ in 0..alto {
        escuchar canal_salida: recibir => fila {
            resultados.agregar(fila)
        }
    }

    log("Imagen procesada: {resultados.longitud()} filas")
}

fn procesar_region(
    imagen: Imagen,
    x1: entero, y1: entero,
    x2: entero, y2: entero,
    entrada: Canal<entero>,
    salida: Canal<Lista<entero>>
) {
    para y in y1..y2 {
        escuchar entrada: recibir => fila {
            let procesada = Lista::nueva()
            para x in x1..x2 {
                let pixel = imagen.pixel(x, y)
                let nuevo = aplicar_filtro(pixel)
                procesada.agregar(nuevo)
            }
            salida <- enviar(procesada)
        }
    }
}
```

## Errores Comunes

1. **Olar sin ceder**: Si una fibras nunca llama a `ceder()`, bloquea
   todas las demás fibras del mismo núcleo.
2. **Acceso compartido sin canal**: Nunca comparta memoria entre fibras
   sin sincronización. Use canales o `Mutex`.
3. **Olvidar esperar**: Si lanza fibras y no espera, el programa puede
   terminar prematuramente.
