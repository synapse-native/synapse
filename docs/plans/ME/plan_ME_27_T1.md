# plan_ME_27_T1 — TDD F27-F30: LSP codeAction + formatting + signatureHelp

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 8 §1.4
texto: "El LSP debe implementar textDocument/codeAction, formatting y signatureHelp (Manual 8 §1.4)."
implementacion: Crear tests/integration/test_lsp_codeaction.py con oráculos reales (llamar al LSP y validar respuesta de codeAction/formatting/signatureHelp). RED hasta que nucleo/lsp.syn lo implemente.
oraculo: tests/integration/test_lsp_codeaction.py

**TDD:** Test TDD: el oráculo debe FALLAR (RED, @pytest.mark.tdd) hasta que el código implemente lo que dice el manual; no usa pytest.skip.

## Alcance (sin desviación)
Crea ÚNICAMENTE el test TDD indicado; no implementa el código de producción (otro ME lo hace).

## Criterio de aceptación
- El test existe y es RED (falla) por ausencia de código.
- Marcado @pytest.mark.tdd y registrado en tests/tdd/REGISTRO_TDD.md.
