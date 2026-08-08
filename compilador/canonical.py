# ============================================================
# CANONICAL ENCODER / DECODER & PRETTY PRINTER
# ============================================================
import json
from typing import List, Optional, Dict, Any

from compilador.ast_nodes import (
    TokenID, Token, Nodo, Programa, Parametro,
    DefinicionFuncion, DefinicionEstructura, ExprAccesoCampo, AsignacionCampo,
    SentenciaSi, SentenciaLanzar, SentenciaRecuperar,
    SentenciaRetornar, SentenciaEscuchar, SentenciaMientras,
    SentenciaRomper, SentenciaSiguiente,
    SentenciaExpr, AsignacionVariable, LogLlamada, SentenciaImportar,
    DeclaracionVariable, SentenciaDelegar, DeclaracionExport,
    OpBinaria, OpUnaria, LlamadaFuncion, Identificador,
    LiteralNumero, LiteralDecimal, LiteralCadena, ExprTensor, ArgumentoTransferido,
    ExprPropagar, DeclaracionExterna, StmtConstante,
)
from compilador.lexer import DICCIONARIOS, DICCIONARIOS_INVERSO


# ============================================================
# AST PRINTER (DEBUG)
# ============================================================
def imprimir_ast(nodo: Nodo, nivel: int = 0):
    prefijo = "  " * nivel

    if isinstance(nodo, Programa):
        print(f"{prefijo}Programa:")
        for s in nodo.sentencias:
            imprimir_ast(s, nivel + 1)

    elif isinstance(nodo, DefinicionFuncion):
        params = ", ".join(f"{p.nombre}: {p.tipo}" for p in nodo.parametros)
        print(f"{prefijo}Función: {nodo.nombre}({params}) -> {nodo.tipo_retorno}")
        for s in nodo.cuerpo:
            imprimir_ast(s, nivel + 1)

    elif isinstance(nodo, SentenciaSi):
        print(f"{prefijo}Si:")
        imprimir_ast(nodo.condicion, nivel + 1)
        print(f"{prefijo}Cuerpo:")
        for s in nodo.cuerpo:
            imprimir_ast(s, nivel + 1)
        if nodo.cuerpo_sino:
            print(f"{prefijo}Sino:")
            for s in nodo.cuerpo_sino:
                imprimir_ast(s, nivel + 1)

    elif isinstance(nodo, SentenciaLanzar):
        print(f"{prefijo}Lanzar:")
        imprimir_ast(nodo.llamada, nivel + 1)

    elif isinstance(nodo, SentenciaRecuperar):
        print(f"{prefijo}Recuperar (Acción Crítica):")
        imprimir_ast(nodo.accion_critica, nivel + 1)
        print(f"{prefijo}Plan B:")
        imprimir_ast(nodo.plan_b, nivel + 1)

    elif isinstance(nodo, SentenciaRetornar):
        if nodo.expr:
            marca = " ->" if nodo.es_transferencia else ""
            print(f"{prefijo}Retornar{marca}:")
            imprimir_ast(nodo.expr, nivel + 1)
        else:
            print(f"{prefijo}Retornar (vacío)")

    elif isinstance(nodo, SentenciaEscuchar):
        print(f"{prefijo}Escuchar (Canal):")
        imprimir_ast(nodo.canal, nivel + 1)
        print(f"{prefijo}  -> Respuesta:")
        imprimir_ast(nodo.respuesta, nivel + 1)

    elif isinstance(nodo, SentenciaRomper):
        print(f"{prefijo}Romper")

    elif isinstance(nodo, SentenciaSiguiente):
        print(f"{prefijo}Siguiente")

    elif isinstance(nodo, SentenciaMientras):
        print(f"{prefijo}Mientras:")
        imprimir_ast(nodo.condicion, nivel + 1)
        print(f"{prefijo}Cuerpo:")
        for s in nodo.cuerpo:
            imprimir_ast(s, nivel + 1)

    elif isinstance(nodo, SentenciaExpr):
        print(f"{prefijo}Expresión:")
        imprimir_ast(nodo.expr, nivel + 1)

    elif isinstance(nodo, AsignacionVariable):
        print(f"{prefijo}Asignacion: {nodo.nombre} =")
        imprimir_ast(nodo.expresion, nivel + 1)

    elif isinstance(nodo, LogLlamada):
        args = ", ".join(_repr_nodo(a) for a in nodo.argumentos)
        print(f"{prefijo}Log: {args}")

    elif isinstance(nodo, OpBinaria):
        print(f"{prefijo}OpBinaria ({nodo.operador}):")
        imprimir_ast(nodo.izquierdo, nivel + 1)
        imprimir_ast(nodo.derecho, nivel + 1)

    elif isinstance(nodo, OpUnaria):
        print(f"{prefijo}OpUnaria ({nodo.operador}):")
        imprimir_ast(nodo.expr, nivel + 1)

    elif isinstance(nodo, LlamadaFuncion):
        args = ", ".join(_repr_nodo(a) for a in nodo.argumentos)
        print(f"{prefijo}Llamada: {nodo.nombre}({args})")

    elif isinstance(nodo, Identificador):
        print(f"{prefijo}ID: {nodo.nombre}")

    elif isinstance(nodo, LiteralNumero):
        print(f"{prefijo}Número: {nodo.valor}")

    elif isinstance(nodo, ExprTensor):
        print(f"{prefijo}Tensor(filas:")
        imprimir_ast(nodo.filas, nivel + 1)
        print(f"{prefijo}  columnas:")
        imprimir_ast(nodo.columnas, nivel + 1)

    elif isinstance(nodo, ExprPropagar):
        print(f"{prefijo}Propagar (?):")
        imprimir_ast(nodo.expresion, nivel + 1)

    elif isinstance(nodo, ArgumentoTransferido):
        print(f"{prefijo}Transferido:")
        imprimir_ast(nodo.expr, nivel + 1)

    elif isinstance(nodo, ExprAccesoCampo):
        print(f"{prefijo}Acceso Campo:")
        imprimir_ast(nodo.objeto, nivel + 1)
        print(f"{prefijo}  .{nodo.nombre_campo}")

    elif isinstance(nodo, LiteralCadena):
        print(f"{prefijo}Cadena: \"{nodo.valor}\"")


def _repr_nodo(n: Nodo) -> str:
    if isinstance(n, Identificador):
        return n.nombre
    if isinstance(n, LiteralNumero):
        return str(n.valor)
    if isinstance(n, LiteralCadena):
        return f'"{n.valor}"'
    if isinstance(n, LlamadaFuncion):
        args = ", ".join(_repr_nodo(a) for a in n.argumentos)
        return f"{n.nombre}({args})"
    if isinstance(n, OpBinaria):
        return f"({_repr_nodo(n.izquierdo)} {n.operador} {_repr_nodo(n.derecho)})"
    if isinstance(n, OpUnaria):
        return f"({n.operador}{_repr_nodo(n.expr)})"
    if isinstance(n, ExprTensor):
        return f"tensor({_repr_nodo(n.filas)}, {_repr_nodo(n.columnas)})"
    if isinstance(n, ExprPropagar):
        return f"{_repr_nodo(n.expresion)}?"
    if isinstance(n, ArgumentoTransferido):
        return f"->{_repr_nodo(n.expr)}"
    return "?"


# ============================================================
# CANONICAL ENCODER / DECODER
# ============================================================
def _nodo_a_dict(nodo: Nodo) -> dict:
    d = {"_tipo": type(nodo).__name__}
    for campo, valor in nodo.__dict__.items():
        if campo in ('linea', 'columna'):
            continue
        if valor is None:
            continue
        if isinstance(valor, Nodo):
            d[campo] = _nodo_a_dict(valor)
        elif isinstance(valor, list):
            processed = []
            for v in valor:
                if isinstance(v, Nodo):
                    processed.append(_nodo_a_dict(v))
                elif isinstance(v, Parametro):
                    processed.append({"nombre": v.nombre, "tipo": v.tipo})
                else:
                    processed.append(v)
            d[campo] = processed
        elif isinstance(valor, Parametro):
            d[campo] = {"nombre": valor.nombre, "tipo": valor.tipo, "es_transferencia": valor.es_transferencia}
        else:
            d[campo] = valor
    return d


def _dict_a_nodo(d: dict) -> Nodo:
    tipo = d["_tipo"]
    cls = globals().get(tipo)
    if cls is None:
        cls = getattr(__import__('compilador.ast_nodes', fromlist=[tipo]), tipo)
    kwargs = {}
    for campo, valor in d.items():
        if campo == "_tipo":
            continue
        if isinstance(valor, dict) and "_tipo" in valor:
            kwargs[campo] = _dict_a_nodo(valor)
        elif isinstance(valor, list):
            processed = []
            for v in valor:
                if isinstance(v, dict) and "_tipo" in v:
                    processed.append(_dict_a_nodo(v))
                elif isinstance(v, dict) and "nombre" in v and "tipo" in v:
                    processed.append(Parametro(**v))
                else:
                    processed.append(v)
            kwargs[campo] = processed
        elif isinstance(valor, dict) and "nombre" in valor and "tipo" in valor:
            kwargs[campo] = Parametro(**valor)
        else:
            kwargs[campo] = valor
    return cls(**kwargs)


def ast_a_canonico(programa: Programa) -> str:
    data = {
        "synapse": "2.0",
        "ast": _nodo_a_dict(programa),
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def canonico_a_ast(json_str: str) -> Programa:
    data = json.loads(json_str)
    if data.get("synapse") != "2.0":
        raise ValueError("Formato canónico no reconocido")
    return _dict_a_nodo(data["ast"])


# ============================================================
# PRETTY PRINTER MULTILENGUAJE
# ============================================================
def _token_a_palabra(tid: TokenID, dicc_inv: Dict[TokenID, str]) -> str:
    return dicc_inv.get(tid, tid.name.lower())


def ast_a_texto(programa: Programa, idioma: str = 'es') -> str:
    if idioma not in DICCIONARIOS_INVERSO:
        raise ValueError(f"Idioma '{idioma}' no soportado para pretty-print")
    dicc_inv = DICCIONARIOS_INVERSO[idioma]
    lineas: List[str] = [f"#lang: {idioma}"]

    def _render_expr(nodo: Optional[Nodo], dicc_inv: Dict[TokenID, str]) -> str:
        if nodo is None:
            return ""
        if isinstance(nodo, LiteralNumero):
            return str(nodo.valor)
        if isinstance(nodo, LiteralCadena):
            return f'"{nodo.valor}"'
        if isinstance(nodo, Identificador):
            return nodo.nombre
        if isinstance(nodo, OpBinaria):
            izq = _render_expr(nodo.izquierdo, dicc_inv)
            der = _render_expr(nodo.derecho, dicc_inv)
            return f"{izq} {nodo.operador} {der}"
        if isinstance(nodo, OpUnaria):
            return f"{nodo.operador}{_render_expr(nodo.expr, dicc_inv)}"
        if isinstance(nodo, LlamadaFuncion):
            args = ", ".join(_render_expr(a, dicc_inv) for a in nodo.argumentos)
            return f"{nodo.nombre}({args})"
        if isinstance(nodo, ExprTensor):
            filas = _render_expr(nodo.filas, dicc_inv)
            cols = _render_expr(nodo.columnas, dicc_inv)
            return f"tensor({filas}, {cols})"
        if isinstance(nodo, ArgumentoTransferido):
            return f"->{_render_expr(nodo.expr, dicc_inv)}"
        if isinstance(nodo, ExprAccesoCampo):
            return f"{_render_expr(nodo.objeto, dicc_inv)}.{nodo.nombre_campo}"
        if isinstance(nodo, ExprPropagar):
            return f"{_render_expr(nodo.expresion, dicc_inv)}?"
        return "?"

    def _render_nodo(nodo: Nodo, indent: int = 0) -> List[str]:
        prefijo = "    " * indent
        lines: List[str] = []

        if isinstance(nodo, DefinicionFuncion):
            params = ", ".join(
                f"{'-> ' if p.es_transferencia else ''}{p.nombre}: {p.tipo}"
                for p in nodo.parametros
            )
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.FUNCION, dicc_inv)} {nodo.nombre}({params}) -> {nodo.tipo_retorno}:")
            for s in nodo.cuerpo:
                lines.extend(_render_nodo(s, indent + 1))

        elif isinstance(nodo, SentenciaSi):
            cond = _render_expr(nodo.condicion, dicc_inv)
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.SI, dicc_inv)} {cond}:")
            for s in nodo.cuerpo:
                lines.extend(_render_nodo(s, indent + 1))
            if nodo.cuerpo_sino:
                lines.append(f"{prefijo}{_token_a_palabra(TokenID.SINO, dicc_inv)}:")
                for s in nodo.cuerpo_sino:
                    lines.extend(_render_nodo(s, indent + 1))

        elif isinstance(nodo, SentenciaMientras):
            cond = _render_expr(nodo.condicion, dicc_inv)
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.MIENTRAS, dicc_inv)} {cond}:")
            for s in nodo.cuerpo:
                lines.extend(_render_nodo(s, indent + 1))

        elif isinstance(nodo, SentenciaRomper):
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.ROMPER, dicc_inv)}")

        elif isinstance(nodo, SentenciaSiguiente):
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.SIGUIENTE, dicc_inv)}")

        elif isinstance(nodo, SentenciaLanzar):
            llam = _render_expr(nodo.llamada, dicc_inv)
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.LANZAR, dicc_inv)} {llam}")

        elif isinstance(nodo, SentenciaRecuperar):
            acc = _render_expr(nodo.accion_critica, dicc_inv)
            plan = _render_expr(nodo.plan_b, dicc_inv)
            lines.append(f"{prefijo}{acc} {_token_a_palabra(TokenID.RECUPERAR, dicc_inv)}: {plan}")

        elif isinstance(nodo, SentenciaRetornar):
            if nodo.expr:
                marca = " ->" if nodo.es_transferencia else ""
                expr_str = _render_expr(nodo.expr, dicc_inv)
                lines.append(f"{prefijo}{_token_a_palabra(TokenID.RETORNAR, dicc_inv)}{marca} {expr_str}")
            else:
                lines.append(f"{prefijo}{_token_a_palabra(TokenID.RETORNAR, dicc_inv)}")

        elif isinstance(nodo, SentenciaEscuchar):
            canal = _render_expr(nodo.canal, dicc_inv)
            resp = _render_expr(nodo.respuesta, dicc_inv)
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.ESCUCHAR, dicc_inv)} {canal} -> {resp}")

        elif isinstance(nodo, SentenciaExpr):
            expr_str = _render_expr(nodo.expr, dicc_inv)
            lines.append(f"{prefijo}{expr_str}")

        elif isinstance(nodo, AsignacionVariable):
            expr_str = _render_expr(nodo.expresion, dicc_inv)
            lines.append(f"{prefijo}{nodo.nombre} = {expr_str}")

        elif isinstance(nodo, DeclaracionVariable):
            # F1.2c: let IDENT [":" tipo] ["=" expresion] (Manual 2 §2 L134)
            expr_str = _render_expr(nodo.expresion, dicc_inv) if nodo.expresion else ''
            if nodo.tipo:
                head = f"let {nodo.nombre}: {nodo.tipo}"
            else:
                head = f"let {nodo.nombre}"
            lines.append(f"{prefijo}{head}" + (f" = {expr_str}" if expr_str else ""))

        elif isinstance(nodo, SentenciaDelegar):
            expr_str = _render_expr(nodo.expresion, dicc_inv)
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.DELEGAR, dicc_inv)} {expr_str}")

        elif isinstance(nodo, DeclaracionExport):
            fn = nodo.funcion
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.EXPORT, dicc_inv)} ({nodo.destino})")
            if isinstance(fn, DefinicionFuncion):
                lines.extend(_render_nodo(fn, indent))

        elif isinstance(nodo, LogLlamada):
            args = ", ".join(_render_expr(a, dicc_inv) for a in nodo.argumentos)
            lines.append(f"{prefijo}log {args}")

        elif isinstance(nodo, SentenciaImportar):
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.IMPORTAR, dicc_inv)} {nodo.modulo}")

        elif isinstance(nodo, DeclaracionExterna):
            params = ", ".join(f"{p.nombre}: {p.tipo}" for p in nodo.parametros)
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.EXTERNO, dicc_inv)} {nodo.nombre}({params}) -> {nodo.tipo_retorno}")

        elif isinstance(nodo, StmtConstante):
            val = _render_expr(nodo.valor, dicc_inv)
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.CONSTANTE, dicc_inv)} {nodo.nombre}: {nodo.tipo} = {val}")

        elif isinstance(nodo, DefinicionEstructura):
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.ESTRUCTURA, dicc_inv)} {nodo.nombre}:")
            for campo in nodo.campos:
                lines.append(f"{prefijo}    {campo.nombre}: {campo.tipo}")

        else:
            lines.append(f"{prefijo}? {type(nodo).__name__}")

        return lines

    for stmt in programa.sentencias:
        lineas.extend(_render_nodo(stmt))

    return "\n".join(lineas)