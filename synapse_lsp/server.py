import sys
import json
from typing import Optional, Any

# ──────────────────────────────────────────────────────────────────────
# Synapse LSP Server — JSON-RPC 2.0 daemon over stdin/stdout
#
# Regla de Oro: NUNCA llamar a sys.exit(). NUNCA dejar que una excepción
# del compilador suba al hilo principal. Capturar todo, formatear como
# publishDiagnostics, y seguir escuchando.
# ──────────────────────────────────────────────────────────────────────

_SERVER_RUNNING = True


# ═══════════════════════════════════════════════════════════════════════
# Transport Layer — raw stdin reader for Content-Length framing
#
# Punto histórico de falla del 90% de los servidores LSP artesanales.
# Debe ser robusto contra:
#   - Líneas extra entre cabeceras
#   - Whitespace alrededor del número
#   - Content-Length malformado
#   - EOF prematuro sin mensaje
# ═══════════════════════════════════════════════════════════════════════

def _leer_mensaje() -> Optional[dict]:
    content_length: Optional[int] = None
    buf = b""

    while True:
        byte = sys.stdin.buffer.read(1)
        if not byte:
            return None
        buf += byte

        if buf.endswith(b"\r\n\r\n"):
            header_section = buf[:-4].decode("utf-8", errors="replace")
            for line in header_section.split("\r\n"):
                if line.lower().startswith("content-length:"):
                    raw_value = line.split(":", 1)[1].strip()
                    try:
                        content_length = int(raw_value)
                    except ValueError:
                        content_length = 0
                    break

            if content_length is None:
                content_length = 0

            body_bytes = sys.stdin.buffer.read(content_length)
            if len(body_bytes) != content_length:
                return None

            try:
                return json.loads(body_bytes.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return None

        if len(buf) > 4096:
            return None


# ═══════════════════════════════════════════════════════════════════════
# Salida — respuesta JSON-RPC por stdout
# ═══════════════════════════════════════════════════════════════════════

def _enviar_respuesta(respuesta: dict) -> None:
    cuerpo = json.dumps(respuesta, ensure_ascii=False)
    raw = f"Content-Length: {len(cuerpo)}\r\n\r\n{cuerpo}"
    sys.stdout.buffer.write(raw.encode("utf-8"))
    sys.stdout.buffer.flush()


def _enviar_notificacion(metodo: str, params: Any) -> None:
    _enviar_respuesta({"jsonrpc": "2.0", "method": metodo, "params": params})


# ═══════════════════════════════════════════════════════════════════════
# Conversión de errores internos → Diagnostics LSP
# ═══════════════════════════════════════════════════════════════════════

def _errores_a_diagnostics(errores: list) -> list:
    lsp_diags = []
    for err in errores:
        syn_linea = err.get("linea", 0)
        syn_columna = err.get("columna", 0)
        codigo = err.get("codigo", "")
        if hasattr(codigo, "name"):
            codigo = codigo.name
        lsp_diags.append({
            "range": {
                "start": {"line": max(0, syn_linea - 1), "character": syn_columna},
                "end": {"line": max(0, syn_linea - 1), "character": syn_columna + 1},
            },
            "severity": 1,
            "code": str(codigo),
            "source": "synapse",
            "message": err.get("mensaje", "Error desconocido"),
        })
    return lsp_diags


# ═══════════════════════════════════════════════════════════════════════
# Compilación exprés (solo para diagnostics — no genera .c ni .exe)
# ═══════════════════════════════════════════════════════════════════════

def _compilar_archivo(texto: str, ruta: str) -> list:
    from lexer import Lexer
    from parser import Parser
    from diagnostics import DiagnosticManager
    from analizador_semantico import AnalizadorSemantico

    fuente_lineas = texto.split("\n")
    diag = DiagnosticManager(fuente_lineas=fuente_lineas, ruta_archivo=ruta)

    try:
        lexer = Lexer(texto, diag)
        tokens = lexer.tokenizar()
    except Exception:
        return diag.errores

    try:
        parser = Parser(tokens, diag)
        ast = parser.parsear()
    except Exception:
        return diag.errores

    try:
        analizador = AnalizadorSemantico(ast, diag)
        analizador.analizar()
    except Exception:
        pass

    return diag.errores


def _enviar_diagnostics_archivo(uri: str, texto: str) -> None:
    try:
        errores = _compilar_archivo(texto, uri)
        lsp_diags = _errores_a_diagnostics(errores) if errores else []
        _enviar_notificacion("textDocument/publishDiagnostics", {
            "uri": uri,
            "diagnostics": lsp_diags,
        })
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════
# Enrutador de mensajes JSON-RPC
# ═══════════════════════════════════════════════════════════════════════

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
                },
                "serverInfo": {
                    "name": "synapse-lsp",
                    "version": "0.1.0",
                },
            },
        }

    if metodo == "initialized":
        return None

    if metodo == "shutdown":
        _SERVER_RUNNING = False
        return {"jsonrpc": "2.0", "id": msg_id, "result": None}

    if metodo == "exit":
        _SERVER_RUNNING = False
        return None

    if metodo in ("textDocument/didOpen", "textDocument/didChange",
                  "textDocument/didSave"):
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
        notif = {
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {"uri": uri, "diagnostics": []},
        }
        _enviar_respuesta(notif)
        return None

    if msg_id is not None:
        return {"jsonrpc": "2.0", "id": msg_id, "result": None}

    return None


# ═══════════════════════════════════════════════════════════════════════
# Bucle daemon principal
# ═══════════════════════════════════════════════════════════════════════

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
            _SERVER_RUNNING = False
            break