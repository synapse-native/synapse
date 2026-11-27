# plan_ME_Q2 — Auditor de calidad de tests

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 7 §2.3 / Manual 3 §12.1
texto: "Los tests validan comportamiento real, no la presencia de texto en el artefacto generado; y toda prueba cita el manual."
implementacion: Crear auditoria/auditar_calidad_tests.py: detecta (a) SNIFF = assert substring en c/syq/salida SIN compilar_texto/subprocess/.exe/gcc; (b) SIN_CITA = archivo test sin 'Manual N'. Salida rc!=0 en CI. Crear tests/auditoria/test_auditar_calidad.py (fixtures sniff y limpio).
oraculo: tests/auditoria/test_auditar_calidad.py

## Alcance (sin desviación)
Solo crea herramienta de auditoría y su self-test; no modifica tests existentes.

## Criterio de aceptación
- El script existe y rc=0 sobre fixtures de ejemplo.
- Detecta un test sniff y uno limpio correctamente.
