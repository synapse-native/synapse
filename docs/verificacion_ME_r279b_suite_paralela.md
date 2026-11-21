# Verificación ME r279b_suite_paralela

**Plan:** `docs/plan_ME_r279b_suite_paralela.md`
**Fecha:** 2026-11-21
**Alcance:** medición de tiempos por suite y paralelismo por archivo con
`pytest-xdist` en los shards de CI. Ningún test se modifica.

## Requisitos

- Manual 1 §7.2 — CUMPLE: la suite se sigue ejecutando completa, repartida por
  archivo (`-n auto --dist loadfile`). Medido: `tests/syquex` **112,96 s →
  75,25 s (−33%)** con recuentos idénticos (281 passed, 1 skipped);
  `tests/integration` (5 archivos, 35 tests) 13,24 s → 14,97 s: en un conjunto
  pequeño el arranque de workers cuesta más de lo que ahorra, y el informe lo
  declara en vez de ocultarlo. `--durations=20` en `tests/unit` (537,82 s)
  muestra que 3 tests concentran el 91% del tiempo. Evidencia:
  `requirements.txt` (`pytest-xdist`), `pytest.ini`, `auditoria/verificar_suite.py`.
- Manual 9 §6.2 — CUMPLE: los shards de `suite-rapida` corren en paralelo y el
  job `test` conserva la suite completa y serial en la matriz 3×3 de SO/Python;
  la paralelización no excluye tests y la composición sigue congelada en
  `auditoria/suite_baseline.json`. Evidencia: `.github/workflows/ci-tests.yml`,
  `auditoria/verificar_suite.py`.

## Gates ejecutados

- `python -m pytest tests/syquex -q` → 281 passed, 1 skipped en 112,96 s.
- `python -m pytest tests/syquex -q -n auto --dist loadfile` → 281 passed,
  1 skipped en 75,25 s.
- `python -m pytest tests/unit -q --durations=20` → 2 failed, 515 passed en
  537,82 s (los 2 fallos son el hallazgo H-R279-2, abajo).
- `python -m pytest tests/integration/test_contracts.py test_axon_e2e.py
  test_concurrency_10.py test_compilacion_fase32.py test_debug_10.py -q` →
  35 passed en 13,24 s (serie) y 14,97 s (paralelo).
- `python auditoria/verificar_suite.py` → composición intacta.
- `python auditoria/verificar_encoding.py` → `OK: encoding`.

## Hallazgo H-R279-2 (preexistente, registrado)

`tests/unit/test_r3_param_adt.py::test_r3_param_adt_s1` y
`::test_r3_param_adt_s2` fallan con `subprocess.TimeoutExpired` a los 120 s al
compilar con `synapse_stage1.exe` / `synapse_stage2.exe`; se reprodujo **en
aislamiento** (2 failed en 250,41 s), así que no es interferencia del
paralelismo ni de este ME. El test es inmutable: queda registrado en
`docs/plan_maestro_deudas.md` con resolución asignada (medir el tiempo real de
ese comando nativo y decidir entre timeout justificado o defecto de la ruta
S1/S2).

## Límites

- La suite de integración completa (>2 h en serie) no se midió entera; el
  subconjunto de 35 tests sirve para comprobar que el paralelismo no cambia
  recuentos, no para estimar el ahorro total.
- El paralelismo no se fuerza en `addopts`: se activa explícitamente
  (`-n auto --dist loadfile`) porque varios tests escriben rutas fijas
  (`tests/fixtures`, `dist/bin`) y la unidad segura es el archivo.
