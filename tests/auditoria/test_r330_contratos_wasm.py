# -*- coding: utf-8 -*-
"""r330_contratos_wasm — validez del módulo y contratos de las 83 funciones.

Antes de este ME el módulo no lexaba (`#` como comentario) y el test de
backend ignoraba los errores del pipeline; por eso la deuda de contratos se
medía sobre código no compilable. Estos casos fallan si el módulo deja de
compilar o pierde un contrato.
"""
import re
import subprocess
import sys
from pathlib import Path

from compilador.analizador_semantico import AnalizadorSemantico
from compilador.diagnostics import DiagnosticManager
from compilador.generator import GeneradorC
from compilador.lexer import Lexer
from compilador.parser import Parser

RAIZ = Path(__file__).resolve().parents[2]
FUENTE = RAIZ / "nucleo" / "wasm_backend.syn"


def _texto() -> str:
    return FUENTE.read_text(encoding="utf-8")


def _analizar():
    diag = DiagnosticManager()
    prog = Parser(Lexer(_texto()).tokenizar(), diag).parsear()
    assert not diag.hay_errores(), [e.get("mensaje") for e in diag.errores]
    AnalizadorSemantico(prog, diag).analizar()
    assert not diag.hay_errores(), [e.get("mensaje") for e in diag.errores]
    return prog


def test_modulo_lexa_parsea_y_analiza_sin_errores():
    _analizar()


def test_generador_emite_las_83_aseraciones_de_contrato():
    codigo = GeneradorC(_analizar()).generar()
    assert codigo.count("assert_contrato") >= 83


def test_83_funciones_con_ambos_contratos():
    texto = _texto()
    assert len(re.findall(r"^funcion\s+\w+\s*\(", texto, re.M)) == 83
    assert texto.count("    requiere:") == 83
    assert texto.count("    garantiza:") == 83


def test_sin_comentarios_invalidos():
    lineas = _texto().splitlines()
    assert lineas[0].startswith("#lang:")
    invalidas = [i + 1 for i, linea in enumerate(lineas) if i and "#" in linea]
    assert not invalidas, f"'#' fuera de #lang en líneas {invalidas[:5]}"


def test_firmas_sin_contratos_dentro_de_parametros():
    texto = _texto()
    for m in re.finditer(r"^funcion\s+(\w+)\s*\(", texto, re.M):
        cierre = texto.find("->", m.start())
        assert "garantiza:" not in texto[m.start():cierre], m.group(1)


def test_sin_codigo_muerto_nuevo():
    r = subprocess.run(
        [sys.executable, str(RAIZ / "auditoria" / "verificar_codigo_muerto.py")],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_ratchet_de_contratos_sin_deuda_para_wasm():
    r = subprocess.run(
        [sys.executable, str(RAIZ / "auditoria" / "verificar_contratos.py")],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    baseline = (RAIZ / "auditoria" / "contratos_baseline.txt").read_text(encoding="utf-8")
    assert "nucleo/wasm_backend.syn::" not in baseline
