# plan_ME_T2 — Trazabilidad al manual: test_bootstrap_10.py, test_frontend_embebido_*.py

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 9 §9.1 / §9.7
texto: "Bootstrap S1→S2→S3 byte-idéntico debe ser verificable y citado."
implementacion: Añadir cita 'Manual 9 §9.1/§9.7' a test_bootstrap_10.py y tests/integration/test_frontend_embebido_*.py.
oraculo: tests/integration/test_bootstrap_10.py

## Alcance (sin desviación)
Solo añade citas de manual a los archivos indicados; no altera asserts.

## Criterio de aceptación
- Los archivos citan Manual X §Y.
- Cobertura de cita M8 sube a >90%.
