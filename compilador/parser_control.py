from typing import List, Optional

from compilador.ast_nodes import (
    TokenID, Nodo,
    SentenciaSi, SentenciaLanzar, SentenciaRetornar,
    SentenciaEscuchar, SentenciaMientras, SentenciaPara,
    SentenciaRomper, SentenciaSiguiente,
    BloqueInseguro,
    NodoCaso, NodoCoincidir,
)
from compilador.diagnostics import ErrorCodes
from compilador.parser_base import (
    ParserBase, _SYNC_STMT, _SYNC_BLOCK, es_token_identificador, nombre_de_token,
)


class ParserControlMixin(ParserBase):
    def _parsear_si(self) -> Optional[SentenciaSi]:
        tok_si = self._esperar(TokenID.SI)
        if tok_si is None:
            self._sincronizar(_SYNC_STMT)
            return None
        condicion = self._parsear_expresion()
        if self._esperar(TokenID.COLON) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        if self._mirar().tipo == TokenID.NEWLINE:
            cuerpo = self._parsear_bloque() or []
        else:
            cuerpo = []
            stmt = self._parsear_sentencia()
            if stmt is not None:
                cuerpo.append(stmt)
        cuerpo_sino = None
        if self._mirar().tipo == TokenID.SINO:
            self._avanzar()
            if self._esperar(TokenID.COLON) is None:
                self._sincronizar(_SYNC_STMT)
            else:
                if self._mirar().tipo == TokenID.NEWLINE:
                    cuerpo_sino = self._parsear_bloque() or []
                else:
                    cuerpo_sino = []
                    stmt = self._parsear_sentencia()
                    if stmt is not None:
                        cuerpo_sino.append(stmt)
        return SentenciaSi(
            condicion=condicion,
            cuerpo=cuerpo,
            cuerpo_sino=cuerpo_sino,
            linea=tok_si.linea,
            columna=tok_si.columna,
        )

    def _parsear_lanzar(self) -> Optional[SentenciaLanzar]:
        tok_spawn = self._esperar(TokenID.LANZAR)
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
        tok_listen = self._esperar(TokenID.ESCUCHAR)
        if tok_listen is None:
            return None
        canal = self._parsear_expresion()
        # F3-7: gramatica del Manual 2 L113 — escuchar_canal ::= "escuchar" expresion
        # ":" NEWLINE INDENT bloque DEDENT. La forma antigua `escuchar canal ->
        # callback` NO esta en el manual (se corrige). El bloque recibe con
        # `canal ->` dentro (Manual 5 §4.2: mensaje = mi_canal ->).
        if self._esperar(TokenID.COLON) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        if self._mirar().tipo == TokenID.NEWLINE:
            cuerpo = self._parsear_bloque() or []
        else:
            cuerpo = []
            stmt = self._parsear_sentencia()
            if stmt is not None:
                cuerpo.append(stmt)
        return SentenciaEscuchar(
            canal=canal,
            cuerpo=cuerpo,
            linea=tok_listen.linea,
            columna=tok_listen.columna,
        )

    def _parsear_mientras(self) -> Optional[SentenciaMientras]:
        tok_mientras = self._esperar(TokenID.MIENTRAS)
        if tok_mientras is None:
            return None
        condicion = self._parsear_expresion()
        if self._esperar(TokenID.COLON) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        if self._mirar().tipo == TokenID.NEWLINE:
            cuerpo = self._parsear_bloque() or []
        else:
            cuerpo = []
            stmt = self._parsear_sentencia()
            if stmt is not None:
                cuerpo.append(stmt)
        return SentenciaMientras(
            condicion=condicion,
            cuerpo=cuerpo,
            linea=tok_mientras.linea,
            columna=tok_mientras.columna,
        )

    def _parsear_para(self) -> Optional[SentenciaPara]:
        # R30 (Manual 2 §2.2 L108): bucle_para ::= "para" IDENTIFICADOR "="
        # expresion "mientras" expresion ":" NEWLINE INDENT bloque DEDENT.
        # La actualizacion del contador es responsabilidad del CUERPO
        # (ej: `para i = 0 mientras i < 10: ... i = i + 1`). Antes se parseaba
        # el dialecto C-style `para i = 0; i < n; i = i + 1:` que NO existe en
        # el Manual (desvio H-R29-2 corregido en la auditoria).
        tok_para = self._esperar(TokenID.PARA)
        if tok_para is None:
            return None
        inicializacion = self._parsear_asignacion()
        if self._esperar(TokenID.MIENTRAS) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        condicion = self._parsear_expresion()
        if self._esperar(TokenID.COLON) is None:
            self._sincronizar(_SYNC_STMT)
            return None
        if self._mirar().tipo == TokenID.NEWLINE:
            cuerpo = self._parsear_bloque() or []
        else:
            cuerpo = []
            stmt = self._parsear_sentencia()
            if stmt is not None:
                cuerpo.append(stmt)
        return SentenciaPara(
            inicializacion=inicializacion,
            condicion=condicion,
            incremento=None,
            cuerpo=cuerpo,
            linea=tok_para.linea,
            columna=tok_para.columna,
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

    def _parsear_coincidir(self) -> Optional[NodoCoincidir]:
        tok_coincidir = self._esperar(TokenID.COINCIDIR)
        if tok_coincidir is None:
            self._sincronizar(_SYNC_STMT)
            return None

        expresion = self._parsear_expresion()

        if self._esperar(TokenID.COLON) is None:
            self.diag.reportar(ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN, self._mirar(),
                               esperado=':', encontrado=self._mirar().tipo.name)
            self._sincronizar(_SYNC_STMT)
            return None

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

        casos: List[NodoCaso] = []
        while self._mirar().tipo not in (TokenID.DEDENT, TokenID.EOF):
            if self._mirar().tipo == TokenID.NEWLINE:
                self._avanzar()
                continue

            tok_patron = self._esperar_identificador()
            if tok_patron is None:
                self._sincronizar(_SYNC_BLOCK)
                break

            # F1.2: el patrón puede ser un keyword contextual (ok/err/algun/ninguno)
            nombre_patron = nombre_de_token(tok_patron)

            # Patron con payload: ok(valor) — Manual 2 §2.2
            # Patron nulo (variante sin argumentos): ninguno — Manual 2 §2.4
            var_patron = None
            if self._mirar().tipo == TokenID.LPAREN:
                self._avanzar()
                tok_var = self._esperar_identificador()
                if tok_var is None:
                    self._sincronizar(_SYNC_BLOCK)
                    break
                var_patron = nombre_de_token(tok_var)
                if self._esperar(TokenID.RPAREN) is None:
                    self.diag.reportar(ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN, self._mirar(),
                                       esperado=')', encontrado=self._mirar().tipo.name)
                    self._sincronizar(_SYNC_BLOCK)
                    break

            if var_patron is not None:
                patron_completo = f"{nombre_patron}({var_patron})"
            else:
                patron_completo = nombre_patron

            if self._esperar(TokenID.ARROW_RIGHT) is None:
                self.diag.reportar(ErrorCodes.ERR_SYNTAX_EXPECTED_TOKEN, self._mirar(),
                                   esperado='=>', encontrado=self._mirar().tipo.name)
                self._sincronizar(_SYNC_BLOCK)
                break

            cuerpo_caso: List[Nodo] = []
            if self._mirar().tipo == TokenID.NEWLINE:
                # R22 (Manual 2 §2.4 L124 / Manual 3 L140): caso_coincidir ::=
                # patron "=>" ( sentencia | NEWLINE INDENT bloque DEDENT ) — el
                # cuerpo del caso puede ser un bloque indentado en la línea
                # siguiente (ej. MANUAL 5 §7). Antes solo se aceptaba la forma
                # de una línea y un coincidir anidado daba error de sintaxis
                # (rc=8 nativo / ARROW_RIGHT tras expresión en S1).
                cuerpo_caso = self._parsear_bloque() or []
            else:
                # R22: la forma de una línea termina en NEWLINE/DEDENT/EOF o en
                # el borde del siguiente caso (columna del patrón) — sin el
                # guard, un coincidir anidado de una línea se tragaba el caso
                # siguiente (Token inesperado 'ARROW_RIGHT' tras expresión).
                # NOTA (revisión code-reviewer): el guard de columna es una
                # HEURÍSTICA de indentación (los bloques anidados consumen su
                # propio DEDENT; el borde del caso siguiente se detecta por
                # columna) — asume columnas consistentes (espacios). Paridad
                # con el nativo (nucleo/parser.syn, guard token_columna <= col_c).
                while (self._mirar().tipo not in (TokenID.NEWLINE, TokenID.DEDENT, TokenID.EOF)
                       and self._mirar().columna > tok_patron.columna):
                    stmt = self._parsear_sentencia()
                    if stmt is not None:
                        cuerpo_caso.append(stmt)
                    else:
                        self._avanzar()

            caso = NodoCaso(
                patron=patron_completo,
                cuerpo=cuerpo_caso,
                linea=tok_patron.linea,
                columna=tok_patron.columna,
            )
            casos.append(caso)

        if self._mirar().tipo != TokenID.EOF:
            self._esperar(TokenID.DEDENT)

        return NodoCoincidir(
            expresion=expresion,
            casos=casos,
            linea=tok_coincidir.linea,
            columna=tok_coincidir.columna,
        )
