from typing import Optional

_CODE_ACTIONS = {
    "ERR_SEM_VAR_NO_DECLARADA": {
        "title": "Declarar variable con tipo 'entero'",
        "kind": "quickfix",
    },
    "ERR_SEM_FUNC_NO_DEFINIDA": {
        "title": "Crear funcion faltante",
        "kind": "quickfix",
    },
    "ERR_FILE_NOT_FOUND": {
        "title": "Verificar ruta del archivo",
        "kind": "quickfix",
    },
    "ERR_LANG_NOT_SUPPORTED": {
        "title": "Usar '#lang: es' para espanol",
        "kind": "quickfix",
    },
}


def _manejar_code_action(msg: dict) -> Optional[list]:
    params = msg.get("params", {})
    doc = params.get("textDocument", {})
    uri = doc.get("uri", "")
    context = params.get("context", {})
    diagnostics = context.get("diagnostics", [])

    actions = []
    for diag in diagnostics:
        code = diag.get("code", "")
        if code in _CODE_ACTIONS:
            action_info = _CODE_ACTIONS[code]
            actions.append({
                "title": action_info["title"],
                "kind": action_info["kind"],
                "diagnostics": [diag],
                "edit": {
                    "changes": {
                        uri: [
                            {
                                "range": diag["range"],
                                "newText": "",
                            }
                        ]
                    }
                },
                "isPreferred": False,
            })

    return actions if actions else None
