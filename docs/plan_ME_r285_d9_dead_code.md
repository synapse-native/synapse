# Plan de Micro-Entregable r285_d9_dead_code

## Objetivo

Cumplir D-9 en `std/texto.syn`: eliminar el bloque duplicado H-R196-2 y
conservar los contratos de las funciones públicas. El trabajo de deduplicación
se ejecutó en el commit `8a2f82b` (r281): `std/texto.syn` pasó de 28 funciones
(275 líneas) a 10 funciones (129 líneas). Este ME verifica y fija ese estado.

## Requisito 1 — contratos en las funciones públicas

requisito: Manual 2 §12
texto: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
implementacion: `std/texto.syn` conserva `requiere:`/`garantiza:` en sus funciones públicas tras eliminar las 12 funciones duplicadas de H-R196-2; el oráculo verifica que no reaparezcan duplicados, que el archivo no vuelva a crecer y que los contratos sigan presentes.
oraculo: tests/auditoria/test_r285_dedup_texto.py

## Requisito 2 — Definition of Done sin código muerto

requisito: Manual 1 §7.4
texto: "- Aprobación del 100% de los tests unitarios, de integración y fuzzing sin regresiones."
implementacion: la poda no cambia el comportamiento: `tests/integration/test_axon_10.py` (7 passed, 1 skipped) y `tests/auditoria/test_r285_dedup_texto.py` pasan sobre el archivo deduplicado; `verificar_alineacion` sigue en 0 brechas.
oraculo: tests/auditoria/test_r285_dedup_texto.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r285_dedup_texto.py` | 3 passed |
| `pytest tests/integration/test_axon_10.py` | 7 passed, 1 skipped |
| Funciones con nombre duplicado | 0 |
| `auditoria/verificar_alineacion.py` | 0 brechas |

## Hallazgos

- **H-R196-2**: **RESUELTO** en `8a2f82b` (28→10 funciones, 275→129 líneas).
- **H-R285-1** (módulos >1200): cubierto por el gate R13 del verificador (registrados en D-9).
- **H-R285-2** (código muerto en otros `.syn`): sin barrido nuevo; el gate actual detecta tamaño y contratos, no funciones sin llamadas.
