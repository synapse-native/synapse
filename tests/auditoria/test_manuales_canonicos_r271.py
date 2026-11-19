# -*- coding: utf-8 -*-
"""Oráculos de D-MAN-1/2: Manual 31/32 canónicos y anexos de apoyo (r271)."""
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUTA = RAIZ / "auditoria" / "verificar_manuales.py"


def _cargar():
    spec = importlib.util.spec_from_file_location("verificar_manuales_r271", RUTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _manual(num):
    return f"# MANUAL {num}: PRUEBA\n\n## 1. UNO\n\n### 1.1. UNO UNO\n\nDebe cumplirse.\n"


def _fixture(tmp_path):
    base = tmp_path / "docs" / "manuales"
    base.mkdir(parents=True)
    for num in (1, 31, 32):
        (base / f"MANUAL {num}.md").write_text(_manual(num), encoding="utf-8")
    for nombre in _cargar().im.ANEXOS.values():
        (base / nombre).write_text("# ANEXO\n\n## 1. UNO\n", encoding="utf-8")
    modulo = _cargar()
    indice = modulo.im.construir_indice(base, tmp_path)
    modulo.im.guardar_indice(indice, base / ".indice.json")
    return base, modulo


def test_nombres_canonicos_31_32_pasan(tmp_path, capsys):
    _fixture(tmp_path)
    modulo = _cargar()
    assert modulo.main(["--nombres", "--root", str(tmp_path)]) == 0
    salida = capsys.readouterr().out
    assert "alias historico" not in salida


def test_indice_canonico_conserva_alias_historico(tmp_path):
    _fixture(tmp_path)
    modulo = _cargar()
    indice = modulo.im.cargar_indice(
        tmp_path / "docs" / "manuales" / ".indice.json",
        tmp_path / "docs" / "manuales",
        tmp_path,
    )
    for num in ("31", "32"):
        entrada = indice["manuales"][num]
        assert entrada["archivo"] == f"docs/manuales/MANUAL {num}.md"
        assert entrada.get("alias")
        assert "MANUAL  FASE" in entrada["alias"][0]
