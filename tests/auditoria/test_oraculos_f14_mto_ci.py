"""
Oraculos del ME f14_mto_ci — incremento del lote en vuelo (2026-10-14).

Frentes verificados (plan docs/plan_ME_f14_mto_ci.md):
  R1 lexer/parser F1.4: firma sin cuerpo -> rc=1 por GRAMATICA del PARSER
     (Manual 2 §2 L56: ':' NEWLINE INDENT bloque DEDENT obligatorio) y archivo
     vacío -> mismo mensaje de familia sin-#lang.
  R6 paridad embebida: 'let y = 1' se parsea igual en nativo y _P_* ( Manual 1
     §3.1 mismo AST canónico) — lo cubre native_puente_paridad.py (no aquí).
  R4 fixtures canónicos: discriminator "tipo" == nombre de nodo (Manual 2 §13).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent.parent
PY = sys.executable

_probe_dir = None


@pytest.fixture(scope="module")
def tmp_probe(tmp_path_factory):
    return tmp_path_factory.mktemp("f14_mto_ci")


def _correr(fuente: str, tmp):
    path = tmp / "probe.sin"
    path.write_text(fuente, encoding="utf-8")
    rc = subprocess.call(
        [PY, str(RAIZ / "main.py"), str(path), "-o", str(tmp / "probe.out.c")],
        cwd=str(RAIZ), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return rc


def test_r1_firma_sin_cuerpo_rc1(tmp_probe):
    """Manual 2 §2 L56 (H-F1.4-1): funcion sin bloque indentado -> rc=1."""
    fuente = "#lang: es\nfuncion incompleta():\n\n"
    assert _correr(fuente, tmp_probe) == 1


def test_r1_funcion_valida_rc0(tmp_probe):
    """La misma funcion con cuerpo obligatorio compila rc=0 (no sobre-aspira)."""
    fuente = "#lang: es\nfuncion bien():\n    retornar\n"
    assert _correr(fuente, tmp_probe) == 0


def test_r1_archivo_vacio_mensaje_familia(tmp_probe):
    """F1.4: archivo vacio -> familia del error sin-#lang ('declaracion de idioma')."""
    vacio = tmp_probe / "vacio.syn"
    vacio.write_text("", encoding="utf-8")
    cp = subprocess.run(
        [PY, str(RAIZ / "main.py"), str(vacio), "-o", str(tmp_probe / "nope.c")],
        capture_output=True, text=True, cwd=str(RAIZ), timeout=120,
    )
    salida = (cp.stdout + cp.stderr).lower()
    assert cp.returncode != 0
    assert "declarac" in salida  # familia: 'falta declaracion de idioma #lang'


def test_r4_fixtures_tipo_discriminante():
    """Manual 2 §13/H-canon-LET: los fixtures vigentes usan 'tipo' (nodo) y la
    lista del Programa es 'declaraciones'."""
    fx = RAIZ / "tests" / "fixtures" / "valid" / "empty.expected.json"
    data = json.loads(fx.read_text(encoding="utf-8"))
    assert data["tipo"] == "Programa"
    assert data["declaraciones"] == []
