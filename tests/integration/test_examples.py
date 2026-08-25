import os
import glob

import pytest

pytestmark = pytest.mark.integration

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _ejecutar_compilador(path_syn: str) -> str:
    from compilador.lexer import Lexer
    from compilador.parser import Parser
    from compilador.diagnostics import DiagnosticManager
    from compilador.analizador_semantico import AnalizadorSemantico
    from compilador.generator import GeneradorC

    with open(path_syn, "r", encoding="utf-8") as f:
        codigo = f.read()

    fuente_lineas = codigo.split("\n")
    diag = DiagnosticManager(fuente_lineas=fuente_lineas, ruta_archivo=path_syn)

    lexer = Lexer(codigo)
    tokens = lexer.tokenizar()
    parser = Parser(tokens, diag)
    ast = parser.parsear()

    for e in diag.errores:
        cod = e.get("codigo", "")
        if hasattr(cod, "name"):
            cod = cod.name
        if cod.startswith("ERR_LEX") or cod.startswith("ERR_SYNTAX"):
            assert False, f"Errores lex/syntax en {path_syn}: {e}"

    analizador = AnalizadorSemantico(ast, diag)
    analizador.analizar()
    for e in diag.errores:
        cod = e.get("codigo", "")
        if hasattr(cod, "name"):
            cod = cod.name
        if cod.startswith("ERR_SEM"):
            assert False, f"Errores semanticos en {path_syn}: {e}"

    generador = GeneradorC(ast)
    codigo_c = generador.generar()
    assert len(codigo_c) > 0, f"Codigo C vacio para {path_syn}"

    return codigo_c


def _descubrir_ejemplos():
    examples_dir = os.path.join(ROOT, "examples")
    return sorted(glob.glob(os.path.join(examples_dir, "**", "*.syn"), recursive=True))


@pytest.mark.parametrize("ruta_syn", _descubrir_ejemplos())
def test_ejemplo_compila(ruta_syn):
    codigo_c = _ejecutar_compilador(ruta_syn)
    assert codigo_c is not None
    assert len(codigo_c.strip()) > 0
