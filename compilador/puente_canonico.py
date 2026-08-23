# ============================================================
# puente_canonico.py — SemNodo[] plano → AST tipado del S1 (R90)
# ============================================================
# Convierte el JSON plano que emite syq_frontend.exe
# (syquex/syq_json.syn, esquema "syquex_flat":"2") al Programa
# tipado de compilador/ast_nodes que consume el pipeline S1
# (pipeline.compilar_desde_canonico, Manual 1 §3.1: backend
# compartido tras el traductor; Manual 6 §1.2 ABI v1; Manual 3
# §11.1 mapeo de nodos).
#
# Campos del registro plano:
#   [0] tipo  [1] linea [2] col  [3] valor_int
#   [4] hijo_izq  [5] hijo_der  [6] hermano  [7] reservado
#   [8] span1(bytes|null)  [9] span2(bytes|null)
#
# Nodos sin equivalente en el AST tipado actual levantan
# PuenteError con el id y el nombre canónico (fail-fast, sin
# pérdida silenciosa): INTENTO(54), LISTA_LIT(55), MAPA_LIT(56),
# PARA_EN(57) — cableado backend pendiente, registrado como
# hallazgo H-R90-1.
# ============================================================

import json

from compilador.ast_nodes import (
    Programa, Parametro,
    DefinicionFuncion, DefinicionEstructura, DeclaracionExterna,
    DeclaracionExport, DeclaracionTipo, ConstructorTipo, StmtConstante,
    SentenciaSi, SentenciaMientras, SentenciaLanzar, SentenciaEscuchar,
    SentenciaRetornar, SentenciaExpr, SentenciaRomper, SentenciaSiguiente,
    SentenciaDelegar, DeclaracionVariable, AsignacionVariable,
    AsignacionCampo, OpBinaria, OpUnaria, LlamadaFuncion, Identificador,
    LiteralNumero, LiteralDecimal, LiteralCadena, LiteralBooleano,
    LiteralNulo, ExprAccesoCampo, ExprIndice, ExprPropagar,
    ArgumentoTransferido, NodoCoincidir, NodoCaso,
)

SCHEMA = "2"

NOMBRE_NODO = {
    1: "PROGRAMA", 2: "FUNCION", 3: "SI", 4: "MIENTRAS", 5: "RETORNAR",
    6: "EXPR", 7: "ASIGNACION", 8: "IDENTIFICADOR", 9: "NUMERO",
    10: "DECIMAL", 11: "CADENA_LIT", 12: "BINARIA", 13: "UNARIA",
    14: "LLAMADA", 15: "PARAMETRO", 16: "ESTRUCTURA", 17: "IMPORTAR",
    18: "LANZAR", 19: "ESCUCHAR", 20: "ROMPER", 21: "SIGUIENTE",
    22: "BOOLEANO", 23: "CONSTANTE", 26: "EXTERNO", 29: "INDICE",
    30: "TRANSFERIDO", 31: "ACCESO_CAMPO", 38: "COINCIDIR", 39: "CASO",
    46: "CONTRATO", 47: "NULO", 48: "LET", 49: "DELEGAR", 50: "EXPORT",
    51: "DECLARACION_TIPO", 52: "CONSTRUCTOR", 53: "PROPAGAR",
}

NO_SOPORTADOS = {
    54: "INTENTO (multi-sentencia; backend pendiente H-R90-1)",
    55: "LISTA_LIT (backend Fase 24 lib/lista)",
    56: "MAPA_LIT (backend Fase 24 lib/mapa)",
    57: "PARA_EN (cableado backend pendiente H-R90-1)",
}

# Códigos de operador de syquex/expr.syn (fallback cuando el lexema no
# quedó en slot1, p. ej. binarias del desugar para-rango).
CODIGO_OPS = {
    100: "y", 101: "o",
    200: ">", 201: "<", 202: "==", 203: "!=", 204: "<=", 205: ">=",
    300: "+", 301: "-",
    400: "*", 401: "/", 402: "%",
}


class PuenteError(Exception):
    pass


def cargar_flat(ruta_json: str) -> dict:
    with open(ruta_json, "r", encoding="utf-8") as f:
        flat = json.load(f)
    if flat.get("syquex_flat") != SCHEMA:
        raise PuenteError(
            f"esquema syquex_flat={flat.get('syquex_flat')!r} "
            f"no soportado (esperado {SCHEMA!r})")
    return flat


class _Puente:
    def __init__(self, flat: dict):
        self.nodos = flat["nodos"]

    # ---- helpers de registro ----
    def txt(self, i: int) -> str:
        campo = self.nodos[i][8]
        return "" if campo is None else bytes(campo).decode("utf-8")

    def txt2(self, i: int) -> str:
        campo = self.nodos[i][9]
        return "" if campo is None else bytes(campo).decode("utf-8")

    def tipo(self, i: int) -> int:
        return self.nodos[i][0]

    # ---- cadenas por hermano ([6]) ----
    def cadena(self, idx: int):
        out = []
        while idx > 0:
            if idx >= len(self.nodos):
                raise PuenteError(f"indice fuera de rango en cadena: {idx}")
            n = self._nodo(idx)
            if n is not None:
                out.append(n)
            idx = self.nodos[idx][6]
        return out

    def _parametro(self, i: int) -> Parametro:
        return Parametro(nombre=self.txt(i), tipo=self.txt2(i) or "entero")

    # ---- despacho principal ----
    def _nodo(self, i: int):
        n = self.nodos[i]
        t, vi = n[0], n[3]
        izq, der, extra = n[4], n[5], n[7]
        lin, col = n[1], n[2]

        def con(nodo):
            nodo.linea = lin
            nodo.columna = col
            return nodo

        if t == 1:   # PROGRAMA
            prog = Programa(sentencias=self.cadena(izq))
            return prog
        if t == 2:   # FUNCION
            req, gar = [], []
            if extra > 0 and self.tipo(extra) == 46:   # CONTRATO fusionado
                req = self.cadena(self.nodos[extra][4])
                gar = self.cadena(self.nodos[extra][5])
            return con(DefinicionFuncion(
                nombre=self.txt(i),
                parametros=[self._parametro(p) for p in self.cadena_ids(izq)],
                tipo_retorno=self.txt2(i),
                requiere=req,
                garantiza=gar,
                cuerpo=self.cadena(der)))
        if t == 3:   # SI
            sino = self.cadena(extra) if extra > 0 else None
            return con(SentenciaSi(condicion=self._nodo(izq),
                                   cuerpo=self.cadena(der),
                                   cuerpo_sino=sino))
        if t == 4:   # MIENTRAS (incluye desugar para-rango R87)
            return con(SentenciaMientras(condicion=self._nodo(izq),
                                         cuerpo=self.cadena(der)))
        if t == 5:   # RETORNAR
            return con(SentenciaRetornar(expr=self._nodo_opt(izq),
                                         es_transferencia=bool(vi)))
        if t == 6:   # EXPR
            return con(SentenciaExpr(expr=self._nodo(izq)))
        if t == 7:   # ASIGNACION (despacha por forma del LHS)
            destino = izq
            dt = self.tipo(destino)
            val = self._nodo(der)
            if dt == 31:   # ACCESO_CAMPO
                return con(AsignacionCampo(
                    objeto=self._nodo(self.nodos[destino][4]),
                    nombre_campo=self.txt(destino),
                    expresion=val))
            if dt == 29:   # INDICE
                raise PuenteError(
                    "asignacion indexada (a[i] = ...) sin clase en el AST "
                    "tipado S1 (H-R90-2)")
            return con(AsignacionVariable(nombre=self.txt(destino),
                                          expresion=val))
        if t == 8:
            if der > 0:
                # Tras el fix R90 del postfix, una llamada sobre
                # identificador es NODO_LLAMADA; si esto aparece, el parser
                # regresó a la forma antigua — fallar, no perder args.
                raise PuenteError(
                    "IDENTIFICADOR con argumentos (llamada sin NODO_LLAMADA) "
                    "— regression del parser Syquex")
            return con(Identificador(nombre=self.txt(i)))
        if t == 9:
            return con(LiteralNumero(valor=int(self.txt(i))))
        if t == 10:
            return con(LiteralDecimal(valor=float(self.txt(i))))
        if t == 11:
            return con(LiteralCadena(valor=self.txt(i)))
        if t == 12:   # BINARIA
            op = self.txt(i) or CODIGO_OPS.get(vi, "?")
            return con(OpBinaria(izquierdo=self._nodo(izq), operador=op,
                                 derecho=self._nodo(der)))
        if t == 13:   # UNARIA
            return con(OpUnaria(operador=self.txt(i) or "-",
                                expr=self._nodo(izq)))
        if t == 14:   # LLAMADA (args en hijo_der — convención sq_args)
            return con(LlamadaFuncion(nombre=self.txt(i),
                                      argumentos=self.cadena(der)))
        if t == 15:   # PARAMETRO suelto (miembro de estructura)
            return con(_campo_como_parametro(self, i))
        if t == 16:   # ESTRUCTURA
            campos = [_campo_como_parametro(self, c)
                      for c in self.cadena_ids(izq)]
            return con(DefinicionEstructura(nombre=self.txt(i),
                                            campos=campos))
        if t == 17:
            from compilador.ast_nodes import SentenciaImportar
            return con(SentenciaImportar(ruta=self.txt(i)))
        if t == 18:
            return con(SentenciaLanzar(llamada=self._nodo(izq)))
        if t == 19:
            return con(SentenciaEscuchar(canal=self._nodo(izq),
                                         cuerpo=self.cadena(der)))
        if t == 20:
            return con(SentenciaRomper())
        if t == 21:
            return con(SentenciaSiguiente())
        if t == 22:
            return con(LiteralBooleano(valor=bool(vi)))
        if t == 23:   # CONSTANTE
            return con(StmtConstante(nombre=self.txt(i), tipo='',
                                     valor=self._nodo_opt(der)))
        if t == 26:   # EXTERNO (vi: 0 funcion / 1 estructura / 2 constante)
            if vi == 0:
                return con(DeclaracionExterna(
                    nombre=self.txt(i),
                    parametros=[self._parametro(p)
                                for p in self.cadena_ids(izq)],
                    tipo_retorno=self.txt2(i)))
            if vi == 2:
                return con(StmtConstante(nombre=self.txt(i), tipo='',
                                         valor=self._nodo_opt(der)))
            raise PuenteError("externo estructura sin clase S1 (H-R90-3)")
        if t == 29:
            return con(ExprIndice(expr=self._nodo(izq),
                                  indice=self._nodo(der)))
        if t == 30:
            return con(ArgumentoTransferido(expr=self._nodo(izq)))
        if t == 31:
            if der > 0:
                # llamada a método: lowering requiere tipos (H-R90-5)
                raise PuenteError(
                    "llamada a metodo (obj.metodo(args)) sin lowering de "
                    "call-site — pendiente decision H-R90-5")
            return con(ExprAccesoCampo(objeto=self._nodo(izq),
                                       nombre_campo=self.txt(i)))
        if t in (34, 48):   # DECLARACION / LET
            return con(DeclaracionVariable(nombre=self.txt(i),
                                           tipo=self.txt2(i),
                                           expresion=self._nodo_opt(der)))
        if t == 38:   # COINCIDIR
            casos = []
            for c in self.cadena_ids(der):
                caso = NodoCaso(patron=self.txt(c),
                                cuerpo=self.cadena(self.nodos[c][5]))
                caso.linea = self.nodos[c][1]
                casos.append(caso)
            return con(NodoCoincidir(expresion=self._nodo(izq), casos=casos))
        if t == 47:
            return con(LiteralNulo())
        if t == 49:
            return con(SentenciaDelegar(expresion=self._nodo(izq)))
        if t == 50:   # EXPORT
            return con(DeclaracionExport(destino=self.txt(i),
                                         funcion=self._nodo(izq)))
        if t == 51:   # DECLARACION_TIPO (alias o ADT enumeracion)
            ctors = [ConstructorTipo(nombre=self.txt(c), tipos=[])
                     for c in self.cadena_ids(der)] if vi == 1 else []
            alias = self.txt2(i)
            return con(DeclaracionTipo(nombre=self.txt(i),
                                       tipo_base=alias,
                                       constructores=ctors))
        if t == 52:   # CONSTRUCTOR suelto (fuera de DECL_TIPO)
            return con(ConstructorTipo(nombre=self.txt(i), tipos=[]))
        if t == 53:
            return con(ExprPropagar(expresion=self._nodo(izq)))

        if t in NO_SOPORTADOS:
            raise PuenteError(
                f"NODO_{NO_SOPORTADOS[t]} — sin equivalente en el AST "
                f"tipado S1 ({NO_SOPORTADOS[t].split('(', 1)[-1]}")
        nombre = NOMBRE_NODO.get(t, f"id {t}")
        raise PuenteError(f"nodo canonico no mapeado en el puente: {nombre}")

    def _nodo_opt(self, idx: int):
        return self._nodo(idx) if idx > 0 else None

    def cadena_ids(self, idx: int):
        out = []
        while idx > 0:
            out.append(idx)
            idx = self.nodos[idx][6]
        return out


def _campo_como_parametro(puente: "_Puente", i: int) -> Parametro:
    """Campo de estructura (PARAMETRO fuente) → Parametro tipado."""
    return Parametro(nombre=puente.txt(i), tipo=puente.txt2(i) or "entero")


def plano_a_programa(flat: dict) -> Programa:
    if flat.get("syquex_flat") != SCHEMA:
        raise PuenteError(
            f"esquema syquex_flat={flat.get('syquex_flat')!r} "
            f"no soportado (esperado {SCHEMA!r})")
    p = _Puente(flat)
    prog = p._nodo(flat["raiz"])
    if not isinstance(prog, Programa):
        raise PuenteError("la raiz del flat no es PROGRAMA")
    return prog


def compilar_desde_plano(ruta_json: str) -> Programa:
    return plano_a_programa(cargar_flat(ruta_json))
