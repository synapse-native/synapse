# PLAN MAESTRO INDUSTRIAL — Synapse + Syquex + OpenSyn

**Fecha:** 2026-11-09
**Base:** `release/v8.1.0-industrial`, HEAD `44b2717` (r204 + documentación)
**Renumeración 2026-11-15:** los MEs r220-r233 se reasignaron a r240-r253 para
no colisionar con la cola de deuda R220/R222/R223 ya commiteada. La secuencia
de olas y dependencias se conserva.
**Estado del programa 2026-11-17:** EN CURSO — Frente A cerrado, Frentes B-G
abiertos. Estado real ME a ME (con evidencia) en §3.1, verificado por comandos
sobre el árbol y el binario, no por estimación.
**Alcance:** convertir en realidad verificable todo lo especificado en los
manuales, con OpenSyn a la altura de opencode/Codebuff en el eje que los
manuales definen: contexto profundo + validación con el compilador real +
privacidad local.
**Naturaleza:** plan de programa. Cada ME de este plan se ejecuta con su propio
`docs/plan_ME_<id>.md` (bloques `requisito:`/`texto:`/`implementacion:`/
`oraculo:`), expediente `docs/alineacion/<id>.md`, reporte `R<N>.md`, fila en
la bitácora canónica y actualización de `MEMORIA_PROYECTO.md`.

> Este documento NO es un plan de ME y no se somete a `contrastar.py` como si
> lo fuera. Es la cartera priorizada que el Arquitecto ratifica y de la que
> salen los planes MTS individuales.

---

## 0. Definición operativa de "industrial"

Un usuario externo puede instalar, usar y actualizar el ecosistema sin ayuda
del equipo; cada capacidad declarada en un manual tiene un test de
comportamiento (no solo inspección de fuente), está integrada en el binario
real, tiene documentación de uso y se distribuye de forma reproducible y
firmada. Esta definición es la de `docs/reportes/EVALUACION_AVANCE_2026-11-08.md`
§2 y se adopta como criterio de cierre del programa.

Reglas de gobernanza que aplican a TODOS los MEs:

- Los manuales son ley; el código desviado se corrige hacia el manual
  (`docs/gobernancia/GUIA_DE_GOBERNANZA.md`).
- Tests inmutables: modificarlos exige aprobación previa y explícita del
  Arquitecto.
- Toda función pública nueva lleva `requiere`/`garantiza` (Manual 2 §5.1 y
  §12).
- Todo archivo de producción modificado lleva un ancla
  `// cumple Manual X §Y` grep-chequeable y su lectura previa registrada.
- Cero deuda sin seguimiento; cero código muerto; módulos >1200 líneas
  requieren registro D-9.
- Nada de `--no-verify`, force-push ni saltos de fase.

---

## 1. Estado verificado al iniciar el programa

### 1.1 Lo que ya está cerrado

| Capacidad | Evidencia | Manual |
|---|---|---|
| Compilador + runtime + stdlib; bootstrap S1→S2 | Gates de bootstrap y matriz de compilación; `MEMORIA_PROYECTO.md` | Manual 1 §6 |
| Distribución firmada y `synapse update` nativo | R202 `f1a4a02`, R203 `d865ab9` | Manual 9 §3.1, §3.2, §6.3 |
| OpenSyn instalable con `llama-server` | R199 `a2d0ca3`, R200 `f3b7268` | Manual 9 §5.1-§5.7, Manual 7 §6.1 |
| OpenSyn chat/lectura/`git status` / `git log` | `opensyn/principal.syn` | Manual 7 §1.1, §2.3, §2.4 |
| `TOOL escribir` / `TOOL editar` con sandbox y aprobación | r204 `f018957`; oráculo E2E 3/3 | Manual 7 §1.1, §2.3, §7.3 |
| Gate de compilación de Fase 32 con baseline/trinquete | r204 `f018957`; `tests/integration/test_compilacion_fase32.py` | Manual 1 §6, Manual 2 §5.1 |

### 1.2 Brechas verificadas (no estimadas)

| Brecha | Evidencia | Manual que la exige |
|---|---|---|
| 10 módulos de producción de Fase 32 no compilan | `tests/fixtures/compilacion_baseline.txt` (10 rutas) y gate r204 | Manual 32 §2-§7; Manual 1 §6 |
| `pipeline_multiagente.syn` importa `opensyn.grafo_conocimiento`, que no existe | Evaluación 2026-11-08 §5.2 | Manual 32 §5.3 |
| `synapse/aiExplain`, `aiComplete`, `aiFix`, `aiStatus` en skip TDD | `tests/integration/test_ai_commands_opensyn.py`; Manual 8 §1.4 los declara soportados | Manual 7 §4.1, Manual 8 §1.4, §5.1 |
| `synapse opensyn <subcomando>` existe en el CLI Python (`cli.py:1285`) pero no en el binario nativo | Evaluación 2026-11-08 §5.4 | Manual 8 §4.1, §7 |
| No existen `aplicar_patch` ni `ejecutar` (shell/tests/build) como tools de OpenSyn | `opensyn/principal.syn` solo despacha `listar` / `leer` / `git` / `escribir` / `editar`; Evaluación §5.3, §6.1 | Paridad de producto (Evaluación §6) + sandbox Manual 7 §7.3 |
| `opensyn doctor` falla en este árbol por `llama-server.exe` ausente | Evaluación 2026-11-08 §5.4 | Manual 9 §5.4, §5.5 |
| No hay E2E con `llama-server` real ni benchmark en esta máquina | Evaluación §5.1, §5.4, §7 | Manual 7 §7.2, §7.3, §8 |
| Varios tests de Fase 32 son inspección de fuente, no comportamiento | Evaluación §5.2, §7 | Manual 32 §9; Manual Tests Obligatorios |
| Memoria de sesión/reanudar/undo no está integrada en el loop vivo | Evaluación §3; `run_manager.syn` no compila | Manual 32 §3.2, §3.4 |

### 1.3 Reglas de convivencia

- `nucleo/lsp_v3.syn`, `nucleo/embedded_libs.h`, `nucleo/lsp_v3.c.bak` y
  `nucleo/lsp_v3.c.new` son trabajo de otro agente. NO se tocan ni se stagean
  desde este programa hasta que su autor los integre.
- El baseline de compilación es un trinquete: cada ME que repara un módulo DEBE
  quitarlo de `tests/fixtures/compilacion_baseline.txt`; el gate falla si un
  módulo del baseline ya compila.

---

## 2. Arquitectura del programa

Seis frentes, ordenados por dependencia real (no por deseo):

| Frente | Objetivo | Por qué primero |
|---|---|---|
| **A. Reparar Fase 32** | Los 10 módulos compilan, se integran y tienen test de comportamiento | Sin ellos, el agente autónomo es código muerto |
| **B. Tools y loop de OpenSyn** | `aplicar_patch`, `ejecutar`, loop editar→validar→corregir, sesiones | Sin edición/ejecución no hay agente de coding |
| **C. LSP/IDE e IA** | `aiExplain/Complete/Fix/Status` reales, VS Code, debugger | Es la puerta de entrada del usuario |
| **D. CLI y paridad nativa** | `synapse opensyn` en el binario nativo; Fase 32 en S2 | El producto se distribuye como binario, no como Python |
| **E. Calidad industrial** | E2E real, benchmark, tests de comportamiento, cobertura | Un "verde" de inspección no prueba comportamiento |
| **F. Distribución y hardening** | Doctor/installer limpios, multiplataforma, release firmado | Cierra la promesa de instalación y actualización |

Frentes de soporte (se ejecutan cuando un ME de A-F los necesita):
**G. Compilador/runtime** (paridad S1↔S2, contratos, bootstrap).

---

## 3. Cartera de MEs

Los identificadores son propuestas de secuencia; el Arquitecto puede
renumerar. La estimación es en "ME" (unidad de sesión de trabajo con gates
completos), no en semanas calendario.

### Frente A — Reparar Fase 32 (prioridad 0)

| ME | Objetivo | Manual | Criterio de aceptación / oráculo | Depende |
|---|---|---|---|---|
| `r205_grafo_conocimiento` | Compilar `nucleo/grafo_conocimiento.syn` y construir el grafo desde el AST canónico | Manual 32 §2.3-§2.6 | `main.py --check --no-emit` rc=0; test de comportamiento que carga un repo pequeño y verifica nodos/aristas; se retira del baseline | r204 |
| `r206_validation_loop` | Compilar `opensyn/validation_loop.syn`; bucle de 3 intentos con feedback del compilador | Manual 7 §4.2, §6.3; Manual 32 §6.3, §6.4 | E2E: código inválido → 3 intentos → error final honesto; código corregible → verde; se retira del baseline | r205 |
| `r207_pipeline_multiagente` | Corregir import del grafo, compilar `opensyn/pipeline_multiagente.syn`, cablear Explorer→Architect→Coder→Reviewer→Fixer | Manual 32 §5.3-§5.5 | Test con LLM falso: 2-3 inferencias, fases deterministas <6 ms, código final compila; se retira del baseline | r205, r206 |
| `r208_run_manager` | Compilar `opensyn/run_manager.syn`; sesiones/reanudar/estado de ejecución | Manual 32 §3.2, §3.4 | Test de comportamiento de reanudación y de límite de sesión; se retira del baseline | r205 |
| `r209_router_chat` | Compilar `opensyn/router.syn` y `opensyn/chat.syn`; enrutado de comandos y extracción de código | Manual 7 §2.4, §4.2 | Test de enrutado y de extracción; se retiran ambos del baseline | r204 |
| `r210_explorer_det` | Compilar `opensyn/explorer_det.syn`; exploración determinista de contexto | Manual 32 §4.3, §4.6 | Test con grafo fixture: archivos relevantes y radio 2; se retira del baseline | r205 |
| `r211_architect_det` | Compilar `opensyn/architect_det.syn`; análisis de impacto determinista | Manual 32 §4.4, §4.6 | Test con grafo fixture: impacto directo/indirecto; se retira del baseline | r205 |
| `r212_memoria_cifrada` | Compilar `opensyn/memoria_persistente_cifrada.syn`; tres capas y cifrado | Manual 32 §3.2-§3.7 | Test de escritura/lectura cifrada y de no-fuga en claro; se retira del baseline | r208 |
| `r213_verificacion_aot` | Compilar `opensyn/verificacion_aot.syn`; auto-refutación con timeout | Manual 32 §6.3-§6.6 | Test: caso límite genera contraejemplo o timeout honesto; se retira del baseline | r206 |
| `r214_baseline_cero` | Vaciar el baseline y dejar el gate como fallo duro | Manual 1 §6; Manual 2 §5.1 | `tests/fixtures/compilacion_baseline.txt` sin rutas; el gate falla si cualquier `.syn` de producción no compila | r205-r213 |

### Frente B — Tools y loop de OpenSyn (prioridad 0/1)

| ME | Objetivo | Manual | Criterio de aceptación / oráculo | Depende |
|---|---|---|---|---|
| `r215_tool_patch` | `TOOL aplicar_patch <ruta> :: <diff>` con sandbox y aprobación | Manual 7 §7.3 (sandbox); Evaluación §6.1 (paridad) | E2E con repo temporal: parche aplicado, contexto no aplicable rechazado, ruta fuera del workspace denegada; test de comportamiento | r204 |
| `r216_tool_ejecutar` | `TOOL ejecutar <comando>` con allowlist (`synapse check`, `pytest`, `git status/diff`, build) y timeout | Manual 32 §6.4 (timeout); Manual 7 §7.3 (sandbox) | E2E: comando permitido ejecuta y devuelve rc/salida; comando no permitido rechazado; timeout corta; sin inyección de shell | r215 |
| `r217_loop_integracion` | Cablear `validation_loop` y el pipeline al loop vivo de `principal.syn` | Manual 32 §5.3, §7.2 | E2E con LLM falso: editar→compilar→corregir; el loop se detiene a los 3 intentos; sin fugas de texto | r207, r216 |
| `r218_sesiones_undo` | Sesión/reanudar/undo/revertir en el loop | Manual 32 §3.2, §3.4 | Test de reanudar una sesión y revertir un cambio; historial consistente | r208, r217 |

### Frente C — LSP/IDE e IA (prioridad 1)

| ME | Objetivo | Manual | Criterio de aceptación / oráculo | Depende |
|---|---|---|---|---|
| `r219_lsp_ai` | Implementar de verdad `aiExplain`, `aiComplete`, `aiFix`, `aiStatus`; quitar los skips TDD | Manual 7 §4.1, §4.2; Manual 8 §1.4, §5.1, §5.4 | Tests LSP sin skip: respuesta JSON-RPC válida; código generado validado con `--check`; `aiStatus` refleja el servidor real | r217 |
| `r240_vscode_ai` | Comandos de la paleta y configuración de la extensión | Manual 8 §2.3, §2.4 | Test de la extensión: comandos despachan a los métodos LSP correctos | r219 |
| `r241_debugger` | Time-travel/reversible y comandos CLI | Manual 8 §3.1-§3.5 | Test de avance/retroceso y snapshots; integración VS Code | r219 |

### Frente D — CLI y paridad nativa (prioridad 1)

| ME | Objetivo | Manual | Criterio de aceptación / oráculo | Depende |
|---|---|---|---|---|
| `r242_native_opensyn_cli` | Despachar `synapse opensyn` (`status`, `download`, `finetune`, `bindings`, `transpile`) en el binario nativo | Manual 8 §4.1, §7 | Test E2E del binario nativo: `status` y `--help`; paridad con el CLI Python | r204 |
| `r243_native_fase32` | Compilar los módulos de Fase 32 con el compilador nativo (S2), no solo con S1 | Manual 1 §6; Manual 2 §5.1 | Bootstrap S1→S2 y gate de compilación nativa de los módulos reparados | r214 |
| `r244_paridad_lint_fmt_test` | Asegurar que `lint/fmt/test` nativos soportan los módulos nuevos | Manual 8 §4.1, §5.5 | Oráculo de paridad S1↔S2 sobre los módulos de Fase 32 | r243 |

### Frente E — Calidad industrial (prioridad 1/2)

| ME | Objetivo | Manual | Criterio de aceptación / oráculo | Depende |
|---|---|---|---|---|
| `r245_e2e_llama_server` | E2E real o hermético de chat + tools + validación con `llama-server` | Manual 7 §7.2, §8; Manual 9 §5.5 | Test E2E reproducible: chat responde, tool se ejecuta con aprobación, código se valida | r217 |
| `r246_benchmark_latencia` | Benchmark de latencia/throughput/VRAM | Manual 7 §7.2 | Umbrales: <1 s prompt corto, >100 tok/s, <6 GB en 7B Q4_K_M; reporte medido | r245 |
| `r247_tests_comportamiento` | Reemplazar tests de inspección de fuente por tests de comportamiento en Fase 32 | Manual 32 §9; Manual Tests Obligatorios | Ratio de tests de comportamiento documentado; 0 tests nuevos de solo grep | r214 |
| `r248_cobertura_opensyn` | Medir cobertura de OpenSyn con `synapse test --coverage` | Manual 8 §4.2 | Informe de cobertura de aristas con umbral acordado | r247 |

### Frente F — Distribución y hardening (prioridad 2)

| ME | Objetivo | Manual | Criterio de aceptación / oráculo | Depende |
|---|---|---|---|---|
| `r249_doctor_installer` | `opensyn doctor` encuentra `llama-server`; instalador limpio | Manual 9 §5.4, §5.5; Manual 7 §6.1 | E2E de instalación limpia y doctor verde | r245 |
| `r250_multiplataforma` | Instaladores Linux/macOS y CI matrix | Manual 9 §2.4, §2.5, §6.2 | Build/instalación en 3 plataformas; firma y checksum | r249 |
| `r251_release_hardening` | SBOM/SLSA, runner limpio, verificación de firma end-to-end | Manual 9 §6.1, §6.3 | Release de prueba verificado en runner limpio | r250 |

### Frente G — Compilador/runtime (soporte)

| ME | Objetivo | Manual | Criterio de aceptación / oráculo | Depende |
|---|---|---|---|---|
| `r252_bootstrap_parity` | Paridad S1↔S2 de nodos/tokens y bootstrap determinista | Manual 1 §6; Manual 2 §7.2 | S2==S3 byte-idéntico; oráculo de paridad de nodos | r243 |
| `r253_contracts_audit` | Contratos en toda función pública y auditoría de deuda | Manual 2 §5.1, §12 | `verificar_alineacion.py` 0 brechas; 0 funciones públicas sin contrato | r214 |

---

### 3.1 Estado real por frente (reconciliado 2026-11-17)

Reconciliación contra el árbol y el binario en `release/v8.1.0-industrial`,
HEAD `c341fc5` (R237). Leyenda: **HECHO** (entregado con reporte y oráculo),
**PARCIAL** (existe infraestructura pero falta lo que el plan exige),
**PENDIENTE** (no hay implementación), **RENUMERADO** (se ejecutó con otro id).

#### Frente A — Reparar Fase 32: **CERRADO**

| ME | Estado | Evidencia |
|---|---|---|
| `r205_grafo_conocimiento` | HECHO | `docs/reportes/R205.md` |
| `r206_validation_loop` | HECHO | `docs/reportes/R206.md`; `opensyn/validation_loop.syn` con `MAX_INTENTOS = 3` |
| `r207_pipeline_multiagente` | HECHO | `docs/reportes/R207.md` |
| `r208_run_manager` | HECHO | `docs/reportes/R208.md` |
| `r209_router_chat` | HECHO | `docs/reportes/R209.md` |
| `r210_explorer_det` | HECHO | `docs/reportes/R210.md` |
| `r211_architect_det` | HECHO | `docs/reportes/R211.md` |
| `r212_memoria_cifrada` | HECHO | `docs/reportes/R212.md` |
| `r213_verificacion_aot` | RENUMERADO → `r219_verificacion_aot` (HECHO) | `docs/reportes/R219.md`, commit `26e4cf8` |
| `r214_baseline_cero` | HECHO (sin reporte propio) | `tests/fixtures/compilacion_baseline.txt` sólo comentarios; `pytest tests/integration/test_compilacion_fase32.py` → 2 passed |

#### Frente B — Tools y loop: **2 de 4**

| ME | Estado | Evidencia |
|---|---|---|
| `r215_tool_patch` | HECHO | `docs/reportes/R215.md` |
| `r216_tool_ejecutar` | HECHO | `docs/reportes/R216.md`; allowlist y timeout en `opensyn/` |
| `r217_loop_integracion` | PENDIENTE | `nucleo/principal.syn` y `opensyn/principal.syn` **no** invocan `validation_loop` ni `pipeline_multiagente` (grep vacío); el loop a 3 intentos sólo existe dentro del módulo y su oráculo. R217 es otro ME (`r217_integracion_determinista`) |
| `r218_sesiones_undo` | PENDIENTE | R218 es `r218_bootstrap_json`, otro ME. `reanudar`/`revertir` aparecen sólo como funciones de `opensyn/run_manager.syn`, sin cableado al loop ni oráculo de reanudación |

#### Frente C — LSP/IDE e IA: **0 de 3**

| ME | Estado | Evidencia |
|---|---|---|
| `r219_lsp_ai` | PENDIENTE | `tests/integration/test_ai_commands_opensyn.py` conserva **5 `pytest.skip`** («no implementado aún (TDD)»); el bloqueo de id viene de que `r219` se usó para `verificacion_aot` |
| `r240_vscode_ai` | PARCIAL | `vscode-synapse/package.json` declara `synapse.aiStatus/aiExplain/aiComplete/aiFix`; los métodos LSP que despachan siguen en skip ⇒ comandos sin verificación real |
| `r241_debugger` | PARCIAL | `opensyn/router.syn` cataloga `std.debug` con `rp_*` (retroceder, breakpoints, pila) y `ms_*`/`tr_*` (snapshots, recording); sin oráculo de time-travel ni integración VS Code |

#### Frente D — CLI y paridad nativa: **3 de 3**

| ME | Estado | Evidencia |
|---|---|---|
| `r242_native_opensyn_cli` | **HECHO** (`616e321`) | `nucleo/principal.syn` despacha `opensyn`: `status`/`doctor` delegados en `opensyn.exe`, ayuda con los 5 subcomandos, errores honestos en el resto; oráculo `test_oraculos_r242_opensyn_nativo.py` 8/8; reporte `docs/reportes/R242.md` |
| `r243_native_fase32` | **HECHO** (`379d978`) | El binario nativo (S2) valida los 14 módulos `opensyn/*.syn` + `nucleo/grafo_conocimiento.syn` con diagnóstico accionable; oráculo `test_compilacion_fase32_s2.py` 8/8; reporte `docs/reportes/R247.md` |
| `r244_paridad_lint_fmt_test` | **HECHO** (`a4b6f6d`) | `lint`/`fmt` aceptan flags en cualquier orden (antes `lint --check f` leía `--check` como ruta), `lint` solo mira código (0 falsos positivos en los 15 módulos) y los relojes de `router`/`run_manager` son portátiles, así que `synapse test` compila y ejecuta un programa que importa `opensyn/router.syn`; oráculo de paridad S1↔S2 `test_paridad_lint_fmt_test_fase32.py` 10/10; reporte `docs/reportes/R248.md` |

#### Frente E — Calidad industrial: **0 de 4**

| ME | Estado | Evidencia |
|---|---|---|
| `r245_e2e_llama_server` | PARCIAL | Doble hermético de LLM (R227, `test_oraculos_r227_llm_mock.py`) y fixtures GGUF; sin E2E de chat+tools+validación contra `llama-server` |
| `r246_benchmark_latencia` | PENDIENTE | No hay reporte con latencia/tok-s/VRAM medidos contra los umbrales de Manual 7 §7.2 (lo más cercano son mediciones sueltas de R136/FASE_29) |
| `r247_tests_comportamiento` | PARCIAL | Existe `auditoria/auditar_calidad_tests.py` (usado en R160/R194); sin ratio de tests de comportamiento documentado para Fase 32 |
| `r248_cobertura_opensyn` | PARCIAL | `synapse test --coverage` funciona en el nativo; sin informe de cobertura de aristas |

#### Frente F — Distribución y hardening: **0 de 3**

| ME | Estado | Evidencia |
|---|---|---|
| `r249_doctor_installer` | PARCIAL | `opensyn doctor` existe en el CLI Python (R200 + `tests/integration/test_opensyn_doctor.py`), no en el binario nativo (`synapse doctor` falla). Instalación limpia: R237 cerró H-R234-2 (el setup ya trae toolchain) pero la VM limpia sigue pendiente |
| `r250_multiplataforma` | PARCIAL | `instaladores/{linux,macos,windows}` y matriz ubuntu/ubuntu-arm/macos/windows en `.github/workflows/release_matrix.yml` y `release-installers.yml`; sin evidencia de ejecución ni firma/checksum por plataforma en un release reciente |
| `r251_release_hardening` | PARCIAL | `scripts/ci_sbom.py` y `scripts/ci_sign.py` cableados en `release_matrix.yml`; falta el release de prueba verificado en runner limpio |

#### Frente G — Compilador/runtime: **0 de 2**

| ME | Estado | Evidencia |
|---|---|---|
| `r252_bootstrap_parity` | RESUELTO por `r270` (2026-11-19) | La paridad de nodos ya estaba cubierta (`tests/auditoria/test_paridad_nodos.py` 4/4). El sello S2==S3 es un oráculo propio con modos `--artefactos`/`--construir`/`--estricto`, invocado por `build.py` y el job `bootstrap` de CI. H-R252-1 fue un artefacto stale (etapa 1 rotulada como 2); H-R252-4 se cerró con `-static` en el enlace nativo win32. S2=S3 `30C07EF61C5F25A7…` (2.559.482 B). |
| `r253_contracts_audit` | PARCIAL | `verificar_alineacion.py` → 0 brechas; falta la auditoría «0 funciones públicas sin `requiere`/`garantiza`» con oráculo propio |

#### MEs entregados fuera de esta cartera

La numeración posterior diverge del plan. Entregados y documentados fuera de
§3: R220 (harness runtime path), R222/R222b/R223 (std texto, wrappers,
Syquex), R227 (mock LLM), R229 (caché resiliente), R234-R237 (certificación de
usuario final, fallback blanco, toolchain resuelto por el binario, toolchain
empaquetado en el instalador). Cualquier reordenamiento futuro debe reasignar
ids libres: **r219, r240-r253 y r218 ya no están disponibles** (colisión).

#### Criterios de cierre de §5 — estado verificado

| # | Criterio | Estado |
|---|---|---|
| 1 | Baseline vacío y gate duro | ✅ cumplido |
| 2 | Los 10 módulos de Fase 32 compilan con S2 + test de comportamiento | ❌ (S2 pendiente, r243) |
| 3 | 7 herramientas de OpenSyn con sandbox | ✅ (`opensyn/principal.syn` las despacha) |
| 4 | Loop editar→compilar→corregir a 3 intentos | ❌ (r217: módulo existe, no cableado) |
| 5 | `ai*` LSP responden, sin skips TDD | ❌ (5 skips) |
| 6 | `synapse opensyn <sub>` en el nativo | ✅ (r242, `616e321`) |
| 7 | E2E `llama-server` + benchmark medido | ❌ (r245/r246) |
| 8 | `doctor` + instalador en máquina limpia, release firmado y verificado | ❌ parcial (VM limpia y verificación end-to-end pendientes) |
| 9 | `verificar_alineacion` 0 brechas, `contrastar` verde, 0 deudas sin resolución | ⚠️ primera mitad cumplida; quedan deudas abiertas en `docs/plan_maestro_deudas.md` |

### 3.2 Frente H — Deuda de ecosistema, manuales y encoding (r270–r284)

Cartera nacida de la auditoría crítica del 2026-11-18. No renumera los MEs
existentes: usa ids libres r270–r284 y absorbe `r252b_emision_paridad` en
`r270`. El detalle ejecutable, los requisitos literales y los oráculos están
en `docs/gobernancia/PLAN_MEJORAS_ECOSISTEMA_R270_R284.md`; la política de
manutención de la ley está en `docs/gobernancia/POLITICA_MANUALES.md`.

| ME | Prioridad | Objetivo | Manual | Criterio de cierre | Depende |
|---|---|---|---|---|---|
| `r270_bootstrap_emision_paridad` | P0 · **CERRADO 2026-11-19 (82fb4c4)** | Unificar la emisión S1/S2 y cerrar S2==S3 | Manual 1 §6; Manual 9 §6.1, §6.2 | Bootstrap 3 etapas con diff 0; oráculo `--estricto`; sin binarios stale | — |
| `r271_manuales_canonicos` | P0 · **CERRADO 2026-11-19** | Índice completo, nombres canónicos y gate de citas/encoding | Manual 2 §1.2; Manual 1 §7.4; Manual 9 §6.2 | `verificar_manuales.py --todo` rc=0; Manual 31/32 canónicos; anexos como apoyo citable; D-MAN-1/2 opción A | — |
| `r272_docs_encoding` | P0 | Reparar corrupción documental y normalizar UTF-8 | Manual 2 §1.2; Manual 1 §7.4 | Auditoría y docs con 0 U+FFFD/C1/doble codificación; 1.275 líneas conservadas | r271 |
| `r273_installer_modelo_grande` | P0 | Instalador con GGUF de 873 MB sin timeout falso | Manual 9 §5.3, §5.5, §6.1; Manual 7 §6.1 | Verificación por streaming/caché; test existente pasa o deuda ambiental medida | — |
| `r274_gates_independientes` | P0 | Gates fuera del build, con oráculos propios y mutación | Manual 9 §6.2, §6.1; Manual 1 §7.4 | Romper el sello hace fallar el gate; CI sin `--sin-oraculos` | r270 |
| `r275_opensyn_e2e_bench` | P1 | E2E real local + benchmark medido | Manual 7 §7.2, §7.3, §8; Manual 9 §5.5 | Chat+tools+validación contra `llama-server`; latencia/tok-s/VRAM medidos | r273 |
| `r276_multiplataforma_release` | P1 | Instalación limpia Windows/Linux/macOS y release firmado | Manual 9 §2.4, §2.5, §6.1–§6.3 | Matriz real ejecutada; firma/checksum y smoke por plataforma | r270, r273 |
| `r277_contracts_audit` | P1 | 0 funciones públicas sin `requiere`/`garantiza` | Manual 2 §5.1, §12 | Escáner + tests de contrato; excepciones FFI justificadas | — |
| `r278_ide_debugger` | P1 | Completar VS Code, comandos IA y time-travel | Manual 8 §2.3, §3.1–§3.5, §1.4, §5.1 | E2E de extensión y debugger sin skips | r275 |
| `r279_suite_rapida` | P1 | Suite determinista y acotada | Manual 1 §7.2; Manual 9 §6.2 | Mismos passed/skipped/failed con tiempos medidos y 0 skips nuevos | r273, r274 |
| `r280_codigo_encoding` | P1 | Limpiar U+FFFD/C1 en runtime/std/fuentes generadas | Manual 2 §1.2; Manual 1 §7.4 | Scan repo-wide 0; `build.py` rc=0; `generator.syn` regenerado | r271 |
| `r281_d9_dead_code` | P2 | D-9, duplicados y código muerto | Manual 1 §7.4; Manual 2 §12 | Módulos >1200 registrados; duplicados 0; tests verdes | r279 |
| `r282_docs_informativos` | P2 | Alinear book2/reportes con la ley | Manual 1 §7.4; Manual 9 §6.1 | Barrido único de `book2` (D-MAN-3 opción A); cabecera informativa, enlaces resolubles, sin contradicciones | r271 |
| `r283_manual_versioning` | P2 | Changelog, semver y deprecación de manuales | Manual 1 §7.4; Manual 9 §6.1 | Cambio sin changelog falla el gate; alias/índice v2 | r271, r282 |
| `r284_observabilidad_local` | P2 | Diagnóstico local opt-in, cero red | Manual 1 §5.7; Manual 7 §7.3; Manual 32 §1.3 | Opt-in por defecto off; test de no-salida; redacción | — |

Reglas del frente H: nada de nube, telemetría, MCP, multi-proveedor ni GUI
externa (Manual 1 §5.7; Manual 32 §1.3); tests existentes inmutables salvo
aprobación; cada ME con su `plan_ME`, expediente, oráculo y reporte.

---

## 4. Secuencia recomendada (olas)

### Ola 0 — Cerrada en r204

- `TOOL escribir`/`TOOL editar` con sandbox y aprobación.
- Gate de compilación con baseline/trinquete de los 10 módulos.
- Evidencia: `f018957`, reporte `docs/reportes/R204.md`.

### Ola 1 — Desbloquear el agente (2-3 ME)

`r205_grafo_conocimiento` → `r206_validation_loop` →
`r207_pipeline_multiagente` → `r209_router_chat` →
`r215_tool_patch` → `r216_tool_ejecutar` → `r242_native_opensyn_cli`.

Por qué: sin grafo no hay contexto profundo; sin validation loop no hay
auto-corrección; sin patch/ejecutar no hay agente de coding; sin CLI nativo el
producto distribuido no expone OpenSyn.

### Ola 2 — Cerrar Fase 32 e integrar el loop (3-4 ME)

`r208_run_manager` → `r210_explorer_det` → `r211_architect_det` →
`r212_memoria_cifrada` → `r213_verificacion_aot` → `r214_baseline_cero` →
`r217_loop_integracion` → `r218_sesiones_undo`.

### Ola 3 — Puerta de entrada y calidad (4-5 ME)

`r219_lsp_ai` → `r240_vscode_ai` → `r241_debugger` →
`r245_e2e_llama_server` → `r246_benchmark_latencia` →
`r247_tests_comportamiento` → `r248_cobertura_opensyn`.

### Ola 4 — Paridad nativa y distribución (4 ME)

`r243_native_fase32` → `r244_paridad_lint_fmt_test` →
`r249_doctor_installer` → `r250_multiplataforma` → `r251_release_hardening` →
`r252_bootstrap_parity` → `r253_contracts_audit`.

---

## 5. Criterios de cierre del programa

El programa se considera "industrial" cuando TODOS estos son verdad:

1. `tests/fixtures/compilacion_baseline.txt` está vacío y el gate falla si
   cualquier `.syn` de producción no compila con S1.
2. Los 10 módulos de Fase 32 compilan también con S2 y tienen al menos un test
   de comportamiento cada uno.
3. OpenSyn expone `listar`, `leer`, `git`, `escribir`, `editar`,
   `aplicar_patch` y `ejecutar`; todas con sandbox y aprobación; E2E verde.
4. El loop editar→compilar→corregir funciona con un LLM real o un doble
   hermético y se detiene a los 3 intentos.
5. `aiExplain`, `aiComplete`, `aiFix`, `aiStatus` responden de verdad; los
   skips TDD de `test_ai_commands_opensyn.py` desaparecen.
6. `synapse opensyn <subcomando>` funciona en el binario nativo.
7. Hay E2E reproducible con `llama-server` (real o hermético) y benchmark
   medido contra los umbrales de Manual 7 §7.2.
8. `opensyn doctor` y el instalador funcionan en una máquina limpia; el
   release está firmado y verificado.
9. `verificar_alineacion.py` 0 brechas, `contrastar.py` verde en cada ME,
   MTO 55 OBL y 0 deudas sin resolución.

---

## 6. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Ownership de `texto` (params consumidos por el callee) | Corrupción de pool, contenido truncado | Usar `_syn_strcpy` en cada call site; test de regresión de escritura/edición (H-R204-1) |
| El compilador nativo (S2) no soporta construcciones de Fase 32 | Los módulos compilan en S1 pero no en el producto | `r243` y `r252`: reparar S1 primero, luego paridad S2 con oráculo |
| `nucleo/lsp_v3.syn` es de otro agente | Conflictos de merge | No tocarlo; planificar `r219` después de su integración |
| `llama-server` no disponible en el árbol de desarrollo | E2E no verificable | `r245`: doble hermético por defecto + job CI con servidor real |
| Tests de Fase 32 son de inspección de fuente | Falsa sensación de verde | `r247`: exigir test de comportamiento por módulo; ratio medido |
| Cambiar tests existentes | Violación de regla 5 | Aprobación previa del Arquitecto; documentar en el plan del ME |
| Citas de manual inventadas | Gate de alineación bloquea | Leer y registrar la sección real; `alineacion.py --leer` antes de codificar |
| Scope creep (MCP, cloud, multi-proveedor) | Distrae del objetivo | Manual 32 §1.3 lo excluye; no abrir frentes fuera del plan |

---

## 7. Primeros 5 MEs (arranque inmediato)

1. **`r205_grafo_conocimiento`**: leer Manual 32 §2.3-§2.6, registrar lectura,
   crear plan MTS, escribir test de comportamiento RED con un repo fixture,
   compilar `nucleo/grafo_conocimiento.syn`, retirarlo del baseline.
2. **`r206_validation_loop`**: leer Manual 7 §4.2/§6.3 y Manual 32 §6.3/§6.4,
   test RED de 3 intentos con compilador real, reparar el módulo.
3. **`r207_pipeline_multiagente`**: corregir el import del grafo, test con LLM
   falso, reparar el pipeline y cablearlo.
4. **`r215_tool_patch`**: test E2E de parche aplicado/rechazado, sandbox y
   aprobación; implementar en `opensyn/herramientas.syn`.
5. **`r216_tool_ejecutar`**: allowlist y timeout, test de comando permitido y
   denegado; implementar con la misma disciplina de ownership.

Cada uno de estos MEs debe empezar con:

```
python auditoria/registrar_lectura.py --pendientes
python auditoria/alineacion.py --leer --me <id>
```

y cerrar con:

```
.venv\Scripts\python.exe main.py <archivo> --check --no-emit
.venv\Scripts\python.exe -m pytest <tests> -v
.venv\Scripts\python.exe auditoria/verificar_alineacion.py
python auditoria/contrastar.py --plan docs/plan_ME_<id>.md
python auditoria/alineacion.py --verificar --me <id>
```

---

## 8. Lo que NO se hace en este programa

- No se toca `nucleo/lsp_v3.syn` ni los artefactos del otro agente.
- No se modifican tests existentes sin aprobación explícita del Arquitecto.
- No se añaden MCP, cloud, multi-proveedor ni telemetría (Manual 32 §1.3).
- No se "arregla" un test para que pase; si el test y el manual discrepan, se
  detiene y se pregunta.
- No se declara un módulo "reparado" solo porque compila: exige test de
  comportamiento y retiro del baseline.

---

*Plan maestro vivo. Se actualiza con cada ola y con cada decisión del
Arquitecto; la fuente de verdad sigue siendo los manuales y la memoria del
proyecto.*
