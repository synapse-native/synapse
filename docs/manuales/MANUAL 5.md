MANUAL 5: CONCURRENCIA Y COMUNICACIÓN ENTRE HILOS
Archivo: 05_CONCURRENCIA_Y_CANALES.md
Versión: 5.1.1-industrial
Propósito: Especificar el modelo de concurrencia basado en canales, la instrucción lanzar, el manejo de errores, la concurrencia distribuida, aprendizaje federado y computación cuántica.

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
    // mensaje ya no es válido aquí
    esperar()
Semántica de move: Todos los argumentos pasados a lanzar son movidos al nuevo hilo. El hilo padre pierde el acceso.
Recuperación de errores (panics):

synapse
lanzar tarea_peligrosa() recuperar:
    escribir_linea("El hilo colapsó, pero recuperamos")
5.3 Canales Tipados (Canal<T>)
Creación:

synapse
canal_sync = canal<entero>(0)      // Síncrono (capacidad 0)
canal_async = canal<texto>(100)    // Asíncrono (buffer)
Operaciones:

Operación	Sintaxis	Comportamiento
Enviar	canal <- valor	Bloquea si canal lleno.
Recibir	valor = canal ->	Bloquea si canal vacío.
Cerrar	cerrar(canal)	Receptores reciben Resultado<T, Error>.
Estructura interna (C):

c
typedef struct {
    void** buffer;
    size_t capacidad;
    size_t head, tail, count;
    bool cerrado;
    pthread_mutex_t mutex;
    pthread_cond_t no_vacio;
    pthread_cond_t no_lleno;
} SynapseCanal;
5.4 Escuchar (Listener)
synapse
escuchar mi_canal:
    mensaje = mi_canal ->
    procesar(mensaje)   // Se ejecuta por cada mensaje hasta que se cierre el canal
5.5 Concurrencia Distribuida (std.cluster) — v5.0
synapse
importar std.cluster
let canal_remoto = cluster::conectar("tcp://192.168.1.100:8080", clave_publica_remota)
canal_remoto.enviar(datos)
let respuesta = canal_remoto.recibir()
Handshake Ed25519 (zero-trust): Cliente envía HELLO con clave pública y firma de un nonce. Servidor verifica y responde. Tráfico cifrado con clave de sesión derivada.

5.6 Aprendizaje Federado y Entrenamiento Distribuido (std::federated)
Synapse incorpora un runtime de aprendizaje federado para entrenar modelos de IA sin centralizar datos, utilizando el algoritmo FedAvg.

5.6.1 Arquitectura y Componentes:

Orquestador (runtime/federated/aggregator.c): Particiona datasets, asigna workers y coordina épocas.

Cliente Federado: Entrena localmente y envía actualizaciones firmadas con Ed25519.

Destilación: Compresión de modelos (Teacher → Student) usando divergencia KL.

Fine‑tuning: Ajuste de capas superiores con tasas de aprendizaje diferenciadas.

5.6.2 API en Synapse:

synapse
// std/federated.syn
tipo FederatedConfig = estructura:
    num_workers: Entero
    num_rounds: Entero
    learning_rate: Flotante
    min_clients: Entero

fn federated::entrenar(modelo: Modelo, dataset: Dataset, config: FederatedConfig) -> Resultado<Modelo, Error>
fn federated::agregar_actualizacion(update: FederatedUpdate) -> Resultado<(), Error>
5.6.3 Tests Obligatorios:

Test	Comando	Criterio
Federated Learning	gcc -o test_fed runtime/federated/aggregator.c -lm -lssl -lcrypto && ./test_fed --rounds 3 --clients 2	0 leaks, 0 crashes
Destilación (KL divergence)	./test_distillation --test kl_loss	Pérdida < 0.01
Fine‑tuning	./test_finetune --test layer_freeze	Capas congeladas no se actualizan
5.7 Computación Cuántica (std::quantum)
Synapse ofrece un simulador cuántico para probar algoritmos en hardware clásico, incluyendo decoherencia y corrección de errores.

5.7.1 Memoria Cuántica (runtime/quantum/matrix.c):

Representación: Matriz de densidad 2x2 para qubits.

Canales de ruido:

T1 (Amplitude Damping): Decaimiento de población.

T2 (Phase Damping): Pérdida de coherencia de fase.

5.7.2 Corrección de Errores Cuánticos (QEC):

Códigos de Superficie: Red 2D de qubits físicos.

Síndrome de Error: Medición de estabilizadores y corrección.

5.7.3 Runtime Cuántico:

Puertas soportadas: X, Y, Z, Hadamard, CNOT, SWAP.

Medición en base Z con colapso del estado.

5.7.4 API en Synapse:

synapse
// std/quantum.syn
tipo Qubit = estructura:
    rho: Matriz<Complejo, 2, 2>
    t1: Flotante
    t2: Flotante

fn quantum::crear_qubit(estado: Estado) -> Qubit
fn quantum::puerta_cnot(control: &mut Qubit, target: &mut Qubit) -> Resultado<(), Error>
fn quantum::medir(qubit: &mut Qubit) -> Resultado<Entero, Error>
5.7.5 Tests Obligatorios:

Test	Comando	Criterio
Ruido T1/T2	gcc -o test_qmem runtime/quantum/matrix.c -lm && ./test_qmem --test amplitude_damping	PASS
Surface Code	./test_surface --test error_correction	Error corregido
Puerta CNOT	./test_quantum_runtime --test cnot_gate	Estado entrelazado correcto