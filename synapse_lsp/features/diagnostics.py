import sys
import logging
import traceback
from exceptions import SynapseError
from synapse_lsp.features.store import _almacenar_documento
from synapse_lsp.transport import _enviar_notificacion

_CODIGOS_OWNERSHIP = frozenset({
    "ERR_SEM_VAR_MOVIDA",
    "ERR_MEM_USE_AFTER_MOVE",  # cumple Manual 2 §9: canonico de uso tras move
    "ERR_SEM_ACCESO_MEMORIA_MOVIDA",
    "ERR_SEM_RESULTADO_SIN_DESEMPAQUETAR",
})


def _errores_a_diagnostics(errores: list) -> list:
    lsp_diags = []
    for err in errores:
        syn_linea = err.get("linea", 0)
        syn_columna = err.get("columna", 0)
        codigo = err.get("codigo", "")
        if hasattr(codigo, "name"):
            codigo = codigo.name
        codigo_str = str(codigo)

        mensaje = err.get("mensaje", "Error desconocido")

        if codigo_str in _CODIGOS_OWNERSHIP:
            mensaje = "[ERR_LIFETIME] " + mensaje

        lsp_diags.append({
            "range": {
                "start": {"line": max(0, syn_linea - 1), "character": syn_columna},
                "end": {"line": max(0, syn_linea - 1), "character": syn_columna + 1},
            },
            "severity": 1,
            "code": codigo_str,
            "source": "synapse",
            "message": mensaje,
        })
    return lsp_diags


def validar_documento(uri: str, codigo_fuente: str) -> list:
    import traceback
    try:
        from compilador.lexer import Lexer
        from compilador.parser import Parser
        from compilador.diagnostics import DiagnosticManager
        from compilador.analizador_semantico import AnalizadorSemantico
    except Exception as e:
        sys.stderr.write(f"[LSP] ERROR importing modules: {e}\n{traceback.format_exc()}\n")
        sys.stderr.flush()
        return []

    fuente_lineas = codigo_fuente.split("\n")
    diag = DiagnosticManager(fuente_lineas=fuente_lineas, ruta_archivo=uri)

    try:
        lexer = Lexer(codigo_fuente)
        tokens = lexer.tokenizar()
    except SynapseError as e:
        _agregar_error_syntax(diag, e)
        return diag.errores
    except Exception as exc:
        sys.stderr.write(f"[LSP] Lexer exception: {exc}\n{traceback.format_exc()}\n")
        sys.stderr.flush()
        return diag.errores

    try:
        parser = Parser(tokens, diag)
        ast = parser.parsear()
    except Exception as exc:
        sys.stderr.write(f"[LSP] Parser exception: {exc}\n{traceback.format_exc()}\n")
        sys.stderr.flush()
        return diag.errores

    analizador = None
    try:
        analizador = AnalizadorSemantico(ast, diag)
        analizador.analizar()
    except Exception as exc:
        sys.stderr.write(f"[LSP] Semantic exception: {exc}\n{traceback.format_exc()}\n")
        sys.stderr.flush()

    _almacenar_documento(uri, codigo_fuente, ast, analizador=analizador)

    return diag.errores


def _agregar_error_syntax(diag, error):
    from compilador.diagnostics import ErrorCodes
    from compilador.ast_nodes import Token, TokenID
    diag.reportar(ErrorCodes.ERR_LEX, Token(TokenID.EOF, error.linea, error.columna), mensaje=error.mensaje)


def _enviar_diagnostics_archivo(uri: str, texto: str) -> None:
    try:
        errores = validar_documento(uri, texto)
        lsp_diags = _errores_a_diagnostics(errores) if errores else []
        _enviar_notificacion("textDocument/publishDiagnostics", {
            "uri": uri,
            "diagnostics": lsp_diags,
        })
    except Exception:
        logging.error("[LSP] Error en validar_documento:\n%s", traceback.format_exc())
