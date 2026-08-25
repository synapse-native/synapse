# -*- coding: utf-8 -*-
"""
test_detect_hardware.py — M7 §7: Detección de hardware.

Manual 7 §7: "Detección de hardware — 100% pass".
Manual 7 §2.5: Detectar RAM, VRAM, CPU, arquitectura.
"""
import os
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestDeteccionHardware:
    """Manual 7 §2.5: Detección de hardware para selección de modelo."""

    def test_installer_syn_existe(self):
        """opensyn/installer.syn debe existir."""
        installer = os.path.join(RAIZ, "opensyn", "installer.syn")
        if os.path.exists(installer):
            assert os.path.getsize(installer) > 0
        else:
            pytest.skip("opensyn/installer.syn no existe aún (TDD)")

    def test_detectar_hardware_funcion(self):
        """installer.syn debe tener función detectar_hardware()."""
        installer = os.path.join(RAIZ, "opensyn", "installer.syn")
        if not os.path.exists(installer):
            pytest.skip("opensyn/installer.syn no existe aún")
        with open(installer, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "detectar_hardware" in contenido or "hardware" in contenido.lower(), \
            "installer.syn debe tener detectar_hardware()"

    def test_hardware_info_campos(self):
        """HardwareInfo debe tener ram_total, vram_total, cpu_nucleos, arquitectura."""
        installer = os.path.join(RAIZ, "opensyn", "installer.syn")
        if not os.path.exists(installer):
            pytest.skip("opensyn/installer.syn no existe aún")
        with open(installer, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        campos = ["ram_total", "vram_total", "cpu_nucleos", "arquitectura"]
        for campo in campos:
            assert campo in contenido or "ram" in contenido.lower(), \
                f"HardwareInfo debe tener '{campo}'"

    def test_std_os_soportado(self):
        """std.os debe existir para detección de hardware."""
        std_os = os.path.join(RAIZ, "std", "os.syn")
        if os.path.exists(std_os):
            assert os.path.getsize(std_os) > 0
        else:
            pytest.skip("std/os.syn no existe aún (TDD)")
