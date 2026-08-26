"""
FASE 24 — Test de Tiempo (Manual 3 §12.1).

TDD: este test ES la especificación. Si _syn_tiempo_* no existen,
el test C NO compila — eso es correcto.

Manual 3 §12.1: lib/tiempo.syq — Fechas y tiempos
Comando: pytest tests/syquex/test_tiempo.py -v
Criterio: valores razonables para fecha/hora del sistema
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

BIN_NAME = "test_tiempo.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)
TEST_SRC = os.path.join(PROJECT_ROOT, "tests", "test_tiempo.c")


def _find_gcc():
    gcc_candidate = os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin", "gcc.exe")
    if os.path.exists(gcc_candidate):
        return gcc_candidate
    for candidate in ("gcc", "gcc.exe"):
        try:
            subprocess.run([candidate, "--version"], capture_output=True)
            return candidate
        except FileNotFoundError:
            continue
    return gcc_candidate


@pytest.fixture(scope="module")
def exe_path():
    """Compila el test C y retorna la ruta al ejecutable."""
    if os.path.exists(BIN_ABS):
        return BIN_ABS

    gcc = _find_gcc()
    r = subprocess.run(
        [gcc, "-O2", "-I", PROJECT_ROOT, "-I.", "-o", BIN_ABS, TEST_SRC,
         "-lm", "-lpthread", "-lws2_32"],
        capture_output=True, text=True, timeout=120
    )
    if r.returncode != 0:
        pytest.fail(
            f"test_tiempo.c NO COMPILA (TDD: falta implementar §12.1).\n"
            f"Error de gcc:\n{r.stderr[-1000:]}"
        )
    assert os.path.exists(BIN_ABS), f"{BIN_NAME} no se creó"
    return BIN_ABS


def _run(exe_path):
    """Ejecuta el test C y retorna (returncode, stdout, stderr)."""
    r = subprocess.run(
        [exe_path], capture_output=True, cwd=PROJECT_ROOT,
        timeout=30, encoding="utf-8", errors="replace"
    )
    return r.returncode, r.stdout, r.stderr


class TestTiempoTimestamp:
    """§12.1 — Timestamps."""

    def test_timestamp_unix(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_tiempo falló:\n{out}\n{err}"
        assert "timestamp_unix > 1700000000" in out

    def test_timestamp_ms(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "timestamp_ms >= timestamp_unix * 1000" in out


class TestTiempoFecha:
    """§12.1 — Componentes de fecha."""

    def test_anio(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_tiempo falló:\n{out}\n{err}"
        assert "anio coincide con sistema" in out

    def test_mes(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "mes coincide con sistema" in out

    def test_dia(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "dia coincide con sistema" in out


class TestTiempoHora:
    """§12.1 — Componentes de hora."""

    def test_hora(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_tiempo falló:\n{out}\n{err}"
        assert "hora coincide con sistema" in out

    def test_minuto(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "minuto coincide con sistema" in out

    def test_segundo_rango(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "segundo en rango 0-59" in out


class TestTiempoOtros:
    """§12.1 — Día semana, día año, formato, diferencia."""

    def test_dia_semana(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_tiempo falló:\n{out}\n{err}"
        assert "dia_semana en rango 0-6" in out

    def test_dia_anio(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "dia_anio en rango 1-366" in out

    def test_fecha_formato(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "fecha_actual formato YYYY-MM-DD" in out

    def test_hora_formato(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "hora_actual formato HH:MM:SS" in out

    def test_datetime_formato(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "datetime_actual tiene espacio entre fecha y hora" in out

    def test_diferencia(self, exe_path):
        rc, out, err = _run(exe_path)
        assert "diferencia(10, 20) == 10" in out


class TestTiempoIntegracion:
    """Tests de integración completos del módulo tiempo."""

    def test_todos_los_tests_c_pasan(self, exe_path):
        rc, out, err = _run(exe_path)
        assert rc == 0, f"test_tiempo falló (rc={rc}):\n{out}\n{err}"
        assert "RESULTADO" in out, f"Sin resultados en stdout:\n{out}"
        assert "[FAIL]" not in out, f"Hay FAILs en output C:\n{out}"
