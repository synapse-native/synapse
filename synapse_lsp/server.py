import sys
import json
from typing import Optional, Any
from exceptions import SynapseError

# ──────────────────────────────────────────────────────────────────────
# Synapse LSP Server — JSON-RPC 2.0 daemon over stdin/stdout
#
# Regla de Oro: NUNCA llamar a sys.exit(). NUNCA dejar que una excepción
# del compilador suba al hilo principal. Capturar todo, formatear como
# publishDiagnostics, y seguir escuchando.
# ──────────────────────────────────────────────────────────────────────

_SERVER_RUNNING = True

# ──────────────────────────────────────────────────────────────────────
# Document Store — mantiene el AST en memoria para hover, completions, etc.
# Restricción arquitectónica: máximo 100 documentos abiertos para evitar
# degradación de RAM.
# ──────────────────────────────────────────────────────────────────────

_MAX_DOCS = 100
_DOCS: dict[str, dict] = {}  # uri -> {texto, ast, version}


def _almacenar_documento(uri: str, texto: str, ast=None, version: int = 1) -> None:
    if len(_DOCS) >= _MAX_DOCS:
        _DOCS.pop(next(iter(_DOCS)))
    _DOCS[uri] = {"texto": texto, "ast": ast, "version": version}


def _eliminar_documento(uri: str) -> None:
    _DOCS.pop(uri, None)


def _obtener_documento(uri: str) -> Optional[dict]:
    return _DOCS.get(uri)


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
    cuerpo_bytes = cuerpo.encode("utf-8")
    raw = f"Content-Length: {len(cuerpo_bytes)}\r\n\r\n".encode("utf-8") + cuerpo_bytes
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()


def _enviar_notificacion(metodo: str, params: Any) -> None:
    _enviar_respuesta({"jsonrpc": "2.0", "method": metodo, "params": params})


# ═══════════════════════════════════════════════════════════════════════
# Conversión de errores internos → Diagnostics LSP
#
# Los errores de ownership (E-501, E-502, E-503) se convierten con
# severidad 1 (Error) para que aparezcan como líneas rojas onduladas
# en el editor en el momento exacto de la infracción.
# ═══════════════════════════════════════════════════════════════════════

_CODIGOS_OWNERSHIP = frozenset({
    "ERR_SEM_VAR_MOVIDA",
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

        lsp_diags.append({
            "range": {
                "start": {"line": max(0, syn_linea - 1), "character": syn_columna},
                "end": {"line": max(0, syn_linea - 1), "character": syn_columna + 1},
            },
            "severity": 1,
            "code": codigo_str,
            "source": "synapse",
            "message": err.get("mensaje", "Error desconocido"),
        })
    return lsp_diags


# ═══════════════════════════════════════════════════════════════════════
# Compilación exprés (solo para diagnostics — no genera .c ni .exe)
# ═══════════════════════════════════════════════════════════════════════

def validar_documento(uri: str, codigo_fuente: str) -> list:
    """Ejecuta la cadena de validación completa del compilador.
    Retorna la lista de errores internos (cada uno con 'codigo', 'linea', 'columna', 'mensaje').
    Nunca lanza excepción.
    """
    import traceback
    try:
        from lexer import Lexer
    except Exception as e:
        sys.stderr.write(f"[LSP] ERROR importing Lexer: {e}\n{traceback.format_exc()}\n")
        sys.stderr.flush()
        return []
    try:
        from parser import Parser
    except Exception as e:
        sys.stderr.write(f"[LSP] ERROR importing Parser: {e}\n")
        sys.stderr.flush()
        return []
    from diagnostics import DiagnosticManager
    try:
        from analizador_semantico import AnalizadorSemantico
    except Exception as e:
        sys.stderr.write(f"[LSP] ERROR importing AnalizadorSemantico: {e}\n")
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

    try:
        analizador = AnalizadorSemantico(ast, diag)
        analizador.analizar()
    except Exception as exc:
        sys.stderr.write(f"[LSP] Semantic exception: {exc}\n{traceback.format_exc()}\n")
        sys.stderr.flush()

    # Almacenar el AST en el document store para hover/completions
    _almacenar_documento(uri, codigo_fuente, ast)

    return diag.errores


def _agregar_error_syntax(diag, error):
    from diagnostics import ErrorCodes
    from ast_nodes import Token, TokenID
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
        pass


# ═══════════════════════════════════════════════════════════════════════
# Manejador de Hover — expone contratos (requiere/garantiza)
#
# Cuando el usuario pasa el cursor sobre una función, el LSP responde
# con su firma completa y los bloques de requiere/garantiza.
# ═══════════════════════════════════════════════════════════════════════

def _nodo_a_texto(expr) -> str:
    """Convierte un nodo de expresión a su representación Synapse."""
    from ast_nodes import (
        LiteralNumero, LiteralDecimal, LiteralCadena, Identificador,
        OpBinaria, OpUnaria, LlamadaFuncion, ExprAccesoCampo,
    )
    if isinstance(expr, LiteralNumero):
        return str(expr.valor)
    if isinstance(expr, LiteralDecimal):
        return str(expr.valor)
    if isinstance(expr, LiteralCadena):
        return f'"{expr.valor}"'
    if isinstance(expr, Identificador):
        return expr.nombre
    if isinstance(expr, OpBinaria):
        izq = _nodo_a_texto(expr.izquierdo)
        der = _nodo_a_texto(expr.derecho)
        return f"({izq} {expr.operador} {der})"
    if isinstance(expr, OpUnaria):
        return f"({expr.operador}{_nodo_a_texto(expr.expr)})"
    if isinstance(expr, LlamadaFuncion):
        args = ", ".join(_nodo_a_texto(a) for a in expr.argumentos)
        return f"{expr.nombre}({args})"
    if isinstance(expr, ExprAccesoCampo):
        return f"{_nodo_a_texto(expr.objeto)}.{expr.nombre_campo}"
    return "?"


def _construir_hover_funcion(fn) -> Optional[dict]:
    """Construye contenido hover para una DefinicionFuncion."""
    from ast_nodes import DefinicionFuncion
    if not isinstance(fn, DefinicionFuncion):
        return None

    params_str = ", ".join(f"{p.nombre}: {p.tipo}" for p in fn.parametros)
    ret = fn.tipo_retorno if fn.tipo_retorno else "nulo"

    lines = [f"```synapse"]
    lines.append(f"funcion {fn.nombre}({params_str}) -> {ret}")

    if fn.requiere:
        lines.append("    requiere:")
        for r in fn.requiere:
            lines.append(f"        {_nodo_a_texto(r)}")

    if fn.garantiza:
        lines.append("    garantiza:")
        for g in fn.garantiza:
            lines.append(f"        {_nodo_a_texto(g)}")

    lines.append("```")
    markdown = "\n".join(lines)

    return {
        "contents": {
            "kind": "markdown",
            "value": markdown,
        }
    }


def _manejar_hover(msg: dict) -> Optional[dict]:
    """Responde a textDocument/hover buscando la función en la posición del cursor."""
    params = msg.get("params", {})
    doc = params.get("textDocument", {})
    uri = doc.get("uri", "")
    pos = params.get("position", {})
    linea = pos.get("line", 0)      # 0-based
    columna = pos.get("character", 0)  # 0-based

    doc_info = _obtener_documento(uri)
    if doc_info is None or doc_info["ast"] is None:
        return None

    from ast_nodes import Programa, DefinicionFuncion, LlamadaFuncion

    ast = doc_info["ast"]
    if not isinstance(ast, Programa):
        return None

    texto = doc_info["texto"]
    lineas = texto.split("\n")

    from ast_nodes import DefinicionFuncion as _DF

    # Buscar la función en cuyo rango de definición cae el cursor
    for s in ast.sentencias:
        if isinstance(s, _DF):
            fn_linea = s.linea - 1
            if fn_linea == linea:
                resultado = _construir_hover_funcion(s)
                if resultado:
                    return resultado

            # Buscar llamadas dentro del cuerpo de la función
            for stmt in s.cuerpo:
                resultado = _buscar_llamada_en_nodo(stmt, linea, columna, ast)
                if resultado:
                    return resultado

    return None


def _buscar_llamada_en_nodo(nodo, linea: int, columna: int, programa) -> Optional[dict]:
    """Busca recursivamente una LlamadaFuncion en la posición dada y resuelve su definición."""
    from ast_nodes import (
        DefinicionFuncion, LlamadaFuncion, SentenciaExpr, AsignacionVariable,
        SentenciaSi, SentenciaMientras, SentenciaRetornar,
        OpBinaria, OpUnaria, ExprAccesoCampo,
    )

    if hasattr(nodo, 'linea') and hasattr(nodo, 'columna'):
        if nodo.linea - 1 == linea:
            pass  # podría estar en la línea correcta

    if isinstance(nodo, LlamadaFuncion):
        if nodo.linea - 1 == linea:
            # Resolver la definición de la función llamada
            for s in programa.sentencias:
                if isinstance(s, DefinicionFuncion) and s.nombre == nodo.nombre:
                    return _construir_hover_funcion(s)
        return None

    # Recorrer hijos según el tipo de nodo
    if isinstance(nodo, SentenciaExpr):
        return _buscar_llamada_en_nodo(nodo.expr, linea, columna, programa)

    if isinstance(nodo, AsignacionVariable):
        return _buscar_llamada_en_nodo(nodo.expresion, linea, columna, programa)

    if type(nodo).__name__ == 'SentenciaRetornar':
        if nodo.expr:
            return _buscar_llamada_en_nodo(nodo.expr, linea, columna, programa)

    if isinstance(nodo, OpBinaria):
        r = _buscar_llamada_en_nodo(nodo.izquierdo, linea, columna, programa)
        if r:
            return r
        return _buscar_llamada_en_nodo(nodo.derecho, linea, columna, programa)

    if isinstance(nodo, OpUnaria):
        return _buscar_llamada_en_nodo(nodo.expr, linea, columna, programa)

    if isinstance(nodo, ExprAccesoCampo):
        return _buscar_llamada_en_nodo(nodo.objeto, linea, columna, programa)

    if isinstance(nodo, SentenciaSi):
        r = _buscar_llamada_en_nodo(nodo.condicion, linea, columna, programa)
        if r:
            return r
        for s in (nodo.cuerpo or []):
            r = _buscar_llamada_en_nodo(s, linea, columna, programa)
            if r:
                return r
        for s in (nodo.cuerpo_sino or []):
            r = _buscar_llamada_en_nodo(s, linea, columna, programa)
            if r:
                return r
        return None

    if isinstance(nodo, SentenciaMientras):
        r = _buscar_llamada_en_nodo(nodo.condicion, linea, columna, programa)
        if r:
            return r
        for s in (nodo.cuerpo or []):
            r = _buscar_llamada_en_nodo(s, linea, columna, programa)
            if r:
                return r
        return None

    return None


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
                    "hoverProvider": True,
                },
                "serverInfo": {
                    "name": "synapse-lsp",
                    "version": "0.2.0",
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
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": resultado,
        }

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
