# plan_ME_27_T3 — TDD F27-F30: VS Code aiStatus/aiTranspile/aiBindings

MTS (docs/METODO_TRABAJO.md). Oráculo ejecutable; el código lleva cita grep-chequeable.

## Requisito
requisito: Manual 8 §2.3
texto: "La extensión VS Code debe exponer aiStatus, aiTranspile, aiBindings (Manual 8 §2.3)."
implementacion: Crear tests/integration/test_vscode_commands.py que invoca los comandos y valida respuesta. RED hasta vscode-synapse/extension.js.
oraculo: tests/integration/test_vscode_commands.py

**TDD:** Test TDD: el oráculo debe FALLAR (RED, @pytest.mark.tdd) hasta que el código implemente lo que dice el manual; no usa pytest.skip.

## Alcance (sin desviación)
Crea ÚNICAMENTE el test TDD indicado; no implementa el código de producción (otro ME lo hace).

## Criterio de aceptación
- El test existe y es RED (falla) por ausencia de código.
- Marcado @pytest.mark.tdd y registrado en tests/tdd/REGISTRO_TDD.md.
