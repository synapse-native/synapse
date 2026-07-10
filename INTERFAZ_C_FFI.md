# Synapse: Interfaz de Función Foránea (FFI) y Puente a C

## 1. El Límite del Metal
Para construir un sistema operativo o interactuar con el hardware de bajo nivel, Synapse necesita consumir librerías escritas en C (como rutinas de cifrado, drivers o POSIX). La Interfaz de Función Foránea (FFI) permite llamar a funciones C directamente desde Synapse con un costo de abstracción cero (Zero-Cost Abstraction).

## 2. Declaración de Funciones Externas (`externo`)
Synapse no incluye cabeceras de C (`#include <header.h>`) directamente en el código fuente para mantener la pureza de su analizador léxico. En su lugar, el programador debe declarar la firma de la función C utilizando la palabra reservada `externo`.

**Sintaxis:**
```synapse
// Declaración de la función C 'write' de POSIX (unistd.h)
externo funcion escribir_posix(fd: entero, buffer: cadena, cuenta: entero) -> entero

funcion principal() -> nulo:
    inseguro:
        bytes = escribir_posix(1, "Hola SO\n", 8)

3. Mapeo Estricto de Tipos (ABI)El compilador y el generador de Synapse asumen el siguiente mapeo binario exacto con la Interfaz Binaria de Aplicación (ABI) de C:Tipo SynapseTipo C (stdint.h / nativo)Tamaño en Memoriaenteroint64_t8 bytesflotantedouble8 bytesbooleanostdbool.h (bool)1 bytecaracterchar1 bytenulovoid0 bytes3.1. El Problema de las Cadenas (CadenaSegura vs char*)Synapse maneja internamente las cadenas de texto como un struct (llamado CadenaSegura) que contiene un puntero a los datos y la longitud de la cadena, previniendo los desbordamientos de búfer típicos de C (Buffer Overflow).Cuando se pasa una cadena de Synapse a una función externo, el Generador extrae automáticamente el puntero subyacente (.datos) y lo pasa como un const char* terminado en null (\0), garantizando la compatibilidad con C sin requerir conversiones manuales costosas.4. Regla de Seguridad: Aislamiento inseguroCualquier llamada a una función declarada como externo viola las garantías de seguridad de memoria del Borrow Checker de Synapse (ya que C puede liberar punteros, escribir fuera de límites, etc.). Por lo tanto, invocar una función externa fuera de un bloque inseguro: producirá un error semántico fatal en tiempo de compilación.
***

### Documento 8: `CONCURRENCIA_NATIVA.md`

```markdown
# Synapse: Física de los Hilos y Concurrencia Nativa

## 1. Filosofía (Share Memory by Communicating)
La mayor fuente de vulnerabilidades en sistemas concurrentes es el estado mutable compartido (condiciones de carrera). Synapse prohíbe esto por diseño. No existen los `Mutex` globales ni los semáforos expuestos al usuario. La memoria de un hilo está aislada; la comunicación se realiza pasando copias o transfiriendo la propiedad (Ownership) a través de Canales.



## 2. La Instrucción `lanzar` (Spawning)
Para crear un hilo asíncrono (respaldado por `pthreads` en el metal), se utiliza la palabra clave `lanzar` seguida de una llamada a función.

* **Regla de Posesión:** Cualquier variable pasada como argumento a la función lanzada sufre un *Move* definitivo. El hilo principal pierde el derecho de acceso.

```synapse
funcion trabajador(id: entero, config: Configuracion) -> nulo:
    // El trabajador ahora es el único dueño de 'config'
    escribir_linea("Hilo activo")

funcion principal() -> nulo:
    conf = cargar_configuracion()
    lanzar trabajador(1, conf)
    // imprimir(conf) -> ERROR SEMÁNTICO: 'conf' fue movida al hilo
3. El Puente Seguro (std.concurrencia.Canal)Para intercambiar información de forma segura, se utiliza la primitiva Canal<T>.3.1. Tipos de CanalesCanales Síncronos (Por defecto): No tienen búfer. El hilo emisor se bloquea hasta que el hilo receptor lee el mensaje. Esto evita picos de consumo de RAM invisibles.Canales Asíncronos (Con búfer): Permiten al emisor colocar hasta N mensajes antes de bloquearse.3.2. Operaciones de Envío y RecepciónLa librería estándar provee enviar y recibir. Ambas operaciones son Thread-Safe y manejadas atómicamente en C.Fragmento de códigoimportar std.concurrencia

funcion productor(c: Canal) -> nulo:
    c.enviar("Datos cifrados listos")

funcion principal() -> nulo:
    canal_datos = concurrencia.crear_canal()
    lanzar productor(canal_datos)
    
    // Bloquea el hilo principal hasta recibir el mensaje
    mensaje = canal_datos.recibir()
    escribir_linea(mensaje)
4. Prevención de DeadlocksAunque Synapse previene Data Races (Carreras de Datos) en tiempo de compilación, los Deadlocks (abrazos mortales donde dos hilos se esperan mutuamente para siempre) son un problema lógico en tiempo de ejecución. Para mitigarlos, recibir() puede retornar un ADT Resultado si el canal se destruye o si se configura con un tiempo límite (timeout), forzando al desarrollador a manejar el escenario de falla mediante coincidir.
***

### Documento 9: `MANUAL_TQC.md`

```markdown
# Synapse: Manual de Control de Calidad Total (TQC)

## 1. La Línea de Montaje Inquebrantable
Synapse no confía en la pericia del desarrollador del compilador. Confía en la matemática y en el castigo de la máquina. Este documento detalla la línea de comandos estricta para integrar el compilador en un pipeline CI/CD de grado industrial. Ningún commit (Pull Request) será fusionado a la rama principal (main) si falla alguna de estas tres etapas.

## 2. Etapa 1: Fuzzing Léxico y Sintáctico (Resiliencia)
El servidor LSP no debe caer ante código corrupto. 
**Herramienta:** AFL++ (American Fuzzy Lop) o Fuzzer Interno de Synapse.
**Comando de estrés:**
```bash
./scripts/fuzzer.sh --target dist/bin/synapse.exe --time 10m
Criterio de Aceptación: Durante 10 minutos de inyección de ruido (bits invertidos, truncamientos masivos, secuencias Unicode rotas), el ejecutable no debe arrojar un solo volcado de memoria (Core Dump / Segfault). Todo error debe ser manejado e impreso como un diagnóstico de Synapse (código de salida diferente a abort).3. Etapa 2: Sanitización de Metal (Memoria e Hilos)El código C generado por Synapse debe ser impoluto. Se utiliza la batería de sanitizadores de LLVM/GCC en las compilaciones de prueba.3.1. AddressSanitizer (ASan) & LeakSanitizer (LSan)Verifica acceso a memoria fuera de límites, Use-After-Free en los bloques inseguros y fugas de memoria estáticas.Comando de prueba:Bashsynapse probar --auditar-memoria
# Internamente ejecuta: gcc -fsanitize=address,leak tests/*.c
3.2. ThreadSanitizer (TSan)Vigila la memoria en tiempo de ejecución para detectar hilos accediendo concurrentemente a la misma dirección sin sincronización atómica.Comando de prueba:Bashsynapse probar --auditar-hilos
# Internamente ejecuta: gcc -fsanitize=thread tests/*.c
Criterio de Aceptación: El binario de prueba debe retornar salida 0. Una sola advertencia del sanitizador bloquea la línea de producción.4. Etapa 3: Regresión Continua del AST (Equivalencia)Cada modificación al compilador debe producir el mismo Árbol de Sintaxis Abstracta (o mejorado) sin corromper proyectos antiguos.El Test de Espejo:Compilar el archivo de referencia (tests/canon.syn) con el binario antiguo y volcar el AST: --dump-ast > ast_viejo.json.Compilar con el nuevo binario propuesto: --dump-ast > ast_nuevo.json.Ejecutar diff estricto.Criterio de Aceptación: Si se modificó la gramática formal intencionalmente, el diff debe ser auditado manualmente. Si es una optimización interna (refactor de código), el diff debe ser exactamente 0 bytes de diferencia.