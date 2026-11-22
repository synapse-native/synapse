# Verificación ME r280_codigo_encoding

**Plan:** `docs/plan_ME_r280_codigo_encoding.md`
**Fecha:** 2026-11-20
**Alcance:** encoding UTF-8 de fuentes de producción (comentarios/cadenas), sin
cambios de semántica; gate repo-wide con ratchet de BOM.

## Requisitos

- Manual 2 §1.2 — CUMPLE: `auditoria/verificar_encoding.py` audita 2307
  archivos versionados y reporta `0 U+FFFD, 0 C1, 0 doble codificación, 0 BOM
  nuevos`; quedan 46 BOM históricos congelados en
  `auditoria/encoding_bom_baseline.txt` (H-R280-2) y 2 fixtures UTF-16 exentos
  (H-R280-3). Evidencia: `auditoria/verificar_encoding.py`,
  `tests/auditoria/test_verificar_encoding.py` 7/7.
- Manual 1 §7.4 — CUMPLE: regresión dirigida sin regresiones:
  `tests/integration/test_axon_e2e.py` 5/5,
  `tests/integration/test_concurrency_10.py` 17/17,
  `tests/auditoria/test_oraculos_r222_std_texto.py` 4/4 y
  `tests/auditoria/test_verificar_encoding.py` 7/7. `build.py --skip-test`
  rc=0, S2==S3 `644ec933740c921a` (2.574.175 B), sello de frescura OK. La
  suite completa sigue siendo el gate de CI.
- Manual 5 §2.1 — CUMPLE: `runtime/core/concurrency.c` solo normaliza
  comentarios (fibras, scheduler M:N, pila de 64 KB); la regresión de
  concurrencia 17/17 confirma que el comportamiento no cambió.

## Gates ejecutados

- `python auditoria/verificar_encoding.py --resumen` → `OK: encoding ...`.
- `python -m pytest tests/auditoria/test_verificar_encoding.py -q` → 7 passed.
- `python -m pytest tests/integration/test_axon_e2e.py -q` → 5 passed.
- `python -m pytest tests/integration/test_concurrency_10.py -q` → 17 passed.
- `python -m pytest tests/auditoria/test_oraculos_r222_std_texto.py -q` → 4 passed.
- `python build.py --skip-test` → rc=0, bootstrap determinista S2==S3.
- `python auditoria/alineacion.py --verificar --me r280_codigo_encoding` → OK,
  5 archivos, 4 oráculos, evidencia `3830ab677863a709`.
- `python auditoria/verificar_alineacion.py` → 0 brechas.

## Límites

- El BOM histórico no se elimina en este ME: se congela con ratchet y
  `--estricto` es el criterio de cierre de H-R280-2.
- Los fixtures UTF-16 de rechazo se mantienen exentos y documentados
  (H-R280-3); no son texto fuente que deba decodificarse.
