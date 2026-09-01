# Synapse/OpenSyn v8.1.0

> **Lenguaje de sistemas nativo, compilado, auto-hospedado y verificado criptográficamente**
> **Estado:** **FASE 30 COMPLETADA** — Instalación Unificada y Distribución Final
> **Suite:** 667 tests Python PASS, bootstrap determinista, SBOM SPDX 2.3, firma Ed25519
> **Instaladores:** Windows, Linux, macOS con verificación Ed25519

---

## Insignias

| Calidad | Estado |
|---------|--------|
| **Tests Python** | 667/667 PASS (unitarios + semántica + integración) |
| **Bootstrap** | Stage1→Stage2→Stage3, **diff=0 bytes** (Manual 9 §9.7) |
| **Fuzzing** | 500+ entradas, **0 crashes** |
| **Concurrencia** | 50 hilos, 13,004 msg/s, **0 deadlocks** |
| **Determinismo** | SHA-256 idéntico en compilaciones repetidas |
| **Firma Ed25519** | Verificada + detección de manipulación |
| **SBOM SPDX 2.3** | Regenerado con v8.1.0 |
| **Multiplataforma** | Windows (MinGW), Linux (gcc), macOS (clang/clang ARM) |
| **Instaladores** | ✅ Windows (Inno Setup), Linux (Bash), macOS (.dmg) |

---

## Instalación Rápida

### Windows
```cmd
# Descargar e instalar
synapse-setup.exe
```

### Linux
```bash
# Instalación interactiva
curl -fsSL https://raw.githubusercontent.com/anomalyco/opencode/main/instaladores/linux/install.sh | bash

# O con opciones
./install.sh --opensyn    # Solo OpenSyn
./install.sh --ecosistema # Ecosistema completo
```

### macOS
```bash
# Crear instalador DMG
./instaladores/macos/create_dmg.sh

# Abrir DMG y arrastrar a Applications
```

**[Guía completa de instalación](./docs/guia_usuario_instaladores.md)**

---

## Quick Start

### Requisitos

- **GCC** (MinGW-w64 en Windows, gcc en Linux) o **Clang** (macOS)
- **Python 3.10+** (solo para desarrollo)

### 1. Compilar el runtime

```bash
gcc -c synapse_rt.c -o synapse_rt.o -lpthread -lm
gcc -c axon/axon_rt.c -o axon_rt.o -lpthread -lm
gcc -c axon/tweetnacl.c -o tweetnacl.o
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

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [`MANUAL 1.md` — Arquitectura del Lenguaje](./docs/manuales/MANUAL%201.md) | Arquitectura del lenguaje, filosofía de diseño |
| [`MANUAL 2.md` — Especificación Sintáctica](./docs/manuales/MANUAL%202.md) | Gramática EBNF, tipos, operadores |
| [`MANUAL 3.md` — Arquitectura del Compilador](./docs/manuales/MANUAL%203.md) | Pipeline 5 etapas, AST, tabla de símbolos |
| [`MANUAL 4.md` — Gestión de Memoria](./docs/manuales/MANUAL%204.md) | Ownership, borrowing, lifetimes |
| [`MANUAL 5.md` — Concurrencia](./docs/manuales/MANUAL%205.md) | Canales, hilos, sincronización |
| [`MANUAL 6.md` — Gestor de Paquetes Axon](./docs/manuales/MANUAL%206.md) | Axon, Ed25519, axon.lock |
| [`MANUAL 7.md` — Herramientas de Desarrollo](./docs/manuales/MANUAL%207.md) | LSP nativo, VS Code extension |
| [`MANUAL 8.md` — Backend y Generación de Código](./docs/manuales/MANUAL%208.md) | Generación C/LLVM/WASM |
| [`MANUAL 9.md` — Bootstrap, Pruebas y QA](./docs/manuales/MANUAL%209.md) | Bootstrap 3 etapas, CI/CD |
| [`ROADMAP.md`](./ROADMAP.md) | Roadmap de implementación F0–F30 |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | Guía de contribución |
| [`Guía de Instaladores`](./docs/guia_usuario_instaladores.md) | Guía completa de instalación |

---

## Características Clave

### Seguridad por Diseño

| Característica | Detalle |
|---------------|---------|
| **Ed25519** | Firmas obligatorias en paquetes (TweetNaCl) |
| **Zero-tolerance** | Autor vacío o .sig ausente → `ERR_AXON_COMPROMISED` |
| **Path traversal** | Bloqueo de `../` y rutas absolutas en TAR |
| **Lockfile** | `axon.lock` con SHA-256 — builds deterministas |
| **Contracts** | `requiere`/`garantiza` — aserciones en tiempo real |
| **ATP** | Motor de verificación formal en modo `--safe` |

### Rendimiento

| Componente | Métrica |
|-----------|---------|
| Runtime total | **< 139 KB** (Synapse RT + Axon + TweetNaCl) |
| Concurrencia | **50 hilos**, **0 deadlocks**, **13,004 msg/seg** |
| SIMD | SSE/AVX/AVX2 acceleration (`std.simd`) |
| Fuzzing | **500+ entradas, 0 crashes** |
| Determinismo | **SHA-256 idéntico** en compilaciones repetidas |
| Bootstrap | **diff 0 bytes** Stage 2 ↔ Stage 3 |

### Herramientas

| Herramienta | Descripción |
|-------------|-------------|
| **LSP Nativo** | Servidor JSON-RPC 2.0, binario nativo **sin Python** |
| **VS Code Extension** | Auto-detect del binario LSP |
| **IA Local (llama.cpp)** | Pipeline RAG + negociación dinámica n_ctx |
| **Shutdown Hooks** | Liberación forzosa RAM/VRAM en señales del SO |

### Multiplataforma

| Plataforma | Compilador | Estado |
|-----------|-----------|--------|
| Windows x64 | `gcc` (MinGW) | ✅ Instalador disponible |
| Linux x64 | `gcc` | ✅ Instalador disponible |
| Linux ARM64 | `aarch64-linux-gnu-gcc` | ✅ Cross-compile |
| macOS ARM (Apple Silicon) | `clang` | ✅ Instalador disponible |

---

## Suites de Validación

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

# Tests de instaladores
python -m pytest tests/installers/ -v
```

---

## Arquitectura del Repositorio

```
proyecto_synapse/
├── nucleo/                  # Compilador nativo en Synapse (.syn)
├── runtime/                 # Runtime modularizado en C
│   └── core/                # memory.c, concurrency.c
├── std/                     # Librería estándar (.syn)
├── librerias/               # Librerías embebidas
├── compilador/              # Compilador Python (referencia)
├── axon/                    # Runtime Axon (axon_rt.c, tweetnacl.c)
├── opensyn/                 # Servicio IA local
├── syquex/                  # Lenguaje de alto nivel
├── scripts/                 # Scripts de build, test, release
├── .github/workflows/       # CI/CD: release matrix, cross-compile
├── docs/manuales/           # Los 9 manuales de ingeniería
├── docs/book.toml           # Configuración mdBook
├── instaladores/            # Instaladores multiplataforma
│   ├── windows/             # Inno Setup
│   ├── linux/               # Bash installer
│   ├── macos/               # DMG creator
│   └── common/              # Verificación Ed25519, auto-actualización
├── vscode-synapse/          # Extensión VS Code
├── tests/                   # Suites de prueba
├── main.py                  # Entry point compilador Python
├── VERSION                  # Versión canónica: 8.1.0
└── synapse.spdx.json        # SBOM SPDX 2.3
```

---

## CI/CD

| Workflow | Trigger | Propósito |
|----------|---------|-----------|
| `ci-tests.yml` | Push/PR a `main` | Tests multiplataforma, linting, bootstrap |
| `release-installers.yml` | Tag `v*` | Build instaladores y publicar en Releases |
| `release_matrix.yml` | Tag `v*` | Build binarios multiplataforma |
| `deploy-docs.yml` | Push a `main` | Despliegue mdBook a GitHub Pages |

---

## Licencia

Distribuido bajo licencia **MIT**. Consulte el archivo [`LICENSE`](./LICENSE) para términos completos.

---

**Synapse/OpenSyn v8.1.0** — *Lanzamiento público con instalación unificada multiplataforma.*
