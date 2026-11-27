# plan_ME_S3 — Conversión sniff→oráculo: tests/integration/ lote 1

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 8 §1.4 / §1.2
texto: "LSP/diagnostics validan comportamiento del protocolo, no texto."
implementacion: Convertir test_diagnostics.py, test_lsp_native.py, test_cli.py de sniff a oráculos conductuales (compilar/ejecutar o contra API real).
oraculo: tests/integration/test_diagnostics.py

## Alcance (sin desviación)
Convierte ÚNICAMENTE los archivos del lote indicado; no toca otros directorios.

## Criterio de aceptación
- Sin assert substring sin compilar/ejecutar.
- El archivo oraculo pasa sin skip de deuda ME-4.
