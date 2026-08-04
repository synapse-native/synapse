# parser.py — orquestador del parser Synapse
#
# Las implementaciones por dominio sintactico viven en los mixins.
# Este modulo las combina y re-exporta para compatibilidad.

from typing import List, Optional

from compilador.ast_nodes import (
    TokenID, Nodo, Programa,
    SentenciaRecuperar, LogLlamada, SentenciaExpr,
    AsignacionVariable, DeclaracionVariable, AsignacionCampo,
    SentenciaEnviarCanal, ExprRecibirCanal,
    Identificador, LlamadaFuncion, ConstructorTipo, DeclaracionTipo,
)
from compilador.diagnostics import ErrorCodes
from compilador.parser_base import _SYNC_EXPR, es_token_identificador, nombre_de_token
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
        if t.tipo == TokenID.FUNCION:
            return self._parsear_def_funcion()
        elif t.tipo == TokenID.ESTRUCTURA:
            return self._parsear_def_estructura()
        elif t.tipo == TokenID.SI:
            return self._parsear_si()
        elif t.tipo == TokenID.LANZAR:
            return self._parsear_lanzar()
        elif t.tipo == TokenID.RETORNAR:
            return self._parsear_retornar()
        elif t.tipo == TokenID.ESCUCHAR:
            return self._parsear_escuchar()
        elif t.tipo == TokenID.MIENTRAS:
            return self._parsear_mientras()
        elif t.tipo == TokenID.PARA:
            return self._parsear_para()
        elif t.tipo == TokenID.ROMPER:
            return self._parsear_romper()
        elif t.tipo == TokenID.SIGUIENTE:
            return self._parsear_siguiente()
        elif t.tipo == TokenID.INSEGURO:
            return self._parsear_inseguro()
        elif t.tipo == TokenID.IMPORTAR_C:
            return self._parsear_importar_c()
        elif t.tipo == TokenID.IMPORTAR:
            return self._parsear_importar()
        elif t.tipo == TokenID.EXTERNO:
            return self._parsear_declaracion_externa()
        elif t.tipo == TokenID.CONSTANTE:
            return self._parsear_constante()
        elif t.tipo == TokenID.COINCIDIR:
            return self._parsear_coincidir()
        elif t.tipo in (TokenID.INDENT, TokenID.NEWLINE, TokenID.DEDENT, TokenID.EOF, TokenID.SEMICOLON):
            return None
        elif (t.tipo == TokenID.TIPO
              and self.pos + 1 < len(self.tokens)
              and es_token_identificador(self.tokens[self.pos + 1])
              and self.pos + 2 < len(self.tokens)
              and self.tokens[self.pos + 2].tipo
                  in (TokenID.ASSIGN, TokenID.LESS, TokenID.PIPE, TokenID.LPAREN)):
            # F1.2: declaración de tipo (Manual 2 §2 declaracion_tipo / §4.2):
            #   tipo X = entero            (alias)
            #   tipo X = ok(entero) | err(texto)   (tipo algebraico)
            #   tipo X<T, E> = ok(T) | err(E)      (genéricos)
            # Ambiguo con `tipo = x` / `tipo == x` / `tipo.x` (tipo como variable
            # contextual): solo se intercepta cuando el siguiente token es un
            # nombre de tipo seguido de =, < (genéricos), | o (.
            return self._parsear_declaracion_tipo()
        else:
            if ((es_token_identificador(t) or t.tipo == TokenID.CANAL)
                    and self.pos + 1 < len(self.tokens)
                    and self.tokens[self.pos + 1].tipo == TokenID.ARROW_LEFT):
                return self._parsear_enviar_canal()
            if (es_token_identificador(t)
                    and self.pos + 1 < len(self.tokens)
                    and self.tokens[self.pos + 1].tipo == TokenID.ASSIGN):
                return self._parsear_asignacion()
            if (es_token_identificador(t)
                    and self.pos + 1 < len(self.tokens)
                    and self.tokens[self.pos + 1].tipo == TokenID.COLON
                    and self.pos + 2 < len(self.tokens)
                    and es_token_identificador(self.tokens[self.pos + 2])):
                idx = self.pos + 3
                while idx < len(self.tokens) and self.tokens[idx].tipo == TokenID.STAR:
                    idx += 1
                if idx < len(self.tokens) and self.tokens[idx].tipo == TokenID.ASSIGN:
                    return self._parsear_declaracion_tipada()
            if (es_token_identificador(t)
                    and self.pos + 3 < len(self.tokens)
                    and self.tokens[self.pos + 1].tipo == TokenID.DOT
                    and es_token_identificador(self.tokens[self.pos + 2])
                    and self.tokens[self.pos + 3].tipo == TokenID.ASSIGN):
                return self._parsear_asignacion_campo()
            return self._parsear_expr_o_recuperar()

    def _parsear_asignacion(self) -> AsignacionVariable:
        tok_id = self._avanzar()
        self._esperar(TokenID.ASSIGN)
        if (es_token_identificador(self._mirar())
                and self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].tipo == TokenID.ARROW):
            expr = self._parsear_recibir_canal()
        else:
            expr = self._parsear_expresion()
        return AsignacionVariable(
            nombre=nombre_de_token(tok_id),
            expresion=expr,
            linea=tok_id.linea,
            columna=tok_id.columna,
        )

    def _parsear_declaracion_tipada(self) -> DeclaracionVariable:
        tok_id = self._avanzar()
        self._esperar(TokenID.COLON)
        tipo = self._parsear_tipo_parametro()
        self._esperar(TokenID.ASSIGN)
        if (es_token_identificador(self._mirar())
                and self.pos + 1 < len(self.tokens)
                and self.tokens[self.pos + 1].tipo == TokenID.ARROW):
            expr = self._parsear_recibir_canal()
        else:
            expr = self._parsear_expresion()
        return DeclaracionVariable(
            nombre=nombre_de_token(tok_id),
            tipo=tipo,
            expresion=expr,
            linea=tok_id.linea,
            columna=tok_id.columna,
        )

    def _parsear_declaracion_tipo(self) -> Optional[DeclaracionTipo]:
        """F1.2: `tipo <Nombre> [<T, E>] = <tipo> | ctor(...) [| ctor(...)]`
        (Manual 2 §2 declaracion_tipo y §4.2). El nombre puede llevar parámetros
        de tipo entre < >; el RHS es un tipo simple o constructores ADT.
        """
        tok_tipo_kw = self._esperar(TokenID.TIPO)
        if tok_tipo_kw is None:
            return None
        tok_nombre = self._esperar_identificador()
        if tok_nombre is None:
            self._sincronizar(_SYNC_EXPR)
            return None
        nombre = nombre_de_token(tok_nombre)
        parametros_tipo: List[str] = []
        if self._mirar().tipo == TokenID.LESS:
            self._avanzar()
            while self._mirar().tipo != TokenID.GREATER and self._mirar().tipo not in (TokenID.EOF, TokenID.NEWLINE):
                tp = self._esperar_identificador()
                if tp is not None:
                    parametros_tipo.append(nombre_de_token(tp))
                if self._mirar().tipo == TokenID.COMMA:
                    self._avanzar()
                elif self._mirar().tipo == TokenID.GREATER:
                    break
                else:
                    break
            self._esperar(TokenID.GREATER)
        if self._esperar(TokenID.ASSIGN) is None:
            self._sincronizar(_SYNC_EXPR)
            return None
        # RHS: alias simple (tipo) o constructores ADT separados por |
        tipo_base = ''
        constructores: List[ConstructorTipo] = []
        if self._mirar().tipo == TokenID.LPAREN:
            self._avanzar()
            self._parsear_constructores(constructores)
            self._esperar(TokenID.RPAREN)
        else:
            primer = self._mirar()
            if es_token_identificador(primer):
                # ¿alias simple o primer constructor?
                sig = self.tokens[self.pos + 1].tipo if self.pos + 1 < len(self.tokens) else TokenID.EOF
                if sig == TokenID.PIPE or sig == TokenID.LPAREN:
                    self._parsear_constructores(constructores)
                else:
                    tipo_base = self._parsear_tipo_parametro()
            elif primer.tipo == TokenID.PIPE:
                self._parsear_constructores(constructores)
        return DeclaracionTipo(
            nombre=nombre,
            parametros_tipo=parametros_tipo,
            tipo_base=tipo_base,
            constructores=constructores,
            linea=tok_tipo_kw.linea,
            columna=tok_tipo_kw.columna,
        )

    def _parsear_constructores(self, constructores: List[ConstructorTipo]):
        """F1.2: lista de constructores ADT: `ctor(T1, T2) | ctor2 | ...`
        (Manual 2 §2 constructor).
        """
        while True:
            tok_ctor = self._esperar_identificador()
            if tok_ctor is None:
                break
            ctor = ConstructorTipo(nombre=nombre_de_token(tok_ctor))
            if self._mirar().tipo == TokenID.LPAREN:
                self._avanzar()
                while self._mirar().tipo not in (TokenID.RPAREN, TokenID.EOF, TokenID.NEWLINE):
                    tipo_c = self._parsear_tipo_parametro()
                    if tipo_c:
                        ctor.tipos.append(tipo_c)
                    if self._mirar().tipo == TokenID.COMMA:
                        self._avanzar()
                    else:
                        break
                self._esperar(TokenID.RPAREN)
            constructores.append(ctor)
            if self._mirar().tipo == TokenID.PIPE:
                self._avanzar()
                continue
            break

    def _parsear_expr_o_recuperar(self) -> Nodo:
        expr = self._parsear_expresion()

        if isinstance(expr, LlamadaFuncion) and expr.nombre == 'log':
            return LogLlamada(
                argumentos=expr.argumentos,
                linea=expr.linea,
                columna=expr.columna,
            )

        if self._mirar().tipo == TokenID.RECUPERAR:
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
        tok_canal = self._esperar_identificador()
        if tok_canal is None:
            return None
        canal_nodo = Identificador(nombre=nombre_de_token(tok_canal),
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
        tok_canal = self._esperar_identificador()
        if tok_canal is None:
            return None
        canal_nodo = Identificador(nombre=nombre_de_token(tok_canal),
                                   linea=tok_canal.linea,
                                   columna=tok_canal.columna)
        if self._esperar(TokenID.ARROW) is None:
            return None
        return ExprRecibirCanal(
            canal=canal_nodo,
            linea=tok_canal.linea,
            columna=tok_canal.columna,
        )
