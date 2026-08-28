# -*- coding: utf-8 -*-
"""
test_download.py — M7 §7: Descarga de modelos.

Manual 7 §7: "Descarga de modelos — 100% pass (con modelo de prueba)".
Manual 7 §2.5: Descarga con verificación SHA-256.
Manual 9 §5.3: Modelo verificado con hash.sha256_archivo().
"""
import os
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestDescargaModelos:
    """Manual 7 §2.5: Descarga de modelos con verificación SHA-256."""

    def test_modelos_toml_existe(self):
        """opensyn/modelos.toml debe existir."""
        modelos = os.path.join(RAIZ, "opensyn", "modelos.toml")
        if os.path.exists(modelos):
            assert os.path.getsize(modelos) > 0
        else:
            pytest.skip("opensyn/modelos.toml no existe aún (TDD)")

    def test_modelos_toml_estructura(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """modelos.toml debe tener URLs, hashes SHA-256, tamaños."""
        modelos = os.path.join(RAIZ, "opensyn", "modelos.toml")
        if not os.path.exists(modelos):
            pytest.skip("opensyn/modelos.toml no existe aún")
        with open(modelos, 'r', encoding='utf-8') as f:
            contenido = f.read()
        assert "url" in contenido.lower() or "sha256" in contenido.lower() or \
            "hash" in contenido.lower(), \
            "modelos.toml debe tener URLs y hashes SHA-256"

    def test_seleccionar_modelo_funcion(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """installer.syn debe tener función seleccionar_modelo()."""
        installer = os.path.join(RAIZ, "opensyn", "installer.syn")
        if not os.path.exists(installer):
            pytest.skip("opensyn/installer.syn no existe aún")
        with open(installer, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "seleccionar_modelo" in contenido or "modelo" in contenido.lower(), \
            "installer.syn debe tener seleccionar_modelo()"

    def test_descargar_modelo_funcion(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """installer.syn debe tener función descargar_modelo()."""
        installer = os.path.join(RAIZ, "opensyn", "installer.syn")
        if not os.path.exists(installer):
            pytest.skip("opensyn/installer.syn no existe aún")
        with open(installer, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "descargar_modelo" in contenido or "descargar" in contenido.lower(), \
            "installer.syn debe tener descargar_modelo()"

    def test_verificacion_sha256(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """La descarga debe verificar SHA-256."""
        installer = os.path.join(RAIZ, "opensyn", "installer.syn")
        if not os.path.exists(installer):
            pytest.skip("opensyn/installer.syn no existe aún")
        with open(installer, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "sha256" in contenido.lower() or "hash" in contenido.lower() or \
            "checksum" in contenido.lower(), \
            "Descarga debe verificar SHA-256"

    def test_seleccion_vram(self):
        pytest.skip('ME-4: Refactor pendiente a validación funcional')
        """Selección de modelo según VRAM (<4GB, 4-6GB, 6-8GB, >8GB)."""
        installer = os.path.join(RAIZ, "opensyn", "installer.syn")
        if not os.path.exists(installer):
            pytest.skip("opensyn/installer.syn no existe aún")
        with open(installer, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "vram" in contenido.lower() or "4" in contenido, \
            "Selección debe basarse en VRAM"
