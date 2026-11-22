// Documento informativo; la ley es docs/manuales/
# R198b2 — Barrido de cierre (2026-10-28)

**Objetivo:** regresión completa del ME r198b2_ancla (dd20276) corriendo la
suite `tests/auditoria` COMPLETA fuera del timeout de 600 s (la familia del
gate ya había pasado 19/19 dentro del ME).

## Resultado

- **222 tests: 214 passed, 7 failed, 1 skipped — 49:51** (timeout por-test 300 s,
  release).
- Las 7 fallas reproducen de forma DETERMINISTA en aislamiento (7/7 en
  153 s): no son contaminación de orden del barrido.
- **R198b2: 0 regresiones.** `test_paridad_nodos.py` 4/4 GREEN dentro del
  barrido (incluido `test_emision_s1_cita_los_nodos_canonicos` — cierre
  H-R198b1-2 confirmado bajo la carga del barrido completo). Ninguna de las
  7 fallas toca `compilador/puente_canonico.py` ni su familia de paridad.

## Hallazgos (4 deudas nuevas a cola, H-R198b2-1..4)

1. **H-R198b2-1 — exes stale ambientales (2 tests):**
   `test_r3_binario_synapse_check` (synapse_stage2.exe anterior a
   `nucleo/coverage.syn`, lección R180-2) y
   `test_guard_frescura_exe_vs_ultimo_commit_fuente` (H-AUD-OP-2:
   `dist/bin/opensyn.exe` 2026-09-26 anterior a `opensyn/principal.syn`
   2026-10-27 — f10401f R198b). Fix: regenerar exes
   (`.venv/Scripts/python.exe main.py opensyn/principal.syn -o
   dist/bin/opensyn.exe`; stage2 con bootstrap determinista). ME corto.
2. **H-R198b2-2 — familia fmt/lint de stage2 (3 tests):**
   `test_fmt_detecta_y_colapsa_espacios` (`fmt --check` rc=0, esperado 1 —
   H-33.5-3), `test_nucleo_formateado` (timeout 120 s sobre
   `nucleo/generator.syn`), `test_dispatch_lint_orden_canonico_m8_41`
   (lint no lee el Temp `bueno.syn`). ME propio de fmt/lint.
3. **H-R198b2-3 — contrato-test desalineado (1 test):**
   `test_r2_binding_std_io_syn` espera `stdin_eof` con
   `resultado == 0 o resultado == 1` y `std/io.syn` lleva `_resultado_`
   (alias canónico M2 §5.1 de f10401f R198b). Dirección: ALINEAR EL TEST
   AL MANUAL por TDD CON aprobación previa y explícita del Arquitecto
   (tests inmutables, regla infrictible: si test y manual discrepan se
   detiene y pregunta).
4. **H-R198b2-4 — oráculo R198b1 con fixture de fecha literal (1 test):**
   `test_resane_end_to_end_expediente_con_hash_anulado` exige ver SOLO la
   brecha de hash, pero el `.antes.json` del caso lleva `fecha: 2026-10-27`
   y al rotar el día la segunda brecha (sello de lectura expirado) entra
   y el resane (correcto) exige expediente fresco. El mecanismo hizo su
   trabajo; el FIXTURE no es independiente de la fecha: debe sellarse con
   la fecha de HOY. ME corto del oráculo (test propio, modificable del
   ME que lo creó con aprobación del Arquitecto).

## Clasificación final

4 deudas nuevas registradas en la cola maestro (bloque R198b2 del plan
maestro); ninguna bloquea la integración (los 4 grupos son
ambientales/fmt/fixture TEST-side). El ME r198b2_ancla quedó verificado
por la familia del gate 19/19 + paridad_nodos 4/4 en el barrido completo.
