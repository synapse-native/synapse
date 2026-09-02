# plan_ME_T1 — Trazabilidad al manual: test_lsp_native.py, test_diagnostics.py

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 8 §1.4
texto: "Las pruebas LSP citan el manual y validan el comportamiento del protocolo."
implementacion: Añadir cita 'Manual 8 §1.4' (y §1.2 donde aplique) y oráculo conductual M8 a test_lsp_native.py y test_diagnostics.py.
oraculo: tests/integration/test_lsp_native.py

## Alcance (sin desviación)
Solo añade citas de manual a los archivos indicados; no altera asserts.

## Criterio de aceptación
- Los archivos citan Manual X §Y.
- Cobertura de cita M8 sube a >90%.
