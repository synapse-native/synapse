"""Check if analizador_semantico.syn parses correctly."""
import sys
sys.path.insert(0, r"D:\proyecto_synapse")

with open(r"D:\proyecto_synapse\src\analizador_semantico.syn") as f:
    src = f.read()

from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.diagnostics import DiagnosticManager

diag = DiagnosticManager(fuente_lineas=src.split('\n'))
lex = Lexer(src)
toks = lex.tokenizar()
print(f"Tokens: {len(toks)}")

par = Parser(toks, diag)
ast = par.parsear()
print(f"Statements: {len(ast.sentencias)}")

for s in ast.sentencias:
    name = getattr(s, "nombre", getattr(s, "tipo", "?"))
    print(f"  {type(s).__name__}: {name}")

if diag.hay_errores():
    print(f"Errors: {len(diag.errores)}")
    for e in diag.errores:
        print(f"  {e}")
else:
    print("OK - no errors")
