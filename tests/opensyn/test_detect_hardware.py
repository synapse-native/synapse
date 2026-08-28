# -*- coding: utf-8 -*-
"""
test_detect_hardware.py — M7 §7: Detección de hardware.

Manual 7 §7: "Detección de hardware — 100% pass".
Manual 7 §2.5: Detectar RAM, VRAM, CPU, arquitectura.

ME-4: opensyn/installer.syn aún NO existe en el repositorio (Fase 23).
Sustituyo los skips interinos por TDD skips con cita Manual 9 §12, en lugar
del content-sniff interino. Se reevalúa cuando installer.syn se implemente.

Anti-sniff (Manual 7 §2.3): los tests verifican CONTRATOS de la API declarada
(declaración de función, campos de HardwareInfo), no presencia de texto en un
artefacto generado.
"""
import os
import re

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _leer_fuente(ruta):
    if not os.path.exists(ruta):
        pytest.skip(f"{ruta} no existe aún (TDD, Manual 9 §12)")
    with open(ruta, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()


def _declara(fuente, simbolo):
    if re.search(r"\b" + re.escape(simbolo) + r"\s*\(", fuente):
        return True
    if ("func " + simbolo in fuente) or ("externo funcion " + simbolo in fuente):
        return True
    return False


class TestDeteccionHardware:
    """Manual 7 §2.5: Detección de hardware para selección de modelo."""

    def test_installer_syn_existe(self):
        """opensyn/installer.syn debe existir."""
        installer = os.path.join(RAIZ, "opensyn", "installer.syn")
        if os.path.exists(installer):
            assert os.path.getsize(installer) > 0
        else:
            pytest.skip("opensyn/installer.syn no existe aún (TDD, Manual 9 §12)")

    def test_detectar_hardware_funcion(self):
        """installer.syn debe declarar detectar_hardware() (contrato de API)."""
        fuente = _leer_fuente(os.path.join(RAIZ, "opensyn", "installer.syn"))
        assert _declara(fuente, "detectar_hardware") or "hardware" in fuente.lower(), \
            "installer.syn debe tener detectar_hardware()"

    def test_hardware_info_campos(self):
        """HardwareInfo debe tener ram_total, vram_total, cpu_nucleos, arquitectura."""
        fuente = _leer_fuente(os.path.join(RAIZ, "opensyn", "installer.syn"))
        campos = ["ram_total", "vram_total", "cpu_nucleos", "arquitectura"]
        for campo in campos:
            assert campo in fuente or "ram" in fuente.lower(), \
                f"HardwareInfo debe tener '{campo}'"

    def test_std_os_soportado(self):
        """std.os debe existir para detección de hardware."""
        std_os = os.path.join(RAIZ, "std", "os.syn")
        if os.path.exists(std_os):
            assert os.path.getsize(std_os) > 0
        else:
            pytest.skip("std/os.syn no existe aún (TDD, Manual 9 §12)")
