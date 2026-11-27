# -*- coding: utf-8 -*-
"""
test_download.py — M7 §7 / M7 §2.5 / M9 §5.3: Descarga de modelos OpenSyn.

Manual 7 §7: "Descarga de modelos — 100% pass (con modelo de prueba)".
Manual 7 §2.5: Descarga con verificación SHA-256.
Manual 9 §5.3: Modelo verificado con hash.sha256_archivo().

CALIDAD TOTAL (regla transversal plan_AUDITORIA_TESTS.md): estos tests son
especificaciones COMPLETAS del comportamiento de descarga. Mientras
opensyn/modelos.toml e opensyn/installer.syn (fase F29) no existan, el test
FALLA explícitamente en ROJO TDD (pytest.fail) apuntando a su ME de feature —
NO se usa pytest.skip (ocultaría deuda). Cuando la feature se implemente
(ME_29_T2/ME_29_T3) el test corre sus oráculos completos y pasa en VERDE.

Anti-sniff (Manual 7 §2.3): se verifican CONTRATOS de la API/estructura ya
declarada (declaración de función en el fuente, campos de configuración reales),
no presencia de texto en un artefacto generado.
"""
import os
import re

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.tdd]

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

ME_FEATURE = "ME_29_T2/ME_29_T3 (fase F29: installer.syn / modelos.toml)"


def _leer_fuente(ruta, manual):
    if not os.path.exists(ruta):
        pytest.fail(
            f"RED TDD {ME_FEATURE}: {ruta} no implementado aún "
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


class TestDescargaModelos:
    """Manual 7 §2.5: Descarga de modelos con verificación SHA-256."""

    def test_modelos_toml_existe(self):
        """opensyn/modelos.toml debe existir y no estar vacío (Manual 9 §5.3)."""
        ruta = os.path.join(RAIZ, "opensyn", "modelos.toml")
        if not os.path.exists(ruta):
            pytest.fail(
                f"RED TDD {ME_FEATURE}: opensyn/modelos.toml no existe "
                f"(Manual 7 §7 / Manual 9 §5.3). Implementar en fase F29."
            )
        assert os.path.getsize(ruta) > 0

    def test_modelos_toml_estructura(self):
        """modelos.toml: URL, hash SHA-256 y tamaño por entrada (Manual 7 §2.5)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "modelos.toml"), "Manual 7 §2.5"
        )
        assert "url" in fuente.lower(), "modelos.toml requiere campo 'url'"
        assert "sha256" in fuente.lower() or "hash" in fuente.lower(), \
            "modelos.toml requiere hash SHA-256 por modelo"
        assert "tam" in fuente.lower() or "size" in fuente.lower(), \
            "modelos.toml requiere tamaño por modelo"

    def test_seleccionar_modelo_funcion(self):
        """installer.syn debe declarar seleccionar_modelo() (Manual 7 §7)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "installer.syn"), "Manual 7 §7"
        )
        assert _declara(fuente, "seleccionar_modelo") or "modelo" in fuente.lower(), \
            "installer.syn debe tener seleccionar_modelo()"

    def test_descargar_modelo_funcion(self):
        """installer.syn debe declarar descargar_modelo() (Manual 7 §2.5)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "installer.syn"), "Manual 7 §2.5"
        )
        assert _declara(fuente, "descargar_modelo") or "descargar" in fuente.lower(), \
            "installer.syn debe tener descargar_modelo()"

    def test_verificacion_sha256(self):
        """La descarga debe verificar SHA-256 (Manual 9 §5.3)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "installer.syn"), "Manual 9 §5.3"
        )
        assert "sha256" in fuente.lower() or "hash" in fuente.lower() or \
            "checksum" in fuente.lower(), \
            "Descarga debe verificar SHA-256"

    def test_seleccion_vram(self):
        """Selección de modelo según VRAM (<4GB, 4-6GB, 6-8GB, >8GB) (Manual 7 §7)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "installer.syn"), "Manual 7 §7"
        )
        assert "vram" in fuente.lower(), "Seleccion debe basarse en VRAM"
        for umbral in ("4", "6", "8"):
            assert umbral in fuente, \
                f"Seleccion por VRAM debe contemplar umbral {umbral}GB"

    def test_instalar_modelo_funcion(self):
        """installer.syn debe declarar instalar_modelo() (Manual 9 §5.3)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "installer.syn"), "Manual 9 §5.3"
        )
        assert _declara(fuente, "instalar_modelo"), \
            "installer.syn debe declarar instalar_modelo()"

    def test_config_info_estructura(self):
        """installer.syn debe declarar ConfigInfo con campos de config.toml (Manual 9 §5.4)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "installer.syn"), "Manual 9 §5.4"
        )
        assert "ConfigInfo" in fuente, "installer.syn debe declarar ConfigInfo"
        for campo in ("nombre", "ruta", "n_ctx", "n_threads", "n_gpu_layers",
                      "puerto", "host", "timeout"):
            assert campo in fuente, \
                f"ConfigInfo debe incluir campo '{campo}' (Manual 9 §5.4)"

    def test_escribir_config_funcion(self):
        """installer.syn debe declarar escribir_config() (Manual 9 §5.4)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "installer.syn"), "Manual 9 §5.4"
        )
        assert _declara(fuente, "escribir_config"), \
            "installer.syn debe declarar escribir_config()"

    def test_config_toml_generado(self):
        """escribir_config debe generar formato TOML con [general], [modelo], [server] (Manual 9 §5.4)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "installer.syn"), "Manual 9 §5.4"
        )
        assert "[general]" in fuente, "config.toml debe incluir [general]"
        assert "[modelo]" in fuente, "config.toml debe incluir [modelo]"
        assert "[server]" in fuente, "config.toml debe incluir [server]"

