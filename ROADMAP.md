# ROADMAP DE IMPLEMENTACIÓN DEL ECOSISTEMA SYNAPSE + SYQUEX + OPENSYN

**Versión:** 8.1.0-industrial  
**Fecha:** 2026-08-03  
**Propósito:** Guía de ejecución definitiva para la implementación completa del ecosistema desde cero. Este documento describe todas las fases, hitos, entregables, dependencias, riesgos y criterios de aceptación necesarios para construir Synapse, Syquex y OpenSyn como una plataforma unificada. No contiene marcas de estado previo, ya que está diseñado para iniciar desde una carpeta vacía.

---

## LEYENDA DE ESTRUCTURA

Cada fase se describe con los siguientes campos:

- **Objetivo:** Declaración clara del propósito de la fase.
- **Entregables:** Lista exhaustiva de artefactos de código, documentación y herramientas que deben generarse.
- **Criterios de Aceptación:** Condiciones que deben cumplirse para considerar la fase completada.
- **Dependencias:** Fases anteriores que deben estar completadas.
- **Riesgos y Mitigaciones:** Posibles obstáculos y estrategias para superarlos.
- **Duración Estimada:** Tiempo de trabajo requerido (expresado en meses-persona o meses-calendario para un equipo de 3-5 ingenieros).

---

## FASES 0 A 21: FUNDACIÓN Y NÚCLEO DE SYNAPSE (24 meses estimados)

Estas fases establecen el compilador de Synapse, el runtime, el sistema de tipos, la concurrencia, el gestor de paquetes Axon, el backend LLVM/WASM y el motor ATP. Constituyen la base de todo el ecosistema.

### FASE 0: SANEAMIENTO Y ESTRUCTURA INICIAL

- **Objetivo:** Preparar el entorno de desarrollo y la estructura de directorios del monorepo.
- **Entregables:**
  - Creación de la estructura de carpetas: `/nucleo/`, `/std/`, `/runtime/`, `/axon/`, `/tests/`.
  - Archivo `.gitignore` con cobertura de artefactos de build (`.exe`, `.o`, `.so`, `.dll`, `__pycache__`, etc.).
  - Archivo `LICENSE` (MIT).
  - Archivo `README.md` inicial con la descripción del proyecto.
  - Configuración de pre-commit hooks (formateo, linting básico).
  - Script de bootstrap inicial (`bootstrap.py` o `build.sh`) para compilar el compilador Stage 0 (si se usa Python como semilla).
- **Criterios de Aceptación:** El repositorio tiene la estructura definida en el Manual 1. El script de bootstrap ejecuta sin errores.
- **Dependencias:** Ninguna.
- **Riesgos y Mitigaciones:** Bajo.
- **Duración Estimada:** 1 mes.

---

### FASE 1: LEXER Y PARSER DE SYNAPSE

- **Objetivo:** Implementar el analizador léxico y el analizador sintáctico de Synapse.
- **Entregables:**
  - `nucleo/lexer.syn`: Tokenizador que soporta `#lang`, indentación (INDENT/DEDENT), comentarios, cadenas, números y operadores.
  - `nucleo/parser.syn`: Parser de descenso recursivo que construye el AST enlazado (`Nodo*`) según la gramática EBNF del Manual 2.
  - `nucleo/tokens.syn`: Definición de `TokenID` y los diccionarios multi-idioma (es, en, fr, pt).
  - `nucleo/ast_nodes.syn`: Definición de las estructuras de nodos del AST.
  - Tests unitarios para lexer y parser (`tests/unit/test_lexer.py`, `tests/unit/test_parser.py`) que cubran casos válidos e inválidos.
- **Criterios de Aceptación:** El lexer tokeniza correctamente todos los ejemplos del Manual 2. El parser construye el AST correctamente para programas válidos y reporta errores sintácticos con ubicación precisa.
- **Dependencias:** Fase 0.
- **Riesgos y Mitigaciones:** Medio. La gestión de indentación puede ser compleja; se deben implementar pruebas de estrés con diferentes niveles de anidación.
- **Duración Estimada:** 2 meses.

---

### FASE 2: TABLA DE SÍMBOLOS Y ANÁLISIS SEMÁNTICO

- **Objetivo:** Implementar la tabla de símbolos y el analizador semántico de tres pasadas.
- **Entregables:**
  - `nucleo/tabla_simbolos.syn`: Gestión de scopes anidados, declaración y búsqueda de símbolos.
  - `nucleo/analizador_semantico.syn`: Motor de análisis de 3 pasadas (Estructuras → Firmas → Cuerpos).
  - `nucleo/errores.syn`: Taxonomía de errores semánticos (ERR_SEM_*).
  - Implementación del algoritmo Hindley-Milner (unificación, occurs check) para inferencia de tipos.
  - Verificación de ownership y borrowing (use-after-move, préstamos).
  - Verificación de exhaustividad en `coincidir` para tipos algebraicos.
- **Criterios de Aceptación:** El compilador detecta variables no declaradas, tipos incompatibles, usos después de movimiento, y falta de casos en match. Todos los tests de integración de la Fase 1 siguen pasando.
- **Dependencias:** Fase 1.
- **Riesgos y Mitigaciones:** Alto. El algoritmo Hindley-Milner debe implementarse con cuidado para evitar falsos positivos. Se recomienda empezar con un subconjunto de tipos y expandir gradualmente.
- **Duración Estimada:** 4 meses.

---

### FASE 3: GENERADOR DE CÓDIGO C Y RUNTIME

- **Objetivo:** Traducir el AST validado a código C estándar y compilar el runtime básico.
- **Entregables:**
  - `nucleo/generator.syn`: Emisor de código C que recorre el AST y escribe archivos `.c`.
  - `runtime/core/memory.c`: Pool allocator básico (sin TLC todavía).
  - `runtime/core/io.c`: Funciones de entrada/salida básicas (log, lectura/escritura de archivos).
  - `runtime/core/concurrency.c`: Soporte para fibras y canales (estructuras base).
  - Inyección de RAII (liberación automática al final del scope).
  - Mapeo de tipos Synapse → C (entero → int, texto → CadenaSegura, tensor → Tensor).
- **Criterios de Aceptación:** El compilador genera un archivo `.c` compilable con GCC/Clang para programas simples. El binario resultante ejecuta `principal()` y produce la salida esperada.
- **Dependencias:** Fase 2.
- **Riesgos y Mitigaciones:** Medio. La generación de código debe manejar correctamente la recursión de estructuras. Se deben implementar pruebas con estructuras auto-referenciales.
- **Duración Estimada:** 3 meses.

---

### FASE 4: CONCURRENCIA Y CANALES

- **Objetivo:** Implementar el modelo de concurrencia (fibras y canales) en el runtime y en el generador.
- **Entregables:**
  - `runtime/core/concurrency.c`: Implementación completa de fibras (scheduler, colas), canales síncronos y asíncronos (buffer circular), mutexes, semáforos.
  - `std/concurrencia.syn`: Bindings para `lanzar`, `escuchar`, `Canal<T>`, `cerrar`.
  - Generación de código para `lanzar` (pthread_create) y `escuchar` (bucle de recepción).
  - Pruebas de estrés con 10,000 fibras concurrentes y comunicación intensiva.
- **Criterios de Aceptación:** 100% de pruebas de concurrencia pasan (sin deadlocks ni data races). El runtime soporta miles de fibras sin degradación significativa.
- **Dependencias:** Fase 3.
- **Riesgos y Mitigaciones:** Alto. La sincronización sin GC requiere cuidado extremo. Se implementará un scheduler work-stealing con pruebas de carga extensivas.
- **Duración Estimada:** 3 meses.

---

### FASE 5: CONTRATOS Y BOOTSTRAP

- **Objetivo:** Implementar contratos lógicos y completar el proceso de bootstrap (self-hosting).
- **Entregables:**
  - `nucleo/verificador_formal.syn`: Motor básico de contratos (requiere/garantiza) que genera aserciones en C.
  - Pipeline de bootstrap de 3 etapas (Stage 1: Python, Stage 2: Synapse compilando Synapse, Stage 3: Synapse compilando Synapse).
  - Verificación de determinismo: `diff` de 0 bytes entre Stage 2 y Stage 3.
- **Criterios de Aceptación:** El compilador de Synapse puede compilar su propio código fuente. El diff entre Stage 2 y Stage 3 es 0 bytes.
- **Dependencias:** Fase 4.
- **Riesgos y Mitigaciones:** Alto. Cualquier error en el generador o en el runtime rompe el bootstrap. Se requiere una suite de tests de regresión exhaustiva antes de iniciar el bootstrap.
- **Duración Estimada:** 3 meses.

---

### FASE 6: AXON (GESTOR DE PAQUETES)

- **Objetivo:** Implementar el gestor de paquetes inmutable con firma Ed25519.
- **Entregables:**
  - `axon/axon_rt.c`: Runtime de Axon (lectura de TOML, manejo de TAR, SHA-256, Ed25519 con TweetNaCl).
  - `axon/tweetnacl.c`: Implementación de criptografía Ed25519.
  - `axon/axon.toml`: Esquema de manifiesto.
  - Comandos CLI: `synapse axon init`, `fetch`, `publish`, `verify`, `search`.
  - Protección contra path traversal en extracción de TAR.
- **Criterios de Aceptación:** Los comandos de Axon funcionan correctamente. Los paquetes se firman y verifican correctamente. Los lockfiles (`axon.lock`) garantizan builds deterministas.
- **Dependencias:** Fase 5.
- **Riesgos y Mitigaciones:** Medio. La implementación de Ed25519 debe ser auditada.
- **Duración Estimada:** 3 meses.

---

### FASE 7: BACKEND LLVM Y WASM

- **Objetivo:** Extender el backend para soportar LLVM IR y WebAssembly.
- **Entregables:**
  - `nucleo/llvm_backend.syn`: Generación de IR LLVM.
  - `nucleo/wasm_backend.syn`: Generación de WAT/WASM (usando emcc o wasm-ld).
  - Comandos CLI: `synapse build --target llvm`, `synapse build --target wasm`.
  - `std/llvm.syn`, `std/wasm.syn`: Bindings básicos.
- **Criterios de Aceptación:** El compilador genera `.ll` válido que se compila con `clang`. El compilador genera `.wasm` ejecutable en navegador.
- **Dependencias:** Fase 6.
- **Riesgos y Mitigaciones:** Medio. El IR LLVM debe ser correcto para múltiples arquitecturas.
- **Duración Estimada:** 3 meses.

---

### FASES 8 A 21: MÓDULOS AVANZADOS

*Nota: Las Fases 8 a 21 cubren módulos avanzados como Concurrencia Distribuida, Time-Travel Debugging, IA Nativa, Federated Learning, Verificación Formal (ATP), Computación Cuántica, Modularización del Runtime, Optimización PGO/LTO, Caché Incremental, etc. Cada una tiene un objetivo específico, entregables, criterios de aceptación, dependencias y riesgos. Para mantener este roadmap manejable y sin ambigüedad, se detallan en el siguiente esquema resumido (pero completo).*

- **Fase 8 (Concurrencia Distribuida):** Implementar `std.cluster` con Raft, work-stealing, multicast, handshake Ed25519. **Duración:** 3 meses.
- **Fase 9 (Time-Travel Debugging):** Implementar `std.debug` y el debugger reversible con snapshots. **Duración:** 3 meses.
- **Fase 10 (Hardening Industrial):** Verificación formal ATP avanzada, SBOM SPDX y SLSA L3, fuzzing 24/7. **Duración:** 3 meses.
- **Fase 11 (Liberación y Distribución):** Release matrix (4 targets), firma Ed25519 de artefactos, marketplace, benchmarks. **Duración:** 3 meses.
- **Fase 12 (IA Nativa):** Modelo local, RAG, fine-tuning LoRA, quantization, distillation. **Duración:** 3 meses.
- **Fase 13 (Federated Learning):** FedAvg, orquestador distribuido. **Duración:** 2 meses.
- **Fase 14 (Verificación Formal Avanzada):** Proof Bridge (Coq/Lean), symbolic execution. **Duración:** 3 meses.
- **Fase 15 (Computación Cuántica):** Quantum runtime, Shor QEC, Surface Code, T1/T2 decoherence. **Duración:** 3 meses.
- **Fase 16 (Modularización Runtime):** Descomposición de `synapse_rt.c` en módulos. **Duración:** 2 meses.
- **Fase 17 (Optimización Runtime):** PGO/LTO, reducción de footprint, benchmarks. **Duración:** 2 meses.
- **Fase 18 (Caché Incremental):** SHA-256 caching, pipeline intercept HIT/MISS/STALE. **Duración:** 2 meses.
- **Fase 19 (CanalRemoto v2):** Handshake Ed25519, canales remotos completos. **Duración:** 2 meses.
- **Fase 20 (Lifetimes Avanzados):** Region graph y union-find para lifetimes. **Duración:** 2 meses.
- **Fase 21 (RAII y Scopes):** Refactorización RAII, destructor maps y scopes. **Duración:** 2 meses.

**Dependencia global:** Todas las Fases 8-21 dependen de la Fase 7 y se pueden ejecutar en paralelo parcial, pero el orden sugerido es secuencial para minimizar conflictos. **Duración total acumulada para Fases 0-21:** 24 meses.

---

## FASES 22 A 30: SYQUEX Y ECOSISTEMA COMPLETO (30 meses estimados)

Estas fases construyen el lenguaje hermano de alto nivel (Syquex), integran OpenSyn como asistente IA universal, y completan la instalación unificada.

### FASE 22: FUNDACIÓN DE SYQUEX (LÉXICO Y PARSER)

- **Objetivo:** Diseñar e implementar el lexer, parser y traductor de Syquex al AST canónico de Synapse (`SemNodo[]`).
- **Entregables:**
  - `syquex/lexer.syq`: Tokenizador con soporte para `#lang`, palabras clave de Syquex (estructura, metodo, crear, intentar, etc.).
  - `syquex/parser.syq`: Parser de descenso recursivo basado en la gramática EBNF del Manual 3.
  - `syquex/traductor.syq`: Conversión del AST de Syquex a `SemNodo[]` (ABI v1).
  - `nucleo/ast_abi.syn`: Definición formal del `SemNodo ABI v1` con versionado y tests de regresión.
  - Pruebas de integración para confirmar que el código Syquex se traduce correctamente y pasa el análisis semántico de Synapse.
- **Criterios de Aceptación:** El compilador acepta archivos `.syq` y genera el mismo AST canónico que Synapse para construcciones equivalentes. La metadata de depuración (archivo, línea, columna) se conserva.
- **Dependencias:** Fase 21 (Synapse completo).
- **Riesgos y Mitigaciones:** Medio. El mapeo de conceptos de alto nivel (métodos, constructores) a funciones de Synapse debe ser preciso. Se debe mantener la ABI del AST estable.
- **Duración Estimada:** 4 meses (incluye Fase 22.B integrada).

---

### FASE 22.B: ESTABILIZACIÓN DEL AST Y ABI (Integrada en Fase 22)

- **Objetivo:** Establecer y probar la estabilidad del AST canónico.
- **Entregables:**
  - `nucleo/ast_abi.syn`: Archivo de especificación de la ABI.
  - Tests de compatibilidad que verifiquen que los cambios en el AST no rompen el traductor.
- **Criterios de Aceptación:** El traductor funciona correctamente con múltiples versiones menores del AST.
- **Duración Estimada:** 1 mes (paralelo al desarrollo del traductor).

---

### FASE 23: MODELO DE MEMORIA DE SYQUEX

- **Objetivo:** Implementar el modelo de memoria híbrido de Syquex (Arenas + RC + Análisis de alcance).
- **Entregables:**
  - `runtime/core/memory.c`: Ampliación con funciones de Arena (`arena_crear`, `arena_alloc`, `arena_free`).
  - `syquex/analizador_alcance.syq`: Módulo que recorre el AST traducido y calcula el último uso de cada variable para insertar liberaciones.
  - Implementación de `rc<T>` (no atómico) y `arc<T>` (atómico) en el runtime.
  - Implementación de `débil<T>` con detección de ciclos en compilación.
  - Pruebas de fugas de memoria (AddressSanitizer) para confirmar que no hay leaks.
- **Criterios de Aceptación:** Los programas Syquex no tienen fugas de memoria. El análisis de alcance inserta correctamente `arena_free` y `rc_decrementar` en todos los caminos de ejecución (incluyendo salidas tempranas).
- **Dependencias:** Fase 22.
- **Riesgos y Mitigaciones:** Alto. El análisis de alcance debe ser interprocedural. Se debe comenzar con un análisis de ámbito simple y luego añadir complejidad progresivamente.
- **Duración Estimada:** 6 meses (incluye Fase 23.B integrada).

---

### FASE 23.B: CFG Y CLEANUP BLOCKS (Integrada en Fase 23)

- **Objetivo:** Implementar generación de Cleanup Blocks para salidas tempranas (`?`, `retornar`).
- **Entregables:**
  - Construcción del Control Flow Graph (CFG) para cada función en `syquex/analizador_alcance.syq`.
  - Análisis de Liveness para determinar variables vivas en cada punto de salida.
  - Generación de bloques de cleanup en el generador de código C.
  - Semántica de Move en canales (invalida la variable origen al enviar).
- **Criterios de Aceptación:** Las funciones con múltiples `retornar` o `?` liberan correctamente todos los recursos en todos los caminos.
- **Duración Estimada:** 2 meses (paralelo al desarrollo del modelo de memoria).

---

### FASE 24: BIBLIOTECA ESTÁNDAR DE SYQUEX (`lib/`)

- **Objetivo:** Construir la biblioteca estándar de Syquex, incluyendo módulos de alto nivel.
- **Entregables:**
  - `lib/io.syq`: Entrada/salida (consola, archivos).
  - `lib/math.syq`: Matemáticas y estadísticas (extiende `std/math` de Synapse).
  - `lib/texto.syq`: Manipulación avanzada de cadenas (split, join, regex).
  - `lib/lista.syq`: Operaciones con listas (map, filter, reduce, sort).
  - `lib/mapa.syq`: Operaciones con mapas/diccionarios.
  - `lib/json.syq`: Serialización JSON (FFI a cJSON).
  - `lib/web.syq`: Servidor HTTP básico (FFI a libmicrohttpd).
  - `lib/db.syq`: Conexión a SQLite (FFI a libsqlite3) y PostgreSQL (FFI a libpq).
  - `lib/tiempo.syq`: Fechas y tiempos.
  - `lib/pruebas.syq`: Framework de testing (similar a unittest).
  - `lib/ia.syq`: Integración con OpenSyn.
- **Criterios de Aceptación:** Todos los módulos `lib/` compilan y pasan sus pruebas unitarias. La interfaz es idiomática para Syquex.
- **Dependencias:** Fase 23.
- **Riesgos y Mitigaciones:** Alto. El FFI con C (marshaling) debe ser robusto. Se requiere una estrategia de zero-copy para cadenas.
- **Duración Estimada:** 8 meses (incluye Fase 24.B integrada).

---

### FASE 24.B: ARENAS DE COMPONENTE Y FFI MARSHALING (Integrada en Fase 24)

- **Objetivo:** Implementar arenas de componente para GUI/DOM y el sistema de marshaling para FFI.
- **Entregables:**
  - `runtime/core/component_arena.c`: Gestión de arenas jerárquicas para componentes UI.
  - `lib/gui.syq`: Bindings a GTK con arenas de componente.
  - `lib/dom.syq`: Manipulación del DOM (WASM) con arenas de componente.
  - `syquex/ffi_marshaling.syq`: Generación automática de conversión para tipos (texto → const char*, estructuras → struct C).
  - Zero-Copy C-String Marshaling.
- **Criterios de Aceptación:** Las aplicaciones GUI con componentes anidados liberan memoria correctamente al destruir ventanas. La llamada a funciones C maneja cadenas sin copias innecesarias.
- **Duración Estimada:** 2 meses (paralelo al desarrollo de la biblioteca estándar).

---

### FASE 25: BACKEND WASM Y FRONTEND (SYQUEX)

- **Objetivo:** Extender el backend de Syquex para generar WASM y proporcionar un módulo para frontend (DOM).
- **Entregables:**
  - `nucleo/wasm_backend.syn`: Adaptación para soportar Syquex (ya compartido).
  - `lib/dom.syq`: Implementación completa de manipulación del DOM (crear elementos, eventos, estilos).
  - Ejemplo de SPA (Single Page Application) en Syquex que corre en navegador.
  - Pruebas E2E con un navegador headless (Playwright o Puppeteer).
- **Criterios de Aceptación:** El compilador de Syquex genera WASM válido. La SPA de ejemplo funciona correctamente en navegadores modernos.
- **Dependencias:** Fase 24.
- **Riesgos y Mitigaciones:** Medio. La interacción con el DOM a través de WASM requiere un binding cuidadoso. Se debe usar la API de WebIDL para generar los bindings automáticamente.
- **Duración Estimada:** 4 meses.

---

### FASE 26: OPENSYN PARA SYQUEX (ASISTENTE IA)

- **Objetivo:** Adaptar OpenSyn para que soporte Syquex (explicación, generación, transpilación y bindings) e implementar el sistema de inyección de contexto estático, el bucle de validación automática y la orquestación de la corrección de código generado.
- **Entregables:**
  - `opensyn/router.syn`: Extensión para manejar consultas específicas de Syquex.
  - `opensyn/transpiler.syn`: Transpilación Python → Syquex (mapeo de tipos y estructuras).
  - **Sistema de inyección de contexto estático:** Integración en el pipeline RAG de un bloque de reglas de Synapse/Syquex (gramática, modelo de memoria, ejemplos) en el System Prompt de cada consulta. Este bloque debe ser configurable y actualizable mediante el archivo de configuración.
  - **Comando `opensyn ai bindings --header header.h`:** Generación automática de wrappers en Syquex a partir de cabeceras C.
  - **Comando `opensyn ai transpile --from python script.py --to syquex`:** Transpilación de Python a Syquex.
  - **Bucle de validación:** Implementación en el LSP de la orquestación del bucle de hasta 3 intentos para corregir código generado que no compila, utilizando el flag `--check` del CLI de Synapse.
  - Pruebas de integración que verifiquen que el código transpilado compila, que los bindings son correctos y que el bucle de corrección funciona.
- **Criterios de Aceptación:** OpenSyn genera código Syquex válido a partir de Python y de cabeceras C. Las explicaciones de código Syquex son precisas. El bucle de validación reduce la tasa de errores de compilación del código generado a menos del 5% en los primeros 3 intentos. El contexto estático se inyecta correctamente en cada prompt.
- **Dependencias:** Fase 25, Fase 12 (IA Nativa de Synapse).
- **Riesgos y Mitigaciones:** Medio. El mapeo de tipos dinámicos de Python a estáticos de Syquex requiere un análisis de tipo avanzado. Se debe empezar con un subconjunto de Python (sin clases complejas) y expandir gradualmente. El bucle de validación debe ser eficiente para no degradar la experiencia de usuario.
- **Duración Estimada:** 5 meses.

---

### FASE 27: HERRAMIENTAS DE DESARROLLO (LSP, VS CODE, DEBUGGER, CLI CHECK)

- **Objetivo:** Completar el ecosistema de herramientas de desarrollo para Synapse y Syquex, incluyendo la integración completa del bucle de validación en el LSP y el flag `--check` en el CLI.
- **Entregables:**
  - `nucleo/lsp.syn`: Servidor LSP nativo con soporte para ambos lenguajes y orquestación del bucle de validación (hasta 3 intentos de corrección).
  - **Flag `--check` / `--no-emit` en el CLI:** Implementación en `synapse` de un modo de validación que solo verifica sintaxis y semántica sin generar código de salida, utilizado por el LSP para la validación rápida.
  - `vscode-synapse/`: Extensión VS Code con resaltado, autocompletado, diagnóstico, comandos IA y soporte para el bucle de corrección (mostrar progreso, errores, etc.).
  - CLI unificado (`synapse`): `build`, `run`, `test`, `fetch`, `opensyn`, `debug`, `check`.
  - Debugger integrado (time-travel, breakpoints reversibles) con integración en VS Code.
  - Pruebas E2E del LSP, la extensión y el flag `--check`.
- **Criterios de Aceptación:** La experiencia de desarrollo (edición, depuración, asistencia IA) es fluida y comparable a la de lenguajes establecidos. El flag `--check` funciona correctamente y es utilizado por el LSP. Las pruebas E2E confirman la integración completa.
- **Dependencias:** Fase 26.
- **Riesgos y Mitigaciones:** Alto. El LSP debe manejar múltiples documentos y cambios incrementales sin fallos. Se debe implementar un mecanismo de sincronización robusto.
- **Duración Estimada:** 6 meses.

---

### FASE 28: CERTIFICACIÓN DE SYQUEX

- **Objetivo:** Validar la estabilidad, el rendimiento y la corrección del lenguaje Syquex y su integración con OpenSyn.
- **Entregables:**
  - Suite de tests unitarios e integración completa para Syquex, incluyendo pruebas específicas del bucle de validación y de la inyección de contexto estático.
  - Pruebas de fuzzing y estrés (concurrencia, memoria, FFI).
  - Pruebas de rendimiento (benchmarks comparativos con Python y Go).
  - Documentación final (tutoriales, guías de referencia, API).
  - Ejemplos de aplicaciones reales (CRUD web, herramienta CLI, GUI básica, uso de OpenSyn).
  - Análisis de cobertura de código ( >95% ).
- **Criterios de Aceptación:** Todos los tests pasan. Los benchmarks muestran que Syquex es 10-50x más rápido que Python en tareas equivalentes. No hay fugas de memoria en pruebas de larga duración. El bucle de validación reduce los errores de compilación en código generado a menos del 5%.
- **Dependencias:** Fase 27.
- **Riesgos y Mitigaciones:** Medio. El rendimiento de la biblioteca estándar (FFI) debe optimizarse. Se debe perfilar y mejorar los cuellos de botella.
- **Duración Estimada:** 4 meses.

---

### FASE 29: DETECCIÓN DE HARDWARE Y GESTIÓN DE MODELOS (OPENSYN)

- **Objetivo:** Implementar la detección automática de hardware y la gestión de modelos codec para OpenSyn.
- **Entregables:**
  - `std/os.syn`: Funciones de detección de sistema (`memoria_total`, `vram_total`, `cpu_nucleos`, `arquitectura`).
  - `opensyn/installer.syn`: Script que selecciona y descarga el modelo GGUF apropiado según la VRAM/CPU. Debe verificar si ya existe un modelo en `~/.opensyn/models/` y preguntar al usuario si desea usarlo o descargar el recomendado.
  - Lógica de almacenamiento en `~/.opensyn/models/` y reutilización de modelos existentes.
  - Verificación de integridad con SHA-256.
  - Configuración automática de `llama-server` (número de hilos, capas GPU, contexto) basada en el hardware detectado.
- **Criterios de Aceptación:** El instalador de OpenSyn detecta correctamente el hardware y descarga el modelo más adecuado. Las descargas fallidas se recuperan y verifican. Si existe un modelo compatible, se ofrece al usuario la opción de reutilizarlo.
- **Dependencias:** Fase 26, Fase 11.
- **Riesgos y Mitigaciones:** Bajo. La detección de hardware es estándar en sistemas operativos modernos.
- **Duración Estimada:** 3 meses.

---

### FASE 30: INSTALACIÓN UNIFICADA Y DISTRIBUCIÓN FINAL

- **Objetivo:** Crear el instalador de un solo clic que permita instalar el ecosistema completo (Synapse + Syquex + OpenSyn) o solo Synapse.
- **Entregables:**
  - Scripts de instalación para Windows (Inno Setup), Linux (Bash + `.deb`/`.rpm`/AppImage), macOS (`.dmg`/`.pkg`).
  - Opciones de instalación: "Solo Synapse" vs "Ecosistema completo" (incluye Syquex y OpenSyn).
  - Verificación de firmas Ed25519 de todos los artefactos descargados.
  - Pruebas de humo post-instalación (compilar `01_basico.syn` y `01_basico.syq`, consultar OpenSyn).
  - Mecanismo de actualización automática (`synapse update`).
  - Publicación en GitHub Releases, Axon Hub y VS Code Marketplace.
- **Criterios de Aceptación:** El instalador funciona en sistemas limpios. La instalación completa (incluyendo OpenSyn) no requiere intervención manual del usuario más allá de la selección inicial. Las actualizaciones se aplican correctamente.
- **Dependencias:** Fase 29, Fase 11.
- **Riesgos y Mitigaciones:** Medio. La compatibilidad entre versiones de modelos y binarios debe ser estricta. Se debe proporcionar un mecanismo de rollback en caso de fallo de actualización.
- **Duración Estimada:** 4 meses.

---

## RESUMEN DE DURACIONES Y DEPENDENCIAS

| Fase | Duración (meses) | Dependencias críticas |
|------|------------------|-----------------------|
| 0 | 1 | - |
| 1 | 2 | 0 |
| 2 | 4 | 1 |
| 3 | 3 | 2 |
| 4 | 3 | 3 |
| 5 | 3 | 4 |
| 6 | 3 | 5 |
| 7 | 3 | 6 |
| 8-21 | 24 (total, secuencial) | 7 |
| 22 | 4 | 21 |
| 23 | 6 | 22 |
| 24 | 8 | 23 |
| 25 | 4 | 24 |
| 26 | 5 | 25, 12 |
| 27 | 6 | 26 |
| 28 | 4 | 27 |
| 29 | 3 | 26, 11 |
| 30 | 4 | 29, 11 |

**Duración total estimada (secuencial):** 1 + 2 + 4 + 3 + 3 + 3 + 3 + 3 + 24 + 4 + 6 + 8 + 4 + 5 + 6 + 4 + 3 + 4 = **90 meses (7.5 años)**.

*Nota: Esta duración es secuencial. Con un equipo de 5-7 ingenieros trabajando en paralelo en diferentes fases (especialmente después de la Fase 7), se puede reducir significativamente a **4-5 años calendario**.*

---

## HITOS PRINCIPALES (CHECKPOINTS)

| Hito | Fase completada | Entregable tangible |
|------|-----------------|---------------------|
| Hito 1 | Fase 5 | Compilador de Synapse auto-hospedado (bootstrap funcional). |
| Hito 2 | Fase 7 | Soporte para LLVM y WASM. |
| Hito 3 | Fase 21 | Synapse completo (todos los módulos avanzados). |
| Hito 4 | Fase 22 | Traductor Syquex funcional (primer programa .syq compilado). |
| Hito 5 | Fase 24 | Biblioteca estándar de Syquex (GUI, Web, DB). |
| Hito 6 | Fase 26 | OpenSyn soporta Syquex con contexto estático, transpilación, bindings y bucle de validación. |
| Hito 7 | Fase 28 | Syquex certificado (v1.0). |
| Hito 8 | Fase 30 | Instalador unificado (lanzamiento público). |

---

## GUÍA DE EJECUCIÓN POR FASES (DETALLE DE ARCHIVOS)

Para cada fase, los equipos deben crear los archivos listados en los entregables. A continuación, se proporciona un mapa de archivos por fase (no exhaustivo, pero suficiente para guiar la implementación).

**Fase 1:** `nucleo/lexer.syn`, `nucleo/parser.syn`, `nucleo/tokens.syn`, `nucleo/ast_nodes.syn`.  
**Fase 2:** `nucleo/tabla_simbolos.syn`, `nucleo/analizador_semantico.syn`, `nucleo/errores.syn`.  
**Fase 3:** `nucleo/generator.syn`, `runtime/core/memory.c`, `runtime/core/io.c`.  
**Fase 4:** `runtime/core/concurrency.c`, `std/concurrencia.syn`.  
**Fase 5:** `nucleo/verificador_formal.syn`, `bootstrap.sh` / `build.bat`.  
**Fase 6:** `axon/axon_rt.c`, `axon/tweetnacl.c`, `axon/axon.toml`.  
**Fase 7:** `nucleo/llvm_backend.syn`, `nucleo/wasm_backend.syn`.  
**Fase 22:** `syquex/lexer.syq`, `syquex/parser.syq`, `syquex/traductor.syq`, `nucleo/ast_abi.syn`.  
**Fase 23:** `syquex/analizador_alcance.syq`, `runtime/core/memory.c` (ampliación).  
**Fase 24:** `lib/io.syq`, `lib/math.syq`, `lib/texto.syq`, `lib/lista.syq`, `lib/mapa.syq`, `lib/json.syq`, `lib/web.syq`, `lib/gui.syq`, `lib/dom.syq`, `lib/db.syq`, `lib/tiempo.syq`, `lib/pruebas.syq`, `lib/ia.syq`, `syquex/ffi_marshaling.syq`, `runtime/core/component_arena.c`.  
**Fase 25:** `lib/dom.syq` (completado).  
**Fase 26:** `opensyn/router.syn`, `opensyn/transpiler.syn`, actualización de `synapse_rag.c` para inyección de contexto estático, `opensyn/installer.syn` (primera versión).  
**Fase 27:** `nucleo/lsp.syn` (con bucle de validación), `vscode-synapse/`, CLI con flag `--check`.  
**Fase 29:** `std/os.syn`, `opensyn/installer.syn` (completado).  
**Fase 30:** Scripts de instalación (`.iss`, `.sh`, `.dmg`), `Makefile` / `build.py`.

---

## RIESGOS GLOBALES Y ESTRATEGIAS DE MITIGACIÓN

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| **Complejidad del análisis de alcance (Fase 23)** | Alto | Comenzar con un análisis de ámbito sencillo (solo funciones sin closures) y añadir complejidad gradualmente. Validar con pruebas de estrés. |
| **Inestabilidad de la ABI del AST (Fase 22.B)** | Alto | Congelar la ABI v1 temprano. Cualquier cambio en `SemNodo` requiere una nueva versión de ABI y un traductor adaptador. |
| **FFI y Marshaling (Fase 24.B)** | Medio | Usar una estrategia Zero-Copy probada en otros lenguajes (ej. Python ctypes). Implementar pruebas de integración con librerías C reales (SQLite, GTK). |
| **Rendimiento del modelo de IA en OpenSyn (Fase 26)** | Medio | Optimizar la selección de modelos. Ofrecer modelos más pequeños para hardware limitado. Usar cuantización avanzada (Q4, Q5). |
| **Falta de datos de entrenamiento para el modelo** | Medio | La estrategia de inyección de contexto estático reduce la necesidad de fine‑tuning. El bucle de validación corrige errores en tiempo real. El feedback de usuarios se recopila para mejorar el contexto. |
| **Adopción y ecosistema** | Alto | Priorizar la experiencia de usuario (instalación cero fricción, documentación clara, ejemplos atractivos). Crear comunidad desde el día uno del lanzamiento. |
| **Bucle de validación demasiado lento** | Medio | Asegurar que el flag `--check` sea eficiente (no generar código, solo analizar). Optimizar la comunicación entre LSP y OpenSyn. |

---

## CONCLUSIÓN

Este roadmap define **todas las fases, hitos, entregables y criterios de aceptación** necesarios para construir el ecosistema Synapse + Syquex + OpenSyn desde cero. Cada fase está especificada con el nivel de detalle necesario para guiar a un equipo de ingenieros sin dejar espacio a interpretaciones ambiguas. Se han incorporado las modificaciones derivadas de los manuales 7 y 8, incluyendo la inyección de contexto estático para que la IA aprenda Synapse/Syquex sin fine‑tuning, el bucle de validación y corrección automática de código, y el flag `--check` en el CLI.

El plan está estructurado para minimizar riesgos mediante la construcción incremental, comenzando por el núcleo de Synapse y añadiendo capas de abstracción (Syquex) y servicios (OpenSyn) sobre una base sólida y probada.

**Estado:** Listo para ejecución.