# -*- coding: utf-8 -*-
"""
tests/installers/test_docs.py — Verifica documentación de instaladores.
Manual 9 §4.1: Documentación de packaging e instalación.
F30 (Instalación Unificada). TDD (ME_30_T8): este oráculo debe FALLAR (RED) hasta que el código
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


class TestDocsInstaladores:
    """Manual 9 §4.1: Documentación de instaladores."""

    def test_readme_instaladores_existe(self):
        """instaladores/README.md debe existir."""
        ruta = os.path.join(RAIZ, 'instaladores', 'README.md')
        if not os.path.exists(ruta):
            pytest.fail(
                "RED TDD ME_30_T8: README.md no existe "
                "(Manual 9 §4.1). Crear documentación de instaladores."
            )
        assert os.path.getsize(ruta) > 0

    def test_readme_tiene_instrucciones_windows(self):
        """README.md debe tener instrucciones para Windows."""
        ruta = os.path.join(RAIZ, 'instaladores', 'README.md')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer README.md"
        assert 'windows' in contenido.lower() or 'inno setup' in contenido.lower() or '.exe' in contenido.lower(), \
            "README.md debe tener instrucciones para Windows"

    def test_readme_tiene_instrucciones_linux(self):
        """README.md debe tener instrucciones para Linux."""
        ruta = os.path.join(RAIZ, 'instaladores', 'README.md')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer README.md"
        assert 'linux' in contenido.lower() or 'install.sh' in contenido.lower() or 'apt' in contenido.lower(), \
            "README.md debe tener instrucciones para Linux"

    def test_readme_tiene_instrucciones_macos(self):
        """README.md debe tener instrucciones para macOS."""
        ruta = os.path.join(RAIZ, 'instaladores', 'README.md')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer README.md"
        assert 'macos' in contenido.lower() or 'dmg' in contenido.lower() or '.app' in contenido.lower(), \
            "README.md debe tener instrucciones para macOS"

    def test_readme_tiene_requisitos_previos(self):
        """README.md debe indicar requisitos previos."""
        ruta = os.path.join(RAIZ, 'instaladores', 'README.md')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer README.md"
        assert 'requisitos' in contenido.lower() or 'prerequisitos' in contenido.lower() or 'requirements' in contenido.lower(), \
            "README.md debe indicar requisitos previos"
