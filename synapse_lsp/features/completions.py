import logging
import traceback
from typing import Optional
from synapse_lsp.features.store import _obtener_documento

_PALABRAS_CLAVE = [
    "si", "sino", "funcion", "retornar", "mientras", "para",
    "romper", "siguiente", "importar", "estructura", "coincidir",
    "lanzar", "recuperar", "escuchar", "inseguro", "externo",
    "constante", "verdadero", "falso", "y", "o", "no",
    "requiere", "garantiza", "canal", "asm",
]

_PALABRAS_CLAVE_LSP = [
    {"label": "si", "kind": 14, "detail": "keyword"},
    {"label": "sino", "kind": 14, "detail": "keyword"},
    {"label": "funcion", "kind": 14, "detail": "keyword"},
    {"label": "retornar", "kind": 14, "detail": "keyword"},
    {"label": "mientras", "kind": 14, "detail": "keyword"},
    {"label": "para", "kind": 14, "detail": "keyword"},
    {"label": "romper", "kind": 14, "detail": "keyword"},
    {"label": "siguiente", "kind": 14, "detail": "keyword"},
    {"label": "importar", "kind": 14, "detail": "keyword"},
    {"label": "estructura", "kind": 14, "detail": "keyword"},
    {"label": "coincidir", "kind": 14, "detail": "keyword"},
    {"label": "lanzar", "kind": 14, "detail": "keyword"},
    {"label": "recuperar", "kind": 14, "detail": "keyword"},
    {"label": "escuchar", "kind": 14, "detail": "keyword"},
    {"label": "inseguro", "kind": 14, "detail": "keyword"},
    {"label": "externo", "kind": 14, "detail": "keyword"},
    {"label": "constante", "kind": 14, "detail": "keyword"},
    {"label": "verdadero", "kind": 14, "detail": "keyword"},
    {"label": "falso", "kind": 14, "detail": "keyword"},
    {"label": "y", "kind": 14, "detail": "keyword"},
    {"label": "o", "kind": 14, "detail": "keyword"},
    {"label": "no", "kind": 14, "detail": "keyword"},
    {"label": "requiere", "kind": 14, "detail": "keyword"},
    {"label": "garantiza", "kind": 14, "detail": "keyword"},
    {"label": "canal", "kind": 14, "detail": "keyword"},
    {"label": "asm", "kind": 14, "detail": "keyword"},
]


def _obtener_simbolos_desde_tabla(uri: str) -> list:
    doc_info = _obtener_documento(uri)
    if doc_info is None or doc_info["ast"] is None:
        return []
    from compilador.ast_nodes import Programa
    from compilador.diagnostics import DiagnosticManager
    from compilador.analizador_semantico import AnalizadorSemantico

    ast = doc_info["ast"]
    if not isinstance(ast, Programa):
        return []

    analizador = doc_info.get("analizador")
    if analizador is None:
        texto = doc_info["texto"]
        fuente_lineas = texto.split("\n")
        diag = DiagnosticManager(fuente_lineas=fuente_lineas, ruta_archivo=uri)
        analizador = AnalizadorSemantico(ast, diag)
        try:
            analizador.analizar()
        except Exception:
            logging.error("[LSP] Error en analisis semantico:\n%s", traceback.format_exc())

    simbolos = []
    try:
        for nombre, sim in analizador.tabla._scopes[-1].items():
            simbolos.append({
                "label": nombre,
                "kind": 6,
                "detail": sim.tipo,
            })
    except (IndexError, AttributeError):
        logging.error("[LSP] Error en obtencion de simbolos:\n%s", traceback.format_exc())
    return simbolos


def _manejar_completado(msg: dict) -> Optional[dict]:
    params = msg.get("params", {})
    doc = params.get("textDocument", {})
    uri = doc.get("uri", "")

    items = list(_PALABRAS_CLAVE_LSP)
    simbolos = _obtener_simbolos_desde_tabla(uri)
    items.extend(simbolos)

    return {"isIncomplete": False, "items": items}
