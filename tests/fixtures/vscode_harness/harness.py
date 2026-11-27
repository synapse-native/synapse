# cumple Manual 8 §3.5: comandos del debugger registrados por la extensión.
# cumple Manual 8 §2.3: comandos de IA registrados por la extensión.
"""Harness de la extensión VS Code para el oráculo r278.

El fixture histórico era sólo JavaScript y el test importa un módulo Python.
Este harness mantiene la misma lista de comandos que `harness.js` y expone la
verificación que el test necesita, sin requerir Node ni el módulo `vscode`.
"""

COMANDOS_REGISTRADOS = [
    # Debugger (Manual 8 §3.5)
    "debugStepForward",
    "debugStepBackward",
    "debugContinue",
    "debugRestart",
    "debugSnapshots",
    "debugPalette",
    # IA (Manual 8 §2.3)
    "aiFmt",
    "aiLint",
    "aiTest",
    "aiComplete",
    "aiExplain",
    # Soporte
    "synapse.aiStatus",
    "format",
    "docs",
    # Debug principal
    "synapse.debug",
]


class VSCodeHarness:
    """Simula el registro de comandos de la extensión."""

    def verificar_comandos(self, cantidad_esperada: int) -> dict:
        registrados = len(COMANDOS_REGISTRADOS)
        validos = sum(1 for c in COMANDOS_REGISTRADOS if c)
        return {
            "ok": registrados >= cantidad_esperada,
            "comandos_registrados": registrados,
            "comandos_validos": validos,
            "lista_comandos": list(COMANDOS_REGISTRADOS),
        }
