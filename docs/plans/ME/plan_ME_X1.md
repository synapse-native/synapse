# plan_ME_X1 — 83 skip TDD → xfail(strict)

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 7 §2.3 / regla 5 gobernanza
texto: "Los tests de feature no implementada no deben usar skip que enmascare regresiones; deben fallar ruidosamente si la feature se implementa distinto."
implementacion: Convertir los 83 pytest.skip('...no existe aún (TDD)') en pytest.mark.xfail(strict=True, reason='feature pendiente') en los archivos correspondientes.
oraculo: tests/opensyn/test_inference.py

## Alcance (sin desviación)
Solo transforma skips de feature-inexistente a xfail(strict); no implementa features ni toca otros asserts.

## Criterio de aceptación
- 0 skips 'no existe aún (TDD' residuales.
- Las pruebas usan xfail(strict=True).
