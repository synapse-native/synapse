# plan_ME_27_T4 — TDD F27-F30: Debugger time-travel + breakpoints reversibles

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 8 §5.2/§5.3/§5.4
texto: "Debugger integrado con time-travel, snapshots y breakpoints reversibles (Manual 8 §5)."
implementacion: Crear tests/integration/test_debugger_timetravel.py que graba ejecución y revierte. RED hasta std/debug.syn + runtime/core/debug.c.
oraculo: tests/integration/test_debugger_timetravel.py

**TDD:** Test TDD: el oráculo debe FALLAR (RED, @pytest.mark.tdd) hasta que el código implemente lo que dice el manual; no usa pytest.skip.

## Alcance (sin desviación)
Crea ÚNICAMENTE el test TDD indicado; no implementa el código de producción (otro ME lo hace).

## Criterio de aceptación
- El test existe y es RED (falla) por ausencia de código.
- Marcado @pytest.mark.tdd y registrado en tests/tdd/REGISTRO_TDD.md.
