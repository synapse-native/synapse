# MANUAL DE INGENIERÍA Y DESARROLLO DE SYNAPSE (v3.0)

**Documento Oficial de Arquitectura, Especificación de Compilador e Implementación**
*Clasificación: Ingeniería / Uso Interno — Núcleo de Desarrollo*

---

## 1. INTRODUCCIÓN Y ALCANCE DE LA INGENIERÍA

Este manual constituye la especificación técnica fundamental para el diseño, desarrollo, mantenimiento y evolución del ecosistema **Synapse**. Su propósito es servir como referencia inequívoca para cualquier ingeniero que se incorpore al proyecto, estableciendo las estructuras de datos, los algoritmos de compilación, las reglas semánticas y los protocolos de integración del runtime.

El desarrollo de Synapse no tolera ambigüedades. Cada módulo está subordinado a los principios de **El Pacto**: tipado estricto inferido, gestión de memoria determinista sin recolector de basura (Ownership & Borrowing), tipado algebraico de errores y rendimiento nativo optimizado con backend C/GCC.

---

## 2. ESTRUCTURA DEL REPOSITORIO Y WORKSPACE LAYOUT

El repositorio está organizado de forma modular para desacoplar el compilador autocontenido, el runtime, el gestor de paquetes y el demonio LSP.

```text
/synapse
│
├── .github/              # Pipelines de CI/CD (Matriz multi-arquitectura y firmas Ed25519)
├── nucleo/               # Código fuente del compilador (Lexer, Parser, Semántico, Generador C)
│   ├── lexer.syn         # Tokenizador e inyector de indentación
│   ├── parser.syn        # Parser de descenso recursivo
│   ├── analizador_semantico.syn # Motor de tipado y verificación de Ownership
│   ├── generator.syn     # Emisor de código C optimizado (-O2)
│   ├── ai_orchestrator.c # Subproceso C para el ciclo de vida de llama-server.exe
│   ├── llama_client.c    # Cliente HTTP nativo para la inferencia local de OpenSyn
│   └── synapse_rag.c     # Pipeline RAG quirúrgico y gestión dinámica de n_ctx
│
├── std/                  # Biblioteca estándar del lenguaje
│   ├── net.syn           # std::net (HTTP / TCP nativo)
│   ├── json.syn          # std::json (Serialización acelerada por SIMD)
│   └── concurrencia.syn  # std::concurrencia (Canales tipados Canal<T>)
│
├── axon/                 # Gestor de paquetes inmutable y criptográfico
│   ├── axon_rt.c         # Runtime de Axon (Verificación Ed25519, manejo TAR)
│   └── axon.toml         # Especificación de metadatos de paquetes
│
├── vscode-synapse/       # Extensión oficial para VS Code y cliente LSP
│   └── src/              # Interfaz TypeScript para el demonio synapse_lsp
│
└── tests/                # Suite de pruebas unitarias, de integración y fuzzing (317+ tests)

```

---

## 3. ESPECIFICACIÓN LÉXICA (`lexer.syn`)

El analizador léxico (`lexer.syn`) es el responsable de transformar el flujo de caracteres de un archivo `.syn` en un flujo estructurado de tokens, controlando de manera estricta la indentación por bloques (regla de los 4 espacios) y validando la cabecera del idioma.

### 3.1. Requisitos de Cabecera y Codificación

* Todo archivo fuente válido **debe** comenzar obligatoriamente en la línea 1 con la directiva de idioma:
```synapse
#lang: es

```


Cualquier archivo que omita esta directiva es rechazado de inmediato por el lexer con el código de error `ERR_LEX_MISSING_LANG`.

### 3.2. Gestión de Indentación (Control de Bloques)

Synapse prohíbe el uso de llaves `{ }` para delimitar bloques. El alcance sintáctico se determina mediante un sistema de pila de indentación (`IndentStack`) evaluado en el lexer:

1. Se contabilizan exclusivamente los espacios al inicio de línea (múltiplos estrictos de 4 espacios). Los tabuladores (`\t`) están prohibidos y generan un error de compilación estático (`ERR_LEX_TAB_DETECTED`).
2. Si el nivel de indentación actual es mayor que el nivel en la cima de la pila, se emite un token sintético `T_INDENT` y se hace `push`.
3. Si el nivel es menor, se emiten tantos tokens `T_DEDENT` como cierres de bloque sean necesarios, haciendo `pop` hasta coincidir con el nivel activo.

### 3.3. Tabla de Tokens Canónicos

El lexer emite estructuras de tipo `Token` con los siguientes campos: `tipo` (Enum), `valor` (String), `linea` (Entero) y `columna` (Entero). Los tipos fundamentales incluyen:

* `T_LANG_DIRECTIVE`: `#lang:`
* `T_IDENT`: Identificadores de variables y funciones (`[a-zA-Z_][a-zA-Z0-9_]*`)
* `T_KEYWORD`: Palabras reservadas (`let`, `fn`, `coincidir`, `ok`, `err`, `lanzar`, `requiere`, `garantiza`)
* `T_COLON`: `:` (Apertura obligatoria de bloque)
* `T_NEWLINE`: Fin de línea significativo
* `T_INDENT` / `T_DEDENT`: Delimitadores de ámbito de bloque

---

## 4. ESPECIFICACIÓN SINTÁCTICA Y PARSER (`parser.syn`)

El parser de Synapse implementa un algoritmo de **descenso recursivo puro** sin retroceso (*backtracking*), optimizado para garantizar un tiempo de compilación lineal $\mathcal{O}(n)$.

### 4.1. Gramática Formal (EBNF de Bloques y Funciones)

```ebnf
Programa       ::= LangDirective { Declaracion }
LangDirective  ::= "#lang:" Identificador Newline
Declaracion    ::= FuncionDef | EstructuraDef | ConstDef
FuncionDef     ::= "fn" Identificador "(" [ Parametros ] ")" [ "->" Tipo ] [ Contratos ] ":" Newline Indent Bloque Dedent
Contratos      ::= [ "requiere" Expr ] [ "garantiza" Expr ]
Parametros     ::= Identificador ":" Tipo { "," Identificador ":" Tipo }
Bloque         ::= { Sentencia Newline }
Sentencia      ::= Asignacion | Retorno | Condicional | Coincidencia | Expresion
Coincidencia   ::= "coincidir" Expresion ":" Newline Indent { PatronCaso } Dedent
PatronCaso     ::= Patron "=>" ( Sentencia | Newline Indent Bloque Dedent )

```

### 4.2. Prevención de Ambigüedades

Para evitar problemas de precedencia de operadores, el parser evalúa las expresiones aritméticas y lógicas mediante funciones de precedencia escalonadas (de menor a mayor: asignación, lógico-or, lógico-and, igualdad, relacionales, aditivos, multiplicativos, unarios).

---

## 5. EL AST CANÓNICO (`ast_nodes.syn`)

El Árbol de Sintaxis Abstracta (AST) de Synapse se serializa internamente en estructuras de nodos fuertemente tipadas (convertibles a formato `.syn.json` para herramientas de migración y análisis estático).

### 5.1. Definición de Nodos Fundamentales

Cada nodo se representa como una estructura con metadatos de origen (archivo, línea, columna) y un identificador de tipo de nodo (`NodoTipo`):

* `NODO_PROGRAMA`: Contiene la lista de declaraciones globales.
* `NODO_FUNCION`: Contiene nombre, lista de parámetros tipados, tipo de retorno, contratos lógicos (`requiere`/`garantiza`) y el bloque de sentencias.
* `NODO_ASIGNACION`: Define la ligadura de un símbolo mediante `let` o inferencia mutable, especificando el tipo estricto.
* `NODO_COINCIDENCIA`: Representa la estructura de desempaquetado obligatorio para tipos algebraicos (`Resultado<T,E>` y `Opcion<T>`).

---

*Estado del Manual: Parte 1 completada conforme a los parámetros de ingeniería de Synapse v3.0.*

## 6. ANALIZADOR SEMÁNTICO Y SISTEMA DE TIPOS (`analizador_semantico.syn`)

El analizador semántico es el auditor central de **El Pacto**. Su función es procesar el AST canónico para resolver símbolos, verificar la consistencia de tipos estrictos e imponer las reglas de ciclo de vida de las variables antes de permitir la generación de código.

### 6.1. Ejecución en Tres Fases (Three-Pass Analysis)

Para evitar problemas de orden de declaración (forward declarations implícitas), el análisis semántico opera estrictamente en tres pasadas secuenciales:

1. **Pasada 1 (Estructuras y Tipos Globales):** Recorre el AST para registrar todas las definiciones de estructuras, tipos algebraicos y constantes globales en la tabla de símbolos principal.
2. **Pasada 2 (Firmas de Funciones):** Analiza las cabeceras de todas las funciones, validando los tipos de los parámetros, los tipos de retorno y los contratos lógicos (`requiere`/`garantiza`).
3. **Pasada 3 (Cuerpos de Código y Verificación de Ownership):** Analiza sintácticamente los bloques internos de cada función, evaluando expresiones, asignaciones, llamadas y flujos de control.

### 6.2. Tipado Estricto e Inferencia

Synapse no utiliza tipado dinámico. Las variables declaradas mediante la palabra clave `let` reciben un tipo estricto deducido por inferencia estática unidireccional en tiempo de compilación. Si una expresión presenta ambigüedad de tipos (ej. operadores mixtos sin conversión explícita), el compilador aborta emitiendo `ERR_SEM_TYPE_AMBIGUOUS`.

### 6.3. Tipos Algebraicos de Datos (ADTs)

El sistema de tipos incorpora uniones etiquetadas nativas para representar estados de éxito o fallo de forma explícita y determinista:

* `Resultado<T, E>`: Envuelve un valor de éxito tipo `T` (`ok`) o un error tipo `E` (`err`).
* `Opcion<T>`: Envuelve un valor existente `T` (`algun`) o la ausencia de valor (`ninguno`).
* **Regla Semántica:** El uso de estos tipos exige de manera obligatoria la instrucción de control `coincidir`. Omitir un caso en la coincidencia genera un error de compilación estático (`ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED`).

---

## 7. EL PACTO: SEGURIDAD DE MEMORIA (OWNERSHIP & BORROWING)

Synapse prescinde totalmente de un Recolector de Basura (Garbage Collector) y prohíbe el uso de asignación manual de memoria (`malloc`/`free`) en el código de usuario. La gestión de memoria se rige por un modelo estricto de **Posesión Única**.

### 7.1. Reglas de Posesión (Ownership)

1. Cada recurso en memoria tiene un **único propietario** (una variable o ámbito que lo enlaza).
2. Cuando el propietario actual sale de su ámbito de visibilidad (*scope*), el compilador inyecta de forma automática y determinista el código de liberación en el emisor C (RAII estático).
3. **Semántica de Movimiento (*Move Semantics*):** Al asignar una variable propietaria a otra o pasarla como argumento de función por valor, la posesión se transfiere (*move*). La variable original queda invalidada en el ámbito origen.
4. **Detección de Use-After-Move:** Si el analizador semántico detecta que una variable invalidada por un *move* previo es consultada o reutilizada, aborta la compilación de inmediato con el error crítico `ERR_MEM_USE_AFTER_MOVE`.

---

## 8. CONCURRENCIA AISLADA Y DISEÑO POR CONTRATO

### 8.1. Concurrencia por Canales Tipados (`std.concurrencia`)

Para garantizar la ausencia absoluta de condiciones de carrera (*data races*) y bloqueos mutuos aleatorios:

* El estado mutable compartido entre hilos está prohibido a nivel de compilación.
* La instrucción `lanzar` inicia un nuevo hilo de ejecución y transfiere de forma segura el *ownership* de las variables capturadas.
* La sincronización se realiza mediante canales fuertemente tipados (`Canal<T>`), asegurando que los datos se muevan de un hilo a otro de manera unidireccional y sin memoria compartida.

### 8.2. Diseño por Contrato (Design by Contract)

Para verificar la corrección lógica del software (y auditar el código generado por asistentes de IA), las funciones admiten especificaciones formales incrustadas en su firma:

* `requiere <expresion_booleana>`: Precondición evaluada al inicio de la función.
* `garantiza <expresion_booleana>`: Postcondición evaluada justo antes del retorno.
* El generador de código traduce estas cláusulas a aserciones de metal en C (`assert()`), fallando de manera segura en tiempo de ejecución si se vulnera el contrato lógico.

---

## 9. GENERADOR DE CÓDIGO C (`generator.syn`)

El generador traduce el AST validado y semánticamente seguro a código fuente C altamente optimizado, sirviendo como paso intermedio antes de invocar al compilador nativo del sistema operativo (GCC/Clang).

### 9.1. Directrices de Emisión

* **Cero Abstracciones Ocultas:** No se emiten macros opacas ni funciones de runtime pesadas. Cada nodo del AST se mapea de forma directa a construcciones de C99/C11 idiomáticas y predecibles.
* **Optimización y Sanitización:** El comando de compilación emite las banderas de optimización agresiva `-O2` y, en entornos de pruebas, incorpora obligatoriamente `-fsanitize=address,undefined` para detectar desbordamientos de búfer o accesos fuera de límites a nivel de binario.

---

## 10. ECOSISTEMA DE IA LOCAL Y LSP (OPENSYN)

El entorno de desarrollo integra un demonio de protocolo de servidor de lenguaje nativo (`synapse_lsp`) y un motor cognitivo soberano (**OpenSyn**).

### 10.1. Arquitectura del LSP (`synapse_lsp`)

* **Comunicación:** Opera mediante el protocolo estándar JSON-RPC 2.0 sobre canales de entrada/salida estándar (`stdio`).
* **Capacidades:** Emite diagnósticos en tiempo real de análisis sintáctico y semántico, soporte para autocompletado de tipos, refactorización y navegación de símbolos.

### 10.2. Orquestación Local de IA (`ai_orchestrator.c` y `llama_client.c`)

* **Ciclo de Vida:** El proceso `ai_orchestrator.c` gestiona de forma autónoma el arranque y apagado seguro de `llama-server.exe`, asegurando mediante *Shutdown Hooks* (`atexit` y señales del SO) la liberación inmediata de RAM y VRAM al cerrar el editor.
* **Pipeline RAG Quirúrgico (`synapse_rag.c`):** Extrae de manera local el nodo AST actual, la línea y los diagnósticos del compilador para inyectarlos como un system prompt compacto, aplicando una negociación dinámica de la ventana de contexto (`n_ctx`) donde el 30% se reserva para la inyección de contexto y el 70% para la generación del modelo.

---

## 11. GESTOR DE PAQUETES INMUTABLE (AXON)

Axon es el sistema de gestión de dependencias de Synapse, diseñado bajo estrictos criterios de seguridad de la cadena de suministro.

### 11.1. Reglas de Hierro de Axon

* **Prohibición de Ejecución Arbitraria:** Axon **no permite** scripts de pre-instalación o post-instalación (`preinstall`/`postinstall`), neutralizando vectores de ataque de ejecución de código malicioso en la máquina del desarrollador.
* **Firma Criptográfica Obligatoria:** Toda dependencia descargada debe estar firmada criptográficamente mediante el algoritmo **Ed25519** (implementado de forma nativa a través de TweetNaCl). El gestor rechaza cualquier paquete cuya firma no coincida con el registro.
* **Bloqueo Determinista (`axon.lock`):** Cada compilación utiliza hashes SHA-256 inmutables para garantizar builds idénticos en cualquier entorno.
* **Protección contra Path Traversal:** El runtime de Axon (`axon_rt.c`) bloquea de forma estricta cualquier intento de descompresión que contenga rutas relativas (`../`) o rutas absolutas maliciosas dentro de los archivos TAR.


## 12. ESPECIFICACIÓN DE LA BIBLIOTECA ESTÁNDAR (`std`)

La biblioteca estándar de Synapse proporciona los bloques de construcción fundamentales para el desarrollo de software de propósito general y alto rendimiento, evitando la dependencia de ecosistemas externos voluminosos.

### 12.1. Módulo de Red e Infraestructura (`std::net`)

* **Propósito:** Proveer abstracciones nativas y eficientes para sockets TCP y protocolos HTTP de alta velocidad.
* **Implementación:** Acoplado directamente a las llamadas del sistema de red subyacentes (`winsock2` en Windows, `sockets` POSIX en Unix), minimizando la sobrecarga de abstracción.
* **Modelo de Uso:** Las operaciones de E/S de red operan bajo tipos algebraicos `Resultado<Conexion, ErrorRed>`, obligando al programador a manejar explícitamente los fallos de conectividad o timeouts.

### 12.2. Módulo de Procesamiento de Datos (`std::json`)

* **Propósito:** Serialización y deserialización de estructuras de datos hacia y desde JSON.
* **Aceleración SIMD:** El motor de análisis sintáctico de JSON utiliza instrucciones vectoriales (SSE/AVX/AVX2 detectadas en tiempo de ejecución por `_simd_detectar()`) para procesar bloques de texto masivos a velocidades que superan los parsers basados en intérpretes tradicionales.

### 12.3. Módulo de Concurrencia (`std::concurrency`)

* **Propósito:** Gestión de hilos de ejecución paralelos mediante canales seguros.
* **Canales Tipados (`Canal<T>`):** Estructuras de paso de mensajes FIFO thread-safe que garantizan que los datos enviados por un hilo sean consumidos de forma exclusiva por otro, impidiendo el intercambio de referencias mutables concurrentes y eliminando por diseño las condiciones de carrera.

---

## 13. PRUEBAS, FUZZING Y ASEGURAMIENTO DE CALIDAD

La estabilidad de Synapse se sustenta en una suite de pruebas automatizadas exhaustiva de más de 317 casos de prueba distribuidos en múltiples capas de validación.

### 13.1. Arquitectura de Testing

* **Suite Python (`pytest`):** Contiene más de 297 pruebas unitarias y de integración que validan de forma aislada el comportamiento del Lexer, el Parser, el Analizador Semántico, el Generador C y el comportamiento del LSP.
* **Suite Nativa en C:** Compila y ejecuta pruebas específicas de bajo nivel para el orquestador de IA (`ai_orchestrator`), el cliente de `llama.cpp` y la robustez de los *Shutdown Hooks* ante señales del sistema operativo.

### 13.2. Fuzzing Destructivo y Estrés de Concurrencia

* **Fuzzing Estructural:** Se inyectan más de 800 entradas sintácticamente corruptas, maliciosas o desbordadas para verificar la resiliencia del parser y del analizador semántico ante fallos inesperados (garantizando 0 crashes).
* **Pruebas de Estrés Concurrente:** Ejecución masiva de pruebas con más de 10,000 hilos concurrentes interactuando a través de canales tipados, validando matemáticamente la ausencia de *deadlocks* y fugas de memoria.

---

## 14. PROCESO DE BOOTSTRAP Y AUTO-HOSPEDAJE (SELF-HOSTING)

El compilador de Synapse ha alcanzado la madurez del auto-hospedaje completo mediante un proceso determinista de tres etapas.

### 14.1. Pipeline de Compilación en Cascada

1. **Stage 1:** El compilador inicial (escrito en Python/C) compila el código fuente del compilador de Synapse escrito en el propio lenguaje (`nucleo/*.syn`).
2. **Stage 2:** El binario resultante del Stage 1 recompila nuevamente el código fuente del compilador para generar el Stage 2.
3. **Stage 3:** El binario del Stage 2 recompila el código fuente para generar el Stage 3.
4. **Verificación de Identidad (Bitwise Comparison):** Se realiza una validación binaria estricta (`diff` de 0 bytes) entre el Stage 2 y el Stage 3. La igualdad absoluta de los binarios certifica que el compilador es completamente autónomo, determinista y libre de dependencias de bootstrapping externas.

---

## 15. GUÍAS DE CONTRIBUCIÓN Y REGLAS DE INGENIERÍA

Cualquier contribución al código fuente de Synapse debe adherirse de manera estricta a los siguientes cánones de desarrollo:

### 15.1. Normas de Estilo y Sintaxis

* **Indentación:** Uso obligatorio de 4 espacios por nivel de indentación. Quedan terminantemente prohibidos los caracteres de tabulación (`\t`). El lexer rechazará cualquier archivo que los contenga.
* **Limpieza de Código:** Cero tolerancia al código muerto, variables no utilizadas o advertencias de compilación GCC/Clang (`-Wall -Wextra -Werror`).

### 15.2. Filosofía de Seguridad y Privacidad

* **Cero Telemetría:** Los binarios compilados y las herramientas del ecosistema no realizan ninguna conexión en red oculta, recolección de datos de uso ni analíticas. La soberanía del entorno del usuario es inviolable.
* **Opt-in de IA:** Las capacidades de asistencia local mediante OpenSyn y `llama.cpp` operan bajo un estricto principio de activación voluntaria (*opt-in*), ejecutándose exclusivamente de manera local sin exportar contexto fuera del hardware del usuario.

## 16. ARQUITECTURA DEL TOOLCHAIN Y CLI (`synapse` CLI)

El acceso a las capacidades del compilador, gestor de paquetes y entorno de desarrollo se centraliza a través de la herramienta de línea de comandos (`synapse`), diseñada para proporcionar una experiencia uniforme y determinista en cualquier sistema operativo.

### 16.1. Comandos Principales del CLI

* `synapse build [archivo.syn]`
* Ejecuta el pipeline completo: lexer, parser, análisis semántico de tres pasadas, verificación de Ownership, traducción a C y compilación nativa a través de GCC/Clang con optimización `-O2`. Genera un binario ejecutable optimizado.


* `synapse run [archivo.syn]`
* Compila de forma temporal el archivo fuente y ejecuta el binario resultante en la misma sesión, capturando la salida estándar (`stdout`) y los códigos de error.


* `synapse test`
* Ejecuta la suite de pruebas unitarias y de integración del proyecto actual, aplicando sanitizadores de memoria y validando contratos lógicos.


* `synapse migrate [archivo.py]`
* Invoca el transpilador estricto basado en AST para proyectar código fuente legacy de Python hacia el formato canónico `.syn.json` y generar la estructura base en Synapse.


* `synapse fetch`
* Comando ejecutado por el gestor Axon para resolver dependencias, validar firmas criptográficas Ed25519 y descargar fuentes bloqueadas en `axon.lock`.



---

## 17. INTEROPERABILIDAD Y FFI (FOREIGN FUNCTION INTERFACE)

Para garantizar que Synapse pueda integrarse con sistemas heredados de alto rendimiento sin perder el control estricto de la memoria, se implementa una interfaz de función extranjera (FFI) nativa con C.

### 17.1. Declaración de Funciones Externas (`extern`)

* Las funciones escritas en bibliotecas de C externas se declaran explícitamente utilizando la palabra clave `extern`, indicando los tipos estrictos de los parámetros y el valor de retorno.
* **Regla de Seguridad:** Las llamadas a funciones FFI externas se consideran bloques de código no verificado (*unsafe* por definición semántica), por lo que el compilador exige que su encapsulamiento esté delimitado bajo contratos lógicos explícitos (`requiere`/`garantiza`) para evitar la propagación de desbordamientos de búfer hacia el runtime seguro de Synapse.

---

## 18. TAXONOMÍA DE ERRORES DEL COMPILADOR

Para asegurar la depuración rápida y la trazabilidad absoluta ante fallos de compilación, el compilador emite códigos de error estructurados y deterministas.

### 18.1. Catálogo de Errores Críticos

* **Errores Léxicos (`ERR_LEX_*`):**
* `ERR_LEX_MISSING_LANG`: Ausencia de la directiva obligatoria `#lang:` en la línea 1 del archivo fuente.
* `ERR_LEX_TAB_DETECTED`: Uso de caracteres de tabulación (`\t`) en lugar de múltiplos estrictos de 4 espacios.


* **Errores Semánticos y de Posesión (`ERR_SEM_*` / `ERR_MEM_*`):**
* `ERR_SEM_TYPE_AMBIGUOUS`: Ambigüedad en la inferencia estática de tipos durante la Pasada 3.
* `ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED`: Falta de cobertura exhaustiva en una sentencia `coincidir` sobre tipos algebraicos (`Resultado` u `Opcion`).
* `ERR_MEM_USE_AFTER_MOVE`: Intento de acceso a una variable cuyo *ownership* fue transferido previamente (*Use-After-Move*).


* **Errores de Contrato (`ERR_CTR_*`):**
* `ERR_CTR_PRECONDITION_FAILED`: Violación de una cláusula `requiere` detectada por las aserciones de metal en tiempo de ejecución.



---

## 19. INGENIERÍA DE RELEASE Y DISTRIBUCIÓN BINARIA

La liberación de versiones estables de Synapse se rige por un proceso de empaquetado inmutable y verificado criptográficamente.

### 19.1. Canal de Construcción y Firma (CI/CD Matrix)

1. **Matriz Multi-Plataforma:** GitHub Actions compila de manera paralela los binarios del compilador (`synapse`) y del demonio LSP (`synapse_lsp`) para `linux_x86_64`, `linux_arm64`, `darwin_arm64` y `windows_x64`.
2. **Sellado Criptográfico:** Cada artefacto compilado pasa por un proceso automático de generación de huellas digitales SHA-256 y firma digital Ed25519, garantizando que el instalador maestro y las extensiones VSIX de VS Code distribuidas públicamente estén libres de alteraciones en la cadena de suministro.

## 20. ANEXO: DIAGRAMA DE FLUJO DEL COMPILADOR Y CHECKLIST DE INTEGRACIÓN

Para garantizar una referencia visual e interactiva del flujo de transformación del código en todo el ecosistema de Synapse, se especifica el mapa de tubería de compilación end-to-end y la lista de comprobación de ingeniería para la entrega de código.

### 20.1. Flujo End-to-End de Compilación

```text
[ Código Fuente (.syn) ]
         │
         ▼
[ Lexer (lexer.syn) ] ──(Filtro #lang, Control 4 espacios, IndentStack)──► [ Flujo de Tokens ]
         │
         ▼
[ Parser (parser.syn) ] ──(Descenso Recursivo, Gramática EBNF)────────────► [ AST Canónico (.syn.json) ]
         │
         ▼
[ Analizador Semántico ] ──(3 Pasadas: Estructuras → Firmas → Ownership)─► [ AST Validado + Tipos ]
         │
         ▼
[ Generador C (generator.syn) ] ──(Emisión C99/C11, -O2, SIMD, RAII)─────► [ Código C Intermedio ]
         │
         ▼
[ Toolchain GCC / Clang ] ──(Linker, -lpthread, -lws2_32)────────────────► [ Binario Nativo (.exe / ELF) ]

```

---

### 20.2. Checklist de Verificación de Calidad (Definition of Done)

Para considerar cualquier nuevo módulo, característica o refactorización del compilador como **completada y lista para producción**, el código debe superar los siguientes controles innegociables:

1. **Cumplimiento Léxico y Sintáctico:**
* Archivo encabezado con la directiva obligatoria `#lang: es`.
* Indentación estricta a 4 espacios sin un solo caracter de tabulación (`\t`).


2. **Verificación de Seguridad de Memoria:**
* Cero uso de `malloc`/`free` manual en código usuario.
* Superación de análisis semántico contra *Use-After-Move* sin advertencias.
* Ausencia de fugas de memoria o accesos inválidos verificados mediante `AddressSanitizer` (`-fsanitize=address,undefined`).


3. **Concurrencia e Integración:**
* Cero variables globales mutables compartidas entre hilos.
* Comunicación aislada mediante canales tipados (`Canal<T>`).


4. **Validación de la Suite de Pruebas:**
* Aprobación del 100% de los 317+ tests unitarios, de integración y fuzzing sin regresiones.
* En caso de modificaciones en el compilador base, verificación de bootstrapped determinista (`diff 0 bytes` entre Stage 2 y Stage 3).


5. **Seguridad en la Cadena de Suministro:**
* Generación automática de hash SHA-256.
* Validación de firma criptográfica **Ed25519** en el pipeline de CI/CD para la distribución en Axon Hub.



---

## 21. FIRMA Y CERTIFICACIÓN TÉCNICA

El **Manual de Ingeniería y Desarrollo de Synapse (v3.0)** queda formalmente consolidado como el documento maestro de especificación técnica del proyecto. Todas las contribuciones, refactorizaciones y desarrollos del compilador, la biblioteca estándar, el LSP, la IA local (OpenSyn) y el gestor de paquetes (Axon) deben alinearse estrictamente con los parámetros aquí expuestos.

```text
================================================================================
  DOCUMENTO OFICIAL DE ARQUITECTURA E INGENIERÍA — SYNAPSE / OPENSYN v3.0
  Estado: APROBADO Y SELLADO
  Principios Rectores: "El Pacto" | Tipado Estricto Inferido | Zero-GC | Soberanía
================================================================================

```