# Synapse LSP Server — JSON-RPC 2.0 daemon over stdin/stdout
#
# Este modulo es el dispatcher delgado. La implementacion de cada
# caracteristica LSP vive en features/ o en transport.py.
# Se re-exportan los simbolos publicos para compatibilidad con tests.

from typing import Optional

from synapse_lsp.transport import _leer_mensaje, _enviar_respuesta
from synapse_lsp.features.store import _DOCS, _eliminar_documento
from synapse_lsp.features.diagnostics import _enviar_diagnostics_archivo
from synapse_lsp.features.hover import _manejar_hover
from synapse_lsp.features.completions import _manejar_completado
from synapse_lsp.features.definition import _manejar_definicion
from synapse_lsp.features.signature import _manejar_signature_help, _manejar_document_symbol
from synapse_lsp.features.code_action import _manejar_code_action
from synapse_lsp.features.formatting import _manejar_formatting
from synapse_lsp.features.ai import (
    _manejar_ai_complete, _manejar_ai_explain, _manejar_ai_status,
    _manejar_hover_ia, _manejar_code_action_ia,
)

# ======================================================================
# Re-exportaciones para compatibilidad de tests (importan desde
# synapse_lsp.server). Los tests no se modifican.
# ======================================================================
from synapse_lsp.features.store import _MAX_DOCS, _almacenar_documento, _obtener_documento  # noqa: F401
from synapse_lsp.features.diagnostics import _CODIGOS_OWNERSHIP, _errores_a_diagnostics, validar_documento, _agregar_error_syntax  # noqa: F401
from synapse_lsp.features.hover import _nodo_a_texto, _construir_hover_funcion, _buscar_tipo_variable_en_ast, _obtener_palabra_en_posicion, _construir_hover_variable, _buscar_llamada_en_nodo  # noqa: F401
from synapse_lsp.features.completions import _PALABRAS_CLAVE, _PALABRAS_CLAVE_LSP, _obtener_simbolos_desde_tabla  # noqa: F401
from synapse_lsp.features.code_action import _CODE_ACTIONS  # noqa: F401
from synapse_lsp.features.formatting import _formatear_codigo  # noqa: F401

_SERVER_RUNNING = True


# ======================================================================
# Enrutador principal de mensajes
# ======================================================================

def _procesar_mensaje(msg: dict) -> Optional[dict]:
    global _SERVER_RUNNING
    metodo = msg.get("method", "")
    msg_id = msg.get("id")

    if metodo == "initialize":
        _SERVER_RUNNING = True
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "capabilities": {
                    "textDocumentSync": {
                        "openClose": True,
                        "change": 1,
                        "save": {"includeText": True},
                    },
                    "hoverProvider": True,
                    "synapseAICompletionProvider": {
                        "triggerCharacters": ["//", "/**"],
                    },
                    "completionProvider": {
                        "triggerCharacters": [".", ":"],
                    },
                    "signatureHelpProvider": {
                        "triggerCharacters": ["(", ","],
                    },
                    "definitionProvider": True,
                    "documentSymbolProvider": True,
                    "codeActionProvider": True,
                    "documentFormattingProvider": True,
                },
                "serverInfo": {
                    "name": "synapse-lsp",
                    "version": "0.4.0",
                    "ai": {
                        "provider": "ollama",
                        "local_only": True,
                    },
                },
            },
        }

    if metodo == "initialized":
        return None

    if metodo == "shutdown":
        _SERVER_RUNNING = False
        _DOCS.clear()
        return {"jsonrpc": "2.0", "id": msg_id, "result": None}

    if metodo == "exit":
        _SERVER_RUNNING = False
        return None

    if metodo in ("textDocument/didOpen", "textDocument/didChange", "textDocument/didSave"):
        params = msg.get("params", {})
        doc = params.get("textDocument", {})
        uri = doc.get("uri", "")
        cambios = params.get("contentChanges", [])
        if cambios:
            texto = cambios[-1]["text"]
        else:
            texto = doc.get("text", "")
        _enviar_diagnostics_archivo(uri, texto)
        return None

    if metodo == "textDocument/didClose":
        uri = msg.get("params", {}).get("textDocument", {}).get("uri", "")
        _eliminar_documento(uri)
        notif = {
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {"uri": uri, "diagnostics": []},
        }
        _enviar_respuesta(notif)
        return None

    if metodo == "textDocument/hover":
        resultado = _manejar_hover(msg)
        ia_resultado = _manejar_hover_ia(msg)
        if ia_resultado and resultado is not None:
            if isinstance(resultado.get("contents"), dict):
                ia_markdown = ia_resultado.get("contents", {}).get("value", "")
                existing = resultado.get("contents", {}).get("value", "")
                resultado["contents"]["value"] = existing + "\n\n---\n\n" + ia_markdown
        return {"jsonrpc": "2.0", "id": msg_id, "result": resultado}

    if metodo == "textDocument/completion":
        resultado = _manejar_completado(msg)
        return {"jsonrpc": "2.0", "id": msg_id, "result": resultado}

    if metodo == "textDocument/definition":
        resultado = _manejar_definicion(msg)
        return {"jsonrpc": "2.0", "id": msg_id, "result": resultado}

    if metodo == "textDocument/signatureHelp":
        resultado = _manejar_signature_help(msg)
        return {"jsonrpc": "2.0", "id": msg_id, "result": resultado}

    if metodo == "textDocument/documentSymbol":
        resultado = _manejar_document_symbol(msg)
        return {"jsonrpc": "2.0", "id": msg_id, "result": resultado}

    if metodo == "textDocument/codeAction":
        resultado = _manejar_code_action(msg)
        ia_actions = _manejar_code_action_ia(msg)
        if ia_actions:
            if resultado is None:
                resultado = ia_actions
            else:
                resultado.extend(ia_actions)
        return {"jsonrpc": "2.0", "id": msg_id, "result": resultado}

    if metodo == "textDocument/formatting":
        resultado = _manejar_formatting(msg)
        return {"jsonrpc": "2.0", "id": msg_id, "result": resultado}

    if metodo == "synapse/aiComplete":
        resultado = _manejar_ai_complete(msg)
        return {"jsonrpc": "2.0", "id": msg_id, "result": resultado}

    if metodo == "synapse/aiExplain":
        resultado = _manejar_ai_explain(msg)
        return {"jsonrpc": "2.0", "id": msg_id, "result": resultado}

    if metodo == "synapse/aiStatus":
        resultado = _manejar_ai_status(msg)
        return {"jsonrpc": "2.0", "id": msg_id, "result": resultado}

    if msg_id is not None:
        return {"jsonrpc": "2.0", "id": msg_id, "result": None}

    return None


# ======================================================================
# Bucle daemon principal
# ======================================================================

def iniciar() -> None:
    global _SERVER_RUNNING
    _SERVER_RUNNING = True

    while _SERVER_RUNNING:
        try:
            msg = _leer_mensaje()
            if msg is None:
                _SERVER_RUNNING = False
                break

            respuesta = _procesar_mensaje(msg)
            if respuesta is not None:
                _enviar_respuesta(respuesta)

        except Exception:
            import logging
            import traceback
            logging.error("[LSP] Error fatal en bucle principal:\n%s", traceback.format_exc())
            _SERVER_RUNNING = False
            break
