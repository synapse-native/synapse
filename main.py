import os
import sys
import json
import argparse
from typing import List, Optional, Dict, Tuple, Any

from compilador.ast_nodes import (
    TokenID, Token, Nodo, Programa, Parametro,
    DefinicionFuncion, DefinicionEstructura, ExprAccesoCampo, AsignacionCampo,
    SentenciaSi, SentenciaLanzar, SentenciaRecuperar,
    SentenciaRetornar, SentenciaEscuchar, SentenciaMientras,
    SentenciaRomper, SentenciaSiguiente,
    SentenciaExpr, AsignacionVariable, LogLlamada, SentenciaImportar,
    OpBinaria, OpUnaria, LlamadaFuncion, Identificador,
    LiteralNumero, LiteralDecimal, LiteralCadena, ExprTensor, ArgumentoTransferido,
    DeclaracionExterna, StmtConstante,
)
from compilador.lexer import Lexer, DICCIONARIOS, DICCIONARIOS_INVERSO
from exceptions import SynapseError
from compilador.parser import Parser
from compilador.generator import GeneradorC
from compilador.diagnostics import DiagnosticManager, ErrorCodes
from compilador.analizador_semantico import AnalizadorSemantico
from compilador.resolvedor_axon import resolver as _resolver_axon, DepNoDeclaradaError



# ============================================================
# AST PRINTER (DEBUG)
# ============================================================
def imprimir_ast(nodo: Nodo, nivel: int = 0):
    prefijo = "  " * nivel

    if isinstance(nodo, Programa):
        print(f"{prefijo}Programa:")
        for s in nodo.sentencias:
            imprimir_ast(s, nivel + 1)

    elif isinstance(nodo, DefinicionFuncion):
        params = ", ".join(f"{p.nombre}: {p.tipo}" for p in nodo.parametros)
        print(f"{prefijo}Función: {nodo.nombre}({params}) -> {nodo.tipo_retorno}")
        for s in nodo.cuerpo:
            imprimir_ast(s, nivel + 1)

    elif isinstance(nodo, SentenciaSi):
        print(f"{prefijo}Si:")
        imprimir_ast(nodo.condicion, nivel + 1)
        print(f"{prefijo}Cuerpo:")
        for s in nodo.cuerpo:
            imprimir_ast(s, nivel + 1)
        if nodo.cuerpo_sino:
            print(f"{prefijo}Sino:")
            for s in nodo.cuerpo_sino:
                imprimir_ast(s, nivel + 1)

    elif isinstance(nodo, SentenciaLanzar):
        print(f"{prefijo}Lanzar:")
        imprimir_ast(nodo.llamada, nivel + 1)

    elif isinstance(nodo, SentenciaRecuperar):
        print(f"{prefijo}Recuperar (Acción Crítica):")
        imprimir_ast(nodo.accion_critica, nivel + 1)
        print(f"{prefijo}Plan B:")
        imprimir_ast(nodo.plan_b, nivel + 1)

    elif isinstance(nodo, SentenciaRetornar):
        if nodo.expr:
            marca = " ->" if nodo.es_transferencia else ""
            print(f"{prefijo}Retornar{marca}:")
            imprimir_ast(nodo.expr, nivel + 1)
        else:
            print(f"{prefijo}Retornar (vacío)")

    elif isinstance(nodo, SentenciaEscuchar):
        print(f"{prefijo}Escuchar (Canal):")
        imprimir_ast(nodo.canal, nivel + 1)
        print(f"{prefijo}  -> Respuesta:")
        imprimir_ast(nodo.respuesta, nivel + 1)

    elif isinstance(nodo, SentenciaRomper):
        print(f"{prefijo}Romper")

    elif isinstance(nodo, SentenciaSiguiente):
        print(f"{prefijo}Siguiente")

    elif isinstance(nodo, SentenciaMientras):
        print(f"{prefijo}Mientras:")
        imprimir_ast(nodo.condicion, nivel + 1)
        print(f"{prefijo}Cuerpo:")
        for s in nodo.cuerpo:
            imprimir_ast(s, nivel + 1)

    elif isinstance(nodo, SentenciaExpr):
        print(f"{prefijo}Expresión:")
        imprimir_ast(nodo.expr, nivel + 1)

    elif isinstance(nodo, AsignacionVariable):
        print(f"{prefijo}Asignacion: {nodo.nombre} =")
        imprimir_ast(nodo.expresion, nivel + 1)

    elif isinstance(nodo, LogLlamada):
        args = ", ".join(_repr_nodo(a) for a in nodo.argumentos)
        print(f"{prefijo}Log: {args}")

    elif isinstance(nodo, OpBinaria):
        print(f"{prefijo}OpBinaria ({nodo.operador}):")
        imprimir_ast(nodo.izquierdo, nivel + 1)
        imprimir_ast(nodo.derecho, nivel + 1)

    elif isinstance(nodo, OpUnaria):
        print(f"{prefijo}OpUnaria ({nodo.operador}):")
        imprimir_ast(nodo.expr, nivel + 1)

    elif isinstance(nodo, LlamadaFuncion):
        args = ", ".join(_repr_nodo(a) for a in nodo.argumentos)
        print(f"{prefijo}Llamada: {nodo.nombre}({args})")

    elif isinstance(nodo, Identificador):
        print(f"{prefijo}ID: {nodo.nombre}")

    elif isinstance(nodo, LiteralNumero):
        print(f"{prefijo}Número: {nodo.valor}")

    elif isinstance(nodo, ExprTensor):
        print(f"{prefijo}Tensor(filas:")
        imprimir_ast(nodo.filas, nivel + 1)
        print(f"{prefijo}  columnas:")
        imprimir_ast(nodo.columnas, nivel + 1)

    elif isinstance(nodo, ArgumentoTransferido):
        print(f"{prefijo}Transferido:")
        imprimir_ast(nodo.expr, nivel + 1)

    elif isinstance(nodo, ExprAccesoCampo):
        print(f"{prefijo}Acceso Campo:")
        imprimir_ast(nodo.objeto, nivel + 1)
        print(f"{prefijo}  .{nodo.nombre_campo}")

    elif isinstance(nodo, LiteralCadena):
        print(f"{prefijo}Cadena: \"{nodo.valor}\"")


def _repr_nodo(n: Nodo) -> str:
    if isinstance(n, Identificador):
        return n.nombre
    if isinstance(n, LiteralNumero):
        return str(n.valor)
    if isinstance(n, LiteralCadena):
        return f'"{n.valor}"'
    if isinstance(n, LlamadaFuncion):
        args = ", ".join(_repr_nodo(a) for a in n.argumentos)
        return f"{n.nombre}({args})"
    if isinstance(n, OpBinaria):
        return f"({_repr_nodo(n.izquierdo)} {n.operador} {_repr_nodo(n.derecho)})"
    if isinstance(n, OpUnaria):
        return f"({n.operador}{_repr_nodo(n.expr)})"
    if isinstance(n, ExprTensor):
        return f"tensor({_repr_nodo(n.filas)}, {_repr_nodo(n.columnas)})"
    if isinstance(n, ArgumentoTransferido):
        return f"->{_repr_nodo(n.expr)}"
    return "?"


# ============================================================
# CANONICAL ENCODER / DECODER
# ============================================================
def _nodo_a_dict(nodo: Nodo) -> dict:
    d = {"_tipo": type(nodo).__name__}
    for campo, valor in nodo.__dict__.items():
        if campo in ('linea', 'columna'):
            continue
        if valor is None:
            continue
        if isinstance(valor, Nodo):
            d[campo] = _nodo_a_dict(valor)
        elif isinstance(valor, list):
            processed = []
            for v in valor:
                if isinstance(v, Nodo):
                    processed.append(_nodo_a_dict(v))
                elif isinstance(v, Parametro):
                    processed.append({"nombre": v.nombre, "tipo": v.tipo})
                else:
                    processed.append(v)
            d[campo] = processed
        elif isinstance(valor, Parametro):
            d[campo] = {"nombre": valor.nombre, "tipo": valor.tipo, "es_transferencia": valor.es_transferencia}
        else:
            d[campo] = valor
    return d


def _dict_a_nodo(d: dict) -> Nodo:
    tipo = d["_tipo"]
    cls = globals().get(tipo)
    if cls is None:
        cls = getattr(__import__('ast_nodes', fromlist=[tipo]), tipo)
    kwargs = {}
    for campo, valor in d.items():
        if campo == "_tipo":
            continue
        if isinstance(valor, dict) and "_tipo" in valor:
            kwargs[campo] = _dict_a_nodo(valor)
        elif isinstance(valor, list):
            processed = []
            for v in valor:
                if isinstance(v, dict) and "_tipo" in v:
                    processed.append(_dict_a_nodo(v))
                elif isinstance(v, dict) and "nombre" in v and "tipo" in v:
                    processed.append(Parametro(**v))
                else:
                    processed.append(v)
            kwargs[campo] = processed
        elif isinstance(valor, dict) and "nombre" in valor and "tipo" in valor:
            kwargs[campo] = Parametro(**valor)
        else:
            kwargs[campo] = valor
    return cls(**kwargs)


def ast_a_canonico(programa: Programa) -> str:
    data = {
        "synapse": "2.0",
        "ast": _nodo_a_dict(programa),
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def canonico_a_ast(json_str: str) -> Programa:
    data = json.loads(json_str)
    if data.get("synapse") != "2.0":
        raise ValueError("Formato canónico no reconocido")
    return _dict_a_nodo(data["ast"])


# ============================================================
# PRETTY PRINTER MULTILENGUAJE
# ============================================================
def _token_a_palabra(tid: TokenID, dicc_inv: Dict[TokenID, str]) -> str:
    return dicc_inv.get(tid, tid.name.lower())


def ast_a_texto(programa: Programa, idioma: str = 'es') -> str:
    if idioma not in DICCIONARIOS_INVERSO:
        raise ValueError(f"Idioma '{idioma}' no soportado para pretty-print")
    dicc_inv = DICCIONARIOS_INVERSO[idioma]
    lineas: List[str] = [f"#lang: {idioma}"]

    def _render_expr(nodo: Optional[Nodo], dicc_inv: Dict[TokenID, str]) -> str:
        if nodo is None:
            return ""
        if isinstance(nodo, LiteralNumero):
            return str(nodo.valor)
        if isinstance(nodo, LiteralCadena):
            return f'"{nodo.valor}"'
        if isinstance(nodo, Identificador):
            return nodo.nombre
        if isinstance(nodo, OpBinaria):
            izq = _render_expr(nodo.izquierdo, dicc_inv)
            der = _render_expr(nodo.derecho, dicc_inv)
            return f"{izq} {nodo.operador} {der}"
        if isinstance(nodo, OpUnaria):
            return f"{nodo.operador}{_render_expr(nodo.expr, dicc_inv)}"
        if isinstance(nodo, LlamadaFuncion):
            args = ", ".join(_render_expr(a, dicc_inv) for a in nodo.argumentos)
            return f"{nodo.nombre}({args})"
        if isinstance(nodo, ExprTensor):
            filas = _render_expr(nodo.filas, dicc_inv)
            cols = _render_expr(nodo.columnas, dicc_inv)
            return f"tensor({filas}, {cols})"
        if isinstance(nodo, ArgumentoTransferido):
            return f"->{_render_expr(nodo.expr, dicc_inv)}"
        if isinstance(nodo, ExprAccesoCampo):
            return f"{_render_expr(nodo.objeto, dicc_inv)}.{nodo.nombre_campo}"
        return "?"

    def _render_nodo(nodo: Nodo, indent: int = 0) -> List[str]:
        prefijo = "    " * indent
        lines: List[str] = []

        if isinstance(nodo, DefinicionFuncion):
            params = ", ".join(
                f"{'-> ' if p.es_transferencia else ''}{p.nombre}: {p.tipo}"
                for p in nodo.parametros
            )
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.FUNCTION, dicc_inv)} {nodo.nombre}({params}) -> {nodo.tipo_retorno}:")
            for s in nodo.cuerpo:
                lines.extend(_render_nodo(s, indent + 1))

        elif isinstance(nodo, SentenciaSi):
            cond = _render_expr(nodo.condicion, dicc_inv)
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.IF, dicc_inv)} {cond}:")
            for s in nodo.cuerpo:
                lines.extend(_render_nodo(s, indent + 1))
            if nodo.cuerpo_sino:
                lines.append(f"{prefijo}{_token_a_palabra(TokenID.ELSE, dicc_inv)}:")
                for s in nodo.cuerpo_sino:
                    lines.extend(_render_nodo(s, indent + 1))

        elif isinstance(nodo, SentenciaMientras):
            cond = _render_expr(nodo.condicion, dicc_inv)
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.WHILE, dicc_inv)} {cond}:")
            for s in nodo.cuerpo:
                lines.extend(_render_nodo(s, indent + 1))

        elif isinstance(nodo, SentenciaRomper):
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.BREAK, dicc_inv)}")

        elif isinstance(nodo, SentenciaSiguiente):
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.CONTINUE, dicc_inv)}")

        elif isinstance(nodo, SentenciaLanzar):
            llam = _render_expr(nodo.llamada, dicc_inv)
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.SPAWN, dicc_inv)} {llam}")

        elif isinstance(nodo, SentenciaRecuperar):
            acc = _render_expr(nodo.accion_critica, dicc_inv)
            plan = _render_expr(nodo.plan_b, dicc_inv)
            lines.append(f"{prefijo}{acc} {_token_a_palabra(TokenID.RECOVER, dicc_inv)}: {plan}")

        elif isinstance(nodo, SentenciaRetornar):
            if nodo.expr:
                marca = f" {_token_a_palabra(TokenID.ARROW, dicc_inv)} " if nodo.es_transferencia else " "
                lines.append(f"{prefijo}{_token_a_palabra(TokenID.RETURN, dicc_inv)}{marca}{_render_expr(nodo.expr, dicc_inv)}")
            else:
                lines.append(f"{prefijo}{_token_a_palabra(TokenID.RETURN, dicc_inv)}")

        elif isinstance(nodo, SentenciaEscuchar):
            can = _render_expr(nodo.canal, dicc_inv)
            resp = _render_expr(nodo.respuesta, dicc_inv)
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.LISTEN, dicc_inv)} {can} -> {resp}")

        elif isinstance(nodo, AsignacionVariable):
            expr = _render_expr(nodo.expresion, dicc_inv)
            lines.append(f"{prefijo}{nodo.nombre} = {expr}")

        elif isinstance(nodo, SentenciaExpr):
            lines.append(f"{prefijo}{_render_expr(nodo.expr, dicc_inv)}")

        elif isinstance(nodo, LogLlamada):
            args = ", ".join(_render_expr(a, dicc_inv) for a in nodo.argumentos)
            lines.append(f"{prefijo}log({args})")

        elif isinstance(nodo, SentenciaImportar):
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.IMPORT, dicc_inv)} {nodo.ruta}")

        elif isinstance(nodo, DefinicionEstructura):
            lines.append(f"{prefijo}{_token_a_palabra(TokenID.STRUCT, dicc_inv)} {nodo.nombre}:")
            for c in nodo.campos:
                lines.append(f"{prefijo}    {c.nombre}: {c.tipo}")

        elif isinstance(nodo, AsignacionCampo):
            obj = _render_expr(nodo.objeto, dicc_inv)
            expr = _render_expr(nodo.expresion, dicc_inv)
            lines.append(f"{prefijo}{obj}.{nodo.nombre_campo} = {expr}")

        return lines

    for s in programa.sentencias:
        lineas.extend(_render_nodo(s))
    return "\n".join(lineas)


# ============================================================
# IMPORT SYSTEM — Bifurcación estricta Sysroot / Axon
# ============================================================
SYNAPSE_BIN = os.path.dirname(os.path.abspath(__file__))

# Rastro de módulos importados para resolución de dependencias nativas (Auto-Linker)
_imports_usados: set[str] = set()

def _resolver_ruta_sysroot(ruta_import: str) -> str:
    if not ruta_import.startswith('std.'):
        raise ValueError(f"No es una ruta de sysroot: {ruta_import}")
    sub_ruta = ruta_import[len('std.'):]
    sub_ruta_rel = sub_ruta.replace('.', '/') + '.syn'

    sysroot_base = os.environ.get('SYNAPSE_LIB_PATH')
    if sysroot_base:
        sysroot_base = os.path.abspath(sysroot_base)
    else:
        sysroot_base = os.path.normpath(os.path.join(SYNAPSE_BIN, '..', 'std'))

    bases = [sysroot_base]
    if not os.environ.get('SYNAPSE_LIB_PATH'):
        bases.append(os.path.join(SYNAPSE_BIN, 'librerias'))

    for base in bases:
        # For librerias/ fallback, keep the std. prefix as a directory
        if base.endswith('librerias'):
            ruta_archivo = os.path.normpath(
                os.path.join(base, ruta_import.replace('.', '/') + '.syn')
            )
            if os.path.exists(ruta_archivo):
                return ruta_archivo
            ruta_directorio = os.path.normpath(
                os.path.join(base, ruta_import.replace('.', '/'), 'principal.syn')
            )
            if os.path.exists(ruta_directorio):
                return ruta_directorio
        else:
            ruta_archivo = os.path.normpath(os.path.join(base, sub_ruta_rel))
            if os.path.exists(ruta_archivo):
                return ruta_archivo
            ruta_directorio = os.path.normpath(
                os.path.join(base, sub_ruta, 'principal.syn')
            )
            if os.path.exists(ruta_directorio):
                return ruta_directorio

    raise FileNotFoundError(
        f"Módulo estándar '{ruta_import}' no encontrado en sysroot"
    )


def compilar_desde_texto(ruta_archivo: str, archivos_procesados: set[str],
                          dir_base: str = '', mostrar_tokens: bool = False,
                          diag: Optional[DiagnosticManager] = None,
                          dependencias: Optional[Dict[str, str]] = None) -> Tuple[Programa, DiagnosticManager]:
    ruta_abs = os.path.abspath(ruta_archivo)
    if ruta_abs in archivos_procesados:
        return Programa(), diag or DiagnosticManager()
    archivos_procesados.add(ruta_abs)

    try:
        with open(ruta_archivo, 'rb') as f:
            raw = f.read()
    except OSError as e:
        diag_local = diag or DiagnosticManager(ruta_archivo=ruta_archivo)
        diag_local.reportar(ErrorCodes.ERR_FILE_NOT_FOUND,
                           Token(TokenID.EOF, 0, 0), archivo=str(e))
        return Programa(), diag_local

    # Intentar decodificar UTF-8; si falla, es un archivo binario -> error
    try:
        fuente = raw.decode('utf-8')
    except UnicodeDecodeError:
        diag_local = diag or DiagnosticManager(ruta_archivo=ruta_archivo)
        diag_local.reportar(ErrorCodes.ERR_LEX, Token(TokenID.EOF, 1, 0),
                           mensaje="El archivo no es texto UTF-8 valido (posible binario)")
        return Programa(), diag_local
    except LookupError:
        diag_local = diag or DiagnosticManager(ruta_archivo=ruta_archivo)
        diag_local.reportar(ErrorCodes.ERR_LEX, Token(TokenID.EOF, 1, 0),
                           mensaje="Codificacion no soportada")
        return Programa(), diag_local

    lineas = fuente.split('\n')
    diag_local = diag or DiagnosticManager(fuente_lineas=lineas, ruta_archivo=ruta_archivo)

    try:
        lexer = Lexer(fuente)
        tokens = lexer.tokenizar()
    except SyntaxError as e:
        diag_local.reportar(ErrorCodes.ERR_LEX, Token(TokenID.EOF, 1, 0), mensaje=str(e))
        return Programa(), diag_local
    except SynapseError as e:
        diag_local.reportar(ErrorCodes.ERR_LEX, Token(TokenID.EOF, e.linea, e.columna), mensaje=e.mensaje)
        return Programa(), diag_local

    if mostrar_tokens:
        print(f"\n=== TOKENS ({ruta_archivo}) [idioma: {lexer.idioma}] ===")
        for t in tokens:
            print(f"  {t}")

    parser = Parser(tokens, diag_local, is_no_std=lexer.is_no_std)
    ast = parser.parsear()

    nuevas_sentencias: List[Nodo] = []
    for stmt in ast.sentencias:
        if isinstance(stmt, SentenciaImportar):
            _imports_usados.add(stmt.ruta)
            try:
                if stmt.ruta.startswith('std.'):
                    # Check for no_std mode: disallow std imports except core
                    if ast.is_no_std and not stmt.ruta.startswith('std.core'):
                        diag_local.reportar(
                            ErrorCodes.ERR_MODULE_STD_NOT_FOUND,
                            Token(TokenID.IDENTIFIER, stmt.linea, stmt.columna),
                            modulo=stmt.ruta,
                        )
                        return Programa(), diag_local
                    ruta_importada = _resolver_ruta_sysroot(stmt.ruta)
                else:
                    ruta_importada = _resolver_axon(stmt.ruta, dir_base, dependencias)
            except DepNoDeclaradaError:
                diag_local.reportar(
                    ErrorCodes.ERR_DEP_NOT_DECLARED,
                    Token(TokenID.IDENTIFIER, stmt.linea, stmt.columna),
                    modulo=stmt.ruta,
                )
                return Programa(), diag_local
            except FileNotFoundError:
                if stmt.ruta.startswith('std.'):
                    codigo = ErrorCodes.ERR_MODULE_STD_NOT_FOUND
                else:
                    codigo = ErrorCodes.ERR_MODULE_AXON_NOT_FOUND
                diag_local.reportar(
                    codigo,
                    Token(TokenID.IDENTIFIER, stmt.linea, stmt.columna),
                    modulo=stmt.ruta,
                )
                return Programa(), diag_local
            if mostrar_tokens:
                print(f"\n[Importando: {stmt.ruta} -> {ruta_importada}]")
            ast_importado, _ = compilar_desde_texto(ruta_importada, archivos_procesados, dir_base, mostrar_tokens, diag_local, dependencias)
            for s in ast_importado.sentencias:
                nuevas_sentencias.append(s)
        else:
            nuevas_sentencias.append(stmt)

    # Unity Build Deduplication: Eliminar redefiniciones globales
    vistos = set()
    sentencias_dedup = []
    for s in nuevas_sentencias:
        if isinstance(s, (DefinicionEstructura, DefinicionFuncion, DeclaracionExterna, StmtConstante)):
            nombre = getattr(s, 'nombre', None)
            if nombre:
                if nombre in vistos:
                    continue
                vistos.add(nombre)
        sentencias_dedup.append(s)

    ast.sentencias = sentencias_dedup
    return ast, diag_local


def compilar_desde_canonico(ruta_json: str) -> Programa:
    with open(ruta_json, 'r', encoding='utf-8') as f:
        return canonico_a_ast(f.read())


# ============================================================
# MAIN ENTRY POINT
# ============================================================
def ejecutar_compilador(ruta_archivo: str, mostrar_tokens: bool = False,
                        output_lang: Optional[str] = None,
                        dump_ast: bool = False,
                        dependencias: Optional[Dict[str, str]] = None,
                        output_path: Optional[str] = None) -> int:
    diag = DiagnosticManager()

    try:
        if ruta_archivo.endswith('.json'):
            try:
                ast = compilar_desde_canonico(ruta_archivo)
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                diag.reportar(ErrorCodes.ERR_CANONICAL_FORMAT,
                              Token(TokenID.EOF, 0, 0))
                print(diag.resumen(), file=sys.stderr)
                return diag.codigo_salida()
        else:
            archivos_procesados: set[str] = set()
            dir_base = os.path.dirname(os.path.abspath(ruta_archivo))

            if not os.path.exists(ruta_archivo):
                diag.reportar(ErrorCodes.ERR_FILE_NOT_FOUND,
                              Token(TokenID.EOF, 0, 0), archivo=ruta_archivo)
                print(diag.resumen(), file=sys.stderr)
                return diag.codigo_salida()

            ast, diag = compilar_desde_texto(ruta_archivo, archivos_procesados,
                                              dir_base, mostrar_tokens,
                                              dependencias=dependencias)

        if diag.hay_errores():
            print(f"\n[ERROR] Compilación abortada — {diag.resumen()}", file=sys.stderr)
            return diag.codigo_salida()

        analizador = AnalizadorSemantico(ast, diag)
        analizador.analizar()

        if diag.hay_errores():
            print(f"\n[ERROR] Análisis semántico fallido — {diag.resumen()}", file=sys.stderr)
            return diag.codigo_salida()

        if dump_ast:
            imprimir_ast(ast)
            return 0

        generador = GeneradorC(ast)
        codigo_c = generador.generar()

        ruta_base = ruta_archivo.rsplit('.', 1)[0]
        ruta_c = "synapse_unity.c" if ruta_base.endswith("principal") else ruta_base + ".c"
        ruta_json = ruta_base + ".syn.json"
        if output_path:
            ruta_exe = output_path
        else:
            ruta_exe = "synapse_bootstrap.exe" if ruta_base.endswith("principal") else ruta_base + ".exe"

        with open(ruta_c, 'w', encoding='utf-8') as f:
            f.write(codigo_c)
        print(f"[OK] Codigo C generado: {ruta_c}")

        linker_extra = generador.linker_flags
        synapse_rt = os.path.join(SYNAPSE_BIN, "synapse_rt.o")
        if not os.path.exists(synapse_rt):
            synapse_rt = os.path.join(SYNAPSE_BIN, "..", "dist", "lib", "synapse_rt.o")
        # TweetNaCl object (Ed25519)
        tweetnacl_obj = os.path.join(SYNAPSE_BIN, "tweetnacl.o")
        if not os.path.exists(tweetnacl_obj):
            tweetnacl_obj = os.path.join(SYNAPSE_BIN, "..", "dist", "lib", "tweetnacl.o")
            if not os.path.exists(tweetnacl_obj):
                tweetnacl_obj = ""
        linker_net = "-lws2_32" if sys.platform == "win32" else ""
        # Add no_std flags if compiling in bare-metal mode
        if ast.is_no_std:
            no_std_flags = "-ffreestanding -fno-builtin"
            # Bare-metal: no runtime object, no pthreads, no networking
            gcc_cmd = f'gcc -O2 -Wl,--stack,8388608 -fno-ident -Wl,--no-insert-timestamp {no_std_flags} -I. "{ruta_c}" -o "{ruta_exe}" -lm {linker_extra}'.strip()
        else:
            rt_objs = f'"{synapse_rt}"'
            if tweetnacl_obj:
                rt_objs += f' "{tweetnacl_obj}"'
            gcc_cmd = f'gcc -O2 -Wl,--stack,8388608 -fno-ident -Wl,--no-insert-timestamp -Wl,--gc-sections -I. "{ruta_c}" {rt_objs} -o "{ruta_exe}" -lpthread -lm {linker_net} {linker_extra}'.strip()
        print(f"[OK] GCC: {gcc_cmd}")
        rc = os.system(gcc_cmd)
        if rc != 0:
            print(f"[!] GCC fallo con codigo {rc}", file=sys.stderr)
        else:
            print(f"[OK] Ejecutable generado: {ruta_exe}")

        canonico = ast_a_canonico(ast)
        with open(ruta_json, 'w', encoding='utf-8') as f:
            f.write(canonico)
        print(f"[OK] AST canonico guardado: {ruta_json}")

        if output_lang:
            if output_lang not in DICCIONARIOS:
                print(f"[!] Idioma '{output_lang}' no soportado. Usar: {', '.join(DICCIONARIOS)}")
            else:
                texto = ast_a_texto(ast, output_lang)
                ruta_texto = ruta_base + f".{output_lang}.syn"
                with open(ruta_texto, 'w', encoding='utf-8') as f:
                    f.write(texto + "\n")
                print(f"[OK] Fuente en '{output_lang}' generada: {ruta_texto}")

    except FileNotFoundError as e:
        diag.reportar(ErrorCodes.ERR_FILE_NOT_FOUND,
                      Token(TokenID.EOF, 0, 0), archivo=str(e))
        return diag.codigo_salida()

    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "construir":
        construir_args = [a for a in sys.argv[2:] if a != "--tokens" and a != "--dump-ast"]
        tokens_flag = "--tokens" in sys.argv
        dump_flag = "--dump-ast" in sys.argv
        lang_val = None
        for i, a in enumerate(sys.argv):
            if a == "--lang" and i + 1 < len(sys.argv):
                lang_val = sys.argv[i + 1]

        # Native build orchestrator (Fase 8)
        axon_exe = os.path.join(os.path.dirname(__file__), "axon_build.exe")
        if not os.path.exists(axon_exe):
            print(f"ERROR: '{axon_exe}' no encontrado. Compilar con: gcc -o axon_build.exe axon_build.c", file=sys.stderr)
            sys.exit(1)

        out_path = os.path.join(os.environ.get('TEMP', '.'), f"axon_out_{os.getpid()}.txt")
        cmd = axon_exe + ' "' + os.getcwd() + '" > "' + out_path + '"'
        ret = os.system(cmd)

        if ret != 0:
            try:
                with open(out_path, 'r') as f:
                    err_line = f.read().strip()
                os.remove(out_path)
            except (FileNotFoundError, OSError):
                err_line = ""

            if ret == 1:  # MANIFEST_NOT_FOUND
                diag = DiagnosticManager()
                diag.reportar(ErrorCodes.ERR_MANIFEST_NOT_FOUND, Token(TokenID.EOF, 0, 0))
                print(diag.resumen(), file=sys.stderr)
                sys.exit(diag.codigo_salida())
            elif ret == 3:  # MISSING_PUNTO_ENTRADA
                print(f"ERROR: El manifiesto axon.toml debe tener '[proyecto]' con clave 'punto_entrada'", file=sys.stderr)
                sys.exit(1)
            elif ret == 4:  # GIT_FAILURE
                dep_name = err_line.split(':')[-1] if ':' in err_line else "desconocida"
                diag = DiagnosticManager()
                diag.reportar(ErrorCodes.ERR_GIT_FAILURE, Token(TokenID.EOF, 0, 0), modulo=dep_name)
                print(diag.resumen(), file=sys.stderr)
                sys.exit(diag.codigo_salida())
            elif ret == 5:  # LOCK_MISMATCH
                dep_name = err_line.split(':')[-1] if ':' in err_line else "desconocida"
                diag = DiagnosticManager()
                diag.reportar(ErrorCodes.ERR_LOCK_HASH_MISMATCH, Token(TokenID.EOF, 0, 0), modulo=dep_name)
                print(diag.resumen(), file=sys.stderr)
                sys.exit(diag.codigo_salida())
            else:
                print(f"ERROR: Fallo en construccion (codigo {ret})", file=sys.stderr)
                sys.exit(1)

        # Parse output from native binary
        lineas = []
        try:
            with open(out_path, 'r') as f:
                lineas = [l.strip() for l in f if l.strip()]
            os.remove(out_path)
        except (FileNotFoundError, OSError):
            pass

        punto_entrada = ""
        dependencias: Dict[str, Any] = {}
        for ln in lineas:
            if ln.startswith("punto_entrada="):
                punto_entrada = ln.split("=", 1)[1]
            else:
                dependencias[ln] = True

        ruta_entrada = os.path.normpath(os.path.join(os.getcwd(), punto_entrada))
        if not os.path.exists(ruta_entrada):
            diag = DiagnosticManager()
            diag.reportar(ErrorCodes.ERR_FILE_NOT_FOUND,
                          Token(TokenID.EOF, 0, 0), archivo=ruta_entrada)
            print(diag.resumen(), file=sys.stderr)
            sys.exit(diag.codigo_salida())

        codigo = ejecutar_compilador(ruta_entrada, mostrar_tokens=tokens_flag,
                                     output_lang=lang_val, dump_ast=dump_flag,
                                     dependencias=dependencias)
        sys.exit(codigo)

    parser = argparse.ArgumentParser(description="Synapse Compiler v2.0 - Poliglota")
    parser.add_argument("archivo", nargs="?", default="programa.syn",
                        help="Archivo fuente .syn (o .syn.json para canonico)")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Ruta del ejecutable de salida")
    parser.add_argument("--tokens", action="store_true", help="Mostrar tokens")
    parser.add_argument("--lang", type=str, default=None,
                        help="Idioma de salida (es, en). Si no da, solo genera C + JSON canonico.")
    parser.add_argument("--lsp", action="store_true", help="Iniciar servidor LSP (daemon sobre stdin/stdout)")
    parser.add_argument("--dump-ast", action="store_true", help="Volcar AST y salir sin generar código")
    args = parser.parse_args()

    if args.lsp:
        from synapse_lsp.server import iniciar
        iniciar()
    else:
        codigo = ejecutar_compilador(args.archivo, mostrar_tokens=args.tokens,
                                     output_lang=args.lang, dump_ast=args.dump_ast,
                                     output_path=args.output)
        sys.exit(codigo)
