import pytest
from compilador.lexer import Lexer, DICCIONARIOS, TOKEN_UNICARACTER, TOKEN_BICARACTER
from compilador.ast_nodes import TokenID, Token
from exceptions import SynapseError


class TestLexerOperadoresFase0:
    def test_menor_igual(self):
        lexer = Lexer("#lang: es\nx = 1 <= 2")
        tokens = lexer.tokenizar()
        assert TokenID.LESS_EQUALS in [t.tipo for t in tokens]

    def test_mayor_igual(self):
        lexer = Lexer("#lang: es\nx = 1 >= 2")
        tokens = lexer.tokenizar()
        assert TokenID.GREATER_EQUALS in [t.tipo for t in tokens]

    def test_distinto(self):
        lexer = Lexer("#lang: es\nx = 1 != 2")
        tokens = lexer.tokenizar()
        assert TokenID.NOT_EQUALS in [t.tipo for t in tokens]

    def test_asignacion_simple(self):
        lexer = Lexer("#lang: es\nx = 10")
        tokens = lexer.tokenizar()
        assert TokenID.ASSIGN in [t.tipo for t in tokens]
        assert TokenID.EQUALS not in [t.tipo for t in tokens]

    def test_igualdad(self):
        lexer = Lexer("#lang: es\nx == 10")
        tokens = lexer.tokenizar()
        assert TokenID.EQUALS in [t.tipo for t in tokens]
        assert TokenID.ASSIGN not in [t.tipo for t in tokens]

    def test_unario_menos(self):
        lexer = Lexer("#lang: es\nx = -5")
        tokens = lexer.tokenizar()
        assert TokenID.MINUS in [t.tipo for t in tokens]

    def test_punto_y_coma(self):
        lexer = Lexer("#lang: es\na=10; b=20")
        tokens = lexer.tokenizar()
        semicolon_count = sum(1 for t in tokens if t.tipo == TokenID.SEMICOLON)
        assert semicolon_count == 1

    def test_unario_not(self):
        lexer = Lexer("#lang: es\nx = !verdadero")
        tokens = lexer.tokenizar()
        assert TokenID.NOT in [t.tipo for t in tokens]

    def test_comparacion_mixta(self):
        lexer = Lexer("#lang: es\nsi a<=b y a!=b:")
        tokens = lexer.tokenizar()
        assert TokenID.LESS_EQUALS in [t.tipo for t in tokens]
        assert TokenID.NOT_EQUALS in [t.tipo for t in tokens]
        assert TokenID.AND in [t.tipo for t in tokens]
