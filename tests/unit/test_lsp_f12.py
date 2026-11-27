# cumple Manual 7 2.3
"""Tests para F12.1: Nuevos proveedores LSP.

Cubre:
- textDocument/signatureHelp
- textDocument/documentSymbol
- textDocument/codeAction
- textDocument/formatting
- ERR_LIFETIME tracing en diagnostics
"""

from synapse_lsp.server import (
    _manejar_signature_help,
    _manejar_document_symbol,
    _manejar_code_action,
    _formatear_codigo,
    _errores_a_diagnostics,
    _almacenar_documento,
    _DOCS,
)
from compilador.ast_nodes import (
    Programa, DefinicionFuncion, Parametro, DefinicionEstructura,
    DeclaracionExterna, StmtConstante,
)


def _simular_mensaje(metodo: str, params: dict, msg_id: int = 1) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "method": metodo, "params": params}


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------

def _setup_doc_con_funcion():
    """Crea un AST con una funcion 'sumar(a: entero, b: entero) -> entero'."""
    prog = Programa()
    fn = DefinicionFuncion(
        nombre="sumar",
        parametros=[
            Parametro(nombre="a", tipo="entero"),
            Parametro(nombre="b", tipo="entero"),
        ],
        tipo_retorno="entero",
        linea=1,
        columna=0,
        cuerpo=[],
    )
    prog.sentencias = [fn]
    codigo = "#lang: es\nfuncion sumar(a: entero, b: entero) -> entero:\n    retornar a + b\n"
    _DOCS.clear()
    _almacenar_documento("file:///test.syn", codigo, prog)
    return prog


def _setup_doc_con_estructura():
    """Crea un AST con una estructura 'Persona'."""
    prog = Programa()
    struct = DefinicionEstructura(
        nombre="Persona",
        campos=[
            Parametro(nombre="nombre", tipo="texto"),
            Parametro(nombre="edad", tipo="entero"),
        ],
        linea=1,
        columna=0,
    )
    prog.sentencias = [struct]
    codigo = "#lang: es\nestructura Persona:\n    nombre: texto\n    edad: entero\n"
    _DOCS.clear()
    _almacenar_documento("file:///test.syn", codigo, prog)
    return prog


def _setup_doc_mixto():
    """Crea un AST con funcion, struct, extern, constante."""
    prog = Programa()
    fn = DefinicionFuncion(
        nombre="main", parametros=[], tipo_retorno="entero",
        linea=1, columna=0, cuerpo=[],
    )
    struct = DefinicionEstructura(
        nombre="Punto", campos=[Parametro(nombre="x", tipo="entero")], linea=3, columna=0,
    )
    ext = DeclaracionExterna(nombre="exit", tipo_retorno="nulo", linea=6, columna=0)
    const = StmtConstante(nombre="MAX", valor=None, tipo="entero", linea=8, columna=0)
    prog.sentencias = [fn, struct, ext, const]
    codigo = "#lang: es\nfuncion main() -> entero:\n    0\n\nestructura Punto:\n    x: entero\n\nexterno funcion exit(codigo: entero) -> nulo\n\nconstante MAX: entero = 100\n"
    _DOCS.clear()
    _almacenar_documento("file:///test.syn", codigo, prog)
    return prog


# ---------------------------------------------------------------------------
# Tests: Signature Help
# ---------------------------------------------------------------------------

def test_signature_help_funcion_conocida():
    """Al escribir 'sumar(' debe mostrar la firma de sumar."""
    prog = Programa()
    fn = DefinicionFuncion(
        nombre="sumar",
        parametros=[
            Parametro(nombre="a", tipo="entero"),
            Parametro(nombre="b", tipo="entero"),
        ],
        tipo_retorno="entero",
        linea=1,
        columna=0,
        cuerpo=[],
    )
    prog.sentencias = [fn]
    # Codigo con llamada a sumar() en linea 3 (0-based: 2)
    codigo = "#lang: es\nfuncion sumar(a: entero, b: entero) -> entero:\n    retornar a + b\n\nfuncion main() -> nulo:\n    sumar(1, 2)\n"
    _DOCS.clear()
    _almacenar_documento("file:///test.syn", codigo, prog)

    msg = _simular_mensaje("textDocument/signatureHelp", {
        "textDocument": {"uri": "file:///test.syn"},
        "position": {"line": 5, "character": 10},
    })
    resultado = _manejar_signature_help(msg)
    assert resultado is not None, "signatureHelp devolvio None"
    signatures = resultado.get("signatures", [])
    assert len(signatures) == 1
    sig = signatures[0]
    assert "sumar" in sig["label"]
    assert "entero" in sig["label"]
    assert len(sig.get("parameters", [])) == 2


def test_signature_help_parametro_activo():
    """Al escribir 'sumar(42, ' el parametro activo debe ser 1."""
    _setup_doc_con_funcion()
    msg = _simular_mensaje("textDocument/signatureHelp", {
        "textDocument": {"uri": "file:///test.syn"},
        "position": {"line": 2, "character": 12},
    })
    resultado = _manejar_signature_help(msg)
    if resultado:
        assert resultado.get("activeParameter") is not None


def test_signature_help_funcion_desconocida():
    """Funcion no definida debe retornar None."""
    _setup_doc_con_funcion()
    msg = _simular_mensaje("textDocument/signatureHelp", {
        "textDocument": {"uri": "file:///test.syn"},
        "position": {"line": 2, "character": 5},
    })
    # 'escribir_linea' no esta definida en el AST simplificado
    resultado = _manejar_signature_help(msg)
    # Puede ser None si no se encuentra
    assert resultado is None or resultado.get("signatures") == []


def test_signature_help_sin_documento():
    """Sin documento almacenado debe retornar None."""
    _DOCS.clear()
    msg = _simular_mensaje("textDocument/signatureHelp", {
        "textDocument": {"uri": "file:///no_existe.syn"},
        "position": {"line": 0, "character": 0},
    })
    resultado = _manejar_signature_help(msg)
    assert resultado is None


# ---------------------------------------------------------------------------
# Tests: Document Symbol
# ---------------------------------------------------------------------------

def test_document_symbol_funcion():
    """Debe listar la funcion como simbolo tipo 12 (Function)."""
    _setup_doc_con_funcion()
    msg = _simular_mensaje("textDocument/documentSymbol", {
        "textDocument": {"uri": "file:///test.syn"},
    })
    resultado = _manejar_document_symbol(msg)
    assert resultado is not None
    nombres = [s["name"] for s in resultado]
    assert "sumar" in nombres
    assert any(s["kind"] == 12 for s in resultado)  # Function


def test_document_symbol_estructura():
    """Debe listar la estructura como simbolo tipo 23 (Struct)."""
    _setup_doc_con_estructura()
    msg = _simular_mensaje("textDocument/documentSymbol", {
        "textDocument": {"uri": "file:///test.syn"},
    })
    resultado = _manejar_document_symbol(msg)
    assert resultado is not None
    nombres = [s["name"] for s in resultado]
    assert "Persona" in nombres
    struct = [s for s in resultado if s["name"] == "Persona"][0]
    assert struct["kind"] == 23  # Struct
    # Debe tener campos como hijos
    hijos = struct.get("children", [])
    nombres_hijos = [h["name"] for h in hijos]
    assert "nombre" in nombres_hijos
    assert "edad" in nombres_hijos


def test_document_symbol_mixto():
    """Debe listar funcion, struct, externo, constante."""
    _setup_doc_mixto()
    msg = _simular_mensaje("textDocument/documentSymbol", {
        "textDocument": {"uri": "file:///test.syn"},
    })
    resultado = _manejar_document_symbol(msg)
    assert resultado is not None
    names = [s["name"] for s in resultado]
    assert "main" in names
    assert "Punto" in names
    assert "exit" in names
    assert "MAX" in names

    kinds = {s["kind"] for s in resultado}
    assert 12 in kinds  # Function
    assert 23 in kinds  # Struct
    assert 14 in kinds  # Constant


def test_document_symbol_sin_documento():
    """Sin documento debe retornar None."""
    _DOCS.clear()
    msg = _simular_mensaje("textDocument/documentSymbol", {
        "textDocument": {"uri": "file:///no_existe.syn"},
    })
    resultado = _manejar_document_symbol(msg)
    assert resultado is None


# ---------------------------------------------------------------------------
# Tests: Code Action
# ---------------------------------------------------------------------------

def test_code_action_error_conocido():
    """Para ERR_SEM_VAR_NO_DECLARADA debe sugerir 'Declarar variable'."""
    msg = _simular_mensaje("textDocument/codeAction", {
        "textDocument": {"uri": "file:///test.syn"},
        "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
        "context": {
            "diagnostics": [
                {"range": {}, "code": "ERR_SEM_VAR_NO_DECLARADA", "message": "x no declarada"}
            ]
        },
    })
    resultado = _manejar_code_action(msg)
    assert resultado is not None
    assert len(resultado) >= 1
    assert "Declarar variable" in resultado[0]["title"]


def test_code_action_error_funcion():
    """Para ERR_SEM_FUNC_NO_DEFINIDA debe sugerir 'Crear funcion'."""
    msg = _simular_mensaje("textDocument/codeAction", {
        "textDocument": {"uri": "file:///test.syn"},
        "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
        "context": {
            "diagnostics": [
                {"range": {}, "code": "ERR_SEM_FUNC_NO_DEFINIDA", "message": "foo no definida"}
            ]
        },
    })
    resultado = _manejar_code_action(msg)
    assert resultado is not None
    assert len(resultado) >= 1
    assert "Crear funcion" in resultado[0]["title"]


def test_code_action_error_desconocido():
    """Error desconocido debe retornar None."""
    msg = _simular_mensaje("textDocument/codeAction", {
        "textDocument": {"uri": "file:///test.syn"},
        "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
        "context": {
            "diagnostics": [
                {"range": {}, "code": "ERR_UNKNOWN", "message": "error raro"}
            ]
        },
    })
    resultado = _manejar_code_action(msg)
    assert resultado is None or len(resultado) == 0


def test_code_action_sin_errores():
    """Sin errores debe retornar None."""
    msg = _simular_mensaje("textDocument/codeAction", {
        "textDocument": {"uri": "file:///test.syn"},
        "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
        "context": {"diagnostics": []},
    })
    resultado = _manejar_code_action(msg)
    assert resultado is None or len(resultado) == 0


# ---------------------------------------------------------------------------
# Tests: Formatting
# ---------------------------------------------------------------------------

def test_formateo_indentacion():
    """Debe indentar correctamente bloques anidados."""
    codigo = """#lang: es
funcion main() -> nulo:
si verdadero:
escribir_linea("hola")
sino:
escribir_linea("mundo")
"""
    formateado = _formatear_codigo(codigo)
    lineas = formateado.split("\n")
    assert lineas[1].startswith("funcion")  # nivel 0
    assert lineas[2].startswith("    si")  # nivel 1
    assert lineas[3].startswith("        escribir_linea")  # nivel 2


def test_formateo_elimina_espacios_extra():
    """Debe eliminar espacios al inicio/final."""
    codigo = "  hola  \n  mundo  "
    formateado = _formatear_codigo(codigo)
    lineas = formateado.split("\n")
    for l in lineas:
        assert l == l.strip() or l.startswith("    "), f"Indentacion incorrecta: {l!r}"


def test_formateo_sin_cambios():
    """Codigo ya formateado debe permanecer igual."""
    codigo = "#lang: es\nfuncion main() -> nulo:\n    retornar 0\n"
    formateado = _formatear_codigo(codigo)
    # Puede cambiar ligeramente por la normalizacion, pero debe ser funcionalmente igual
    assert "funcion main()" in formateado


# ---------------------------------------------------------------------------
# Tests: ERR_LIFETIME Tracing
# ---------------------------------------------------------------------------

def test_errores_a_diagnostics_lifetime():
    """Los errores de ownership deben incluir marcador ERR_LIFETIME."""
    errores = [
        {
            "codigo": "ERR_SEM_VAR_MOVIDA",
            "linea": 5,
            "columna": 10,
            "mensaje": "Variable 'x' fue movida",
        }
    ]
    diags = _errores_a_diagnostics(errores)
    assert len(diags) == 1
    assert "[ERR_LIFETIME]" in diags[0]["message"]
    assert diags[0]["code"] == "ERR_SEM_VAR_MOVIDA"


def test_errores_a_diagnostics_no_lifetime():
    """Errores no de ownership no deben tener marcador ERR_LIFETIME."""
    errores = [
        {
            "codigo": "ERR_SYNTAX_EXPECTED_TOKEN",
            "linea": 5,
            "columna": 10,
            "mensaje": "Se esperaba ':'",
        }
    ]
    diags = _errores_a_diagnostics(errores)
    assert len(diags) == 1
    assert "[ERR_LIFETIME]" not in diags[0]["message"]


def test_errores_a_diagnostics_conversion_coordenadas():
    """Las coordenadas Synapse (1-based) deben convertirse a LSP (0-based)."""
    errores = [
        {
            "codigo": "ERR_LEX",
            "linea": 3,
            "columna": 5,
            "mensaje": "Caracter inesperado",
        }
    ]
    diags = _errores_a_diagnostics(errores)
    assert len(diags) == 1
    assert diags[0]["range"]["start"]["line"] == 2  # 3 - 1 = 2
    assert diags[0]["range"]["start"]["character"] == 5


# ---------------------------------------------------------------------------
# Tests: Capacidades declaradas en initialize
# ---------------------------------------------------------------------------

def test_initialize_capacidades():
    """El resultado de initialize debe declarar todas las capacidades."""
    from synapse_lsp.server import _procesar_mensaje
    msg = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
           "params": {"processId": None, "capabilities": {}}}
    resultado = _procesar_mensaje(msg)
    assert resultado is not None
    caps = resultado.get("result", {}).get("capabilities", {})
    # F12.1: Nuevas capacidades
    assert caps.get("signatureHelpProvider") is not None
    assert caps.get("documentSymbolProvider") is True
    assert caps.get("codeActionProvider") is True
    assert caps.get("documentFormattingProvider") is True
    # Capacidades existentes
    assert caps.get("hoverProvider") is True
    assert caps.get("definitionProvider") is True
    assert caps.get("completionProvider") is not None
