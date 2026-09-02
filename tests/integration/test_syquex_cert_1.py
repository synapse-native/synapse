# -*- coding: utf-8 -*-
"""
tests/integration/test_syquex_cert_1.py — Syquex certificado v1.0: conformidad de frontend (Hito 7).
Manual 3 §3 (certificacion). TDD (ME_28_T1): valida que el frontend Syquex
(lexer → parser → AST → puente → codegen S1) produce código C válido que compila y ejecuta.
cumple Manual 3 3
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


class TestSyquexCertFrontend:
    """ME_28_T1: Conformidad de frontend Syquex (Manual 3 §3)."""

    def test_r91_fullstack_compila(self, tmp_path):
        """M3 §3: Syquex fullstack (estructura+metodos+enumeracion+export) compila."""
        rc, out = _compilar_syq("test_r91_fullstack.syq", tmp_path)
        assert rc == 0, f"Compilación falló (rc={rc})"
        assert os.path.exists(out) and os.path.getsize(out) > 0

    def test_r91_fullstack_ejecuta(self, tmp_path):
        """M3 §3: Syquex fullstack ejecuta y produce salida correcta."""
        rc, out = _compilar_syq("test_r91_fullstack.syq", tmp_path)
        assert rc == 0
        e = _ejecutar(out)
        assert e.returncode == 0, f"Ejecución falló: {e.stderr}"
        lineas = e.stdout.strip().splitlines()
        assert "0" in lineas, f"Esperaba '0' en salida: {e.stdout}"
        assert "100" in lineas, f"Esperaba '100' en salida: {e.stdout}"
        assert "ok" in lineas, f"Esperaba 'ok' en salida: {e.stdout}"

    def test_r90_coincidir_compila(self, tmp_path):
        """M3 §3: Syquex R90 — coincidir + enumeracion + constante + @export (sin para_en/intentar)."""
        rc, out = _compilar_syq("test_r90_compila.syq", tmp_path)
        assert rc == 0, f"Compilación R90 compila falló (rc={rc})"
        assert os.path.exists(out)
        e = _ejecutar(out)
        assert e.returncode == 0, f"Ejecución R90 falló: {e.stderr}"
        assert "cero" in e.stdout

    def test_r89_estructura_export_compila(self, tmp_path):
        """M3 §3: Syquex R89 — estructura + crear() + metodos + @export (R91 fullstack)."""
        rc, out = _compilar_syq("test_r91_fullstack.syq", tmp_path)
        assert rc == 0, f"Compilación R89 estructura falló (rc={rc})"
        assert os.path.exists(out)
        e = _ejecutar(out)
        assert e.returncode == 0, f"Ejecución R89 falló: {e.stderr}"
        assert "0" in e.stdout.splitlines()

    def test_r92_variable_compila(self, tmp_path):
        """M3 §3: Syquex R92 (variable mutable, asignación) compila."""
        rc, out = _compilar_syq("test_r92_variable.syq", tmp_path)
        assert rc == 0, f"Compilación R92 falló (rc={rc})"
        assert os.path.exists(out)

    def test_f24_simple_compila(self, tmp_path):
        """M3 §3: Syquex F24 (IO básico, imprimir) compila."""
        rc, out = _compilar_syq("test_f24_simple.syq", tmp_path)
        assert rc == 0, f"Compilación F24 simple falló (rc={rc})"
        assert os.path.exists(out)

    def test_f24_lista_mapa_compila(self, tmp_path):
        """M3 §3: Syquex F24 (lista + mapa) compila."""
        rc, out = _compilar_syq("test_f24_lista_mapa.syq", tmp_path)
        assert rc == 0, f"Compilación F24 lista+mapa falló (rc={rc})"
        assert os.path.exists(out)

    def test_f24_lista_mapa_ejecuta(self, tmp_path):
        """M3 §3: Syquex F24 (lista + mapa) ejecuta correctamente."""
        rc, out = _compilar_syq("test_f24_lista_mapa.syq", tmp_path)
        assert rc == 0
        e = _ejecutar(out)
        assert e.returncode == 0, f"Ejecución falló: {e.stderr}"
        assert "lista:" in e.stdout or "mapa:" in e.stdout

    def test_range_loop_compila(self, tmp_path):
        """M3 §3: Syquex (rango con paso) compila."""
        rc, out = _compilar_syq("test_range_loop.syq", tmp_path)
        assert rc == 0, f"Compilación range falló (rc={rc})"
        assert os.path.exists(out)

    def test_r94_multi_campo_compila(self, tmp_path):
        """M3 §3: Syquex R94 (estructura multi-campo) compila."""
        rc, out = _compilar_syq("test_r94_multi_campo.syq", tmp_path)
        assert rc == 0, f"Compilación R94 falló (rc={rc})"
        assert os.path.exists(out)
