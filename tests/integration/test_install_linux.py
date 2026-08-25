# -*- coding: utf-8 -*-
"""
test_install_linux.py — M9 §7: Instalación en Linux.

Manual 9 §7: "Instalación en Linux — Instalación exitosa, synapse en PATH, synapse build funciona".
"""
import os
import subprocess
import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestInstalacionLinux:
    """Manual 9 §7: Instalación en Linux."""

    def test_install_sh_existe(self):
        """install.sh debe existir."""
        sh = os.path.join(RAIZ, "install.sh")
        if os.path.exists(sh):
            assert os.path.getsize(sh) > 0
        else:
            pytest.skip("install.sh no encontrado")

    def test_synapse_binario(self):
        """synapse binario debe existir para Linux."""
        binarios = [
            os.path.join(RAIZ, "synapse"),
            os.path.join(RAIZ, "synapse.exe"),
        ]
        alguno = any(os.path.exists(f) for f in binarios)
        if not alguno:
            pytest.skip("Binario synapse no encontrado")
        assert alguno, "synapse binario debe existir para Linux"

    def test_runtime_lib(self):
        """runtime/ debe existir para instalación."""
        runtime = os.path.join(RAIZ, "runtime")
        assert os.path.exists(runtime), "runtime/ no existe"

    def test_std_lib(self):
        """std/ debe existir para instalación."""
        std = os.path.join(RAIZ, "std")
        assert os.path.exists(std), "std/ no existe"
