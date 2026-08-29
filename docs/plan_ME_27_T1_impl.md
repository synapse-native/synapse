# Plan ME: Implementar LSP codeAction/formatting/signatureHelp

## Problema

Los handlers `handle_code_action`, `handle_formatting`, `handle_signature_help` en
`nucleo/lsp_v3.syn` son stubs que devuelven respuestas vacías. El test TDD
`test_lsp_codeaction.py` es un placeholder `pytest.fail`.

## Requisitos

requisito: Manual 8 §1.4
texto: "textDocument/codeAction — Sugiere correcciones rápidas (refactorización).
  textDocument/formatting — Formatea el código según las reglas de estilo.
  textDocument/signatureHelp — Muestra la firma de la función mientras se escribe."
implementacion: Implementar handlers reales en lsp_v3.syn + test real en test_lsp_codeaction.py.
oraculo: tests/integration/test_lsp_codeaction.py

## Alcance por handler

### codeAction
- Retornar acciones vacías si no hay diagnósticos (comportamiento correcto)
- Futuro: quick fixes para ERR_SEM_* ( fuera de alcance de este ME)

### formatting
- Normalizar indentación a 4 espacios
- Eliminar espacios trailing
- Preservar estructura de código

### signatureHelp
- Buscar función en la posición del cursor
- Retornar firma con parámetros y tipo de retorno

## Cambios

| Archivo | Cambio |
|---|---|
| `nucleo/lsp_v3.syn` | Implementar handle_code_action, handle_formatting, handle_signature_help |
| `tests/integration/test_lsp_codeaction.py` | Reemplazar placeholder con test real |

## Validación

1. `python -m pytest tests/integration/test_lsp_codeaction.py -v` — PASS
2. `python -m pytest tests/integration/test_lsp_*.py -v` — 0 regresiones
3. `python auditoria/verificar_alineacion.py` — 0 brechas
4. `python auditoria/contrastar.py --plan docs/plan_ME_27_T1_impl.md` — gate
