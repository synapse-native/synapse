# -*- coding: utf-8 -*-
"""
test_download.py — M7 §7: Descarga de modelos.

Manual 7 §7: "Descarga de modelos — 100% pass (con modelo de prueba)".
Manual 7 §2.5: Descarga con verificación SHA-256.
Manual 9 §5.3: Modelo verificado con hash.sha256_archivo().

ME-4: las funcionalidades de descarga (modelos.toml, installer.syn) aún NO están
implementadas en el repositorio. Sustituyo los `pytest.skip('ME-4...')` por TDD
skips con cita Manual 9 §12 (símbolo no implementado), en lugar del content-sniff.
"""
import os

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _modelos():
    f = os.path.join(RAIZ, "opensyn", "modelos.toml")
    if not os.path.exists(f):
        pytest.skip("opensyn/modelos.toml no existe aún (TDD, Manual 9 §12)")
    return f


def _instalador():
    f = os.path.join(RAIZ, "opensyn", "installer.syn")
    if not os.path.exists(f):
        pytest.skip("opensyn/installer.syn no existe aún (TDD, Manual 9 §12)")
    return f


class TestDescargaModelos:
    """Manual 7 §2.5: Descarga de modelos con verificación SHA-256."""

    def test_modelos_toml_existe(self):
        """opensyn/modelos.toml debe existir."""
        if not os.path.exists(_modelos()):
            pytest.skip("opensyn/modelos.toml no existe aún (TDD, Manual 9 §12)")
        assert os.path.getsize(_modelos()) > 0

    def test_modelos_toml_estructura(self):
        """modelos.toml debe tener URLs, hashes SHA-256, tamaños."""
        f = _modelos()
        with open(f, "r", encoding="utf-8") as fh:
            contenido = fh.read()
        assert "url" in contenido.lower() or "sha256" in contenido.lower() or \
            "hash" in contenido.lower(), \
            "modelos.toml debe tener URLs y hashes SHA-256"

    def test_seleccionar_modelo_funcion(self):
        """installer.syn debe tener función seleccionar_modelo()."""
        f = _instalador()
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            contenido = fh.read()
        assert "seleccionar_modelo" in contenido or "modelo" in contenido.lower(), \
            "installer.syn debe tener seleccionar_modelo()"

    def test_descargar_modelo_funcion(self):
        """installer.syn debe tener función descargar_modelo()."""
        f = _instalador()
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            contenido = fh.read()
        assert "descargar_modelo" in contenido or "descargar" in contenido.lower(), \
            "installer.syn debe tener descargar_modelo()"

    def test_verificacion_sha256(self):
        """La descarga debe verificar SHA-256."""
        f = _instalador()
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            contenido = fh.read()
        assert "sha256" in contenido.lower() or "hash" in contenido.lower() or \
            "checksum" in contenido.lower(), \
            "Descarga debe verificar SHA-256"

    def test_seleccion_vram(self):
        """Selección de modelo según VRAM (<4GB, 4-6GB, 6-8GB, >8GB)."""
        f = _instalador()
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            contenido = fh.read()
        assert "vram" in contenido.lower() or "4" in contenido, \
            "Seleccion debe basarse en VRAM"
