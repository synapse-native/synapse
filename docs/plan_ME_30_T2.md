# plan_ME_30_T2 — TDD F27-F30: Makefile / build.py

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 9 §9 / F30
texto: "Build unificado vía Makefile/build.py (F30)."
implementacion: Crear tests/integration/test_build_py.py con oráculo de build reproducible. RED hasta F30.
oraculo: tests/integration/test_build_py.py

**TDD:** Test TDD: el oráculo debe FALLAR (RED, @pytest.mark.tdd) hasta que el código implemente lo que dice el manual; no usa pytest.skip.

## Alcance (sin desviación)
Crea ÚNICAMENTE el test TDD indicado; no implementa el código de producción (otro ME lo hace).

## Criterio de aceptación
- El test existe y es RED (falla) por ausencia de código.
- Marcado @pytest.mark.tdd y registrado en tests/tdd/REGISTRO_TDD.md.
