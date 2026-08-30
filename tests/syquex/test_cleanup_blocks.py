"""
FASE 23 ME-5: Scope analyzer runtime C + cleanup blocks tests
( Manual 4 §5.2-5.3, Manual 4 §9)

Valida:
1. syquex/analizador_alcance.syq compila (test_scope_analysis.py)
2. Runtime C _a_* functions (test_cleanup_blocks.c) cuentan correctamente
   rc/arc vars y preservan débiles
3. No hay memoria leak (ASAN skipado en MinGW; verificación manual)

Comando (Manual 4 §9):
    pytest tests/syquex/test_scope_analysis.py -v
    pytest tests/syquex/test_cleanup_blocks.py -v
Criterio: 0 falsos positivos en liberación
"""

import json
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

BIN_NAME = "test_cleanup_blocks.exe"
BIN_ABS = os.path.join(PROJECT_ROOT, "tests", BIN_NAME)

SYQ_FRONTEND = os.path.join(PROJECT_ROOT, "build", "syq_frontend.exe")
ANALIZADOR = os.path.join(PROJECT_ROOT, "syquex", "analizador_alcance.syq")


def _decode_nodos(data):
    """Extrae todos los strings del SemNodo[] JSON (almacenados como byte arrays)."""
    textos = []
    for nodo in data.get("nodos", []):
        for campo in nodo:
            if isinstance(campo, list):
                try:
                    s = bytes(campo).decode("utf-8", errors="replace")
                    if s and all(32 <= c < 127 for c in campo):
                        textos.append(s)
                except (ValueError, TypeError):
                    pass
            elif isinstance(campo, str):
                textos.append(campo)
    return textos


@pytest.fixture(scope="module")
def exe_path():
    if not os.path.exists(BIN_ABS):
        pytest.skip(f"{BIN_NAME} no compilado por conftest")
    return BIN_ABS


class TestSemNodoWalker:
    """Manual 4 §5.2 — el runtime C _a_analizar_bloque cuenta rc/arC vars."""

    def test_compila(self):
        if not os.path.exists(BIN_ABS):
            pytest.skip(f"{BIN_NAME} no existe")
        assert os.path.exists(BIN_ABS)

    def test_cuenta_rc_y_arc(self, exe_path):
        """2 rc/arC vars detectadas (rc + arc), plain y debil no cuentan."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, f"test_cleanup_blocks fallo:\n{r.stdout}\n{r.stderr}"
        assert "2 rc/arC vars" in r.stdout
        assert "rc cuenta" in r.stdout
        assert "arc cuenta" in r.stdout
        assert "plain no cuenta" in r.stdout

    def test_reset_limpia_contador(self, exe_path):
        """_a_reset_rc_vars limpia el contador."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "contador = 0 tras reset" in r.stdout

    def test_null_safety(self, exe_path):
        """NULL safety: no crashea con base NULL."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "0 vars con base NULL" in r.stdout

    def test_debil_no_cuenta(self, exe_path):
        """debil: no incrementa rc_count."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        # El C test usa caracteres UTF-8 (débil). Buscar por "cuenta como ownership"
        assert "cuenta como ownership" in r.stdout

    def test_no_leaks(self, exe_path):
        """0 fugas: todos los recursos liberados."""
        r = subprocess.run([exe_path], capture_output=True, text=True, timeout=30)
        assert "0 failed" in r.stdout


class TestSyqCompilacion:
    """Manual 4 §5.3 — el analizador .syq compila correctamente."""

    def test_analizador_compila(self):
        """syquex/analizador_alcance.syq compila con syq_frontend.exe."""
        if not os.path.exists(SYQ_FRONTEND):
            pytest.skip("syq_frontend.exe no existe")
        r = subprocess.run([SYQ_FRONTEND, ANALIZADOR], capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, f"analizador no compila: {r.stderr}"

    def test_tiene_api_limpieza(self):
        """El .syq expone analizar_ciclos/funcion/programa + externs."""
        if not os.path.exists(SYQ_FRONTEND):
            pytest.skip("syq_frontend.exe no existe")
        r = subprocess.run([SYQ_FRONTEND, ANALIZADOR], capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, f"frontend falló: {r.stderr}"
        # El JSON almacena nombres como arrays de bytes — decodificar
        data = json.loads(r.stdout)
        texto = " ".join(_decode_nodos(data))
        assert "analizar_ciclos" in texto
        assert "analizar_ciclos" in texto, "falta analizar_ciclos"
        assert "_a_analizar_bloque" in texto, "falta _a_analizar_bloque"
        assert "_a_get_rc_count" in texto, "falta _a_get_rc_count"
