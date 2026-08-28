# plan_ME_S2 — Conversión sniff→oráculo: tests/opensyn/ restantes

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 7 §2.3 / Manual 7 §7
texto: "Oráculos reales sobre la API ya implementada, no content-sniff."
implementacion: Convertir test_inference.py, test_download.py, test_detect_hardware.py, test_bindings.py: reemplazar skips/interinas y substring por asserts de contrato/contra la API real o compilación del artefacto.
oraculo: tests/opensyn/test_inference.py

## Alcance (sin desviación)
Convierte ÚNICAMENTE los archivos del lote indicado; no toca otros directorios.

## Criterio de aceptación
- Sin assert substring sin compilar/ejecutar.
- El archivo oraculo pasa sin skip de deuda ME-4.
