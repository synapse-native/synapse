"""D-1.2 (Manual 4 §5.2; §3.2; §3.3; Manual 2 §4.3): emisión nativa del decremento
rc/arc al cierre de scope.

TDD:
  - tests/test_rc_scope_cleanup.c es la especificación de comportamiento del
    runtime: el decremento a 0 (código que el codegen nativo emite en
    gen_cerrar_bloque_c para vars de clase rc/arc) dispara el destructor
    exactamente 1 vez por instancia al salir de scope. El binario lo construye
    la fixture de sesión de conftest (enlaza todo el runtime: resuelve
    _syn_rc_*/_syn_arc_*).
  - Además se verifica que el codegen NATIVO (nucleo/generator.syn,
    regenerado desde nucleo/generador/*.syn) contiene la rama que emite
    `_syn_rc_decrement`/`_syn_arc_decrement`/`rc_weak_release` según la clase
    de la variable (D-1.2). Esto prueba que la emisión está cableada sin
    necesidad del bootstrap completo de 3 etapas.
"""
import os
import subprocess

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.path.join(PROJECT_ROOT, "tests", "test_rc_scope_cleanup.exe")
SRC = os.path.join(PROJECT_ROOT, "tests", "test_rc_scope_cleanup.c")
GEN = os.path.join(PROJECT_ROOT, "nucleo", "generator.syn")


@pytest.fixture(scope="module")
def exe_path():
    if not os.path.exists(BIN):
        pytest.fail(f"test_rc_scope_cleanup.exe no fue construido por la fixture de sesión (conftest).")
    return BIN


def _run(exe):
    r = subprocess.run([exe], capture_output=True, cwd=PROJECT_ROOT,
                       timeout=30, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout


def test_scope_cleanup_ok(exe_path):
    rc, out = _run(exe_path)
    assert rc == 0, out
    assert "RC_SCOPE_OK" in out


def test_native_codegen_emite_rc_decrement():
    # D-1.2: el codegen nativo debe emitir el decremento rc/arc al cierre de scope.
    assert os.path.exists(GEN), f"Falta {GEN}"
    with open(GEN, encoding="utf-8", errors="replace") as f:
        contenido = f.read()
    # gen_cerrar_bloque_c ramifica segun _G_scope_vars_kind
    assert "_G_scope_vars_kind" in contenido, "Falta tracking de clase RAII (D-1.2)"
    assert "_syn_rc_decrement" in contenido, "Falta emision _syn_rc_decrement (rc, Manual 4 §3.2)"
    assert "_syn_arc_decrement" in contenido, "Falta emision _syn_arc_decrement (arc, Manual 4 §3.3)"
    assert "rc_weak_release" in contenido, "Falta emision rc_weak_release (debil, Manual 4 §4.2)"
    # la clase 1=rc, 2=arc, 3=debil debe estar presente en la rama
    assert '_G_scope_vars_kind[_v] == 1' in contenido, "Rama rc no cableada"
    assert '_G_scope_vars_kind[_v] == 2' in contenido, "Rama arc no cableada"
    assert '_G_scope_vars_kind[_v] == 3' in contenido, "Rama debil no cableada"
