# MANUAL 1: VISIÓN GENERAL, FILOSOFÍA Y ARQUITECTURA DEL ECOSISTEMA

**Archivo:** `01_VISION_Y_ARQUITECTURA.md`  
**Versión:** 8.0.0-industrial  
**Propósito:** Establecer los fundamentos conceptuales, los principios rectores y la arquitectura de alto nivel del ecosistema completo Synapse + Syquex + OpenSyn, definiendo el alcance del proyecto y su hoja de ruta evolutiva.

---

## 1. INTRODUCCIÓN Y VISIÓN GENERAL

### 1.1. ¿Qué es el Ecosistema Synapse?

El ecosistema Synapse es una **plataforma de desarrollo de software completa y unificada** que abarca desde el metal desnudo hasta la capa de aplicación, integrando tres componentes fundamentales que funcionan en perfecta armonía:

| Componente | Nivel | Propósito | Analogía |
|------------|-------|-----------|----------|
| **Synapse** | Bajo / Sistemas | Lenguaje de sistemas, control total de memoria, rendimiento extremo | "El motor" |
| **Syquex** | Alto / Productividad | Lenguaje de scripting, aplicaciones, GUI, web, prototipado | "La carrocería" |
| **OpenSyn** | IA / Asistencia | Asistente de IA local, generación de código, explicaciones, transpilación | "El copiloto" |

**Synapse** es el lenguaje de programación nativo, compilado y de grado de sistemas que sirve como cimiento para sistemas operativos, motores de bases de datos, infraestructura de red y aplicaciones Edge AI. Opera sin recolector de basura, sin dependencias opacas y sin telemetría forzada.

**Syquex** es el lenguaje de alto nivel hermano de Synapse, diseñado para la productividad del desarrollador: scripting, aplicaciones de escritorio, backends web, frontend (via WASM), prototipado rápido y automatización. Ofrece una sintaxis limpia y natural, gestión de memoria automática sin GC (basada en arenas y análisis de alcance), y una biblioteca estándar «baterías incluidas».

**OpenSyn** es el asistente de inteligencia artificial local del ecosistema. Actúa como un compañero de programación inteligente que corre íntegramente en la máquina del desarrollador, sin depender de servicios en la nube. OpenSyn:
- Se ejecuta en la terminal de VS Code (o cualquier editor que soporte LSP).
- Utiliza modelos de lenguaje especializados en código (codec), descargados y optimizados localmente.
- Es capaz de **aprender Synapse y Syquex**, y también domina otros lenguajes (Python, JavaScript, C, C++, Rust, etc.).
- Proporciona explicaciones de código, generación automática, autocompletado contextual, refactorización asistida y corrección de errores.
- Al instalarse, detecta automáticamente los recursos de hardware (RAM, VRAM, CPU) y selecciona el modelo codec más adecuado.
- Puede instalarse como un complemento opcional junto con Synapse y Syquex.

### 1.2. Público Objetivo

**Synapse** está dirigido a:
- Ingenieros de sistemas y desarrolladores de kernels.
- Arquitectos de infraestructura que requieren máximo rendimiento y control.
- Equipos de Edge AI y sistemas embebidos.
- Desarrolladores que buscan un lenguaje productivo pero con garantías de memoria y concurrencia.

**Syquex** está dirigido a:
- Desarrolladores que buscan productividad similar a Python pero con mejor rendimiento.
- Equipos que necesitan construir aplicaciones completas (web, escritorio, CLI) con un solo lenguaje.
- Desarrolladores que quieren aprovechar Synapse para el núcleo pesado sin salir del ecosistema.
- Comunidad hispanohablante (sintaxis multilingüe).

**OpenSyn** está dirigido a:
- Programadores de todos los niveles que deseen acelerar su flujo de trabajo con asistencia inteligente local.
- Equipos que quieran mantener su código y datos privados, sin depender de la nube.
- Educadores y estudiantes que quieran aprender Synapse o Syquex de forma interactiva.

---

## 2. LOS PILARES DEL ECOSISTEMA (El Pacto Extendido)

El ecosistema Synapse se rige por un conjunto de principios que denominamos **«El Pacto»**. Estos son innegociables y deben ser respetados por el compilador, el runtime y toda la cadena de herramientas. Se aplican a Synapse, Syquex y OpenSyn en la medida que corresponde.

| Principio | Synapse | Syquex | OpenSyn | Implementación |
|-----------|---------|--------|---------|----------------|
| **Rendimiento Nativo** | Compilación a C/LLVM | Compilación a C/LLVM | Inferencia local optimizada | Backend compartido (GCC/Clang/LLVM/emcc) |
| **Seguridad de Memoria** | Ownership + Borrowing | Arenas + RC + Análisis de alcance | N/A (aplicación) | Modelo de memoria determinista sin GC |
| **Cero Telemetría** | ✅ | ✅ | ✅ | Sin conexiones en red ocultas, sin recolección de datos |
| **Cero Dependencias** | Binario monolítico | Binario monolítico | Modelos descargables | `synapse.exe` autocontenido |
| **Multilingüe** | `#lang: es/en/fr/pt` | `#lang: es/en/fr/pt` | Respuestas en el idioma del usuario | Diccionario de tokens universales (AST canónico) |
| **Reproducibilidad** | SHA-256 + diff 0 bytes | Heredado de Synapse | N/A | `axon.lock` + bootstrap de 3 etapas |
| **Verificación Formal** | ATP + Proof Bridge | Heredado de Synapse | N/A | Motor ATP integrado, exportación a Coq/Lean |
| **Tipado Estricto Inferido** | Hindley-Milner | Hindley-Milner | N/A | Unificación con occurs check |
| **Algebraic Error Handling** | `Resultado<T,E>`, `Opcion<T>` | `Resultado<T,E>`, `Opcion<T>` | N/A | Exhaustividad de match en tiempo de compilación |
| **Soberanía del Usuario** | ✅ | ✅ | ✅ | El usuario controla todos los datos y procesos locales |

---

## 3. ARQUITECTURA DEL COMPILADOR UNIFICADO

### 3.1. El Pipeline de Compilación

El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CÓDIGO FUENTE                                  │
├─────────────────────┬───────────────────────┬─────────────────────┤
│   .syn (Synapse)    │    .syq (Syquex)      │   Prompt (Natural)  │
└──────────┬──────────┴───────────┬───────────┴──────────┬──────────┘
           │                      │                       │
           ▼                      ▼                       ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────┐
│  Lexer (synapse)    │ │  Lexer (syquex)     │ │  OpenSyn        │
│  Tokens específicos  │ │  Tokens específicos  │ │  (Procesamiento │
│  de bajo nivel       │ │  de alto nivel      │ │  de lenguaje)   │
└──────────┬──────────┘ └──────────┬──────────┘ └────────┬────────┘
           │                      │                       │
           ▼                      ▼                       ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────┐
│  Parser (synapse)   │ │  Parser (syquex)    │ │  Generación     │
│  AST bajo nivel     │ │  AST alto nivel     │ │  de código      │
└──────────┬──────────┘ └──────────┬──────────┘ └────────┬────────┘
           │                      │                       │
           └──────────┬───────────┘                       │
                      ▼                                   │
           ┌─────────────────────────────┐                │
           │  TRADUCTOR (traductor.syq)  │                │
           │  Mapea AST de Syquex a      │                │
           │  SemNodo[] de Synapse       │                │
           └──────────────┬──────────────┘                │
                      │                                   │
                      ▼                                   │
           ┌─────────────────────────────┐                │
           │  ANALIZADOR SEMÁNTICO       │                │
           │  (Compartido)               │                │
           │  - Tabla de símbolos        │                │
           │  - Hindley-Milner           │                │
           │  - Ownership / Borrowing    │                │
           │  - Análisis de alcance      │                │
           │  - ATP (--safe)             │                │
           └──────────────┬──────────────┘                │
                      │                                   │
                      ▼                                   │
           ┌─────────────────────────────┐                │
           │  GENERADOR (Compartido)     │                │
           │  - C / LLVM IR              │                │
           │  - WASM                     │                │
           │  - Inserción de liberación  │                │
           └──────────────┬──────────────┘                │
                      │                                   │
                      ▼                                   │
           ┌─────────────────────────────┐                │
           │  BACKEND                     │                │
           │  - GCC/Clang para binarios   │◄───────────────┘
           │  - emcc para WASM           │
           └─────────────────────────────┘
```

### 3.2. Componentes del Compilador

**1. Lexer (`lexer.syn` / `lexer.syq`):**
- Lee caracteres e inyecta tokens de indentación (INDENT/DEDENT).
- Detecta la directiva `#lang:` y selecciona el diccionario multi-idioma.
- Salida: flujo de tokens (TokenID + valor + ubicación).

**2. Parser (`parser.syn` / `parser.syq`):**
- Descenso recursivo puro sin backtracking.
- Construye el AST (Árbol de Sintaxis Abstracta) como una lista enlazada.
- Salida: AST enlazado.

**3. Traductor de Syquex (`traductor.syq`):**
- Convierte el AST de Syquex (alto nivel) al AST canónico `SemNodo[]` de Synapse.
- Preserva la metadata de depuración (archivo, línea, columna originales).
- Permite que Syquex herede todo el backend de Synapse sin duplicación.

**4. Analizador Semántico (Compartido):**
- **Pasada 1:** Registro de estructuras y tipos globales.
- **Pasada 2:** Registro de firmas de funciones.
- **Pasada 3:** Análisis de cuerpos de funciones, inferencia de tipos (Hindley-Milner), verificación de ownership/borrowing, análisis de alcance (para Syquex), y motor ATP (modo `--safe`).
- **Salida:** AST anotado con tipos y tabla de símbolos.

**5. Generador (Compartido):**
- Traduce el AST validado a código intermedio: C (C99/C11), LLVM IR o WAT (WASM).
- Emite funciones en orden alfabético (determinismo).
- Inyecta contratos como aserciones o `llvm.assume`.
- Inserta liberaciones de memoria (RAII, Cleanup Blocks).
- Salida: `synapse_unity.c`, `.ll` o `.wat`.

**6. Backend:**
- **C:** GCC/Clang con flags de optimización (PGO, LTO, sanitizadores).
- **LLVM:** Generación de IR, optimización y JIT.
- **WASM:** `emcc` para generar WebAssembly.
- **Enlace:** Runtime modular (memory, concurrency, io, net, quantum, ml, federated).

---

## 4. ESTRUCTURA DEL REPOSITORIO (Monorepo)

El repositorio está organizado de manera modular para desacoplar el compilador, el runtime, el gestor de paquetes, el LSP, OpenSyn y los dos lenguajes.

```
/synapse/
│
├── .github/                         # Pipelines de CI/CD (matriz multi‑arquitectura, firmas Ed25519)
│   └── workflows/
│       ├── release_matrix.yml       # Compila para Windows, Linux, macOS, WASM
│       ├── vscode_publish.yml       # Publica la extensión VS Code
│       └── test.yml                 # Ejecuta tests en cada push
│
├── nucleo/                          # Núcleo de Synapse (bajo nivel)
│   ├── lexer.syn                    # Tokenizador e inyector de indentación
│   ├── parser.syn                   # Parser de descenso recursivo
│   ├── ast_nodes.syn                # Definición del AST (SemNodo[]) ABI v1
│   ├── analizador_semantico.syn     # Motor de tipado, ownership y ATP
│   ├── generator.syn                # Emisor de código C optimizado
│   ├── llvm_backend.syn             # Backend LLVM (IR, JIT)
│   ├── wasm_backend.syn             # Backend WebAssembly (WAT)
│   ├── verificador_formal.syn       # Motor ATP y exportación a Coq/Lean
│   ├── lifetimes.syn                # Análisis de tiempos de vida
│   ├── cache.syn                    # Sistema de caché incremental SHA‑256
│   ├── principal.syn                # Punto de entrada del compilador
│   ├── lsp.syn                      # Servidor LSP nativo
│   ├── tokens.syn                   # Definiciones de TokenID y diccionarios
│   ├── errores.syn                  # Taxonomía de errores
│   ├── ast_abi.syn                  # ABI estable del AST (NUEVO)
│   ├── ai_orchestrator.c            # Orquestación de llama-server (C)
│   ├── llama_client.c               # Cliente HTTP nativo para OpenSyn
│   ├── synapse_rag.c                # Pipeline RAG quirúrgico
│   ├── detect_hardware.c            # Detección de RAM, VRAM, CPU
│   ├── fine_tuning.c                # Fine‑tuning LoRA
│   ├── quantization.c               # Cuantización de modelos
│   ├── distillation.c               # Destilación de conocimiento (KD)
│   ├── federated.c                  # FedAvg y orquestación distribuida
│   ├── quantum_runtime.c            # Simulación cuántica
│   ├── proof_bridge.c               # Exportación a Coq/Lean
│   └── ...
│
├── syquex/                          # Frontend de Syquex (alto nivel)
│   ├── lexer.syq                    # Tokenizador de Syquex
│   ├── parser.syq                   # Parser de descenso recursivo
│   ├── traductor.syq                # Mapeo a SemNodo[] de Synapse
│   ├── analizador_alcance.syq       # CFG + Cleanup Blocks (NUEVO)
│   ├── ffi_marshaling.syq           # Marshaling para C (NUEVO)
│   ├── arena_componente.syq         # Arenas de componente (NUEVO)
│   ├── builtins.syq                 # Funciones integradas de Syquex
│   └── syquex.syn                   # Compilador de Syquex (escrito en Synapse)
│
├── std/                             # Librería estándar de Synapse
│   ├── io.syn                       # Entrada/salida básica
│   ├── math.syn                     # Matemáticas y tensores
│   ├── net.syn                      # Redes (TCP, HTTP)
│   ├── concurrencia.syn             # Canales, fibras
│   ├── cluster.syn                  # Concurrencia distribuida
│   ├── debug.syn                    # Depuración time‑travel
│   ├── os.syn                       # Sistema operativo (detección HW)
│   ├── federated.syn                # Aprendizaje federado
│   ├── quantum.syn                  # Computación cuántica
│   └── modelo.syn                   # Modelos de IA (GGUF)
│
├── lib/                             # Librería estándar de Syquex
│   ├── io.syq                       # Entrada/salida
│   ├── math.syq                     # Matemáticas y estadísticas
│   ├── texto.syq                    # Manipulación de cadenas
│   ├── lista.syq                    # Operaciones con listas
│   ├── mapa.syq                     # Mapas/diccionarios
│   ├── json.syq                     # Serialización JSON (cJSON)
│   ├── web.syq                      # Servidor HTTP (libmicrohttpd)
│   ├── gui.syq                      # Bindings a GTK (NUEVO)
│   ├── dom.syq                      # Manipulación del DOM (NUEVO)
│   ├── db.syq                       # SQLite, PostgreSQL (FFI)
│   ├── tiempo.syq                   # Fechas y tiempos
│   ├── pruebas.syq                  # Framework de testing
│   ├── ia.syq                       # Integración con OpenSyn
│   └── ffi.syq                      # Marshaling automático (NUEVO)
│
├── runtime/                         # Runtime compartido (C)
│   ├── core/
│   │   ├── memory.c                 # Pool allocator + TLC + Arena
│   │   ├── concurrency.c            # Canales, fibras, mutexes
│   │   └── io.c                     # File I/O, sockets
│   ├── net/
│   │   └── http.c                   # Cliente/servidor HTTP
│   ├── quantum/
│   │   └── matrix.c                 # Simulación cuántica
│   ├── ml/
│   │   └── gguf.c                   # Carga de modelos GGUF
│   └── federated/
│       └── aggregator.c             # Algoritmos FedAvg
│
├── opensyn/                         # Asistente IA (compartido)
│   ├── orchestrator.c               # Ciclo de vida de llama-server
│   ├── llama_client.c               # Cliente HTTP para inferencia
│   ├── synapse_rag.c                # Pipeline RAG quirúrgico
│   ├── router.syn                   # Enrutador de peticiones
│   ├── installer.syn                # Instalador de OpenSyn
│   └── transpiler.syn               # Transpilación Python→Syquex (NUEVO)
│
├── axon/                            # Gestor de paquetes (C)
│   ├── axon_rt.c                    # Runtime de Axon (Ed25519, TAR, HTTP, TOML, SemVer)
│   └── tweetnacl.c                  # Implementación de Ed25519
│
├── vscode-synapse/                  # Extensión VS Code (TypeScript)
│   ├── package.json
│   ├── extension.js                 # Cliente LSP y comandos
│   ├── snippets/                    # Snippets de código
│   └── syntaxes/                    # Definición de sintaxis
│
├── tests/                           # Suites de pruebas
│   ├── unit/                        # Tests unitarios (Python)
│   ├── integration/                 # Tests de integración (Python)
│   ├── fuzz/                        # Fuzzing destructivo (7 estrategias)
│   ├── stress/                      # Pruebas de estrés
│   ├── micro_bootstrap/             # Tests del proceso de bootstrap
│   ├── syquex/                      # Tests de Syquex (NUEVO)
│   └── validate_*.c                 # Tests nativos en C
│
├── docs/                            # Documentación del ecosistema
│   ├── 01_VISION_Y_ARQUITECTURA.md
│   ├── 02_SINTAXIS_SYNAPSE.md
│   ├── 03_SINTAXIS_SYQUEX.md
│   ├── 04_MODELO_MEMORIA_SYQUEX.md
│   ├── 05_CONCURRENCIA.md
│   ├── 06_INTEGRACION_ECOSISTEMA.md
│   ├── 07_OPENSYN_ASISTENTE.md
│   ├── 08_HERRAMIENTAS_DESARROLLO.md
│   └── 09_INSTALACION_Y_DISTRIBUCION.md
│
├── examples/                        # Ejemplos de código
│   ├── synapse/                     # Ejemplos de Synapse
│   │   ├── 01_basico.syn
│   │   ├── 02_estructuras.syn
│   │   └── 03_tensores_ia.syn
│   └── syquex/                      # Ejemplos de Syquex
│       ├── 01_basico.syq
│       ├── 02_web.syq
│       └── 03_gui.syq
│
├── build/                           # Directorio de salida de builds (generado)
├── synapse.exe                      # Binario final (generado)
├── README.md                        # Manifiesto del proyecto
├── LICENSE                          # MIT
└── .gitignore
```

---

## 5. FILOSOFÍA DE DISEÑO

### 5.1. Legibilidad Absoluta (El espíritu de Python)
El código debe leerse casi como un lenguaje natural estructurado. Synapse y Syquex eliminan la «basura visual» (llaves, paréntesis redundantes y símbolos esotéricos). Utilizan **indentación estricta** (4 espacios) para definir bloques lógicos, obligando a crear un código limpio y estandarizado por defecto.

### 5.2. Rendimiento de Metal Desnudo (El motor de C/C++)
La simplicidad visual no debe costar milisegundos. Synapse y Syquex no se interpretan; se **compilan directamente a código máquina** optimizado (via C/LLVM). Se ejecutan tan cerca del hardware que son ideales para desarrollar desde inteligencia artificial hasta sistemas operativos completos.

### 5.3. Seguridad Inteligente (El escudo de Rust, sin el dolor)
Synapse introduce un **compilador predictivo** que usa análisis estático avanzado para inferir el tiempo de vida de las variables y gestionar la memoria automáticamente en tiempo de compilación (ownership + borrowing). Syquex hereda esta seguridad mediante **análisis de alcance** + **arenas** + **conteo de referencias**, eliminando la necesidad de un GC.

### 5.4. Concurrencia Orgánica (El flujo de Go)
El hardware moderno tiene múltiples núcleos, pero programar hilos sigue siendo un dolor de cabeza. Synapse y Syquex ofrecen concurrencia **nativa** mediante **fibras** (procesos ultraligeros) que se comunican a través de **canales tipados** (`Canal<T>`), permitiendo ejecutar miles de tareas en paralelo con una sola palabra clave (`lanzar` o `spawn`).

### 5.5. IA como Ciudadano de Primera Clase
Los lenguajes antiguos fueron creados antes de la revolución de la inteligencia artificial. Synapse incluye **tensores nativos** y soporte para modelos GGUF, tratándolos como tipos de datos primitivos. OpenSyn proporciona asistencia de IA local integrada, sin dependencia de la nube.

### 5.6. Multilingüismo Natural
La programación ha estado secuestrada por el inglés técnico desde los años 50. Synapse y Syquex eliminan esa barrera mediante **diccionarios de tokens universales** y la directiva `#lang:`. Los desarrolladores pueden escribir código en español, inglés, francés, portugués, etc., y el compilador lo procesa de forma idéntica.

### 5.7. Cero Telemetría y Soberanía del Usuario
Los binarios compilados y las herramientas del ecosistema no realizan ninguna conexión en red oculta, recolección de datos de uso ni analíticas. La soberanía del entorno del usuario es inviolable. Las capacidades de IA mediante OpenSyn operan bajo un estricto principio de activación voluntaria (*opt-in*), ejecutándose exclusivamente de manera local sin exportar contexto fuera del hardware del usuario.

---

## 6. HOJA DE RUTA TÉCNICA (Resumen de Evolución)

La evolución del ecosistema sigue una hoja de ruta clara, documentada en el ROADMAP.md:

| Fase | Versión | Entregable clave |
|------|---------|------------------|
| **Fundación** | v1.x | Compilador en Python, sintaxis básica, bootstrap manual. |
| **Auto‑hospedaje** | v2.x | Compilador nativo en Synapse (`nucleo/*.syn`). Fin de la dependencia Python para producción. |
| **Concurrencia y Seguridad** | v3.x | Ownership completo, canales `Canal<T>`, contratos `requiere`/`garantiza`. |
| **Ecosistema** | v4.x | Axon (Ed25519), LSP nativo, integración VS Code, Edge AI (Ollama). |
| **Revolución Cognitiva + Certificación Industrial** | v5.1.1‑industrial | Caché incremental SHA‑256, Time‑Travel Debugging, Sandbox (`seccomp`), LLVM Backend (IR/JIT), WASM, Axon Hub (IPFS), IA Nativa (`llama.cpp`), Motor ATP y Verificación Formal, Aprendizendo Federado (`std::federated`), Simulación Cuántica (`std::quantum`), Runtime modularizado, Asignador con TLC. |
| **Frontend de Productividad (Syquex)** | v6.0 | Lenguaje de alto nivel con arenas, análisis de alcance, biblioteca estándar (web, GUI, DB), WASM para frontend. |
| **Asistente IA Universal (OpenSyn)** | v7.0 | OpenSyn como asistente multilenguaje (Synapse, Syquex, Python, JS, etc.), transpilación, generación automática de bindings C, instalación unificada. |

**Regla de hierro:** Ninguna característica nueva puede romper el *bootstrap* (etapas 0→1→2→3 con diff binario 0). El determinismo se verifica obligatoriamente en la CI mediante la comparación de los hashes SHA‑256 de las etapas 2 y 3.

---

## 7. GUÍAS DE CONTRIBUCIÓN Y ESTÁNDARES DE CALIDAD

### 7.1. Estilo de Código

- **Indentación:** 4 espacios, prohibido el uso de tabuladores (`\t`).
- **Comentarios:** `//` para línea y `/* */` para bloque.
- **Nombres:** en español para el código fuente de Synapse y Syquex; en inglés para el código C del runtime (por convención).
- **Orden alfabético:** todas las funciones globales, estructuras y variables estáticas deben emitirse en orden alfabético en el archivo C generado.

### 7.2. Pruebas

Todo cambio debe pasar la suite completa de pruebas:

- `pytest tests/unit/` (184+ tests).
- `pytest tests/integration/` (17 archivos).
- Ejecución de los tests nativos en C (`validate_*.c`).
- Fuzzing destructivo (`tests/fuzz/fuzz_engine.py` con 500+ iteraciones, 0 crashes).
- Pruebas de estrés de concurrencia y memoria.

### 7.3. Seguridad y Privacidad

- **Cero telemetría:** ningún binario realiza conexiones en red ocultas.
- **Opt‑in de IA:** OpenSyn solo se activa explícitamente; nunca envía datos fuera del equipo.
- **Firma criptográfica:** todos los artefactos distribuidos deben estar firmados con Ed25519.
- **Reporte de vulnerabilidades:** `seguridad@synapse-lang.org` (PGP cifrado).

### 7.4. Definition of Done (Checklist de Calidad)

Para considerar cualquier nuevo módulo, característica o refactorización como **completada y lista para producción**, el código debe superar los siguientes controles innegociables:

1. **Cumplimiento Léxico y Sintáctico:**
   - Archivo encabezado con la directiva obligatoria `#lang: es` (o el idioma correspondiente).
   - Indentación estricta a 4 espacios sin un solo caracter de tabulación (`\t`).

2. **Verificación de Seguridad de Memoria:**
   - Cero uso de `malloc`/`free` manual en código de usuario (Synapse y Syquex).
   - Superación de análisis semántico contra *Use-After-Move* sin advertencias.
   - Ausencia de fugas de memoria o accesos inválidos verificados mediante `AddressSanitizer` (`-fsanitize=address,undefined`).

3. **Concurrencia e Integración:**
   - Cero variables globales mutables compartidas entre hilos.
   - Comunicación aislada mediante canales tipados (`Canal<T>`).

4. **Validación de la Suite de Pruebas:**
   - Aprobación del 100% de los tests unitarios, de integración y fuzzing sin regresiones.
   - En caso de modificaciones en el compilador base, verificación de bootstrapped determinista (`diff 0 bytes` entre Stage 2 y Stage 3).

5. **Seguridad en la Cadena de Suministro:**
   - Generación automática de hash SHA‑256.
   - Validación de firma criptográfica **Ed25519** en el pipeline de CI/CD para la distribución en Axon Hub.

6. **Documentación:**
   - Actualización de los manuales correspondientes.
   - Ejemplos de uso en la carpeta `examples/`.

---

## 8. DIAGRAMA DE FLUJO END‑TO‑END

El siguiente diagrama ilustra el flujo completo desde el código fuente hasta el binario ejecutable, incluyendo la interacción con OpenSyn:

```
[ Código Fuente (.syn / .syq) ]
         │
         ▼
[ Lexer (lexer.syn / lexer.syq) ] ──(Filtro #lang, Control 4 espacios, IndentStack)──► [ Flujo de Tokens ]
         │
         ▼
[ Parser (parser.syn / parser.syq) ] ──(Descenso Recursivo, Gramática EBNF)────────────► [ AST (Alto nivel para Syquex / Bajo nivel para Synapse) ]
         │
         ▼
[ Traductor (traductor.syq) ] ──(Solo para Syquex: mapeo a SemNodo[] de Synapse)─────► [ AST Canónico Unificado ]
         │
         ▼
[ Analizador Semántico ] ──(3 Pasadas: Estructuras → Firmas → Cuerpos + Ownership + Lifetimes + ATP + Análisis de alcance)─► [ AST Validado + Tipos + Contratos ]
         │
         ▼
[ Generador ] ──(Emisión C99/C11, -O2, SIMD, RAII, Cleanup Blocks, Pool Alloc)─────► [ Código C Intermedio / LLVM IR / WAT ]
         │
         ▼
[ Backend GCC/Clang/LLVM/emcc ] ──(Linker, -lpthread, -lws2_32)─────────────────────► [ Binario Nativo (.exe / ELF) / WASM ]
         │
         ▼
[ Ejecución ]  →  [ Si OpenSyn activo, se comunica con llama-server y el LSP para asistencia ]
```

---

## 9. SIGUIENTES PASOS

Este manual sienta las bases conceptuales y arquitectónicas del ecosistema Synapse + Syquex + OpenSyn. El siguiente manual (Manual 2) se adentrará en los detalles del compilador de Synapse: su sintaxis, semántica, lexer, parser y AST.

---

*Este documento es la piedra angular del proyecto. Todas las contribuciones, refactorizaciones y desarrollos deben alinearse con los principios aquí expuestos.*

**Fin del Manual 1**