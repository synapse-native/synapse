# DOCUMENTO MAESTRO DE INGENIERÍA INDUSTRIAL: SYNAPSE Y OPENSYN

**Clasificación:** Confidencial / Core Architecture
**Rol del Documento:** Especificación Técnica Definitiva (TQC Nivel Máximo)

---

## PREÁMBULO DEL INGENIERO DE PROYECTO

Este documento constituye la especificación arquitectónica y operativa inmutable para la finalización del lenguaje de sistemas **Synapse** y la consolidación del ecosistema **OpenSyn**.

Como Ingeniero de Proyecto, establezco que cualquier desviación de las directivas aquí detalladas resultará en deuda técnica crítica. Si un ingeniero, sistema automatizado o agente de IA no logra compilar, ejecutar y escalar el lenguaje utilizando este documento, el fallo reside en la violación de estos protocolos. **Está estrictamente prohibido resumir o inferir comportamientos que no estén matemáticamente probados en el código.** El desarrollo debe ser hermético, resiliente y guiado por el Control de Calidad Total (TQC).

---

## PARTE I: OPENSYN (EL MOTOR DE EJECUCIÓN)

### 1.1 Definición y Propósito

**OpenSyn** (operativamente referido como Opencode) no es un simple repositorio o un conjunto de scripts. Es el **Marco de Ejecución Técnica** y el "Arquitecto Técnico" del proyecto. Es el sistema, los protocolos y (cuando aplica) el agente de inteligencia artificial encargado de traducir las directivas arquitectónicas a código C y Synapse impecable.

### 1.2 Reglas de Ejecución para OpenSyn

Cualquier ingeniero humano o agente de IA que asuma el rol de OpenSyn debe operar bajo las siguientes leyes inquebrantables (Leyes de Dirección General):

1. **Cero Condescendencia:** Está prohibido el uso de lenguaje complaciente. Las evaluaciones de código deben basarse exclusivamente en métricas de rendimiento, seguridad de memoria y complejidad ciclomática.
2. **Corrección Frontal:** Si una directiva de la Dirección de Ingeniería viola el modelo de Ownership, genera data races o introduce leaks, OpenSyn DEBE abortar la compilación y reportar el fallo estructural con evidencia en los logs.
3. **Honestidad Técnica:** No se asumen librerías de terceros. Si una macro en C o una llamada al sistema (`syscall`) no es estándar en POSIX o Windows de 64 bits, debe ser reportada antes de su inyección.
4. **Prohibición de Dependencias Opacas:** Synapse se construye sobre sí mismo. Está prohibido el uso de binarios precompilados externos (`.dll`, `.so`, `.a` que no provengan del propio toolchain validado de GCC/Clang) para evitar vectores de ataque (Supply Chain Attacks).

---

## PARTE II: ARQUITECTURA DEL NÚCLEO (SYNAPSE CORE)

Synapse es un lenguaje auto-alojado (Bootstrapped). El compilador está escrito en Synapse (`main.syn`), genera código C intermedio (`salida_metal.c`), y este es compilado por GCC/Clang junto con un entorno de ejecución estricto (`synapse_rt.c`).

### 2.1 El Ecosistema de Archivos Core

Para que un ingeniero retome el proyecto, debe garantizar la integridad de la siguiente estructura:

* `main.syn`: El punto de entrada del compilador. Orquesta el lexer, parser y generador.
* `parser.syn`: Analizador sintáctico. Convierte tokens en el Árbol Sintáctico Abstracto (AST).
* `generator.syn`: El transpilador. Recorre el AST y emite código C ANSI seguro.
* `synapse_rt.c`: El Runtime nativo. Contiene el gestor de memoria cruda, el Monitor de Integridad (MIM) y las primitivas del sistema operativo.
* `synapse2.exe`: El binario resultante del Bootstrap Definitivo. Es la herramienta de compilación actual.

### 2.2 Gestión de Memoria y TQC Nivel 2 (Estado Actual: Validado)

Synapse **no tiene Garbage Collector (Recolector de Basura)**. Utiliza un modelo de *Ownership* (Pertenencia) resuelto en tiempo de compilación.

**El Monitor de Integridad de Memoria (MIM):**
Debido a bloqueos ambientales para usar `-lasan` en ciertos entornos Windows nativos, el control de fugas de memoria está incrustado en el runtime mediante el módulo `MemoryWatchdog`.

Cualquier ingeniero que modifique la asignación dinámica debe respetar la siguiente estructura C en `synapse_rt.c`:

```c
#ifdef SYNAPSE_DEBUG_MEM
// Estructura obligatoria para el rastreo de fugas
typedef struct {
    void* ptr;
    size_t size;
    const char* file;
    int line;
    bool active;
} RegistroMemoria;

// El pool global debe estar protegido por un Mutex en entornos multihilo
extern RegistroMemoria _watchdog_tabla[100000];
extern pthread_mutex_t _watchdog_mutex;

void* watchdog_malloc(size_t size, const char* file, int line);
void watchdog_free(void* ptr);
void watchdog_report(void); // Ejecutado vía atexit()
#endif

```

**Regla de Validación:** La salida de `watchdog_report()` al finalizar cualquier binario generado por Synapse debe ser indefectiblemente: `0 bytes perdidos`. Un solo byte huérfano es motivo de congelamiento inmediato del desarrollo (Abortar Fases Posteriores).

---

## PARTE III: FASE DE CONCURRENCIA Y EL PACTO (HOJA DE RUTA ACTUAL)

Esta es la fase crítica donde la mayoría de lenguajes colapsan. Synapse implementará concurrencia bajo el principio de **Cero Estado Compartido**.

### 3.1 Arquitectura de Canales (Micro-entregable 2.1)

Está prohibido que dos hilos compartan acceso de escritura/lectura al mismo puntero de memoria simultáneamente (Data Races). Toda comunicación inter-hilo se hará por paso de mensajes a través de Canales Tipados (`Canal<T>`).

**Especificación de Implementación para OpenSyn:**

1. **Estructura Interna (`synapse_rt.c`):**
El canal debe ser un Ring Buffer (búfer circular) de tamaño fijo en el heap, protegido por Mutex y Variables de Condición.
```c
typedef struct {
    void** buffer;
    size_t capacidad;
    size_t head;
    size_t tail;
    size_t count;
    pthread_mutex_t mutex;
    pthread_cond_t no_vacio;
    pthread_cond_t no_lleno;
} SynapseCanal;

```


2. **Transferencia de Propiedad (Ownership Transfer):**
Cuando el hilo A ejecuta `mi_canal.enviar(objeto)`, el AST en `generator.syn` debe hacer que la variable `objeto` quede **invalidada** en el ámbito local de A.
* Si el hilo A intenta usar `objeto` en la línea siguiente, el compilador (`parser.syn` o la etapa de análisis semántico) debe lanzar un FATAL ERROR antes de generar el código C.
* El hilo B, al ejecutar `objeto_recibido = mi_canal.recibir()`, se convierte en el dueño absoluto del puntero y es el único responsable de su liberación (la cual el generador insertará al final del *scope* de B).



### 3.2 El Pacto: Contratos Lógicos (`requiere` / `garantiza`)

Para garantizar la inmunidad a errores lógicos en tiempo de ejecución, Synapse implementa validación de precondiciones y postcondiciones.

**Instrucción de Inyección para el Generador:**
El analizador sintáctico debe identificar los bloques de contrato y traducirlos a aserciones crudas en C (`#include <assert.h>`).

*Sintaxis en Synapse (`main.syn`):*

```synapse
funcion dividir(a: Entero, b: Entero) -> Entero {
    requiere:
        b != 0;
    garantiza:
        _resultado_ * b == a;
    
    retornar a / b;
}

```

*Traducción C exigida a OpenSyn (`generator.syn`):*

```c
int synapse_dividir(int a, int b) {
    // Bloque Requiere
    #ifndef SYNAPSE_RELEASE
    assert(b != 0 && "Fallo de Contrato: requiere b != 0");
    #endif

    int _resultado_ = a / b;

    // Bloque Garantiza
    #ifndef SYNAPSE_RELEASE
    assert((_resultado_ * b == a) && "Fallo de Contrato: garantiza _resultado_ * b == a");
    #endif

    return _resultado_;
}

```

**Nota Arquitectónica:** En compilación para producción (`--release`), el compilador omitirá los asserts para maximizar el rendimiento. Por lo tanto, ningún contrato debe contener lógica con efectos secundarios (ej. no se puede instanciar variables dentro de un `requiere`).

---

## PARTE IV: RESTRICCIONES DE HARDWARE Y EDGE AI

Synapse está destinado a correr inferencia de IA local y operaciones de alta eficiencia.

1. **Sobrecarga Mínima:** El runtime (`synapse_rt.c`) no debe superar los 500 KB en su binario estático.
2. **Agnóstico del Entorno:** La compilación del código generado (GCC/Clang) debe ejecutarse correctamente tanto en sistemas con CPU de recursos limitados (ej. arquitectura x86_64, procesadores de doble núcleo) sin depender de instrucciones exclusivas de GPUs o aceleradores a menos que se importen módulos específicos explícitamente (`std.simd`).

---

**[FIN DE LA PARTE 1]**

El diseño arquitectónico base, las directivas del ejecutor y las leyes de memoria y concurrencia han sido establecidas.

# DOCUMENTO MAESTRO DE INGENIERÍA INDUSTRIAL: SYNAPSE Y OPENSYN (CONTINUACIÓN)

---

## PARTE V: EL ECOSISTEMA AXON (GESTOR DE PAQUETES ENCRIPTADO Y SOBERANO)

**Axon** es el sistema nervioso de Synapse. A diferencia de gestores de dependencias tradicionales (como `npm` o `pip`) que dependen de repositorios centralizados vulnerables a ataques de cadena de suministro (Supply Chain Attacks), Axon está diseñado bajo una arquitectura de **Confianza Cero (Zero Trust)** y **Distribución Encriptada**.

### 5.1 Especificación Criptográfica y Resolución de Dependencias

Cualquier módulo externo de Synapse debe ser importado a través de Axon. Las reglas de diseño para la implementación de `axon.exe` por parte de OpenSyn son absolutas:

1. **Firma Obligatoria (Ed25519):** Todo paquete publicado o descargado debe estar firmado criptográficamente por el autor utilizando curvas elípticas (Ed25519). El compilador rechazará automáticamente cualquier paquete cuya firma no coincida con su hash de contenido (SHA-256 o SHA-3).
2. **Inmutabilidad del Manifiesto (`axon.lock`):** El archivo de bloqueo no es opcional. Axon debe generar un grafo de dependencias determinista. Si un ingeniero compila el mismo proyecto en dos máquinas distintas, el hash binario resultante debe ser bit a bit idéntico (Reproducible Builds).
3. **Red P2P / Nodos Aislados:** Axon debe soportar la resolución de dependencias desde repositorios locales (carpetas *offline* físicas) o redes privadas de la empresa, sin obligar al host a conectarse a internet.

### 5.2 Estructura del Manifiesto `proyecto.axon`

El diseño del AST para leer el manifiesto del proyecto debe soportar la siguiente estructura estrictamente tipada:

```toml
[paquete]
nombre = "nucleo_tensor"
version = "1.0.0"
autor = "Firma_Publica_Hex_a1b2c3..."
tipo = "estatico" # o "dinamico"

[dependencias]
# El hash asegura que la versión no fue alterada en tránsito
"std.matematicas" = { version = "0.9.1", hash = "sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08" }

```

**Directiva para OpenSyn:** La implementación del comando `axon fetch` debe descargar los paquetes en un espacio de memoria aislado, verificar los hashes contra el `axon.lock`, y si existe la más mínima discrepancia, borrar la caché completa e interrumpir la compilación con un código de error fatal `ERR_AXON_COMPROMISED`.

---

## PARTE VI: EXPERIENCIA DEL DESARROLLADOR (LSP Y TELEMETRÍA LOCAL)

Para que Synapse sea adoptado a nivel industrial, requiere herramientas que asistan al ingeniero sin comprometer la privacidad. Esto se logra mediante el **Language Server Protocol (LSP)** nativo.

### 6.1 Arquitectura del Servidor LSP (`synapse_lsp.exe`)

OpenSyn debe desarrollar un binario secundario que se comunique mediante JSON-RPC sobre la entrada/salida estándar (`stdin`/`stdout`). Este servidor alimentará entornos como VS Code.

**Capacidades Exigidas del LSP:**

1. **Diagnósticos en Tiempo Real:** El LSP debe ejecutar el Lexer y el Parser (`parser.syn`) en un hilo de fondo. Cada vez que el usuario guarde el archivo, el LSP debe mapear los errores sintácticos y de violaciones de *Ownership* (Pertenencia) a la línea y columna exacta del editor.
2. **Puente de IA Local (Local-LLM Bridge):** El LSP de Synapse debe estar preparado para interactuar con modelos locales (ej. Ollama, Phi-3). Toda telemetría y contexto (comentarios, nombres de variables) debe procesarse exclusivamente en la máquina host (*localhost*). Está terminantemente prohibido integrar llamadas a APIs de nube (como OpenAI o Anthropic) en el código base del compilador o del LSP.

**Mapeo de Errores de Memoria en el Editor:**
Si el desarrollador escribe código que viola el ciclo de vida de un puntero, el LSP no debe arrojar un error genérico. Debe trazar la vida de la variable y mostrar exactamente dónde se invalidó.
*Mensaje de Error Exigido:* `[ERR_LIFETIME]: El puntero 'matriz_pesos' fue movido al canal 'mi_canal' en la línea 45. El intento de lectura en la línea 48 viola la seguridad de memoria.`

---

## PARTE VII: PROTOCOLO DE PRUEBAS DESTRUCTIVAS (FUZZING AXON.TQC)

Antes de que la versión **1.0 (Gold Master)** de Synapse pueda ser liberada, OpenSyn debe someter tanto el compilador como el runtime a pruebas destructivas sistemáticas. No buscamos probar que funciona; **buscamos intentar destruirlo.**

### 7.1 Fuzzing del Compilador (Frontend)

El binario `synapse2.exe` debe ser sometido a un analizador *Fuzzer* (como AFL++ o libFuzzer).

* **Mecanismo:** Se generarán decenas de millones de archivos `.syn` con caracteres aleatorios, cierres de llaves incorrectos, y caracteres Unicode malformados.
* **Criterio de Aprobación:** El compilador **jamás** debe generar una violación de segmento (*Segmentation Fault*). Todo archivo inválido, sin importar qué tan corrompido esté, debe ser manejado por el sistema de recuperación de errores del Parser, terminando la ejecución de forma segura y controlada (`exit code 1`).

### 7.2 Fuzzing del Runtime de Concurrencia (Backend)

Para validar el diseño de la **Parte III (Canales y Contratos)**, OpenSyn debe codificar una prueba de estrés masiva en C (generado por Synapse):

* **Mecanismo:** Levantar simultáneamente **10,000 hilos** de ejecución. Cada hilo debe crear datos dinámicos, pasarlos a través de canales de alta presión, y leerlos en el otro extremo usando contratos lógicos (`requiere`/`garantiza`).
* **Criterio de Aprobación:** Tras 24 horas de ejecución ininterrumpida bajo el *MemoryWatchdog* (MIM), el sistema debe reportar:
* `0 Deadlocks` (Bloqueos mutuos).
* `0 Data Races` (Carreras de datos, verificadas mediante ThreadSanitizer o equivalente).
* `0 Bytes Perdidos` (Fugas de memoria).



---

## PARTE VIII: PROTOCOLO DE EMERGENCIAS Y RESOLUCIÓN DE DEUDA TÉCNICA

La Ley de "Parar la Línea de Producción" (Stop the World).

Si durante el desarrollo de una nueva fase, un ingeniero o el propio OpenSyn detecta un fallo estructural en los cimientos (fuga de memoria, falla del *Ownership*, vulnerabilidad en el `watchdog`), aplica el siguiente protocolo obligatorio:

1. **Congelamiento Inmediato:** Todo desarrollo de características nuevas (features) queda suspendido.
2. **Aislamiento del Defecto:** Se debe crear un archivo mínimo reproducible (`repro.syn`) que dispare el fallo aislando todas las demás variables.
3. **Auditoría y Parche:** El sistema no avanza hasta que la prueba automatizada que falló esté en verde constante (TQC 100%).

---

## DECLARACIÓN FINAL DEL DIRECTOR DE INGENIERÍA

Este **Documento Maestro** no es una guía de sugerencias, es el código genético del lenguaje.

Si un ingeniero no posee el contexto, o si un sistema de IA sufre degradación de contexto, su primer mandato operativo es re-ingestar la totalidad de este archivo antes de emitir una sola línea de código en C o Synapse.

El proyecto Synapse tiene como objetivo redefinir la programación de sistemas eliminando los compromisos entre la velocidad del metal y la seguridad matemática. La ejecución a partir de este punto debe ser implacable, matemática y libre de errores voluntarios.

**[FIN DEL DOCUMENTO MAESTRO]**
*(Archivado y bloqueado para escritura. Sello de Aprobación TQC).*