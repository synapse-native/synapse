# Synapse/OpenSyn v5.0

> **Lenguaje de sistemas nativo, compilado, auto-hospedado y verificado criptograficamente**
> **Estado:** **PRODUCTION-READY** — 523 tests Python + 52 C/nativos, 0 errores GCC, 0 crashes fuzzing
> **IA Nativa:** Pipeline RAG quirurgico + negociacion dinamica n_ctx + shutdown hooks verificados

---

## 🏆 Insignias

| Calidad | Estado |
|---------|--------|
| **Tests Python** | 523 collected (523 passed, 5 skipped) |
| **Tests C/Nativos** | 52/52 passed |
| **GCC** | 0 errores, 0 warnings en modulos IA |
| **Bootstrap** | Stage0→Stage1→Stage2→Stage3, diff=0 bytes |
| **Fuzzing** | 500+ entradas, **0 crashes** |
| **Concurrencia** | 10,000 hilos, **0 deadlocks, 0 fugas** |
| **Axon** | 19/19 E2E — Ed25519, TAR, SemVer, axon.lock |
| **LSP Nativo** | 5/5 tests — binario nativo sin Python |
| **IA Local** | RAG quirurgico + n_ctx dinamico + shutdown hooks |
| **Runtime** | < 139 KB |
| **Multiplataforma** | Windows (gcc), Linux (gcc), macOS (clang) |

---

## 📋 Documentación Maestra

| Documento | Descripcion |
|-----------|-------------|
| [`ARCH_ESPECIFICACION.md`](./ARCH_ESPECIFICACION.md) | Arquitectura del compilador, AST aplanado `SemNodo[]`, pipeline nativa |
| [`MANUAL_LENGUAJE.md`](./MANUAL_LENGUAJE.md) | Sintaxis, tipos seguros, contratos logicos, canales tipados |
| [`AXON_SPEC.md`](./AXON_SPEC.md) | Especificacion del gestor de paquetes Axon |
| [`LSP_NATIVO.md`](./LSP_NATIVO.md) | Servidor LSP nativo + integracion VS Code + IA local |
| [`GUIA_DESPLIEGUE.md`](./GUIA_DESPLIEGUE.md) | Despliegue del ejecutable unico, compilacion, instalacion |
| [`ROADMAP.md`](./ROADMAP.md) | Historial completo de desarrollo y fases F0–F19 |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | Guia de contribucion |
| [`BENCHMARK_RESULTS.md`](./BENCHMARK_RESULTS.md) | Benchmark completo: JSON parsing, SIMD, canales, throughput |
| [`docs/especificacion_opensyn.md`](./docs/especificacion_opensyn.md) | Especificacion OpenSyn v5.0 — motor IA local y migracion automatica |
| [`docs/migracion_python_synapse.md`](./docs/migracion_python_synapse.md) | Guia de migracion Python → Synapse v5.0 |

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

### ⚡ Rendimiento

| Componente | Métrica |
|-----------|---------|
| Runtime total | **< 139 KB** (Synapse RT + Axon + TweetNaCl) |
| Concurrencia | **10,000 hilos**, **0 deadlocks**, **8,083 msg/seg** |
| SIMD | SSE/AVX/AVX2 acceleration (`std.simd`) |
| Fuzzing | **500+ entradas, 0 crashes** |

### 🛠️ Herramientas

| Herramienta | Descripción |
|-------------|-------------|
| **LSP Nativo** | Servidor JSON-RPC 2.0, binario nativo **sin Python** |
| **VS Code Extension** | `vscode-synapse/` — auto-detect del binario LSP |
| **IA Local Nativa (llama.cpp)** | Pipeline RAG quirúrgico + negociación dinámica n_ctx: `synapse/aiExplain`, `synapse/aiComplete` |
| **Shutdown Hooks** | `synapse_shutdown_hook()` — atexit + signals (CTRL_C_EVENT/SIGINT/SIGTERM) — liberación forzosa RAM/VRAM |

### 🌐 Multiplataforma

| Plataforma | Compilador | Estado |
|-----------|-----------|--------|
| Windows | `gcc` (MinGW) | ✅ Probado |
| Linux | `gcc` | ✅ Soporte |
| macOS (Intel) | `clang` | ✅ Auto-detect |
| macOS (Apple Silicon) | `clang` | ✅ Auto-detect |

---

## 📦 Binarios

| Binario | Propósito | Tamaño |
|---------|-----------|--------|
| `test_lsp_bin.exe` | Servidor LSP nativo | ~909 KB |
| `synapse_bootstrap.exe` | Compilador auto-hospedado | ~738 KB |
| `tests/test_axon_e2e_native.exe` | Suite E2E Axon | Compilado desde fuente |
| `tests/stress/stress_concurrencia.exe` | Test de estrés concurrencia | Compilado desde fuente |

---

## 🔬 Suites de Validación

```bash
# Tests unitarios
python -m pytest tests/ -q

# Fuzzing destructivo
python tests/fuzz/fuzz_engine.py --iterations 500

# Prueba de estrés (10,000 hilos)
python tests/stress/run_stress.py

# Axon E2E (Python)
python tests/test_axon_e2e.py

# LSP Nativo (5/5 tests)
pytest tests/integration/test_lsp_native.py -v
```

---

## 🏗️ Arquitectura del Repositorio

```
proyecto_synapse/
├── nucleo/                  # Compilador nativo en Synapse (.syn)
│   ├── tokens.syn           # Definición de tokens
│   ├── lexer.syn            # Tokenizador
│   ├── parser.syn           # Parser recursivo descendente
│   ├── analizador_semantico.syn  # Validación semántica
│   ├── generator.syn        # Generador de código C
│   ├── principal.syn        # Pipeline nativa (orquestador)
│   └── lsp.syn              # Servidor LSP nativo
├── compilador/              # Compilador Python (referencia)
├── axon_rt.c                # Runtime de Axon (HTTP, TAR, Ed25519)
├── synapse_rt.c             # Runtime base (canales, SIMD, SHA-256, GGUF)
├── tweetnacl.c / .h         # Criptografía Ed25519
├── main.py                  # Compilador (entry point Python)
├── vscode-synapse/          # Extensión VS Code
│   ├── extension.js         # Cliente LSP nativo
│   └── package.json         # Configuración
├── tests/                   # Suites de prueba
│   ├── fuzz/                # Fuzzing destructivo
│   ├── stress/              # Prueba de estrés concurrencia
│   └── integration/         # Tests de integración LSP
├── ARCH_ESPECIFICACION.md   # Documentación arquitectónica
├── MANUAL_LENGUAJE.md       # Manual del lenguaje
├── AXON_SPEC.md             # Especificación de Axon
└── LSP_NATIVO.md            # Referencia del LSP
```

---

## 🧠 IA Local Nativa (llama.cpp) — v2.2.2

**Pipeline RAG Quirúrgico + Negociación Dinámica n_ctx**

| Componente | Descripción |
|------------|-------------|
| **Endpoint** | `synapse/aiExplain` — Explica código en contexto (línea actual, AST, diagnósticos) |
| **Pipeline RAG** | Ventana 11 líneas (±5), línea exacta, tipo nodo AST, diagnósticos recientes |
| **Negociación n_ctx** | Lee `n_ctx` desde `/props`, calcula `max_tokens = clamp(n_ctx * 0.3, 64, 2048)` |
| **Prompt Controlado** | `synapse_rag_construir_prompt()` con presupuesto de tokens inyectado |
| **Respuesta** | Incluye `n_ctx` y `max_tokens` usados en metadata JSON-RPC |

**Shutdown Hooks Garantizados**

| Hook | Plataforma | Acción |
|------|------------|--------|
| `synapse_shutdown_hook()` | Windows | `SetConsoleCtrlHandler` → `CTRL_C_EVENT`, `CTRL_CLOSE_EVENT`, `CTRL_LOGOFF_EVENT`, `CTRL_SHUTDOWN_EVENT` → `TerminateProcess` + `EmptyWorkingSet` + `cuDevicePrimaryCtxRelease` |
| `synapse_shutdown_hook()` | POSIX | `signal(SIGINT/SIGTERM/SIGHUP)` → `SIGKILL` + `waitpid` + `malloc_trim(0)` + `cuDevicePrimaryCtxRelease` vía `dlopen` |

**Validado:** 7/7 tests `synapse_shutdown_hook`, 9/9 tests `llama_client`, 4/4 tests `synapse_rag` — **sin leaks, sin huérfanos**.

---

## 📜 Licencia

Este proyecto se distribuye bajo licencia de código abierto. Consulte el archivo de licencia para más detalles.

---

**Synapse v2.2.2** — *IA Nativa Integrada y Saneamiento Estructural.*
