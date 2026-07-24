from typing import Optional
from synapse_lsp.features.store import _obtener_documento


def _manejar_signature_help(msg: dict) -> Optional[dict]:
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
    lineas = texto.split("\n")
    if linea < 0 or linea >= len(lineas):
        return None
    linea_texto = lineas[linea][:columna]
    paren_idx = linea_texto.rfind("(")
    if paren_idx < 0:
        return None
    antes_paren = linea_texto[:paren_idx].rstrip()
    palabras = antes_paren.split()
    if not palabras:
        return None
    nombre_funcion = palabras[-1].strip()

    from compilador.ast_nodes import Programa, DefinicionFuncion
    ast = doc_info["ast"]
    if not isinstance(ast, Programa):
        return None

    for s in ast.sentencias:
        if isinstance(s, DefinicionFuncion) and s.nombre == nombre_funcion:
            params_str = ", ".join(
                f"{p.nombre}: {p.tipo}" for p in s.parametros
            )
            ret = s.tipo_retorno if s.tipo_retorno else "nulo"
            label = f"funcion {s.nombre}({params_str}) -> {ret}"
            signature = {
                "label": label,
                "parameters": [
                    {"label": f"{p.nombre}: {p.tipo}"}
                    for p in s.parametros
                ],
            }
            texto_argumentos = lineas[linea][paren_idx+1:columna]
            nivel = 0
            comas = 0
            for c in texto_argumentos:
                if c == '(':
                    nivel += 1
                elif c == ')':
                    nivel -= 1
                elif c == ',' and nivel == 0:
                    comas += 1
            active_param = min(comas, len(s.parametros) - 1) if s.parametros else 0

            return {
                "signatures": [signature],
                "activeSignature": 0,
                "activeParameter": max(0, active_param),
            }

    return None


def _manejar_document_symbol(msg: dict) -> Optional[list]:
    params = msg.get("params", {})
    doc = params.get("textDocument", {})
    uri = doc.get("uri", "")

    doc_info = _obtener_documento(uri)
    if doc_info is None or doc_info["ast"] is None:
        return None

    from compilador.ast_nodes import (
        Programa, DefinicionFuncion, DefinicionEstructura,
        DeclaracionExterna, StmtConstante,
    )

    ast = doc_info["ast"]
    if not isinstance(ast, Programa):
        return None

    symbols = []

    for s in ast.sentencias:
        if isinstance(s, DefinicionFuncion):
            nombre = s.nombre
            params_str = ", ".join(f"{p.nombre}: {p.tipo}" for p in s.parametros)
            ret = s.tipo_retorno if s.tipo_retorno else "nulo"
            symbols.append({
                "name": nombre,
                "kind": 12,
                "detail": f"({params_str}) -> {ret}",
                "range": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, (s.linea or 0) + 0), "character": s.columna + len(nombre)},
                },
                "selectionRange": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, s.linea - 1), "character": s.columna + len(nombre)},
                },
                "children": [],
            })
            for p in s.parametros:
                symbols[-1]["children"].append({
                    "name": p.nombre,
                    "kind": 13,
                    "detail": p.tipo,
                    "range": {
                        "start": {"line": max(0, s.linea - 1), "character": 0},
                        "end": {"line": max(0, s.linea - 1), "character": 0},
                    },
                    "selectionRange": {
                        "start": {"line": max(0, s.linea - 1), "character": 0},
                        "end": {"line": max(0, s.linea - 1), "character": 0},
                    },
                })

        elif isinstance(s, DefinicionEstructura):
            symbols.append({
                "name": s.nombre,
                "kind": 23,
                "range": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, s.linea - 1), "character": s.columna + len(s.nombre)},
                },
                "selectionRange": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, s.linea - 1), "character": s.columna + len(s.nombre)},
                },
                "children": [
                    {
                        "name": c.nombre,
                        "kind": 8,
                        "detail": c.tipo,
                        "range": {
                            "start": {"line": max(0, getattr(c, 'linea', 1) - 1), "character": getattr(c, 'columna', 0)},
                            "end": {"line": max(0, getattr(c, 'linea', 1) - 1), "character": getattr(c, 'columna', 0) + len(c.nombre)},
                        },
                        "selectionRange": {
                            "start": {"line": max(0, getattr(c, 'linea', 1) - 1), "character": getattr(c, 'columna', 0)},
                            "end": {"line": max(0, getattr(c, 'linea', 1) - 1), "character": getattr(c, 'columna', 0) + len(c.nombre)},
                        },
                    }
                    for c in (s.campos if hasattr(s, 'campos') else [])
                ],
            })

        elif isinstance(s, DeclaracionExterna):
            symbols.append({
                "name": s.nombre,
                "kind": 12,
                "detail": "externo",
                "range": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, s.linea - 1), "character": s.columna + len(s.nombre)},
                },
                "selectionRange": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, s.linea - 1), "character": s.columna + len(s.nombre)},
                },
            })

        elif isinstance(s, StmtConstante):
            symbols.append({
                "name": s.nombre,
                "kind": 14,
                "detail": "constante",
                "range": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, s.linea - 1), "character": s.columna + len(s.nombre)},
                },
                "selectionRange": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, s.linea - 1), "character": s.columna + len(s.nombre)},
                },
            })

    return symbols
