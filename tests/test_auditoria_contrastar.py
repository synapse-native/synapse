# Verificacion del gate MTS (auditoria/contrastar.py). Manual 2 §12 (contratos).
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "auditoria"))
import contrastar as ct

PLAN = """requisito: Manual 8 §1.2
texto: rechaza Content-Length invalido
implementacion: validacion de protocolo LSP
oraculo: tests/test_lsp_release_invalid.py

requisito: Manual 2 §8.2
texto: tipos ADT anidados
implementacion: parseo balanceado
oraculo: tests/test_adt.py
"""


def test_parsear_plan_por_bloque():
    # Empareja requisito<->oraculo por bloque, no por posicion (zip).
    reqs = ct.parsear_plan(PLAN)
    assert len(reqs) == 2
    assert reqs[0]["manual"] == "8" and reqs[0]["seccion"] == "1.2"
    assert reqs[0]["oraculo"] == "tests/test_lsp_release_invalid.py"
    assert reqs[1]["manual"] == "2" and reqs[1]["seccion"] == "8.2"
    assert reqs[1]["oraculo"] == "tests/test_adt.py"


def test_seccion_existe_y_no_existe():
    assert ct.seccion_existe("2", "12") is True
    assert ct.seccion_existe("2", "999") is False
    assert ct.seccion_existe("99", "1") is False


def test_cubre_req_prefijo():
    citas = [("8", "1.2")]
    assert ct.cubre_req("8", "1.2", citas) is True
    assert ct.cubre_req("8", "1", citas) is True
    assert ct.cubre_req("2", "8.2", citas) is False


def test_citas_archivo():
    src = "// cumple Manual 8 §1.2\nfuncion x() {}\n# cumple Manual 2 §8.2\n"
    p = os.path.join(tempfile.gettempdir(), "t_citas_contrastar.syn")
    with open(p, "w", encoding="utf-8") as f:
        f.write(src)
    citas = ct.citas_archivo(p)
    assert ("8", "1.2") in citas and ("2", "8.2") in citas
    os.remove(p)
