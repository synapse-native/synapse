# plan_ME_27_T2 — TDD F27-F30: LSP workspace/didChangeConfiguration

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 8 §1.4
texto: "El LSP debe manejar workspace/didChangeConfiguration (Manual 8 §1.4)."
implementacion: Crear tests/integration/test_lsp_workspace.py con oráculo real. RED hasta implementación.
oraculo: tests/integration/test_lsp_workspace.py

**TDD:** Test TDD: el oráculo debe FALLAR (RED, @pytest.mark.tdd) hasta que el código implemente lo que dice el manual; no usa pytest.skip.

## Alcance (sin desviación)
Crea ÚNICAMENTE el test TDD indicado; no implementa el código de producción (otro ME lo hace).

## Criterio de aceptación
- El test existe y es RED (falla) por ausencia de código.
- Marcado @pytest.mark.tdd y registrado en tests/tdd/REGISTRO_TDD.md.
