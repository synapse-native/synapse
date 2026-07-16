from synapse_lsp.server import (
    _manejar_completado, _PALABRAS_CLAVE_LSP,
)


def _simular_mensaje(metodo: str, params: dict, msg_id: int = 1) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "method": metodo, "params": params}


def test_completado_palabras_clave():
    msg = _simular_mensaje("textDocument/completion", {
        "textDocument": {"uri": "file:///test.syn"},
        "position": {"line": 0, "character": 0},
    })
    resultado = _manejar_completado(msg)
    assert resultado is not None
    items = resultado.get("items", [])
    labels = [i["label"] for i in items]
    for kw in ["si", "mientras", "para", "funcion", "estructura"]:
        assert kw in labels, f"Falta palabra clave: {kw}"
    assert len(items) >= 26


def test_completado_con_simbolos():
    from synapse_lsp.server import _DOCS, _almacenar_documento
    from compilador.ast_nodes import Programa

    prog = Programa()
    _almacenar_documento("file:///test2.syn", "#lang: es\nfuncion principal() -> nulo:\n    x = 1\n    y = 2", prog)

    msg = _simular_mensaje("textDocument/completion", {
        "textDocument": {"uri": "file:///test2.syn"},
        "position": {"line": 2, "character": 4},
    })
    resultado = _manejar_completado(msg)
    assert resultado is not None
    items = resultado.get("items", [])
    labels = [i["label"] for i in items]
    for kw in ["si", "mientras", "para", "funcion"]:
        assert kw in labels, f"Falta palabra clave: {kw}"
    assert len(items) >= 26