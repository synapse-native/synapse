# plan_ME_T3 — Trazabilidad al manual: test_cluster_*.py, test_release_matrix.py, test_artifact_signing.py

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 5 §6 / Manual 11 (F11)
texto: "Pruebas de cluster/release/signing citan el manual correspondiente."
implementacion: Añadir citas Manual 5 §6 / Manual 11 a test_cluster_*.py (×6), test_release_matrix.py, test_artifact_signing.py.
oraculo: tests/integration/test_release_matrix.py

## Alcance (sin desviación)
Solo añade citas de manual a los archivos indicados; no altera asserts.

## Criterio de aceptación
- Los archivos citan Manual X §Y.
- Cobertura de cita M8 sube a >90%.
