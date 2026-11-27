# Verificación ME r150_funcional — cierre de hallazgos funcionales R149

Fecha: 2026-09-18 · Verificador: `auditoria/contrastar.py` (gate MTS fase 4b)
Oráculos: `tests/auditoria/test_oraculos_r150.py` — **GREEN 14/14** ·
`tests/auditoria/test_matriz_compilacion.py` — **GREEN 35/35**

## M1 — Manual 1 §3 (enlace de emisores llvm/wasm) — CUMPLE
`synapse_llvm.c` / `synapse_wasm.c` en `_RT_FUENTES` de `pipeline.py:828-850`.
Oráculo OBL-R150-M1: probe E2E importando std.llvm/std.wasm con llamada inocua
— enlaza y ejecuta rc=0 (antes: "compilaba pero no enlazaba").

## M2 — Manual 5 §8.1 (work-stealing expuesto a std) — CUMPLE
`runtime/core/cluster.c:2350` implementa worker_ejecutar/worker_robar/
worker_cola_vacia sobre la cola ws_* real; declaraciones en `cluster.h:104`.
Oráculo OBL-R150-M2: probe C directo con aserciones — GREEN.

## M3a — Manual 7 §1 (bindings reales) — CUMPLE
`cli.py:1245`: subcomando bindings regenera `lib/runtime_bindings.syq` vía
subproceso y propaga rc. Oráculo OBL-R150-M3a: archivo con marcador real — GREEN.

## M3b — Manual 7 §3 (status local honesto) — CUMPLE
`cli.py:1156/1203`: status lee config real y sondea http://127.0.0.1:8088/v1/models
(timeout 2 s), lista modelos locales. 100% local, sin telemetría.
Oráculo OBL-R150-M3b: rc=0 y sin "(offline)" fijo — GREEN.

## M3c — Manual 8 §4.1 (download/finetune honestos) — CUMPLE
Sin servicio activo → mensaje claro y rc=1; jamás imprimen [OK] sin hacer nada.
Oráculo OBL-R150-M3c — GREEN.

## M3d/M4 — Manual 8 §3.4 (debugger time-travel real; construir muerto) — CUMPLE
`cli.py:34/1071`: debug --load parsea TRACE v1 real de `_syn_debug_finalizar_sesion`;
--step/--reverse/--snapshots navegan eventos reales; sin traza → rc=1 honesto.
`construir` removido del CLI (código muerto, D-R150-2 ratificada).
Oráculo OBL-R150-M3d: traza sintética → navegación real de eventos — GREEN.

## M6 — Manual 8 §4.1 (versión única) — CUMPLE
Banner de cli.py lee VERSION (única fuente de verdad); ROADMAP cabecera
8.1.0-industrial. Oráculo OBL-R150-M6: banner == VERSION — GREEN.

## M7 — Manual 1 §3 (instalador real) — CUMPLE
`scripts/verificar_e2e.py`: rutas en raw string, import sin SyntaxWarning.
Oráculo OBL-R150-M7 — GREEN.

## M13 — Manual 9 §9 (working tree limpio) — CUMPLE
`.gitignore` +`.venv-1/` +`keep/`; directorios no rastreados eliminados.
Oráculo OBL-R150-M13: raíz sin keep/ ni .venv-1/ — GREEN.

## M14 — Manual 2 §12 (suite operativa) — CUMPLE
pytest-timeout en requirements.txt; la suite corre sin
"Unknown config option: timeout" (visible en la salida de pytest: timeout: 300.0s).

## M15 — Manual 7 §2.3 (verificar() expuesto por std/testing) — CUMPLE
Wrapper verificar(condicion, nombre) en `std/testing.syn:49` (delega en
assert_verdadero). Oráculo OBL-R150-M15: probe importa std.testing y llama
verificar(1==1,"x") → compila, enlaza, PASS — GREEN.

## M16 — Manual 2 §2 (gramática: retorno opcional; sin casts inventados) — CUMPLE
`compilador/parser_declarations.py:54/314`: retorno ausente normaliza a 'nulo'
según `[ "->" tipo ]` opcional de la EBNF (L56); UnboundLocalError de
tok_retorno corregido. `std/symbolic_exec.syn`: casts `(Decimal)x` eliminados
— la coerción entero→decimal en FFI es implícita (bisección, caso F).
D-R150-10: std/agent_skills deja de definir `principal` (patrón solo de
programa, M2 §13) → demostrar_agent_skills() + contrato requiere (M2 §12).
Oráculo: matriz 35/35 incluye los módulos reparados — GREEN.

## M17 — Manual 2 §4.1 (entero = int64_t; tipos canónicos) — CUMPLE
`generator.py:898` + `emit_tensors.py:11`: prototipos builtin en int64_t
(paridad con el C emitido desde std.math/std.mem — D-R150-8). std/atp_engine.syn
y std/quantum_err_corr.syn normalizados a los tipos canónicos en minúsculas de
§4.1 (D-R150-9; los capitalizados no son aliases y producían TVar ambiguos).
Oráculo: matriz math/mem/atp_engine/quantum_err_corr GREEN — 35/35.

## Evidencia de gates (sesión 2026-09-18)
- `contrastar.py --plan docs/plan_ME_r150_funcional.md`: 14 requisitos OK,
  12 archivos vinculados, 2 oráculos ejecutados en release, verificar_alineacion
  sin brechas → "Todos los chequeos de contrastar pasaron correctamente".
- `alineacion.py --verificar --me r150_funcional`: 12 archivos, citas textuales
  verificadas, oráculos=2 ejecutados, evidencia auditoria/evidencia/*.json.
- `verificar_alineacion.py`: SIN BRECHAS.
- Regresión: 633 passed / 4 failed = línea base R149 §2.3 EXACTA (0 regresiones).
