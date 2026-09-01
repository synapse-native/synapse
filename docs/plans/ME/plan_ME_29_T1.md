# plan_ME_29_T1 — TDD F27-F30: Detección de hardware (std/os.syn)

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 9 §5.7 / F29
texto: "std/os.syn debe exponer detección de hardware (memoria, núcleos, VRAM) según Manual 9 §5.7."
implementacion: Crear tests/opensyn/test_os_syn_hw.py con oráculos reales contra la API. RED hasta F29.
oraculo: tests/opensyn/test_os_syn_hw.py

**TDD:** Test TDD: el oráculo debe FALLAR (RED, @pytest.mark.tdd) hasta que el código implemente lo que dice el manual; no usa pytest.skip.

## Alcance (sin desviación)
Crea ÚNICAMENTE el test TDD indicado; no implementa el código de producción (otro ME lo hace).

## Criterio de aceptación
- El test existe y es RED (falla) por ausencia de código.
- Marcado @pytest.mark.tdd y registrado en tests/tdd/REGISTRO_TDD.md.
