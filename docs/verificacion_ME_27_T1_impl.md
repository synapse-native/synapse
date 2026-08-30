# Verificación ME — ME_27_T1_impl: LSP codeAction/formatting/signatureHelp

## Requisito 1: textDocument/codeAction — sugiere correcciones rápidas (Manual 8 §1.4)
- CUMPLE: `nucleo/lsp_v3.syn` `handle_code_action()` detecta funciones sin `retornar` y sugiere quickfix "Agregar retornar 0".
- Oráculo: `tests/integration/test_lsp_codeaction.py::TestLSPCodeAction::test_codeaction_devuelve_array` PASSED.

## Requisito 2: textDocument/formatting — formatea código según reglas de estilo (Manual 8 §1.4)
- CUMPLE: `nucleo/lsp_v3.syn` `handle_formatting()` normaliza indentación a 4 espacios y reemplaza tabs.
- Oráculo: `tests/integration/test_lsp_codeaction.py::TestLSPFormatting::test_formatting_devuelve_array` PASSED.

## Requisito 3: textDocument/signatureHelp — muestra firma de función (Manual 8 §1.4)
- CUMPLE: `nucleo/lsp_v3.syn` `handle_signature_help()` extrae nombre de función bajo cursor, busca definición en documento, retorna firma completa.
- Oráculo: `tests/integration/test_lsp_codeaction.py::TestLSPSignatureHelp::test_signaturehelp_devuelve_objeto` PASSED.

## Verificaciones adicionales
- 12/12 LSP tests PASSED (hover, completion, definition, codeAction/formatting/signatureHelp)
- verificar_alineacion.py: 0 brechas
- Sin regresión en tests existentes
