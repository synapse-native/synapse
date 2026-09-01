# -*- coding: utf-8 -*-
"""
tests/installers/test_windows.py — Verifica instalador Windows (Inno Setup).
Manual 9 §4.1: Distribución para Windows.
F30 (Instalación Unificada). TDD (ME_30_T2): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
"""
import os
import re
import pytest

pytestmark = pytest.mark.tdd

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _leer_archivo(ruta):
    """Lee archivo de texto."""
    if not os.path.exists(ruta):
        return None
    with open(ruta, 'r', encoding='utf-8', errors='ignore') as fh:
        return fh.read()


class TestInstaladorWindows:
    """Manual 9 §4.1: Instalador Windows (Inno Setup)."""

    def test_synapse_iss_existe(self):
        """instaladores/windows/synapse.iss debe existir."""
        ruta = os.path.join(RAIZ, 'instaladores', 'windows', 'synapse.iss')
        if not os.path.exists(ruta):
            pytest.fail(
                "RED TDD ME_30_T2: synapse.iss no existe "
                "(Manual 9 §4.1). Crear script Inno Setup."
            )
        assert os.path.getsize(ruta) > 0

    def test_sintaxis_inno_setup(self):
        """synapse.iss debe tener sintaxis Inno Setup válida."""
        ruta = os.path.join(RAIZ, 'instaladores', 'windows', 'synapse.iss')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer synapse.iss"

        # Verificar secciones básicas de Inno Setup
        assert '[Setup]' in contenido, "synapse.iss debe tener sección [Setup]"
        assert '[Files]' in contenido, "synapse.iss debe tener sección [Files]"
        assert '[Icons]' in contenido, "synapse.iss debe tener sección [Icons]"

    def test_opciones_componentes(self):
        """synapse.iss debe ofrecer opciones de componentes."""
        ruta = os.path.join(RAIZ, 'instaladores', 'windows', 'synapse.iss')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer synapse.iss"

        # Verificar que menciona componentes
        assert 'syquex' in contenido.lower() or 'ecosistema' in contenido.lower(), \
            "synapse.iss debe incluir opción de Syquex/Ecosistema completo"
        assert 'opensyn' in contenido.lower(), \
            "synapse.iss debe incluir opción de OpenSyn"

    def test_accesos_directos(self):
        """synapse.iss debe crear accesos directos."""
        ruta = os.path.join(RAIZ, 'instaladores', 'windows', 'synapse.iss')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer synapse.iss"

        # Verificar Icons section
        assert 'desktopicon' in contenido.lower() or 'desktop' in contenido.lower(), \
            "synapse.iss debe crear acceso directo de escritorio"
        assert '{group}' in contenido or 'group' in contenido.lower(), \
            "synapse.iss debe crear grupo en Menú Inicio"

    def test_desinstalador(self):
        """synapse.iss debe incluir desinstalador."""
        ruta = os.path.join(RAIZ, 'instaladores', 'windows', 'synapse.iss')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer synapse.iss"

        # Verificar desinstalador
        assert 'uninstall' in contenido.lower() or 'desinstalar' in contenido.lower(), \
            "synapse.iss debe incluir desinstalador"

    def test_app_metadata(self):
        """synapse.iss debe tener metadata de la aplicación."""
        ruta = os.path.join(RAIZ, 'instaladores', 'windows', 'synapse.iss')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer synapse.iss"

        assert 'AppName' in contenido, "synapse.iss debe tener AppName"
        assert 'AppVersion' in contenido, "synapse.iss debe tener AppVersion"
        assert 'AppPublisher' in contenido, "synapse.iss debe tener AppPublisher"
