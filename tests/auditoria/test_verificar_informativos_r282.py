# -*- coding: utf-8 -*-
"""Oraculos r282: cabecera, mapa canonico y enlaces de docs/book2-desarrollo."""
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUTA = RAIZ / "auditoria" / "verificar_manuales.py"
CABECERA = "> Documento informativo. La fuente de verdad es `docs/manuales/`."


def _cargar():
    spec = importlib.util.spec_from_file_location("verificar_manuales_r282", RUTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _fixture(tmp_path, con_cabecera=True, con_mapa=True, extra=""):
    docs = tmp_path / "docs"
    manuales = docs / "manuales"
    manuales.mkdir(parents=True)
    (manuales / "MANUAL 1.md").write_text(
        "# MANUAL 1\n\n## 1. UNO\n", encoding="utf-8")
    book = docs / "book2-desarrollo"
    book.mkdir()
    lineas = []
    if con_cabecera:
        lineas.append(CABECERA)
    if con_mapa:
        lineas.append(
            "> **Mapa canónico:** [MANUAL 1](../manuales/MANUAL 1.md) §1.")
    lineas.extend([
        "",
        "# Documento",
        "",
        "[Manual 1](../manuales/MANUAL 1.md)",
        extra,
    ])
    (book / "ok.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return tmp_path, _cargar()


def test_book2_limpio_pasa(tmp_path, capsys):
    root, modulo = _fixture(tmp_path)
    assert modulo.main(["--informativos", "--root", str(root)]) == 0
    assert "OK" in capsys.readouterr().out


def test_falta_cabecera_falla(tmp_path, capsys):
    root, modulo = _fixture(tmp_path, con_cabecera=False)
    assert modulo.main(["--informativos", "--root", str(root)]) == 1
    assert "cabecera" in capsys.readouterr().out


def test_falta_mapa_falla(tmp_path, capsys):
    root, modulo = _fixture(tmp_path, con_mapa=False)
    assert modulo.main(["--informativos", "--root", str(root)]) == 1
    assert "Mapa canónico" in capsys.readouterr().out


def test_enlace_roto_falla(tmp_path, capsys):
    root, modulo = _fixture(tmp_path, extra="[roto](no-existe.md)")
    assert modulo.main(["--informativos", "--root", str(root)]) == 1
    assert "enlace roto" in capsys.readouterr().out


def test_enlace_externo_pasa(tmp_path, capsys):
    root, modulo = _fixture(tmp_path, extra="[web](https://example.com)")
    assert modulo.main(["--informativos", "--root", str(root)]) == 0
    assert "OK" in capsys.readouterr().out


def test_contradiccion_conocida_falla(tmp_path, capsys):
    root, modulo = _fixture(tmp_path, extra="Los 9 manuales oficiales")
    assert modulo.main(["--informativos", "--root", str(root)]) == 1
    assert "contradicción" in capsys.readouterr().out


def test_docs_incluye_informativos(tmp_path, capsys):
    root, modulo = _fixture(tmp_path, con_cabecera=False)
    assert modulo.main(["--docs", "--root", str(root)]) == 1
    assert "cabecera" in capsys.readouterr().out


def test_fuera_de_book2_no_aplica(tmp_path, capsys):
    root, modulo = _fixture(tmp_path)
    (root / "docs" / "otro.md").write_text("# Otro\n", encoding="utf-8")
    assert modulo.main(["--informativos", "--root", str(root)]) == 0
    assert "OK" in capsys.readouterr().out
