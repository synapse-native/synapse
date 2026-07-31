MANUAL 5: CONCURRENCIA Y COMUNICACIÓN ENTRE HILOS
Archivo: 05_CONCURRENCIA_Y_CANALES.md
Versión: 5.1.1-industrial
Propósito: Especificar el modelo de concurrencia basado en canales, la instrucción lanzar, el manejo de errores y la concurrencia distribuida.

5.1 Filosofía: "Share Memory by Communicating"
Prohibido: Estado mutable compartido entre hilos.

Permitido: Transferencia de ownership mediante canales.

Garantía: Zero data races (verificado en tiempo de compilación para ownership; en tiempo de ejecución para canales).

5.2 La Instrucción lanzar (Spawning)
synapse
funcion trabajador(id: entero, datos: &texto) -> nulo:
    escribir_linea("Hilo " + entero_a_texto(id) + " procesa: " + datos)

funcion principal() -> nulo:
    mensaje = "Hola desde el hilo principal"
    lanzar trabajador(1, mensaje)   // mensaje se mueve al hilo
    // mensaje ya no es válido aquí (ERR_MEM_USE_AFTER_MOVE)
    esperar()   // Bloquea hasta que todos los hilos terminen
Semántica de move: Todos los argumentos pasados a lanzar son movidos al nuevo hilo. El hilo padre pierde el acceso.

Recuperación de errores (panics):

synapse
lanzar tarea_peligrosa() recuperar:
    escribir_linea("El hilo colapsó, pero recuperamos")
5.3 Canales Tipados (Canal<T>)
Creación:

synapse
// Síncrono (capacidad 0): emisor bloquea hasta que receptor lea.
canal_sync = canal<entero>(0)

// Asíncrono (capacidad N): emisor bloquea solo si el buffer está lleno.
canal_async = canal<texto>(100)
Operaciones:

Operación	Sintaxis	Comportamiento
Enviar	canal <- valor	Bloquea si canal lleno (sync) o buffer lleno (async).
Recibir	valor = canal ->	Bloquea si canal vacío.
Cerrar	cerrar(canal)	Marca el canal como cerrado. Los receptores reciben Resultado<T, Error>.
Estructura interna (C):

c
typedef struct {
    void** buffer;              // Ring buffer
    size_t capacidad;
    size_t head;
    size_t tail;
    size_t count;
    bool cerrado;
    pthread_mutex_t mutex;
    pthread_cond_t no_vacio;
    pthread_cond_t no_lleno;
} SynapseCanal;
Implementación de enviar/recibir (pseudocódigo C):

c
void canal_enviar(SynapseCanal* c, void* item) {
    pthread_mutex_lock(&c->mutex);
    while (c->count == c->capacidad && !c->cerrado) {
        pthread_cond_wait(&c->no_lleno, &c->mutex);
    }
    if (c->cerrado) { pthread_mutex_unlock(&c->mutex); return; }
    c->buffer[c->tail] = item;
    c->tail = (c->tail + 1) % c->capacidad;
    c->count++;
    pthread_cond_signal(&c->no_vacio);
    pthread_mutex_unlock(&c->mutex);
}

void* canal_recibir(SynapseCanal* c) {
    pthread_mutex_lock(&c->mutex);
    while (c->count == 0 && !c->cerrado) {
        pthread_cond_wait(&c->no_vacio, &c->mutex);
    }
    if (c->count == 0 && c->cerrado) {
        pthread_mutex_unlock(&c->mutex);
        return NULL; // Canal cerrado y vacío
    }
    void* item = c->buffer[c->head];
    c->head = (c->head + 1) % c->capacidad;
    c->count--;
    pthread_cond_signal(&c->no_lleno);
    pthread_mutex_unlock(&c->mutex);
    return item;
}
5.4 Escuchar (Listener)
synapse
escuchar mi_canal:
    // Este bloque se ejecuta una vez por cada mensaje recibido.
    // Se ejecuta en el hilo actual, bloqueando hasta que el canal se cierre.
    mensaje = mi_canal ->   // Recibir explícito dentro del listener
    procesar(mensaje)
5.5 Concurrencia Distribuida (std.cluster) — v5.0
Canal Remoto:

synapse
importar std.cluster

let canal_remoto = cluster::conectar("tcp://192.168.1.100:8080", clave_publica_remota)
canal_remoto.enviar(datos)
let respuesta = canal_remoto.recibir()
Handshake Ed25519 (zero-trust):

Cliente envía HELLO con su clave pública y firma de un nonce.

Servidor verifica la firma.

Servidor responde con su propio HELLO.

Ambos canales se autentican mutuamente. El tráfico se cifra con una clave de sesión derivada.

Protección: El compilador y el runtime previenen deadlocks mediante timeouts configurables (recibir_con_timeout(ms)).

