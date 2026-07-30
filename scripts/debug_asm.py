#!/usr/bin/env python3
"""Debug script: trace asm() parsing for principal.syn"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Tokenize ONE specific asm line from principal.syn
asm_line = '        asm("    if(strcmp(t,\\"SentenciaRetornar\\")==0) return 5;")'

from compilador.lexer import Lexer
from compilador.ast_nodes import TokenID

# Create a full valid Synapse program with this line
test_src = """#lang: es
funcion foo() -> nulo:
    inseguro:
""" + asm_line + """
        asm("ok")
"""

print("=== FULL TEST SOURCE ===")
for i, line in enumerate(test_src.split('\n'), 1):
    print(f"{i:4d}: {line}")

print("\n=== LEXER TOKENS ===")
lexer = Lexer(test_src)
tokens = lexer.tokenizar()
for t in tokens:
    print(f"  {t}")

print("\n=== PARSER AST ===")
from compilador.parser import Parser
from compilador.diagnostics import DiagnosticManager
from compilador.ast_nodes import ExprAsm, LiteralCadena

diag = DiagnosticManager()
parser = Parser(tokens, diag)
ast = parser.parsear()

if diag.hay_errores():
    print(f"\n!!! PARSER ERRORS: {diag.resumen()}")
    for err in diag.errores:
        print(f"  ERROR: {err}")

print(f"\nAST statements: {len(ast.sentencias)}")
for s in ast.sentencias:
    print(f"  {type(s).__name__}")
    # Look inside for asm expressions
    if hasattr(s, 'cuerpo'):
        for stmt in s.cuerpo:
            print(f"    {type(stmt).__name__}")
            if hasattr(stmt, 'expr'):
                expr = stmt.expr
                print(f"      EXPR: {type(expr).__name__}")
                if isinstance(expr, ExprAsm):
                    print(f"        instruccion: {expr.instruccion!r}")
                    print(f"        expr: {expr.expr!r}")
                if isinstance(expr, LiteralCadena):
                    print(f"        valor: {expr.valor!r}")
