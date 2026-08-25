# -*- coding: utf-8 -*-
"""
Tests de cobertura para compilador/lexer.py — M2 §12 (100% cobertura).

Metodo TDD: cada test es la especificacion del Manual 2, S1 y S12.
"""
import pytest
from compilador.lexer import Lexer, TokenID
from exceptions import SynapseError

pytestmark = pytest.mark.unit


class TestLexerCoberturaExtra:
    """Tests para lograr 100% cobertura de compilador/lexer.py."""

    # --- Linea 337: BOM UTF-8 al inicio ---
    def test_bom_utf8_limpia(self):
        """M2 S1: archivos UTF-8 con BOM deben ser limpiados."""
        fuente = "\ufeff#lang: es\nx = 1\n"
        tokens = Lexer(fuente).tokenizar()
        assert any(t.tipo == TokenID.IDENTIFIER and t.valor == "x" for t in tokens)

    # --- Linea 364: 'externo funcion' skip en _validar_cuerpos ---
    def test_externo_funcion_no_invalida_cabecera(self):
        """M2 S2: 'externo funcion' no debe validarse como funcion con cuerpo."""
        fuente = "#lang: es\nexterno funcion strlen(s: &texto) -> entero\n"
        tokens = Lexer(fuente).tokenizar()
        tipos = [t.tipo for t in tokens]
        assert TokenID.EXTERNO in tipos
        assert TokenID.FUNCION in tipos

    # --- Lineas 386-390: firma sin LPAREN+RPAREN se deja al parser ---
    def test_funcion_firma_incompleta(self):
        """Linea 386-390: firma sin parentesis no se valida en lexer."""
        fuente = "#lang: es\nfuncion f -> nulo:\n    x = 1\n"
        tokens = Lexer(fuente).tokenizar()
        tipos = [t.tipo for t in tokens]
        assert TokenID.FUNCION in tipos

    # --- Lineas 392-398: ':' con tokens despues (no es cabecera) ---
    def test_funcion_dos_puntos_con_token_despues(self):
        """Lineas 392-398: tokens despues de ':' -> no es cabecera."""
        fuente = "#lang: es\nfuncion f(): algo\n"
        tokens = Lexer(fuente).tokenizar()
        tipos = [t.tipo for t in tokens]
        assert TokenID.FUNCION in tipos
        assert TokenID.IDENTIFIER in tipos

    # --- Lineas 406-408: funcion sin cuerpo ---
    def test_funcion_con_dos_puntos_sin_body(self):
        """Lineas 406-408: funcion con ':' pero sin bloque indentado."""
        fuente = "#lang: es\nfuncion incompleta():\n\n"
        with pytest.raises(SynapseError) as exc:
            Lexer(fuente).tokenizar()
        assert "sin cuerpo" in exc.value.mensaje

    # --- Linea 415: archivo vacio -> error ---
    def test_archivo_vacio_error(self):
        """M2 S1: archivo vacio debe ser rechazado con error."""
        with pytest.raises(SynapseError) as exc:
            Lexer("").tokenizar()
        assert "vacío" in exc.value.mensaje.lower() or "vacio" in exc.value.mensaje.lower()

    # --- Linea 490: escape \t ---
    def test_cadena_escape_tab(self):
        """Linea 490: escape \\t en cadena produce tabulacion."""
        bs = chr(92)
        fuente = '#lang: es\nx = "hola' + bs + 'tmundo"\n'
        tokens = Lexer(fuente).tokenizar()
        strs = [t for t in tokens if t.tipo == TokenID.STRING]
        assert strs and "\t" in strs[0].valor

    # --- Linea 492: escape \r ---
    def test_cadena_escape_retorno_carro(self):
        """Linea 492: escape \\r en cadena produce retorno de carro."""
        bs = chr(92)
        fuente = '#lang: es\nx = "hola' + bs + 'rmundo"\n'
        tokens = Lexer(fuente).tokenizar()
        strs = [t for t in tokens if t.tipo == TokenID.STRING]
        assert strs and chr(13) in strs[0].valor

    # --- Linea 494: escape \\ ---
    def test_cadena_escape_backslash(self):
        """Linea 494: escape \\\\ en cadena produce backslash literal."""
        bs = chr(92)
        fuente = '#lang: es\nx = "' + bs + bs + 'n"\n'
        tokens = Lexer(fuente).tokenizar()
        strs = [t for t in tokens if t.tipo == TokenID.STRING]
        assert strs and strs[0].valor == bs + "n"

    # --- Linea 496: escape de comilla ---
    def test_cadena_escape_comilla(self):
        """Linea 496: escape de comilla en cadena."""
        bs = chr(92)
        fuente = '#lang: es\nx = "' + bs + '"hola' + bs + '""\n'
        tokens = Lexer(fuente).tokenizar()
        strs = [t for t in tokens if t.tipo == TokenID.STRING]
        assert strs and '"hola' in strs[0].valor

    # --- Lineas 497-523: escape Unicode ---
    def test_cadena_escape_unicode(self):
        """Lineas 497-523: escape Unicode \\uXXXX."""
        bs = chr(92)
        fuente = '#lang: es\nx = "hello' + bs + 'u0041"\n'
        tokens = Lexer(fuente).tokenizar()
        strs = [t for t in tokens if t.tipo == TokenID.STRING]
        assert strs and "helloA" in strs[0].valor

    def test_cadena_escape_unicode_incompleto(self):
        """Lineas 504-508: escape Unicode incompleto (< 4 hex digits)."""
        bs = chr(92)
        fuente = '#lang: es\nx = "hello' + bs + 'u004"\n'
        with pytest.raises(SynapseError) as exc:
            Lexer(fuente).tokenizar()
        assert "Unicode incompleto" in exc.value.mensaje

    def test_cadena_escape_unicode_invalido(self):
        """Lineas 517-523: escape Unicode con hex invalido."""
        bs = chr(92)
        fuente = '#lang: es\nx = "' + bs + 'uZZZZ"\n'
        with pytest.raises(SynapseError) as exc:
            Lexer(fuente).tokenizar()
        assert "Unicode" in exc.value.mensaje

    # NOTA: lineas 510, 517-523 son codigo muerto (unreachable):
    # 510: len(hex_str) != 4 siempre es False porque el loop produce 4 chars
    # 517-523: int(hex_str, 16) nunca falla porque solo contiene hex validos

    # --- Lineas 593-598: notacion cientifica ---
    def test_numero_notacion_cientifica(self):
        """Lineas 593-598: notacion cientifica 1e3, 1.5E+2."""
        fuente = "#lang: es\nx = 1e3\ny = 1.5E+2\n"
        tokens = Lexer(fuente).tokenizar()
        floats = [t for t in tokens if t.tipo == TokenID.FLOAT]
        assert len(floats) == 2
        assert floats[0].valor == 1000.0
        assert floats[1].valor == 150.0
