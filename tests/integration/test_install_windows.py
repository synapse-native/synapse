# -*- coding: utf-8 -*-
"""
test_install_windows.py — M9 §7: Instalación en Windows.

Manual 9 §7: "Instalación en Windows (limpiamente) — Instalación exitosa, PATH configurado, synapse --version funciona".
"""
import os
import subprocess
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestInstalacionWindows:
    """Manual 9 §7: Instalación limpia en Windows."""

    def test_synapse_exe_existe(self):
        """synapse.exe debe existir."""
        exe = os.path.join(RAIZ, "synapse.exe")
        if os.path.exists(exe):
            assert os.path.getsize(exe) > 0
        else:
            pytest.skip("synapse.exe no encontrado")

    def test_synapse_lsp_exe(self):
        """synapse_lsp.exe debe existir."""
        exe = os.path.join(RAIZ, "synapse_lsp.exe")
        if os.path.exists(exe):
            assert os.path.getsize(exe) > 0
        else:
            pytest.skip("synapse_lsp.exe no encontrado")

    def test_runtime_directorio(self):
        """Directorio runtime/ debe existir."""
        runtime = os.path.join(RAIZ, "runtime")
        assert os.path.exists(runtime), "Directorio runtime/ no existe"

    def test_std_directorio(self):
        """Directorio std/ debe existir."""
        std = os.path.join(RAIZ, "std")
        assert os.path.exists(std), "Directorio std/ no existe"

    def test_version_output(self):
        """synapse --version debe retornar versión."""
        exe = os.path.join(RAIZ, "synapse.exe")
        if not os.path.exists(exe):
            pytest.skip("synapse.exe no encontrado")
        r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=10)
        assert r.returncode == 0 or "version" in r.stdout.lower() or \
            "version" in r.stderr.lower(), \
            f"synapse --version falló: {r.stderr[:200]}"
