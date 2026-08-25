# -*- coding: utf-8 -*-
"""
Tests de cobertura para compilador/parser.py — M2 §12 (100% cobertura).

Metodo TDD: cada test es la especificacion del Manual 2, S12.
"""
import pytest
from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.diagnostics import DiagnosticManager
from compilador.ast_nodes import (
    SentenciaExpr, ExprRecibirCanal, SentenciaEnviarCanal,
    DeclaracionTipo,
)

pytestmark = pytest.mark.unit


def _parsear(fuente: str):
    lexer = Lexer(fuente)
    tokens = lexer.tokenizar()
    diag = DiagnosticManager()
    parser = Parser(tokens, diag)
    prog = parser.parsear()
    return prog, diag


def _funcion(prog, nombre: str):
    for s in prog.sentencias:
        if hasattr(s, 'nombre') and s.nombre == nombre:
            return s
    raise AssertionError("funcion '%s' no encontrada" % nombre)


class TestParserCoberturaExtra:
    """Tests para lograr 100% cobertura de compilador/parser.py."""

    # --- Lineas 103-105: ch -> como expression statement (receive) ---
    def test_receive_canal_standalone(self):
        """Manual 5 S4.2: 'ch ->' como statement independiente."""
        fuente = "#lang: es\nfuncion f() -> nulo:\n    ch = canal(entero, 4)\n    ch ->\n"
        prog, diag = _parsear(fuente)
        f = _funcion(prog, 'f')
        expr_stmts = [s for s in f.cuerpo if isinstance(s, SentenciaExpr)
                      and isinstance(s.expr, ExprRecibirCanal)]
        assert len(expr_stmts) >= 1

    # --- Linea 229: tipo sin nombre -> _esperar returns None ---
    def test_tipo_nombre_fallido(self):
        """Linea 229: _esperar_identificador retorna None en tipo declaration."""
        # tipo <NUMBER> = ... -> el token despues de '<' no es identificador
        prog, diag = _parsear("#lang: es\ntipo < 3 = entero\n")
        # El parser debe manejar el error sin crash

    # --- Lineas 232-233: tipo con error de sync ---
    def test_tipo_sync_error(self):
        """Lineas 232-233: _sincronizar + return None en tipo declaration."""
        prog, diag = _parsear("#lang: es\ntipo < = entero\n")
        # El parser debe manejar el error sin crash

    # --- Lineas 353, 358: _parsear_enviar_canal con CANAL keyword ---
    def test_enviar_canal_con_keyword_canal(self):
        """Lineas 353, 358: 'canal' keyword como variable en enviar canal."""
        fuente = "#lang: es\nfuncion f() -> nulo:\n    canal <- 42\n"
        prog, diag = _parsear(fuente)
        # El parser debe manejar este caso sin crash

    # --- Lineas 370, 375: _parsear_recibir_canal defensivo ---
    def test_recibir_canal_defensivo(self):
        """Lineas 370, 375: receive canal defensivo."""
        fuente = "#lang: es\nfuncion f() -> nulo:\n    ch ->\n"
        prog, diag = _parsear(fuente)
        f = _funcion(prog, 'f')
        expr_stmts = [s for s in f.cuerpo if isinstance(s, SentenciaExpr)
                      and isinstance(s.expr, ExprRecibirCanal)]
        assert len(expr_stmts) >= 1
