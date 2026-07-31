MANUAL 1: ARQUITECTURA DEL LENGUAJE Y FILOSOFÍA DE DISEÑO
Archivo: 01_ARQUITECTURA_Y_FILOSOFIA.md
Versión: 5.1.1-industrial (Revisada por Auditoría)
Propósito: Definir los principios rectores, la visión de negocio/ingeniería y la hoja de ruta evolutiva del lenguaje.

1.1 Visión General
Synapse es un lenguaje de programación nativo, compilado y de grado de sistemas. Está diseñado para ser el cimiento de sistemas operativos, motores de bases de datos, infraestructura de red y aplicaciones Edge AI. Opera sin recolector de basura, sin dependencias opacas y sin telemetría forzada.

Público objetivo: Ingenieros de sistemas, desarrolladores de kernels, arquitectos de infraestructura y equipos que requieren máximo rendimiento con garantías formales de seguridad de memoria.

1.2 Los Pilares de "El Pacto" (Principios Innegociables)
Principio	Descripción formal	Implementación en el compilador
Tipado Estricto Inferido	Todo símbolo tiene un tipo único deducido estáticamente. El compilador rechaza ambigüedades (ej. let x = 42 + 3.14 → error).	Algoritmo Hindley-Milner restringido en el Analizador Semántico (Pasada 2 y 3).
Zero-GC (Sin Recolector)	Gestión de memoria determinista basada en RAII estático. No hay pausas por GC.	Ownership + Borrowing. El generador inyecta pool_free() al final del scope del propietario.
Algebraic Error Handling	Prohibido null y códigos de error enteros. Todo error se modela con Resultado<T, E> o Opcion<T>.	Tipos predefinidos en el prelude. El analizador exige coincidir exhaustivo.
Rendimiento Nativo	El código generado compite con C/C++ en rendimiento.	Generación de C optimizado (-O2, PGO, LTO) + backend LLVM/WASM.
Soberanía del Usuario	Cero telemetría, cero conexiones en red ocultas. Todo es local y verificable.	El runtime no tiene hilos en segundo plano. LSP solo escucha en stdio. Axon requiere --online explícito.
Reproducibilidad	Mismo código fuente → mismo binario bit a bit en cualquier máquina.	axon.lock con SHA-256 + bootstrap de 3 etapas con diff binario. Regla de oro: Toda iteración sobre mapas/diccionarios en el generador y analizador debe realizarse en orden lexicográfico de claves para garantizar determinismo.
Verificación Formal (ATP)	Demostración automática de teoremas para contratos (pre/post), terminación e invariantes en modo --safe.	Motor ATP integrado en el analizador semántico (Pasada 3 extendida) + ejecución simbólica en nucleo/verificador_formal.syn.
1.3 El Ecosistema de Compilación (Self-Hosted)
El compilador está escrito íntegramente en Synapse. El pipeline es lineal e inmutable:

Lexer (lexer.syn): Texto → Tokens.

Parser (parser.syn): Tokens → AST (linked-list).

Analizador Semántico (analizador_semantico.syn): AST → Tabla de símbolos + validación (3 pasadas). Las tablas de símbolos se serializan en orden alfabético para asegurar determinismo.

Generador C/LLVM/WASM (generator.syn, llvm_backend.syn, wasm_backend.syn): AST validado → Código intermedio. Las funciones emitidas se ordenan por nombre en el archivo de salida.

Backend (GCC/Clang/LLVM/emcc): Código intermedio → Binario nativo o WASM.

El binario final (synapse.exe) está compuesto por los siguientes módulos de runtime (modularizados):

runtime/core/memory.c: Pool allocator con caché por hilo (TLC).

runtime/core/concurrency.c: Canales, hilos, sincronización.

runtime/core/io.c: E/S de archivos y sockets base.

runtime/net/http.c: Cliente/servidor HTTP.

runtime/quantum/matrix.c: Simulación cuántica (matrices de densidad).

runtime/ml/gguf.c: Carga de modelos locales y tensor ops.

runtime/federated/aggregator.c: Algoritmos FedAvg y destilación.

axon/axon_rt.c: Gestor de paquetes.

tweetnacl.c: Criptografía Ed25519.

1.4 Filosofía de Evolución (Hoja de Ruta Técnica)
Fase	Versión	Entregable clave
Fundación	v1.x	Compilador en Python, sintaxis básica, bootstrap manual.
Auto-hospedaje	v2.x	Compilador nativo en Synapse (nucleo/*.syn). Fin de la dependencia Python para producción.
Concurrencia y Seguridad	v3.x	Ownership completo, canales Canal<T>, contratos requiere/garantiza.
Ecosistema	v4.x	Axon (Ed25519), LSP nativo, integración VS Code, Edge AI (Ollama).
Revolución Cognitiva + Certificación Industrial	v5.1.1-industrial	Caché incremental SHA-256, Time-Travel Debugging, Sandbox (seccomp), LLVM Backend (IR/JIT), WASM, Axon Hub (IPFS), IA Nativa (llama.cpp), Motor ATP y Verificación Formal, Aprendizaje Federado (std::federated), Simulación Cuántica (std::quantum), Runtime modularizado, Asignador con TLC.
Regla de hierro: Ninguna característica nueva puede romper el bootstrap (etapas 0→1→2→3 con diff binario 0). El determinismo se verifica obligatoriamente en la CI mediante la comparación de los hashes SHA-256 de las etapas 2 y 3.

1.5 Estructura Física del Proyecto (Workspace)
text
/synapse
├── nucleo/                 # Corazón del compilador (escrito en Synapse)
│   ├── lexer.syn
│   ├── parser.syn
│   ├── analizador_semantico.syn
│   ├── generator.syn
│   ├── principal.syn
│   ├── lsp.syn
│   ├── cache.syn
│   ├── wasm_backend.syn
│   ├── verificador_formal.syn
│   └── llvm_backend.syn
├── std/                    # Librería estándar (módulos .syn)
│   ├── io.syn
│   ├── concurrencia.syn
│   ├── cluster.syn
│   ├── debug.syn
│   ├── federated.syn
│   ├── quantum.syn
│   └── modelo.syn
├── runtime/                # Runtime modular (C)
│   ├── core/
│   │   ├── memory.c        # Pool allocator + TLC
│   │   ├── concurrency.c   # Canales, mutexes
│   │   └── io.c            # File I/O, sockets
│   ├── net/
│   │   └── http.c
│   ├── quantum/
│   │   └── matrix.c
│   ├── ml/
│   │   └── gguf.c
│   └── federated/
│       └── aggregator.c
├── axon/                   # Runtime de Axon (C)
│   ├── axon_rt.c
│   └── tweetnacl.c
├── opensyn/                # Servicio de IA desacoplado
│   ├── orchestrator.c
│   ├── llama_client.c
│   └── router.syn
├── lsp/                    # Puente LSP (Python legacy, opcional)
├── tests/                  # Suites de prueba (Python + C)
│   ├── unit/
│   ├── integration/
│   ├── fuzz/
│   ├── stress/
│   └── validate_*.c
└── vscode-synapse/         # Extensión VS Code