import sys
import json
import textwrap
from typing import Optional, Any, List, Dict
from exceptions import SynapseError
from synapse_lsp.llm_bridge import (
    generar_completado,
    explicar_codigo,
    sugerir_correccion,
)

# ----------------------------------------------------------------------
# Synapse LSP Server — JSON-RPC 2.0 daemon over stdin/stdout
#
# Regla de Oro: NUNCA llamar a sys.exit(). NUNCA dejar que una excepcion
# del compilador suba al hilo principal. Capturar todo, formatear como
# publishDiagnostics, y seguir escuchando.
# ----------------------------------------------------------------------

_SERVER_RUNNING = True

# ----------------------------------------------------------------------
# Document Store — mantiene el AST en memoria para hover, completions, etc.
# Restriccion arquitectonica: maximo 100 documentos abiertos para evitar
# degradacion de RAM.
# ----------------------------------------------------------------------

_MAX_DOCS = 100
_DOCS: dict[str, dict] = {}  # uri -> {texto, ast, version, analizador}

def _almacenar_documento(uri: str, texto: str, ast=None, version: int = 1, analizador=None) -> None:
    if len(_DOCS) >= _MAX_DOCS:
        _DOCS.pop(next(iter(_DOCS)))
    _DOCS[uri] = {"texto": texto, "ast": ast, "version": version, "analizador": analizador}

def _eliminar_documento(uri: str) -> None:
    _DOCS.pop(uri, None)

def _obtener_documento(uri: str) -> Optional[dict]:
    return _DOCS.get(uri)


# ======================================================================
# Transport Layer — raw stdin reader for Content-Length framing
# ======================================================================

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


# ======================================================================
# Salida — respuesta JSON-RPC por stdout
# ======================================================================

def _enviar_respuesta(respuesta: dict) -> None:
    cuerpo = json.dumps(respuesta, ensure_ascii=False)
    cuerpo_bytes = cuerpo.encode("utf-8")
    raw = f"Content-Length: {len(cuerpo_bytes)}\r\n\r\n".encode("utf-8") + cuerpo_bytes
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()

def _enviar_notificacion(metodo: str, params: Any) -> None:
    _enviar_respuesta({"jsonrpc": "2.0", "method": metodo, "params": params})


# ======================================================================
# Conversion de errores internos a Diagnostics LSP
# ======================================================================

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

        mensaje = err.get("mensaje", "Error desconocido")

        # ERR_LIFETIME: anadir trazabilidad de ownership al mensaje
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


# ======================================================================
# Compilacion express (solo para diagnostics — no genera .c ni .exe)
# ======================================================================

def validar_documento(uri: str, codigo_fuente: str) -> list:
    """Ejecuta la cadena de validacion completa del compilador.
    Retorna la lista de errores internos.
    Almacena el AST y el analizador semantico en el document store.
    Nunca lanza excepcion.
    """
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

    # Almacenar el AST y analizador en el document store
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
        pass


# ======================================================================
# Hover — textDocument/hover
# ======================================================================

def _nodo_a_texto(expr) -> str:
    """Convierte un nodo de expresion a su representacion Synapse."""
    from compilador.ast_nodes import (
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
    from compilador.ast_nodes import DefinicionFuncion
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

def _buscar_tipo_variable_en_ast(ast, nombre: str) -> Optional[str]:
    from compilador.ast_nodes import (
        Nodo, DeclaracionVariable, AsignacionVariable,
        LiteralNumero, LiteralDecimal, LiteralCadena, LiteralBooleano,
        SentenciaSi, SentenciaMientras, SentenciaPara, BloqueInseguro,
        DefinicionFuncion, Programa,
    )
    def _recorrer_nodos(nodos):
        for n in nodos:
            if isinstance(n, DeclaracionVariable) and n.nombre == nombre:
                return n.tipo
            if isinstance(n, AsignacionVariable) and n.nombre == nombre:
                if isinstance(n.expresion, LiteralNumero):
                    return 'entero'
                if isinstance(n.expresion, LiteralDecimal):
                    return 'decimal'
                if isinstance(n.expresion, LiteralCadena):
                    return 'texto'
                if isinstance(n.expresion, LiteralBooleano):
                    return 'booleano'
                return 'entero'
            hijos = []
            if hasattr(n, 'cuerpo') and isinstance(n.cuerpo, list):
                hijos.extend(n.cuerpo)
            if hasattr(n, 'cuerpo_sino') and isinstance(n.cuerpo_sino, list):
                hijos.extend(n.cuerpo_sino)
            if isinstance(n, (SentenciaSi, SentenciaMientras, SentenciaPara, BloqueInseguro)):
                if hasattr(n, 'condicion') and isinstance(n.condicion, Nodo):
                    pass
            if hasattr(n, 'sentencias') and isinstance(n.sentencias, list):
                hijos.extend(n.sentencias)
            if hijos:
                r = _recorrer_nodos(hijos)
                if r:
                    return r
        return None

    if isinstance(ast, Programa):
        return _recorrer_nodos(ast.sentencias)
    return _recorrer_nodos([ast])

def _obtener_palabra_en_posicion(texto: str, linea: int, columna: int) -> Optional[str]:
    lineas = texto.split("\n")
    if linea < 0 or linea >= len(lineas):
        return None
    linea_texto = lineas[linea]
    if columna < 0 or columna >= len(linea_texto):
        return None
    inicio = columna
    while inicio > 0 and (linea_texto[inicio - 1].isalnum() or linea_texto[inicio - 1] == '_'):
        inicio -= 1
    fin = columna
    while fin < len(linea_texto) and (linea_texto[fin].isalnum() or linea_texto[fin] == '_'):
        fin += 1
    return linea_texto[inicio:fin]

def _construir_hover_variable(nombre: str, tipo: str) -> dict:
    return {
        "contents": {
            "kind": "markdown",
            "value": f"```synapse\n{nombre}: {tipo}\n```",
        }
    }

def _manejar_hover(msg: dict) -> Optional[dict]:
    params = msg.get("params", {})
    doc = params.get("textDocument", {})
    uri = doc.get("uri", "")
    pos = params.get("position", {})
    linea = pos.get("line", 0)
    columna = pos.get("character", 0)

    doc_info = _obtener_documento(uri)
    if doc_info is None or doc_info["ast"] is None:
        return None

    from compilador.ast_nodes import Programa, DefinicionFuncion as _DF

    ast = doc_info["ast"]
    if not isinstance(ast, Programa):
        return None

    texto = doc_info["texto"]

    for s in ast.sentencias:
        if isinstance(s, _DF):
            fn_linea = s.linea - 1
            if fn_linea == linea:
                resultado = _construir_hover_funcion(s)
                if resultado:
                    return resultado

            for stmt in s.cuerpo:
                resultado = _buscar_llamada_en_nodo(stmt, linea, columna, ast)
                if resultado:
                    return resultado

    palabra = _obtener_palabra_en_posicion(texto, linea, columna)
    if palabra:
        tipo = _buscar_tipo_variable_en_ast(ast, palabra)
        if tipo:
            return _construir_hover_variable(palabra, tipo)

    return None

def _buscar_llamada_en_nodo(nodo, linea: int, columna: int, programa) -> Optional[dict]:
    from compilador.ast_nodes import (
        DefinicionFuncion, LlamadaFuncion, SentenciaExpr, AsignacionVariable,
        SentenciaSi, SentenciaMientras, SentenciaRetornar,
        OpBinaria, OpUnaria, ExprAccesoCampo,
    )

    if isinstance(nodo, LlamadaFuncion):
        if nodo.linea - 1 == linea:
            for s in programa.sentencias:
                if isinstance(s, DefinicionFuncion) and s.nombre == nodo.nombre:
                    return _construir_hover_funcion(s)
        return None

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


# ======================================================================
# Completado — textDocument/completion
# ======================================================================

_PALABRAS_CLAVE = [
    "si", "sino", "funcion", "retornar", "mientras", "para",
    "romper", "siguiente", "importar", "estructura", "coincidir",
    "lanzar", "recuperar", "escuchar", "inseguro", "externo",
    "constante", "verdadero", "falso", "y", "o", "no",
    "requiere", "garantiza", "canal", "asm",
]

_PALABRAS_CLAVE_LSP = [
    {"label": "si", "kind": 14, "detail": "keyword"},
    {"label": "sino", "kind": 14, "detail": "keyword"},
    {"label": "funcion", "kind": 14, "detail": "keyword"},
    {"label": "retornar", "kind": 14, "detail": "keyword"},
    {"label": "mientras", "kind": 14, "detail": "keyword"},
    {"label": "para", "kind": 14, "detail": "keyword"},
    {"label": "romper", "kind": 14, "detail": "keyword"},
    {"label": "siguiente", "kind": 14, "detail": "keyword"},
    {"label": "importar", "kind": 14, "detail": "keyword"},
    {"label": "estructura", "kind": 14, "detail": "keyword"},
    {"label": "coincidir", "kind": 14, "detail": "keyword"},
    {"label": "lanzar", "kind": 14, "detail": "keyword"},
    {"label": "recuperar", "kind": 14, "detail": "keyword"},
    {"label": "escuchar", "kind": 14, "detail": "keyword"},
    {"label": "inseguro", "kind": 14, "detail": "keyword"},
    {"label": "externo", "kind": 14, "detail": "keyword"},
    {"label": "constante", "kind": 14, "detail": "keyword"},
    {"label": "verdadero", "kind": 14, "detail": "keyword"},
    {"label": "falso", "kind": 14, "detail": "keyword"},
    {"label": "y", "kind": 14, "detail": "keyword"},
    {"label": "o", "kind": 14, "detail": "keyword"},
    {"label": "no", "kind": 14, "detail": "keyword"},
    {"label": "requiere", "kind": 14, "detail": "keyword"},
    {"label": "garantiza", "kind": 14, "detail": "keyword"},
    {"label": "canal", "kind": 14, "detail": "keyword"},
    {"label": "asm", "kind": 14, "detail": "keyword"},
]

def _obtener_simbolos_desde_tabla(uri: str) -> list:
    doc_info = _obtener_documento(uri)
    if doc_info is None or doc_info["ast"] is None:
        return []
    from compilador.ast_nodes import Programa
    from compilador.diagnostics import DiagnosticManager
    from compilador.analizador_semantico import AnalizadorSemantico

    ast = doc_info["ast"]
    if not isinstance(ast, Programa):
        return []

    # Reutilizar analizador almacenado si existe
    analizador = doc_info.get("analizador")
    if analizador is None:
        texto = doc_info["texto"]
        fuente_lineas = texto.split("\n")
        diag = DiagnosticManager(fuente_lineas=fuente_lineas, ruta_archivo=uri)
        analizador = AnalizadorSemantico(ast, diag)
        try:
            analizador.analizar()
        except Exception:
            pass

    simbolos = []
    try:
        for nombre, sim in analizador.tabla._scopes[-1].items():
            simbolos.append({
                "label": nombre,
                "kind": 6,
                "detail": sim.tipo,
            })
    except (IndexError, AttributeError):
        pass
    return simbolos

def _manejar_completado(msg: dict) -> Optional[dict]:
    params = msg.get("params", {})
    doc = params.get("textDocument", {})
    uri = doc.get("uri", "")

    items = list(_PALABRAS_CLAVE_LSP)
    simbolos = _obtener_simbolos_desde_tabla(uri)
    items.extend(simbolos)

    return {"isIncomplete": False, "items": items}


# ======================================================================
# Definicion — textDocument/definition
# ======================================================================

def _manejar_definicion(msg: dict) -> Optional[dict]:
    params = msg.get("params", {})
    doc = params.get("textDocument", {})
    uri = doc.get("uri", "")
    pos = params.get("position", {})
    linea = pos.get("line", 0)
    columna = pos.get("character", 0)

    doc_info = _obtener_documento(uri)
    if doc_info is None or doc_info["ast"] is None:
        return None

    texto = doc_info["texto"]
    palabra = _obtener_palabra_en_posicion(texto, linea, columna)
    if not palabra:
        return None

    from compilador.ast_nodes import (
        DeclaracionVariable, AsignacionVariable, DefinicionFuncion, Programa,
    )

    ast = doc_info["ast"]
    if not isinstance(ast, Programa):
        return None

    def _buscar_declaracion(nodos):
        for n in nodos:
            if isinstance(n, DeclaracionVariable) and n.nombre == palabra:
                return n.linea, n.columna, len(palabra)
            if isinstance(n, AsignacionVariable) and n.nombre == palabra:
                return n.linea, n.columna, len(palabra)
            if isinstance(n, DefinicionFuncion) and n.nombre == palabra:
                return n.linea, n.columna, len(palabra)
            hijos = []
            if hasattr(n, 'cuerpo') and isinstance(n.cuerpo, list):
                hijos.extend(n.cuerpo)
            if hasattr(n, 'cuerpo_sino') and isinstance(n.cuerpo_sino, list):
                hijos.extend(n.cuerpo_sino)
            if hasattr(n, 'sentencias') and isinstance(n.sentencias, list):
                hijos.extend(n.sentencias)
            if hijos:
                r = _buscar_declaracion(hijos)
                if r:
                    return r
        return None

    loc = _buscar_declaracion(ast.sentencias)
    if loc is None:
        return None

    def_linea, def_col, largo = loc
    return {
        "uri": uri,
        "range": {
            "start": {"line": max(0, def_linea - 1), "character": def_col},
            "end": {"line": max(0, def_linea - 1), "character": def_col + largo},
        },
    }


# ======================================================================
# F12.1: SignatureHelp — textDocument/signatureHelp
# Muestra la firma de la funcion cuando el usuario escribe '('
# ======================================================================

def _manejar_signature_help(msg: dict) -> Optional[dict]:
    params = msg.get("params", {})
    doc = params.get("textDocument", {})
    uri = doc.get("uri", "")
    pos = params.get("position", {})
    linea = pos.get("line", 0)
    columna = pos.get("character", 0)

    doc_info = _obtener_documento(uri)
    if doc_info is None or doc_info["ast"] is None:
        return None

    texto = doc_info["texto"]
    # Obtener el nombre de la funcion antes del cursor
    lineas = texto.split("\n")
    if linea < 0 or linea >= len(lineas):
        return None
    linea_texto = lineas[linea][:columna]
    # Buscar el ultimo '(' y el identificador antes
    paren_idx = linea_texto.rfind("(")
    if paren_idx < 0:
        return None
    antes_paren = linea_texto[:paren_idx].rstrip()
    palabras = antes_paren.split()
    if not palabras:
        return None
    nombre_funcion = palabras[-1].strip()

    from compilador.ast_nodes import Programa, DefinicionFuncion
    ast = doc_info["ast"]
    if not isinstance(ast, Programa):
        return None

    # Buscar la funcion en el AST
    for s in ast.sentencias:
        if isinstance(s, DefinicionFuncion) and s.nombre == nombre_funcion:
            params_str = ", ".join(
                f"{p.nombre}: {p.tipo}" for p in s.parametros
            )
            ret = s.tipo_retorno if s.tipo_retorno else "nulo"
            label = f"funcion {s.nombre}({params_str}) -> {ret}"
            signature = {
                "label": label,
                "parameters": [
                    {"label": f"{p.nombre}: {p.tipo}"}
                    for p in s.parametros
                ],
            }
            # Calcular activeParameter basado en cuantos argumentos ya hay escritos
            after_paren = lineas[linea][columna:] if columna < len(lineas[linea]) else ""
            # Contar comas en el texto desde el paren hasta el cursor
            # (para editores que pasan el cursor DENTRO de los parens)
            texto_argumentos = lineas[linea][paren_idx+1:columna]
            # Contar comas no anidadas para determinar el parametro activo
            nivel = 0
            comas = 0
            for c in texto_argumentos:
                if c == '(':
                    nivel += 1
                elif c == ')':
                    nivel -= 1
                elif c == ',' and nivel == 0:
                    comas += 1
            active_param = min(comas, len(s.parametros) - 1) if s.parametros else 0

            return {
                "signatures": [signature],
                "activeSignature": 0,
                "activeParameter": max(0, active_param),
            }

    return None


# ======================================================================
# F12.1: DocumentSymbol — textDocument/documentSymbol
# Arbol de simbolos para outline/navegacion
# ======================================================================

def _manejar_document_symbol(msg: dict) -> Optional[list]:
    params = msg.get("params", {})
    doc = params.get("textDocument", {})
    uri = doc.get("uri", "")

    doc_info = _obtener_documento(uri)
    if doc_info is None or doc_info["ast"] is None:
        return None

    from compilador.ast_nodes import (
        Programa, DefinicionFuncion, DefinicionEstructura,
        DeclaracionExterna, StmtConstante, DeclaracionVariable,
    )

    ast = doc_info["ast"]
    if not isinstance(ast, Programa):
        return None

    symbols = []

    # Tipos de simbolos LSP:
    # 1=File, 2=Module, 3=Namespace, 4=Package, 5=Class, 6=Method,
    # 7=Property, 8=Field, 9=Constructor, 10=Enum, 11=Interface,
    # 12=Function, 13=Variable, 14=Constant, 15=String, 16=Number,
    # 17=Boolean, 18=Array, 19=Object, 20=Key, 21=Null, 22=EnumMember,
    # 23=Struct, 24=Event, 25=Operator, 26=TypeParameter

    for s in ast.sentencias:
        if isinstance(s, DefinicionFuncion):
            nombre = s.nombre
            params_str = ", ".join(f"{p.nombre}: {p.tipo}" for p in s.parametros)
            ret = s.tipo_retorno if s.tipo_retorno else "nulo"
            symbols.append({
                "name": nombre,
                "kind": 12,  # Function
                "detail": f"({params_str}) -> {ret}",
                "range": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, (s.linea or 0) + 0), "character": s.columna + len(nombre)},
                },
                "selectionRange": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, s.linea - 1), "character": s.columna + len(nombre)},
                },
                "children": [],
            })
            # Anadir parametros como hijos
            for p in s.parametros:
                symbols[-1]["children"].append({
                    "name": p.nombre,
                    "kind": 13,  # Variable
                    "detail": p.tipo,
                    "range": {
                        "start": {"line": max(0, s.linea - 1), "character": 0},
                        "end": {"line": max(0, s.linea - 1), "character": 0},
                    },
                    "selectionRange": {
                        "start": {"line": max(0, s.linea - 1), "character": 0},
                        "end": {"line": max(0, s.linea - 1), "character": 0},
                    },
                })

        elif isinstance(s, DefinicionEstructura):
            symbols.append({
                "name": s.nombre,
                "kind": 23,  # Struct
                "range": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, s.linea - 1), "character": s.columna + len(s.nombre)},
                },
                "selectionRange": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, s.linea - 1), "character": s.columna + len(s.nombre)},
                },
                "children": [
                    {
                        "name": c.nombre,
                        "kind": 8,  # Field
                        "detail": c.tipo,
                        "range": {
                            "start": {"line": max(0, getattr(c, 'linea', 1) - 1), "character": getattr(c, 'columna', 0)},
                            "end": {"line": max(0, getattr(c, 'linea', 1) - 1), "character": getattr(c, 'columna', 0) + len(c.nombre)},
                        },
                        "selectionRange": {
                            "start": {"line": max(0, getattr(c, 'linea', 1) - 1), "character": getattr(c, 'columna', 0)},
                            "end": {"line": max(0, getattr(c, 'linea', 1) - 1), "character": getattr(c, 'columna', 0) + len(c.nombre)},
                        },
                    }
                    for c in (s.campos if hasattr(s, 'campos') else [])
                ],
            })

        elif isinstance(s, DeclaracionExterna):
            symbols.append({
                "name": s.nombre,
                "kind": 12,  # Function
                "detail": "externo",
                "range": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, s.linea - 1), "character": s.columna + len(s.nombre)},
                },
                "selectionRange": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, s.linea - 1), "character": s.columna + len(s.nombre)},
                },
            })

        elif isinstance(s, StmtConstante):
            symbols.append({
                "name": s.nombre,
                "kind": 14,  # Constant
                "detail": "constante",
                "range": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, s.linea - 1), "character": s.columna + len(s.nombre)},
                },
                "selectionRange": {
                    "start": {"line": max(0, s.linea - 1), "character": s.columna},
                    "end": {"line": max(0, s.linea - 1), "character": s.columna + len(s.nombre)},
                },
            })

    return symbols


# ======================================================================
# F12.1: CodeAction — textDocument/codeAction
# Quick fixes para errores comunes del compilador
# ======================================================================

# Mapa de codigos de error a acciones de quick fix
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
                                "newText": "",  # Placeholder
                            }
                        ]
                    }
                },
                "isPreferred": False,
            })

    return actions if actions else None


# ======================================================================
# F12.1: Formateo — textDocument/formatting
# Formateador basico: indentacion consistente, espacios, saltos de linea
# ======================================================================

def _formatear_codigo(texto: str, tab_size: int = 4) -> str:
    """Formateador basico para codigo Synapse.
    - Normaliza indentacion a 4 espacios
    - Elimina espacios al final de lineas
    - Normaliza saltos de linea
    """
    lineas = texto.split("\n")
    resultado = []
    indent_level = 0

    for linea in lineas:
        stripped = linea.strip()

        # Lineas vacias: preservar sin modificar indentacion
        if not stripped:
            resultado.append("")
            continue

        # Disminuir indentacion si la linea comienza con cierre de bloque
        if stripped in ("}", "])", ")", ":") or stripped.startswith("sino") or stripped.startswith("fin"):
            indent_level = max(0, indent_level - 1)

        resultado.append(" " * (indent_level * tab_size) + stripped)

        # Aumentar indentacion si la linea termina con ':'
        if stripped.endswith(":") and not stripped.startswith("#"):
            indent_level += 1
        # Aumentar para estructuras de control
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
    lineas_formateadas = texto_formateado.split("\n")

    # Si no hay cambios, retornar array vacio
    if texto_original == texto_formateado:
        return []

    # Aplicar cambio full-documento
    return [
        {
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": len(lineas_original), "character": 0},
            },
            "newText": texto_formateado,
        }
    ]


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
        # Enriquecer con IA local si esta disponible
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
        # Enriquecer con IA local
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

    # ======================================================================
    # F12.3: LLM Local - Metodos personalizados de IA
    # ======================================================================
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
# F12.3: Manejadores de IA Local
# ======================================================================

def _manejar_ai_complete(msg: dict) -> Optional[dict]:
    """synapse/aiComplete: Genera codigo Synapse con IA local."""
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
    """synapse/aiExplain: Explica codigo Synapse con IA local."""
    params = msg.get("params", {})
    uri = params.get("textDocument", {}).get("uri", "")
    codigo = params.get("code", "")

    if not codigo:
        doc_info = _obtener_documento(uri)
        if doc_info:
            # Extraer la linea o bloque alrededor del cursor
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
    """synapse/aiStatus: Verifica disponibilidad de IA local."""
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
    """Enriquece el hover con explicacion de IA si esta disponible."""
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

    # Obtener la linea actual para contexto
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
    """Anade code actions potenciados por IA local."""
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

        # Solo para errores de compilacion conocidos
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
            break  # Solo una sugerencia por request para evitar spam

    return actions if actions else None


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
            _SERVER_RUNNING = False
            break
