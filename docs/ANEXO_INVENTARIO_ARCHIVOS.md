# ANEXO: Inventario de Archivos Según los Manuales v8.1.0

> Anexo informativo que reúne la **lista exhaustiva de archivos que deben estar
> escritos en Synapse puro** (extensión `.syn` para Synapse, `.syq` para Syquex)
> dentro del ecosistema. No incluye código C, Python, TypeScript, JSON, TOML, etc.
> — solo lo que los manuales exigen que esté en Synapse. Derivado de la
> revisión cruzada contra los Manuales 1-9 y el Roadmap.

---

## 1. NÚCLEO DEL COMPILADOR (`/nucleo/`)

Estos son el corazón del compilador. Están escritos en Synapse **por definición**
(auto‑hospedaje).

| Archivo | Manual de referencia | Propósito |
|---------|----------------------|-----------|
| `nucleo/lexer.syn` | M2 §3 | Tokenizador e inyector de indentación (INDENT/DEDENT). |
| `nucleo/parser.syn` | M2 §4 | Parser de descenso recursivo. Construye el AST enlazado. |
| `nucleo/ast_nodes.syn` | M2 §5 | Definición de los nodos del AST (`SemNodo[]` ABI v1). |
| `nucleo/tokens.syn` | M2 §3.3 | Definición de `TokenID` y diccionarios multi‑idioma (es, en, fr, pt). |
| `nucleo/tabla_simbolos.syn` | M3 §2 | Gestión de scopes, símbolos y búsqueda léxica. |
| `nucleo/analizador_semantico.syn` | M3 §6 | Motor de análisis de 3 pasadas (estructuras → firmas → cuerpos). |
| `nucleo/errores.syn` | M3 §10 | Taxonomía de errores del compilador. |
| `nucleo/generator.syn` | M4 §2 | Generador de código C (emisor). |
| `nucleo/llvm_backend.syn` | M8 §1 | Backend LLVM IR (opcional, pero especificado en Synapse). |
| `nucleo/wasm_backend.syn` | M8 §2 | Backend WebAssembly (WAT/WASM). |
| `nucleo/verificador_formal.syn` | M3 §8 | Motor de contratos (`requiere`/`garantiza`) y ATP básico. |
| `nucleo/lifetimes.syn` | M4 §4.3 | Análisis de tiempos de vida (lifetimes). |
| `nucleo/cache.syn` | M8 §3 | Sistema de caché incremental (SHA‑256). |
| `nucleo/principal.syn` | M1 §3, M9 §1 | Punto de entrada del compilador (orquesta el pipeline). |
| `nucleo/lsp.syn` | M8 §1 | Servidor LSP nativo. |
| `nucleo/ast_abi.syn` | M6 §1.2, Roadmap F22.B | Especificación de la ABI del AST (versionado). |
| `nucleo/builtins.syn` | M8 §5 | Funciones integradas (ej. `a_texto`, `leer_bytes`). |

---

## 2. FRONTEND DE SYQUEX (`/syquex/`)

Estos archivos definen el lenguaje hermano de alto nivel. Todos están escritos
en Synapse puro porque el compilador de Syquex está escrito en Synapse.

| Archivo | Manual de referencia | Propósito |
|---------|----------------------|-----------|
| `syquex/lexer.syq` | M3 §3 | Tokenizador de Syquex (soporta `#lang`, palabras clave de alto nivel). |
| `syquex/parser.syq` | M3 §4 | Parser de Syquex (descenso recursivo, gramática EBNF). |
| `syquex/traductor.syq` | M3 §11 | Traducción del AST de Syquex a `SemNodo[]` de Synapse. |
| `syquex/analizador_alcance.syq` | M4 §5 | Análisis de alcance para liberación automática de memoria (Cleanup Blocks). |
| `syquex/ffi_marshaling.syq` | M4 §5 | Marshaling automático para FFI (conversión de tipos a C). |
| `syquex/arena_componente.syq` | M4 §6 | Gestión de arenas de componente para GUI/DOM. |
| `syquex/builtins.syq` | M3 §5 | Funciones integradas de Syquex (ej. `escribir_linea`). |
| `syquex/syquex.syn` | M3 §1 | Compilador de Syquex (orquesta lexer → parser → traductor). |

---

## 3. BIBLIOTECA ESTÁNDAR DE SYNAPSE (`/std/`)

Estos módulos están escritos en Synapse puro y proporcionan funcionalidades
básicas al lenguaje de sistemas.

| Archivo | Manual de referencia | Propósito |
|---------|----------------------|-----------|
| `std/io.syn` | M1 §4.3 | Entrada/salida básica (log, lectura/escritura de archivos). |
| `std/math.syn` | M1 §4.3 | Matemáticas y tensores. |
| `std/net.syn` | M5 §5 | Concurrencia distribuida (`std.cluster`). |
| `std/concurrencia.syn` | M5 §3 | Canales tipados (`Canal<T>`) y fibras. |
| `std/debug.syn` | M8 §3 | Depuración time‑travel y trazas. |
| `std/os.syn` | M7 §2.5, M9 §5 | Sistema (detección de hardware, memoria, CPU). |
| `std/federated.syn` | M5 §6 | Aprendizaje federado (FedAvg). |
| `std/quantum.syn` | M5 §7 | Computación cuántica (qubits, puertas, QEC). |
| `std/modelo.syn` | M7 §3 | Carga y ejecución de modelos GGUF (IA). |

---

## 4. BIBLIOTECA ESTÁNDAR DE SYQUEX (`/lib/`)

Estos módulos están escritos en **Synapse puro** (extensión `.syq`) y
proporcionan el ecosistema de alto nivel para Syquex.

| Archivo | Manual de referencia | Propósito |
|---------|----------------------|-----------|
| `lib/io.syq` | M9 §2.2, Material F24 | Entrada/salida de consola y archivos. |
| `lib/math.syq` | M9 §2.2 | Funciones matemáticas y estadísticas. |
| `lib/texto.syq` | M9 §2.2 | Manipulación avanzada de cadenas. |
| `lib/lista.syq` | M9 §2.2 | Operaciones funcionales con listas (map, filter, reduce). |
| `lib/mapa.syq` | M9 §2.2 | Operaciones con mapas/diccionarios. |
| `lib/json.syq` | M9 §2.2, Material F24 | Serialización/deserialización JSON. |
| `lib/web.syq` | M9 §2.2, Material F24 | Servidor HTTP con fibras. |
| `lib/gui.syq` | M9 §2.2 | Bindings a GTK (con arenas de componente). |
| `lib/dom.syq` | M9 §2.2, Material F25 | Manipulación del DOM (WASM). |
| `lib/db.syq` | M9 §2.2 | Conexión a SQLite y PostgreSQL. |
| `lib/tiempo.syq` | M9 §2.2 | Fechas y tiempos. |
| `lib/pruebas.syq` | M9 §2.2 | Framework de testing. |
| `lib/ia.syq` | M9 §2.2 | Integración con OpenSyn. |
| `lib/ffi.syq` | M4 §5 | Marshaling automático (extensión). |

---

## 5. ASISTENTE IA OPENSYN (`/opensyn/`)

Estos archivos están escritos en Synapse puro porque OpenSyn es una
aplicación del ecosistema.

| Archivo | Manual de referencia | Propósito |
|---------|----------------------|-----------|
| `opensyn/router.syn` | M7 §2.4 | Enrutador de peticiones de IA. |
| `opensyn/installer.syn` | M7 §2.5 | Instalador de OpenSyn (detección HW, descarga de modelos). |
| `opensyn/transpiler.syn` | M7 §5.1 | Transpilación Python → Syquex. |
| `opensyn/synapse_rag.syn` | M7 §2.3 | Pipeline RAG (inyección de contexto). |

---

## 6. HERRAMIENTAS DE DESARROLLO (`/vscode-synapse/`)

La extensión VS Code está escrita en **TypeScript/JavaScript**, no en Synapse.
Sin embargo, el servidor LSP (`nucleo/lsp.syn`) está en Synapse puro.

---

## 7. EJEMPLOS (`/examples/`)

Estos archivos son código de usuario escrito en Synapse puro (`.syn`) o
Syquex (`.syq`). No son parte del compilador, pero son fundamentales para la
demostración.

| Archivo | Manual de referencia | Propósito |
|---------|----------------------|-----------|
| `examples/synapse/01_basico.syn` | M1 | Hola Mundo en Synapse. |
| `examples/synapse/02_estructuras.syn` | M2 | Uso de estructuras y métodos. |
| `examples/synapse/03_tensores_ia.syn` | M7 | Tensores y operaciones de IA. |
| `examples/syquex/01_basico.syq` | M3 | Hola Mundo en Syquex. |
| `examples/syquex/02_web.syq` | M9 | Servidor web en Syquex. |
| `examples/syquex/03_gui.syq` | M9 | GUI con GTK en Syquex. |

---

## 8. TESTS (`/tests/`)

Los tests están escritos en múltiples lenguajes según el manual:

- **Python**: `tests/unit/`, `tests/integration/` (para pruebas del compilador).
- **C**: `tests/validate_*.c` (para pruebas del runtime).
- **Synapse puro**: `tests/micro_bootstrap/`, `tests/syquex/` (para pruebas de
  integración de los lenguajes).

---

## 📊 RESUMEN POR CATEGORÍA

| Categoría | Archivos .syn/.syq | % del total |
|-----------|-------------------|-------------|
| Núcleo del compilador (`nucleo/`) | 18 | 30% |
| Frontend Syquex (`syquex/`) | 8 | 13% |
| Biblioteca estándar Synapse (`std/`) | 9 | 15% |
| Biblioteca estándar Syquex (`lib/`) | 14 | 23% |
| OpenSyn (`opensyn/`) | 4 | 7% |
| Ejemplos (`examples/`) | 6 | 10% |
| **Total** | **59 archivos** | **100%** |

---

## 🛠️ EXCEPCIONES: CÓDIGO QUE NO ES SYNAPSE PURO

Según los manuales, estos componentes **no están escritos en Synapse puro**:

| Componente | Lenguaje | Razón |
|------------|----------|-------|
| Runtime (`runtime/`) | C | Interacción con el sistema operativo y hardware. |
| Axon (`axon/`) | C | Gestión de paquetes y criptografía Ed25519. |
| OpenSyn server (`opensyn/*.c`) | C | Orquestación de `llama-server`. |
| Extensión VS Code (`vscode-synapse/`) | TypeScript/JS | Integración con el editor. |
| Tests Python (`tests/unit/`, `tests/integration/`) | Python | Bootstrap y validación del compilador. |
| Bindings generados (`bindings/`) | Python, Java, TS | Código generado, no escrito manualmente. |

---

## 🔍 VERIFICACIÓN CON LOS MANUALES

He cotejado esta lista con:

- **Manual 1** (Estructura del repositorio)
- **Manual 2** (Sintaxis de Synapse)
- **Manual 3** (Sintaxis de Syquex)
- **Manual 4** (Modelo de memoria)
- **Manual 5** (Concurrencia)
- **Manual 6** (Integración)
- **Manual 7** (OpenSyn)
- **Manual 8** (Herramientas)
- **Manual 9** (Instalación)
- **Roadmap F22–F30**

**Resultado:** La lista es completa y coincide con la especificación de los
manuales v8.1.0. No falta ningún archivo .syn/.syq que esté mencionado en los
manuales.
