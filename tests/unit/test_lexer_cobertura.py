# -*- coding: utf-8 -*-
"""
Tests de cobertura para compilador/lexer.py — M2 §12 (>95% cobertura).
"""
import pytest
from compilador.lexer import Lexer, TokenID
from exceptions import SynapseError


class TestLexerCoberturaExtra:
    """Tests para lineas del lexer sin cobertura segun M2 §12 (>95%)."""

    def test_externo_funcion_no_invalida_cabecera(self):
        """Linea 364: 'externo funcion' no debe invalidar la cabecera."""
        fuente = "#lang: es\nexterno funcion strlen(s: &texto) -> entero\n"
        tokens = Lexer(fuente).tokenizar()
        tipos = [t.tipo for t in tokens]
        assert TokenID.EXTERNO in tipos
        assert TokenID.FUNCION in tipos

    def test_funcion_con_dos_puntos_sin_body(self):
        """Lineas 386-398: funcion con ':' pero sin bloque indentado."""
        fuente = "#lang: es\nfuncion incompleta():\n\n"
        with pytest.raises(SynapseError) as exc:
            Lexer(fuente).tokenizar()
        assert "sin cuerpo" in exc.value.mensaje

    def test_cadena_escape_unicode(self):
        """Lineas 492-523: escape Unicode en cadenas."""
        bs = chr(92)
        fuente = '#lang: es\nx = "hello' + bs + 'u0041"\n'
        tokens = Lexer(fuente).tokenizar()
        strs = [t for t in tokens if t.tipo == TokenID.STRING]
        assert strs and "helloA" in strs[0].valor

    def test_cadena_escape_unicode_incompleto(self):
        """Linea 510-514: escape Unicode incompleto debe lanzar error."""
        bs = chr(92)
        fuente = '#lang: es\nx = "hello' + bs + 'u004"\n'
        with pytest.raises(SynapseError) as exc:
            Lexer(fuente).tokenizar()
        assert "Unicode incompleto" in exc.value.mensaje

    def test_numero_notacion_cientifica(self):
        """Lineas 593-598: notacion cientifica 1e3, 1.5E+2."""
        fuente = "#lang: es\nx = 1e3\ny = 1.5E+2\n"
        tokens = Lexer(fuente).tokenizar()
        floats = [t for t in tokens if t.tipo == TokenID.FLOAT]
        assert len(floats) == 2
        assert floats[0].valor == 1000.0
        assert floats[1].valor == 150.0

    def test_dedent_al_final(self):
        """Linea 337: dedent automatico al final de archivo con indentacion."""
        fuente = "#lang: es\nfuncion f() -> nulo:\n    x = 1\n"
        tokens = Lexer(fuente).tokenizar()
        tipos = [t.tipo for t in tokens]
        assert tipos.count(TokenID.DEDENT) >= 1
