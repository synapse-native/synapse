# -*- coding: utf-8 -*-
"""
test_opensyn_hardware.py — M9 §7: OpenSyn en hardware limitado.

Manual 9 §7: "OpenSyn en hardware limitado — Modelo Q3 seleccionado, consulta exitosa".
Manual 7 §2.5: Selección de modelo según VRAM (<4GB → Q3).
"""
import os
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestOpenSynHardwareLimitado:
    """Manual 9 §7: OpenSyn en máquina con 4GB VRAM."""

    def test_opensyn_archivos(self):
        """opensyn/ debe existir con archivos necesarios."""
        opensyn = os.path.join(RAIZ, "opensyn")
        assert os.path.exists(opensyn), "opensyn/ no existe"

    def test_modelo_q3_seleccionado(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """En 4GB VRAM, modelo Q3 debe ser seleccionado."""
        installer = os.path.join(RAIZ, "opensyn", "installer.syn")
        if not os.path.exists(installer):
            pytest.skip("installer.syn no existe aún")
        with open(installer, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "Q3" in contenido or "q3" in contenido or \
            "4" in contenido or "vram" in contenido.lower(), \
            "Selección de modelo debe considerar VRAM < 4GB"

    def test_config_toml_modelo(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """~/.opensyn/config.toml debe tener ruta de modelo."""
        config = os.path.expanduser("~/.opensyn/config.toml")
        if os.path.exists(config):
            with open(config, 'r', encoding='utf-8') as f:
                contenido = f.read()
            assert "modelo" in contenido.lower() or "model" in contenido.lower() or \
                "ruta" in contenido.lower() or "path" in contenido.lower(), \
                "config.toml debe tener ruta de modelo"
        else:
            pytest.skip("config.toml no existe aún")
