from typing import Optional
from synapse_lsp.features.store import _obtener_documento


def _formatear_codigo(texto: str, tab_size: int = 4) -> str:
    lineas = texto.split("\n")
    resultado = []
    indent_level = 0

    for linea in lineas:
        stripped = linea.strip()

        if not stripped:
            resultado.append("")
            continue

        if stripped in ("}", "])", ")", ":") or stripped.startswith("sino") or stripped.startswith("fin"):
            indent_level = max(0, indent_level - 1)

        resultado.append(" " * (indent_level * tab_size) + stripped)

        if stripped.endswith(":") and not stripped.startswith("#"):
            indent_level += 1
        if stripped in ("requiere:", "garantiza:"):
            indent_level += 1

    return "\n".join(resultado)


def _manejar_formatting(msg: dict) -> Optional[list]:
    params = msg.get("params", {})
    doc = params.get("textDocument", {})
    uri = doc.get("uri", "")
    options = params.get("options", {})
    tab_size = options.get("tabSize", 4)

    doc_info = _obtener_documento(uri)
    if doc_info is None:
        return None

    texto_original = doc_info["texto"]
    texto_formateado = _formatear_codigo(texto_original, tab_size)

    lineas_original = texto_original.split("\n")

    if texto_original == texto_formateado:
        return []

    return [
        {
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": len(lineas_original), "character": 0},
            },
            "newText": texto_formateado,
        }
    ]
