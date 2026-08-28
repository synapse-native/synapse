# plan_ME_28_T1 — TDD F27-F30: Certificación Syquex v1.0 (Hito 7) - parte 1

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 3 (certificación)
texto: "Syquex debe certificarse v1.0: conformidad del frontend con el manual (Hito 7, F28)."
implementacion: Crear tests/integration/test_syquex_cert_1.py con oráculos de certificación extraídos de M3. RED hasta F28.
oraculo: tests/integration/test_syquex_cert_1.py

**TDD:** Test TDD: el oráculo debe FALLAR (RED, @pytest.mark.tdd) hasta que el código implemente lo que dice el manual; no usa pytest.skip.

## Alcance (sin desviación)
Crea ÚNICAMENTE el test TDD indicado; no implementa el código de producción (otro ME lo hace).

## Criterio de aceptación
- El test existe y es RED (falla) por ausencia de código.
- Marcado @pytest.mark.tdd y registrado en tests/tdd/REGISTRO_TDD.md.
