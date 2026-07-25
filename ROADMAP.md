# 🗺️ ROADMAP — Synapse/OpenSyn v2.2.2 → v3.0

> **Estado Actual:** ✅ **v2.2.2 — RELEASE CANDIDATE** — Base estable: 297 tests Python + 20 C/nativos | GCC 0 errores | Pipeline nativa | IA nativa | Axon | LSP | SIMD
> **Próximo:** 🚀 **v3.0 — PLANIFICACIÓN ACTIVA** — Multiplataforma + Migración Python→Synapse + Dominio IDE
> **Lema:** Estabilizar antes de expandir. Cero código nuevo hasta que el núcleo sea sólido.

---

## � HISTORIAL COMPLETO v1.0 → v2.2.2 (Fases F0-F19)

| Fase | Descripción | Estado | Tests |
|------|-------------|--------|-------|
| **F0** | Saneamiento del repositorio | ✅ | 231 |
| **F1** | Eliminación de código muerto | ✅ | 231 |
| **F2** | Reparación del generador C | ✅ | 231 |
| **F3** | Bootstrap (Python→Stage1→2→3) | ✅ | 285 |
| **F3 bis** | Bootstrap reparación (generar + F8) | ✅ | 285 |
| **F4** | Refactor generador (7 módulos) | ✅ | 231 |
| **F4.5** | Post-processing asm() | ✅ | 231 |
| **F5** | CI/CD | ✅ | 231 |
| **F6** | Refactor .syn + eliminar TEMP | ✅ | 231 |
| **F7** | Generador nativo (sin Python) | ✅ | 231 |
| **F8** | Análisis semántico nativo V2 | ✅ | 285 |
| **F9** | Eliminar post-processing + fix emisores | ✅ | 231 |
| **F10** | Concurrencia (canales tipados) | ✅ | 240 |
| **F11** | Fuzzing destructivo | ✅ | 240 |
| **F12** | LSP nativo | ✅ | 283 |
| **F13** | Extensión VS Code + LSP | ✅ | 283 |
| **F14** | Estabilización LSP nativo | ✅ | 283 |
| **F15** | Renombrar EOF→T_FIN | ✅ | 285 |
| **F15b** | Pipeline nativa reentrante | ✅ | 285 |
| **F16** | Contratos lógicos nativos | ✅ | 283 |
| **F17** | Bootstrap full auto-hospedado | ✅ | 283 |
| **F18** | Axon gestor de paquetes | ✅ | 33/33 E2E + Fuzz |
| **F19** | Edge AI runtime (SIMD) | ✅ | 283 |

**Plan de Ataque Industrial v2.2.2:** Fases 1-4 completadas (Reproducibilidad, Erradicación excepciones, Deuda técnica, Estabilización CI/CD). 5.8MB código muerto purgado. IA Nativa integrada.

---

---

## 📋 ROADMAP v3.0 — FASES FUTURAS M1-M5

### M1: INFRAESTRUCTURA MULTIPLATAFORMA Y DISTRIBUCIÓN GLOBAL

**M1.1 Pipeline de Compilación Cruzada (CI/CD Matrix)**
- [ ] Targets: linux_x86_64, linux_arm64, darwin_arm64, windows_x64
- [ ] Toolchain estático inyectado con flags `-static -O2 -lpthread -lm`
- [ ] Artefactos: `synapse-{target}`, `synapse_lsp-{target}`, runtime estático

**M1.2 Firma Criptográfica de Artefactos (Ed25519 & SHA-256)**
- [ ] `axon fetch` y `axon verify` validan `axon.lock` + firma Ed25519
- [ ] GitHub Actions: step `sign-artifacts` con `cosign`/`gpg` + Ed25519 (TweetNaCl)
- [ ] `synapse.exe --verify <binario>` verifica SHA-256 + firma embebida

**M1.3 Empaquetado Unix Nativo**
- [ ] `install.sh` (Linux/macOS): descarga binario + runtime + LSP, instala en `/usr/local/bin`
- [ ] `install.ps1` (Windows): equivalente PowerShell con MinGW portable
- [ ] Descarga opcional de `llama-server.exe` + modelo `.gguf` (auto-selección VRAM)

---

### M2: MIGRADOR AUTOMATIZADO PYTHON → SYNAPSE (OPENSYN)

**M2.1 Analizador Estructural de Python (py_parser)**
- [ ] `synapse_lsp/open_syn/py_parser.py`: usa `ast` nativo → AST Universal Canónico
- [ ] Mapeo: `FunctionDef` → `DefinicionFuncion`, `If` → `SentenciaSi`, `ClassDef` → `DefinicionEstructura`
- [ ] **Prohibido:** manipulación de texto plano / regex — solo transformación AST→AST

**M2.2 Inferencia de Tipos Estrictos**
- [ ] `Any` → requiere anotación explícita (`entero`, `decimal`, `texto`, `booleano`, `Resultado<T,E>`, `Opcion<T>`)
- [ ] Variables sin tipo inferible → error con sugerencia de anotación
- [ ] `typing.Optional[T]` → `Opcion<T>`, `typing.Union[T,E]` → `Resultado<T,E>`

**M2.3 Endpoint LSP de Migración (`synapse/migrateFile`)**
- [ ] VS Code: Code Action `synapse.migrateFile` en `.py` → genera `.syn` optimizado
- [ ] RAG local inyecta contexto: imports resueltos, tipos inferidos, contratos sugeridos
- [ ] Diff interactivo: VS Code nativo (original .py ↔ generado .syn)

---

### M3: CONSOLIDACIÓN DE LA BIBLIOTECA ESTÁNDAR Y AXON HUB

**M3.1 Módulos Core (std)**
- [ ] `std.net`: HTTP/TCP nativo alto rendimiento en C (epoll/kqueue/IOCP) — 🚀 Planificado
- [ ] `std.json`: Serialización SIMD-accelerada (AVX2/SSE4/NEON) — 🚀 Planificado
- [x] `std.concurrencia`: `Canal<T>` tipado con `enviar`, `recibir`, `cerrar`, `destruir`, `ErrorCanal` — ✅ Completado (v2.2.2 M3.1)
- [x] `analizador_semantico.syn`: Ownership enforcement en `SentenciaLanzar` — move incondicional de variables capturadas, `ERR_MEM_USE_AFTER_MOVE` (E-504) — ✅ Completado
- [x] Test E2E: `tests/e2e/e2e_concurrencia.syn` — comunicación bidireccional `Canal<T>`, validación ownership — ✅ Completado

**M3.2 Axon Hub e Inmutabilidad**
- [x] Registro centralizado: `axon.toml` canónico + validación SemVer estricta
- [x] `axon fetch`: verificación Ed25519 obligatoria + `axon.lock` SHA-256
- [x] Cero scripts arbitrarios pre/post-instalación — solo declarativo TOML
  - [x] `_syn_axon_validar_manifiesto()`: valida campos requeridos, rechaza `[scripts]` con `preinstall`/`postinstall`
  - [x] Prueba de fuzzing: 14/14 tests con TAR malicioso + firma falsificada + `../` + hooks combinados
- [x] Resolución local: caché `.axon_cache/` + `axon.lock` persistente

---

### M4: DOMINIO DEL IDE Y EXPANSIÓN DE OPENSYN (VS CODE)

**M4.1 Publicación en Marketplace**
- [ ] `vsce package` → `synapse-vscode-v3.x.vsix`
- [ ] Publicación automática en Visual Studio Marketplace (tag `v3.x`)
- [ ] Configuración: `synapse.lsp.nativeBinary` auto-detecta binario por OS/arch

**M4.2 Optimización RAG Quirúrgico**
- [ ] Contexto micro-dosis: nodo AST actual + 5 líneas arriba/abajo + diagnóstico
- [ ] Sugerencias: optimización SIMD (`std.simd`), detección dead-code

**M4.3 Auditoría Dinámica de Hardware**
- [ ] `synapse.exe --detect-hardware` → detecta VRAM/RAM/CPU → sugiere modelo `.gguf` (1.2B/7B/70B)
- [ ] Auto-config en `axon.toml`: `ia.modelo = "llama-3.2-1b-instruct.Q4_K_M.gguf"`

---

### M5: GUERRA DE RENDIMIENTO Y POSICIONAMIENTO COMERCIAL

**M5.1 Suite de Benchmarks Abiertos**
- [ ] Bucles concurrentes 10K hilos: > 8000 msg/s (actual: 8083)
- [ ] Parseo JSON SIMD 100MB: > 500 MB/s
- [ ] Multiplicación matriz 256x256: < 5ms (actual: 4.28ms AVX2)
- [ ] Bootstrap auto-hospedado: < 30s

**M5.2 Casos de Estudio y Whitepapers**
- [ ] Migración backend Python → Synapse: reducción RAM 60%+, latencia -40%
- [ ] Soberanía de datos: cero telemetría, cero nube, binario autónomo

---

## ️ IMPLEMENTACIÓN INMEDIATA (PRÓXIMOS PASOS)

1. **`.github/workflows/cross-compile.yml`** — Matrix CI/CD 4 targets + firma + upload
2. **`docs/OPEN_SYN.md`** — Especificación técnica completa del migrador Python→Synapse
3. **`compilador/open_syn/`** — Nuevo submódulo: `py_parser.py`, `type_inference.py`, `ast_mapper.py`
4. **`synapse_lsp/open_syn/`** — Endpoint LSP `synapse/migrateFile` + CodeAction `synapse.migrateFile`

---

*Roadmap vivo — actualizado 24 Julio 2026. v2.2.2 base estable. v3.0 inicia ejecución M1-M5.*
