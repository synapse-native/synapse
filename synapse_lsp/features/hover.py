from typing import Optional
from synapse_lsp.features.store import _obtener_documento


def _nodo_a_texto(expr) -> str:
    from compilador.ast_nodes import (
        LiteralNumero, LiteralDecimal, LiteralCadena, Identificador,
        OpBinaria, OpUnaria, LlamadaFuncion, ExprAccesoCampo,
    )
    if isinstance(expr, LiteralNumero):
        return str(expr.valor)
    if isinstance(expr, LiteralDecimal):
        return str(expr.valor)
    if isinstance(expr, LiteralCadena):
        return f'"{expr.valor}"'
    if isinstance(expr, Identificador):
        return expr.nombre
    if isinstance(expr, OpBinaria):
        izq = _nodo_a_texto(expr.izquierdo)
        der = _nodo_a_texto(expr.derecho)
        return f"({izq} {expr.operador} {der})"
    if isinstance(expr, OpUnaria):
        return f"({expr.operador}{_nodo_a_texto(expr.expr)})"
    if isinstance(expr, LlamadaFuncion):
        args = ", ".join(_nodo_a_texto(a) for a in expr.argumentos)
        return f"{expr.nombre}({args})"
    if isinstance(expr, ExprAccesoCampo):
        return f"{_nodo_a_texto(expr.objeto)}.{expr.nombre_campo}"
    return "?"


def _construir_hover_funcion(fn) -> Optional[dict]:
    from compilador.ast_nodes import DefinicionFuncion
    if not isinstance(fn, DefinicionFuncion):
        return None

    params_str = ", ".join(f"{p.nombre}: {p.tipo}" for p in fn.parametros)
    ret = fn.tipo_retorno if fn.tipo_retorno else "nulo"

    lines = ["```synapse"]
    lines.append(f"funcion {fn.nombre}({params_str}) -> {ret}")

    if fn.requiere:
        lines.append("    requiere:")
        for r in fn.requiere:
            lines.append(f"        {_nodo_a_texto(r)}")

    if fn.garantiza:
        lines.append("    garantiza:")
        for g in fn.garantiza:
            lines.append(f"        {_nodo_a_texto(g)}")

    lines.append("```")
    markdown = "\n".join(lines)

    return {
        "contents": {
            "kind": "markdown",
            "value": markdown,
        }
    }


def _buscar_tipo_variable_en_ast(ast, nombre: str) -> Optional[str]:
    from compilador.ast_nodes import (
        Nodo, DeclaracionVariable, AsignacionVariable,
        LiteralNumero, LiteralDecimal, LiteralCadena, LiteralBooleano,
        SentenciaSi, SentenciaMientras, SentenciaPara, BloqueInseguro,
        Programa,
    )

    def _recorrer_nodos(nodos):
        for n in nodos:
            if isinstance(n, DeclaracionVariable) and n.nombre == nombre:
                return n.tipo
            if isinstance(n, AsignacionVariable) and n.nombre == nombre:
                if isinstance(n.expresion, LiteralNumero):
                    return 'entero'
                if isinstance(n.expresion, LiteralDecimal):
                    return 'decimal'
                if isinstance(n.expresion, LiteralCadena):
                    return 'texto'
                if isinstance(n.expresion, LiteralBooleano):
                    return 'booleano'
                return 'entero'
            hijos = []
            if hasattr(n, 'cuerpo') and isinstance(n.cuerpo, list):
                hijos.extend(n.cuerpo)
            if hasattr(n, 'cuerpo_sino') and isinstance(n.cuerpo_sino, list):
                hijos.extend(n.cuerpo_sino)
            if isinstance(n, (SentenciaSi, SentenciaMientras, SentenciaPara, BloqueInseguro)):
                if hasattr(n, 'condicion') and isinstance(n.condicion, Nodo):
                    pass
            if hasattr(n, 'sentencias') and isinstance(n.sentencias, list):
                hijos.extend(n.sentencias)
            if hijos:
                r = _recorrer_nodos(hijos)
                if r:
                    return r
        return None

    if isinstance(ast, Programa):
        return _recorrer_nodos(ast.sentencias)
    return _recorrer_nodos([ast])


def _obtener_palabra_en_posicion(texto: str, linea: int, columna: int) -> Optional[str]:
    lineas = texto.split("\n")
    if linea < 0 or linea >= len(lineas):
        return None
    linea_texto = lineas[linea]
    if columna < 0 or columna >= len(linea_texto):
        return None
    inicio = columna
    while inicio > 0 and (linea_texto[inicio - 1].isalnum() or linea_texto[inicio - 1] == '_'):
        inicio -= 1
    fin = columna
    while fin < len(linea_texto) and (linea_texto[fin].isalnum() or linea_texto[fin] == '_'):
        fin += 1
    return linea_texto[inicio:fin]


def _construir_hover_variable(nombre: str, tipo: str) -> dict:
    return {
        "contents": {
            "kind": "markdown",
            "value": f"```synapse\n{nombre}: {tipo}\n```",
        }
    }


def _manejar_hover(msg: dict) -> Optional[dict]:
    params = msg.get("params", {})
    doc = params.get("textDocument", {})
    uri = doc.get("uri", "")
    pos = params.get("position", {})
    linea = pos.get("line", 0)
    columna = pos.get("character", 0)

    doc_info = _obtener_documento(uri)
    if doc_info is None or doc_info["ast"] is None:
        return None

    from compilador.ast_nodes import Programa, DefinicionFuncion as _DF

    ast = doc_info["ast"]
    if not isinstance(ast, Programa):
        return None

    texto = doc_info["texto"]

    for s in ast.sentencias:
        if isinstance(s, _DF):
            fn_linea = s.linea - 1
            if fn_linea == linea:
                resultado = _construir_hover_funcion(s)
                if resultado:
                    return resultado

            for stmt in s.cuerpo:
                resultado = _buscar_llamada_en_nodo(stmt, linea, columna, ast)
                if resultado:
                    return resultado

    palabra = _obtener_palabra_en_posicion(texto, linea, columna)
    if palabra:
        tipo = _buscar_tipo_variable_en_ast(ast, palabra)
        if tipo:
            return _construir_hover_variable(palabra, tipo)

    return None


def _buscar_llamada_en_nodo(nodo, linea: int, columna: int, programa) -> Optional[dict]:
    from compilador.ast_nodes import (
        DefinicionFuncion, LlamadaFuncion, SentenciaExpr, AsignacionVariable,
        SentenciaSi, SentenciaMientras,
        OpBinaria, OpUnaria, ExprAccesoCampo,
    )

    if isinstance(nodo, LlamadaFuncion):
        if nodo.linea - 1 == linea:
            for s in programa.sentencias:
                if isinstance(s, DefinicionFuncion) and s.nombre == nodo.nombre:
                    return _construir_hover_funcion(s)
        return None

    if isinstance(nodo, SentenciaExpr):
        return _buscar_llamada_en_nodo(nodo.expr, linea, columna, programa)
    if isinstance(nodo, AsignacionVariable):
        return _buscar_llamada_en_nodo(nodo.expresion, linea, columna, programa)
    if type(nodo).__name__ == 'SentenciaRetornar':
        if nodo.expr:
            return _buscar_llamada_en_nodo(nodo.expr, linea, columna, programa)
    if isinstance(nodo, OpBinaria):
        r = _buscar_llamada_en_nodo(nodo.izquierdo, linea, columna, programa)
        if r:
            return r
        return _buscar_llamada_en_nodo(nodo.derecho, linea, columna, programa)
    if isinstance(nodo, OpUnaria):
        return _buscar_llamada_en_nodo(nodo.expr, linea, columna, programa)
    if isinstance(nodo, ExprAccesoCampo):
        return _buscar_llamada_en_nodo(nodo.objeto, linea, columna, programa)
    if isinstance(nodo, SentenciaSi):
        r = _buscar_llamada_en_nodo(nodo.condicion, linea, columna, programa)
        if r:
            return r
        for s in (nodo.cuerpo or []):
            r = _buscar_llamada_en_nodo(s, linea, columna, programa)
            if r:
                return r
        for s in (nodo.cuerpo_sino or []):
            r = _buscar_llamada_en_nodo(s, linea, columna, programa)
            if r:
                return r
        return None
    if isinstance(nodo, SentenciaMientras):
        r = _buscar_llamada_en_nodo(nodo.condicion, linea, columna, programa)
        if r:
            return r
        for s in (nodo.cuerpo or []):
            r = _buscar_llamada_en_nodo(s, linea, columna, programa)
            if r:
                return r
        return None
    return None
