from typing import List, Optional

from compilador.ast_nodes import (
    TokenID, Nodo, Parametro,
    DefinicionFuncion, DefinicionEstructura,
    SentenciaImportar,
    ImportarC, DeclaracionExterna,
    StmtConstante,
)
from compilador.parser_base import ParserBase, _SYNC_TOP, _SYNC_STMT, _SYNC_BLOCK


class ParserDeclarationsMixin(ParserBase):
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
        requiere: List[Nodo] = []
        garantiza: List[Nodo] = []
        if self._mirar().tipo == TokenID.NEWLINE:
            self._avanzar()
        if self._mirar().tipo == TokenID.INDENT:
            self._avanzar()
            while self._mirar().tipo in (TokenID.REQUIERE, TokenID.GARANTIZA):
                tok_contrato = self._mirar()
                self._avanzar()
                if self._esperar(TokenID.COLON) is None:
                    self._sincronizar(_SYNC_STMT)
                    break
                exprs = []
                while self._mirar().tipo == TokenID.NEWLINE:
                    self._avanzar()
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
            cuerpo: List[Nodo] = []
            while self._mirar().tipo not in (TokenID.DEDENT, TokenID.EOF):
                stmt = self._parsear_sentencia()
                if stmt is not None:
                    cuerpo.append(stmt)
                else:
                    self._avanzar()
            if self._mirar().tipo == TokenID.DEDENT:
                self._avanzar()
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
            tok_campo = self._mirar()
            if tok_campo.tipo in (TokenID.DEDENT, TokenID.EOF, TokenID.COLON):
                break
            self._avanzar()
            campo_nombre = tok_campo.valor
            if not campo_nombre and tok_campo.tipo is not None:
                campo_nombre = tok_campo.tipo.name.lower()
            if not campo_nombre:
                self._sincronizar(_SYNC_BLOCK)
                break
            if self._esperar(TokenID.COLON) is None:
                self._sincronizar(_SYNC_BLOCK)
                break
            tok_tipo = self._mirar()
            if tok_tipo.tipo in (TokenID.DEDENT, TokenID.EOF, TokenID.NEWLINE):
                self._sincronizar(_SYNC_BLOCK)
                break
            self._avanzar()
            tipo_valor = tok_tipo.valor
            if not tipo_valor and tok_tipo.tipo is not None:
                tipo_valor = tok_tipo.tipo.name.lower()
            if not tipo_valor:
                tipo_valor = 'int'
            campos.append(Parametro(nombre=campo_nombre, tipo=tipo_valor))
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
