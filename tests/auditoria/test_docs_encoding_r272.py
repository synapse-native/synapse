# -*- coding: utf-8 -*-
"""Oráculos de r272: encoding documental y cabecera informativa."""
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUTA = RAIZ / "auditoria" / "verificar_manuales.py"
CABECERA = "> Documento informativo. La fuente de verdad es `docs/manuales/`."


def _cargar():
    spec = importlib.util.spec_from_file_location("verificar_manuales_r272", RUTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _sin_corrupcion(rel):
    modulo = _cargar()
    path = RAIZ / rel
    raw = path.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{rel}: BOM UTF-8"
    texto = raw.decode("utf-8")
    assert "\ufffd" not in texto, f"{rel}: U+FFFD"
    assert not any(0x80 <= ord(c) <= 0x9f for c in texto), f"{rel}: C1"
    assert not modulo.RE_MOJIBAKE.search(texto), f"{rel}: doble codificación"


def test_docs_encoding_global_sin_corrupcion():
    modulo = _cargar()
    assert modulo.verificar_encoding(RAIZ, docs=True) == []


def test_auditoria_conserva_contenido_y_cabecera():
    rel = "docs/auditorias/AUDITORIA_ALINEACION_MANUALES.md"
    _sin_corrupcion(rel)
    texto = (RAIZ / rel).read_text(encoding="utf-8")
    assert len(texto.splitlines()) >= 1275
    assert CABECERA in texto


def test_r205_cabecera_informativa():
    rel = "docs/reportes/R205.md"
    _sin_corrupcion(rel)
    texto = (RAIZ / rel).read_text(encoding="utf-8")
    assert CABECERA in texto
