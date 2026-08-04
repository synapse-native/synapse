# MANUAL 5: CONCURRENCIA Y COMUNICACIÓN

**Archivo:** `05_CONCURRENCIA_Y_COMUNICACION.md`  
**Versión:** 8.0.0-industrial  
**Propósito:** Especificar el modelo de concurrencia del ecosistema Synapse/Syquex, basado en fibras ligeras y canales tipados. Este manual cubre la creación de fibras (`lanzar`), la comunicación mediante canales (`Canal<T>`), la escucha de eventos (`escuchar`), las primitivas de sincronización (mutex, semáforos, barreras), la concurrencia distribuida con `std.cluster` (handshake Ed25519, Raft, work-stealing), y la integración con OpenSyn para asistencia en programación concurrente. Todo el modelo está diseñado para eliminar condiciones de carrera y bloqueos por diseño, siguiendo la filosofía «Share Memory by Communicating».

---

## 1. FILOSOFÍA: «SHARE MEMORY BY COMMUNICATING»

El ecosistema Synapse/Syquex adopta la filosofía de **compartir memoria mediante comunicación**, popularizada por lenguajes como Go y Erlang. Esto significa:

- **El estado mutable compartido entre hilos está prohibido** a nivel de compilación.
- La comunicación entre fibras se realiza exclusivamente a través de **canales tipados** (`Canal<T>`), que transfieren la propiedad de los datos.
- El modelo de ownership (Synapse) o el análisis de alcance (Syquex) garantiza que no haya condiciones de carrera (*data races*) ni bloqueos mutuos (*deadlocks*) por diseño.

**Garantía fundamental:** Un programa concurrente en Synapse/Syquex nunca tiene condiciones de carrera (verificado en tiempo de compilación para ownership; en tiempo de ejecución para canales).

---

## 2. FIBRAS LIGERAS (`lanzar`)

### 2.1. Concepto

Una **fibra** es un hilo de usuario ultraligero que se ejecuta sobre un pool de hilos del sistema operativo (M:N scheduling). Cada fibra tiene:
- Pila propia (tamaño configurable, por defecto 64 KB).
- Contexto de ejecución (registros, program counter).
- Identificador único.

Las fibras son **mucho más ligeras que los hilos del sistema operativo** (pesan kilobytes vs megabytes). Se pueden crear miles de fibras sin degradar el rendimiento.

### 2.2. Sintaxis en Synapse

```synapse
funcion trabajador(id: entero, mensaje: texto) -> nulo:
    log("Hilo ", id, " dice: ", mensaje)

funcion principal() -> nulo:
    mensaje = "Hola desde el hilo principal"
    lanzar trabajador(1, mensaje)   // mensaje se mueve
    // mensaje ya no es válido aquí (use-after-move)
```

### 2.3. Sintaxis en Syquex

```syquex
funcion trabajador(id: entero):
    log("Fibra ", id, " ejecutándose")

funcion principal():
    lanzar trabajador(1)
    lanzar trabajador(2)
    lanzar trabajador(3)
    esperar()   // Espera a que todas las fibras terminen
```

### 2.4. Semántica de Movimiento (Ownership)

Todos los argumentos pasados a `lanzar` se **mueven** al nuevo hilo. El compilador verifica que no se usen después de la llamada (Synapse: `ERR_MEM_USE_AFTER_MOVE`; Syquex: análisis de alcance).

**Ejemplo inválido (Synapse):**

```synapse
funcion principal() -> nulo:
    msg = "Hola"
    lanzar trabajador(1, msg)
    log(msg)   // ERROR: ERR_MEM_USE_AFTER_MOVE (msg fue movido)
```

**Ejemplo inválido (Syquex):**

```syquex
funcion principal():
    msg = "Hola"
    lanzar trabajador(1, msg)
    log(msg)   // ERROR: uso después de movimiento (detectado por análisis de alcance)
```

### 2.5. Recuperación de Errores (Panics)

Si una fibra entra en pánico (error no recuperable), se puede ejecutar una expresión de recuperación con `recuperar`.

**Synapse:**
```synapse
lanzar tarea_peligrosa() recuperar:
    log("El hilo colapsó, pero recuperamos")
```

**Syquex:**
```syquex
lanzar tarea_peligrosa() recuperar:
    log("La fibra colapsó, pero recuperamos")
```

### 2.6. Implementación en el Runtime (C)

```c
// runtime/core/concurrency.c

typedef struct Fibra {
    void* stack;                // Pila de la fibra
    size_t stack_size;          // Tamaño de la pila
    void* context;              // ucontext_t (POSIX) o estructura personalizada
    struct Fibra* next;         // Siguiente fibra en la cola de scheduling
    int id;                     // Identificador único
    bool terminada;             // Flag de finalización
    void* resultado;            // Resultado de la fibra (si retorna)
} Fibra;

typedef struct Scheduler {
    Fibra* cola_activa;         // Cola de fibras listas para ejecutar
    Fibra* cola_espera;         // Cola de fibras bloqueadas
    int num_fibras;             // Número total de fibras
    pthread_t* hilos_os;        // Hilos del sistema operativo (pool)
    int num_hilos_os;           // Número de hilos OS (por defecto = núcleos)
    bool ejecutando;            // Flag de ejecución
    pthread_mutex_t mutex;      // Mutex para operaciones en colas
} Scheduler;

void fibra_crear(void (*func)(void*), void* arg, size_t stack_size);
void fibra_esperar(int fibra_id);
void fibra_terminar(void* resultado);
void scheduler_iniciar(int num_hilos_os);
void scheduler_detener();
```

**Flujo de creación de una fibra:**
1. Se asigna una pila (por defecto 64 KB).
2. Se inicializa el contexto (ucontext_t o similar).
3. Se añade la fibra a la cola activa del scheduler.
4. Un hilo del sistema operativo toma la fibra y la ejecuta.
5. Al terminar, la fibra se elimina y su pila se libera.

---

## 3. CANALES TIPADOS (`Canal<T>`)

### 3.1. Concepto

Un canal es una cola FIFO thread-safe que permite la comunicación entre fibras. Es **tipado**: solo transporta datos de un tipo específico (`T`). Puede ser **síncrono** (capacidad 0) o **asíncrono** (buffer de tamaño N).

### 3.2. Sintaxis

**Creación:**
```synapse
canal_sync = canal<entero>(0)      // Síncrono (capacidad 0)
canal_async = canal<texto>(100)    // Asíncrono (buffer de 100)
```

**Operaciones:**

| Operación | Sintaxis (Synapse) | Sintaxis (Syquex) | Comportamiento |
|-----------|-------------------|-------------------|----------------|
| Envío | `canal <- valor` | `canal <- valor` | Bloquea si canal lleno (asíncrono) o si no hay receptor (síncrono). |
| Recepción | `valor = canal ->` | `valor = canal ->` | Bloquea si canal vacío. |
| Cierre | `cerrar(canal)` | `cerrar(canal)` | Cierra el canal; los receptores reciben `Resultado<T, Error>` indicando cierre. |

### 3.3. Ejemplo Completo (Syquex)

```syquex
funcion productor(c: Canal<int>):
    para i = 0 mientras i < 10:
        c <- i
        log("Enviado: ", i)
    cerrar(c)

funcion consumidor(c: Canal<int>):
    escuchar c:
        let valor = c ->
        log("Recibido: ", valor)

funcion principal():
    let c = Canal<int>(10)   // Buffer de 10
    lanzar productor(c)
    lanzar consumidor(c)
```

### 3.4. Estructura Interna en C

```c
// runtime/core/concurrency.c

typedef struct Canal {
    void** buffer;              // Buffer circular de punteros a datos
    size_t capacidad;           // Tamaño del buffer (0 para síncrono)
    size_t head;                // Índice de lectura (cabeza)
    size_t tail;                // Índice de escritura (cola)
    size_t count;               // Número de elementos en el buffer
    bool cerrado;               // Flag de cierre
    pthread_mutex_t mutex;      // Mutex para proteger el acceso
    pthread_cond_t no_vacio;    // Condición: buffer no vacío (para receptores)
    pthread_cond_t no_lleno;    // Condición: buffer no lleno (para emisores)
    size_t tipo_tamano;         // Tamaño del tipo T (para memoria)
    void (*destructor)(void*);  // Destructor para los datos (opcional)
} Canal;

Canal* canal_crear(size_t capacidad, size_t tipo_tamano, void (*destructor)(void*));
void canal_enviar(Canal* canal, void* dato);
void* canal_recibir(Canal* canal, bool* cerrado);
void canal_cerrar(Canal* canal);
void canal_destruir(Canal* canal);
```

### 3.5. Semántica de Movimiento en Canales

Cuando un dato se envía a través de un canal, el emisor **mueve** la propiedad al canal. El receptor **toma** la propiedad al recibirlo.

- **Synapse:** El compilador verifica que el dato no se use después del envío (use-after-move).
- **Syquex:** El análisis de alcance detecta el movimiento y marca la variable como inválida.

**Esto garantiza que un dato solo sea accedido por una fibra a la vez.**

### 3.6. Cierre de Canales

Cuando se cierra un canal (`cerrar()`), los receptores que intenten recibir obtienen un `Resultado<T, Error>` que indica cierre. Esto permite manejar la finalización de manera ordenada.

**Synapse:**
```synapse
funcion consumidor(c: Canal<int>) -> nulo:
    coincidir c ->:
        ok(valor) => log("Recibido: ", valor)
        err(error) => log("Canal cerrado")
```

**Syquex:**
```syquex
funcion consumidor(c: Canal<int>):
    escuchar c:
        let resultado = c ->  // Resultado<int, Error>
        coincidir resultado:
            ok(valor) => log("Recibido: ", valor)
            err(error) => log("Canal cerrado")
```

---

## 4. ESCUCHA (`escuchar`)

### 4.1. Concepto

La instrucción `escuchar` procesa mensajes de un canal de forma continua, ejecutando un bloque por cada mensaje recibido hasta que el canal se cierra.

### 4.2. Sintaxis

**Synapse:**
```synapse
escuchar mi_canal:
    mensaje = mi_canal ->
    procesar(mensaje)
```

**Syquex:**
```syquex
escuchar mi_canal:
    let mensaje = mi_canal ->
    procesar(mensaje)
```

### 4.3. Implementación

`escuchar` se traduce a un bucle infinito que:
1. Recibe del canal (`canal_recibir()`).
2. Si el canal está cerrado, sale del bucle.
3. Ejecuta el bloque de código con el mensaje.

**C generado (simplificado):**
```c
void _listener_mi_canal() {
    while (1) {
        bool cerrado;
        void* msg = canal_recibir(canal, &cerrado);
        if (cerrado) break;
        // Ejecutar bloque con msg
    }
}
```

---

## 5. SINCRONIZACIÓN ADICIONAL

Aunque el uso de canales es la forma recomendada de comunicación, Syquex y Synapse proporcionan primitivas de sincronización de bajo nivel para casos específicos (siempre que se usen dentro de bloques `inseguro` en Synapse).

### 5.1. Mutex

**Synapse:**
```synapse
inseguro:
    let mutex = mutex_crear()
    mutex_bloquear(mutex)
    // Sección crítica
    mutex_desbloquear(mutex)
    mutex_destruir(mutex)
```

**Syquex:**
```syquex
importar std.sync

funcion principal():
    let m = sync.mutex()
    m.bloquear()
    // Sección crítica
    m.desbloquear()
```

### 5.2. Semáforos

```syquex
importar std.sync

funcion principal():
    let s = sync.semaforo(3)  // Capacidad 3
    s.esperar()
    // ...
    s.señalar()
```

### 5.3. Barreras

```syquex
importar std.sync

funcion trabajador(b: sync.Barrera):
    // Hacer trabajo
    b.esperar()   // Espera a que todos los hilos lleguen

funcion principal():
    let b = sync.barrera(5)  // 5 hilos
    lanzar trabajador(b)
    // ...
```

### 5.4. Implementación (C)

```c
// runtime/core/concurrency.c

typedef struct Mutex {
    pthread_mutex_t mutex;
} Mutex;

typedef struct Semaforo {
    int valor;
    pthread_mutex_t mutex;
    pthread_cond_t cond;
} Semaforo;

typedef struct Barrera {
    int total;
    int esperando;
    pthread_mutex_t mutex;
    pthread_cond_t cond;
} Barrera;

void mutex_bloquear(Mutex* m);
void mutex_desbloquear(Mutex* m);
void semaforo_esperar(Semaforo* s);
void semaforo_señalar(Semaforo* s);
void barrera_esperar(Barrera* b);
```

---

## 6. CONCURRENCIA DISTRIBUIDA (`std.cluster`)

### 6.1. Introducción

El módulo `std.cluster` extiende la concurrencia a través de la red. Permite que fibras en diferentes máquinas se comuniquen como si estuvieran en el mismo proceso, utilizando canales remotos con cifrado y autenticación Ed25519.

### 6.2. Canal Remoto (`CanalRemoto<T>`)

Un canal remoto se comporta como un canal local, pero los mensajes se transmiten a través de TCP/IP con un handshake Ed25519 y cifrado de sesión.

**Synapse:**
```synapse
importar std.cluster

canal_remoto = cluster::conectar("tcp://192.168.1.100:8080", clave_publica_remota)
```

**Syquex:**
```syquex
importar std.cluster

let canal_remoto = cluster.conectar("tcp://192.168.1.100:8080", clave_publica_remota)
```

**Handshake (zero-trust):**
1. El cliente envía un mensaje `HELLO` con su clave pública y una firma de un nonce.
2. El servidor verifica la firma y responde con su propio `HELLO`.
3. Se deriva una clave de sesión (usando `crypto_kx` de libsodium o similar) para cifrar el tráfico.

**Operaciones:**
- `canal_remoto.enviar(datos)`: serializa y envía datos al nodo remoto.
- `let respuesta = canal_remoto.recibir()`: recibe datos del nodo remoto.
- `cerrar(canal_remoto)`: cierra la conexión.

### 6.3. Serialización de Datos

Para transmitir datos a través de la red, los canales remotos serializan los valores a un formato binario.

**Formato (similar a MessagePack):**

| Tipo | Identificador (1 byte) | Datos |
|------|------------------------|-------|
| `nulo` | `0xC0` | (ninguno) |
| `booleano` (falso) | `0xC2` | (ninguno) |
| `booleano` (verdadero) | `0xC3` | (ninguno) |
| `entero` (8 bits) | `0x00` | 1 byte |
| `entero` (16 bits) | `0x01` | 2 bytes (big‑endian) |
| `entero` (32 bits) | `0x02` | 4 bytes |
| `entero` (64 bits) | `0x03` | 8 bytes |
| `decimal` (32 bits) | `0x04` | 4 bytes (IEEE 754) |
| `decimal` (64 bits) | `0x05` | 8 bytes (IEEE 754) |
| `texto` | `0x06` | longitud (32 bits) + bytes UTF‑8 |
| `tensor` | `0x07` | filas (32 bits) + columnas (32 bits) + datos (float* en binario) |
| `estructura` | `0x08` | (serialización secuencial de campos) |

**Ejemplo: serialización de un entero 42**
```
[0x02][0x00][0x00][0x00][0x2A]
```

### 6.4. Descubrimiento y Multicast

- **Auto‑Discovery:** Los nodos pueden anunciarse en la red mediante multicast UDP o mediante un servicio de descubrimiento (ej. mDNS).
- **Multicast:** Permite enviar mensajes a múltiples nodos simultáneamente.

**Syquex:**
```syquex
importar std.cluster

funcion principal():
    let canal = cluster.multicast("239.0.0.1:8080")
    canal.enviar("Hola a todos")
```

### 6.5. Work‑Stealing y Raft (Para Sistemas Distribuidos)

El módulo `std.cluster` incluye implementaciones de:
- **Work‑Stealing:** Balanceo de carga entre nodos para tareas paralelas.
- **Raft:** Consenso distribuido para sistemas de alta disponibilidad.

Estos subsistemas se integran con el runtime de fibras y permiten construir sistemas distribuidos tolerantes a fallos.

---

## 7. INTEGRACIÓN CON OPENSYN

### 7.1. Asistencia en Concurrencia

OpenSyn puede ayudar a los desarrolladores a escribir código concurrente correcto:
- Explica el modelo de concurrencia (fibras, canales).
- Sugiere el uso de canales en lugar de mutexes.
- Detecta patrones de bloqueo potenciales en el código.
- Genera código concurrente a partir de descripciones en lenguaje natural.

**Ejemplo de consulta a OpenSyn:**
```
Usuario: "Quiero procesar 1000 archivos en paralelo, cada archivo en una fibra, y recolectar los resultados en una lista."
OpenSyn: "Puedes usar lanzar para cada archivo y enviar los resultados a un canal. Luego, escuchar el canal para recolectar los resultados."
```

### 7.2. Transpilación de Python Asyncio a Syquex

OpenSyn puede transpilar código Python con `asyncio` a código Syquex con fibras y canales.

**Python:**
```python
import asyncio

async def procesar(dato):
    await asyncio.sleep(1)
    return dato * 2

async def principal():
    tareas = [procesar(i) for i in range(10)]
    resultados = await asyncio.gather(*tareas)
    print(resultados)
```

**Syquex generado:**
```syquex
funcion procesar(dato: entero) -> entero:
    dormir(1000)  // ms
    retornar dato * 2

funcion principal():
    let resultados = lista<entero>()
    let c = Canal<Resultado<entero, Error>>(10)
    para i = 0 mientras i < 10:
        lanzar procesar_en_fibra(i, c)
    escuchar c:
        let r = c ->
        coincidir r:
            ok(valor) => resultados.agregar(valor)
            err(e) => log("Error: ", e)
    log(resultados)
```

---

## 8. IMPLEMENTACIÓN EN EL RUNTIME (DETALLES)

### 8.1. Scheduler Work‑Stealing

El scheduler de fibras utiliza un algoritmo de **work‑stealing** para balancear la carga entre hilos del sistema operativo.

**Estructura:**
```c
typedef struct Worker {
    pthread_t hilo_os;
    Fibra** cola_local;        // Cola de fibras por hilo (deque)
    int cola_primero;
    int cola_ultimo;
    struct Worker** otros;     // Punteros a otros workers (para robo)
    int num_workers;
} Worker;

void worker_ejecutar(Worker* w);
Fibra* worker_robar(Worker* w);  // Roba una fibra de otro worker
```

### 8.2. Canal de Eventos (Interrupción)

Para implementar `escuchar` sin polling, el runtime utiliza un **canal de eventos** (basado en `epoll`/`kqueue`/IOCP). Cuando un canal tiene datos, se notifica al scheduler para despertar la fibra bloqueada.

### 8.3. Gestión de Fibras Bloqueadas

Las fibras bloqueadas (esperando en un canal o en una sincronización) se mueven a una cola de espera. Cuando el evento ocurre (datos disponibles, mutex liberado, temporizador), la fibra se despierta y se reinserta en la cola activa.

---

## 9. PRUEBAS OBLIGATORIAS PARA ESTA ETAPA

| Test | Comando | Criterio |
|------|---------|----------|
| `lanzar` básico | `pytest tests/integration/test_spawn.py -v` | 100% pass |
| Canales síncronos/asíncronos | `pytest tests/integration/test_channels.py -v` | 0 deadlocks, 0 data races |
| `escuchar` | `pytest tests/integration/test_listen.py -v` | 100% pass |
| Canal remoto (cluster) | `pytest tests/integration/test_cluster_remote.py -v` | Handshake exitoso, envío/recepción |
| Work‑stealing | `pytest tests/integration/test_work_stealing.py -v` | Balanceo correcto entre hilos |
| Raft (consenso) | `pytest tests/integration/test_raft.py -v` | 100% pass en casos de fallo |
| Auto‑Discovery | `pytest tests/integration/test_discovery.py -v` | Nodos se encuentran automáticamente |
| Multicast | `pytest tests/integration/test_multicast.py -v` | Mensajes llegan a todos los nodos |
| Concurrencia distribuida (carga) | `pytest tests/stress/test_cluster_stress.py -v` | 10,000 mensajes/s sin pérdidas |

---

## 10. EJEMPLO COMPLETO: SISTEMA DE PROCESAMIENTO DE DATOS

**Código Syquex (`procesador_distribuido.syq`):**

```syquex
#lang: es

importar std.io
importar std.cluster
importar std.tiempo

estructura Tarea:
    id: entero
    datos: texto

funcion trabajador_local(tareas: Canal<Tarea>, resultados: Canal<Resultado<texto, texto>>):
    escuchar tareas:
        let tarea = tareas ->
        io.escribir_linea("Procesando tarea ", tarea.id)
        // Simular procesamiento
        tiempo.dormir(100)  // 100 ms
        resultados <- ok("Resultado de tarea " + tarea.id.texto())

funcion trabajador_remoto(clave_servidor: texto):
    let canal_remoto = cluster.conectar("tcp://192.168.1.100:8080", clave_servidor)
    // Enviar datos al servidor
    canal_remoto.enviar("Solicitud de tareas")
    escuchar canal_remoto:
        let tarea = canal_remoto ->
        io.escribir_linea("Procesando tarea remota: ", tarea)
        canal_remoto.enviar("Tarea completada: " + tarea)

funcion principal() -> Resultado<nulo, texto>:
    let tareas = Canal<Tarea>(100)
    let resultados = Canal<Resultado<texto, texto>>(100)

    // Lanzar 10 trabajadores locales
    para i = 0 mientras i < 10:
        lanzar trabajador_local(tareas, resultados)

    // Lanzar trabajador remoto
    let clave_servidor = io.leer_linea("Clave pública del servidor: ")
    lanzar trabajador_remoto(clave_servidor)

    // Enviar 1000 tareas
    para i = 0 mientras i < 1000:
        tareas <- Tarea(i, "Datos de tarea " + i.texto())

    // Recolectar resultados
    let contador = 0
    escuchar resultados:
        let r = resultados ->
        coincidir r:
            ok(valor) => 
                contador = contador + 1
                io.escribir_linea("Resultado ", contador, ": ", valor)
            err(error) => io.escribir_linea("Error: ", error)

    retornar ok()
```

---

## 11. SIGUIENTES PASOS

Con la concurrencia y comunicación cubiertas, el siguiente manual (Manual 6) se centrará en la **Integración del Ecosistema**: cómo Synapse, Syquex y OpenSyn se interconectan, la FFI, la serialización, la generación de bindings y la interoperabilidad.

---

*Este manual proporciona la especificación completa de la concurrencia y comunicación en el ecosistema Synapse/Syquex. La implementación debe seguir estos lineamientos para garantizar programas concurrentes seguros, eficientes y escalables.*

**Fin del Manual 5**