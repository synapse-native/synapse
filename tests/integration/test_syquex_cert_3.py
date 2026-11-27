# -*- coding: utf-8 -*-
"""
tests/integration/test_syquex_cert_3.py — Syquex certificado v1.0: integracion e2e.
Manual 3 (certificacion). TDD (ME_28_T3): valida el pipeline completo Syquex
(.syq → frontend → puente → codegen S1 → gcc → ejecutable) end-to-end.
cumple Manual 3 3
"""
import os
import subprocess
import sys
import glob

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


def _listar_fixtures_syq():
    """Lista todos los fixtures .syq disponibles."""
    return sorted(glob.glob(os.path.join(FIXTURES, "*.syq")))


class TestSyquexCertE2E:
    """ME_28_T3: Integración end-to-end Syquex (pipeline completo)."""

    def test_r91_pipeline_completo(self, tmp_path):
        """M3 §3: Pipeline completo .syq → exe con output verificable."""
        rc, out = _compilar_syq("test_r91_fullstack.syq", tmp_path)
        assert rc == 0, f"Pipeline completo falló (rc={rc})"
        assert os.path.exists(out) and os.path.getsize(out) > 100
        e = _ejecutar(out)
        assert e.returncode == 0, f"Ejecución e2e falló: {e.stderr}"
        lineas = e.stdout.strip().splitlines()
        assert len(lineas) >= 4, f"Salida insuficiente: {e.stdout}"

    def test_r90_compila_pipeline(self, tmp_path):
        """M3 §3: Pipeline R90 (funciones + coincidir + mientras)."""
        rc, out = _compilar_syq("test_r90_compila.syq", tmp_path)
        assert rc == 0
        e = _ejecutar(out)
        assert e.returncode == 0
        assert "cero" in e.stdout

    def test_r92_pipeline(self, tmp_path):
        """M3 §3: Pipeline R92 (variable mutable)."""
        rc, out = _compilar_syq("test_r92_variable.syq", tmp_path)
        assert rc == 0

    def test_f24_simple_pipeline(self, tmp_path):
        """M3 §3: Pipeline F24 (IO básico)."""
        rc, out = _compilar_syq("test_f24_simple.syq", tmp_path)
        assert rc == 0

    def test_f24_lista_mapa_pipeline(self, tmp_path):
        """M3 §3: Pipeline F24 (lista + mapa)."""
        rc, out = _compilar_syq("test_f24_lista_mapa.syq", tmp_path)
        assert rc == 0
        e = _ejecutar(out)
        assert e.returncode == 0

    def test_range_loop_pipeline(self, tmp_path):
        """M3 §3: Pipeline (rango con paso)."""
        rc, out = _compilar_syq("test_range_loop.syq", tmp_path)
        assert rc == 0

    def test_r94_multi_campo_pipeline(self, tmp_path):
        """M3 §3: Pipeline R94 (estructura multi-campo)."""
        rc, out = _compilar_syq("test_r94_multi_campo.syq", tmp_path)
        assert rc == 0

    def test_todos_los_fixtures_compilan(self, tmp_path):
        """M3 §3: Todos los fixtures .syq compilan sin errores (excepto known limitations)."""
        KNOWN_LIMITED = {"test_r90_e2e.syq", "test_r89_e2e.syq", "test_h12_oraculo_modelo.syq",
                         "test_f24_io.syq", "test_r92_neg_let.syq"}
        fixtures = _listar_fixtures_syq()
        assert len(fixtures) >= 10, f"Pocos fixtures: {len(fixtures)}"
        fallos = []
        for ruta in fixtures:
            nombre = os.path.basename(ruta)
            if nombre in KNOWN_LIMITED:
                continue
            out = str(tmp_path / nombre.replace('.syq', '.exe'))
            rc = ejecutar_compilador(ruta, output_path=out)
            if rc != 0:
                fallos.append(f"{nombre}: rc={rc}")
        assert len(fallos) == 0, (
            f"Fixtures fallan:\n" + "\n".join(fallos)
        )

    def test_r91_ejecuta_valores_correctos(self, tmp_path):
        """M3 §3: R91 ejecuta y produce valores exactos del manual."""
        rc, out = _compilar_syq("test_r91_fullstack.syq", tmp_path)
        assert rc == 0
        e = _ejecutar(out)
        assert e.returncode == 0
        lineas = e.stdout.strip().splitlines()
        # R91 spec: 0, 100, 20, 5, ok
        assert lineas[0] == "0", f"Linea 1: esperaba 0, got {lineas[0]}"
        assert lineas[1] == "100", f"Linea 2: esperaba 100, got {lineas[1]}"
        assert lineas[2] == "20", f"Linea 3: esperaba 20, got {lineas[2]}"
        assert lineas[3] == "5", f"Linea 4: esperaba 5, got {lineas[3]}"
        assert lineas[4] == "ok", f"Linea 5: esperaba ok, got {lineas[4]}"
