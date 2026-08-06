"""Probe A2.1b: verifica que 'let r: puntero = 0' emite void* r y que el struct
LexerBuffers con campos puntero no trunca los punteros (64-bit)."""
import io
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import compilar_desde_texto  # noqa: E402
from compilador.generator import GeneradorC  # noqa: E402

prueba = """#lang: es

estructura LexerBuffers:
    tokens: puntero
    sbuf: puntero
    str_pos: entero
    ntks: entero

funcion lexer_buffers() -> puntero:
    inseguro:
        let r: puntero = 0
        asm("static struct TokenLex _X_tks[1024];")
        asm("r = (void*)&_X_tks;")
        retornar r

funcion usar() -> entero:
    inseguro:
        let p: puntero = 0
        asm("p = lexer_buffers();")
        asm("((struct LexerBuffers*)p)->ntks = 7;")
        r = 0
        asm("r = ((struct LexerBuffers*)p)->ntks;")
        retornar r
"""

tmp = tempfile.mkdtemp(prefix="a21ptr_")
p = os.path.join(tmp, "t.syn")
io.open(p, "w", encoding="utf-8").write(prueba)
ast, diag = compilar_desde_texto(p, set())
print("errores:", diag.hay_errores())
if diag.hay_errores():
    print(diag)
else:
    c = GeneradorC(ast).generar()
    for i, ln in enumerate(c.split(chr(10))):
        if "LexerBuffers" in ln or "lexer_buffers" in ln or "_X_tks" in ln or "void* usar" in ln or "void* lexer_buffers" in ln:
            print(i, ln[:120])
