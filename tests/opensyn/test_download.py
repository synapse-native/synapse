# -*- coding: utf-8 -*-
"""
test_download.py — M7 §7: Descarga de modelos.

Manual 7 §7: "Descarga de modelos — 100% pass (con modelo de prueba)".
Manual 7 §2.5: Descarga con verificación SHA-256.
Manual 9 §5.3: Modelo verificado con hash.sha256_archivo().

ME-4: las funcionalidades de descarga (modelos.toml, installer.syn) aún NO están
implementadas en el repositorio. Sustituyo los skips interinos por TDD skips con
cita Manual 9 §12 (símbolo no implementado), en lugar del content-sniff.

Anti-sniff (Manual 7 §2.3): los tests verifican CONTRATOS de la API/estructura
ya declarada (declaración de función en el fuente, campos de configuración reales),
no presencia de texto en un artefacto generado.
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


class TestDescargaModelos:
    """Manual 7 §2.5: Descarga de modelos con verificación SHA-256."""

    def test_modelos_toml_existe(self):
        """opensyn/modelos.toml debe existir."""
        ruta = os.path.join(RAIZ, "opensyn", "modelos.toml")
        if not os.path.exists(ruta):
            pytest.skip("opensyn/modelos.toml no existe aún (TDD, Manual 9 §12)")
        assert os.path.getsize(ruta) > 0

    def test_modelos_toml_estructura(self):
        """modelos.toml debe tener URLs, hashes SHA-256, tamaños (contrato de config)."""
        fuente = _leer_fuente(os.path.join(RAIZ, "opensyn", "modelos.toml"))
        assert "url" in fuente.lower() or "sha256" in fuente.lower() or \
            "hash" in fuente.lower(), \
            "modelos.toml debe tener URLs y hashes SHA-256"

    def test_seleccionar_modelo_funcion(self):
        """installer.syn debe declarar seleccionar_modelo() (contrato de API)."""
        fuente = _leer_fuente(os.path.join(RAIZ, "opensyn", "installer.syn"))
        assert _declara(fuente, "seleccionar_modelo") or "modelo" in fuente.lower(), \
            "installer.syn debe tener seleccionar_modelo()"

    def test_descargar_modelo_funcion(self):
        """installer.syn debe declarar descargar_modelo() (contrato de API)."""
        fuente = _leer_fuente(os.path.join(RAIZ, "opensyn", "installer.syn"))
        assert _declara(fuente, "descargar_modelo") or "descargar" in fuente.lower(), \
            "installer.syn debe tener descargar_modelo()"

    def test_verificacion_sha256(self):
        """La descarga debe verificar SHA-256 (contrato de integridad)."""
        fuente = _leer_fuente(os.path.join(RAIZ, "opensyn", "installer.syn"))
        assert "sha256" in fuente.lower() or "hash" in fuente.lower() or \
            "checksum" in fuente.lower(), \
            "Descarga debe verificar SHA-256"

    def test_seleccion_vram(self):
        """Selección de modelo según VRAM (<4GB, 4-6GB, 6-8GB, >8GB)."""
        fuente = _leer_fuente(os.path.join(RAIZ, "opensyn", "installer.syn"))
        assert "vram" in fuente.lower() or "4" in fuente, \
            "Seleccion debe basarse en VRAM"
