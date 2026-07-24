from typing import Optional
from synapse_lsp.features.store import _obtener_documento
from synapse_lsp.features.hover import _obtener_palabra_en_posicion
from synapse_lsp.llm_bridge import (
    generar_completado,
    explicar_codigo,
    sugerir_correccion,
)


def _manejar_ai_complete(msg: dict) -> Optional[dict]:
    params = msg.get("params", {})
    uri = params.get("textDocument", {}).get("uri", "")
    contexto = params.get("context", "")
    prompt = params.get("prompt", "")

    doc_info = _obtener_documento(uri)
    buffer_actual = doc_info["texto"] if doc_info else ""

    codigo_generado = generar_completado(buffer_actual or contexto, prompt)

    if codigo_generado is None:
        return {
            "ai_available": False,
            "message": "IA local no disponible. Instala Ollama y un modelo (ej. phi3:mini).",
            "code": None,
        }

    return {
        "ai_available": True,
        "provider": "ollama",
        "code": codigo_generado,
    }


def _manejar_ai_explain(msg: dict) -> Optional[dict]:
    params = msg.get("params", {})
    uri = params.get("textDocument", {}).get("uri", "")
    codigo = params.get("code", "")

    if not codigo:
        doc_info = _obtener_documento(uri)
        if doc_info:
            pos = params.get("position", {})
            linea = pos.get("line", 0)
            lineas = doc_info["texto"].split("\n")
            if 0 <= linea < len(lineas):
                codigo = lineas[linea]

    if not codigo:
        return {"ai_available": False, "message": "No hay codigo para explicar.", "explanation": None}

    explicacion = explicar_codigo(codigo)

    if explicacion is None:
        return {"ai_available": False, "message": "IA local no disponible.", "explanation": None}

    return {
        "ai_available": True,
        "provider": "ollama",
        "explanation": explicacion,
        "code": codigo,
    }


def _manejar_ai_status(msg: dict) -> dict:
    from synapse_lsp.llm_bridge import _obtener_cliente
    cliente = _obtener_cliente()
    disponible = cliente.verificar_disponible()
    modelos = cliente.listar_modelos() if disponible else []

    return {
        "ai_available": disponible,
        "provider": "ollama" if disponible else None,
        "host": "localhost:11434",
        "modelos": modelos,
        "local_only": True,
        "message": "IA local lista" if disponible else "Ollama no detectado. Instalalo en https://ollama.ai",
    }


def _manejar_hover_ia(msg: dict) -> Optional[dict]:
    params = msg.get("params", {})
    uri = params.get("textDocument", {}).get("uri", "")
    pos = params.get("position", {})
    linea = pos.get("line", 0)
    columna = pos.get("character", 0)

    doc_info = _obtener_documento(uri)
    if doc_info is None:
        return None

    texto = doc_info["texto"]
    palabra = _obtener_palabra_en_posicion(texto, linea, columna)
    if not palabra:
        return None

    lineas = texto.split("\n")
    if 0 <= linea < len(lineas):
        codigo_linea = lineas[linea].strip()
        if codigo_linea:
            explicacion = explicar_codigo(codigo_linea)
            if explicacion:
                return {
                    "contents": {
                        "kind": "markdown",
                        "value": f"_✨ Explicacion IA:_\n\n{explicacion}",
                    }
                }

    return None


def _manejar_code_action_ia(msg: dict) -> Optional[list]:
    params = msg.get("params", {})
    doc = params.get("textDocument", {})
    uri = doc.get("uri", "")
    context = params.get("context", {})
    diagnostics = context.get("diagnostics", [])

    if not diagnostics:
        return None

    doc_info = _obtener_documento(uri)
    if doc_info is None:
        return None

    texto = doc_info["texto"]
    actions = []

    for diag in diagnostics:
        code = diag.get("code", "")
        message = diag.get("message", "")
        codigo_error = str(code)

        if not codigo_error.startswith("ERR_"):
            continue

        correccion = sugerir_correccion(codigo_error, message, texto)
        if correccion:
            actions.append({
                "title": f"🤖 IA: Sugerir correccion para {codigo_error}",
                "kind": "quickfix",
                "diagnostics": [diag],
                "edit": {
                    "changes": {
                        uri: [
                            {
                                "range": diag.get("range", {
                                    "start": {"line": 0, "character": 0},
                                    "end": {"line": 0, "character": 0},
                                }),
                                "newText": f"\n// IA sugiere:\n// {correccion}\n",
                            }
                        ]
                    }
                },
                "isPreferred": False,
            })
            break

    return actions if actions else None
