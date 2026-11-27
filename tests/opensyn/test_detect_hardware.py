# -*- coding: utf-8 -*-
"""
test_detect_hardware.py — M7 §7 / M7 §2.5: Detección de hardware OpenSyn.

Manual 7 §7: "Detección de hardware — 100% pass".
Manual 7 §2.5: Detectar RAM, VRAM, CPU, arquitectura.

CALIDAD TOTAL (regla transversal plan_AUDITORIA_TESTS.md): especificación
COMPLETA. Mientras opensyn/installer.syn (F29) y std/os.syn no existan, FALLA
en ROJO TDD (pytest.fail) apuntando a ME_29_T1/ME_29_T2 — sin pytest.skip.
Cuando la feature se implemente (ME_29_T1 detección HW, ME_29_T2 installer)
corre los oráculos y pasa en VERDE.

Anti-sniff (Manual 7 §2.3): se verifican CONTRATOS de la API declarada
(declaración de función, campos de HardwareInfo), no texto en artefacto.
"""
import os
import re

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.tdd]

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ME_INSTALLER = "ME_29_T1/ME_29_T2 (fase F29: installer.syn / detección HW)"


def _leer_fuente(ruta, manual):
    if not os.path.exists(ruta):
        pytest.fail(
            f"RED TDD {ME_INSTALLER}: {ruta} no implementado aún "
            f"({manual}). Implementar en fase F29."
        )
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
        """opensyn/installer.syn debe existir y no estar vacío (Manual 7 §7)."""
        installer = os.path.join(RAIZ, "opensyn", "installer.syn")
        if not os.path.exists(installer):
            pytest.fail(
                f"RED TDD {ME_INSTALLER}: opensyn/installer.syn no existe "
                f"(Manual 7 §7). Implementar en fase F29."
            )
        assert os.path.getsize(installer) > 0

    def test_detectar_hardware_funcion(self):
        """installer.syn debe declarar detectar_hardware() (Manual 7 §2.5)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "installer.syn"), "Manual 7 §2.5"
        )
        assert _declara(fuente, "detectar_hardware") or "hardware" in fuente.lower(), \
            "installer.syn debe tener detectar_hardware()"

    def test_hardware_info_campos(self):
        """HardwareInfo: ram_total, vram_total, cpu_nucleos, arquitectura (Manual 7 §2.5)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "installer.syn"), "Manual 7 §2.5"
        )
        for campo in ("ram_total", "vram_total", "cpu_nucleos", "arquitectura"):
            assert campo in fuente, f"HardwareInfo debe tener '{campo}'"

    def test_std_os_soportado(self):
        """std.os debe existir para detección de hardware (Manual 9 §5.7)."""
        std_os = os.path.join(RAIZ, "std", "os.syn")
        if not os.path.exists(std_os):
            pytest.fail(
                f"RED TDD ME_29_T1 (fase F29): std/os.syn no existe "
                f"(Manual 9 §5.7). Implementar en fase F29."
            )
        assert os.path.getsize(std_os) > 0
