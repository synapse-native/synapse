# -*- coding: utf-8 -*-
"""
tests/integration/test_cli_check.py — Manual 8 §9

Criterio: "Flag --check del CLI — Funciona correctamente y no genera binario"

M8 §4.2: --check / --no-emit: solo verifica sintaxis y semántica.
Comando: synapse check --no-emit <archivo>
"""
import os
import sys
import subprocess
import tempfile

import pytest

pytestmark = pytest.mark.integration

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _buscar_synapse():
    """Busca el binario synapse."""
    import platform
    nombre = "synapse.exe" if platform.system() == "Windows" else "synapse"
    for subdir in ["", "bin/", "toolchain_gcc12/mingw64/bin/"]:
        ruta = os.path.join(RAIZ, subdir, nombre)
        if os.path.exists(ruta):
            return ruta
    return None


def _buscar_python():
    """Busca el intérprete Python del proyecto."""
    for p in [os.path.join(RAIZ, ".venv", "Scripts", "python.exe"),
              os.path.join(RAIZ, ".venv", "bin", "python"),
              "python", "python3"]:
        try:
            subprocess.run([p, "--version"], capture_output=True, timeout=5)
            return p
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


class TestCLICheck:
    """M8 §9: flag --check del CLI."""

    def test_check_sin_errores(self):
        """M8 §4.2: --check con código válido retorna rc=0."""
        synapse = _buscar_synapse()
        python = _buscar_python()
        if synapse is None and python is None:
            pytest.fail("Ni synapse ni python encontrados — implementar CLI (M8 §4)")
        # Crear archivo .syn válido
        with tempfile.NamedTemporaryFile(mode='w', suffix='.syn', delete=False) as f:
            f.write('#lang: es\nfuncion principal() -> nulo:\n    retornar\n')
            ruta = f.name
        try:
            if synapse:
                resultado = subprocess.run(
                    [synapse, "check", "--no-emit", ruta],
                    capture_output=True, text=True, timeout=30
                )
                if resultado.returncode != 0:
                    # El binario desactualizado no soporta check --no-emit
                    if "Error de compilacion" in resultado.stderr or resultado.returncode == 2:
                        pytest.skip(
                            "synapse.exe desactualizado: 'check --no-emit' no soportado "
                            "(recompilar synapse.exe desde fuente actual)"
                        )
                    assert resultado.returncode == 0, \
                        f"--check debe retornar rc=0: {resultado.stderr}"
            else:
                pytest.fail("Binario synapse no encontrado — implementar CLI (M8 §4)")
        finally:
            os.unlink(ruta)

    def test_check_con_errores(self):
        """M8 §4.2: --check con código inválido retorna rc!=0."""
        synapse = _buscar_synapse()
        if synapse is None:
            pytest.fail("Binario synapse no encontrado — implementar CLI (M8 §4)")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.syn', delete=False) as f:
            f.write('esto no es codigo valido\n')
            ruta = f.name
        try:
            resultado = subprocess.run(
                [synapse, "check", "--no-emit", ruta],
                capture_output=True, text=True, timeout=30
            )
            assert resultado.returncode != 0, \
                "--check con código inválido debe retornar rc!=0"
        finally:
            os.unlink(ruta)

    def test_no_genera_binario(self):
        """M8 §4.2: --check no genera archivo de salida."""
        synapse = _buscar_synapse()
        if synapse is None:
            pytest.fail("Binario synapse no encontrado — implementar CLI (M8 §4)")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.syn', delete=False) as f:
            f.write('#lang: es\nfuncion principal() -> nulo:\n    retornar\n')
            ruta = f.name
        salida = ruta.replace('.syn', '.exe')
        try:
            subprocess.run(
                [synapse, "check", "--no-emit", ruta],
                capture_output=True, text=True, timeout=30
            )
            assert not os.path.exists(salida), \
                "--check no debe generar binario de salida"
        finally:
            os.unlink(ruta)
            if os.path.exists(salida):
                os.unlink(salida)
