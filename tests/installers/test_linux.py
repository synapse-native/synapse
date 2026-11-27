# -*- coding: utf-8 -*-
"""
tests/installers/test_linux.py — Verifica instalador Linux (Bash).
Manual 9 §4.1: Distribución para Linux.
F30 (Instalación Unificada). TDD (ME_30_T3): este oráculo debe FALLAR (RED) hasta que el código
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


class TestInstaladorLinux:
    """Manual 9 §4.1: Instalador Linux (Bash)."""

    def test_install_sh_existe(self):
        """instaladores/linux/install.sh debe existir."""
        ruta = os.path.join(RAIZ, 'instaladores', 'linux', 'install.sh')
        if not os.path.exists(ruta):
            pytest.fail(
                "RED TDD ME_30_T3: install.sh no existe "
                "(Manual 9 §4.1). Crear script Bash de instalación."
            )
        assert os.path.getsize(ruta) > 0

    def test_install_sh_es_ejecutable(self):
        """install.sh debe ser ejecutable."""
        ruta = os.path.join(RAIZ, 'instaladores', 'linux', 'install.sh')
        if not os.path.exists(ruta):
            pytest.fail("install.sh no existe")
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer install.sh"
        assert contenido.startswith('#!/bin/bash') or contenido.startswith('#!/usr/bin/env bash'), \
            "install.sh debe tener shebang #!/bin/bash"

    def test_deteccion_distribucion(self):
        """install.sh debe detectar distribución Linux."""
        ruta = os.path.join(RAIZ, 'instaladores', 'linux', 'install.sh')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer install.sh"
        assert 'apt' in contenido.lower() or 'dnf' in contenido.lower() or 'yum' in contenido.lower(), \
            "install.sh debe detectar gestor de paquetes (apt/dnf/yum)"

    def test_opciones_componentes(self):
        """install.sh debe ofrecer opciones de componentes."""
        ruta = os.path.join(RAIZ, 'instaladores', 'linux', 'install.sh')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer install.sh"
        assert 'syquex' in contenido.lower() or 'ecosistema' in contenido.lower(), \
            "install.sh debe incluir opción de Syquex/Ecosistema completo"
        assert 'opensyn' in contenido.lower(), \
            "install.sh debe incluir opción de OpenSyn"

    def test_enlaces_simbolicos(self):
        """install.sh debe crear enlaces simbólicos."""
        ruta = os.path.join(RAIZ, 'instaladores', 'linux', 'install.sh')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer install.sh"
        assert 'ln' in contenido or 'symlink' in contenido.lower() or 'enlace' in contenido.lower(), \
            "install.sh debe crear enlaces simbólicos"

    def test_directorio_instalacion(self):
        """install.sh debe instalar en directorio estándar."""
        ruta = os.path.join(RAIZ, 'instaladores', 'linux', 'install.sh')
        contenido = _leer_archivo(ruta)
        assert contenido is not None, "No se pudo leer install.sh"
        assert '/opt/synapse' in contenido or '/usr/local' in contenido or 'INSTALL_DIR' in contenido, \
            "install.sh debe instalar en /opt/synapse o /usr/local"
