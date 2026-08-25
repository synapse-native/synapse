"""
test_r94_multi_campo.py — AUDITOR-4: structs multi-campo e2e
(Manual 3 §6.2: estructura con >=2 campos, field access, field assignment,
method call con self inyectado).

Verifica que el pipeline S1 completo (.syq → syq_frontend → JSON → puente →
semántico → GeneradorC → gcc → ejecución) maneja structs con 2+ campos
correctamente. Todos los tests anteriores usaban structs de 1 campo.
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pipeline import ejecutar_compilador

FIXTURE = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_r94_multi_campo.syq")
SALIDA_ESPERADA = ["8", "11", "5"]


@pytest.fixture(scope="module")
def exe_path(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("r94mc") / "r94_mc.exe")
    rc = ejecutar_compilador(FIXTURE, output_path=out)
    assert rc == 0, f"compilación .syq multi-campo rc={rc}"
    assert os.path.exists(out)
    return out


def test_compila_hasta_exe(exe_path):
    assert os.path.getsize(exe_path) > 0


def test_multi_campo_field_access_assignment(exe_path):
    """Valida en UNA ejecución: ctor sin args, 2-field struct, field assignment
    (p.xx=3, p.yy=5), method call con self injectado (p.sumar(2,1)), field read."""
    e = subprocess.run([exe_path], capture_output=True, text=True,
                       timeout=60, encoding="utf-8", errors="replace")
    assert e.returncode == 0, f"run rc={e.returncode}\n{e.stdout}\n{e.stderr}"
    lineas = [l for l in e.stdout.splitlines() if l.strip()]
    assert lineas == SALIDA_ESPERADA, f"salida={lineas}"
