# plan_ME_27_T6 — TDD F27-F30: LSP completion_symbols (gap FFI RAII)

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 8 §1.4
texto: "textDocument/completion debe devolver símbolos reales del documento (Manual 8 §1.4); pendiente por crash FFI RAII."
implementacion: Crear tests/integration/test_lsp_completion_symbols.py con oráculo real de lista de símbolos. RED hasta resolver FFI RAII en completion_symbols.
oraculo: tests/integration/test_lsp_completion_symbols.py

**TDD:** Test TDD: el oráculo debe FALLAR (RED, @pytest.mark.tdd) hasta que el código implemente lo que dice el manual; no usa pytest.skip.

## Alcance (sin desviación)
Crea ÚNICAMENTE el test TDD indicado; no implementa el código de producción (otro ME lo hace).

## Criterio de aceptación
- El test existe y es RED (falla) por ausencia de código.
- Marcado @pytest.mark.tdd y registrado en tests/tdd/REGISTRO_TDD.md.
