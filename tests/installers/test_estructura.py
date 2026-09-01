# -*- coding: utf-8 -*-
"""
tests/installers/test_estructura.py — Verifica estructura de instaladores.
Manual 9 §4.1 / Manual 9 §4.2: Distribución multiplataforma.
F30 (Instalación Unificada). TDD (ME_30_T1): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
"""
import os
import pytest

pytestmark = pytest.mark.tdd

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def test_directorio_instaladores_existe():
    """instaladores/ debe existir para distribución multiplataforma."""
    ruta = os.path.join(RAIZ, 'instaladores')
    if not os.path.exists(ruta):
        pytest.fail(
            "RED TDD ME_30_T1: directorio instaladores/ no existe "
            "(Manual 9 §4.1). Crear estructura de instaladores."
        )
    assert os.path.isdir(ruta)


def test_directorio_windows_existe():
    """instalador_synapse.iss debe existir en la raíz para Windows (Inno Setup)."""
    ruta = os.path.join(RAIZ, 'instalador_synapse.iss')
    if not os.path.exists(ruta):
        pytest.fail(
            "RED TDD ME_30_T1: instalador_synapse.iss no existe "
            "(Manual 9 §4.1). Script Inno Setup para Windows."
        )
    assert os.path.isfile(ruta)


def test_directorio_linux_existe():
    """instaladores/linux/ debe existir para Linux (Bash)."""
    ruta = os.path.join(RAIZ, 'instaladores', 'linux')
    if not os.path.exists(ruta):
        pytest.fail(
            "RED TDD ME_30_T1: directorio instaladores/linux/ no existe "
            "(Manual 9 §4.1). Crear para Linux (Bash)."
        )
    assert os.path.isdir(ruta)


def test_directorio_macos_existe():
    """instaladores/macos/ debe existir para macOS (.dmg/.pkg)."""
    ruta = os.path.join(RAIZ, 'instaladores', 'macos')
    if not os.path.exists(ruta):
        pytest.fail(
            "RED TDD ME_30_T1: directorio instaladores/macos/ no existe "
            "(Manual 9 §4.1). Crear para macOS (.dmg/.pkg)."
        )
    assert os.path.isdir(ruta)


def test_directorio_common_existe():
    """instaladores/common/ debe existir para scripts compartidos."""
    ruta = os.path.join(RAIZ, 'instaladores', 'common')
    if not os.path.exists(ruta):
        pytest.fail(
            "RED TDD ME_30_T1: directorio instaladores/common/ no existe "
            "(Manual 9 §4.1). Crear para scripts compartidos."
        )
    assert os.path.isdir(ruta)
