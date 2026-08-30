# -*- coding: utf-8 -*-
"""Tests unitarios del lexer S1 (checklist FASE 1, 1.5/1.6).

Manual 2 §12 — Lexer multi-idioma: `pytest tests/unit/test_lexer.py -v`
con 100% pass y >95% cobertura de compilador/lexer.py.
Criterio 1.6: los ejemplos del Manual 2 tokenizan y los errores léxicos
reportan ubicación precisa (línea y columna) via SynapseError.
"""
import os
import re

import pytest

from compilador.lexer import Lexer
from compilador.ast_nodes import TokenID
from exceptions import SynapseError

pytestmark = pytest.mark.unit


def _tipos(fuente: str):
    return [t.tipo for t in Lexer(fuente).tokenizar()]


def _tokens(fuente: str):
    return Lexer(fuente).tokenizar()


# ---------------------------------------------------------------- Fase 0 (operadores)


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


# ------------------------------------------------------ 1.5: idioma y directivas


class TestLexerIdiomaYDirectivas:
    def test_lang_es(self):
        tipos = _tipos("#lang: es\nx = 1")
        assert TokenID.IDENTIFIER in tipos
        assert TokenID.ASSIGN in tipos
        assert TokenID.NUMBER in tipos

    @pytest.mark.parametrize("idioma,kw", [
        ('es', 'si'), ('en', 'if'), ('fr', 'si'),
        ('pt', 'se'), ('de', 'wenn'), ('it', 'se'),
    ])
    def test_lang_todos_idiomas(self, idioma, kw):
        """Manual 2 §3: tabla multi-idioma — 'si' se tokeniza como T_SI en cada idioma."""
        tipos = _tipos("#lang: " + idioma + "\n" + kw + " a == 1:\n    x = 1")
        assert TokenID.SI in tipos, "idioma " + idioma + ": keyword '" + kw + "'"

    def test_lang_faltante_ubicacion(self):
        with pytest.raises(SynapseError) as exc:
            Lexer("x = 1").tokenizar()
        assert exc.value.linea == 1
        assert exc.value.columna == 0

    def test_lang_codigo_vacio(self):
        with pytest.raises(SynapseError) as exc:
            Lexer("#lang:").tokenizar()
        assert exc.value.linea == 1

    def test_lang_no_soportado(self):
        with pytest.raises(SynapseError) as exc:
            Lexer("#lang: xx\nx = 1").tokenizar()
        assert "no soportado" in exc.value.mensaje
        assert exc.value.linea == 1

    def test_pragma_no_std(self):
        lexer = Lexer("#lang: es\n#pragma: no_std\nx = 1")
        lexer.tokenizar()
        assert lexer.is_no_std is True

    def test_entrada_vacia_es_error(self):
        """Entrada vacía: cae en 'falta #lang' (el diccionario no se puede
        inferir), que es el contrato del Manual 2: todo archivo comienza con
        `#lang:` en la línea 1."""
        with pytest.raises(SynapseError) as exc:
            Lexer("").tokenizar()
        assert exc.value.linea == 1


# ------------------------------------------------------ 1.5: indentación


class TestLexerIndentacion:
    def test_indent_dedent(self):
        tipos = _tipos("#lang: es\nfuncion f() -> nulo:\n    retornar\n")
        assert tipos.count(TokenID.INDENT) == 1
        assert tipos.count(TokenID.DEDENT) == 1

    def test_indent_multiples_niveles(self):
        tipos = _tipos("#lang: es\nsi a:\n    si b:\n        x = 1\n")
        assert tipos.count(TokenID.INDENT) == 2
        assert tipos.count(TokenID.DEDENT) == 2

    def test_indent_no_multiplo_4(self):
        with pytest.raises(SynapseError) as exc:
            Lexer("#lang: es\nsi a:\n   x = 1").tokenizar()
        assert exc.value.linea == 3

    def test_indent_inconsistente_ubicacion(self):
        # Pila [0,1,3] y luego nivel 2 -> inconsistente en la línea 4
        fuente = "#lang: es\n    a = 1\n            b = 2\n        c = 3\n"
        with pytest.raises(SynapseError) as exc:
            Lexer(fuente).tokenizar()
        assert "inconsistente" in exc.value.mensaje
        assert exc.value.linea == 4


# ------------------------------------------------------ 1.5: literales


class TestLexerLiterales:
    @pytest.mark.parametrize("fuente,expected", [
        ("#lang: es\nx = 42", 42),
        ("#lang: es\nx = 0", 0),
        ("#lang: es\nx = 999999", 999999),
        ("#lang: es\nx = 255", 255),
    ])
    def test_numero_entero_valor(self, fuente, expected):
        ts = _tokens(fuente)
        nums = [t for t in ts if t.tipo == TokenID.NUMBER]
        assert nums and nums[0].valor == expected

    @pytest.mark.parametrize("fuente,expected", [
        ("#lang: es\nx = 3.14", 3.14),
        ("#lang: es\nx = 0.0", 0.0),
        ("#lang: es\nx = 1e3", 1000.0),
        ("#lang: es\nx = 1.5E+2", 150.0),
    ])
    def test_numero_flotante_valor(self, fuente, expected):
        ts = _tokens(fuente)
        fl = [t for t in ts if t.tipo in (TokenID.FLOAT, TokenID.NUMBER)]
        assert fl and abs(fl[0].valor - expected) < 1e-9

    @pytest.mark.parametrize("fuente,expected", [
        ('#lang: es\nx = "a\\nb\\tc"', "a\nb\tc"),
        ("#lang: es\nx = 'hola'", "hola"),
        ('#lang: es\nx = "dijo: \\"hola\\""', 'dijo: "hola"'),
        ('#lang: es\nx = "a\\\\b"', "a\\b"),
    ])
    def test_cadena_escapes(self, fuente, expected):
        ts = _tokens(fuente)
        cad = [t for t in ts if t.tipo == TokenID.STRING]
        assert cad and cad[0].valor == expected

    def test_cadena_sin_cerrar_ubicacion(self):
        with pytest.raises(SynapseError) as exc:
            Lexer('#lang: es\nx = "abc').tokenizar()
        assert "Cadena sin cerrar" in exc.value.mensaje
        assert exc.value.linea == 2
        assert exc.value.columna == 4


# ---------------------------------------------- 1.5: keywords y contextuales


class TestLexerKeywordsYContextuales:
    @pytest.mark.parametrize("idioma,kw,ret,and_,verdad", [
        ('es', 'funcion', 'retornar', 'y', 'verdadero'),
        ('en', 'function', 'return', 'and', 'true'),
        ('fr', 'fonction', 'retourner', 'et', 'vrai'),
        ('pt', 'funcao', 'retornar', 'e', 'verdadeiro'),
        ('de', 'funktion', 'rueckgabe', 'und', 'wahr'),
        ('it', 'funzione', 'restituisci', 'e', 'vero'),
    ])
    def test_keywords_multi_idioma(self, idioma, kw, ret, and_, verdad):
        """Manual 2 §3: palabras reservadas de los 6 idiomas del lexer."""
        tipos = _tipos("#lang: " + idioma + "\n" + kw +
                       " f() -> nulo:\n    x = " + verdad + " " + and_ + " " + ret)
        assert TokenID.FUNCION in tipos, idioma + ": " + kw
        assert TokenID.RETORNAR in tipos, idioma + ": " + ret
        assert TokenID.AND in tipos, idioma + ": " + and_
        assert TokenID.VERDADERO in tipos, idioma + ": " + verdad

    def test_contextuales_conservan_lexema(self):
        """F1.2/F1.4: los keywords contextuales (tipo/nulo/ok/err/rc/arc/débil/
        modulo) conservan su lexema en Token.valor."""
        ts = _tokens("#lang: es\nx = nulo")
        nul = [t for t in ts if t.tipo == TokenID.NULO]
        assert nul and nul[0].valor == "nulo"

    def test_contextual_debil_utf8(self):
        ts = _tokens("#lang: es\nx = débil")
        deb = [t for t in ts if t.tipo == TokenID.DEBIL]
        assert deb and deb[0].valor == "débil"

    def test_identificador_guion_bajo(self):
        ts = _tokens("#lang: es\nx = _mi_var_1")
        ids = [t for t in ts if t.tipo == TokenID.IDENTIFIER]
        assert ids and ids[-1].valor == "_mi_var_1"

    def test_export(self):
        tipos = _tipos("#lang: es\n@export ( c ) funcion f() -> nulo:\n    retornar")
        assert TokenID.EXPORT in tipos

    def test_arobas_palabra_invalida(self):
        with pytest.raises(SynapseError) as exc:
            Lexer("#lang: es\nx = @foo").tokenizar()
        assert exc.value.linea == 2

    def test_arobas_suelto(self):
        with pytest.raises(SynapseError) as exc:
            Lexer("#lang: es\nx = @").tokenizar()
        assert exc.value.linea == 2


# ------------------------------------------------------ 1.5: comentarios


class TestLexerComentarios:
    def test_comentario_linea_completa(self):
        tipos = _tipos("#lang: es\n// comentario\nx = 1")
        assert tipos.count(TokenID.IDENTIFIER) == 1  # solo la 'x'

    def test_comentario_tras_codigo(self):
        ts = _tokens("#lang: es\nx = 1 // resto de linea")
        tipos = [t.tipo for t in ts]
        assert TokenID.NUMBER in tipos
        assert tipos.count(TokenID.IDENTIFIER) == 1

    def test_linea_directiva_ignorada(self):
        tipos = _tipos("#lang: es\n# otra directiva\nx = 1")
        assert TokenID.IDENTIFIER in tipos


# -------------------------------------------- 1.5/1.6: operadores y ubicación


class TestLexerOperadoresExtendidos:
    def test_arrow(self):
        assert TokenID.ARROW in _tipos("#lang: es\nx = a -> b")

    def test_arrow_right(self):
        assert TokenID.ARROW_RIGHT in _tipos("#lang: es\nx = a => b")

    def test_arrow_left(self):
        assert TokenID.ARROW_LEFT in _tipos("#lang: es\nch <- x")

    def test_pipe(self):
        assert TokenID.PIPE in _tipos(
            "#lang: es\ntipo X = ok(entero) | err(texto)")

    def test_interrogacion(self):
        assert TokenID.INTERROGACION in _tipos("#lang: es\nx = f()?")

    def test_punteros_dereferencia(self):
        tipos = _tipos("#lang: es\nx = &a\nz = *p")
        assert TokenID.AMPERSAND in tipos
        assert TokenID.STAR in tipos

    def test_indice(self):
        tipos = _tipos("#lang: es\nx = t[0]")
        assert TokenID.LBRACKET in tipos
        assert TokenID.RBRACKET in tipos

    def test_caracter_inesperado_ubicacion(self):
        with pytest.raises(SynapseError) as exc:
            Lexer("#lang: es\nx = $").tokenizar()
        assert exc.value.linea == 2
        assert exc.value.columna == 4


# ------------------------------------------------------ 1.6: ejemplos del Manual 2


def _ejemplos_manual_2():
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "docs", "manuales", "MANUAL 2.md")
    with open(ruta, encoding="utf-8") as f:
        texto = f.read()
    return re.findall(r"```synapse\n(.*?)\n```", texto, re.DOTALL)


class TestEjemplosManual2:
    def test_hay_ejemplos(self):
        bloques = _ejemplos_manual_2()
        assert len(bloques) >= 3

    def test_ejemplos_tokenizan(self):
        """Criterio 1.6: los ejemplos del Manual 2 tokenizan sin error. El
        Manual 2 §1 exige `#lang:` en la línea 1 de todo archivo; se prepende
        cuando el ejemplo no la incluye."""
        for i, bloque in enumerate(_ejemplos_manual_2()):
            fuente = bloque if bloque.strip().startswith("#lang:") else (
                "#lang: es\n" + bloque)
            tokens = Lexer(fuente).tokenizar()  # no debe lanzar SynapseError
            assert tokens[-1].tipo == TokenID.EOF, "bloque " + str(i)







