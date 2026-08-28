# plan_ME_30_T1 — TDD F27-F30: Instalador unificado .iss/.sh/.dmg

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 9 §9 / F30
texto: "Scripts de instalación .iss/.sh/.dmg unificados (F30, lanzamiento)."
implementacion: Crear tests/integration/test_installer_iss_sh_dmg.py con oráculo de generación de instaladores. RED hasta F30.
oraculo: tests/integration/test_installer_iss_sh_dmg.py

**TDD:** Test TDD: el oráculo debe FALLAR (RED, @pytest.mark.tdd) hasta que el código implemente lo que dice el manual; no usa pytest.skip.

## Alcance (sin desviación)
Crea ÚNICAMENTE el test TDD indicado; no implementa el código de producción (otro ME lo hace).

## Criterio de aceptación
- El test existe y es RED (falla) por ausencia de código.
- Marcado @pytest.mark.tdd y registrado en tests/tdd/REGISTRO_TDD.md.
