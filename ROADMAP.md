# ROADMAP DE IMPLEMENTACIÓN DEL ECOSISTEMA SYNAPSE + SYQUEX + OPENSYN

**Versión:** 8.3.0-industrial  
**Fecha:** 2026-09-12  
**Propósito:** Guía de ejecución definitiva para la implementación completa del ecosistema desde cero. Este documento describe todas las fases, hitos, entregables, dependencias, riesgos y criterios de aceptación necesarios para construir Synapse, Syquex, OpenSyn, las herramientas nativas (Fase 31) y el agente de codificación avanzado (Fase 32) como una plataforma unificada. No contiene marcas de estado previo, ya que está diseñado para iniciar desde una carpeta vacía.

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

---

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
  - **Fase 2 nativa (P1) — ✅ completada (2026-08-09, rama `feature/fase2-nativa-hm`):**
    validación de aridad/base/argumentos de instanciaciones de ADT (`Resultado<entero,texto>` vs
    `Resultado<T,E>`) portada a `nucleo/analizador_semantico.syn` (`registrar_adt` + `validar_tipo_instanciacion`,
    flag `hay_error_2_4` que aborta el pipeline) con paridad al S1; 6 tests de paridad
    (`tests/test_fase2_nativa_hm.py`), bootstrap S2==S3 byte-idéntico, regresión completa verde.
    **Pendiente residual:** unificación HM de TVars de función (`identidad(x: T) -> T`) en el nativo
    y tipos anidados (`A<B<C>,D>`, sin soporte en ningún frontend). Divergencias documentadas en
    `nucleo/README.md`; reporte `docs/reportes/FASE_2_2.4_NATIVA.md` (ref. S1: `compilador/tipos.py` +
    `compilador/semantic_types.py`, `docs/reportes/FASE_2_2.4.md` §6).
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

*Nota: Las Fases 8 a 21 cubren módulos avanzados como Concurrencia Distribuida, Time-Travel Debugging, IA Nativa, Federated Learning, Verificación Formal (ATP), Computación Cuántica, Modularización del Runtime, Optimización PGO/LTO, Caché Incremental, etc. Cada una tiene un objetivo específico, entregables, criterios de aceptación, dependencias y riesgos.*

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

---

### FASE 22: FUNDACIÓN DE SYQUEX (LÉXICO Y PARSER)

- **Objetivo:** Diseñar e implementar el lexer, parser y traductor de Syquex al AST canónico de Synapse (`SemNodo[]`).
- **Entregables:**
  - `syquex/lexer.syn`: Tokenizador con soporte para `#lang`, palabras clave de Syquex (estructura, metodo, crear, intentar, etc.).
  - `syquex/parser.syn`: Parser de descenso recursivo basado en la gramática EBNF del Manual 3.
  - `syquex/traductor.syn`: Conversión del AST de Syquex a `SemNodo[]` (ABI v1).
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
  - `syquex/analizador_alcance.syn`: Módulo que recorre el AST traducido y calcula el último uso de cada variable para insertar liberaciones.
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
  - Construcción del Control Flow Graph (CFG) para cada función en `syquex/analizador_alcance.syn`.
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
  - `syquex/ffi_marshaling.syn`: Generación automática de conversión para tipos (texto → const char*, estructuras → struct C).
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
  - **Flag `--check` / `--no-emit` en el CLI:** Implementación en `synapse` de un modo de validación que solo verifica sintaxis y semántica sin generar código de salida, utilizado por el LSP para la validación rápida. **Subfase 26.1:** Este flag se adelanta a la Fase 26 para habilitar el bucle de validación de OpenSyn.
  - Pruebas de integración que verifiquen que el código transpilado compila, que los bindings son correctos y que el bucle de corrección funciona.
- **Criterios de Aceptación:** OpenSyn genera código Syquex válido a partir de Python y de cabeceras C. Las explicaciones de código Syquex son precisas. El bucle de validación reduce la tasa de errores de compilación del código generado a menos del 5% en los primeros 3 intentos. El contexto estático se inyecta correctamente en cada prompt.
- **Dependencias:** Fase 25, Fase 12 (IA Nativa de Synapse).
- **Riesgos y Mitigaciones:** Medio. El mapeo de tipos dinámicos de Python a estáticos de Syquex requiere un análisis de tipo avanzado. Se debe empezar con un subconjunto de Python (sin clases complejas) y expandir gradualmente. El bucle de validación debe ser eficiente para no degradar la experiencia de usuario.
- **Duración Estimada:** 5 meses.

---

### FASE 27: HERRAMIENTAS DE DESARROLLO (LSP, VS CODE, DEBUGGER)

- **Objetivo:** Completar el ecosistema de herramientas de desarrollo para Synapse y Syquex, incluyendo la integración completa del bucle de validación en el LSP. El flag `--check` del CLI se implementa en la Fase 26 (subfase 26.1) y se utiliza desde aquí.
- **Entregables:**
  - `nucleo/lsp.syn`: Servidor LSP nativo con soporte para ambos lenguajes y orquestación del bucle de validación (hasta 3 intentos de corrección).
  - `vscode-synapse/`: Extensión VS Code con resaltado, autocompletado, diagnóstico, comandos IA y soporte para el bucle de corrección (mostrar progreso, errores, etc.).
  - CLI unificado (`synapse`): `build`, `run`, `test`, `fetch`, `opensyn`, `debug`, `check`.
  - Debugger integrado (time-travel, breakpoints reversibles) con integración en VS Code.
  - Pruebas E2E del LSP, la extensión y el flag `--check` (validación rápida).
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

## FASE 31: HERRAMIENTAS DE DESARROLLO NATIVAS (TOOLING COMPLETO)

Esta fase implementa el conjunto completo de herramientas de desarrollo nativas, eliminando la dependencia de Python en la cadena de desarrollo.

- **Objetivo:** Implementar el conjunto completo de herramientas de desarrollo (package manager, testing, linting, formateo, CI/CD) de forma nativa en Synapse/Syquex, eliminando toda dependencia de Python en la cadena de desarrollo.
- **Entregables:**
  - **31.1 Aislamiento de Workspaces en Axon:**
    - `axon/axon_rt.c` ampliado con funciones de workspace (`axon_workspace_crear`, `axon_workspace_resolver`).
    - Cada proyecto tiene su propio directorio de caché (`.axon/cache/`) y su propio `axon.lock`.
    - Los lockfiles registran dependencias específicas del proyecto con hashes SHA-256.
  - **31.2 Testing Nativo sin Genéricos:**
    - `lib/pruebas.syq`: Framework de testing con sobrecarga estática explícita (`assert_eq_int`, `assert_eq_texto`, `assert_eq_decimal`, `assert_eq_booleano`, `assert_eq_tensor`).
    - Funciones `test` y `suite` para agrupar y ejecutar pruebas.
    - Flags `--junit`, `--coverage`, `--json` en `synapse test`.
  - **31.3 Linter Nativo (`synapse lint`):**
    - `nucleo/lint.syn`: Linter que procesa el AST unificado (`SemNodo[]`).
    - Reglas: variables no utilizadas, funciones sin contratos, indentación incorrecta, nombres no estándar, código muerto.
    - Flags `--fix` (corregir automáticamente) y `--check` (verificar sin modificar).
  - **31.4 Formateador Nativo (`synapse fmt`):**
    - `nucleo/formatter.syn`: Formateador que reescribe el código según reglas de estilo.
    - Reglas: 4 espacios, espacios alrededor de operadores, una línea en blanco entre funciones.
    - Flags `--check` y `--dry-run`.
  - **31.5 CI/CD Reporting Mejorado:**
    - Extensión de `synapse test` para generar reportes en formatos estándar (JUnit XML, JSON, HTML de cobertura).
- **Criterios de Aceptación:**
  - `lib/pruebas.syq` compila y pasa sus pruebas unitarias.
  - `synapse lint` detecta correctamente variables no utilizadas, funciones sin contratos, etc.
  - `synapse fmt` reescribe archivos según las reglas de estilo.
  - `synapse test --junit` genera un XML válido.
  - `synapse test --coverage` genera un informe HTML de cobertura.
  - Todos los tests originales (184+) siguen pasando.
- **Dependencias:** Fase 27 (CLI unificado), Fase 24.B (`lib/pruebas.syq`), Fase 22 (AST canónico).
- **Riesgos y Mitigaciones:**
  - **Riesgo:** El linter puede ser lento en archivos grandes.
    - **Mitigación:** Procesar el AST en una sola pasada y optimizar el recorrido.
  - **Riesgo:** El formateador puede introducir cambios no deseados.
    - **Mitigación:** Incluir flag `--check` para verificar sin modificar archivos.
- **Duración Estimada:** 8 meses.

---

## FASE 32: AGENTE DE CODIFICACIÓN AVANZADO Y MEMORIA PERSISTENTE (8 meses)

Esta fase transforma a OpenSyn de un asistente de código en un agente de codificación autónomo de grado industrial, incorporando: grafo de conocimiento construido desde el AST canónico, memoria persistente cifrada, análisis de impacto determinista, pipeline multi-agente optimizado para hardware local, y verificación AOT con auto-refutación.

---

### 32.0 VISIÓN Y DIFERENCIADOR ESTRATÉGICO

- **Objetivo:** OpenCode, Cursor, Claude Code y Codex compiten en velocidad de generación de código. Ese eje es un **commodity**: la ejecución técnica (LLM → código) ya está resuelta. La ventaja competitiva real está en la **capa de contexto y confianza**.
- **La regla de oro de la Fase 32:** Ningún competidor puede replicar nuestro grafo de conocimiento porque ninguno controla el AST del compilador. Esa es nuestra ventaja estructural.
- **Alcance explícitamente descartado:**
  - ❌ Sistema de plugins (superficie de ataque)
  - ❌ Soporte MCP (integración con herramientas externas)
  - ❌ Panel visual de grafo (mejora cosmética, no funcional)
  - ❌ App GUI/escritorio (la TUI + extensión VS Code cubren el 90% del uso)
  - ❌ Cualquier integración cloud, telemetría o gateway externo

---

### 32.1 GRAFO DE CONOCIMIENTO (Mes 1)

- **Objetivo:** Construir un grafo dirigido de dependencias, contratos y relaciones entre todos los nodos del proyecto, **directamente desde el AST canónico (`SemNodo[]`) durante el pipeline del compilador**, sin análisis heurístico ni embeddings.
- **Entregables:**
  - `nucleo/grafo_builder.syn`: Módulo que construye el grafo desde el `SemNodo[]`.
    - `construir_grafo_desde_semnodo(semnodos, total, proyecto) -> GrafoProyecto`
    - Pasada 1: Crear nodos (funciones, estructuras).
    - Pasada 2: Crear aristas (llamadas, importaciones, uso de tipos).
    - Pasada 3: Calcular dependientes (índice invertido).
    - Pasada 4: Calcular nivel de riesgo.
    - Pasada 5: Detectar ciclos (Tarjan).
    - Pasada 6: Calcular métricas agregadas.
  - Estructuras definidas: `NodoGrafo`, `ContratoInfo`, `AristaGrafo`, `GrafoProyecto`, `MetricasGrafo`.
  - Persistencia: `~/.synapse/cache/grafo/<hash_ast>.json.gz`.
  - `tests/opensyn/test_grafo.py`: Tests unitarios (determinismo, construcción correcta).
  - `tests/opensyn/test_grafo_perf.py`: Test de rendimiento (< 100 ms en 1000 archivos).
- **Criterios de Aceptación:**
  - Construir grafo de un proyecto de 1,000 archivos en < 100 ms.
  - Grafo es determinista: mismo AST → mismo hash SHA-256.
  - Sin fugas de memoria (ASan).
  - Persistencia funciona: cargar grafo cacheado es < 10 ms.
- **Dependencias:** Fase 22 (`SemNodo[]`), Fase 2 (analizador semántico).
- **Riesgos y Mitigaciones:**
  - **Riesgo:** La construcción del grafo puede ralentizar la compilación.
    - **Mitigación:** Cachear el grafo por hash de AST. Solo se reconstruye cuando el AST cambia.
- **Duración Estimada:** 1 mes.

---

### 32.2 ALGORITMOS DE GRAFO DETERMINISTAS (Mes 2)

- **Objetivo:** Implementar los algoritmos de exploración y análisis de impacto **sin LLM**, usando teoría de grafos sobre el grafo de conocimiento.
- **Entregables:**
  - `opensyn/explorer_det.syn`: Explorer determinista (BFS).
    - `explorar_contexto(archivo_objetivo, grafo, radio) -> Lista<ArchivoRelevante>`
    - `calcular_distancia(grafo, origen, destino) -> entero`
  - `opensyn/architect_det.syn`: Architect determinista (DFS invertido + Tarjan).
    - `analizar_impacto_completo(archivo, grafo) -> AnalisisImpacto`
    - `dfs_invertido(id_inicio, grafo) -> Lista<(texto, entero, texto)>`
    - `detectar_ciclo_tarjan(id_inicio, grafo) -> Ciclo`
  - Estructuras definidas: `ArchivoRelevante`, `AnalisisImpacto`, `NodoAfectado`, `ContratoCritico`, `Ciclo`, `MetricasImpacto`.
  - `tests/opensyn/test_explorer_det.py`: Tests unitarios.
  - `tests/opensyn/test_architect_det.py`: Tests unitarios.
  - `tests/opensyn/test_tarjan.py`: Tests de detección de ciclos (0 falsos positivos).
- **Criterios de Aceptación:**
  - BFS de dependencias: < 1 ms en proyecto de 1,000 archivos.
  - Análisis de impacto completo: < 5 ms.
  - Detección de ciclos: O(V+E), correcta según Tarjan.
  - Cero falsos positivos en 100 proyectos de prueba.
- **Dependencias:** Fase 32.1 (grafo de conocimiento).
- **Riesgos y Mitigaciones:**
  - **Riesgo:** Los algoritmos pueden ser incorrectos en grafos complejos.
    - **Mitigación:** Tests exhaustivos con grafos conocidos y verificación cruzada con NetworkX (solo para tests).
- **Duración Estimada:** 1 mes.

---

### 32.3 MEMORIA PERSISTENTE CIFRADA (Mes 3)

- **Objetivo:** Implementar tres capas de memoria persistente **cifradas en reposo**, usando exclusivamente las primitivas criptográficas del ecosistema (TweetNaCl/XSalsa20-Poly1305), sin dependencias externas.
- **Entregables:**
  - `opensyn/memoria.syn`: Memoria persistente cifrada.
    - `memoria_inicializar(passphrase) -> Resultado<nulo, texto>`
    - `memoria_guardar_patron(patron, contexto, exito) -> Resultado<nulo, texto>`
    - `memoria_consultar_patrones(contexto) -> Lista<PatronAprendido>`
    - `memoria_registrar_fallo(intento, razon, solucion) -> Resultado<nulo, texto>`
    - `memoria_evitar_fallos(contexto) -> Lista<MemoriaNegativa>`
    - `memoria_guardar_proyecto(hash_ast, datos) -> Resultado<nulo, texto>`
    - `memoria_cerrar()`
  - Estructuras: `PatronAprendido`, `MemoriaNegativa`, `EntradaCifrada`.
  - Índice en RAM para búsquedas rápidas (`_indice_contexto`).
  - `tests/opensyn/test_memoria_cifrada.py`: Tests unitarios.
    - Verificar que `strings ~/.opensyn/memoria.db` no muestra texto legible.
    - Verificar que la clave nunca se escribe a disco.
    - Verificar que el descifrado de 100 entradas tarda < 50 ms.
- **Criterios de Aceptación:**
  - `strings ~/.opensyn/memoria.db` no muestra texto legible.
  - La clave nunca se escribe a disco, logs ni archivos temporales.
  - El descifrado de 100 entradas tarda < 50 ms (con índice en RAM).
  - Derivación de clave con Argon2id tarda < 500 ms.
  - Al reiniciar OpenSyn sin passphrase, la memoria no es accesible.
- **Dependencias:** Fase 32.1 (memoria de proyecto), Fase 6 (TweetNaCl).
- **Riesgos y Mitigaciones:**
  - **Riesgo:** El cifrado puede ralentizar el acceso a la memoria.
    - **Mitigación:** Índice en RAM para búsquedas rápidas. Descifrado solo bajo demanda.
- **Duración Estimada:** 1 mes.

---

### 32.4 DERIVACIÓN DE CLAVE CON ARGON2ID (Mes 4)

- **Objetivo:** Implementar la derivación de clave maestra del hardware + passphrase, usando Argon2id (implementación ligera embebida).
- **Entregables:**
  - `runtime/core/key_derivation.c`: Implementación de Argon2id.
    - `key_derivation_maestra(passphrase, hardware_uuid, machine_id, clave_salida) -> int`
    - `argon2id_derivar(passphrase, salt, iteraciones, memoria_kb, paralelismo, salida, salida_len) -> int`
  - `tests/opensyn/test_key_derivation.py`: Tests unitarios.
    - Verificar que la derivación tarda < 500 ms.
    - Verificar que funciona en Windows, Linux y macOS.
    - Verificar que el fallback (PBKDF2 sin TPM) funciona.
- **Criterios de Aceptación:**
  - Derivación de clave con Argon2id tarda < 500 ms.
  - Funciona en Windows, Linux y macOS.
  - Fallback si no hay TPM: PBKDF2 con passphrase.
- **Dependencias:** Fase 32.3 (memoria cifrada).
- **Riesgos y Mitigaciones:**
  - **Riesgo:** Argon2id puede ser lento en hardware antiguo.
    - **Mitigación:** Parámetros ajustables (iteraciones, memoria). Fallback a PBKDF2 si es necesario.
- **Duración Estimada:** 1 mes.

---

### 32.5 VERIFICACIÓN AOT CON AUTO-REFUTACIÓN (Mes 5)

- **Objetivo:** Expandir el bucle de validación actual (`synapse check --no-emit`) con **auto-refutación**: generar casos límite, compilarlos y ejecutarlos para verificar que el código es robusto.
- **Entregables:**
  - `runtime/core/proceso.c`: Ejecución asíncrona de subprocesos con timeout.
    - `proceso_ejecutar_async(comando, timeout_ms) -> ProcesoAsync*`
    - `proceso_esperar(p, codigo_salida) -> bool`
    - `proceso_matar(p)`
  - `opensyn/verificacion.syn`: Verificación AOT con auto-refutación.
    - `verificar_caso_limite(codigo, caso) -> ResultadoCaso`
    - `generar_casos_limite(codigo) -> Lista<CasoLimite>`
    - `verificar_codigo_generado(codigo, archivo_original) -> Resultado<Verificacion, texto>`
  - Estructuras: `CasoLimite`, `ResultadoCaso`, `Verificacion`.
  - `tests/opensyn/test_verificacion_aot.py`: Tests unitarios.
    - Verificar que la compilación de caso límite es < 1 s.
    - Verificar que la ejecución con timeout funciona.
    - Verificar que la ejecución paralela de 5 casos es < 3 s.
- **Criterios de Aceptación:**
  - Compilación de caso límite: < 1 s.
  - Ejecución con timeout: funciona correctamente.
  - Ejecución paralela de 5 casos: < 3 s.
  - Detección de bucles infinitos: timeout de 5 s funciona.
- **Dependencias:** Fase 32.1 (grafo de conocimiento), Fase 26 (flag `--check`), Fase 4 (fibras).
- **Riesgos y Mitigaciones:**
  - **Riesgo:** La compilación de casos límite puede ser costosa.
    - **Mitigación:** Máximo 5 casos por verificación. Ejecución en paralelo. Caché de compilaciones.
- **Duración Estimada:** 1 mes.

---

### 32.6 INTEGRACIÓN RAG CON MEMORIA (Mes 6)

- **Objetivo:** Integrar la memoria persistente y el análisis de impacto determinista en el pipeline RAG, para que el prompt incluya patrones exitosos, fallos previos y análisis de impacto.
- **Entregables:**
  - Modificación de `opensyn/synapse_rag.c`: `rag_construir_prompt_con_memoria(ctx, n_ctx)`.
  - `opensyn/router.syn`: Integración de la memoria en el pipeline.
  - `opensyn/feedback.syn`: Ciclo de feedback automático.
    - `registrar_feedback(codigo_generado, codigo_corregido, error)`
  - `tests/integration/test_rag_pipeline.py`: Tests de integración.
    - Verificar que el prompt incluye patrones y fallos.
    - Verificar que el análisis de impacto se incluye.
- **Criterios de Aceptación:**
  - El prompt incluye análisis de impacto determinista.
  - El prompt incluye patrones exitosos y fallos previos.
  - La latencia total del ciclo es < 30 s.
- **Dependencias:** Fase 32.3 (memoria cifrada), Fase 32.2 (análisis de impacto).
- **Riesgos y Mitigaciones:**
  - **Riesgo:** El prompt puede exceder el límite de tokens.
    - **Mitigación:** Truncar patrones y fallos a los más relevantes. Respetar la negociación 30/70.
- **Duración Estimada:** 1 mes.

---

### 32.7 PIPELINE MULTI-AGENTE OPTIMIZADO (Mes 7)

- **Objetivo:** Implementar un pipeline multi-agente **secuencial con 2-3 inferencias máximo**, donde los roles deterministas (Explorer, Architect) se resuelven con el grafo (32.2) y solo los roles creativos (Coder, Reviewer, Fixer) usan LLM.
- **Entregables:**
  - `opensyn/orquestador_multi.syn`: Pipeline multi-agente optimizado.
    - `ejecutar_pipeline(instruccion, archivo) -> ResultadoPipeline`
    - `construir_prompt_coder(contexto) -> texto`
    - `construir_prompt_reviewer(contexto) -> texto`
    - `construir_prompt_fixer(contexto) -> texto`
  - Estructuras: `ContextoPipeline`, `ResultadoPipeline`.
  - `opensyn/principal.syn`: Tabla de modos (ask, plan, code, debug, orchestrator).
  - `tests/integration/test_pipeline_32.py`: Tests de integración.
    - Verificar que el ciclo completo usa 2-3 inferencias.
    - Verificar que el tiempo total es < 30 s.
    - Verificar que la tasa de corrección exitosa en ≤3 intentos es > 95%.
- **Criterios de Aceptación:**
  - Ciclo completo: 2-3 inferencias máximo.
  - Tiempo total: < 30 segundos en hardware medio.
  - Tasa de corrección exitosa en ≤3 intentos: > 95%.
  - Latencia de fases deterministas (Explorer + Architect): < 6 ms.
- **Dependencias:** Fase 32.6 (integración RAG), Fase 32.2 (análisis de impacto).
- **Riesgos y Mitigaciones:**
  - **Riesgo:** El pipeline puede ser más lento de lo esperado.
    - **Mitigación:** Optimizar prompts. Reducir el número de inferencias. Cachear análisis deterministas.
- **Duración Estimada:** 1 mes.

---

### 32.8 CERTIFICACIÓN DE LA FASE 32 (Mes 8)

- **Objetivo:** Validar la estabilidad, el rendimiento y la corrección del agente de codificación avanzado.
- **Entregables:**
  - Suite de tests unitarios e integración completa para la Fase 32.
  - Pruebas de fuzzing y estrés (concurrencia, memoria, cifrado).
  - Pruebas de rendimiento (benchmarks comparativos con OpenCode, Cursor, Claude Code).
  - Documentación final (tutoriales, guías de referencia, API).
  - Ejemplos de aplicaciones reales (CRUD web, herramienta CLI, GUI básica, uso de OpenSyn con memoria).
  - Análisis de cobertura de código ( >95% ).
  - `docs/reportes/FASE_32_CERTIFICACION.md`: Reporte final.
- **Criterios de Aceptación:**
  - Todos los tests pasan.
  - Los benchmarks muestran que OpenSyn es competitivo en contexto y confianza.
  - No hay fugas de memoria en pruebas de larga duración.
  - El cifrado funciona correctamente.
  - El análisis de impacto es determinista y sin falsos positivos.
- **Dependencias:** Fase 32.7 (pipeline multi-agente).
- **Riesgos y Mitigaciones:**
  - **Riesgo:** La certificación puede revelar problemas no detectados.
    - **Mitigación:** Tests exhaustivos previos. Revisión de código por pares.
- **Duración Estimada:** 1 mes.

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
| 31 | 8 | 27, 24.B, 22 |
| 32 | 8 | 31, 22 |

**Duración total estimada (secuencial):** 1 + 2 + 4 + 3 + 3 + 3 + 3 + 3 + 24 + 4 + 6 + 8 + 4 + 5 + 6 + 4 + 3 + 4 + 8 + 8 = **106 meses (8.8 años)**.

*Nota: Esta duración es secuencial. Con un equipo de 5-7 ingenieros trabajando en paralelo en diferentes fases (especialmente después de la Fase 7), se puede reducir significativamente a **5-6 años calendario**.*

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
| Hito 9 | Fase 31 | Herramientas nativas completas (lint, fmt, test, workspaces). |
| Hito 10 | Fase 32 | Agente de codificación avanzado con memoria persistente y grafo de conocimiento. |

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
**Fase 22:** `syquex/lexer.syn`, `syquex/parser.syn`, `syquex/traductor.syn`, `nucleo/ast_abi.syn`.  
**Fase 23:** `syquex/analizador_alcance.syn`, `runtime/core/memory.c` (ampliación).  
**Fase 24:** `lib/io.syq`, `lib/math.syq`, `lib/texto.syq`, `lib/lista.syq`, `lib/mapa.syq`, `lib/json.syq`, `lib/web.syq`, `lib/gui.syq`, `lib/dom.syq`, `lib/db.syq`, `lib/tiempo.syq`, `lib/pruebas.syq`, `lib/ia.syq`, `syquex/ffi_marshaling.syn`, `runtime/core/component_arena.c`.  
**Fase 25:** `lib/dom.syq` (completado).  
**Fase 26:** `opensyn/router.syn`, `opensyn/transpiler.syn`, actualización de `synapse_rag.c` para inyección de contexto estático, `opensyn/installer.syn` (primera versión). **Subfase 26.1:** Flag `--check` / `--no-emit` en el CLI.  
**Fase 27:** `nucleo/lsp.syn` (con bucle de validación), `vscode-synapse/`, debugger integrado.  
**Fase 29:** `std/os.syn`, `opensyn/installer.syn` (completado).  
**Fase 30:** Scripts de instalación (`.iss`, `.sh`, `.dmg`), `Makefile` / `build.py`.  
**Fase 31:** `lib/pruebas.syq` (ampliación), `nucleo/lint.syn`, `nucleo/formatter.syn`, `axon/axon_rt.c` (ampliación), `tests/nucleo/test_lint.py`, `tests/nucleo/test_fmt.py`, `tests/integration/test_reports.py`, `tests/integration/test_coverage.py`.  
**Fase 32:** `nucleo/grafo_builder.syn`, `opensyn/explorer_det.syn`, `opensyn/architect_det.syn`, `opensyn/memoria.syn`, `runtime/core/key_derivation.c`, `runtime/core/proceso.c`, `opensyn/verificacion.syn`, `opensyn/orquestador_multi.syn`, `opensyn/feedback.syn`, `opensyn/principal.syn` (tabla de modos), `tests/opensyn/test_grafo.py`, `tests/opensyn/test_explorer_det.py`, `tests/opensyn/test_architect_det.py`, `tests/opensyn/test_memoria_cifrada.py`, `tests/opensyn/test_key_derivation.py`, `tests/opensyn/test_verificacion_aot.py`, `tests/integration/test_pipeline_32.py`.

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
| **Complejidad del grafo de conocimiento (Fase 32.1)** | Medio | Comenzar con un grafo simple (funciones y llamadas). Añadir complejidad (contratos, tipos) gradualmente. |
| **Cifrado de memoria puede ralentizar el acceso (Fase 32.3)** | Medio | Índice en RAM para búsquedas rápidas. Descifrado solo bajo demanda. |
| **Pipeline multi-agente puede exceder latencia (Fase 32.7)** | Medio | Reducir el número de inferencias. Cachear análisis deterministas. Optimizar prompts. |
| **Verificación AOT puede ser costosa (Fase 32.5)** | Medio | Máximo 5 casos por verificación. Ejecución en paralelo. Caché de compilaciones. |

---

## CONCLUSIÓN

Este roadmap define **todas las fases, hitos, entregables y criterios de aceptación** necesarios para construir el ecosistema Synapse + Syquex + OpenSyn desde cero, incluyendo las herramientas nativas (Fase 31) y el agente de codificación avanzado (Fase 32). Cada fase está especificada con el nivel de detalle necesario para guiar a un equipo de ingenieros sin dejar espacio a interpretaciones ambiguas.

El plan está estructurado para minimizar riesgos mediante la construcción incremental, comenzando por el núcleo de Synapse y añadiendo capas de abstracción (Syquex), servicios (OpenSyn) y capacidades avanzadas (grafo de conocimiento, memoria persistente, pipeline multi-agente) sobre una base sólida y probada.

**El diferenciador real está en la capa de contexto y confianza:** ningún competidor puede replicar nuestro grafo de conocimiento porque ninguno controla el AST del compilador. Esa es nuestra ventaja estructural.

**Estado:** Listo para ejecución.