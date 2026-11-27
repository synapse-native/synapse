# Patrones Concurrentes en Syquex

Este capítulo cubre los patrones comunes de concurrencia en Syquex: productor-consumidor, fan-out/fan-in, y patrones de sincronización. Aprenderás a resolver problemas concurrentes de forma elegante.

Estos patrones son la base para construir sistemas concurrentes robustos.

<!-- cumple Manual 3 §8 -->

## 1. Patrón Productor-Consumidor

```syquex
importar lib.concurrente

funcion productor(canal: Canal<entero>, max: entero):
    para i en 1..max:
        await sleep(aleatorio(10, 100))  // Simular trabajo
        canal <- i
        io.escribir_linea("Producido: " + i.texto())
    canal.cerrar()

funcion consumidor(canal: Canal<entero>):
    escuchar canal:
        let item = canal ->
        io.escribir_linea("Consumido: " + item.texto())

funcion principal():
    let buffer = Canal<entero>(5)  // Buffer de tamaño 5
    
    lanzar productor(buffer, 20)
    lanzar consumidor(buffer)
```

## 2. Fan-Out / Fan-In

```syquex
async funcion procesar_elemento(x: entero) -> entero:
    await sleep(aleatorio(50, 200))
    retornar x * x

async funcion fan_out_fan_in(datos: Lista<entero>) -> Lista<entero>:
    // Fan-out: distribuir trabajo a múltiples tareas
    let tareas = datos.mapear(lambda x: Tarea.crear(async:
        retornar await procesar_elemento(x)
    ))
    
    // Fan-in: recoger resultados
    retornar await Promise.all(tareas)

funcion principal():
    let datos = [1, 2, 3, 4, 5, 6, 7, 8]
    let resultados = await fan_out_fan_in(datos)
    io.escribir_linea("Resultados: " + resultados.texto())
```

## 3. Worker Pool

```syquex
estructura WorkerPool<T, R>:
    entrada: Canal<T>
    salida: Canal<R>
    num_workers: entero

    crear(num_workers: entero):
        self.num_workers = num_workers
        self.entrada = Canal<T>(num_workers * 2)
        self.salida = Canal<R>(num_workers * 2)

    metodo enviar(tarea: T):
        self.entrada <- tarea

    metodo iniciar(worker_fn: funcion(T) -> R):
        para i en 1..self.num_workers:
            lanzar self.worker(worker_fn)

    metodo worker(fn: funcion(T) -> R):
        escuchar self.entrada:
            let item = self.entrada ->
            let resultado = fn(item)
            self.salida <- resultado

    metodo resultados() -> Canal<R>:
        retornar self.salida

// Uso
funcion principal():
    let pool = WorkerPool<entero, entero>(4)
    pool.iniciar(lambda x: x * x)
    
    para i en 1..20:
        pool.enviar(i)
    
    // Recoger resultados
    para i en 1..20:
        escuchar pool.resultados():
            let r = pool.resultados() ->
            io.escribir_linea("Resultado: " + r.texto())
```

## 4. Barreras y Puntos de Sincronización

```syquex
funcion trabajo_paralelo():
    io.escribir_linea("Trabajando...")

funcion principal():
    // Crear una barrera para N tareas
    let barrera = Barrera.crear(3)
    
    lanzar async:
        trabajo_paralelo()
        barrera.wait()
    
    lanzar async:
        trabajo_paralelo()
        barrera.wait()
    
    lanzar async:
        trabajo_paralelo()
        barrera.wait()
    
    // Todas las tareas deben llegar a la barrera antes de continuar
    barrera.wait()
    io.escribir_linea("Todas las tareas completadas")
```

## 5. Pub-Sub (Publicador-Suscriptor)

```syquex
importar lib.eventos

estructura EventoChat:
    mensaje: texto
    usuario: texto

estructura ChatRoom:
    suscriptores: Lista<Canal<EventoChat>>

    metodo suscribir() -> Canal<EventoChat>:
        let canal = Canal<EventoChat>(100)
        self.suscriptores.agregar(canal)
        retornar canal

    metodo publicar(evento: EventoChat):
        para canal en self.suscriptores:
            canal <- evento

funcion principal():
    let sala = ChatRoom()
    
    // Suscriptores
    let usuario1 = sala.suscribir()
    let usuario2 = sala.suscribir()
    
    // Publicar mensaje
    sala.publicar(EventoChat("Hola!", "Ana"))
    
    // Escuchar
    escuchar usuario1:
        let evento = usuario1 ->
        io.escribir_linea(usuario1.nombre + " dice: " + evento.mensaje)
```

## 6. Rate Limiting

```syquex
estructura RateLimiter:
    capacidad: entero
    tokens: entero
    ultima_recarga: tiempo
    intervalo_recarga: entero

    crear(capacidad: entero, intervalo_ms: entero):
        self.capacidad = capacidad
        self.tokens = capacidad
        self.ultima_recarga = ahora()
        self.intervalo_recarga = intervalo_ms

    metodo try_consume() -> booleano:
        // Recargar tokens
        let ahora = ahora()
        let elapsed = ahora - self.ultima_recarga
        let tokens_nuevos = (elapsed / self.intervalo_recarga) * self.capacidad
        self.tokens = min(self.capacidad, self.tokens + tokens_nuevos)
        self.ultima_recarga = ahora
        
        si self.tokens >= 1:
            self.tokens = self.tokens - 1
            retornar verdadero
        retornar falso

    metodo wait_consume():
        mientras !self.try_consume():
            await sleep(10)

funcion principal():
    let limiter = RateLimiter(10, 1000)  // 10 req/s
    
    para i en 1..20:
        if limiter.try_consume():
            lanzar procesar_request(i)
        sino:
            io.escribir_linea("Rate limit: " + i.texto())
```

## 7. Retry con Exponencial Backoff

```syquex
funcion retry<T>(operacion: funcion() -> Resultado<T, texto>, max_intentos: entero = 3) -> Resultado<T, texto>:
    intento = 1
    mientras intento <= max_intentos:
        let resultado = operacion()
        coincidir resultado:
            caso ok(valor):
                retornar ok(valor)
            caso err(e):
                io.escribir_linea(
                    "Intento " + intento.texto() + " falló: " + e
                )
                let delay = 100 * (2 ^ (intento - 1))  // 100ms, 200ms, 400ms...
                await sleep(delay)
                intento = intento + 1
    
    retornar err("Agotados " + max_intentos.texto() + " intentos")

// Uso
funcion principal():
    let resultado = await retry(lambda: api.call())
    coincidir resultado:
        caso ok(data): "Éxito: " + data
        caso err(e): "Falló después de reintentos: " + e
```

## 8. Dead Letter Queue

```syquex
estructura DLQueue<T>:
    principal: Canal<T>
    dead_letter: Canal<(T, texto)>
    procesador: funcion(T) -> Resultado<nulo, texto>

    crear(procesador: funcion(T) -> Resultado<nulo, texto>):
        self.principal = Canal<T>(100)
        self.dead_letter = Canal<(T, texto)>(100)
        self.procesador = procesador

    metodo enqueue(item: T):
        self.principal <- item

    metodo iniciar():
        lanzar self.worker()

    metodo worker():
        escuchar self.principal:
            let item = self.principal ->
            let resultado = self.procesador(item)
            coincidir resultado:
                caso err(e):
                    self.dead_letter <- (item, e)
                    io.escribir_linea("Enviado a DLQ: " + e)

// Uso
funcion principal():
    let dlq = DLQueue<entero>(lambda x:
        si x > 10: retornar err("Valor demasiado grande")
        retornar ok()
    )
    
    dlq.iniciar()
    dlq.enqueue(5)
    dlq.enqueue(20)  // Irá a la DLQ
```

## Referencias

- **Manual 3 §8**: Concurrencia y comunicación en Syquex (fibras + canales)
- **Manual 5 §6**: Patrones de concurrencia avanzados
- **Manual 2 §8**: Concurrencia en Synapse (canales, move semantics)

// cumple Manual 3 §8
