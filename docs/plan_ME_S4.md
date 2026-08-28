# plan_ME_S4 — Conversión sniff→oráculo: tests/integration/ lote 2

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 5 §6 / Manual 11 (F11)
texto: "Cluster/release/signing validan comportamiento real."
implementacion: Convertir test_cluster_*.py, test_release_matrix.py, test_artifact_signing.py de substring a oráculos conductuales (contra símbolos/constantes reales o ejecución).
oraculo: tests/integration/test_release_matrix.py

## Alcance (sin desviación)
Convierte ÚNICAMENTE los archivos del lote indicado; no toca otros directorios.

## Criterio de aceptación
- Sin assert substring sin compilar/ejecutar.
- El archivo oraculo pasa sin skip de deuda ME-4.
