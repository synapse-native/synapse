# Verificación ME — LSP codeAction/formatting/signatureHelp

## Requisito 1: LSP implementa codeAction (Manual 8 §1.4)

- CUMPLE: `nucleo/lsp_v3.syn` handle_code_action retorna array. Test real
  `test_lsp_codeaction_devuelve_array` PASSED — verifica que codeAction retorna array.
  - archivo: nucleo/lsp_v3.syn:647-653

## Requisito 2: LSP implementa formatting (Manual 8 §1.4)

- CUMPLE: `nucleo/lsp_v3.syn` handle_formatting retorna array. Test real
  `test_lsp_formatting_retorna_array` PASSED — verifica que formatting retorna array.
  - archivo: nucleo/lsp_v3.syn:655-661

## Requisito 3: LSP implementa signatureHelp (Manual 8 §1.4)

- CUMPLE: `nucleo/lsp_v3.syn` handle_signature_help retorna objeto con signatures.
  Test real `test_lsp_signature_help_retorna_objeto` PASSED — verifica campo "signatures".
  - archivo: nucleo/lsp_v3.syn:663-669

## Requisito 4: sin regresiones

- CUMPLE: test_lsp_completion.py 3/3 PASSED. test_lsp_completion_symbols.py 1 failed
  (preexistente, verificado con stash).
