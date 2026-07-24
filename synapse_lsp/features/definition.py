from typing import Optional
from synapse_lsp.features.store import _obtener_documento
from synapse_lsp.features.hover import _obtener_palabra_en_posicion


def _manejar_definicion(msg: dict) -> Optional[dict]:
    params = msg.get("params", {})
    doc = params.get("textDocument", {})
    uri = doc.get("uri", "")
    pos = params.get("position", {})
    linea = pos.get("line", 0)
    columna = pos.get("character", 0)

    doc_info = _obtener_documento(uri)
    if doc_info is None or doc_info["ast"] is None:
        return None

    texto = doc_info["texto"]
    palabra = _obtener_palabra_en_posicion(texto, linea, columna)
    if not palabra:
        return None

    from compilador.ast_nodes import (
        DeclaracionVariable, AsignacionVariable, DefinicionFuncion, Programa,
    )

    ast = doc_info["ast"]
    if not isinstance(ast, Programa):
        return None

    def _buscar_declaracion(nodos):
        for n in nodos:
            if isinstance(n, DeclaracionVariable) and n.nombre == palabra:
                return n.linea, n.columna, len(palabra)
            if isinstance(n, AsignacionVariable) and n.nombre == palabra:
                return n.linea, n.columna, len(palabra)
            if isinstance(n, DefinicionFuncion) and n.nombre == palabra:
                return n.linea, n.columna, len(palabra)
            hijos = []
            if hasattr(n, 'cuerpo') and isinstance(n.cuerpo, list):
                hijos.extend(n.cuerpo)
            if hasattr(n, 'cuerpo_sino') and isinstance(n.cuerpo_sino, list):
                hijos.extend(n.cuerpo_sino)
            if hasattr(n, 'sentencias') and isinstance(n.sentencias, list):
                hijos.extend(n.sentencias)
            if hijos:
                r = _buscar_declaracion(hijos)
                if r:
                    return r
        return None

    loc = _buscar_declaracion(ast.sentencias)
    if loc is None:
        return None

    def_linea, def_col, largo = loc
    return {
        "uri": uri,
        "range": {
            "start": {"line": max(0, def_linea - 1), "character": def_col},
            "end": {"line": max(0, def_linea - 1), "character": def_col + largo},
        },
    }
