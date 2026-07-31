# Synapse/OpenSyn v5.1.1-industrial

> **Lenguaje de sistemas nativo, compilado, auto-hospedado y verificado criptográficamente**
> **Estado:** **CERTIFICADO PRODUCCIÓN** — 125/125 tests Python, bootstrap determinista, SBOM SPDX 2.3, firma Ed25519
> **Auditoría:** Fase 0 a Fase 20 certificada punto por punto bajo estándares industriales

---

## 🏆 Insignias

| Calidad | Estado |
|---------|--------|
| **Tests Python** | 125/125 PASS (unitarios + semántica) |
| **Tests Integración** | 337/337 PASS |
| **Tests Nativos C** | 1/1 PASS |
| **GCC/Clang** | 0 errores, 0 warnings |
| **Bootstrap** | Stage0→Stage1→Stage2→Stage3, **diff=0 bytes** |
| **Fuzzing** | 500+ entradas, **0 crashes** |
| **Concurrencia** | 50 hilos, 13,004 msg/s, **0 deadlocks** |
| **Determinismo** | SHA-256 idéntico en compilaciones repetidas |
| **Firma Ed25519** | Verificada + detección de manipulación |
| **SBOM SPDX 2.3** | 3,023 archivos escaneados |
| **SLSA Level 3** | Attestación firmada |
| **Runtime** | < 139 KB |
| **Multiplataforma** | Windows (MinGW), Linux (gcc), macOS (clang/clang ARM) |

---

## 📋 Documentación Maestra

| Documento | Descripción |
|-----------|-------------|
| [`MANUAL_1.md` — Arquitectura del Lenguaje](./docs/manuales/MANUAL_1.md) | Arquitectura del lenguaje, filosofía de diseño, hoja de ruta |
| [`MANUAL_2.md` — Especificación Sintáctica](./docs/manuales/MANUAL_2.md) | Gramática EBNF, tipos, operadores, contratos |
| [`MANUAL_3.md` — Arquitectura del Compilador](./docs/manuales/MANUAL_3.md) | Pipeline 5 etapas, AST, tabla de símbolos, motor ATP |
| [`MANUAL_4.md` — Gestión de Memoria y Ownership](./docs/manuales/MANUAL_4.md) | Ownership, borrowing, lifetimes, pool allocator |
| [`MANUAL_5.md` — Concurrencia y Comunicación](./docs/manuales/MANUAL_5.md) | Canales, hilos, sincronización, federated learning |
| [`MANUAL_6.md` — Gestor de Paquetes Axon](./docs/manuales/MANUAL_6.md) | Axon, Ed25519, axon.lock, TAR |
| [`MANUAL_7.md` — Herramientas de Desarrollo](./docs/manuales/MANUAL_7.md) | LSP nativo, VS Code extension, CLI |
| [`MANUAL_8.md` — Backend y Generación de Código](./docs/manuales/MANUAL_8.md) | Generación C/LLVM/WASM, orden alfabético, PGO |
| [`MANUAL_9.md` — Bootstrap, Pruebas y QA](./docs/manuales/MANUAL_9.md) | Bootstrap 3 etapas, CI/CD, sanitizadores, SBOM |
| [`ROADMAP.md`](./ROADMAP.md) | Historial completo de desarrollo y fases F0–F20 |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | Guía de contribución |
| [`BENCHMARK_RESULTS.md`](./BENCHMARK_RESULTS.md) | Benchmark completo: JSON parsing, SIMD, canales, throughput |
| [`DOCS/`](./docs/) | Especificaciones adicionales y guías de migración |

---

## 🚀 Quick Start

### Requisitos

- **GCC** (MinGW-w64 en Windows, gcc en Linux) o **Clang** (macOS)
- **Python 3.10+** (solo para desarrollo, no para producción)

### 1. Compilar el runtime

```bash
gcc -c synapse_rt.c -o synapse_rt.o -lpthread -lm
gcc -c axon_rt.c -o axon_rt.o -lpthread -lm
gcc -c tweetnacl.c -o tweetnacl.o
```

### 2. Escribir tu primer programa

Crea `hola.syn`:

```synapse
#lang: es
importar std.io

funcion principal() -> nulo:
    escribir_linea("Hola, Silicio. El mundo exterior te saluda.")
```

### 3. Compilar y ejecutar

```bash
python main.py hola.syn
./hola.exe
```

### 4. Gestor de paquetes Axon

```bash
synapse.exe axon init
synapse.exe axon fetch --online
```

---

## ✨ Características Clave

### 🔐 Seguridad por Diseño

| Característica | Detalle |
|---------------|---------|
| **Ed25519** | Firmas obligatorias en paquetes (TweetNaCl) |
| **Zero-tolerance** | Autor vacío o .sig ausente → `ERR_AXON_COMPROMISED` |
| **Path traversal** | Bloqueo de `../` y rutas absolutas en TAR |
| **Lockfile** | `axon.lock` con SHA-256 — builds deterministas |
| **Contracts** | `requiere`/`garantiza` — aserciones en tiempo real |
| **ATP** | Motor de verificación formal en modo `--safe` |

### ⚡ Rendimiento

| Componente | Métrica |
|-----------|---------|
| Runtime total | **< 139 KB** (Synapse RT + Axon + TweetNaCl) |
| Concurrencia | **50 hilos**, **0 deadlocks**, **13,004 msg/seg** |
| SIMD | SSE/AVX/AVX2 acceleration (`std.simd`) |
| Fuzzing | **500+ entradas, 0 crashes** |
| Determinismo | **SHA-256 idéntico** en compilaciones repetidas |
| Bootstrap | **diff 0 bytes** Stage 2 ↔ Stage 3 |

### 🛠️ Herramientas

| Herramienta | Descripción |
|-------------|-------------|
| **LSP Nativo** | Servidor JSON-RPC 2.0, binario nativo **sin Python** |
| **VS Code Extension** | `vscode-synapse/` — auto-detect del binario LSP |
| **IA Local (llama.cpp)** | Pipeline RAG + negociación dinámica n_ctx |
| **Shutdown Hooks** | Liberación forzosa RAM/VRAM en señales del SO |

### 🌐 Multiplataforma

| Plataforma | Compilador | Estado |
|-----------|-----------|--------|
| Windows x64 | `gcc` (MinGW) | ✅ Probado + Instalador |
| Linux x64 | `gcc` | ✅ Release matrix |
| Linux ARM64 | `aarch64-linux-gnu-gcc` | ✅ Cross-compile |
| macOS ARM (Apple Silicon) | `clang` | ✅ Release matrix |

---

## 🔬 Suites de Validación

```bash
# Tests unitarios y semántica
python -m pytest tests/unit/ tests/test_semantico.py -v

# Tests de integración
python -m pytest tests/integration/ -v --timeout=300

# Fuzzing destructivo
python tests/fuzz/fuzz_engine.py --iterations 500

# Prueba de estrés concurrencia
python tests/stress/run_stress.py

# Tests nativos C
python scripts/run_native_tests.py

# Suite completa release matrix
python -m pytest tests/integration/test_release_matrix.py -v
```

---

## 🏗️ Arquitectura del Repositorio

```
proyecto_synapse/
├── nucleo/                  # Compilador nativo en Synapse (.syn)
│   ├── tokens.syn           # Definición de tokens
│   ├── lexer.syn            # Tokenizador
│   ├── parser.syn           # Parser recursivo descendente
│   ├── analizador_semantico.syn  # Validación semántica (3 pasadas)
│   ├── generator.syn        # Generador de código C/LLVM/WASM
│   ├── principal.syn        # Pipeline nativa (orquestador)
│   ├── lsp.syn              # Servidor LSP nativo
│   ├── verificador_formal.syn  # Motor ATP
│   └── cache.syn            # Caché incremental SHA-256
├── runtime/                 # Runtime modularizado en C
│   ├── core/                # memory.c, concurrency.c, io.c
│   ├── net/                 # http.c
│   ├── quantum/             # matrix.c
│   └── federated/           # aggregator.c
├── std/                     # Librería estándar (.syn)
├── compilador/              # Compilador Python (referencia)
├── axon/                    # Runtime Axon
├── opensyn/                 # Servicio IA local
├── scripts/                 # Scripts de build, test, release
├── .github/workflows/       # CI/CD: release matrix, cross-compile, instalador
├── docs/manuales/          # Los 9 manuales de ingeniería (MANUAL_1.md..MANUAL_9.md)
├── vscode-synapse/          # Extensión VS Code
│   ├── extension.js         # Cliente LSP nativo
│   └── package.json         # Configuración
├── tests/                   # Suites de prueba
│   ├── unit/                # Tests unitarios Python
│   ├── integration/         # Tests de integración
│   ├── fuzz/                # Fuzzing destructivo
│   ├── synapse/             # Tests nativos C Synapse
│   └── micro_bootstrap/     # Tests de bootstrap
├── nucleo/principal.syn.json  # Manifiesto del compilador
├── axon.toml                # Configuración Axon
├── synapse_rt.c/.h          # Runtime base
├── tweetnacl.c/.h           # Criptografía Ed25519
├── main.py                  # Entry point compilador Python
├── cli.py                   # CLI unificada
├── VERSION                  # Versión canónica: 5.1.1-industrial
├── instalador_synapse.iss   # Inno Setup installer
└── synapse.spdx.json        # SBOM SPDX 2.3
```

---

## 📜 Licencia

Distribuido bajo licencia **MIT**. Consulte el archivo [`LICENSE`](./LICENSE) para términos completos.

---

**Synapse/OpenSyn v5.1.1-industrial** — *Auditado, certificado y sellado bajo estándares de ingeniería de grado industrial.*
