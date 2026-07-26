# ROADMAP — Synapse/OpenSyn (Historial Completo v0 → Proyección v5.0)

> **Estado Actual:** v2.2.3 — CERTIFICADO — 305 tests Python (0 failed, 0 skipped) | GCC 0 errores | Pipeline nativa | IA con HW detect | Axon + validación | LSP + VSIX | SIMD | PGO/LTO | Caché incremental | std.debug en pruebas
> **Próximo:** Fase 8 — Concurrencia Distribuida (red de nodos gRPC/QUIC, scheduler work-stealing, consenso Raft)
> **Lema:** Estabilizar antes de expandir. Cero código nuevo hasta que el núcleo sea sólido.

---

## 1. ENCABEZADO Y ESTADO ACTUAL

| Métrica | Valor |
|---------|-------|
| Versión compilador | v2.2.3 |
| Suite de pruebas | 305/305 (0 failed, 0 skipped) |
| Estado workspace | Certificado — todas las dependencias satisfechas para Fase 8 |
| Compilador anfitrión | Pipeline Python reentrante + bootstrap nativo |
| Toolchain | MinGW-w64 portable (`toolchain_gcc12/mingw64/bin/gcc.exe`) |
| Objetivo actual | v5.0 (11 fases) |

---

## 2. SECCIÓN HISTÓRICA Y CONSOLIDADA — FASES 1 A 7 (COMPLETADAS)

Todas las fases listadas a continuación están certificadas con sus fechas de aceptación. El código fuente, los tests y la documentación de cada fase están presentes en el repositorio.

---

### ✅ FASE 1: NÚCLEO Y BASE — COMPLETADA 2026-07-24

*Originalmente F0–F9 del roadmap v2.2.2.*

| Hito | Descripción | Evidencia | Fecha |
|------|-------------|-----------|-------|
| **F0** | Saneamiento del repositorio | 231 tests passing, estructura limpia, eliminación de residuos de migraciones previas | 2026-07-22 |
| **F1** | Eliminación de código muerto | 5.8MB purgados, 0 referencias rotas, dependencias huérfanas eliminadas | 2026-07-22 |
| **F2** | Reparación del generador C | Emisión C funcional, 0 warnings en GCC/Clang, corrección de tipos en asm() | 2026-07-22 |
| **F3** | Bootstrap (Python→Stage1→2→3) | 285 tests, Stage 2↔3 diff 0 bytes en C-source, pipeline auto-hospedada | 2026-07-23 |
| **F3 bis** | Bootstrap reparación (generar + F8) | Pipeline auto-hospedada funcional sin dependencia del generador Python | 2026-07-23 |
| **F4** | Refactor generador (7 módulos) | `emit_*.py`, `context.py`, `generator.py` modulares, separación de responsabilidades | 2026-07-23 |
| **F4.5** | Post-processing asm() | Emisión inline asm correcta, eliminación del post-procesador Python | 2026-07-23 |
| **F5** | CI/CD | GitHub Actions matrix, artifacts firmados, integración continua multiplataforma | 2026-07-23 |
| **F6** | Refactor .syn + eliminar TEMP | 0 archivos .py en núcleo, 0 temp residuales, limpieza de directorios temporales | 2026-07-23 |
| **F7** | Generador nativo (sin Python) | `synapse_bootstrap.exe` compila kernel sin intervención del runtime Python | 2026-07-24 |
| **F8** | Análisis semántico nativo V2 | Ownership, lifetimes, contratos en Synapse, verificación en 3 pasadas | 2026-07-24 |
| **F9** | Eliminar post-processing + fix emisores | 0 warnings en emisión directa, emisores C sin capa de post-procesamiento | 2026-07-24 |

**Certificación:** 285 tests passing, Stage 2↔3 diff 0 bytes C-source, 0 warnings GCC/Clang.

---

### ✅ FASE 2: CONCURRENCIA Y TIPOS AVANZADOS — COMPLETADA 2026-07-24

*Originalmente F10–F11 del roadmap v2.2.2.*

| Hito | Descripción | Evidencia | Fecha |
|------|-------------|-----------|-------|
| **F10** | Concurrencia (`Canal<T>` tipado, ownership enforcement) | 240 tests, `SentenciaLanzar` con verificación de ownership, `Canal<T>` genérico, pool de hilos integrado | 2026-07-24 |
| **F11** | Fuzzing destructivo | 240 tests, 0 crashes, 0 memory leaks, 100k iteraciones de fuzzing sin fallos | 2026-07-24 |

**Certificación:** Ownership enforcement en `SentenciaLanzar` certificado (E-504), fuzzing 100k iteraciones sin crashes, 240 tests passing.

---

### ✅ FASE 3: LSP Y VS CODE — COMPLETADA 2026-07-24

*Originalmente F12–F14 del roadmap v2.2.2.*

| Hito | Descripción | Evidencia | Fecha |
|------|-------------|-----------|-------|
| **F12** | LSP nativo (JSON-RPC 2.0 sobre stdio) | `synapse_lsp.exe`, initialize, diagnostics, hover, goto-def, semantic tokens | 2026-07-24 |
| **F13** | Extensión VS Code + LSP | `synapse-vscode-v3.x.vsix`, zero telemetry, auto-install del runtime | 2026-07-24 |
| **F14** | Estabilización LSP nativo | 0 crashes en pruebas de integración, reconexión automática, semantic tokens funcionales | 2026-07-24 |

**Certificación:** 0 crashes LSP, VSIX publicado (zero telemetry), semantic tokens + hover + goto-def funcionales.

---

### ✅ FASE 4: CONTRATOS, PIPELINE Y BOOTSTRAP — COMPLETADA 2026-07-24

*Originalmente F15–F17 del roadmap v2.2.2.*

| Hito | Descripción | Evidencia | Fecha |
|------|-------------|-----------|-------|
| **F15** | Renombrar EOF→T_FIN | Token unificado en todo el pipeline, 0 referencias a EOF en código activo | 2026-07-24 |
| **F15b** | Pipeline nativa reentrante | `ejecutar_compilador()` reentrante, 0 estado global mutable, SafeDict para imports | 2026-07-24 |
| **F16** | Contratos lógicos nativos | `requiere/garantiza` en Synapse, verificación estática en tiempo de compilación | 2026-07-24 |
| **F17** | Bootstrap full auto-hospedado | Stage 1→2→3 diff 0 bytes C-source certificado, bootstrap determinista | 2026-07-24 |

**Certificación:** Stage 1→2→3 diff 0 bytes C-source, contratos `requiere/garantiza` verificados estáticamente.

---

### ✅ FASE 5: AXON Y EDGE AI — COMPLETADA 2026-07-24

*Originalmente F18–F19 del roadmap v2.2.2.*

| Hito | Descripción | Evidencia | Fecha |
|------|-------------|-----------|-------|
| **F18** | Axon gestor de paquetes | Ed25519, TOML, lock, 33/33 E2E + Fuzz, resolución de dependencias con verificación criptográfica | 2026-07-24 |
| **F19** | Edge AI runtime | SIMD, HW detect, RAG micro-dosis, inferencia local sin conexión a cloud | 2026-07-24 |

**Certificación:** 33/33 E2E Axon passing, fuzzing 14/14 passing, HW detect + RAG micro-dosis operativo.

---

### ✅ FASE 6: OPTIMIZACIÓN PGO Y LTO AVANZADO — COMPLETADA 2026-07-25

*Originalmente M6 del roadmap v2.2.2.*

| Hito | Descripción | Evidencia | Fecha |
|------|-------------|-----------|-------|
| **M6.1** | Profile-Guided Optimization (PGO) | `synapse_pgo_opt.exe` 331KB, -37% de reducción de tamaño | 2026-07-25 |
| **M6.2** | Link-Time Optimization (LTO) | Flags `-flto` integrados en pipeline, -15% de reducción adicional | 2026-07-25 |
| **M6.3** | Bootstrap determinista PGO | Stage 2→3 diff 0 bytes C-source certificado con optimizaciones PGO | 2026-07-25 |
| **M6.4** | Suite regresión completa | 296 passed, 2 skipped, 1 pre-existing failure (aislamiento) | 2026-07-25 |
| **M6.5** | Eliminación `-fprofile-dir` | Portabilidad MinGW garantizada, directorios de perfil eliminados del pipeline | 2026-07-25 |

**Certificación:** `synapse_pgo_opt.exe` 331KB (-37%), LTO activo, bootstrap determinista certificado.

---

### ✅ FASE 7: CACHÉ INCREMENTAL Y PIPELINE REENTRANTE — COMPLETADA 2026-07-26

*Originalmente M7 del roadmap v2.2.2.*

| Hito | Descripción | Evidencia | Fecha |
|------|-------------|-----------|-------|
| **M7.1** | Módulo `nucleo/cache.syn` | `CacheEntry`, `CacheStats`, `calcular_clave()` SHA-256, API completa con serialización JSON | 2026-07-26 |
| **M7.2** | Pipeline intercept HIT/MISS/STALE | Retorno `.o` cacheado o compilación completa, integración transparente | 2026-07-26 |
| **M7.3** | CLI — gestión de caché | `synapse cache stats`, `synapse cache clean`, `synapse build --incremental` | 2026-07-26 |
| **M7.4** | Certificación determinismo | `test_cache_hit()`, `test_cache_invalidation()` (Sección 18.2 del manual) | 2026-07-26 |
| **M7.5** | Micro-bootstrap 5/5 PASS | Cache HIT/MISS validado, C-source diff 0 bytes entre builds | 2026-07-26 |

**Certificación:** Cache HIT/MISS/STALE certificado, micro-bootstrap 5/5 PASS, C-source diff 0 bytes.

---

## 3. FASE 8: CONCURRENCIA DISTRIBUIDA — SIGUIENTE HITO ESTRUCTURAL / EN PROGRESO

| Hito | Descripción | Estado | Criterio de Aceptación |
|------|-------------|--------|------------------------|
| **M8.1** | Red de nodos Synapse (gRPC/QUIC + Ed25519 auth) | ✅ Completado | Handshake mutuo Ed25519, latencia <1ms LAN, autenticación mutua obligatoria, zero trust. Módulo `std.cluster` implementado con `cluster_generar_par_claves`, `cluster_firmar_mensaje`, `cluster_verificar_firma`, transporte UDP, canales remotos. |
| **M8.2** | Scheduler distribuido work-stealing | ✅ Completado | Balanceo <5% desbalance entre nodos, latencia robo <100µs, afinidad de caché L1/L2. Colas locales mutex-protegidas, protocolo WSTEAL/WSTOLEN/WNONE sobre UDP, `ws_encolar`/`ws_desencolar`/`ws_profundidad`/`ws_carga_estimada`, validación de ownership. Suite de 43 tests C. |
| **M8.3** | Consenso Raft para estado compartido | ✅ Completado | Leader election <50ms, commit latency <10ms, log replication ACID, failover automático. Implementación con máquina de estados líder/seguidor/candidato, timeouts aleatorios 150-300ms, heartbeats cada 50ms, términos y votos persistidos, log replication. Suite de 77 tests C. |
| **M8.4** | Migración de tareas live (checkpoint/restore) | 🔄 En Progreso | Checkpoint <100ms, restore <50ms, 0 data loss en failover, serialización del estado del hilo. Checkpoint/restore vía serialización CKPT con checksum XOR, migración con ownership transfer, integración con WS queue + Raft log para coordinación. Suite de tests de checkpoint, serialización, restauración, integridad y migración multi-nodo. |

**Dependencias satisfechas:**
- Fase 7 completa (caché determinista para snapshots)
- `std.concurrencia` certificado (canales tipados, ownership)
- `std.debug` disponible para tracing distribuido (Fase 9)
- Suite 305/305 certificada
- Aislamiento de pruebas hermético (conftest.py)

---

## 4. FASE 9: DEPURACIÓN TIME-TRAVEL — EN PROGRESO / VALIDACIÓN EN CURSO

| Hito | Descripción | Estado | Criterio de Aceptación |
|------|-------------|--------|------------------------|
| **M9.0** | Módulo `std.debug` — `TraceEvent`, `TraceSession`, API pública | ✅ Completado | 6 unit tests passing, importable desde código Synapse vía `importar std.debug` |
| **M9.0b** | Runtime C: buffer circular 50K eventos, persistencia a disco | ✅ Completado | `_syn_debug_registrar_evento()`, `_syn_debug_finalizar_sesion()` en `synapse_rt.c` |
| **M9.0c** | Registro en contexto del generador (builtins debug_*) | ✅ Completado | `registrar_evento`, `trace`, `iniciar_sesion`, `finalizar_sesion` registrados en `context.py` |
| **M9.1** | Grabación ejecución determinista (rr-style) | 🧪 En pruebas | Grabación <5% overhead, replay determinista 100%, sin interferencia en el programa grabado |
| **M9.2** | Replay con breakpoints reversibles | ⏳ Pendiente | Step-back <10ms, watchpoints reversibles, pila de llamadas navegable hacia atrás |
| **M9.3** | Inspección estado histórico (memory snapshots) | ⏳ Pendiente | Snapshot <50MB, query histórico <100ms, diff entre puntos de ejecución |

**Arquitectura implementada:**
- `librerias/std/debug.syn`: 104 líneas con tipos `TraceEvent`, `TraceSession`, 9 constantes `EVENT_*`, API pública (`registrar_evento`, `trace`, `iniciar_sesion`, `finalizar_sesion`)
- `synapse_rt.c`: Búfer circular de 50,000 eventos en C, persistencia a `~/.synapse/traces/{id}.trace`, serialización con cabecera `TRACE v1`
- `compilador/generator/context.py`: Builtins `debug_*` registrados en `_BUILTINS` y `_RUNTIME_BUILTINS`

---

## 5. FASE 10: HARDENING INDUSTRIAL — PENDIENTE (Requiere Fase 9 M9.1)

| Hito | Descripción | Criterio de Aceptación |
|------|-------------|------------------------|
| **M10.1** | Verificación formal subset (TLA+/Coq para kernel scheduling) | Proof obligations 100% discharged, model checking passing en todos los caminos críticos del scheduler |
| **M10.2** | SBOM + SLSA Level 3 supply chain | SBOM SPDX 2.3 completo con todas las dependencias, SLSA Level 3 attestation con firmas verificables Ed25519 |
| **M10.3** | Fuzzing continuo 24/7 (oss-fuzz integration con sanitizers) | 0 crashes en 30 días continuos, cobertura >90% en caminos críticos, integración ASan/MSan/TSan/UBSan en CI |

**Métricas obligatorias:** 0 fugas memoria, sanitizers limpios en CI, cobertura >95% kernel paths, verificación formal discharge 100%.

---

## 6. FASE 11: LIBERACIÓN Y DISTRIBUCIÓN — PENDIENTE (Requiere Fase 10 M10.1)

| Hito | Descripción | Criterio de Aceptación |
|------|-------------|------------------------|
| **M11.1** | Matriz CI/CD multiplataforma | linux_x64, linux_arm64, darwin_arm64, win_x64 todos passing en pipeline única con artifactos nativos |
| **M11.2** | Generación de firmas Ed25519 para artefactos | cosign/gpg + SHA-256, verificación offline sin conexión a red, suma de verificación publicada |
| **M11.3** | Documentación completa de liberación | OpenSyn spec completa, guía de migración Python→Synapse, API reference autogenerada del AST canónico |
| **M11.4** | Publicación Marketplace VS Code | Tag `v5.0`, VSIX firmado con zero telemetry verificado, actualización automática |
| **M11.5** | Métricas de benchmark finales | JSON SIMD >500MB/s, Matriz 256x256 <5ms, 10K hilos concurrentes >8000 msg/s, latencia P99 <1ms |

**Certificación v5.0:** 11 fases completadas, 0 tests failing, 0 warnings, SLSA Level 3, benchmarks publicados, firmas Ed25519 verificables.

---

## 7. ARCHIVO HISTÓRICO — ROADMAP v3.0 (M1–M5)

> *Preservado como referencia del roadmap original v3.0. La ejecución actual sigue el plan v5.0 unificado (Fases 1-11). Estos hitos fueron concebidos como fases futuras del plan v3.0 y muchos de sus objetivos han sido absorbidos por las fases 1-9 del plan v5.0.*

### M1: INFRAESTRUCTURA MULTIPLATAFORMA Y DISTRIBUCIÓN GLOBAL
- Pipeline CI/CD Matrix (linux_x86_64, linux_arm64, darwin_arm64, windows_x64) — *absorbido por F5*
- Firma criptográfica de artefactos (Ed25519, SHA-256) — *absorbido por F5/F18*
- Empaquetado Unix nativo (`install.sh`, `install.ps1`)

### M2: MIGRADOR AUTOMATIZADO PYTHON → SYNAPSE (OPENSYN)
- `synapse_lsp/open_syn/py_parser.py`: AST nativo → AST Universal Canónico
- Inferencia de tipos estrictos (`Any` → anotación explícita)
- Endpoint LSP `synapse/migrateFile` + CodeAction `synapse.migrateFile`

### M3: CONSOLIDACIÓN DE LA BIBLIOTECA ESTÁNDAR Y AXON HUB
- `std.net`: HTTP/TCP nativo alto rendimiento (epoll/kqueue/IOCP)
- `std.json`: Serialización SIMD-acelerada (AVX2/SSE4/NEON)
- Axon Hub inmutabilidad + validación SemVer estricta — *absorbido por F18*

### M4: DOMINIO DEL IDE Y EXPANSIÓN DE OPENSYN (VS CODE)
- Publicación automática Marketplace (tag `v3.x`)
- Zero Telemetry, RAG micro-dosis, HW-aware AI args — *absorbido por F19*

### M5: GUERRA DE RENDIMIENTO Y POSICIONAMIENTO COMERCIAL
- Benchmarks abiertos: JSON SIMD >500MB/s, Matriz 256x256 <5ms, 10K hilos >8000 msg/s
- Casos de estudio: Migración Python→Synapse RAM -60%+, latencia -40%

---

## REGISTRO DE CAMBIOS DEL DOCUMENTO

| Fecha | Versión Documento | Cambio | Autor |
|-------|-------------------|--------|-------|
| 2026-07-24 | 1.0 | Creación inicial del roadmap unificado. Fases 1-5 completadas, histórico M1-M5 preservado. | Arquitecto |
| 2026-07-25 | 2.0 | Fase 6 (PGO/LTO) completada, benchmarks registrados, documentación de optimizaciones. | Ingeniero |
| 2026-07-26 | 3.0 | Fase 7 (Caché incremental) completada, certificación de determinismo. | Ingeniero |
| 2026-07-26 | 4.0 | Unificación v5.0 — proyección F8-F11 con criterios técnicos detallados. | Arquitecto |
| 2026-07-26 | 5.0 | Test isolation certificado (305/305, 0 skipped, 0 failed). Fase 8 → SIGUIENTE HITO. Fase 9 → EN PROGRESO con std.debug. Archivos roadmap redundantes eliminados. | Arquitecto |
| 2026-07-26 | 6.0 | Restauración del historial completo desde v0. Secciones jerarquizadas (1-7). Fechas de certificación por hito. Trazabilidad F0→M7.5. M1-M5 con notas de absorción. | Arquitecto |

---

*Roadmap vivo — actualizado 26 Julio 2026. v2.2.3 base certificada (305 tests, 0 failed, 0 skipped). Único archivo de control autorizado: ROADMAP.md. Archivos redundantes eliminados: ROADMAP_DE_EJECUCIÓN_DEFINITIVO.md (obsoleto), ROADMAP_GENERADOR.md → renombrado a LECCIONES_GENERADOR.md (preservado como documentación técnica).*