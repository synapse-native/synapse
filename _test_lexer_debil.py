"""Test lexer S1 con debil."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from compilador.lexer import Lexer

# Test without accent (debil)
texto1 = "#lang: es\nfuncion f() -> nulo:\n    let x = 5\n    retornar"
lex1 = Lexer(texto1)
toks1 = lex1.tokenizar()
print("Test 1 (no accent):", len(toks1), "tokens")

# Test with accent (débil)
texto2 = "#lang: es\nfuncion f() -> nulo:\n    let ref: débil<int> = nulo\n    retornar"
lex2 = Lexer(texto2)
try:
    toks2 = lex2.tokenizar()
    print("Test 2 (with accent):", len(toks2), "tokens")
    for t in toks2[:15]:
        print(f"  {t.tipo}: {repr(t.lexema)}")
except Exception as e:
    print("Test 2 Error:", e)
