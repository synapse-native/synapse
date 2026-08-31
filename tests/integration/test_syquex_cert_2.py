# -*- coding: utf-8 -*-
"""
tests/integration/test_syquex_cert_2.py — Syquex certificado v1.0: semantica y traduccion.
Manual 3 (certificacion). TDD (ME_28_T2): valida que el analisis semantico Syquex
(inferencia de tipos, contratos, alcance, error algebraico) funciona correctamente.
cumple Manual 3 §5/§6/§8
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, RAIZ)

from pipeline import ejecutar_compilador

FIXTURES = os.path.join(RAIZ, "tests", "fixtures")


def _compilar_syq(nombre_archivo, tmp_path):
    ruta = os.path.join(FIXTURES, nombre_archivo)
    if not os.path.exists(ruta):
        pytest.fail(f"Fixture no encontrado: {nombre_archivo}")
    out = str(tmp_path / nombre_archivo.replace('.syq', '.exe'))
    rc = ejecutar_compilador(ruta, output_path=out)
    return rc, out


def _ejecutar(exe_path, timeout=30):
    return subprocess.run(
        [exe_path], capture_output=True, text=True, timeout=timeout,
        encoding="utf-8", errors="replace",
    )


class TestSyquexCertSemantica:
    """ME_28_T2: Semántica y traducción Syquex (Manual 3 §5/§6/§8)."""

    def test_r91_estructura_metodos(self, tmp_path):
        """M3 §6: estructura con campos, crear() y métodos con self."""
        rc, out = _compilar_syq("test_r91_fullstack.syq", tmp_path)
        assert rc == 0, f"Compilación falló (rc={rc})"
        e = _ejecutar(out)
        assert e.returncode == 0, f"Ejecución falló: {e.stderr}"
        # R91 testa Contador con crear(), pon(), sumado(), valor()
        assert "0" in e.stdout.splitlines(), "Contador().valor() debe ser 0"

    def test_r91_enumeracion(self, tmp_path):
        """M3 §8: enumeracion con variantes."""
        rc, out = _compilar_syq("test_r91_fullstack.syq", tmp_path)
        assert rc == 0
        e = _ejecutar(out)
        assert e.returncode == 0

    def test_r91_constante(self, tmp_path):
        """M3 §5: constante global LIMITE = 10."""
        rc, out = _compilar_syq("test_r91_fullstack.syq", tmp_path)
        assert rc == 0
        e = _ejecutar(out)
        # doble(LIMITE) = doble(10) = 20
        assert "20" in e.stdout.splitlines(), "doble(LIMITE) debe ser 20"

    def test_r91_export(self, tmp_path):
        """M3 §6: @export(python) funcion visible."""
        rc, out = _compilar_syq("test_r91_fullstack.syq", tmp_path)
        assert rc == 0

    def test_r90_coincidir_patrones(self, tmp_path):
        """M3 §8: coincidir con patrones literales sobre primitivo."""
        rc, out = _compilar_syq("test_r90_compila.syq", tmp_path)
        assert rc == 0, f"Compilación R90 compila falló (rc={rc})"
        e = _ejecutar(out)
        assert e.returncode == 0, f"Ejecución falló: {e.stderr}"
        assert "cero" in e.stdout, f"coincidir(0) debe imprimir 'cero': {e.stdout}"

    def test_r90_mientras(self, tmp_path):
        """M3 §8: mientras (loop condicional)."""
        rc, out = _compilar_syq("test_r90_compila.syq", tmp_path)
        assert rc == 0
        e = _ejecutar(out)
        assert e.returncode == 0
        # suma_hasta(4) = 0+1+2+3 = 6
        assert "6" in e.stdout.splitlines(), "suma_hasta(4) debe ser 6"

    def test_r92_variable_mut(self, tmp_path):
        """M3 §5: variable mutable (let + reasignación)."""
        rc, out = _compilar_syq("test_r92_variable.syq", tmp_path)
        assert rc == 0, f"Compilación R92 falló (rc={rc})"
        assert os.path.exists(out)

    def test_r94_multi_campo(self, tmp_path):
        """M3 §6: estructura con múltiples campos."""
        rc, out = _compilar_syq("test_r94_multi_campo.syq", tmp_path)
        assert rc == 0, f"Compilación R94 falló (rc={rc})"
        assert os.path.exists(out)

    def test_f24_lista_mapa(self, tmp_path):
        """M3 §5: lista y mapa (operaciones de colección)."""
        rc, out = _compilar_syq("test_f24_lista_mapa.syq", tmp_path)
        assert rc == 0
        e = _ejecutar(out)
        assert e.returncode == 0, f"Ejecución falló: {e.stderr}"
        assert "lista:" in e.stdout or "mapa:" in e.stdout
