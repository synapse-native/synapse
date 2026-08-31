# plan_ME_29_T3 — TDD F27-F30: Gestión de modelos OpenSyn

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 7 §2.3 / F29
texto: "OpenSyn debe gestionar modelos (descargar/cachear) según F29."
implementacion: Crear tests/opensyn/test_model_mgmt.py con oráculos de gestión. RED hasta F29.
oraculo: tests/opensyn/test_model_mgmt.py

**TDD:** Test TDD: el oráculo debe FALLAR (RED, @pytest.mark.tdd) hasta que el código implemente lo que dice el manual; no usa pytest.skip.

## Alcance (sin desviación)
Crea ÚNICAMENTE el test TDD indicado; no implementa el código de producción (otro ME lo hace).

## Criterio de aceptación
- El test existe y es RED (falla) por ausencia de código.
- Marcado @pytest.mark.tdd y registrado en tests/tdd/REGISTRO_TDD.md.
