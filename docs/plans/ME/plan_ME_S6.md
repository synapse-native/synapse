# plan_ME_S6 — Conversión sniff→oráculo: tests/security/ + tests/fuzz/ + tests/stress/

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 12 (seguridad) / Manual 3 §12.1
texto: "Tests de seguridad/fuzz validan comportamiento observable, no substring."
implementacion: Convertir los tests de tests/security/, tests/fuzz/, tests/stress/ que usan substring de artefacto sin ejecutar, a oráculos conductuales.
oraculo: tests/security/test_security.py

## Alcance (sin desviación)
Convierte ÚNICAMENTE los archivos del lote indicado; no toca otros directorios.

## Criterio de aceptación
- Sin assert substring sin compilar/ejecutar.
- El archivo oraculo pasa sin skip de deuda ME-4.
