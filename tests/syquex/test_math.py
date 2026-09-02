"""
FASE 24 — Test de Math (Manual 3 §12.1).

TDD: este test ES la especificación. Si _syn_potencia/_syn_sqrt/etc.
no existen, el test C NO compila — eso es correcto. Se corrige el CÓDIGO, no el test.

Manual 3 §12.1: lib/math.syq — Matemáticas y estadísticas
Comando: pytest tests/syquex/test_math.py -v
Criterio: precisión razonable para funciones de punto flotante
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

BIN_NAME = "test_math.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)
TEST_SRC = os.path.join(PROJECT_ROOT, "tests", "test_math.c")


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
            f"test_math.c NO COMPILA (TDD: falta implementar §12.1).\n"
            f"Error de gcc:\n{r.stderr[-1000:]}"
        )
    assert os.path.exists(BIN_ABS), f"{BIN_NAME} no se creó"
    return BIN_ABS


class TestMathPotencia:
    """§12.1 — Potencia y raíz cuadrada."""

    def test_potencia(self, exe_path):
        """Potencia: 2^10 = 1024."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert r.returncode == 0, f"test_math falló:\n{r.stdout}\n{r.stderr}"
        assert "potencia(2,10) == 1024" in r.stdout

    def test_potencia_negativa(self, exe_path):
        """Potencia negativa: 2^(-1) = 0.5."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert "potencia(2,-1) == 0.5" in r.stdout

    def test_potencia_cero(self, exe_path):
        """Potencia cero: 5^0 = 1."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert "potencia(5,0) == 1" in r.stdout


class TestMathRaiz:
    """§12.1 — Raíz cuadrada."""

    def test_sqrt_cuadrado_perfecto(self, exe_path):
        """sqrt(4) = 2."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert r.returncode == 0, f"test_math falló:\n{r.stdout}\n{r.stderr}"
        assert "sqrt(4) == 2" in r.stdout

    def test_sqrt_cero(self, exe_path):
        """sqrt(0) = 0."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert "sqrt(0) == 0" in r.stdout

    def test_sqrt_irracional(self, exe_path):
        """sqrt(2) ~ 1.414."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert "sqrt(2) ~ 1.414" in r.stdout


class TestMathTrigonometria:
    """§12.1 — Trigonometría."""

    def test_seno(self, exe_path):
        """sen(0) = 0, sen(pi/2) ~ 1."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert r.returncode == 0, f"test_math falló:\n{r.stdout}\n{r.stderr}"
        assert "sen(0) == 0" in r.stdout
        assert "sen(pi/2) ~ 1" in r.stdout

    def test_coseno(self, exe_path):
        """cos(0) = 1, cos(pi) ~ -1."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert "cos(0) == 1" in r.stdout
        assert "cos(pi) ~ -1" in r.stdout

    def test_tangente(self, exe_path):
        """tan(0) = 0, tan(pi/4) ~ 1."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert "tan(0) == 0" in r.stdout
        assert "tan(pi/4) ~ 1" in r.stdout


class TestMathRedondeo:
    """§12.1 — Redondeo."""

    def test_round(self, exe_path):
        """round(1.5) = 2, round(1.4) = 1."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert r.returncode == 0, f"test_math falló:\n{r.stdout}\n{r.stderr}"
        assert "round(1.5) == 2" in r.stdout
        assert "round(1.4) == 1" in r.stdout

    def test_round_negativo(self, exe_path):
        """round(-1.5) = -2."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert "round(-1.5) == -2" in r.stdout

    def test_ceil(self, exe_path):
        """ceil(1.1) = 2, ceil(2.0) = 2."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert "ceil(1.1) == 2" in r.stdout
        assert "ceil(2.0) == 2" in r.stdout

    def test_floor(self, exe_path):
        """floor(1.9) = 1, floor(2.0) = 2."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert "floor(1.9) == 1" in r.stdout
        assert "floor(2.0) == 2" in r.stdout


class TestMathLogaritmos:
    """§12.1 — Logaritmos."""

    def test_logaritmo(self, exe_path):
        """log(1) = 0, log(e) ~ 1."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert r.returncode == 0, f"test_math falló:\n{r.stdout}\n{r.stderr}"
        assert "log(1) == 0" in r.stdout
        assert "log(e) ~ 1" in r.stdout


class TestMathIntegracion:
    """Tests de integración completos del módulo math."""

    def test_todos_los_tests_c_pasan(self, exe_path):
        """Verifica que TODOS los tests C pasaron (sin FAILs)."""
        r = subprocess.run([exe_path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        assert r.returncode == 0, f"test_math falló (rc={r.returncode}):\n{r.stdout}\n{r.stderr}"
        assert "RESULTADO" in r.stdout, f"Sin resultados en stdout:\n{r.stdout}"
        assert "[FAIL]" not in r.stdout, f"Hay FAILs en output C:\n{r.stdout}"
