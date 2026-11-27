# -*- coding: utf-8 -*-
"""Oráculos de auditoria/verificar_manuales.py (Manual 2 §1.2, Manual 1 §7.4)."""
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUTA = RAIZ / "auditoria" / "verificar_manuales.py"


def _cargar():
    spec = importlib.util.spec_from_file_location("verificar_manuales", RUTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _manual(num, extra=""):
    return (
        f"# MANUAL {num}: PRUEBA\n\n"
        f"## 1. UNO\n\n"
        f"### 1.1. UNO UNO\n\n"
        f"Todos los archivos fuente deben estar en UTF-8 sin BOM. {extra}\n"
    )


def _fixture(tmp_path):
    base = tmp_path / "docs" / "manuales"
    base.mkdir(parents=True)
    (base / "MANUAL 1.md").write_text(_manual(1), encoding="utf-8")
    for nombre in _cargar().im.ALIAS_MANUALES.values():
        (base / nombre).write_text("# MANUAL TEMPORAL\n\n## 1. UNO\n", encoding="utf-8")
    for nombre in _cargar().im.ANEXOS.values():
        (base / nombre).write_text("# ANEXO\n\n## 1. UNO\n", encoding="utf-8")
    modulo = _cargar()
    indice = modulo.im.construir_indice(base, tmp_path)
    modulo.im.guardar_indice(indice, base / ".indice.json")
    return base, modulo


def test_todo_limpio_pasa(tmp_path, capsys):
    _fixture(tmp_path)
    modulo = _cargar()
    assert modulo.main(["--todo", "--root", str(tmp_path)]) == 0
    assert "verificados" in capsys.readouterr().out


def test_bom_falla(tmp_path, capsys):
    base, modulo = _fixture(tmp_path)
    ruta = base / "MANUAL 1.md"
    ruta.write_bytes(b"\xef\xbb\xbf" + ruta.read_bytes())
    assert modulo.main(["--encoding", "--root", str(tmp_path)]) == 1
    assert "BOM" in capsys.readouterr().out


def test_u_fffd_y_c1_fallan(tmp_path, capsys):
    base, modulo = _fixture(tmp_path)
    (base / "MANUAL 1.md").write_text(
        "# MANUAL 1\n\n## 1. UNO\n\n" + "\ufffd" + "\x80" + "\n",
        encoding="utf-8")
    assert modulo.main(["--encoding", "--root", str(tmp_path)]) == 1
    salida = capsys.readouterr().out
    assert "U+FFFD" in salida
    assert "C1" in salida


def test_nombre_no_canonico_falla(tmp_path, capsys):
    base, modulo = _fixture(tmp_path)
    (base / "MANUAL  X.md").write_text("# X\n", encoding="utf-8")
    assert modulo.main(["--nombres", "--root", str(tmp_path)]) == 1
    assert "nombre no canonico" in capsys.readouterr().out


def test_indice_desactualizado_falla(tmp_path, capsys):
    base, modulo = _fixture(tmp_path)
    (base / "MANUAL 1.md").write_text(_manual(1, "Cambio."), encoding="utf-8")
    assert modulo.main(["--indice", "--root", str(tmp_path)]) == 1
    assert "sha256 desactualizado" in capsys.readouterr().out


def test_cita_rota_falla(tmp_path, capsys):
    _fixture(tmp_path)
    nucleo = tmp_path / "nucleo"
    nucleo.mkdir()
    (nucleo / "x.syn").write_text(
        "#lang: es\n// cumple Manual 1 §9.9\n", encoding="utf-8")
    modulo = _cargar()
    assert modulo.main(["--citas", "--root", str(tmp_path)]) == 1
    assert "cita rota" in capsys.readouterr().out


def test_cita_valida_pasa(tmp_path, capsys):
    _fixture(tmp_path)
    nucleo = tmp_path / "nucleo"
    nucleo.mkdir()
    (nucleo / "x.syn").write_text(
        "#lang: es\n// cumple Manual 1 §1.1\n", encoding="utf-8")
    modulo = _cargar()
    assert modulo.main(["--citas", "--root", str(tmp_path)]) == 0
    assert "OK" in capsys.readouterr().out
