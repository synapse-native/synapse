# parser.py — orquestador del parser Synapse
#
# Las implementaciones por dominio sintactico viven en los mixins.
# Este modulo las combina y re-exporta para compatibilidad.

from typing import Optional

from compilador.ast_nodes import (
    TokenID, Nodo, Programa,
    SentenciaRecuperar, LogLlamada, SentenciaExpr,
    AsignacionVariable, DeclaracionVariable, AsignacionCampo,
    SentenciaEnviarCanal, ExprRecibirCanal,
    Identificador, LlamadaFuncion,
)
from compilador.diagnostics import ErrorCodes
from compilador.parser_base import _SYNC_EXPR
from compilador.parser_expressions import ParserExpressionsMixin
from compilador.parser_control import ParserControlMixin
from compilador.parser_declarations import ParserDeclarationsMixin


class Parser(
    ParserExpressionsMixin,
    ParserControlMixin,
    ParserDeclarationsMixin,
):
    def parsear(self) -> Programa:
        prog = Programa(linea=1, columna=0, is_no_std=self.is_no_std)
        while self._mirar().tipo != TokenID.EOF:
            stmt = self._parsear_sentencia()
            if stmt is not None:
                prog.sentencias.append(stmt)
            else:
                self._avanzar()
        return prog

    def _parsear_sentencia(self) -> Optional[Nodo]:
        t = self._mirar()
        if t.tipo == TokenID.FUNCTION:
            return self._parsear_def_funcion()
        elif t.tipo == TokenID.STRUCT:
            return self._parsear_def_estructura()
        elif t.tipo == TokenID.IF:
            return self._parsear_si()
        elif t.tipo == TokenID.SPAWN:
            return self._parsear_lanzar()
        elif t.tipo == TokenID.RETURN:
            return self._parsear_retornar()
        elif t.tipo == TokenID.LISTEN:
            return self._parsear_escuchar()
        elif t.tipo == TokenID.WHILE:
            return self._parsear_mientras()
        elif t.tipo == TokenID.PARA:
            return self._parsear_para()
        elif t.tipo == TokenID.BREAK:
            return self._parsear_romper()
        elif t.tipo == TokenID.CONTINUE:
            return self._parsear_siguiente()
        elif t.tipo == TokenID.INSEGURO:
            return self._parsear_inseguro()
        elif t.tipo == TokenID.IMPORTAR_C:
            return self._parsear_importar_c()
        elif t.tipo == TokenID.IMPORT:
            return self._parsear_importar()
        elif t.tipo == TokenID.EXTERNO:
            return self._parsear_declaracion_externa()
        elif t.tipo == TokenID.CONSTANTE:
            return self._parsear_constante()
        elif t.tipo == TokenID.MATCH:
            return self._parsear_coincidir()
        elif t.tipo in (TokenID.INDENT, TokenID.NEWLINE, TokenID.DEDENT, TokenID.EOF, TokenID.SEMICOLON):
            return None
        else:
            if (t.tipo in (TokenID.IDENTIFIER, TokenID.CANAL)
                    and self.pos + 1 < len(self.tokens)
                    and self.tokens[self.pos + 1].tipo == TokenID.ARROW_LEFT):
                return self._parsear_enviar_canal()
            if (t.tipo == TokenID.IDENTIFIER
                    and self.pos + 1 < len(self.tokens)
                    and self.tokens[self.pos + 1].tipo == TokenID.ASSIGN):
                return self._parsear_asignacion()
            if (t.tipo == TokenID.IDENTIFIER
                    and self.pos + 1 < len(self.tokens)
                    and self.tokens[self.pos + 1].tipo == TokenID.COLON
                    and self.pos + 2 < len(self.tokens)
                    and self.tokens[self.pos + 2].tipo == TokenID.IDENTIFIER):
                idx = self.pos + 3
                while idx < len(self.tokens) and self.tokens[idx].tipo == TokenID.STAR:
                    idx += 1
                if idx < len(self.tokens) and self.tokens[idx].tipo == TokenID.ASSIGN:
                    return self._parsear_declaracion_tipada()
            if (t.tipo == TokenID.IDENTIFIER
                    and self.pos + 3 < len(self.tokens)
                    and self.tokens[self.pos + 1].tipo == TokenID.DOT
                    and self.tokens[self.pos + 2].tipo == TokenID.IDENTIFIER
                    and self.tokens[self.pos + 3].tipo == TokenID.ASSIGN):
                return self._parsear_asignacion_campo()
            return self._parsear_expr_o_recuperar()

    def _parsear_asignacion(self) -> AsignacionVariable:
        tok_id = self._avanzar()
        self._esperar(TokenID.ASSIGN)
        if (self._mirar().tipo in (TokenID.IDENTIFIER, TokenID.CANAL)
                and self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].tipo == TokenID.ARROW):
            expr = self._parsear_recibir_canal()
        else:
            expr = self._parsear_expresion()
        return AsignacionVariable(
            nombre=tok_id.valor,
            expresion=expr,
            linea=tok_id.linea,
            columna=tok_id.columna,
        )

    def _parsear_declaracion_tipada(self) -> DeclaracionVariable:
        tok_id = self._avanzar()
        self._esperar(TokenID.COLON)
        tipo = self._parsear_tipo_parametro()
        self._esperar(TokenID.ASSIGN)
        if (self._mirar().tipo in (TokenID.IDENTIFIER, TokenID.CANAL)
                and self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].tipo == TokenID.ARROW):
            expr = self._parsear_recibir_canal()
        else:
            expr = self._parsear_expresion()
        return DeclaracionVariable(
            nombre=tok_id.valor,
            tipo=tipo,
            expresion=expr,
            linea=tok_id.linea,
            columna=tok_id.columna,
        )

    def _parsear_expr_o_recuperar(self) -> Nodo:
        expr = self._parsear_expresion()

        if isinstance(expr, LlamadaFuncion) and expr.nombre == 'log':
            return LogLlamada(
                argumentos=expr.argumentos,
                linea=expr.linea,
                columna=expr.columna,
            )

        if self._mirar().tipo == TokenID.RECOVER:
            self._avanzar()
            if self._esperar(TokenID.COLON) is None:
                self._sincronizar(_SYNC_EXPR)
                return SentenciaExpr(expr=expr, linea=expr.linea, columna=expr.columna)
            plan_b = self._parsear_expresion()
            return SentenciaRecuperar(
                accion_critica=expr,
                plan_b=plan_b,
                linea=expr.linea,
                columna=expr.columna,
            )
        elif self._mirar().tipo in (TokenID.NEWLINE, TokenID.DEDENT, TokenID.EOF):
            return SentenciaExpr(expr=expr, linea=expr.linea, columna=expr.columna)
        else:
            t = self._mirar()
            self.diag.reportar(ErrorCodes.ERR_SYNTAX_UNEXPECTED_TOKEN, t,
                               tok_name=t.tipo.name)
            self._sincronizar(_SYNC_EXPR)
            return SentenciaExpr(expr=expr, linea=expr.linea, columna=expr.columna)

    def _parsear_asignacion_campo(self) -> AsignacionCampo:
        tok_obj = self._avanzar()
        self._avanzar()  # DOT
        tok_campo = self._avanzar()
        self._esperar(TokenID.ASSIGN)
        expr = self._parsear_expresion()
        return AsignacionCampo(
            objeto=Identificador(nombre=tok_obj.valor, linea=tok_obj.linea, columna=tok_obj.columna),
            nombre_campo=tok_campo.valor,
            expresion=expr,
            linea=tok_obj.linea,
            columna=tok_obj.columna,
        )

    def _parsear_enviar_canal(self) -> Optional[SentenciaEnviarCanal]:
        tok_canal = self._esperar(TokenID.IDENTIFIER)
        if tok_canal is None:
            return None
        canal_nodo = Identificador(nombre=tok_canal.valor,
                                   linea=tok_canal.linea,
                                   columna=tok_canal.columna)
        if self._esperar(TokenID.ARROW_LEFT) is None:
            return None
        valor = self._parsear_expresion()
        return SentenciaEnviarCanal(
            canal=canal_nodo,
            valor=valor,
            linea=tok_canal.linea,
            columna=tok_canal.columna,
        )

    def _parsear_recibir_canal(self) -> Optional[ExprRecibirCanal]:
        tok_canal = self._esperar(TokenID.IDENTIFIER)
        if tok_canal is None:
            return None
        canal_nodo = Identificador(nombre=tok_canal.valor,
                                   linea=tok_canal.linea,
                                   columna=tok_canal.columna)
        if self._esperar(TokenID.ARROW) is None:
            return None
        return ExprRecibirCanal(
            canal=canal_nodo,
            linea=tok_canal.linea,
            columna=tok_canal.columna,
        )
