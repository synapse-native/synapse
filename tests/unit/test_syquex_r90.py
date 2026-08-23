"""
test_syquex_r90.py — FASE 22 / R90: serialización SemNodo[] -> JSON plano
(Manual 1 §3.1: el traductor alimenta el backend compartido; Manual 6 §1.2
ABI v1). Construye el frontend (scripts/build_syquex_frontend.py), lo ejecuta
sobre tests/fixtures/test_r90_e2e.syq y valida el esquema plano que consumirá
compilador/puente_canonico.py.
"""

import json
import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FRONTEND = os.path.join(PROJECT_ROOT, "build", "syq_frontend.exe")
FIXTURE_SYQ = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_r90_e2e.syq")


@pytest.fixture(scope="module")
def flat() -> dict:
    r = subprocess.run(
        [sys.executable, os.path.join(PROJECT_ROOT, "scripts",
                                      "build_syquex_frontend.py")],
        capture_output=True, text=True, timeout=900, cwd=PROJECT_ROOT)
    assert r.returncode == 0, f"build frontend rc={r.returncode}\n{r.stderr[-2000:]}"
    assert os.path.exists(FRONTEND)

    e = subprocess.run([FRONTEND, FIXTURE_SYQ], capture_output=True,
                       text=True, timeout=120, encoding="utf-8",
                       errors="replace")
    assert e.returncode == 0, f"frontend rc={e.returncode}\n{e.stdout[-800:]}"
    assert "SYQ_JSON_ERROR" not in e.stdout
    return json.loads(e.stdout)


def _texto(nodo: list) -> str:
    campo = nodo[8]
    if campo is None:
        return ""
    return bytes(campo).decode("utf-8")


def test_esquema_cabecera(flat):
    assert flat["syquex_flat"] == "1"
    assert flat["total"] == len(flat["nodos"])
    assert flat["total"] > 40
    assert flat["raiz"] == 0


def test_raiz_programa_y_sin_bloque_sq(flat):
    nodos = flat["nodos"]
    assert nodos[0][0] == 1          # NODO_PROGRAMA reservado (ABI v1 R85)
    tipos = {n[0] for n in nodos}
    assert 58 not in tipos           # BLOQUE_SQ desenrollado (paridad R22)


def _nombres_funcion(flat):
    return {_texto(n) for n in flat["nodos"] if n[0] == 2}   # NODO_FUNCION=2


def test_funciones_decoradas_presentes(flat):
    nombres = _nombres_funcion(flat)
    assert "__init__" in nombres
    assert "Punto_desplazar" in nombres
    assert {"visible", "clasifica", "usa_color", "principal"} <= nombres


def test_estructura_solo_campos(flat):
    nodos = flat["nodos"]
    est = next(n for n in nodos if n[0] == 16 and _texto(n) == "Punto")
    campos = []
    f = est[4]                       # hizq = cadena de miembros
    while f > 0:
        n = nodos[f]
        if _texto(n) in ("x", "yy"):
            campos.append(_texto(n))
        f = n[6]                     # herm
    assert campos == ["x", "yy"]     # métodos hoisteados: solo PARAMETRO queda


def test_patrones_caso_como_texto(flat):
    # CASO=39: patrón reconstruido como span slot1 (paridad R11/R22)
    casos = [_texto(n) for n in flat["nodos"] if n[0] == 39]
    assert casos == ["0", "_", "rojo(v)", "verde", "_"]


def test_metadata_linea_estructura(flat):
    nodos = flat["nodos"]
    est = next(n for n in nodos if n[0] == 16 and _texto(n) == "Punto")
    assert est[1] == 9               # línea de `estructura Punto` en el fixture R90


def test_export_preserva_idioma(flat):
    # NODO_EXPORT=50 con payload del lenguaje (@export(python), R89 H-R88-1)
    exports = [_texto(n) for n in flat["nodos"] if n[0] == 50]
    assert any("python" in t for t in exports)


def test_json_roundtrip_indices_validos(flat):
    total = flat["total"]
    for n in flat["nodos"]:
        for idx in (n[4], n[5], n[6]):
            assert -1 <= idx < total
