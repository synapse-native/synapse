"""Probe A2.1: comprueba si S1 acepta 'let' a nivel de modulo y como lo emite."""
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import compilar_desde_texto  # noqa: E402
from compilador.generator import GeneradorC  # noqa: E402

prueba = """#lang: es

let _N_global = 42

funcion obtener() -> entero:
    retornar _N_global
"""

tmp = tempfile.mkdtemp(prefix="a21let_")
p = os.path.join(tmp, "t.syn")
io.open(p, "w", encoding="utf-8").write(prueba)
ast, diag = compilar_desde_texto(p, set())
print("errores:", diag.hay_errores())
if diag.hay_errores():
    print(diag)
else:
    c = GeneradorC(ast).generar()
    print("C contiene _N_global file-scope:")
    for i, ln in enumerate(c.split(chr(10))):
        if "_N_global" in ln:
            print(" ", i, ln[:110])
