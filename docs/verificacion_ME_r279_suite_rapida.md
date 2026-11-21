# Verificación ME r279_suite_rapida

**Plan:** `docs/plan_ME_r279_suite_rapida.md`
**Fecha:** 2026-11-21
**Alcance:** infraestructura de tests (gate con ratchet, medición por suite,
shards de CI, marcador `network`). Ningún test existente se modifica.

## Requisitos

- Manual 1 §7.2 — CUMPLE: `auditoria/verificar_suite.py` mide la suite por
  suites acotadas y congela su composición en `auditoria/suite_baseline.json`
  (3078 tests recolectados, 243 skips declarados en 10 suites); falla si una
  suite pierde tests o gana skips y `--medir` cronometra
  `passed`/`skipped`/`failed` con `--comparar` contra la línea base medida.
  Los tests de red quedan opt-in (`network` declarado en `pytest.ini`,
  excluidos con `-m "not network"`). Evidencia: `auditoria/verificar_suite.py`,
  `auditoria/suite_baseline.json`, `tests/auditoria/test_verificar_suite.py`
  4/4.
- Manual 9 §6.2 — CUMPLE: `ci-tests.yml` conserva el job `test` con la suite
  completa en la matriz 3×3 de SO/Python y añade `suite-rapida` (matriz de
  shards `unit`/`integration`/`auditoria`/`opensyn`/`syquex`/`e2e`, sin red y
  con `PYTHONHASHSEED=0`) y `suite-ratchet` (recolección + ratchet en cada
  push/PR). El recuento exacto se exige en la plataforma de la línea base y en
  el resto sólo se exige que ninguna suite registrada quede en cero, porque
  los módulos importables dependen del SO. Evidencia:
  `.github/workflows/ci-tests.yml`, `auditoria/verificar_suite.py`.

## Gates ejecutados

- `python auditoria/verificar_suite.py --baseline` → línea base con 10 suites.
- `python auditoria/verificar_suite.py --resumen` → `OK: suite — 3078 tests
  recolectados en 10 suites, 243 skips declarados (sin altas)`.
- `python -m pytest tests/auditoria/test_verificar_suite.py -q` → 4 passed
  (verde con baseline, rojo con tests perdidos, rojo con skip nuevo, `--medir`
  deja recuentos y duración).
- `python auditoria/verificar_suite.py --medir --suite e2e --guardar-medido
  --json auditoria/evidencia/suite_r279.json` → `e2e`: 8 passed, 0 skipped,
  0 failed en 271,98 s (4:30), registrado en `medido.e2e` del baseline.
- `python auditoria/verificar_encoding.py` → `OK: encoding` sobre los archivos
  nuevos (gate de r280 sin regresión).

## Límites

- La corrida cronometrada de las diez suites no se ejecutó completa en esta
  sesión (la suite de integración sola supera las dos horas): el baseline
  registra la medición de `e2e` y la comparación medida queda en CI, que es
  donde la suite completa corre por target (Manual 9 §6.2).
- El ratchet compara el recuento exacto sólo en `win32` (plataforma donde se
  generó la línea base); en otra plataforma exige que ninguna suite registrada
  quede en cero y aplica siempre el ratchet de skips, que es estático.
