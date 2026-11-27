# Verificación ME_Q2 — Auditor de calidad de tests

- **Plan:** `docs/plan_ME_Q2.md`
- **Fase/Roadmap:** F27 (habilitador transversal de Workstream A)
- **Manuales aplicables:** Manual 7 §2.3 (los tests validan comportamiento real, no presencia de texto en el artefacto), Manual 3 §12.1 (estructura de módulos/tests).
- **Oráculo:** `tests/auditoria/test_auditar_calidad.py` (self-test del auditor).

## Resultado del oráculo

```
.venv\Scripts\python.exe -m pytest tests/auditoria/test_auditar_calidad.py -q
3 passed
```

## Implementación entregada

- `auditoria/auditar_calidad_tests.py`: detecta `SNIFF` (assert substring en artefacto generado sin compilar/ejecutar) y `SIN_CITA` (archivo test sin cita Manual). rc=0 si limpio, rc=1 si hay problemas → apto como gate CI.
- `tests/auditoria/test_auditar_calidad.py`: reemplaza el stub RED por self-test real (3 casos: detecta SNIFF, no falsea en test que ejecuta, detecta SIN_CITA, valida MTO).
- `docs/manuales/MANUAL_TESTS_OBLIGATORIOS.md`: corregidas 3 entradas OBL sin `Manual §` (ahora 38 validadas por el propio auditor).

## Estado: CUMPLE

El auditor está operativo y degrada rc=1 sobre el repo real (56 SIN_CITA / 48 SNIFF existentes), lo que constituye el gate CI del Workstream A. La deuda detectada se cierra en ME_S1..S6 / ME_T1..T4 / ME_X1.
