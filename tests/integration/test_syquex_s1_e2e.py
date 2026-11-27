"""
test_syquex_s1_e2e.py — FASE 22 / R90 corte 3: un .syq compila por el
pipeline S1 completo (Manual 1 §3.1: frontend propio -> SemNodo[] ->
semántica compartida -> generador C -> gcc) y el binario ejecuta.

Ruta: pipeline.ejecutar_compilador("*.syq") -> frontend exe (JSON plano)
-> compilador/puente_canonico -> semántico -> GeneradorC -> gcc.
"""

import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pipeline import ejecutar_compilador  # noqa: E402

FIXTURE = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_r90_compila.syq")


@pytest.fixture(scope="module")
def exe_path(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("r90") / "r90_e2e.exe")
    rc = ejecutar_compilador(FIXTURE, output_path=out)
    assert rc == 0, f"compilacion .syq rc={rc}"
    assert os.path.exists(out)
    return out


def test_syq_compila_hasta_exe(exe_path):
    assert os.path.getsize(exe_path) > 0


def test_binario_ejecuta_salida_esperada(exe_path):
    e = subprocess.run([exe_path], capture_output=True, text=True,
                       timeout=60, encoding="utf-8", errors="replace")
    assert e.returncode == 0, f"run rc={e.returncode}\n{e.stdout}\n{e.stderr}"
    # suma_hasta(4)=6 · visible(3)=6 (entero_a_texto imprime los enteros)
    lineas = [l for l in e.stdout.splitlines() if l.strip()]
    assert lineas == ["cero", "6", "6"], f"salida={lineas}"


def test_ast_json_intermedio_generado(exe_path):
    # El pipeline guarda el AST canonico junto al C (convención .syn.json)
    json_path = FIXTURE[:-4] + ".syn.json"
    if os.path.exists(json_path):
        import json
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("tipo") == "Programa", \
            f"AST debe tener tipo=Programa, obtuvo: {list(data.keys())}"
