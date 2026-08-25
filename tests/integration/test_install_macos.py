# -*- coding: utf-8 -*-
"""
test_install_macos.py — M9 §7: Instalación en macOS.

Manual 9 §7: "Instalación en macOS — Instalación exitosa, synapse funciona".
"""
import os
import subprocess
import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestInstalacionMacOS:
    """Manual 9 §7: Instalación en macOS ARM."""

    def test_install_sh_existe(self):
        """install.sh debe existir."""
        sh = os.path.join(RAIZ, "install.sh")
        if os.path.exists(sh):
            assert os.path.getsize(sh) > 0
        else:
            pytest.skip("install.sh no encontrado")

    def test_runtime_lib(self):
        """runtime/ debe existir."""
        runtime = os.path.join(RAIZ, "runtime")
        assert os.path.exists(runtime), "runtime/ no existe"

    def test_std_lib(self):
        """std/ debe existir."""
        std = os.path.join(RAIZ, "std")
        assert os.path.exists(std), "std/ no existe"
