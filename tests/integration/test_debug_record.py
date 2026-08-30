# -*- coding: utf-8 -*-
"""
tests/integration/test_debug_record.py — Manual 8 §9

Criterio: "Debugger (grabación) — Traza generada correctamente"

M8 §3: grabación de ejecución, debug.iniciar_sesion(), debug.guardar_traza().
"""
import os
import sys
import subprocess
import tempfile

import pytest

pytestmark = pytest.mark.integration

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _buscar_python():
    for p in [os.path.join(RAIZ, ".venv", "Scripts", "python.exe"),
              os.path.join(RAIZ, ".venv", "bin", "python"),
              "python", "python3"]:
        try:
            subprocess.run([p, "--version"], capture_output=True, timeout=5)
            return p
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


class TestDebuggerRecord:
    """M8 §9: grabación de traza del debugger."""

    def test_grabar_traza(self):
        """M8 §3: debug.guardar_traza genera archivo de traza."""
        python = _buscar_python()
        if python is None:
            pytest.fail("Python no encontrado")
        # Verificar que std.debug existe en el runtime
        runtime_debug = os.path.join(RAIZ, "runtime", "core", "debug.c")
        if not os.path.exists(runtime_debug):
            pytest.fail("runtime/core/debug.c no existe — implementar debugger (M8 §3)")
        # El test falla si el módulo debug no está implementado
        pytest.fail("debug.guardar_traza no implementado — M8 §3 requiere grabación de traza")

    def test_traza_contiene_pasos(self):
        """M8 §3: la traza contiene eventos de ejecución."""
        runtime_debug = os.path.join(RAIZ, "runtime", "core", "debug.c")
        if not os.path.exists(runtime_debug):
            pytest.fail("runtime/core/debug.c no existe — implementar debugger (M8 §3)")
        pytest.fail("Eventos de traza no implementados — M8 §3 requiere DebugEvento")
