# cumple Manual 8 §4.1: subcomandos del CLI unificado deben despacharse desde
# el binario sin romper el lexer (bloque observability envuelto en asm()).
"""Oráculo del ME r274_bootstrap_contracts.

Fija la regresión R274: el bloque del subcomando `observability` en
nucleo/principal.syn estaba como C crudo (sin `asm("...")`), lo que rompía el
lexer en la primera `\\` de `\\"observability\\"` y enmascaraba contratos
inválidos. Estos tests fallan si el bloque vuelve a quedar fuera de `asm()`.
"""

from pathlib import Path

from compilador.lexer import Lexer

RAIZ = Path(__file__).resolve().parents[2]
PRINCIPAL = RAIZ / "nucleo" / "principal.syn"


def test_observability_dispatch_usa_asm():
    fuente = PRINCIPAL.read_text(encoding="utf-8")
    lineas = [l for l in fuente.splitlines()
              if "observability" in l and "strcmp" in l]
    assert lineas, "no se encontró el despacho de 'observability' en principal.syn"
    for linea in lineas:
        assert "asm(" in linea, (
            "el despacho de observability debe ir dentro de asm(...): "
            f"{linea!r}"
        )


def test_principal_tokeniza_sin_error_lexico():
    fuente = PRINCIPAL.read_text(encoding="utf-8")
    tokens = Lexer(fuente).tokenizar()
    # Sanity: el compilador completo produce miles de tokens; si el lexer
    # abortara por un carácter inesperado, esta línea no se alcanzaría.
    assert len(tokens) > 1000, f"tokenización sospechosamente corta: {len(tokens)}"
