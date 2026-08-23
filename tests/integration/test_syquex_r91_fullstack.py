"""
test_syquex_r91_fullstack.py — FASE 22 / R91: validación full-stack del
frontend Syquex sobre el backend compartido (Manual 1 §3.1; Manual 3 §3
L88-92 OOP con métodos sin parámetros; Manual 6 §1.3 lowering de call-sites).

Ruta validada: .syq -> syq_frontend.exe (SemNodo[] -> JSON plano) ->
compilador/puente_canonico (con lowering OOP H-R90-5) -> análisis semántico
S1 -> GeneradorC -> gcc -> ejecución.
"""

import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pipeline import ejecutar_compilador  # noqa: E402

FIXTURE = os.path.join(PROJECT_ROOT, "tests", "fixtures",
                       "test_r91_fullstack.syq")

SALIDA_ESPERADA = ["0", "100", "20", "5", "ok"]


@pytest.fixture(scope="module")
def exe_path(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("r91") / "r91_fullstack.exe")
    rc = ejecutar_compilador(FIXTURE, output_path=out)
    assert rc == 0, f"compilación .syq full-stack rc={rc}"
    assert os.path.exists(out)
    return out


def test_compila_hasta_exe(exe_path):
    assert os.path.getsize(exe_path) > 0


def test_oop_lowering_y_coincidir_primitivos(exe_path):
    """Valida en UNA ejecución: ctor sin args, método sin params que
    retorna, método con params + self inyectado (H-R90-5), coincidir
    literal/primitivo (H-R90-6), constante, @export."""
    e = subprocess.run([exe_path], capture_output=True, text=True,
                       timeout=60, encoding="utf-8", errors="replace")
    assert e.returncode == 0, f"run rc={e.returncode}\n{e.stdout}\n{e.stderr}"
    lineas = [l for l in e.stdout.splitlines() if l.strip()]
    assert lineas == SALIDA_ESPERADA, f"salida={lineas}"
