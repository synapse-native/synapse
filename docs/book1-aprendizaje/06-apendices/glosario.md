# Glosario de Términos

Este apéndice define los términos técnicos utilizados a lo largo del libro. Incluye definiciones claras y concisas de conceptos de programación, concurrencia, seguridad de tipos y más.

Úsalo como referencia rápida cuando encuentres un término desconocido.

<!-- cumple Manual 1-9 -->

## A

### ADT (Algebraic Data Type)
Tipo algebraico de datos. Unión etiquetada que puede tener uno de varios constructores. Ejemplo: `Resultado<T, E> = ok(T) | err(E)`.

### Arena
Bloque de memoria contiguo del cual se asignan objetos mediante bump allocator. La liberación es O(1) al salir del ámbito. Usado en Syquex por defecto.

### AST (Abstract Syntax Tree)
Árbol de Sintaxis Abstracta. Representación en árbol del código fuente después del parsing. Usado por el compilador y OpenSyn para análisis.

### Async/Await
Patrón de programación para operaciones asíncronas. En Syquex, se implementa con fibras y canales.

### Axon
Gestor de paquetes del ecosistema Synapse. Maneja dependencias, versiones y verificación de integridad.

## B

### Binding
Enlace entre lenguajes. Permite que código Synapse/Syquex use funciones de C (o viceversa) mediante una capa de marshaling.

### Borrowing (Préstamo)
Mecanismo de Synapse para acceder a un valor sin tomar posesión. Sintaxis: `&T` (inmutable) o `&mut T` (mutable).

### Bump Allocator
Algoritmo de asignación de memoria que simplemente incrementa un puntero. Muy rápido (O(1)) pero no permite liberación individual.

## C

### Canal (Channel)
Mecanismo de comunicación entre fibras/hilos. Tipado (`Canal<T>`), thread-safe, y aplica move semantics al transferir datos.

### CadenaSegura
Tipo de datos para cadenas de texto en Synapse. Estructura de 16 bytes con `{char* datos; int longitud; int capacidad}`.

### Código de Idioma (#lang:)
Directiva obligatoria en la primera línea de archivos Synapse/Syquex. Indica el idioma del código (`#lang: es`).

### Coincidir (Match)
Pattern matching exhaustivo. En Syquex, la instrucción `coincidir` requiere cubrir todos los casos de un ADT.

### Compilador Cruzado
Compilador que genera código para una plataforma diferente a la que se ejecuta. Ejemplo: compilar en Linux para Windows.

### Contrato (Contract)
Especificación formal del comportamiento de una función. En Synapse: `requiere` (precondición) y `garantiza` (postcondición).

### CUDA
Arquitectura de cómputo paralelo de NVIDIA. Usada por OpenSyn para aceleración GPU.

## D

### Débil (Weak Reference)
Referencia que no incrementa el conteo de referencias. Previene ciclos. Se invalida cuando el objeto fuerte se destruye.

### Dispatch Dinámico
Resolución en tiempo de ejecución de qué método llamar. Usado para polimorfismo con traits/interfaces.

### Donde Cláusula (Where Clause)
Restricción sobre tipos genéricos. Ejemplo: `funcion ordenar<T: Comparable>(lista: Lista<T>)`.

## E

### EBNF
Extended Backus-Naur Form. Notación para describir gramáticas formales. Usada en los manuales 2 y 3.

### Enumeración (Enum)
Tipo de dato que puede tomar uno de un conjunto finito de valores nombrados. En Syquex: `enumeracion`.

### Error de Compilación
Problema detectado por el compilador antes de ejecutar el programa. Ejemplos: errores de sintaxis, tipos incompatibles, ownership inválido.

### Error de Runtime
Problema que ocurre durante la ejecución del programa. Ejemplos: división por cero, stack overflow, archivo no encontrado.

### Escapado
Mecanismo para incluir caracteres especiales en strings. En Synapse: `\\n`, `\\t`, `\\\\`, `\\\"`.

## F

### Fibra
Hilo de usuario ultraligero. Las fibras en Synapse/Syquex pesan ~64 KB vs megabytes de un hilo del sistema operativo.

### FFI (Foreign Function Interface)
Interfaz para llamar funciones escritas en otros lenguajes. En Synapse: `@export`. En Syquex: `externo`.

### File Watcher
Componente que observa cambios en archivos del sistema de archivos y notifica al programa.

### Flujo (Stream)
Secuencia de datos que se procesa de forma incremental. Soporta operaciones lazy como `mapear`, `filtrar`.

## G

### GIL (Global Interpreter Lock)
Mecanismo de Python que limita la concurrencia real. Synapse/Syquex no tiene GIL.

### GC (Garbage Collector)
Recolector de basura. Mecanismo automático de gestión de memoria. Synapse/Syquex no usa GC, sino arenas + RC.

### Generic
Función o tipo que funciona con múltiples tipos. En Synapse/Syquex: `<T>`.

### Gradio
Framework para construir interfaces de usuario para modelos de IA. Similar a Streamlit.

## H

### Hilo (Thread)
Unidad de ejecución concurrente del sistema operativo. Las fibras son más ligeras que los hilos.

### Hiper-parámetro
Parámetro de configuración que controla el comportamiento de un modelo o algoritmo. No se aprende de los datos.

## I

### Inmutable
Que no puede cambiar después de ser creado. En Synapse: `constante`. En Syquex: `constante`.

### Instanciar
Crear un objeto a partir de una clase/estructura. En Syquex: `Persona("Ana", 28)`.

### Interoperabilidad
Capacidad de dos sistemas para trabajar juntos. En Synapse/Syquex: FFI a C, exportación a Python/TS.

### Intentar/Atrapar
Try/catch. Manejo de errores en tiempo de ejecución. En Syquex: `intentar ... atrapar e: ...`.

## L

### Lambda
Función anónima. En Syquex: `lambda x: x * 2`.

### Lifetime
Tiempo de vida de una referencia. En Synapse, analizado estáticamente para evitar uso después de liberación.

### LSP (Language Server Protocol)
Protocolo estándar para integración de lenguajes con editores. Usado por Synapse para VS Code, Vim, etc.

## M

### Marshaling
Conversión de datos entre diferentes formatos o representaciones. Usado en FFI para adaptar tipos.

### Match Exhaustivo
Pattern matching que cubre todos los casos posibles. Requerido para ADTs en Synapse/Syquex.

### Memoria Automática
Gestión automática de memoria sin intervención del programador. Syquex usa arenas + análisis de alcance.

### Metaprogramación
Programación que manipula o genera código. En Syquex: generación de bindings, macros (futuro).

### Método
Función asociada a una estructura. En Syquex: `metodo nombre(): ...`.

### Move Semantics
Transferencia de ownership de un valor. Después del move, la variable original es inválida.

### Mutex
Primitiva de sincronización que permite acceso exclusivo a un recurso. En Synapse: `inseguro` blocks.

## N

### No-op
Operación que no tiene efecto. Usado en el compilador para literales estáticos.

## O

### OpenSyn
Asistente de IA local del ecosistema Synapse. Genera código, explica, refactoriza, transpila, todo local.

### Ownership (Posesión)
Modelo de memoria donde cada valor tiene un único "dueño". Cuando el dueño sale del ámbito, el valor se libera.

## P

### Parsing
Análisis sintáctico del código fuente para construir un AST.

### Pipeline
Cadena de procesamiento de datos donde la salida de una etapa es la entrada de la siguiente.

### Préstamo (Borrow)
Ver "Borrowing".

### Protocolo
Conjunto de reglas que definen cómo se comunican dos sistemas. Ejemplos: HTTP, LSP, Canal.

### Polimorfismo
Capacidad de código para trabajar con diferentes tipos. En Syquex: traits.

## R

### RAG (Retrieval-Augmented Generation)
Técnica donde un modelo de IA recupera contexto relevante antes de generar una respuesta.

### RC (Reference Counting)
Conteo de referencias. Mecanismo de gestión de memoria donde cada objeto tiene un contador de referencias activas.

### Reactor
Patrón para manejar múltiples fuentes de eventos (I/O, timers) en un solo hilo.

### Recursión
Función que se llama a sí misma. Requiere caso base para terminar.

### Resultado<T, E>
Tipo algebraico que representa éxito (`ok(T)`) o error (`err(E)`). Alternativa a las excepciones.

### Router
Componente que dirige solicitudes a diferentes manejadores o modelos.

## S

### Sandbox
Entorno aislado donde se ejecuta código con permisos restringidos. Usado por OpenSyn para inferencia.

### Semántica
Significado de las expresiones del lenguaje. Distinto de sintaxis (forma).

### Serialización
Conversión de una estructura de datos a un formato que se puede almacenar o transmitir (JSON, binario, etc.).

### Singleton
Patrón de diseño que garantiza una única instancia de una clase.

### Stack Trace
Lista de llamadas de funciones activas cuando ocurre un error.

### Struct
Ver "Estructura".

### Subtipo
Tipo que es compatible con otro tipo (más específico). En Synapse/Syquex: jerarquía de tipos.

## T

### Tensor
Tipo nativo de Synapse para matrices multidimensionales. Usado para IA y cómputo numérico.

### Token
Unidad léxica. El lexer convierte código fuente en tokens antes del parsing.

### Trait
Conjunto de métodos que una estructura puede implementar. Similar a interfaces en otros lenguajes.

### Type Inference
Inferencia de tipos. El compilador deduce el tipo de una expresión sin anotación explícita. Algoritmo Hindley-Milner.

## U

### Union Type
Tipo que puede ser uno de varios tipos específicos. En Synapse: tipos algebraicos.

## V

### Valor por Defecto
Valor que toma un parámetro si no se proporciona explícitamente. En Syquex: `param: tipo = valor`.

### Variable
Enlace entre un nombre y un valor. En Synapse: `let x = 5`.

### Verificación Formal
Prueba matemática de que el código cumple con una especificación. En Synapse: motor ATP en modo `--safe`.

## W

### WebSocket
Protocolo de comunicación bidireccional sobre TCP. Usado para chat en tiempo real, notificaciones, etc.

### Work-Stealing
Algoritmo de balanceo de carga donde hilos inactivos "roban" trabajo de hilos ocupados.

## Símbolos y Términos Cortos

| Símbolo | Significado |
|---------|-------------|
| `&` | Préstamo inmutable (referencia) |
| `&mut` | Préstamo mutable |
| `->` | Tipo de retorno / Move semantics |
| `<-` | Enviar a canal |
| `?` | Propagación de error |
| `*` | Multiplicación / Puntero |
| `!` | Negación lógica |
| `==` | Comparación de igualdad |
| `:=` | Asignación (algunos lenguajes) |
| `_` | Wildcard / Valor descartado |

## Referencias

- **Manual 1-9**: Documentación completa del ecosistema
- **Manual 2 §1-3**: Sintaxis y semántica de Synapse
- **Manual 3 §1-3**: Sintaxis y semántica de Syquex
- **Manual 4 §2-6**: Modelo de memoria de Syquex
- **Manual 5 §2-5**: Concurrencia y comunicación
- **Manual 6 §1-5**: Integración del ecosistema

// cumple Manual 1-9
