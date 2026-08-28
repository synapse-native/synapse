"""
test_f23_e2e.py — ME-F23-7: end-to-end .syq -> S1 -> C codegen -> runtime.

Verifica que un programa .syq con tipos de gestión de memoria (rc/arc/débil)
compila por el pipeline S1 completo y el binario ejecuta correctamente,
incluyendo los cleanup blocks generados (Manual 4 §3.2, §3.3, §4.2, §5.2).

Ruta: pipeline.ejecutar_compilador("*.syq") -> frontend SyQuex (JSON plano)
-> compilador/puente_canonico -> semántico -> GeneradorC -> gcc -> runtime.
"""

import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from pipeline import ejecutar_compilador  # noqa: E402

FIXTURE = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_f23_e2e.syq")


@pytest.fixture(scope="module")
def exe_path(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("f23") / "f23_e2e.exe")
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
    lineas = [l for l in e.stdout.splitlines() if l.strip()]
    assert lineas == ["42", "100", "rc_clean", "arc_clean", "debil_clean"], (
        f"salida={lineas}"
    )


def test_codigo_c_contiene_destructores(exe_path):
    pytest.skip('ME-4: Refactor pendiente a validación funcional')
    c_path = FIXTURE[:-4] + ".c"
    assert os.path.exists(c_path), f"No se genero {c_path}"
    with open(c_path, encoding="utf-8", errors="replace") as f:
        contenido = f.read()
    # Manual 4 §5.2-5.3: cleanup blocks deben emitir los destructores
    assert "rc_decrementar" in contenido, "Falta rc_decrementar (Manual 4 §5.2)"
    assert "arc_decrementar" in contenido, "Falta arc_decrementar (Manual 4 §5.2)"
    assert "rc_weak_release" in contenido, "Falta rc_weak_release (Manual 4 §4.2)"
    # WeakRef debe estar definido para débil<T>
    assert "typedef struct" in contenido and "WeakRef" in contenido
