# Tareas (Tasks) en Syquex

Este capítulo explora las tareas (tasks) como unidad de trabajo concurrente en Syquex. Aprenderás a crear, programar y comunicar tareas para construir aplicaciones paralelas.

Las tareas permiten ejecutar múltiple operaciones de forma concurrente sin bloquear el hilo principal.

<!-- cumple Manual 3 §8 -->

## 1. Creación y ejecución de tareas

```syquex
importar lib.concurrente

// Crear una tarea
let tarea = Tarea.crear(funcion():
    io.escribir_linea("Tarea ejecutándose")
    retornar 42
)

// Ejecutar y esperar
let resultado = await tarea
io.escribir_linea("Resultado: " + resultado.texto())
```

## 2. Scheduling y prioridades

```syquex
// Tarea con prioridad
let tarea_alta = Tarea.crear_con_prioridad(
    lambda: proceso_intenso(),
    prioridad: Prioridad.ALTA
)

// Tarea con límite de tiempo
let tarea_timeout = Tarea.crear(
    lambda: operacion_lenta(),
    timeout: 5000  // 5 segundos
)
```

## 3. Task Groups

```syquex
async funcion procesar_en_paralelo(urls: Lista<texto>) -> Lista<texto>:
    let grupos = TaskGroup.crear()
    
    para url en urls:
        grupos.agregar(async:
            let resp = await http.get(url)
            retornar resp.cuerpo
        )
    
    retornar await grupos.esperar_todos()
```

## 4. Comunicación entre tareas

### Canales sin conexión (Unbounded)

```syquex
let canal = Canal<entero>()

tarea_productor = lanzar:
    para i en 1..100:
        canal <- i

tarea_consumidor = lanzar:
    escuchar canal:
        let item = canal ->
        io.escribir_linea("Recibido: " + item.texto())
```

### Canales con capacidad (Bounded)

```syquex
let canal = Canal<texto>(10)  // Buffer de 10 elementos

funcion worker(id: entero, canal: Canal<texto>):
    para i en 1..10:
        canal <- "Worker " + id.texto() + " mensaje " + i.texto()

lanzar worker(1, canal)
lanzar worker(2, canal)

escuchar canal:
    let msg = canal ->
    io.escribir_linea(msg)
```

## 5. Cancelación y abort

```syquex
let tarea = Tarea.crear(funcion_lenta)

// Cancelar después de 1 segundo
Cron.cada(1000):
    tarea.cancelar()

// Verificar cancelación
si tarea.esta_cancelada():
    io.escribir_linea("Tarea fue cancelada")
```

## 6. Pool de hilos

```syquex
let pool = ThreadPool.crear(4)  // 4 hilos

// Enviar trabajos al pool
pool.ejecutar(lambda:
    io.escribir_linea("Trabajo ejecutado en hilo")
)

pool.esperar_completados()
pool.cerrar()
```

## 7. Monitoreo y métricas

```syquex
let tarea = Tarea.crear(operacion_compleja)

// Monitorear estado
tarea.onEstadoCambio(lambda estado:
    io.escribir_linea("Estado: " + estado.texto())
)

// Obtener métricas
let metricas = tarea.metricas()
io.escribir_linea("CPU: " + metricas.cpu_porcentaje.texto() + "%")
io.escribir_linea("Memoria: " + metricas.memoria_bytes.texto() + " bytes")
```

## 8. Patrones avanzados

### Pipeline de procesamiento

```syquex
async funcion pipeline(datos: Stream<entero>) -> Stream<entero>:
    retornar datos
        .filtrar(lambda x: x > 0)
        .mapear(lambda x: x * 2)
        .limitar(100)
        .agregar_tarea(lambda x: procesar_elemento(x))
```

### Worker pool persistente

```syquex
estructura WorkerPool:
    tareas: Canal<Tarea>
    resultados: Canal<Resultado>

    crear(num_workers: entero):
        self.tareas = Canal<Tarea>()
        self.resultados = Canal<Resultado>()
        
        para i en 1..num_workers:
            lanzar self.worker_loop()

    metodo worker_loop():
        escuchar self.tareas:
            let tarea = self.tareas ->
            try:
                let resultado = tarea.ejecutar()
                self.resultados <- ok(resultado)
            atrapar e:
                self.resultados <- err(e)
```

## Referencias

- **Manual 3 §8.1**: Lanzar y escuchar fibras
- **Manual 2 §1**: Concurrencia con canales y move semantics
- **Manual 5 §6**: Patrones de concurrencia avanzados

// cumple Manual 3 §8
