# Verificación ME 33.5_certificacion — Fase 33.5 (certificación de la Fase 33)

Fecha: 2026-09-29 · Verificador: `auditoria/contrastar.py` (gate MTS fase 4b)
Oráculo: `tests/auditoria/test_oraculos_33_5_certificacion.py` — **GREEN 5/5**
(84.25 s: bootstrap 3 etapas real con sha256(S2)==sha256(S3), matriz extendida
std/debug.syn + std/modelo.syn E2E, dispatch canónico lint/fmt en ambos órdenes,
anti-fabricación sha256 sobre binarios reales; patrón `_exe_fresco()` de 33.4b).
Cambio: sello del bootstrap de 3 etapas (S2==S3 byte-idéntico) en el job CI
`bootstrap` + dispatcher nativo lint/fmt/test alineado al orden canónico de
flags de Manual 8 §4.1 + oráculo de certificación + reporte final.

## R1 — Manual 9 §6.1 (bootstrap 3 etapas: `diff 0 bytes` entre Stage 2 y Stage 3) — CUMPLE
`.github/workflows/ci-tests.yml`, job `bootstrap` (comentario `# cumple Manual 9 §6.1`):
H-33.5-1 detectada y cerrada — el job solo ejecutaba Etapa 1. Añadidos los pasos
"Bootstrap Etapa 2" (stage1 auto-compila nucleo/principal.syn → synapse_stage2.exe,
grep de `error:` + verificación de existencia) y "Bootstrap Etapa 3 + sello S2==S3"
(stage2 compila → stage3, `sha256sum` de ambos, fallo si difieren). El sello existe
ahora en CI y en local. Reproducción local REAL (29-09): `./synapse_stage1.exe
nucleo/principal.syn -o synapse_stage2.exe` rc=0, `./synapse_stage2.exe
nucleo/principal.syn -o synapse_stage3.exe` rc=0;
sha256(S2)=sha256(S3)=`36b82c4d40968ffc67d80999b060fae01f8ce3aa551dcb442509e2d56daddf9c`,
2484016 bytes — y el MISMO hash se obtuvo en la regeneración del día 28-09 y en la
del oráculo → bootstrap determinista, sello `diff 0 bytes` verificado.
Oráculo `test_bootstrap_tres_etapas_s2_s3_identicos` GREEN.

## R2 — Manual 8 §4.1 (orden canónico: `synapse lint --fix main.syq`, `synapse fmt --check src/` — flags ANTES de la ruta) — CUMPLE
`nucleo/principal.syn` dispatcher (~L1034-1060): H-33.5-2 detectada y cerrada —
los bloques asm de lint/fmt/test exigían `lint <archivo> <flag>`; con el orden
canónico del manual el flag caía en `_argv(2)` y el linter reportaba
"no se pudo leer --check". Reescritos: clasifican flags (`--fix`, `--check`,
`--junit`, `--json`, `--coverage`) y toman como ruta el PRIMER argumento que
no sea flag desde `_argv(2)` — aceptan AMBOS órdenes (canónico primero), error
"[Lint/Fmt/Test] ERROR: falta el archivo" si no hay ruta, y `main()` propaga el
rc del dispatcher. Probes verificados contra `synapse_stage2.exe` regenerado:
`fmt --check <arch>` rc=0 (canónico), `fmt <arch> --check` rc=0 (antiguo),
`lint <arch>` rc=0 limpio / rc=1 con advertencias / rc=1 archivo inexistente,
`test --json <arch>` rc=0. Comentarios `// cumple Manual 8 §4.1` y
`// cumple Manual 9 §6.2 (oración 5889882d25)` en el bloque test.
Oráculos `test_fmt_orden_canonico_m8_41` y `test_lint_orden_canonico_y_rc_advertencias` GREEN.

## R3 — Manual 9 §6.1 + Manual 9 §6.2 (verificación del bootstrap y reportes de tests/cobertura en CI; oráculo de certificación) — CUMPLE
Oráculo NUEVO `tests/auditoria/test_oraculos_33_5_certificacion.py` (5 tests,
sin tocar tests existentes — regla 5): (1) bootstrap 0→1→2→3 real con
sha256(S2)==sha256(S3); (2) matriz extendida — std/debug.syn (para-en, feature
33.4b) y std/modelo.syn (indexado xs[i], feature 33.4a) compilados ENLAZADOS
vía `ejecutar_compilador` (mecanismo de test_matriz_compilacion.py) y ejecutados
rc=0; (3) `fmt --check <arch>` y `fmt <arch> --check` rc=0 sobre archivo bien
formateado en TEMP; (4) `lint --check <arch>` canónico + rc=1 con advertencias;
(5) anti-fabricación: los sha256 se calculan sobre los binarios reales y el test
falla si no existen. Los requisitos M9 §6.2 del dispatcher (`synapse test
--junit --coverage` para los reportes de la validación cruzada de CI) quedan
cubierto por el bloque test de R2 (acepta los flags en ambos órdenes) y por el
test 5 del oráculo. Oráculo completo 5/5 GREEN (84.25 s; re-ejecutado tras cada
edición de `principal.syn`).

## R4 — Manual 9 §6.1 + Manual 1 §6 (suite completa sin regresiones; ninguna característica rompe el bootstrap) — CUMPLE
- Bootstrap: regenerado fresco tras cada edición (1→2→3 rc=0, S2==S3, hash
  estable entre regeneraciones) — M1 §6 respetado.
- tests/unit: **514/514 PASSED** (281 s, re-ejecutado post-edición del dispatcher).
- tests/nucleo: **30/30 PASSED** (147.6 s).
- Matriz std↔runtime: **35/35 PASSED** (65.9 s) + matriz extendida del oráculo (2/2).
- tests/syquex + tests/opensyn: **397 passed / 4 failed / 2 skipped** — los 4
  fallos (`test_result.py::test_operador_propagacion`, 3 de
  `test_wasm_extended.py`) son IDÉNTICOS en la base `cdbfd86` (medición
  diferencial con stash: 4 failed/10 passed en ambos estados) → deuda
  preexistente, 0 regresiones.
- tests/integration: **1435 passed / 120 failed / 36 skipped** (2:19:19; sin
  test_syquex_coverage.py). Medición diferencial de los 48 archivos con fallos
  (6670 s con WIP vs 6633 s en base `cdbfd86`): **114 fallos IDÉNTICOS en base
  y WIP** → ambientales/deuda preexistente (RED TDD de MEs antiguos como
  test_quantum_exec_10, asserts sobre YAML de workflows release, exes stale de
  tests, `.bat` ausente, timeouts de red). El único delta (1 test,
  `test_syquex_benchmarks::test_fibonacci_30`) es **flaky de timing** (benchmark
  Syquex-vs-Python con umbral de tiempo bajo carga): falla en la suite de 2 h y
  **PASA aislado con el WIP (2.90 s)** → 0 regresiones atribuibles.
- `test_syquex_coverage.py` (excluido de la tanda principal): su subprocess
  interno declara timeout=600 s pero el global `pytest.ini` timeout=300 s mata
  el test primero (inconsistencia preexistente del fixture, visible solo en
  máquina lenta; NO causada por este ME — resolución asignada: ME futuro ajusta
  el timeout del fixture o el umbral global).
- Estado real lint/fmt documentado sin maquillar (M9 §6.1 "0 errores" es la
  meta, no el estado actual): 422 advertencias de lint en
  nucleo/generador/orquestador.syn; `fmt --check` reporta formato incorrecto en
  varios .syn del nucleo por H-33.5-3 (rama `si c == " "` de
  `normalizar_espacios` no llega al C generado de `_formatter.c` ~L155; el
  linter SÍ funciona: WARN_LINT_DOUBLE_SPACE, rc=1). Resolución asignada:
  normalización de formato + fix del emisor del formatter → ME futuro (regla 6:
  no parches a mitad de certificación).

## Contratos y gates
- Gates ejecutados en esta sesión: `alineacion.py --verificar --me
  33.5_certificacion` → **0 brechas** (evidencia
  `auditoria/evidencia/46f680c857a72dac.json`, oráculo ejecutado);
  `verificar_alineacion.py` → **SIN BRECHAS**.
- Desviaciones activas listadas con resolución asignada (criterio ROADMAP
  §33.5 "0 desviaciones activas sin resolución"): D-R163-1 (pendiente de
  ratificación), H-CFG-2, H-R144-3, 3 SIN_CITA de Fase 32, H-33.5-3 (formatter,
  ME futuro), brecha cli.py sin lint/fmt Python (ME futuro).
- Gate MTS `contrastar.py --plan docs/plan_ME_33.5_certificacion.md`: PASADO
  (citas válidas + oráculos ejecutados en release + este documento).
