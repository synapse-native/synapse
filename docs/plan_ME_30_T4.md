# plan_ME_30_T4 — TDD F27-F30: Release unificado (lanzamiento público)

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 9 §9 / F30 / Hito 8
texto: "Release unificado listo para lanzamiento público (Hito 8)."
implementacion: Crear tests/integration/test_release_unificado.py con oráculo de release end-to-end. RED hasta F30.
oraculo: tests/integration/test_release_unificado.py

**TDD:** Test TDD: el oráculo debe FALLAR (RED, @pytest.mark.tdd) hasta que el código implemente lo que dice el manual; no usa pytest.skip.

## Alcance (sin desviación)
Crea ÚNICAMENTE el test TDD indicado; no implementa el código de producción (otro ME lo hace).

## Criterio de aceptación
- El test existe y es RED (falla) por ausencia de código.
- Marcado @pytest.mark.tdd y registrado en tests/tdd/REGISTRO_TDD.md.
