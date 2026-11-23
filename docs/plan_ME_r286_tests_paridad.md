# Plan de Micro-Entregable r286_tests_paridad

## Objetivo

Fijar la paridad de encoding de los fixtures de test y ampliar la suite con un
oráculo que la compruebe archivo por archivo (H-R286-1). El commit `554210a` no
modificó tests: este ME añade el oráculo y verifica el estado.

## Requisito 1 — fixtures en UTF-8 sin BOM

requisito: Manual 2 §1.2
texto: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
implementacion: `tests/integration/test_r286_encoding_fixtures.py` recorre `tests/fixtures/` y `tests/integration/fixtures/` (extensiones de texto), exige decodificación UTF-8 sin U+FFFD, sin controles C1 y sin BOM, y declara explícitamente las dos exenciones UTF-16 de rechazo de `auditoria/verificar_encoding.py` (H-R280-3), fallando si dejan de ser UTF-16.
oraculo: tests/integration/test_r286_encoding_fixtures.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/integration/test_r286_encoding_fixtures.py` | 4 passed |
| `pytest tests/integration/test_axon_10.py` | 7 passed, 1 skipped |
| `auditoria/verificar_encoding.py --estricto` | OK — 0 U+FFFD, 0 C1, 0 BOM nuevos |
| `auditoria/verificar_alineacion.py` | 0 brechas |

## Hallazgos

- **H-R286-1** (ampliar suite con paridad de encoding): **RESUELTO** — oráculo nuevo de fixtures.
- **H-R286-2** (fixtures sin U+FFFD/C1): cubierto por el oráculo y por el gate repo-wide.
- **H-R286-3** (tests de contratos en runtime): cubierto por `tests/auditoria/test_verificar_contratos.py` (4/4) y `tests/integration/test_contracts.py` (5/5).
