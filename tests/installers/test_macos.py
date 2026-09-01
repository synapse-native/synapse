# -*- coding: utf-8 -*-
"""
tests/installers/test_macos.py — Verifica instalador macOS (.dmg/.pkg).
Manual 9 §4.1: Distribución para macOS.
F30 (Instalación Unificada). TDD (ME_30_T4): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
"""
import os
import pytest

pytestmark = pytest.mark.tdd

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _leer_archivo(ruta):
    """Lee archivo de texto."""
    if not os.path.exists(ruta):
        return None
    with open(ruta, 'r', encoding='utf-8', errors='ignore') as fh:
        return fh.read()


class TestInstaladorMacOS:
    """Manual 9 §4.1: Instalador macOS (.dmg/.pkg)."""

    def test_create_dmg_sh_existe(self):
        """instaladores/macos/create_dmg.sh debe existir."""
        ruta = os.path.join(RAIZ, 'instaladores', 'macos', 'create_dmg.sh')
        if not os.path.exists(ruta):
            pytest.fail(
                "RED TDD ME_30_T4: create_dmg.sh no existe "
                "(Manual 9 §4.1). Crear script para macOS."
            )
        assert os.path.getsize(ruta) > 0

    def test_create_dmg_sh_shebang(self):
        """create_dmg.sh debe tener shebang bash."""
        ruta = os.path.join(RAIZ, 'instaladores', 'macos', 'create_dmg.sh')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer create_dmg.sh"
        assert contenido.startswith('#!/bin/bash') or contenido.startswith('#!/usr/bin/env bash'), \
            "create_dmg.sh debe tener shebang #!/bin/bash"

    def test_crea_estructura_app(self):
        """create_dmg.sh debe crear estructura .app."""
        ruta = os.path.join(RAIZ, 'instaladores', 'macos', 'create_dmg.sh')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer create_dmg.sh"
        assert '.app' in contenido or 'Contents' in contenido or 'Info.plist' in contenido, \
            "create_dmg.sh debe crear estructura .app"

    def test_genera_dmg(self):
        """create_dmg.sh debe generar archivo .dmg."""
        ruta = os.path.join(RAIZ, 'instaladores', 'macos', 'create_dmg.sh')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer create_dmg.sh"
        assert 'dmg' in contenido.lower() or 'hdiutil' in contenido.lower(), \
            "create_dmg.sh debe generar .dmg con hdiutil"

    def test_info_plist(self):
        """create_dmg.sh debe crear Info.plist válido."""
        ruta = os.path.join(RAIZ, 'instaladores', 'macos', 'create_dmg.sh')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer create_dmg.sh"
        assert 'Info.plist' in contenido, \
            "create_dmg.sh debe crear Info.plist"
        assert 'CFBundleExecutable' in contenido or 'CFBundleName' in contenido, \
            "Info.plist debe tener CFBundleExecutable o CFBundleName"

    def test_opciones_componentes(self):
        """create_dmg.sh debe ofrecer opciones de componentes."""
        ruta = os.path.join(RAIZ, 'instaladores', 'macos', 'create_dmg.sh')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer create_dmg.sh"
        assert 'syquex' in contenido.lower() or 'ecosistema' in contenido.lower(), \
            "create_dmg.sh debe incluir opción de Syquex/Ecosistema completo"
        assert 'opensyn' in contenido.lower(), \
            "create_dmg.sh debe incluir opción de OpenSyn"
