from typing import List, Optional, Set

from ast_nodes import (
    TokenID, Token, Nodo, Programa, Parametro,
    DefinicionFuncion, DefinicionEstructura, ExprAccesoCampo, AsignacionCampo,
    StmtConstante,
    SentenciaSi, SentenciaLanzar, SentenciaRetornar,
    SentenciaEscuchar, SentenciaMientras, SentenciaImportar,
    AsignacionVariable, SentenciaRecuperar, LogLlamada, SentenciaExpr,
    SentenciaRomper, SentenciaSiguiente,
    OpBinaria, OpUnaria, LlamadaFuncion, Identificador,
    LiteralNumero, LiteralDecimal, LiteralCadena, ExprTensor, ArgumentoTransferido,
    BloqueInseguro, ExprObtenerDireccion, ExprDereferencia, TipoPuntero,
    ImportarC, DeclaracionExterna,
    NodoCaso, NodoCoincidir,
    ExprCrearCanal, SentenciaEnviarCanal, ExprRecibirCanal,
    ExprAsm,
)
from lexer import OPERADORES_BINARIOS
from diagnostics import DiagnosticManager, ErrorCodes


# Conjuntos de sincronizacion por nivel
_SYNC_TOP = {TokenID.FUNCTION, TokenID.IMPORT, TokenID.EOF}
_SYNC_STMT = {TokenID.NEWLINE, TokenID.DEDENT, TokenID.EOF} | _SYNC_TOP
_SYNC_BLOCK = {TokenID.DEDENT, TokenID.EOF}
_SYNC_EXPR = {TokenID.NEWLINE, TokenID.DEDENT, TokenID.EOF,
              TokenID.COMMA, TokenID.RPAREN, TokenID.COLON}


class Parser:
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
        elif t.tipo == TokenID.INDENT:
            return None
        elif t.tipo == TokenID.NEWLINE:
            return None
        elif t.tipo == TokenID.DEDENT:
            return None
        elif t.tipo == TokenID.EOF:
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
                    and self.pos + 3 < len(self.tokens)
                    and self.tokens[self.pos + 1].tipo == TokenID.DOT
                    and self.tokens[self.pos + 2].tipo == TokenID.IDENTIFIER
                    and self.tokens[self.pos + 3].tipo == TokenID.ASSIGN):
                return self._parsear_asignacion_campo()
            return self._parsear_expr_o_recuperar()

    def _parsear_def_funcion(self) -> Optional[DefinicionFuncion]:
        if self._esperar(TokenID.FUNCTION) is None:
            self._sincronizar(_SYNC_TOP)
            return None
        tok_nombre = self._esperar(TokenID.IDENTIFIER)
        if tok_nombre is None:
            self._sincronizar(_SYNC_TOP)
            return None
        if self._esperar(TokenID.LPAREN) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        params: List[Parametro] = []
        if self._mirar().tipo != TokenID.RPAREN:
            es_trans = self._posible(TokenID.ARROW) is not None
            tok_nombre_param = self._esperar(TokenID.IDENTIFIER)
            if tok_nombre_param is None:
                self._sincronizar(_SYNC_STMT)
                return None
            self._esperar(TokenID.COLON)
            tipo = self._parsear_tipo_parametro()
            params.append(Parametro(nombre=tok_nombre_param.valor, tipo=tipo, es_transferencia=es_trans))
            while self._mirar().tipo == TokenID.COMMA:
                self._avanzar()
                es_trans = self._posible(TokenID.ARROW) is not None
                tok_nombre_param = self._esperar(TokenID.IDENTIFIER)
                if tok_nombre_param is None:
                    break
                self._esperar(TokenID.COLON)
                tipo = self._parsear_tipo_parametro()
                params.append(Parametro(nombre=tok_nombre_param.valor, tipo=tipo, es_transferencia=es_trans))
        if self._esperar(TokenID.RPAREN) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        if self._esperar(TokenID.ARROW) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        tok_retorno = self._esperar(TokenID.IDENTIFIER)
        if tok_retorno is None:
            self._sincronizar(_SYNC_STMT)
            return None
        if self._esperar(TokenID.COLON) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        # --- parsear bloques de contrato opcionales (requiere / garantiza) ---
        # Primero consumir el NEWLINE + INDENT del cuerpo de la función
        requiere: List[Nodo] = []
        garantiza: List[Nodo] = []
        # Saltamos NEWLINE
        if self._mirar().tipo == TokenID.NEWLINE:
            self._avanzar()
        # Entramos al INDENT del cuerpo
        if self._mirar().tipo == TokenID.INDENT:
            self._avanzar()  # consume INDENT
            # Detectar bloques de contrato opcionales dentro del cuerpo
            while self._mirar().tipo in (TokenID.REQUIERE, TokenID.GARANTIZA):
                tok_contrato = self._mirar()
                self._avanzar()   # consume 'requiere' o 'garantiza'
                if self._esperar(TokenID.COLON) is None:
                    self._sincronizar(_SYNC_STMT)
                    break
                exprs = []
                # Saltar NEWLINE del contrato de una sola línea
                while self._mirar().tipo == TokenID.NEWLINE:
                    self._avanzar()
                # Parsear las expresiones del contrato (pueden venir en la misma
                # línea o en un sub-bloque indentado)
                if self._mirar().tipo == TokenID.INDENT:
                    self._avanzar()
                    while self._mirar().tipo not in (TokenID.DEDENT, TokenID.EOF):
                        if self._mirar().tipo == TokenID.NEWLINE:
                            self._avanzar()
                            continue
                        e = self._parsear_expresion()
                        if e:
                            exprs.append(e)
                    if self._mirar().tipo == TokenID.DEDENT:
                        self._avanzar()
                else:
                    # Contrato de una sola expresión en la misma línea
                    while self._mirar().tipo not in (TokenID.NEWLINE, TokenID.DEDENT, TokenID.EOF):
                        e = self._parsear_expresion()
                        if e:
                            exprs.append(e)
                        else:
                            break
                    if self._mirar().tipo == TokenID.NEWLINE:
                        self._avanzar()
                if tok_contrato.tipo == TokenID.REQUIERE:
                    requiere = exprs
                else:
                    garantiza = exprs
            # Parsear el cuerpo real de la función (estamos dentro del INDENT)
            cuerpo: List[Nodo] = []
            while self._mirar().tipo not in (TokenID.DEDENT, TokenID.EOF):
                stmt = self._parsear_sentencia()
                if stmt is not None:
                    cuerpo.append(stmt)
                else:
                    self._avanzar()
            if self._mirar().tipo == TokenID.DEDENT:
                self._avanzar()  # consume DEDENT del cuerpo
        else:
            cuerpo = []

        return DefinicionFuncion(
            nombre=tok_nombre.valor,
            parametros=params,
            tipo_retorno=tok_retorno.valor,
            requiere=requiere,
            garantiza=garantiza,
            cuerpo=cuerpo,
            linea=tok_nombre.linea,
            columna=tok_nombre.columna,
        )

    def _parsear_si(self) -> Optional[SentenciaSi]:
        tok_si = self._esperar(TokenID.IF)
        if tok_si is None:
            self._sincronizar(_SYNC_STMT)
            return None
        condicion = self._parsear_expresion()
        if self._esperar(TokenID.COLON) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        cuerpo = self._parsear_bloque() or []
        cuerpo_sino = None
        if self._mirar().tipo == TokenID.ELSE:
            self._avanzar()
            if self._esperar(TokenID.COLON) is None:
                self._sincronizar(_SYNC_STMT)
            else:
                cuerpo_sino = self._parsear_bloque() or []
        return SentenciaSi(
            condicion=condicion,
            cuerpo=cuerpo,
            cuerpo_sino=cuerpo_sino,
            linea=tok_si.linea,
            columna=tok_si.columna,
        )

    def _parsear_lanzar(self) -> Optional[SentenciaLanzar]:
        tok_spawn = self._esperar(TokenID.SPAWN)
        if tok_spawn is None:
            return None
        llamada = self._parsear_llamada()
        return SentenciaLanzar(
            llamada=llamada,
            linea=tok_spawn.linea,
            columna=tok_spawn.columna,
        )

    def _parsear_retornar(self) -> SentenciaRetornar:
        tok_ret = self._avanzar()
        expr = None
        es_transferencia = False
        if self._mirar().tipo not in (TokenID.NEWLINE, TokenID.DEDENT, TokenID.EOF):
            if self._mirar().tipo == TokenID.ARROW:
                self._avanzar()
                es_transferencia = True
            expr = self._parsear_expresion()
        return SentenciaRetornar(
            expr=expr,
            es_transferencia=es_transferencia,
            linea=tok_ret.linea,
            columna=tok_ret.columna,
        )

    def _parsear_escuchar(self) -> Optional[SentenciaEscuchar]:
        tok_listen = self._esperar(TokenID.LISTEN)
        if tok_listen is None:
            return None
        canal = self._parsear_expresion()
        if self._esperar(TokenID.ARROW) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        respuesta = self._parsear_llamada()
        return SentenciaEscuchar(
            canal=canal,
            respuesta=respuesta,
            linea=tok_listen.linea,
            columna=tok_listen.columna,
        )

    def _parsear_mientras(self) -> Optional[SentenciaMientras]:
        tok_mientras = self._esperar(TokenID.WHILE)
        if tok_mientras is None:
            return None
        condicion = self._parsear_expresion()
        if self._esperar(TokenID.COLON) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        cuerpo = self._parsear_bloque() or []
        return SentenciaMientras(
            condicion=condicion,
            cuerpo=cuerpo,
            linea=tok_mientras.linea,
            columna=tok_mientras.columna,
        )

    def _parsear_romper(self) -> Optional[SentenciaRomper]:
        tok = self._avanzar()
        return SentenciaRomper(linea=tok.linea, columna=tok.columna)

    def _parsear_siguiente(self) -> Optional[SentenciaSiguiente]:
        tok = self._avanzar()
        return SentenciaSiguiente(linea=tok.linea, columna=tok.columna)

    def _parsear_inseguro(self) -> Optional[BloqueInseguro]:
        if self._esperar(TokenID.INSEGURO) is None:
            return None
        if self._esperar(TokenID.COLON) is None:
            return None
        cuerpo = self._parsear_bloque() or []
        return BloqueInseguro(cuerpo=cuerpo)

    def _parsear_importar_c(self) -> Optional[ImportarC]:
        if self._esperar(TokenID.IMPORTAR_C) is None:
            return None
        tok_ruta = self._esperar(TokenID.STRING)
        if tok_ruta is None:
            self._sincronizar(_SYNC_TOP)
            return None
        ruta = tok_ruta.valor
        es_sistema = ruta.startswith('<') and ruta.endswith('>')
        if es_sistema:
            ruta = ruta[1:-1]
        return ImportarC(ruta=ruta, es_sistema=es_sistema)

    def _parsear_declaracion_externa(self) -> Optional[DeclaracionExterna]:
        if self._esperar(TokenID.EXTERNO) is None:
            return None
        if self._esperar(TokenID.FUNCTION) is None:
            self._sincronizar(_SYNC_TOP)
            return None
        tok_nombre = self._esperar(TokenID.IDENTIFIER)
        if tok_nombre is None:
            self._sincronizar(_SYNC_TOP)
            return None
        if self._esperar(TokenID.LPAREN) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        params: List[Parametro] = []
        if self._mirar().tipo != TokenID.RPAREN:
            es_trans = self._posible(TokenID.ARROW) is not None
            tok_nombre_param = self._esperar(TokenID.IDENTIFIER)
            if tok_nombre_param is None:
                self._sincronizar(_SYNC_STMT)
                return None
            self._esperar(TokenID.COLON)
            tok_tipo = self._esperar(TokenID.IDENTIFIER)
            tipo = tok_tipo.valor if tok_tipo else 'int'
            if self._mirar().tipo == TokenID.STAR:
                self._avanzar()
                tipo += '*'
            params.append(Parametro(nombre=tok_nombre_param.valor, tipo=tipo, es_transferencia=es_trans))
            while self._mirar().tipo == TokenID.COMMA:
                self._avanzar()
                es_trans = self._posible(TokenID.ARROW) is not None
                tok_nombre_param = self._esperar(TokenID.IDENTIFIER)
                if tok_nombre_param is None:
                    break
                self._esperar(TokenID.COLON)
                tok_tipo = self._esperar(TokenID.IDENTIFIER)
                tipo = tok_tipo.valor if tok_tipo else 'int'
                if self._mirar().tipo == TokenID.STAR:
                    self._avanzar()
                    tipo += '*'
                params.append(Parametro(nombre=tok_nombre_param.valor, tipo=tipo, es_transferencia=es_trans))
        if self._esperar(TokenID.RPAREN) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        if self._esperar(TokenID.ARROW) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        tok_retorno = self._esperar(TokenID.IDENTIFIER)
        if tok_retorno is None:
            self._sincronizar(_SYNC_STMT)
            return None
        return DeclaracionExterna(
            nombre=tok_nombre.valor,
            parametros=params,
            tipo_retorno=tok_retorno.valor,
            linea=tok_nombre.linea,
            columna=tok_nombre.columna,
        )

    def _parsear_constante(self) -> Optional[StmtConstante]:
        if self._esperar(TokenID.CONSTANTE) is None:
            return None
        tok_nombre = self._esperar(TokenID.IDENTIFIER)
        if tok_nombre is None:
            self._sincronizar(_SYNC_STMT)
            return None
        tipo: str = ''
        if self._posible(TokenID.COLON) is not None:
            tok_tipo = self._esperar(TokenID.IDENTIFIER)
            tipo = tok_tipo.valor if tok_tipo else ''
        if self._esperar(TokenID.ASSIGN) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        valor = self._parsear_expresion()
        if valor is None:
            self._sincronizar(_SYNC_STMT)
            return None
        return StmtConstante(
            nombre=tok_nombre.valor,
            tipo=tipo,
            valor=valor,
            linea=tok_nombre.linea,
            columna=tok_nombre.columna,
        )

    def _parsear_importar(self) -> Optional[SentenciaImportar]:
        tok_import = self._esperar(TokenID.IMPORT)
        if tok_import is None:
            return None
        primera_parte = self._esperar(TokenID.IDENTIFIER)
        if primera_parte is None:
            self._sincronizar(_SYNC_STMT)
            return None
        ruta = primera_parte.valor
        while self._mirar().tipo == TokenID.DOT:
            self._avanzar()
            parte = self._esperar(TokenID.IDENTIFIER)
            if parte is None:
                break
            ruta += '.' + parte.valor
        return SentenciaImportar(
            ruta=ruta,
            linea=tok_import.linea,
            columna=tok_import.columna,
        )

    def _parsear_asignacion(self) -> AsignacionVariable:
        tok_id = self._avanzar()
        self._esperar(TokenID.ASSIGN)
        # Detectar recepción de canal: resultado = c ->
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
            return LiteralNumero(valor=1, linea=t.linea, columna=t.columna)
        if t.tipo == TokenID.FALSE:
            self._avanzar()
            return LiteralNumero(valor=0, linea=t.linea, columna=t.columna)
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

    def _parsear_def_estructura(self) -> Optional[DefinicionEstructura]:
        if self._esperar(TokenID.STRUCT) is None:
            self._sincronizar(_SYNC_TOP)
            return None
        tok_nombre = self._esperar(TokenID.IDENTIFIER)
        if tok_nombre is None:
            self._sincronizar(_SYNC_TOP)
            return None
        if self._esperar(TokenID.COLON) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        if self._esperar(TokenID.NEWLINE) is None:
            self._sincronizar(_SYNC_BLOCK)
            return None
        if self._esperar(TokenID.INDENT) is None:
            self._sincronizar(_SYNC_BLOCK)
            return None
        campos: List[Parametro] = []
        while self._mirar().tipo not in (TokenID.DEDENT, TokenID.EOF):
            if self._mirar().tipo == TokenID.NEWLINE:
                self._avanzar()
                continue
            tok_campo = self._esperar(TokenID.IDENTIFIER)
            if tok_campo is None:
                self._sincronizar(_SYNC_BLOCK)
                break
            if self._esperar(TokenID.COLON) is None:
                self._sincronizar(_SYNC_BLOCK)
                break
            tok_tipo = self._esperar(TokenID.IDENTIFIER)
            if tok_tipo is None:
                self._sincronizar(_SYNC_BLOCK)
                break
            campos.append(Parametro(nombre=tok_campo.valor, tipo=tok_tipo.valor))
            if self._mirar().tipo == TokenID.NEWLINE:
                self._avanzar()
        if self._mirar().tipo != TokenID.EOF:
            self._esperar(TokenID.DEDENT)
        return DefinicionEstructura(
            nombre=tok_nombre.valor,
            campos=campos,
            linea=tok_nombre.linea,
            columna=tok_nombre.columna,
        )

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

    def _parsear_coincidir(self) -> Optional[NodoCoincidir]:
        tok_coincidir = self._esperar(TokenID.MATCH)
        if tok_coincidir is None:
            self._sincronizar(_SYNC_STMT)
            return None
        
        # a) Consumir la expresión objetivo
        expresion = self._parsear_expresion()
        
        # b) Exigir TOKEN_COLON (:)
        if self._esperar(TokenID.COLON) is None:
            self.diag.reportar(ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN, self._mirar(),
                               esperado=':', encontrado=self._mirar().tipo.name)
            self._sincronizar(_SYNC_STMT)
            return None
        
        # c) Exigir TOKEN_NEWLINE seguido de TOKEN_INDENT
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
        
        # d) Iterar consumiendo los patrones
        casos: List[NodoCaso] = []
        while self._mirar().tipo not in (TokenID.DEDENT, TokenID.EOF):
            # Consumir NEWLINE si está presente al inicio de cada caso
            if self._mirar().tipo == TokenID.NEWLINE:
                self._avanzar()
                continue
            
            # Parsear patrón: identificador + paréntesis
            tok_patron = self._esperar(TokenID.IDENTIFIER)
            if tok_patron is None:
                self._sincronizar(_SYNC_BLOCK)
                break
            
            nombre_patron = tok_patron.valor
            
            # Exigir LPAREN
            if self._esperar(TokenID.LPAREN) is None:
                self.diag.reportar(ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN, self._mirar(),
                                   esperado='(', encontrado=self._mirar().tipo.name)
                self._sincronizar(_SYNC_BLOCK)
                break
            
            # Consumir identificador dentro del paréntesis (ej. v en ok(v))
            tok_var = self._esperar(TokenID.IDENTIFIER)
            if tok_var is None:
                self._sincronizar(_SYNC_BLOCK)
                break
            
            var_patron = tok_var.valor
            
            # Exigir RPAREN
            if self._esperar(TokenID.RPAREN) is None:
                self.diag.reportar(ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN, self._mirar(),
                                   esperado=')', encontrado=self._mirar().tipo.name)
                self._sincronizar(_SYNC_BLOCK)
                break
            
            # Construir string del patrón completo (ej. "ok(v)")
            patron_completo = f"{nombre_patron}({var_patron})"
            
            # Exigir TOKEN_FLECHA (=>)
            if self._esperar(TokenID.ARROW_RIGHT) is None:
                self.diag.reportar(ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN, self._mirar(),
                                   esperado='=>', encontrado=self._mirar().tipo.name)
                self._sincronizar(_SYNC_BLOCK)
                break
            
            # e) Parsear el bloque de sentencias del caso
            cuerpo_caso: List[Nodo] = []
            while self._mirar().tipo not in (TokenID.NEWLINE, TokenID.DEDENT, TokenID.EOF):
                stmt = self._parsear_sentencia()
                if stmt is not None:
                    cuerpo_caso.append(stmt)
                else:
                    self._avanzar()
            
            # Crear NodoCaso
            caso = NodoCaso(
                patron=patron_completo,
                cuerpo=cuerpo_caso,
                linea=tok_patron.linea,
                columna=tok_patron.columna,
            )
            casos.append(caso)
        
        # e) Consumir TOKEN_DEDENT final
        if self._mirar().tipo != TokenID.EOF:
            self._esperar(TokenID.DEDENT)
        
        return NodoCoincidir(
            expresion=expresion,
            casos=casos,
            linea=tok_coincidir.linea,
            columna=tok_coincidir.columna,
        )

    # ------------------------------------------------------------------
    # Canales: envío y recepción
    # ------------------------------------------------------------------

    def _parsear_enviar_canal(self) -> Optional[SentenciaEnviarCanal]:
        """canal <- valor   → SentenciaEnviarCanal"""
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
        """var = canal ->   → ExprRecibirCanal  (llamado desde _parsear_asignacion)"""
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

    # ------------------------------------------------------------------
    # Bloques de expresiones para contratos (requiere / garantiza)
    # ------------------------------------------------------------------

    def _parsear_bloque_expresiones(self) -> List[Nodo]:
        """Parsea un bloque indentado de expresiones (una por línea)."""
        nodos: List[Nodo] = []
        if self._mirar().tipo == TokenID.NEWLINE:
            self._avanzar()
        if self._mirar().tipo != TokenID.INDENT:
            # contrato de una sola línea (sin bloque indentado)
            expr = self._parsear_expresion()
            if expr:
                nodos.append(expr)
            return nodos
        self._avanzar()   # consume INDENT
        while self._mirar().tipo not in (TokenID.DEDENT, TokenID.EOF):
            if self._mirar().tipo == TokenID.NEWLINE:
                self._avanzar()
                continue
            expr = self._parsear_expresion()
            if expr:
                nodos.append(expr)
        if self._mirar().tipo == TokenID.DEDENT:
            self._avanzar()   # consume DEDENT
        return nodos

    # ------------------------------------------------------------------
    # Tipos genéricos en parámetros: Canal<entero>, etc.
    # ------------------------------------------------------------------

    def _parsear_tipo_parametro(self) -> str:
        """Lee un tipo de parámetro, soportando genéricos: Canal<entero> o T*"""
        tok_tipo = self._esperar(TokenID.IDENTIFIER)
        if tok_tipo is None:
            return 'int'
        tipo = tok_tipo.valor
        # Genérico: Canal<entero>
        if self._mirar().tipo == TokenID.LESS:
            self._avanzar()   # consume '<'
            partes = [tipo, '<']
            # Consumir hasta '>' o EOF
            while self._mirar().tipo not in (TokenID.GREATER, TokenID.EOF,
                                              TokenID.NEWLINE, TokenID.RPAREN):
                partes.append(str(self._avanzar().valor or ''))
            if self._mirar().tipo == TokenID.GREATER:
                self._avanzar()   # consume '>'
            partes.append('>')
            tipo = ''.join(partes)
        # Puntero: T*
        elif self._mirar().tipo == TokenID.STAR:
            self._avanzar()
            tipo += '*'
        return tipo
