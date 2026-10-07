# cumple Manual 1 §6: infraestructura Python del compilador Synapse (regla de hierro del bootstrap)
# cumple Manual 8 4: toolchain de construcción
from typing import List, Optional

from compilador.ast_nodes import (
    TokenID, Token, Nodo,
    OpBinaria, OpUnaria, LlamadaFuncion, Identificador,
    LiteralNumero, LiteralDecimal, LiteralCadena, LiteralBooleano, ExprTensor,
    LiteralNulo, ArgumentoTransferido, ExprCrearCanal,
    ExprObtenerDireccion, ExprDereferencia, ExprAccesoCampo, ExprAsm,
    ExprIndice, ExprPropagar,
)
from compilador.lexer import OPERADORES_BINARIOS
from compilador.diagnostics import ErrorCodes
from compilador.parser_base import ParserBase, _SYNC_EXPR, es_token_identificador, nombre_de_token

# F1.2: constructores ADT del Manual 2 §4.2 en posición de expresión.
_CONSTRUCTORES_ADT: frozenset = frozenset({
    TokenID.OK, TokenID.ERR, TokenID.ALGUN, TokenID.NINGUNO,
})


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
        ops = {TokenID.STAR, TokenID.SLASH, TokenID.MOD}
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
            # Manual 4 §4.2: &mut x (préstamo mutable) vs &x (inmutable)
            es_mutable = False
            if (self._mirar().tipo == TokenID.IDENTIFIER
                    and (self._mirar().valor or '') == 'mut'):
                self._avanzar()
                es_mutable = True
            expr = self._parsear_unario()
            return ExprObtenerDireccion(
                expr=expr,
                es_mutable=es_mutable,
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

    def _parsear_postfijo(self, expr: Nodo) -> Nodo:
        """Postfijos: `.campo`, `[indice]` y `?` (D-6, Manual 3 §7 L331-342).
        El `?` propaga el `err` de un Resultado y desempaqueta el valor `ok`."""
        while self._mirar().tipo in (TokenID.DOT, TokenID.LBRACKET, TokenID.INTERROGACION):
            if self._mirar().tipo == TokenID.DOT:
                self._avanzar()
                tok_campo = self._esperar_identificador()
                if tok_campo is None:
                    break
                # cumple Manual 3 §3 (H-R153-3): `IDENT . IDENT (` → llamada a
                # método (postfijo). Se representa como LlamadaFuncion con el
                # objeto como primer argumento; el emisor resuelve el backend
                # (colecciones stdlib, Manual 3 §5.2). Sin tabla de métodos:
                # inline por tipo de receptor.
                if self._mirar().tipo == TokenID.LPAREN:
                    llamada = self._parsear_llamada(
                        Identificador(nombre=tok_campo.valor or '',
                                      linea=expr.linea, columna=expr.columna))
                    llamada.nombre = f"metodo:{tok_campo.valor or ''}"
                    llamada.argumentos.insert(0, expr)
                    llamada.linea = expr.linea
                    llamada.columna = expr.columna
                    expr = llamada
                    continue
                expr = ExprAccesoCampo(
                    objeto=expr,
                    nombre_campo=tok_campo.valor or tok_campo.tipo.name.lower(),
                    linea=expr.linea,
                    columna=expr.columna,
                )
            elif self._mirar().tipo == TokenID.LBRACKET:
                self._avanzar()  # consume [
                indice = self._parsear_expresion()
                self._esperar(TokenID.RBRACKET)
                expr = ExprIndice(
                    expr=expr,
                    indice=indice,
                    linea=expr.linea,
                    columna=expr.columna,
                )
            else:  # TokenID.INTERROGACION
                tok_q = self._avanzar()
                expr = ExprPropagar(
                    expresion=expr,
                    linea=tok_q.linea,
                    columna=tok_q.columna,
                )
        return expr

    def _parsear_primario(self) -> Nodo:
        t = self._mirar()
        # cumple Manual 2 §12 (ME r184_r185_e2e, H-R181-3): keyword de operador
        # (y/o/no) en posición de OPERANDO = nombre de usuario (`p.y = y`, RHS).
        # En posición de operador `parsear_expr_binaria` los consume ANTES
        # (L29 ops = {AND, OR}); aquí es inequívocamente un identificador. La
        # negación `no` se consume en el bucle unario (L99) antes de llegar aquí.
        if t.tipo in (TokenID.AND, TokenID.OR, TokenID.NOT):
            self._avanzar()
            return Identificador(
                nombre=t.valor or t.tipo.name.lower(),
                linea=t.linea,
                columna=t.columna,
            )
        if t.tipo == TokenID.NUMBER:
            self._avanzar()
            return LiteralNumero(valor=t.valor, linea=t.linea, columna=t.columna)
        if t.tipo == TokenID.FLOAT:
            self._avanzar()
            return LiteralDecimal(valor=t.valor, linea=t.linea, columna=t.columna)
        if t.tipo == TokenID.STRING:
            self._avanzar()
            return LiteralCadena(valor=t.valor, linea=t.linea, columna=t.columna)
        if t.tipo == TokenID.VERDADERO:
            self._avanzar()
            return LiteralBooleano(valor=True, linea=t.linea, columna=t.columna)
        if t.tipo == TokenID.FALSO:
            self._avanzar()
            return LiteralBooleano(valor=False, linea=t.linea, columna=t.columna)
        if t.tipo == TokenID.ASM:
            self._avanzar()
            self._esperar(TokenID.LPAREN)
            expr = self._parsear_expresion()
            self._esperar(TokenID.RPAREN)
            if isinstance(expr, LiteralCadena):
                return ExprAsm(instruccion=expr.valor, linea=t.linea, columna=t.columna)
            return ExprAsm(expr=expr, linea=t.linea, columna=t.columna)
        if t.tipo == TokenID.NULO:
            # F1.2: literal nulo (Manual 2 §4.1) — emitido como la macro `nulo`
            self._avanzar()
            return LiteralNulo(linea=t.linea, columna=t.columna)
        if t.tipo == TokenID.TENSOR:
            # F1.2: tensor(filas, columnas) como expresión (Manual 2 §2 tensor)
            # o `tensor` como nombre de tipo/variable contextual (std/tensor.syn:
            # `rope(tensor: tensor, ...)`); se decide tras consumir el token.
            self._avanzar()
            if self._mirar().tipo == TokenID.LPAREN:
                return self._parsear_tensor(t)
            expr: Nodo = Identificador(nombre='tensor', linea=t.linea, columna=t.columna)
            return self._parsear_postfijo(expr)
        if es_token_identificador(t) or t.tipo == TokenID.CANAL:
            self._avanzar()
            if t.tipo in _CONSTRUCTORES_ADT:
                # F1.2: constructores ADT (ok/err/algun/ninguno) — llamada o
                # identificador (en patrones de coincidir se manejan aparte).
                nombre = t.valor or t.tipo.name.lower()
                if self._mirar().tipo == TokenID.LPAREN:
                    expr = self._parsear_llamada(
                        Identificador(nombre=nombre, linea=t.linea, columna=t.columna))
                else:
                    expr = Identificador(nombre=nombre, linea=t.linea, columna=t.columna)
            elif t.tipo == TokenID.CANAL:
                if self._mirar().tipo == TokenID.LPAREN:
                    expr = self._parsear_crear_canal(t)
                else:
                    expr = Identificador(nombre='canal', linea=t.linea, columna=t.columna)
            else:
                nombre = nombre_de_token(t)
                # cumple Manual 2 §4.3 (H-R153-1): instanciación de colección
                # genérica `Lista<T>()` / `Mapa<K,V>()` — el parser plano
                # rechaza el `<` tras el nombre (misma razón por la que
                # crear_canal<T> necesita rama propia). Se consume la lista de
                # parámetros de tipo y se construye la llamada al constructor
                # del runtime de colecciones (H-R153-2).
                if (nombre in ('Lista', 'Mapa')
                        and self._mirar().tipo == TokenID.LESS):
                    self._avanzar()
                    profundidad = 1
                    partes = []
                    while profundidad > 0:
                        tok = self._mirar()
                        if tok.tipo in (TokenID.EOF, TokenID.NEWLINE):
                            break
                        if tok.tipo == TokenID.LESS:
                            profundidad += 1
                        elif tok.tipo == TokenID.GREATER:
                            profundidad -= 1
                            if profundidad == 0:
                                self._avanzar()
                                break
                        elif tok.tipo == TokenID.COMMA:
                            partes.append(',')
                            self._avanzar()
                            continue
                        partes.append(str(tok.valor or tok.tipo.name.lower()))
                        self._avanzar()
                    args_tipo = ''.join(partes).replace(' ', '')
                    expr = LlamadaFuncion(
                        nombre=f'{nombre}<{args_tipo}>',
                        linea=t.linea,
                        columna=t.columna,
                    )
                    if self._mirar().tipo == TokenID.LPAREN:
                        self._parsear_llamada(expr)
                    return self._parsear_postfijo(expr)
                if nombre == 'tensor' and self._mirar().tipo == TokenID.LPAREN:
                    expr = self._parsear_tensor(t)
                elif self._mirar().tipo == TokenID.LPAREN:
                    expr = self._parsear_llamada(
                        Identificador(nombre=nombre, linea=t.linea, columna=t.columna))
                else:
                    expr = Identificador(nombre=nombre, linea=t.linea, columna=t.columna)
            return self._parsear_postfijo(expr)
        if t.tipo == TokenID.LPAREN:
            self._avanzar()
            expr = self._parsear_expresion()
            self._esperar(TokenID.RPAREN)
            return self._parsear_postfijo(expr)
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
            self._saltar_nueva_linea()
            if self._mirar().tipo == TokenID.ARROW:
                self._avanzar()
                args.append(ArgumentoTransferido(expr=self._parsear_expresion()))
            else:
                args.append(self._parsear_expresion())
            while self._mirar().tipo == TokenID.COMMA:
                self._avanzar()
                self._saltar_nueva_linea()
                if self._mirar().tipo == TokenID.ARROW:
                    self._avanzar()
                    args.append(ArgumentoTransferido(expr=self._parsear_expresion()))
                else:
                    args.append(self._parsear_expresion())
        self._saltar_nueva_linea()
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
        if es_token_identificador(self._mirar()):
            tok_tipo = self._avanzar()
            tipo_contenido = nombre_de_token(tok_tipo)
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
