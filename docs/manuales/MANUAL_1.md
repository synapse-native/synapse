MANUAL 1: ARQUITECTURA DEL LENGUAJE Y FILOSOFÍA DE DISEÑO
Archivo: 01_ARQUITECTURA_Y_FILOSOFIA.md
Versión: 5.1.1-industrial
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
Reproducibilidad	Mismo código fuente → mismo binario bit a bit en cualquier máquina.	axon.lock con SHA-256 + bootstrap de 3 etapas con diff binario.
1.3 El Ecosistema de Compilación (Self-Hosted)
El compilador está escrito íntegramente en Synapse. El pipeline es lineal e immutable:

Lexer (lexer.syn): Texto → Tokens.

Parser (parser.syn): Tokens → AST (linked-list).

Analizador Semántico (analizador_semantico.syn): AST → Tabla de símbolos + validación (3 pasadas).

Generador C (generator.syn): AST validado → Código C estándar (C11/C17).

Backend (GCC/Clang/LLVM): Código C → Binario nativo o WASM.

El binario final (synapse.exe) incluye el runtime (synapse_rt.c), el gestor de paquetes (axon_rt.c) y la criptografía (tweetnacl.c). El LSP (synapse_lsp.exe) es un binario hermano que comparte el mismo núcleo de análisis.

1.4 Filosofía de Evolución (Hoja de Ruta Técnica)
Fase	Versión	Entregable clave
Fundación	v1.x	Compilador en Python, sintaxis básica, bootstrap manual.
Auto-hospedaje	v2.x	Compilador nativo en Synapse (nucleo/*.syn). Fin de la dependencia Python para producción.
Concurrencia y Seguridad	v3.x	Ownership completo, canales Canal<T>, contratos requiere/garantiza.
Ecosistema	v4.x	Axon (Ed25519), LSP nativo, integración VS Code, Edge AI (Ollama).
Revolución Cognitiva	v5.0	Caché incremental SHA-256, Time-Travel Debugging, Sandbox (seccomp), LLVM Backend, WASM, Axon Hub (IPFS), IA Nativa (llama.cpp).
Regla de hierro: Ninguna característica nueva puede romper el bootstrap (etapas 0→1→2→3 con diff binario 0).

1.5 Estructura Física del Proyecto (Workspace)
text
/synapse
├── nucleo/                 # Corazón del compilador (escrito en Synapse)
│   ├── lexer.syn
│   ├── parser.syn
│   ├── analizador_semantico.syn
│   ├── generator.syn
│   ├── principal.syn       # Orquestador nativo
│   ├── lsp.syn             # Servidor LSP nativo
│   ├── cache.syn           # Sistema de caché incremental
│   └── wasm_backend.syn    # Backend WebAssembly
├── std/                    # Librería estándar (módulos .syn)
│   ├── io.syn
│   ├── concurrencia.syn
│   ├── cluster.syn
│   ├── debug.syn
│   └── modelo.syn          # IA nativa
├── axon/                   # Runtime de Axon (C)
│   ├── axon_rt.c
│   └── tweetnacl.c
├── synapse_rt.c            # Runtime base (canales, SIMD, memoria)
├── opensyn/                # Servicio de IA desacoplado (C/Synapse)
│   ├── orchestrator.c
│   ├── llama_client.c
│   └── router.syn
├── lsp/                    # Puente LSP (Python legacy, opcional)
├── tests/                  # Suites de prueba (Python + C)
├── docs/manuales/          # Los 9 manuales de ingeniería (MANUAL_1.md..MANUAL_9.md)
└── vscode-synapse/         # Extensión VS Code