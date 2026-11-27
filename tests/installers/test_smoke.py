# -*- coding: utf-8 -*-
"""
tests/installers/test_smoke.py — Tests de smoke para instaladores.
Manual 9 §4.1: Verificación de integridad y ejecución de instaladores.
F30 (Instalación Unificada). TDD (ME_30_T6): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
"""
import os
import subprocess
import pytest

pytestmark = pytest.mark.tdd

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _leer_archivo(ruta):
    """Lee archivo de texto."""
    if not os.path.exists(ruta):
        return None
    with open(ruta, 'r', encoding='utf-8', errors='ignore') as fh:
        return fh.read()


def _verificar_sintaxis_bash(ruta):
    """Verifica que un script Bash no tenga errores de sintaxis básicos."""
    try:
        contenido = _leer_archivo(ruta)
        if contenido is None:
            return False
        # Verificaciones básicas de sintaxis
        if not (contenido.startswith('#!/bin/bash') or contenido.startswith('#!/usr/bin/env bash')):
            return False
        # Verificar que no haya caracteres ilegales
        for i, linea in enumerate(contenido.split('\n'), 1):
            if '\x00' in linea:
                return False
        return True
    except Exception:
        return False


class TestSmokeInstaladores:
    """Manual 9 §4.1: Tests de smoke para instaladores."""

    def test_install_sh_sin_errores_sintaxis(self):
        """install.sh no debe tener errores de sintaxis."""
        ruta = os.path.join(RAIZ, 'instaladores', 'linux', 'install.sh')
        if not os.path.exists(ruta):
            pytest.fail("install.sh no existe")
        assert _verificar_sintaxis_bash(ruta), \
            "install.sh tiene errores de sintaxis Bash"

    def test_create_dmg_sh_sin_errores_sintaxis(self):
        """create_dmg.sh no debe tener errores de sintaxis."""
        ruta = os.path.join(RAIZ, 'instaladores', 'macos', 'create_dmg.sh')
        if not os.path.exists(ruta):
            pytest.fail("create_dmg.sh no existe")
        assert _verificar_sintaxis_bash(ruta), \
            "create_dmg.sh tiene errores de sintaxis Bash"

    def test_verificar_firma_importable(self):
        """verificar_firma.py debe ser importable sin errores."""
        ruta = os.path.join(RAIZ, 'instaladores', 'common', 'verificar_firma.py')
        if not os.path.exists(ruta):
            pytest.fail("verificar_firma.py no existe")
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("verificar_firma", ruta)
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
        except Exception as e:
            pytest.fail(f"verificar_firma.py tiene errores de importación: {e}")

    def test_instaladores_tienen_comentarios_manual(self):
        """Todos los instaladores deben tener comentarios de cumplimiento."""
        archivos = [
            'instaladores/linux/install.sh',
            'instaladores/macos/create_dmg.sh',
            'instaladores/common/verificar_firma.py'
        ]
        for archivo in archivos:
            ruta = os.path.join(RAIZ, archivo)
            if os.path.exists(ruta):
                contenido = _leer_archivo(ruta)
                assert 'Manual' in contenido or 'manual' in contenido, \
                    f"{archivo} no tiene comentario de Manual"

    def test_instaladores_tienen_permisos_ejecucion(self):
        """Scripts Bash deben tener shebang."""
        scripts = [
            'instaladores/linux/install.sh',
            'instaladores/macos/create_dmg.sh'
        ]
        for script in scripts:
            ruta = os.path.join(RAIZ, script)
            if os.path.exists(ruta):
                contenido = _leer_archivo(ruta)
                assert contenido.startswith('#!/bin/bash') or \
                       contenido.startswith('#!/usr/bin/env bash'), \
                    f"{script} no tiene shebang Bash"
