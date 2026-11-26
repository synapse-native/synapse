# -*- coding: utf-8 -*-
"""Oráculo r331: el LSP nativo compila con una única definición pública de
`cmp_texto` (Manual 2 §5.1, Manual 8 §1.7.3). Regresión de 8a2f82b: el
envoltorio se eliminó creyéndolo duplicado y lsp_v3.syn quedó con 80 usos
de un símbolo inexistente.
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def test_lsp_v3_compila_sin_cmp_texto_indefinida():
    r = subprocess.run(
        [sys.executable, str(RAIZ / "main.py"),
         str(RAIZ / "nucleo" / "lsp_v3.syn"), "--check", "--no-emit"],
        cwd=str(RAIZ), capture_output=True, text=True, timeout=120)
    salida = (r.stdout or "") + (r.stderr or "")
    assert r.returncode == 0, salida[-2000:]
    assert "cmp_texto' no definida" not in salida


def test_cmp_texto_tiene_una_sola_definicion_publica():
    texto = (RAIZ / "std" / "texto.syn").read_text(encoding="utf-8")
    assert texto.count("funcion cmp_texto(") == 1
    assert "retornar _syn_strcmp(a, b)" in texto
