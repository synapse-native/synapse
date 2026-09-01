# plan_ME_S5 — Conversión sniff→oráculo: tests/syquex/ + tests/unit/

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 3 §3 / Manual 2 §4
texto: "Los tests de frontend/semántica validan AST/comportamiento, no forma de texto."
implementacion: Convertir los tests de tests/syquex/ y tests/unit/ que usan substring de código generado sin ejecutar, a oráculos que compilan/ejecutan o validan AST.
oraculo: tests/syquex/test_scope_analysis.py

## Alcance (sin desviación)
Convierte ÚNICAMENTE los archivos del lote indicado; no toca otros directorios.

## Criterio de aceptación
- Sin assert substring sin compilar/ejecutar.
- El archivo oraculo pasa sin skip de deuda ME-4.
