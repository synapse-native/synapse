# plan_ME_T4 — Trazabilidad al manual: Barrido de 62 archivos sin cita + cobertura M8

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 8 §1.4 (fase activa)
texto: "Toda prueba cita un manual; la fase actual F27 (M8) debe tener trazabilidad >90%."
implementacion: Añadir 'Manual X §Y' a los 62 archivos sin cita según funcionalidad; elevar cobertura de citas M8 a >90% (hoy 19).
oraculo: docs/manuales/MANUAL_TESTS_OBLIGATORIOS.md

## Alcance (sin desviación)
Solo añade citas de manual a los archivos indicados; no altera asserts.

## Criterio de aceptación
- Los archivos citan Manual X §Y.
- Cobertura de cita M8 sube a >90%.
