# Plan ME r279b_suite_paralela

**Fase del roadmap:** Frente H (sostenibilidad), continuación de `r279_suite_rapida`.
**Micro-entregable:** `r279b_suite_paralela`.
**Depende de:** `r279_suite_rapida` (CERRADO, `ec85c17`).
**Manuales:** Manual 1 §7.2; Manual 9 §6.2.
**Origen:** medición de `r279` (`--durations`): la suite no es lenta por pytest
sino por compilación real por test; el paralelismo por archivo es la palanca de
menor riesgo y no toca ninguna aserción.

> Alcance real de esta sesión: medir con `--durations` las suites acotadas,
> añadir `pytest-xdist` como dependencia de test y ejecutar los shards de CI en
> paralelo con `--dist loadfile`. **No se modifica ningún test**: la unidad de
> paralelismo es el archivo, porque varios tests escriben rutas fijas
> (`tests/fixtures`, `dist/bin`).

---

requisito: Manual 1 §7.2
texto: "Todo cambio debe pasar la suite completa de pruebas:"
implementacion: la suite se sigue ejecutando completa, pero repartida por archivo entre workers (`pytest-xdist`, `-n auto --dist loadfile`): cada archivo cae en un solo worker para no romper los tests que escriben rutas fijas. La medición con `--durations` identifica el coste real (en `tests/unit`, 3 tests concentran el 91% del tiempo: 172,88 s + 171,27 s + 145,22 s de 537,82 s) y sirve de línea base para comparar. Se verifica que los recuentos no cambian con el paralelismo (syquex: 281 passed / 1 skipped antes y después).
oraculo: auditoria/verificar_suite.py

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: los shards de CI (`suite-rapida`) pasan a ejecutarse con `-n auto --dist loadfile` y el job `test` conserva la suite completa y serial en la matriz 3×3 de SO/Python, que es la ley por target. La paralelización no excluye tests: los recuentos del shard deben coincidir con la línea base de composición (`auditoria/suite_baseline.json`).
oraculo: tests/auditoria/test_verificar_suite.py

## Medición que motiva el cambio

| suite | serial | paralelo (`-n auto --dist loadfile`) | recuentos |
|---|---:|---:|---|
| `tests/syquex` (282) | 112,96 s | 75,25 s (−33%) | idénticos: 281 passed, 1 skipped |
| `tests/unit` (517) | 537,82 s | — | 3 tests = 91% del tiempo |

Hallazgo **H-R279-2 (preexistente, ajeno a este ME):**
`tests/unit/test_r3_param_adt.py::test_r3_param_adt_s1/s2` falla por
`subprocess.TimeoutExpired` a los 120 s compilando con `synapse_stage1.exe` /
`synapse_stage2.exe`, también en aislamiento. El test es inmutable: se registra
con resolución asignada en `docs/plan_maestro_deudas.md`.

## Criterio de cierre

1. `python -m pytest tests/syquex -q -n auto --dist loadfile` → mismos
   recuentos que en serie (281 passed, 1 skipped) y menos tiempo.
2. `python auditoria/verificar_suite.py` → `OK: suite` con la composición
   intacta (3078 tests, 243 skips).
3. `pytest tests/auditoria/test_verificar_suite.py` 4/4.
4. `python auditoria/contrastar.py --plan docs/plan_ME_r279b_suite_paralela.md`
   PASS y `python auditoria/verificar_alineacion.py` 0 brechas.
5. Documentar en `docs/reportes/R279b.md` los tiempos medidos y el hallazgo
   H-R279-2.

## Política

Tests inmutables: sólo se añade infraestructura (dependencia de test, flags de
CI, documentación). El paralelismo se activa explícitamente y nunca sustituye
la corrida completa por target.
