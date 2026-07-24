from synapse_lsp.server import (
    _manejar_completado, _manejar_hover, _manejar_definicion,
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
    from synapse_lsp.server import _almacenar_documento
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


def test_hover_variable():
    from synapse_lsp.server import _almacenar_documento
    from compilador.lexer import Lexer
    from compilador.parser import Parser
    from compilador.diagnostics import DiagnosticManager

    codigo = "#lang: es\nfuncion principal() -> nulo:\n    x: entero = 1\n    escribir_linea(x)"
    fuente_lineas = codigo.split("\n")
    diag = DiagnosticManager(fuente_lineas=fuente_lineas, ruta_archivo="file:///test_hover.syn")
    lexer = Lexer(codigo)
    tokens = lexer.tokenizar()
    parser = Parser(tokens, diag)
    ast = parser.parsear()
    _almacenar_documento("file:///test_hover.syn", codigo, ast)

    msg = _simular_mensaje("textDocument/hover", {
        "textDocument": {"uri": "file:///test_hover.syn"},
        "position": {"line": 2, "character": 4},
    })
    resultado = _manejar_hover(msg)
    assert resultado is not None
    contents = resultado.get("contents", {})
    value = contents.get("value", "")
    assert "x" in value
    assert "entero" in value


def test_definicion_variable():
    from synapse_lsp.server import _almacenar_documento
    from compilador.lexer import Lexer
    from compilador.parser import Parser
    from compilador.diagnostics import DiagnosticManager

    codigo = "#lang: es\nfuncion principal() -> nulo:\n    x: entero = 1\n    escribir_linea(x)"
    fuente_lineas = codigo.split("\n")
    diag = DiagnosticManager(fuente_lineas=fuente_lineas, ruta_archivo="file:///test_def.syn")
    lexer = Lexer(codigo)
    tokens = lexer.tokenizar()
    parser = Parser(tokens, diag)
    ast = parser.parsear()
    _almacenar_documento("file:///test_def.syn", codigo, ast)

    msg = _simular_mensaje("textDocument/definition", {
        "textDocument": {"uri": "file:///test_def.syn"},
        "position": {"line": 3, "character": 19},
    })
    resultado = _manejar_definicion(msg)
    assert resultado is not None, "definition returned None"
    assert "uri" in resultado
    assert "range" in resultado
    assert isinstance(resultado["range"]["start"]["line"], int)
    assert isinstance(resultado["range"]["start"]["character"], int)
    assert resultado["range"]["end"]["character"] > resultado["range"]["start"]["character"]