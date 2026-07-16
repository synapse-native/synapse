import os, sys, json, re
from typing import Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from compilador.ast_nodes import TokenID, Token, Programa
from compilador.lexer import Lexer
from compilador.parser import Parser
from diagnostics import DiagnosticManager, ErrorCodes
from exceptions import SynapseError

# Reuse the canonical encoder from main.py
from main import _nodo_a_dict


DIR_FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')
DIR_VALID = os.path.join(DIR_FIXTURES, 'valid')
DIR_INVALID = os.path.join(DIR_FIXTURES, 'invalid')


def compilar_texto(fuente: str, idioma: str = 'es') -> Tuple[Programa, DiagnosticManager]:
    lineas = fuente.split('\n')
    diag = DiagnosticManager(fuente_lineas=lineas, ruta_archivo='<test>', idioma=idioma)
    try:
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
    except (SyntaxError, SynapseError) as e:
        mensaje = str(e)
        token = Token(TokenID.EOF, linea=1, columna=0)
        if 'indentaci' in mensaje:
            if 'múltiplo' in mensaje:
                diag.reportar(ErrorCodes.ERR_INDENT_INVALID, token)
            else:
                diag.reportar(ErrorCodes.ERR_INDENT_INCONSISTENT, token)
        elif 'Cadena sin cerrar' in mensaje:
            diag.reportar(ErrorCodes.ERR_STRING_UNCLOSED, token)
        elif 'Carácter inesperado' in mensaje or 'caracter inesperado' in mensaje:
            match = re.search(r"'([^']+)'", mensaje)
            diag.reportar(ErrorCodes.ERR_LEX_CHAR_UNEXPECTED, token, char=match.group(1) if match else '?')
        elif 'Idioma' in mensaje or 'idioma' in mensaje or '#lang' in mensaje:
            diag.reportar(ErrorCodes.ERR_LANG_MISSING, token)
        else:
            diag.reportar(ErrorCodes.ERR_LEX_CHAR_UNEXPECTED, token, char='?')
        return Programa(), diag
    parser = Parser(tokens, diag)
    ast = parser.parsear()
    from analizador_semantico import AnalizadorSemantico
    analizador = AnalizadorSemantico(ast, diag)
    analizador.analizar()
    return ast, diag


def ast_a_canonico_test(programa: Programa) -> str:
    return json.dumps(_nodo_a_dict(programa), indent=2, ensure_ascii=False)
