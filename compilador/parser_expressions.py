from typing import List, Optional

from compilador.ast_nodes import (
    TokenID, Token, Nodo,
    OpBinaria, OpUnaria, LlamadaFuncion, Identificador,
    LiteralNumero, LiteralDecimal, LiteralCadena, LiteralBooleano, ExprTensor,
    ArgumentoTransferido, ExprCrearCanal,
    ExprObtenerDireccion, ExprDereferencia, ExprAccesoCampo, ExprAsm,
)
from compilador.lexer import OPERADORES_BINARIOS
from compilador.diagnostics import ErrorCodes
from compilador.parser_base import ParserBase, _SYNC_EXPR


class ParserExpressionsMixin(ParserBase):
    def _parsear_expresion(self) -> Nodo:
        return self._parsear_logica()

    def _parsear_logica(self) -> Nodo:
        izquierdo = self._parsear_comparacion()
        ops = {TokenID.AND, TokenID.OR}
        while self._mirar().tipo in ops:
            tok_op = self._avanzar()
            derecho = self._parsear_comparacion()
            izquierdo = OpBinaria(
                izquierdo=izquierdo,
                operador=OPERADORES_BINARIOS[tok_op.tipo],
                derecho=derecho,
                linea=izquierdo.linea,
                columna=izquierdo.columna,
            )
        return izquierdo

    def _parsear_comparacion(self) -> Nodo:
        izquierdo = self._parsear_adicion()
        ops = {TokenID.GREATER, TokenID.LESS, TokenID.EQUALS,
               TokenID.NOT_EQUALS, TokenID.LESS_EQUALS, TokenID.GREATER_EQUALS}
        while self._mirar().tipo in ops:
            tok_op = self._avanzar()
            derecho = self._parsear_adicion()
            izquierdo = OpBinaria(
                izquierdo=izquierdo,
                operador=OPERADORES_BINARIOS[tok_op.tipo],
                derecho=derecho,
                linea=izquierdo.linea,
                columna=izquierdo.columna,
            )
        return izquierdo

    def _parsear_adicion(self) -> Nodo:
        izquierdo = self._parsear_multiplicacion()
        ops = {TokenID.PLUS, TokenID.MINUS}
        while self._mirar().tipo in ops:
            tok_op = self._avanzar()
            derecho = self._parsear_multiplicacion()
            izquierdo = OpBinaria(
                izquierdo=izquierdo,
                operador=OPERADORES_BINARIOS[tok_op.tipo],
                derecho=derecho,
                linea=izquierdo.linea,
                columna=izquierdo.columna,
            )
        return izquierdo

    def _parsear_multiplicacion(self) -> Nodo:
        izquierdo = self._parsear_unario()
        ops = {TokenID.STAR, TokenID.SLASH, TokenID.MODULO}
        while self._mirar().tipo in ops:
            tok_op = self._avanzar()
            derecho = self._parsear_unario()
            izquierdo = OpBinaria(
                izquierdo=izquierdo,
                operador=OPERADORES_BINARIOS[tok_op.tipo],
                derecho=derecho,
                linea=izquierdo.linea,
                columna=izquierdo.columna,
            )
        return izquierdo

    def _parsear_unario(self) -> Nodo:
        t = self._mirar()
        if t.tipo == TokenID.MINUS:
            self._avanzar()
            expr = self._parsear_unario()
            return OpUnaria(
                operador='-',
                expr=expr,
                linea=t.linea,
                columna=t.columna,
            )
        if t.tipo == TokenID.NOT:
            self._avanzar()
            expr = self._parsear_unario()
            return OpUnaria(
                operador='!',
                expr=expr,
                linea=t.linea,
                columna=t.columna,
            )
        if t.tipo == TokenID.AMPERSAND:
            self._avanzar()
            expr = self._parsear_unario()
            return ExprObtenerDireccion(
                expr=expr,
                linea=t.linea,
                columna=t.columna,
            )
        if t.tipo == TokenID.STAR:
            self._avanzar()
            expr = self._parsear_unario()
            return ExprDereferencia(
                expr=expr,
                linea=t.linea,
                columna=t.columna,
            )
        return self._parsear_primario()

    def _parsear_primario(self) -> Nodo:
        t = self._mirar()
        if t.tipo == TokenID.NUMBER:
            self._avanzar()
            return LiteralNumero(valor=t.valor, linea=t.linea, columna=t.columna)
        if t.tipo == TokenID.FLOAT:
            self._avanzar()
            return LiteralDecimal(valor=t.valor, linea=t.linea, columna=t.columna)
        if t.tipo == TokenID.STRING:
            self._avanzar()
            return LiteralCadena(valor=t.valor, linea=t.linea, columna=t.columna)
        if t.tipo == TokenID.TRUE:
            self._avanzar()
            return LiteralBooleano(valor=True, linea=t.linea, columna=t.columna)
        if t.tipo == TokenID.FALSE:
            self._avanzar()
            return LiteralBooleano(valor=False, linea=t.linea, columna=t.columna)
        if t.tipo == TokenID.ASM:
            self._avanzar()
            self._esperar(TokenID.LPAREN)
            tok_str = self._esperar(TokenID.STRING)
            instruccion = tok_str.valor if tok_str else ''
            self._esperar(TokenID.RPAREN)
            return ExprAsm(instruccion=instruccion, linea=t.linea, columna=t.columna)
        if t.tipo in (TokenID.IDENTIFIER, TokenID.CANAL):
            self._avanzar()
            nombre = t.valor if t.tipo == TokenID.IDENTIFIER else 'canal'
            if self._mirar().tipo == TokenID.LPAREN:
                if nombre == 'tensor':
                    return self._parsear_tensor(t)
                if nombre == 'canal':
                    return self._parsear_crear_canal(t)
                return self._parsear_llamada(Identificador(nombre=nombre, linea=t.linea, columna=t.columna))
            expr: Nodo = Identificador(nombre=nombre, linea=t.linea, columna=t.columna)
            while self._mirar().tipo == TokenID.DOT:
                self._avanzar()
                tok_campo = self._esperar(TokenID.IDENTIFIER)
                if tok_campo is None:
                    break
                expr = ExprAccesoCampo(
                    objeto=expr,
                    nombre_campo=tok_campo.valor,
                    linea=expr.linea,
                    columna=expr.columna,
                )
            return expr
        if t.tipo == TokenID.LPAREN:
            self._avanzar()
            expr = self._parsear_expresion()
            self._esperar(TokenID.RPAREN)
            return expr
        self.diag.reportar(ErrorCodes.ERR_SYNTAX_UNEXPECTED_EXPR, t, tipo=t.tipo.name)
        self._sincronizar(_SYNC_EXPR)
        return LiteralNumero(valor=0, linea=t.linea, columna=t.columna)

    def _parsear_tensor(self, tok_id: Token) -> ExprTensor:
        self._esperar(TokenID.LPAREN)
        filas = self._parsear_expresion()
        self._esperar(TokenID.COMMA)
        columnas = self._parsear_expresion()
        self._esperar(TokenID.RPAREN)
        return ExprTensor(
            filas=filas,
            columnas=columnas,
            linea=tok_id.linea,
            columna=tok_id.columna,
        )

    def _parsear_llamada(self, id_nodo: Optional[Nodo] = None) -> LlamadaFuncion:
        if id_nodo is None:
            id_nodo = self._esperar(TokenID.IDENTIFIER)
            if id_nodo is None:
                return LlamadaFuncion(nombre='?error?', linea=0, columna=0)
            tok_id = id_nodo
        else:
            tok_id = id_nodo
        self._esperar(TokenID.LPAREN)
        args: List[Nodo] = []
        if self._mirar().tipo != TokenID.RPAREN:
            if self._mirar().tipo == TokenID.ARROW:
                self._avanzar()
                args.append(ArgumentoTransferido(expr=self._parsear_expresion()))
            else:
                args.append(self._parsear_expresion())
            while self._mirar().tipo == TokenID.COMMA:
                self._avanzar()
                if self._mirar().tipo == TokenID.ARROW:
                    self._avanzar()
                    args.append(ArgumentoTransferido(expr=self._parsear_expresion()))
                else:
                    args.append(self._parsear_expresion())
        self._esperar(TokenID.RPAREN)
        nombre = tok_id.nombre if isinstance(tok_id, Nodo) and hasattr(tok_id, 'nombre') else getattr(tok_id, 'valor', '?')
        return LlamadaFuncion(
            nombre=nombre,
            argumentos=args,
            linea=tok_id.linea if isinstance(tok_id, Token) else 0,
            columna=tok_id.columna if isinstance(tok_id, Token) else 0,
        )

    def _parsear_crear_canal(self, tok_id: Token) -> ExprCrearCanal:
        self._esperar(TokenID.LPAREN)
        tipo_contenido = ''
        capacidad = None
        if self._mirar().tipo == TokenID.IDENTIFIER:
            tok_tipo = self._avanzar()
            tipo_contenido = tok_tipo.valor or ''
        if self._mirar().tipo == TokenID.COMMA:
            self._avanzar()
            capacidad = self._parsear_expresion()
        self._esperar(TokenID.RPAREN)
        return ExprCrearCanal(
            tipo_contenido=tipo_contenido,
            capacidad=capacidad,
            linea=tok_id.linea,
            columna=tok_id.columna,
        )
