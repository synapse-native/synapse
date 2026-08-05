from typing import List, Optional, Set

from compilador.ast_nodes import (
    TokenID, Token, Nodo,
)
from compilador.diagnostics import DiagnosticManager, ErrorCodes


_SYNC_TOP = {TokenID.FUNCION, TokenID.IMPORTAR, TokenID.EOF}
_SYNC_STMT = {TokenID.NEWLINE, TokenID.DEDENT, TokenID.EOF} | _SYNC_TOP
_SYNC_BLOCK = {TokenID.DEDENT, TokenID.EOF}
_SYNC_EXPR = {TokenID.NEWLINE, TokenID.DEDENT, TokenID.EOF,
              TokenID.COMMA, TokenID.RPAREN, TokenID.COLON, TokenID.SEMICOLON}

# AUDITORIA F1.2 (D-F1): keywords contextuales que el parser acepta donde un
# identificador es válido (campo x.tipo, variable/parámetro tipo o tensor,
# tipo de retorno nulo/tensor, patrones ADT ok/err/algun/ninguno). El lexer
# conserva su lexema en Token.valor (ver TOKENS_CONTEXTUALES en lexer.py).
TOKENS_CONTEXTUALES: frozenset = frozenset({
    TokenID.TIPO, TokenID.TENSOR, TokenID.NULO,
    TokenID.OK, TokenID.ERR, TokenID.ALGUN, TokenID.NINGUNO,
    TokenID.ARC, TokenID.DEBIL,
})


def es_token_identificador(t: Token) -> bool:
    """True si el token puede actuar como identificador (IDENTIFIER o keyword contextual)."""
    return t.tipo == TokenID.IDENTIFIER or t.tipo in TOKENS_CONTEXTUALES


def nombre_de_token(t: Token) -> str:
    """Lexema usable del token (identificadores y keywords contextuales)."""
    if t.valor:
        return t.valor
    if t.tipo == TokenID.IDENTIFIER:
        return t.valor or ''
    return t.tipo.name.lower()


class ParserBase:
    def __init__(self, tokens: List[Token], diag: DiagnosticManager, is_no_std: bool = False):
        self.tokens = tokens
        self.pos = 0
        self.diag = diag
        self.is_no_std = is_no_std

    def _mirar(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token(TokenID.EOF, 0, 0)

    def _avanzar(self) -> Token:
        t = self._mirar()
        self.pos += 1
        return t

    def _sincronizar(self, sync_tokens: Set[TokenID]) -> None:
        self._avanzar()
        while self._mirar().tipo not in sync_tokens:
            self._avanzar()

    def _posible(self, *tipos: TokenID) -> Optional[Token]:
        t = self._mirar()
        if t.tipo in tipos:
            return self._avanzar()
        return None

    def _esperar(self, *tipos: TokenID) -> Optional[Token]:
        t = self._mirar()
        if t.tipo not in tipos:
            esperado = ' o '.join(tt.name for tt in tipos)
            self.diag.reportar(ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN, t,
                               esperado=esperado, encontrado=t.tipo.name)
            self._sincronizar(_SYNC_EXPR)
            return None
        return self._avanzar()

    def _esperar_identificador(self) -> Optional[Token]:
        """Consume un token usable como identificador: IDENTIFIER o keyword
        contextual (F1.2). Devuelve el token (con su lexema en .valor) o None."""
        t = self._mirar()
        if not es_token_identificador(t):
            self.diag.reportar(ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN, t,
                               esperado='IDENTIFICADOR', encontrado=t.tipo.name)
            self._sincronizar(_SYNC_EXPR)
            return None
        return self._avanzar()

    def _parsear_bloque(self) -> Optional[List[Nodo]]:
        if self._esperar(TokenID.NEWLINE) is None:
            self.diag.reportar(ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN, self._mirar(),
                               esperado='NEWLINE', encontrado=self._mirar().tipo.name)
            self._sincronizar(_SYNC_BLOCK)
            return None
        if self._esperar(TokenID.INDENT) is None:
            self.diag.reportar(ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN, self._mirar(),
                               esperado='INDENT', encontrado=self._mirar().tipo.name)
            self._sincronizar(_SYNC_BLOCK)
            return None
        stmts: List[Nodo] = []
        while self._mirar().tipo not in (TokenID.DEDENT, TokenID.EOF):
            s = self._parsear_sentencia()
            if s is not None:
                stmts.append(s)
            else:
                self._avanzar()
        if self._mirar().tipo != TokenID.EOF:
            token_dedent = self._mirar()
            dedent_ok = self._posible(TokenID.DEDENT)
            if not dedent_ok:
                self.diag.reportar(ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN, token_dedent,
                                   esperado='DEDENT', encontrado=token_dedent.tipo.name)
                self._sincronizar(_SYNC_BLOCK)
        return stmts

    def _parsear_bloque_expresiones(self) -> List[Nodo]:
        nodos: List[Nodo] = []
        if self._mirar().tipo == TokenID.NEWLINE:
            self._avanzar()
        if self._mirar().tipo != TokenID.INDENT:
            expr = self._parsear_expresion()
            if expr:
                nodos.append(expr)
            return nodos
        self._avanzar()
        while self._mirar().tipo not in (TokenID.DEDENT, TokenID.EOF):
            if self._mirar().tipo == TokenID.NEWLINE:
                self._avanzar()
                continue
            expr = self._parsear_expresion()
            if expr:
                nodos.append(expr)
        if self._mirar().tipo == TokenID.DEDENT:
            self._avanzar()
        return nodos

    def _saltar_nueva_linea(self):
        while self._mirar().tipo in (TokenID.NEWLINE,):
            self._avanzar()

    def _parsear_tipo_parametro(self) -> str:
        prefijo = ''
        # Manual 4 §4.2: referencias &T y &mut T
        if self._mirar().tipo == TokenID.AMPERSAND:
            self._avanzar()
            if es_token_identificador(self._mirar()) and (self._mirar().valor or '') == 'mut':
                self._avanzar()
                prefijo = '&mut '
            else:
                prefijo = '&'
        tok_tipo = self._esperar_identificador()
        if tok_tipo is None:
            return prefijo + 'int'
        tipo = prefijo + (tok_tipo.valor or tok_tipo.tipo.name.lower())
        if self._mirar().tipo == TokenID.LESS:
            self._avanzar()
            partes = [tipo, '<']
            while self._mirar().tipo not in (TokenID.GREATER, TokenID.EOF, TokenID.NEWLINE, TokenID.RPAREN):
                partes.append(str(self._avanzar().valor or ''))
            if self._mirar().tipo == TokenID.GREATER:
                self._avanzar()
            partes.append('>')
            tipo = ''.join(partes)
        elif self._mirar().tipo == TokenID.STAR:
            self._avanzar()
            tipo += '*'
        return tipo
