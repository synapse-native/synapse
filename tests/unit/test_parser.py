from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.ast_nodes import (
    SentenciaSi, AsignacionVariable,
    OpBinaria, OpUnaria,
)
from compilador.diagnostics import DiagnosticManager


def _parsear(fuente: str):
    lexer = Lexer(fuente)
    tokens = lexer.tokenizar()
    diag = DiagnosticManager()
    parser = Parser(tokens, diag)
    prog = parser.parsear()
    return prog, diag


class TestParserOperadoresFase0:
    def test_comparacion_menor_igual(self):
        prog, diag = _parsear("#lang: es\nx = 1 <= 2")
        assert not diag.hay_errores()
        assign = prog.sentencias[0]
        assert isinstance(assign, AsignacionVariable)
        assert isinstance(assign.expresion, OpBinaria)
        assert assign.expresion.operador == "<="

    def test_comparacion_mayor_igual(self):
        prog, diag = _parsear("#lang: es\nx = 1 >= 2")
        assert not diag.hay_errores()
        assign = prog.sentencias[0]
        assert isinstance(assign.expresion, OpBinaria)
        assert assign.expresion.operador == ">="

    def test_comparacion_distinto(self):
        prog, diag = _parsear("#lang: es\nx = 1 != 2")
        assert not diag.hay_errores()
        assign = prog.sentencias[0]
        assert isinstance(assign.expresion, OpBinaria)
        assert assign.expresion.operador == "!="

    def test_igualdad_vs_asignacion(self):
        prog_asign, _ = _parsear("#lang: es\nx = 10")
        assign = prog_asign.sentencias[0]
        assert isinstance(assign, AsignacionVariable)

        prog_igual, _ = _parsear("#lang: es\nx = 10 == 10")
        assign2 = prog_igual.sentencias[0]
        assert isinstance(assign2, AsignacionVariable)
        assert isinstance(assign2.expresion, OpBinaria)
        assert assign2.expresion.operador == "=="

    def test_unario_menos(self):
        prog, diag = _parsear("#lang: es\nx = -a")
        assert not diag.hay_errores()
        assign = prog.sentencias[0]
        assert isinstance(assign, AsignacionVariable)
        assert isinstance(assign.expresion, OpUnaria)
        assert assign.expresion.operador == "-"

    def test_punto_y_coma_separador(self):
        prog, diag = _parsear("#lang: es\nfuncion f() -> nulo:\n    a=10; b=20")
        assert not diag.hay_errores()

    def test_si_inline_operadores(self):
        prog, diag = _parsear("#lang: es\nsi a<=b: escribir_linea(\"OK\")")
        assert not diag.hay_errores()
        assert isinstance(prog.sentencias[0], SentenciaSi)

    def test_cadena_comparacion(self):
        prog, diag = _parsear("#lang: es\nx = -a==-10")
        assert not diag.hay_errores()
        assign = prog.sentencias[0]
        assert isinstance(assign, AsignacionVariable)
        assert isinstance(assign.expresion, OpBinaria)
        assert assign.expresion.operador == "=="
        izq = assign.expresion.izquierdo
        assert isinstance(izq, OpUnaria)
        assert izq.operador == "-"
