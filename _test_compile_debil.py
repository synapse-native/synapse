"""Test compilar_desde_texto con débil."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from pipeline import compilar_desde_texto
import tempfile, os

src = """#lang: es

funcion principal() -> nulo:
    let ref: débil<int> = nulo
    retornar
"""

with tempfile.TemporaryDirectory() as tmp:
    path = os.path.join(tmp, "p.syn")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    
    ast, diag = compilar_desde_texto(path, set())
    print("Errors:", diag.hay_errores())
    if diag.hay_errores():
        for e in diag.errores:
            print("  ERR:", e)
