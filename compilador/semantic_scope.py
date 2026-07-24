from typing import List, Optional, Dict, Tuple

from compilador.ast_nodes import (
    Programa, DefinicionEstructura, Token, TokenID,
)
from compilador.diagnostics import DiagnosticManager
from compilador.symbol_table import SymbolTable
from compilador.generator import MAPA_TIPOS_C


_FUNCIONES_BUILTIN: Dict[str, Tuple[List[str], str]] = {
    'reserva': (['int'], 'tensor'),
    'libera': (['tensor'], 'nulo'),
    'crear_tensor': (['int', 'int'], 'tensor'),
    'suma_tensor': (['tensor', 'tensor'], 'tensor'),
    'producto_punto': (['tensor', 'tensor'], 'tensor'),
    'abrir': (['texto', 'texto'], 'Canal'),
    'leer': (['Canal'], 'texto'),
    'escribir': (['texto'], 'nulo'),
    'escribir_linea': (['texto'], 'nulo'),
    'leer_linea': ([], 'texto'),
    'cerrar': (['Canal'], 'nulo'),
    'suma': (['tensor', 'tensor'], 'tensor'),
    'producto': (['tensor', 'tensor'], 'tensor'),
    'relu': (['tensor'], 'tensor'),
    'tokenizar': (['texto'], 'int'),
    'parsear': (['texto'], 'Programa'),
    'generar': (['Programa', 'texto'], 'int'),
    '_argc': ([], 'int'),
    '_argv': (['int'], 'texto'),
    'salir': (['int'], 'nulo'),
    'concat': (['texto', 'texto'], 'texto'),
    'texto_a_entero': (['texto'], 'int'),
    'texto_a_decimal': (['texto'], 'decimal'),
    'entero_a_texto': (['int'], 'texto'),
    'decimal_a_texto': (['decimal'], 'texto'),
    'volcar_ast': (['Programa', 'int'], 'nulo'),
    'crear_analizador': (['Programa'], 'int'),
    'analizar': (['int'], 'nulo'),
    'canal_crear': (['int'], 'CanalConcurrencia*'),
    'canal_enviar': (['CanalConcurrencia*', 'void*'], 'nulo'),
    'canal_recibir': (['CanalConcurrencia*'], 'void*'),
    'cerrar_canal': (['CanalConcurrencia*'], 'nulo'),
}


def _tipo_normalizado(tipo: str) -> str:
    return MAPA_TIPOS_C.get(tipo, tipo)


class AnalizadorSemanticoScope:
    def __init__(self, programa: Programa, diag: DiagnosticManager):
        self.programa = programa
        self.diag = diag
        self.tabla = SymbolTable()
        self._func_retorno: Optional[str] = None
        self._func_actual: Optional[str] = None
        self._estructuras: Dict[str, DefinicionEstructura] = {}
        self._en_coincidir: bool = False
        self._dentro_de_inseguro: bool = False

    def _token(self, linea: int, columna: int) -> Token:
        return Token(TokenID.IDENTIFIER, linea, columna)
