> Documento informativo. La fuente de verdad es `docs/manuales/`.
>
> **Mapa canónico:** [MANUAL 1](../../manuales/MANUAL 1.md) §1; [ROADMAP.md](../../../ROADMAP.md).
> **Vigencia:** histórico (v8.1.0); el roadmap vigente es `ROADMAP.md`.

# Visión General del Proyecto

## Roadmap del Ecosistema Synapse

### Estado Actual (v8.1.0)

| Fase | Estado | Descripción |
|------|--------|-------------|
| Fase 0-7 | ✅ Completada | Núcleo del compilador, runtime, herramientas |
| Fase 8-21 | ✅ Completada | Módulos avanzados del lenguaje |
| Fase 22-25 | ✅ Completada | Syquex y biblioteca estándar |
| Fase 26-27 | ✅ Completada | OpenSyn y herramientas de desarrollo |
| Fase 28-29 | ✅ Completada | Funcionalidades avanzadas |
| Fase 30 | ✅ Completada | Instalación unificada y distribución |

### Hitos Alcanzados

1. **Hito 1 (Fase 5):** Compilador auto-hospedado (bootstrap funcional)
2. **Hito 2 (Fase 7):** Soporte para LLVM y WASM
3. **Hito 3 (Fase 21):** Synapse completo (todos los módulos avanzados)
4. **Hito 4 (Fase 22):** Traductor Syquex funcional
5. **Hito 5 (Fase 24):** Biblioteca estándar de Syquex
6. **Hito 6 (Fase 26):** OpenSyn soporta Syquex
7. **Hito 7 (Fase 28):** Syquex certificado (v1.0)
8. **Hito 8 (Fase 30):** Instalador unificado (lanzamiento público)

## Arquitectura del Sistema

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                    ECOSISTEMA SYNAPSE                        │
├─────────────────┬─────────────────┬─────────────────────────┤
│    SYNAPSE      │    SYQUEX       │       OPENSYN           │
│  (Sistemas)     │  (Alto Nivel)   │      (IA Local)         │
├─────────────────┴─────────────────┴─────────────────────────┤
│                 COMPILADOR UNIFICADO                         │
│    Lexer → Parser → Analizador → Generador → Optimizador    │
├─────────────────────────────────────────────────────────────┤
│                    RUNTIME MODULAR                           │
│    memory.c │ concurrency.c │ io.c │ net.c │ crypto.c      │
├─────────────────────────────────────────────────────────────┤
│                 GESTOR DE PAQUETES AXON                      │
│           Seguridad Ed25519 │ Lockfile SHA-256               │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Compilación

```
Código Fuente (.syn / .syq)
        │
        ▼
┌───────────────┐
│     Lexer     │ ← Tokenización
└───────┬───────┘
        │
        ▼
┌───────────────┐
│     Parser    │ ← Análisis sintáctico
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   Analizador  │ ← Análisis semántico
│   Semántico   │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   Generador   │ ← Generación de código C/LLVM/WASM
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  Compilador   │ ← GCC/Clang/LLVM
│  (C/LLVM)     │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│   Binario     │ ← Ejecutable nativo
│   Nativo      │
└───────────────┘
```

## Estructura del Repositorio

```
proyecto_synapse/
├── nucleo/                  # Compilador nativo en Synapse (.syn)
├── runtime/                 # Runtime modularizado en C
│   └── core/                # memory.c, concurrency.c, io.c, net.c
├── std/                     # Librería estándar (.syn)
├── syquex/                  # Lenguaje de alto nivel
├── opensyn/                 # Servicio IA local
├── axon/                    # Runtime Axon (gestor de paquetes)
├── librerias/               # Librerías embebidas
├── compilador/              # Compilador Python (referencia)
├── scripts/                 # Scripts de build, test, release
├── .github/workflows/       # CI/CD: release matrix, cross-compile
├── docs/                    # Documentación
│   ├── book1-aprendizaje/   # Manual de aprendizaje
│   ├── book2-desarrollo/    # Guía para desarrolladores
│   └── manuales/            # Manuales oficiales (1–9, 31, 32)
├── tests/                   # Suites de prueba
├── instaladores/            # Instaladores multiplataforma
├── vscode-synapse/          # Extensión VS Code
├── main.py                  # Entry point compilador Python
├── VERSION                  # Versión canónica: 8.1.0
└── synapse.spdx.json        # SBOM SPDX 2.3
```

## Estándares del Proyecto

### Calidad de Código

- **Tests:** 667+ tests Python PASS
- **Bootstrap:** Stage1→Stage2→Stage3, diff=0 bytes
- **Fuzzing:** 500+ entradas, 0 crashes
- **Concurrencia:** 50 hilos, 13,004 msg/s, 0 deadlocks

### Seguridad

- **Firma Ed25519:** Todos los paquetes verificados
- **Zero-tolerance:** Sin dependencias opacas
- **Cero telemetría:** Sin conexiones en red ocultas

### Multiplataforma

- Windows x64 (MinGW)
- Linux x64 (gcc)
- Linux ARM64 (cross-compile)
- macOS ARM (Apple Silicon)

## Próximos Pasos

1. Revisa el [protocolo de trabajo](../../../AGENTS.md)
2. Explora el [índice informativo](../SUMMARY.md) y el [MANUAL 1](../../manuales/MANUAL 1.md)
3. Revisa los [Benchmarks](../06-referencia/benchmarks.md)

---

*Documento informativo; el roadmap vigente es `ROADMAP.md`.*
