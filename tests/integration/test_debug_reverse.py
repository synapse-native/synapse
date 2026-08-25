# -*- coding: utf-8 -*-
"""
tests/integration/test_debug_reverse.py — Manual 8 §9

Criterio: "Debugger (reversión) — Retroceso funciona"

M8 §3: reversión a puntos anteriores, breakpoints reversibles, memory snapshots.
"""
import os
import sys

import pytest

pytestmark = pytest.mark.integration

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


class TestDebuggerReverse:
    """M8 §9: reversión del debugger."""

    def test_revertir_paso(self):
        """M8 §3: retroceder un paso de ejecución."""
        runtime_debug = os.path.join(RAIZ, "runtime", "core", "debug.c")
        if not os.path.exists(runtime_debug):
            pytest.fail("runtime/core/debug.c no existe — implementar debugger (M8 §3)")
        pytest.fail("Reversión de debugger no implementada — M8 §3 requiere time-travel debugging")

    def test_revertir_multiple(self):
        """M8 §3: retroceder múltiples pasos."""
        runtime_debug = os.path.join(RAIZ, "runtime", "core", "debug.c")
        if not os.path.exists(runtime_debug):
            pytest.fail("runtime/core/debug.c no existe — implementar debugger (M8 §3)")
        pytest.fail("Reversión múltiple no implementada — M8 §3 requiere breakpoints reversibles")
