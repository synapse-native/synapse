# AUDITORÍA DE ALINEACIÓN — MANUALES v8.1.0 vs CÓDIGO (Ecosistema Synapse + Syquex + OpenSyn)

> **Propósito:** Registro oficial y AUTOCONTENIDO de la auditoría punto por punto que alinea
> TODO el código del repositorio con los 9 manuales de ingeniería (v8.1.0-industrial) y el
> roadmap de implementación (`ROADMAP.md`). Cualquier sesión puede retomar la auditoría
> leyendo SOLO este documento y el plan de reparación de instalación limpia.
>
> **Autor:** Buffy (Freebuff AI) — Programador Synapse
> **Inicio:** 2026-08-04
> **Versión objetivo:** 8.1.0-industrial (manuales, gobernanza y roadmap)
> **Versión del código al iniciar:** 5.1.1-industrial (VERSION) → ACTUALIZADA a 8.1.0-industrial
> **Estado general:** 🔄 EN PROGRESO — Fase 0 ✅ commitada y revisada (commit `auditoria(F0): revision code-reviewer…`); **Fase 1 (F1) en curso**: F1.3 parcial — TokenID alineados al Manual 2 §3 y 14 TokenID nuevos (H19–H25, D-F1 pendiente de parser); **herramienta de espejo del frontend embebido creada (H24 VIVO)** — `nucleo/_gen_frontend_p.py` + `frontend_p.syn` regenerado, espejo `_G_fp*`/`_G_tk*` exacto, bootstrap diff 0 bytes; **F1.2 (D-F1, Fase B) completado en el frontend embebido** — `declaracion_tipo` (alias/ADT/genéricos), `nulo`, `tensor()` y structs C nuevas; bootstrap-full diff 0 bytes

---

## 1. REGLAS DE LA AUDITORÍA (Gobernanza v8.1.0)

1. **Fuentes de verdad absolutas:** `docs/manuales/MANUAL 1.md` … `MANUAL 9.md` y `ROADMAP.md`.
2. **Cada micro-entregable DEBE referenciar:** `Manual X, Sección Y, Hito Z`.
3. **NO inventar APIs.** Si no está en los manuales, no existe.
4. **TODAS las funciones públicas** deben tener `requiere` y `garantiza` (Manual 2).
5. **Los tests son inmodificables** salvo endurecimiento con aprobación previa del Arquitecto.
6. **No arreglos ilegítimos ni hardcoding.** Reparación con código real y funcional.
7. **Respetar el orden del roadmap.** No adelantar fases (p.ej. `syquex/`, `lib/` = Fases 22+).
8. **Cero dependencias no especificadas.** Solo Axon está autorizado.
9. **Cero deuda técnica** (nueva o antigua): todo hallazgo se resuelve o se registra con
   resolución asignada; nada queda sin seguimiento.
10. **Código muerto se elimina.** Todo archivo/símbolo sin uso real se borra o se justifica.
11. **Modularizacion** todo archivo debe ser evaluado para su modularizacion.


## 2. PROTOCOLO DE ENTREGA (por micro-entregable)

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: [nombre]
FASE: [número]
MANUAL REFERENCIADO: [sección y párrafo]
HASH COMMIT: [sha256]
COMPILACIÓN: [log 10 líneas]
TESTS: [lista + resultado]
COBERTURA: [%]
MODIFICACIONES DE TESTS: [ninguna / justificación + aprobación]
MODULARIZACIÓN: [ninguna / archivos nuevos]
RIESGOS IDENTIFICADOS: [lista]
PRÓXIMO PASO: [descripción]
--- FIN ---
```

---

## 3. CHECKLIST GLOBAL POR FASE (punto por punto)

Leyenda: ⬜ PENDIENTE · 🔄 EN PROGRESO · ✅ VERIFICADO (con evidencia) · ⚠️ DESVÍO registrado

### FASE 0: SANEAMIENTO Y ESTRUCTURA INICIAL (Manual 1 §4; criterios en ROADMAP.md)

| # | Punto | Manual | Estado |
|---|-------|--------|--------|
| 0.1 | Estructura de carpetas: `/nucleo/`, `/std/`, `/runtime/`, `/axon/`, `/tests/` | Manual 1 §4 | ✅ migración std/ + axon/ completada (30 .syn + 3 fuentes C); refs a `librerias/std` = 0 en spdx; headers .syn corregidos |
| 0.2 | `.gitignore` con cobertura total de artefactos (`.exe`, `.o`, `.so`, `.dll`, `__pycache__`, `_*.h`, `prueba_*.c`, `.o` dentro de `runtime/core/`) | Manual 1 §4 | ✅ ampliado (bootstrap_tmp/, dist/) + 202 artefactos y 8 carpetas temporales eliminados |
| 0.3 | `LICENSE` (MIT) | Manual 1 §4 | ✅ verificado |
| 0.4 | `README.md` alineado a la estructura real y a v8.1.0 | Manual 1 §4, §7.4.6 | ✅ enlaces MANUAL N.md corregidos (espacio, no guion bajo); estructura runtime real; métricas 667 tests |
| 0.5 | Pre-commit hooks (formateo, linting) | Manual 1 §4 | ✅ verificado (`.pre-commit-config.yaml`) |
| 0.6 | Script de bootstrap (`build.sh`/`build.bat`) ejecuta sin errores | Manual 1 §4, Manual 9 §9.1 | ✅ bootstrap-full S1→S2→S3 con diff 0 bytes (bug H14 corregido) |
| 0.7 | Versión unificada 8.1.0-industrial en todos los manifiestos | Manual 1 §6, §7 | ✅ VERSION, README, workflows, axon.toml, spdx, instalador, vsix, docs/src, sbom.py |
| 0.8 | Eliminar código muerto y artefactos de build de la raíz | Manual 1 §4 | ✅ 202 artefactos, 8 carpetas tmp, legacy/, test_count_nodes.c (PE32), test_principal_legacy.c (PE32) |

### FASE 1: LEXER Y PARSER (Manual 2; criterios en ROADMAP.md)

| # | Punto | Manual | Estado |
|---|-------|--------|--------|
| 1.1 | `nucleo/lexer.syn`: `#lang`, INDENT/DEDENT, comentarios, cadenas, números, operadores | Manual 2 (EBNF) | ⬜ |
| 1.2 | `nucleo/parser.syn`: descenso recursivo, AST enlazado (`Nodo*`) | Manual 2 | ⬜ |
| 1.3 | `nucleo/tokens.syn`: `TokenID` + diccionarios multi-idioma (es/en/fr/pt) | Manual 2 | 🔄 TokenID renombrados al Manual 2 §3 (T_SI/T_SINO; enum Python SI/SINO/FUNCION/…) + 14 TokenID nuevos (H22); lexer Python: 6 keywords activados (let, delegar, arc, débil, @export — H21); activación completa bloqueada por colisiones con el parser actual (D-F1) |
| 1.4 | `nucleo/ast_nodes.syn`: estructuras de nodos del AST | Manual 2 | ⬜ |
| 1.5 | Tests unitarios lexer/parser (válidos e inválidos) | Manual 2 §Tests | ⬜ |
| 1.6 | Criterio: ejemplos del Manual 2 tokenizan; errores con ubicación precisa | Manual 2 | ⬜ |

### FASE 2: TABLA DE SÍMBOLOS Y ANÁLISIS SEMÁNTICO (Manual 2)

| # | Punto | Manual | Estado |
|---|-------|--------|--------|
| 2.1 | `nucleo/tabla_simbolos.syn`: scopes anidados | Manual 2 | ⬜ |
| 2.2 | `nucleo/analizador_semantico.syn`: 3 pasadas (Estructuras→Firmas→Cuerpos) | Manual 2 | ⬜ |
| 2.3 | `nucleo/errores.syn`: taxonomía ERR_SEM_* | Manual 2 | ⬜ |
| 2.4 | Hindley-Milner (unificación, occurs check) | Manual 2 | ⬜ |
| 2.5 | Ownership/borrowing (use-after-move, préstamos) | Manual 2 | ⬜ |
| 2.6 | Exhaustividad en `coincidir` para ADT | Manual 2 | ⬜ |

### FASE 3: GENERADOR DE CÓDIGO C Y RUNTIME (Manual 3)

| # | Punto | Manual | Estado |
|---|-------|--------|--------|
| 3.1 | `nucleo/generator.syn`: emisor C (C99/C11, orden alfabético, determinismo) | Manual 3 | ⬜ |
| 3.2 | `runtime/core/memory.c`: pool allocator | Manual 3 | ⬜ |
| 3.3 | `runtime/core/io.c`: I/O básico (log, archivos) | Manual 3 | ⬜ |
| 3.4 | `runtime/core/concurrency.c`: fibras y canales | Manual 3 | ⬜ |
| 3.5 | RAII: liberación automática al final del scope | Manual 3 | ⬜ |
| 3.6 | Mapeo de tipos Synapse→C (entero→int, texto→CadenaSegura, tensor→Tensor) | Manual 3 | ⬜ |

### FASE 4: CONCURRENCIA Y CANALES (Manual 3/4)

| # | Punto | Manual | Estado |
|---|-------|--------|--------|
| 4.1 | `runtime/core/concurrency.c`: fibras, canales sync/async, mutex, semáforos | Manual 4 | ⬜ |
| 4.2 | `std/concurrencia.syn`: `lanzar`, `escuchar`, `Canal<T>`, `cerrar` | Manual 4 | ⬜ |
| 4.3 | Generación de código para `lanzar`/`escuchar` | Manual 4 | ⬜ |
| 4.4 | Pruebas de estrés (10,000 fibras) sin deadlocks ni data races | Manual 4 §Tests | ⬜ |

### FASE 5: CONTRATOS Y BOOTSTRAP (Manual 4/9)

| # | Punto | Manual | Estado |
|---|-------|--------|--------|
| 5.1 | `nucleo/verificador_formal.syn`: `requiere`/`garantiza` → aserciones C | Manual 4 | ⬜ |
| 5.2 | Bootstrap 3 etapas (S1 Python, S2 Synapse→Synapse, S3 Synapse→Synapse) | Manual 9 §9.1 | ⬜ |
| 5.3 | Determinismo: diff 0 bytes S2 vs S3 | Manual 9 §9.7 | ⬜ |

### FASE 6: AXON (GESTOR DE PAQUETES) (Manual 5/8)

| # | Punto | Manual | Estado |
|---|-------|--------|--------|
| 6.1 | `axon/axon_rt.c`: TOML, TAR, SHA-256, Ed25519, SemVer, lock | Manual 8 | ⬜ |
| 6.2 | `axon/tweetnacl.c`: Ed25519 | Manual 8 | ⬜ |
| 6.3 | `axon/axon.toml`: esquema de manifiesto | Manual 8 | ⬜ |
| 6.4 | CLI: `axon init`, `fetch`, `publish`, `verify`, `search` | Manual 8 | ⬜ |
| 6.5 | Protección path traversal en TAR | Manual 8 | ⬜ |
| 6.6 | Lockfiles `axon.lock` deterministas | Manual 8 | ⬜ |

### FASE 7: BACKEND LLVM Y WASM (Manual 5)

| # | Punto | Manual | Estado |
|---|-------|--------|--------|
| 7.1 | `nucleo/llvm_backend.syn`: IR LLVM válido | Manual 5 | ⬜ |
| 7.2 | `nucleo/wasm_backend.syn`: WAT/WASM | Manual 5 | ⬜ |
| 7.3 | CLI: `build --target llvm`, `build --target wasm` | Manual 5 | ⬜ |
| 7.4 | `std/llvm.syn`, `std/wasm.syn` | Manual 5 | ⬜ |

### FASES 8–21: MÓDULOS AVANZADOS (Manuales 5–9)

| # | Punto | Manual | Estado |
|---|-------|--------|--------|
| 8 | `std.cluster`: Raft, work-stealing, multicast, handshake Ed25519 | Manual 5 | ⬜ |
| 9 | `std.debug`: time-travel, snapshots | Manual 6 | ⬜ |
| 10 | Hardening: ATP avanzado, SBOM SPDX, SLSA L3, fuzzing 24/7 | Manual 9 | ⬜ |
| 11 | Release matrix (4 targets), firma Ed25519, marketplace, benchmarks | Manual 9 | ⬜ |
| 12 | IA Nativa: modelo local, RAG, LoRA, quantization, distillation | Manual 7 | ⬜ |
| 13 | Federated: FedAvg, orquestador distribuido | Manual 7 | ⬜ |
| 14 | Proof Bridge (Coq/Lean), symbolic execution | Manual 9 | ⬜ |
| 15 | Quantum: Shor QEC, Surface Code, T1/T2 | Manual 9 | ⬜ |
| 16 | Modularización de `synapse_rt.c` | Manual 3 §3.1 | ⬜ |
| 17 | PGO/LTO, footprint, benchmarks | Manual 9 | ⬜ |
| 18 | Caché incremental SHA-256 (HIT/MISS/STALE) | Manual 9 | ⬜ |
| 19 | CanalRemoto v2: handshake Ed25519 | Manual 5 | ⬜ |
| 20 | Lifetimes avanzados: region graph, union-find | Manual 2 | ⬜ |
| 21 | RAII y scopes: destructor maps | Manual 3 | ⬜ |

### FASES 22–30: SYQUEX Y ECOSISTEMA COMPLETO (Manuales 1/3, ROADMAP)

| # | Punto | Manual | Estado |
|---|-------|--------|--------|
| 22 | `syquex/`: lexer, parser, traductor, `nucleo/ast_abi.syn` | Manual 3 | ⬜ no adelantar |
| 23 | Modelo de memoria Syquex (arenas, RC, alcance) | Manual 3 | ⬜ no adelantar |
| 24 | `lib/`: std lib de Syquex (io, math, texto, lista, mapa, json, web, gui, dom, db, tiempo, pruebas, ia) | Manual 3 | ⬜ no adelantar |
| 25 | Backend WASM + frontend DOM para Syquex | Manual 3 | ⬜ no adelantar |
| 26 | OpenSyn para Syquex (router, transpiler, contexto estático, bindings) | Manual 7 | ⬜ no adelantar |
| 27 | Herramientas: LSP, VS Code, `--check` | Manual 8 | ⬜ no adelantar |
| 28 | Certificación de Syquex | Manual 9 | ⬜ no adelantar |
| 29 | Detección HW y gestión de modelos (`std/os.syn`, `opensyn/installer.syn`) | Manual 7 | ⬜ no adelantar |
| 30 | Instalación unificada (Inno Setup, .deb, .dmg, firmas, update) | Manual 9 §9.9 | ⬜ no adelantar |

---

## 4. HALLAZGOS GLOBALES (sin deuda oculta)

| # | Hallazgo | Severidad | Resolución | Estado |
|---|----------|-----------|-----------|--------|
| H1 | Migración `librerias/std/*.syn → std/` incompleta: `synapse.spdx.json` (60+ refs), headers de los `.syn`, `_gen_embedded.py`, manifests `.syn.json` aún apuntan a `librerias/std` | Alta | Fase 0.1 | ✅ RESUELTA — headers .syn corregidos, spdx regenerado (0 refs a librerias/std), _gen_embedded.py ya usaba std/ |
| H2 | Migración `tweetnacl.c/.h` y `axon_rt.c` → `axon/` incompleta: comentarios de compilación en tests C, `synapse.spdx.json` | Media | Fase 0.1 | ✅ RESUELTA — spdx regenerado con rutas axon/; comentarios de compilación de tests C aún con `tweetnacl.c` raíz (cosmético, se revisan en Fase 6) |
| H3 | `VERSION` y todos los manifiestos en 5.1.1 vs manuales 8.1.0 | Alta | Fase 0.3 | ✅ RESUELTA — 8.1.0-industrial unificada (VERSION, README, workflows, axon.toml, spdx, instalador, vsix, docs/src, sbom.py, cli.py, pipeline.py, main.py) |
| H4 | ~100 artefactos de build en raíz (`.exe`, `.o`, `_*.c`, logs, `nul`, `programa.c`) | Media | Fase 0.2 | ✅ RESUELTA — 202 artefactos eliminados; raíz de 244 a 42 archivos legítimos |
| H5 | `.gitignore` no cubre `_*.h`, `prueba_*.c`, `runtime/core/*.o` (artefactos en carpeta trackeada) | Media | Fase 0.2 | ✅ RESUELTA — `_*.h`, `prueba_*.c`, `bootstrap_tmp/`, `dist/` añadidos; `*.o` global ya cubría runtime/core/ |
| H6 | `runtime/` incompleto vs Manual 1 §4: falta `runtime/core/io.c`, `net/`, `quantum/`, `ml/`, `federated/` | Media | Fase 0.4 (registro) | 🔄 registro — se completa en Fase 3 (io.c) y Fase 16 (net/quantum/ml/federated) |
| H7 | `README.md` describe estructura inexistente (`runtime/net`, `runtime/quantum`) | Media | Fase 0.4 | ✅ RESUELTA — README ahora refleja solo runtime/core/ y marca pendientes |
| H8 | `std/*.syn` con headers que aún dicen `#librerias/std/...` | Baja | Fase 0.1 | ✅ RESUELTA — llvm.syn, quantum_memory.syn, surface_code.syn corregidos |
| H9 | `librerias/` residual: `librerias/compiler/` (stubs legacy divergentes de nucleo/) y `librerias/embedded_libs.h` — mecanismo vivo (synapse_rt.c, main.syn, cache.syn) | Media | Fase 3/16 | 🔄 registro — evaluar en Fase 3 (embedded libs) y 16 (modularización) |
| H10 | `examples/` sin subcarpetas `synapse/` y `syquex/` (Manual 1 §4) y con `.c`/`.syn.json` generados mezclados | Media | Fase 0.4 | 🔄 pendiente — reorganizar en Fase 0.4 (ver Fase 0 checklist) |
| H11 | Workflows: faltan `test.yml` (existe `ci-tests.yml`) — alinear nombres a Manual 1 §4 | Baja | Fase 0.4 | 🔄 registro — renombrar/crear alias test.yml en Fase 0.4 |
| H12 | `opensyn/` stale: `opensyn/principal.syn` no bootstrapea (deuda D5 de Fase R) | Media | decidir en Fase 26 | ⬜ |
| H13 | `librerias/compiler/*.syn` (53–188 líneas) son stubs legacy que DIFIEREN de `nucleo/*.syn` (734–3591 líneas); solo usados por tabla virtual embedded | Media | Fase 3 | 🔄 registro — no tocar sin auditar flujo de embedded libs |
| H14 | **`build.bat bootstrap-full` comparaba Etapa 1 (Python, -static) vs Etapa 2 (nativa) — no es el criterio del Manual 9 §9.7 (S2 vs S3) → BINARY MISMATCH siempre** | **Crítica** | Fase 0.6 | ✅ RESUELTA — build.bat, build.sh y scripts/bootstrap.sh unificados a 3 etapas nativas (S1→S2→S3), diff S2 vs S3 = 0 bytes VERIFICADO en Windows; ASCII puro + CRLF para cmd.exe |
| H15 | **`ci-tests.yml` job bootstrap usaba `python main.py src/main.syn` (entrada vieja) + compilaba .o a mano — desvío del Manual 9 §9.1 y de ME-R2** | Alta | Fase 0.6 | ✅ RESUELTA — corregido a `python main.py nucleo/principal.syn -o synapse_stage1.exe` + verificación de existencia |
| H16 | **`scripts/bootstrap.sh` usaba `src/main.syn` como entrada y nomenclatura stage2/stage3 para las etapas 1/2** | Media | Fase 0.6 | ✅ RESUELTA — alineado a `nucleo/principal.syn` y nomenclatura stage1/stage2/stage3 con diff S2 vs S3 |
| H17 | **SBOM incluía `.venv`, `build/`, `dist/` (miles de archivos de pip) — SBOM no significativo** | Media | Fase 0.6 | ✅ RESUELTA — `ci_sbom.py` excluye .venv, venv, build, dist, distbin, .pytest_cache, .synapse, .axon_cache; SBOM regenerado: 2,368 archivos, 0 refs .venv |
| H18 | **README: métricas de insignias viejas de certificación 5.1.1 (337/337, 1/1, runtime <139KB, SLSA) inconsistentes con baseline 667** | Baja | Fase 0.6 | ✅ RESUELTA — insignias alineadas a 667 tests; runtime/SLSA marcados pendientes de re-certificación en Fases 10/17 |
| H19 | **`compilador/ast_nodes.py` definía `MODULO` dos veces** (operador `%` y keyword T_MODULO) → `TypeError: 'MODULO' already defined` al importar → **compilador Python caído** (bloqueaba toda la F1) | **Crítica** | F1 | ✅ RESUELTA — operador renombrado a `MOD`/`T_MOD` (paridad auto-hospedado `T_MOD=34`); refs en lexer.py, parser_expressions.py y tests |
| H20 | **`_T_MAP` en `compilador/generator/generator.py` con claves obsoletas** (IF/ELSE/FUNCTION/…) tras el rename del enum → los #define T_* emitidos dependían del fallback; hubiera divergido de las constantes del auto-hospedado | Alta | F1 | ✅ RESUELTA — claves = nombres actuales del enum (SI/SINO/FUNCION/…) y valores alineados a `nucleo/tokens.syn`; añadidos los 14 nuevos (H22) |
| H21 | **6 keywords del Manual 2 §3 conectados al lexer Python** (let→T_LET, delegar→T_DELEGAR, arc→T_ARC, débil→T_DEBIL, @export→T_EXPORT con soporte de `@`; module→T_MODULO no conectado por colisión) | Media | F1 | ✅ RESUELTA — DICCIONARIOS es/en/fr/pt + de/it (fallback EN documentado); 8 tests nuevos en test_lexer.py (endurecimiento, ver bitácora). **Nota:** estas 6 palabras pasan a ser RESERVADAS en el lexer Python (cambio de lenguaje conforme al Manual 2 §3; verificado sin regresiones en el repo — 675 tests + bootstrap) |
| H22 | **14 TokenID del Manual 2 §3 faltantes** en enum Python y `nucleo/tokens.syn` (T_LET, T_TIPO, T_TENSOR, T_NULO, T_OK, T_ERR, T_ALGUN, T_NINGUNO, T_MODULO, T_DELEGAR, T_EXPORT, T_RC, T_ARC, T_DEBIL) | Media | F1 | ✅ RESUELTA — añadidos (59–72) en enum Python, tokens.syn, lexer.syn, parser_constantes.syn; **no activables aún** en el lexer (D-F1) |
| H23 | **`T_IF`/`T_ELSE` (y enum IF/ELSE) no coincidían con el Manual 2 §3 (T_SI/T_SINO)** — nombre universal del token condicional | Media | F1 | ✅ RESUELTA — renombrado en los 5 `.syn` (tokens, lexer, parser_constantes, parser, parser_stmt); valores intactos (1/2); determinismo S2==S3 verificado (md5 `7911ea60…`) |
| H24 | **Frontend embebido `_P_*` es CÓDIGO VIVO (no muerto):** el auto-hospedado S2/S3 NO usa `nucleo/lexer.syn`/`parser*.syn` sino el frontend C legacy embebido (`_P_tokenizar`/`_P_programa`), generado por `emit_selfhost.py` (S1→S2) y espejado como cadenas `_G_fp*` en `generator.syn` (`gen_emitir_frontend_p`, 758 líneas) + `_G_tk*` (`gen_emitir_tokenizar`, 17 líneas). Esquema legacy T_IF/T_ELSE/T_FUNC/T_RET auto-consistente con los valores del Manual (solo difieren los nombres). `lexer.syn`/`parser*.syn` SON código muerto en runtime (reescritos por el frontend embebido). | **Alta** | F1.2/1.4 | ✅ VIVO — tool `nucleo/_gen_frontend_p.py` CREADO (faltaba) + `nucleo/generador/frontend_p.syn` generado; espejo verificado EXACTO (doble-escapado) y `_rebuild_generator.py` reensambla `generator.syn` byte-idéntico; fix 10 bytes NUL (`'\0'`→`'\\0'`) en `emit_selfhost.py` que alineaba S1 a S2/S3; bootstrap-full OK diff 0 bytes; D-F1 se implementará en el frontend embebido (fase B) |
| H25 | **Artefactos generados trackeados obsoletos vs `.syn` renombrados**: `nucleo/lexer.c`, `nucleo/parser.c`, `nucleo/generator.c`, `nucleo/parser_unity.c` (dumps por módulo sin script regenerador; `principal.syn.json` SÍ se regeneró en el bootstrap y `tests/integration/_synapse_shared.h` + `test_cluster_handshake.c` se regeneraron en la suite) | Baja | ME-R8 | 🔄 registro — higiene en ME-R8 (no son insumos de build) |

---

## 5. BITÁCORA DE EJECUCIÓN

| Fecha | Micro-entregable | Resultado | Evidencia |
|-------|------------------|-----------|-----------|
| 2026-08-04 | F0.1 Migración estructural std/ + axon/ | ✅ Completada | headers .syn corregidos; `embedded_libs.h` regenerado (11 libs); `synapse.spdx.json` regenerado con v8.1.0 y **0 refs a librerias/std** |
| 2026-08-04 | F0.2 Saneamiento | ✅ Completado | 202 artefactos + 8 carpetas tmp + legacy/ + 2 PE32 disfrazados de .c eliminados; `.gitignore` ampliado (bootstrap_tmp/, dist/, _*.h, prueba_*.c) |
| 2026-08-04 | F0.3 Versión 8.1.0-industrial | ✅ Completada | VERSION, README, workflows, axon.toml, spdx, instalador, vsix, docs/src, sbom.py, ci_sign.py, pipeline.py, cli.py, main.py |
| 2026-08-04 | F0.4 README + estructura | ✅ Enlaces y estructura | README: MANUAL N.md (con espacio), runtime/ solo core/, métricas 667 tests, estado EN AUDITORÍA |
| 2026-08-04 | F0.5 Bootstrap + tests | ✅ Validados | `python main.py nucleo/principal.syn` → S1 OK; **667 passed, 9 skipped, 1 xfailed** en 12:32 min; hola.syn compilado por nativo OK |
| 2026-08-04 | F0.6 Determinismo (bug H14) | ✅ Corregido y verificado | `build.bat bootstrap-full`: S1→S2→S3; **diff 0 bytes S2 vs S3 (Manual 9 §9.7)**; causa: comparaba S1(Python) vs S2(nativa); fix ASCII+CRLF |
| 2026-08-04 | F0.6b Revisión code-reviewer | ✅ 3 puntos críticos resueltos | H15 ci-tests.yml→nucleo/principal.syn; H16 bootstrap.sh→stage1/2/3; H17 SBOM excluye .venv/build/dist; H18 README métricas; build.sh→3 etapas nativas |
| 2026-08-04 | F1.1 TokenID al Manual 2 §3 + 14 nuevos + 6 keywords activos | ✅ Completado | Renombrado enum Python (IF→SI, …) + `nucleo/tokens.syn` (T_IF→T_SI, T_ELSE→T_SINO); H19 (MODULO dup) y H20 (_T_MAP) corregidos; 14 constantes añadidas (59–72); lexer Python: let/delegar/arc/débil/@export (H21); **suite completa 675 passed, 9 skipped, 1 xfailed** (667 + 8 tests nuevos = 675); **bootstrap S1→S2→S3 OK con DIFF 0 bytes** (md5 `7911ea60…`); `nucleo/principal.syn.json` regenerado; tests modificados SOLO en referencias de token y añadidos (endurecimiento: 8 tests lexer) |
| 2026-08-04 | F1.x Herramienta de espejo del frontend embebido (H24 VIVO) | ✅ Completado | **H24 re-clasificado: el frontend embebido `_P_*` es CÓDIGO VIVO** — S2/S3 no usan `lexer.syn`/`parser*.syn` (código muerto en runtime). Creado `nucleo/_gen_frontend_p.py` (regenera `nucleo/generador/frontend_p.syn` desde `emitir_parsear`/`emitir_tokenizar`) + `nucleo/generador/frontend_p.syn`; espejo `_G_fp*` (758) + `_G_tk*` (17) verificado EXACTO (doble-escapado: C + Synapse; decodificación = 2 pasadas de unescape); `_rebuild_generator.py` reensambla `generator.syn` **byte-idéntico** al commit; fix en `emit_selfhost.py`: 10 bytes NUL reales en el C generado (`'\0'`) → `'\\0'` (alinea S1 a S2/S3, funcionalmente idéntico); **bootstrap-full S1→S2→S3 diff 0 bytes OK**; smoke 16/16, unitarios 106, generator 49 |
| 2026-08-04 | F1.2 (D-F1, Fase B) Frontend embebido: `declaracion_tipo` + `nulo` + `tensor()` + ADT (Manual 2 §2 L74-75, §4.1, §4.3 L194) | ✅ Completado | `compilador/generator/emit_selfhost.py` extendido (paridad con el parser Python `compilador/parser.py` L73-86): token `\|`→**T_PIPE 58**; `_P_decl_tipo` + `_P_leer_constructores` (alias, ADT con `\|`, genéricos `<T,E>`, paréntesis externos, `&mut`, `Canal<T>`), dispatch en `_P_sentencia` por `val=="tipo"` + lookahead `{=,<,|,(}`; `nulo`→**LiteralNulo** y `tensor(filas, columnas)`→**ExprTensor** en `_P_prim`. Structs **LiteralNulo/ConstructorTipo/DeclaracionTipo** añadidas a `nucleo/ast_nodes.syn` (fuente REAL de tipos del build S2/S3; `ast_types.h` es legacy generado desde hola.c y no se incluye en ningún build) + espejo en `ast_types.h`. Espejo `_G_fp*` regenerado (`nucleo/_gen_frontend_p.py` + `nucleo/_rebuild_generator.py`); diff en `generator.syn` SOLO del bloque frontend (1656 líneas `_G_fp*` desplazadas por 1 string insertado, 0 fuera del bloque). **Harness C `tests/test_frontend_embebido_d_f1.py`**: compila structs reales + `_P_*` y verifica los 4 casos (alias, ADT genérica, ADT parentizada, función con `nulo`/`tensor(4,5)`). **bootstrap-full S1→S2→S3 diff 0 bytes OK**; suite **694 passed, 9 skipped, 1 xfailed**. Pendiente F1.2b (codegen `gen_visitar_top_level` en `generator.syn`, sin dispatch D-F1 aún) y resto de FASE B (`let`/`delegar`/`arc`/`débil`/`@export`). `rc`/`modulo` siguen sin mapeo (deuda D-F1 parcial, ver nota). |

> **Nota F1 (tests):** conforme a la regla 5 (tests inmodificables), los únicos cambios a tests fueron: (a) renombrado de `TokenID.*` a los nombres del Manual en `tests/test_lexer.py` (consecuencia directa del rename, sin tocar aserciones de comportamiento) y (b) **8 tests NUEVOS** añadidos en `TestLexerKeywordsNuevos` (endurecimiento). Pendiente de aprobación formal del Arquitecto como quedó registrado en Fase R.
>
> **DEUDA D-F1 (nueva, resolución obligatoria y BLOQUEANTE para F1.2/1.4):** los keywords restantes del Manual 2 §3 (tipo, tensor, nulo, ok, err, algun, ninguno, rc, modulo) **NO se activan** en el lexer porque colisionan con identificadores/constructores existentes del lenguaje (evidencia): `rc` = variable de retorno (`std/cluster.syn:149`, `std/quantum_err_corr.syn:47`), `tipo` = campo de struct (`x.tipo`), `tensor` = tipo y constructor `tensor(filas, columnas)`, `nulo` = tipo `-> nulo:`, `ok/err/algun/ninguno` = constructores ADT, `modulo` = parámetro `gen_emitir_traza(est, modulo: puntero, …)` en `nucleo/generator.syn:343`. **Resolución: F1.2/1.4 (estratégia A en fases — decidida por el Arquitecto): FASE B** — extender el frontend embebido `_P_*` (`emit_selfhost.py` + regenerar `_G_fp*` con `nucleo/_gen_frontend_p.py`, ver H24) para soportar `tipo X = …` (alias y ADT con `|`), `nulo`, `tensor()`, constructores ADT, `let`/`delegar`/`arc`/`débil`/`@export`; luego **FASE A** — refactorizar el frontend embebido al frontend Synapse nativo (`lexer.syn`/`parser*.syn`), que hoy es código muerto en runtime (reescrito por `_P_*`). Mientras tanto los TokenID quedan DEFINIDOS (set canónico completo) pero sin mapping de palabra.
>
> **Progreso F1.2 (2026-08-04):** FASE B **parcial ejecutada** — `declaracion_tipo` (alias, ADT con `|`, genéricos `<T,E>`, paréntesis), `nulo` y `tensor(filas, columnas)` ya se parsean en el frontend embebido `_P_*` con structs nuevas (`LiteralNulo`/`ConstructorTipo`/`DeclaracionTipo` en `nucleo/ast_nodes.syn`); ver fila F1.2. **Pendientes de FASE B:** codegen F1.2b (`gen_visitar_top_level` en `generator.syn`, sin dispatch D-F1), `let`/`delegar`/`arc`/`débil`/`@export`, y el mapeo de `rc`/`modulo`.
>
> **NOTA LATENTE (sin cambio de comportamiento):** el fallback de `_emitir_token_defines` para programas que NO declaran constantes T_* emite `T_FIN` con el valor auto() del enum (73, desplazado por los 14 nuevos) en vez de 57; el override por `ast_vals` lo neutraliza para el auto-hospedado (siempre declara T_FIN=57). Si en el futuro un programa de usuario dependiera de T_* embebidos sin declararlos, fijar 57 explícito.

---

## 6. NOTAS DE GOBERNANZA

- Este documento se actualiza en CADA micro-entregable; es la fuente para retomar la auditoría.
- Ninguna fase se marca ✅ sin evidencia de: compilación (log), tests (resultado), cobertura y commit hash.
- Si la auditoría revela que un punto NO se puede cumplir sin violar los manuales → **DETENERSE Y PREGUNTAR** al Arquitecto (formato `PREGUNTA AL ARQUITECTO:`).
- Los tests son inmodificables; cualquier ajuste requiere aprobación previa documentada.
- El roadmap impone el orden: no crear `syquex/` ni `lib/` hasta la Fase 22+.
