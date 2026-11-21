# cumple Manual 1 §7.2 — la suite completa de pruebas debe poder medirse y su
# composición no puede encogerse ni ganar skips en silencio.
# cumple Manual 9 §6.2 — el gate de la suite tiene que poder fallar: un informe
# sin ratchet no es evidencia de que la suite completa siga corriendo.
"""Regresión de `auditoria/verificar_suite.py` (ME r279).

Árboles sintéticos: el gate pasa con la composición registrada, falla cuando una
suite pierde tests o gana skips, y `--medir` deja recuentos y duración reales.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
GATE = RAIZ / "auditoria" / "verificar_suite.py"


def _cargar_gate():
    spec = importlib.util.spec_from_file_location("verificar_suite", GATE)
    modulo = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modulo)
    return modulo


def _arbol(tmp_path: Path) -> Path:
    raiz = tmp_path / "repo"
    unidad = raiz / "tests" / "unit"
    unidad.mkdir(parents=True)
    (unidad / "test_a.py").write_text(
        "def test_uno():\n    assert True\n\n"
        "def test_dos():\n    assert True\n", encoding="utf-8")
    return raiz


def test_verde_con_baseline(tmp_path, capsys):
    raiz = _arbol(tmp_path)
    gate = _cargar_gate()
    assert gate.main(["--raiz", str(raiz), "--baseline"]) == 0
    capsys.readouterr()
    assert gate.main(["--raiz", str(raiz)]) == 0
    salida = capsys.readouterr().out
    assert "OK: suite" in salida
    assert "2 tests recolectados" in salida


def test_falla_si_desaparecen_tests(tmp_path, capsys):
    raiz = _arbol(tmp_path)
    gate = _cargar_gate()
    assert gate.main(["--raiz", str(raiz), "--baseline"]) == 0
    capsys.readouterr()
    (raiz / "tests" / "unit" / "test_a.py").write_text(
        "def test_uno():\n    assert True\n", encoding="utf-8")
    assert gate.main(["--raiz", str(raiz)]) == 1
    salida = capsys.readouterr().out
    assert "tests perdidos" in salida


def test_falla_si_aparece_skip_nuevo(tmp_path, capsys):
    raiz = _arbol(tmp_path)
    gate = _cargar_gate()
    assert gate.main(["--raiz", str(raiz), "--baseline"]) == 0
    capsys.readouterr()
    archivo = raiz / "tests" / "unit" / "test_a.py"
    archivo.write_text(
        "import pytest\n\n\n"
        "@pytest.mark.skip(reason='temporal')\n"
        "def test_uno():\n    assert True\n\n"
        "def test_dos():\n    assert True\n", encoding="utf-8")
    assert gate.main(["--raiz", str(raiz)]) == 1
    salida = capsys.readouterr().out
    assert "skips nuevos" in salida


def test_medir_registra_recuentos_y_tiempo(tmp_path, capsys):
    raiz = _arbol(tmp_path)
    gate = _cargar_gate()
    evidencia = tmp_path / "ev.json"
    codigo = gate.main(["--raiz", str(raiz), "--medir", "--suite", "unit",
                        "--json", str(evidencia)])
    assert codigo == 0, capsys.readouterr().out
    datos = json.loads(evidencia.read_text(encoding="utf-8"))
    assert datos["resultado"] == "PASS"
    assert datos["medido"]["unit"]["passed"] == 2
    assert datos["medido"]["unit"]["skipped"] == 0
    assert datos["medido"]["unit"]["duracion_s"] >= 0
