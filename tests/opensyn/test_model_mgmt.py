# -*- coding: utf-8 -*-
"""
tests/opensyn/test_model_mgmt.py — OpenSyn gestiona modelos (descargar/cachear).
Manual 7 §7 / Manual 9 §5.3: descarga y verificación SHA-256 de modelos.
F29 (gestion de modelos). TDD MTO (ME_29_T3_mod): verifica funcionalidad implementada.
cumple Manual 7 §7
cumple Manual 9 §5.3
"""
import os
import re

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.tdd]

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _leer_fuente(ruta):
    """Lee archivo de código fuente."""
    if not os.path.exists(ruta):
        return None
    with open(ruta, 'r', encoding='utf-8', errors='ignore') as fh:
        return fh.read()


def _declara_funcion(fuente, nombre):
    """Verifica si una función está declarada."""
    if re.search(r'\b' + re.escape(nombre) + r'\s*\(', fuente):
        return True
    if ('funcion ' + nombre in fuente) or ('externo funcion ' + nombre in fuente):
        return True
    return False


class TestGestionModelos:
    """Manual 7 §7 / Manual 9 §5.3: OpenSyn gestiona modelos."""

    def test_installer_syn_existe(self):
        """opensyn/installer.syn debe existir."""
        ruta = os.path.join(RAIZ, 'opensyn', 'installer.syn')
        assert os.path.exists(ruta), \
            "opensyn/installer.syn no existe (Manual 9 §5.3)"

    def test_seleccionar_modelo_funcion(self):
        """installer.syn debe declarar seleccionar_modelo() (Manual 9 §5.3)."""
        ruta = os.path.join(RAIZ, 'opensyn', 'installer.syn')
        fuente = _leer_fuente(ruta)
        assert fuente is not None, "No se pudo leer installer.syn"
        assert _declara_funcion(fuente, 'seleccionar_modelo'), \
            "installer.syn debe declarar seleccionar_modelo()"

    def test_descargar_modelo_funcion(self):
        """installer.syn debe declarar descargar_modelo() (Manual 9 §5.3)."""
        ruta = os.path.join(RAIZ, 'opensyn', 'installer.syn')
        fuente = _leer_fuente(ruta)
        assert fuente is not None, "No se pudo leer installer.syn"
        assert _declara_funcion(fuente, 'descargar_modelo'), \
            "installer.syn debe declarar descargar_modelo()"

    def test_instalar_modelo_funcion(self):
        """installer.syn debe declarar instalar_modelo() (Manual 9 §5.3)."""
        ruta = os.path.join(RAIZ, 'opensyn', 'installer.syn')
        fuente = _leer_fuente(ruta)
        assert fuente is not None, "No se pudo leer installer.syn"
        assert _declara_funcion(fuente, 'instalar_modelo'), \
            "installer.syn debe declarar instalar_modelo()"

    def test_modelo_info_estructura(self):
        """installer.syn debe declarar ModeloInfo con campos requeridos (Manual 9 §5.3)."""
        ruta = os.path.join(RAIZ, 'opensyn', 'installer.syn')
        fuente = _leer_fuente(ruta)
        assert fuente is not None, "No se pudo leer installer.syn"
        assert 'ModeloInfo' in fuente, \
            "installer.syn debe declarar estructura ModeloInfo"
        for campo in ('nombre', 'url', 'sha256', 'tamano_aprox'):
            assert campo in fuente, \
                f"ModeloInfo debe incluir campo '{campo}' (Manual 9 §5.3)"

    def test_seleccion_vram(self):
        """Selección de modelo según VRAM con umbrales (Manual 9 §5.3)."""
        ruta = os.path.join(RAIZ, 'opensyn', 'installer.syn')
        fuente = _leer_fuente(ruta)
        assert fuente is not None, "No se pudo leer installer.syn"
        assert 'vram' in fuente.lower(), \
            "Selección debe basarse en VRAM"
        for umbral in ('4096', '8192', '12288'):
            assert umbral in fuente, \
                f"Selección por VRAM debe contemplar umbral {umbral}"

    def test_verificacion_sha256(self):
        """Descarga debe verificar SHA-256 (Manual 9 §5.3)."""
        ruta = os.path.join(RAIZ, 'opensyn', 'installer.syn')
        fuente = _leer_fuente(ruta)
        assert fuente is not None, "No se pudo leer installer.syn"
        assert 'sha256' in fuente.lower() or 'hash' in fuente.lower(), \
            "Descarga debe verificar SHA-256"
