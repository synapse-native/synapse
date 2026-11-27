import pytest

pytestmark = pytest.mark.integration

# Harness simula la extensión VS Code para probar el registro de comandos
def test_vscode_harness_r278():
    """Verifica que la extensión VS Code registre 15 comandos de debugger."""
    from tests.fixtures.vscode_harness.harness import VSCodeHarness

    harness = VSCodeHarness()
    resultado = harness.verificar_comandos(15)

    assert resultado["ok"], f"Expected HARNESS OK, got: {resultado}"
    assert resultado["comandos_registrados"] == 15, \
        f"Expected 15 commands, got {resultado['comandos_registrados']}"
    assert resultado["comandos_validos"] >= 15, \
        f"Expected >= 15 valid commands, got {resultado['comandos_validos']}"

    # Verificar comandos clave
    comandos_requeridos = [
        "debugStepForward", "debugStepBackward",
        "debugContinue", "debugRestart",
        "debugSnapshots", "aiFmt", "aiLint", "aiTest"
    ]
    for cmd in comandos_requeridos:
        assert cmd in resultado["lista_comandos"], \
            f"Required command '{cmd}' not found in registered commands"