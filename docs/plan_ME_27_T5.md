# plan_ME_27_T5 — TDD F27-F30: CLI run/debug/opensyn

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 8 §4.2 / §5 / §7
texto: "El CLI debe tener subcomandos run, debug, opensyn (Manual 8 §4.2/§5/§7)."
implementacion: Crear tests/integration/test_cli_run_debug.py que invoca synapse run/debug/opensyn. RED hasta cli.py.
oraculo: tests/integration/test_cli_run_debug.py

**TDD:** Test TDD: el oráculo debe FALLAR (RED, @pytest.mark.tdd) hasta que el código implemente lo que dice el manual; no usa pytest.skip.

## Alcance (sin desviación)
Crea ÚNICAMENTE el test TDD indicado; no implementa el código de producción (otro ME lo hace).

## Criterio de aceptación
- El test existe y es RED (falla) por ausencia de código.
- Marcado @pytest.mark.tdd y registrado en tests/tdd/REGISTRO_TDD.md.
