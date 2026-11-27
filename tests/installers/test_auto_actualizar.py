# -*- coding: utf-8 -*-
"""
tests/installers/test_auto_actualizar.py — Verifica auto-actualización.
Manual 9 §4.1: Sistema de auto-actualización para instaladores.
F30 (Instalación Unificada). TDD (ME_30_T7): este oráculo debe FALLAR (RED) hasta que el código
implemente lo que dice el manual. No usar pytest.skip.
"""
import os
import pytest

pytestmark = pytest.mark.tdd

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _importar_modulo(ruta):
    """Importa módulo Python dinámicamente."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("auto_actualizar", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TestAutoActualizar:
    """Manual 9 §4.1: Auto-actualización."""

    def test_auto_actualizar_existe(self):
        """instaladores/common/auto_actualizar.py debe existir."""
        ruta = os.path.join(RAIZ, 'instaladores', 'common', 'auto_actualizar.py')
        if not os.path.exists(ruta):
            pytest.fail(
                "RED TDD ME_30_T7: auto_actualizar.py no existe "
                "(Manual 9 §4.1). Crear módulo de auto-actualización."
            )
        assert os.path.getsize(ruta) > 0

    def test_verificar_version(self):
        """auto_actualizar.py debe tener función verificar_version."""
        ruta = os.path.join(RAIZ, 'instaladores', 'common', 'auto_actualizar.py')
        modulo = _importar_modulo(ruta)
        assert hasattr(modulo, 'verificar_version'), \
            "auto_actualizar.py debe tener función verificar_version"

    def test_descargar_actualizacion(self):
        """auto_actualizar.py debe tener función descargar_actualizacion."""
        ruta = os.path.join(RAIZ, 'instaladores', 'common', 'auto_actualizar.py')
        modulo = _importar_modulo(ruta)
        assert hasattr(modulo, 'descargar_actualizacion'), \
            "auto_actualizar.py debe tener función descargar_actualizacion"

    def test_instalar_actualizacion(self):
        """auto_actualizar.py debe tener función instalar_actualizacion."""
        ruta = os.path.join(RAIZ, 'instaladores', 'common', 'auto_actualizar.py')
        modulo = _importar_modulo(ruta)
        assert hasattr(modulo, 'instalar_actualizacion'), \
            "auto_actualizar.py debe tener función instalar_actualizacion"

    def test_rollback(self):
        """auto_actualizar.py debe tener función rollback."""
        ruta = os.path.join(RAIZ, 'instaladores', 'common', 'auto_actualizar.py')
        modulo = _importar_modulo(ruta)
        assert hasattr(modulo, 'rollback'), \
            "auto_actualizar.py debe tener función rollback"
