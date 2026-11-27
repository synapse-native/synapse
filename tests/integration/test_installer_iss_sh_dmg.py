# -*- coding: utf-8 -*-
"""
tests/integration/test_installer_iss_sh_dmg.py — Instaladores unificados .iss/.sh/.dmg.
Manual 9 §9 / F30 / ME-30_T1. TDD (ME_30_T1): este oraculo verifica que los tres
instaladores unificados existen y estan alineados al Manual 9 §2.5.
cumple Manual 9 §2.5: Configuracion de Inno Setup (Windows)
cumple Manual 9 §4.1: GitHub Releases
"""
import os

import pytest

pytestmark = pytest.mark.tdd

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_instaladores_iss_sh_dmg():
    """Instaladores unificados .iss/.sh/.dmg existen en instaladores/<plataforma>/."""
    # Windows: .iss en instaladores/windows/
    iss_path = os.path.join(RAIZ, "instaladores", "windows", "synapse.iss")
    assert os.path.exists(iss_path), f"instaladores/windows/synapse.iss no existe"

    # Linux: .sh en instaladores/linux/
    sh_path = os.path.join(RAIZ, "instaladores", "linux", "install.sh")
    assert os.path.exists(sh_path), f"instaladores/linux/install.sh no existe"

    # macOS: .sh (create_dmg.sh) en instaladores/macos/
    dmg_script = os.path.join(RAIZ, "instaladores", "macos", "create_dmg.sh")
    assert os.path.exists(dmg_script), f"instaladores/macos/create_dmg.sh no existe"


def test_iss_secciones_requeridas():
    """Manual 9 §2.5: el .iss debe tener Setup, Files, Components, Types, Run, Registry."""
    iss_path = os.path.join(RAIZ, "instaladores", "windows", "synapse.iss")
    with open(iss_path, encoding="utf-8", errors="ignore") as f:
        content = f.read()

    for seccion in ("[Setup]", "[Files]", "[Components]", "[Types]", "[Run]", "[Registry]"):
        assert seccion in content, f"Sección {seccion} faltante en synapse.iss"


def test_iss_componentes_manual():
    """Manual 9 §2.5: componentes synapse/syquex/opensyn/vscode con tipos full/minimal."""
    iss_path = os.path.join(RAIZ, "instaladores", "windows", "synapse.iss")
    with open(iss_path, encoding="utf-8", errors="ignore") as f:
        content = f.read()

    for comp in ("synapse", "syquex", "opensyn", "vscode"):
        assert f'"{comp}"' in content, f"Componente {comp} faltante"
    for tipo in ("full", "minimal"):
        assert f'"{tipo}"' in content, f"Tipo {tipo} faltante"
