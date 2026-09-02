# =============================================================================
# compilador/wat_generator.py — WebAssembly WAT text generator (M12.1.2)
#
# Genera WAT de texto (.wat) a partir del AST canónico de Synapse.
# Sin dependencias externas — emite texto plano usando solo stdlib.
#
# Soporta: i32, i64, f64, memoria, imports, exports, globals.
#
# Referencias: Manual 1 §5 (Generador → WAT), §6 (Backend WASM)
#              Manual 4 §6.6 (Arenas de componente WASM)
#              Manual 8 §4.2 (--target wasm)
#
# cumple Manual 1 5: generador WAT
# cumple Manual 4 6.6: arenas de componente WASM
# cumple Manual 8 4.2: backend WASM
# =============================================================================
from typing import List, Optional
from compilador.ast_nodes import (
    Nodo, Programa, DefinicionFuncion, SentenciaSi,
    SentenciaRetornar, SentenciaMientras, SentenciaPara,
    OpBinaria, OpUnaria, LlamadaFuncion, Identificador,
    LiteralNumero, LiteralDecimal, LiteralCadena, LiteralBooleano,
    SentenciaExpr, DeclaracionVariable, AsignacionVariable,
    SentenciaRomper, SentenciaSiguiente,
)


class WATGenerator:
    """Genera WAT de texto desde el AST de Synapse.

    Extensiones FASE 25:
    - Tipos: i32, i64, f64
    - Memoria: (memory N), load/store
    - Imports/exports para JS interop
    - Globals mutables
    - Strings en memoria lineal
    """

    # Mapeo de tipos Syquex → WASM
    TIPO_WASM = {
        'entero': 'i32', 'int': 'i32',
        'entero64': 'i64', 'i64': 'i64',
        'decimal': 'f64', 'float': 'f64', 'f64': 'f64',
        'booleano': 'i32', 'bool': 'i32',
        'texto': 'i32', 'string': 'i32',  # puntero
        'nulo': 'i32', 'void': None,
    }

    def __init__(self, ast: Programa, diag):
        self.ast = ast
        self.diag = diag
        self._lines: List[str] = []
        self._indent = 0
        self._var_map: dict = {}  # nombre → tipo wasm
        self._globals: dict = {}  # nombre → (tipo, valor_inicial)
        self._imports: List[tuple] = []  # (modulo, nombre, params, results)
        self._exports: List[str] = []  # nombres de funciones a exportar
        self._memory_pages = 1
        self._data_segments: List[tuple] = []  # (offset, string)
        self._data_offset = 0  # siguiente offset libre para data

    def _emit(self, line: str) -> None:
        if self._indent:
            self._lines.append(("  " * self._indent) + line)
        else:
            self._lines.append(line)

    def _push_indent(self) -> None:
        self._indent += 1

    def _pop_indent(self) -> None:
        if self._indent > 0:
            self._indent -= 1

    def _tipo_a_wasm(self, tipo: Optional[str]) -> Optional[str]:
        """Convierte tipo Syquex a tipo WASM."""
        if tipo is None:
            return None
        return self.TIPO_WASM.get(tipo, 'i32')

    def _agregar_data(self, texto: str) -> int:
        """Agrega un string a los data segments y retorna su offset."""
        offset = self._data_offset
        self._data_segments.append((offset, texto))
        self._data_offset += len(texto) + 1  # +1 para null terminator
        return offset

    def agregar_import(self, modulo: str, nombre: str,
                       params: List[str] = None, results: List[str] = None) -> None:
        """Registra un import para incluir en el módulo."""
        self._imports.append((modulo, nombre, params or [], results or []))

    def agregar_global(self, nombre: str, tipo: str = 'i32',
                       mutable: bool = True, valor_inicial: str = '0') -> None:
        """Registra un global mutable."""
        self._globals[nombre] = (tipo, mutable, valor_inicial)

    def agregar_export(self, nombre: str) -> None:
        """Registra una función para exportar."""
        self._exports.append(nombre)

    def set_memory(self, pages: int) -> None:
        """Establece el número de páginas de memoria."""
        self._memory_pages = pages
    def generar(self) -> str:
        self._lines = []
        self._indent = 0
        self._var_map = {}

        self._emit('(module')
        self._push_indent()

        # Imports
        for modulo, nombre, params, results in self._imports:
            params_str = ' '.join(f'(param {p})' for p in params)
            results_str = ' '.join(f'(result {r})' for r in results)
            sig = f'{params_str} {results_str}'.strip()
            self._emit(f'(import "{modulo}" "{nombre}" (func ${nombre} {sig}))')

        # Memory
        if self._memory_pages > 0:
            self._emit(f'(memory {self._memory_pages})')
            self._emit('(export "memory" (memory 0))')

        # Globals
        for nombre, (tipo, mutable, valor) in self._globals.items():
            mut_str = '(mut ' if mutable else ''
            mut_end = ')' if mutable else ''
            self._emit(f'(global ${nombre} {mut_str}{tipo}{mut_end} ({tipo}.const {valor}))')

        # Funciones (primero generamos para poblar data_segments)
        for sentencia in self.ast.sentencias:
            if isinstance(sentencia, DefinicionFuncion):
                self._generar_funcion(sentencia)

        # Exports (a nivel módulo, después de funciones)
        for nombre in self._exports:
            self._emit(f'(export "{nombre}" (func ${nombre}))')

        # Data segments (después de funciones para que estén poblados)
        for offset, texto in self._data_segments:
            escaped = texto.replace('\\', '\\\\').replace('"', '\\"')
            self._emit(f'(data (i32.const {offset}) "{escaped}")')

        self._pop_indent()
        self._emit(')')

        return '\n'.join(self._lines) + '\n'

    def _generar_funcion(self, fn: DefinicionFuncion) -> None:
        self._var_map = {}

        # Params con tipos
        params_parts = []
        for p in fn.parametros:
            tipo_wasm = self._tipo_a_wasm(getattr(p, 'tipo', None) or 'entero')
            params_parts.append(f'(param ${p.nombre} {tipo_wasm})')
            self._var_map[p.nombre] = tipo_wasm or 'i32'
        params_str = ' '.join(params_parts)

        # Result type
        tipo_ret = self._tipo_a_wasm(fn.tipo_retorno)
        result_str = f'(result {tipo_ret})' if tipo_ret else ''

        self._emit(f'(func ${fn.nombre} {params_str} {result_str}'.strip())
        self._push_indent()

        self._emit(';; entry block')
        for stmt in fn.cuerpo:
            self._generar_sentencia(stmt)

        self._pop_indent()
        self._emit(')')

    def _generar_sentencia(self, stmt: Nodo) -> None:
        if isinstance(stmt, SentenciaRetornar):
            if stmt.expr:
                self._generar_expr(stmt.expr)
                self._emit('return')
            else:
                self._emit('i32.const 0')
                self._emit('return')
        elif isinstance(stmt, SentenciaSi):
            self._generar_si(stmt)
        elif isinstance(stmt, SentenciaMientras):
            self._generar_mientras(stmt)
        elif isinstance(stmt, DeclaracionVariable):
            tipo_wasm = self._tipo_a_wasm(stmt.tipo) or 'i32'
            self._var_map[stmt.nombre] = tipo_wasm
            if stmt.expr:
                self._generar_expr(stmt.expr)
                self._emit(f'local.set ${stmt.nombre}')
        elif isinstance(stmt, AsignacionVariable):
            if stmt.expr:
                self._generar_expr(stmt.expr)
                self._emit(f'local.set ${stmt.nombre}')
        elif isinstance(stmt, SentenciaExpr):
            self._generar_expr(stmt.expr)
        else:
            pass  # sentencias no soportadas aún

    def _generar_si(self, stmt: SentenciaSi) -> None:
        self._generar_expr(stmt.condicion)
        self._emit('if')
        self._push_indent()
        for s in stmt.cuerpo:
            self._generar_sentencia(s)
        self._pop_indent()
        if stmt.cuerpo_sino:
            self._emit('else')
            self._push_indent()
            for s in stmt.cuerpo_sino:
                self._generar_sentencia(s)
            self._pop_indent()
        self._emit('end')

    def _generar_mientras(self, stmt: SentenciaMientras) -> None:
        self._emit('loop $loop')
        self._push_indent()
        self._generar_expr(stmt.condicion)
        self._emit('if')
        self._push_indent()
        for s in stmt.cuerpo:
            self._generar_sentencia(s)
        self._pop_indent()
        self._emit('else')
        self._emit('end')
        self._emit('br $loop')
        self._pop_indent()
        self._emit('end')

    def _generar_expr(self, expr: Nodo) -> None:
        if isinstance(expr, LiteralNumero):
            self._emit(f'i32.const {expr.valor}')
        elif isinstance(expr, LiteralBooleano):
            self._emit('i32.const ' + ('1' if expr.valor else '0'))
        elif isinstance(expr, LiteralDecimal):
            self._emit(f'f64.const {expr.valor}')
        elif isinstance(expr, LiteralCadena):
            # Almacenar string en memoria y retornar puntero
            offset = self._agregar_data(expr.valor)
            self._emit(f'i32.const {offset}')
        elif isinstance(expr, Identificador):
            tipo = self._var_map.get(expr.nombre, 'i32')
            self._emit(f'local.get ${expr.nombre}')
        elif isinstance(expr, OpBinaria):
            self._generar_expr(expr.izquierdo)
            self._generar_expr(expr.derecho)
            op = expr.operador
            # Detectar tipo de los operandos
            tipo_izq = self._detectar_tipo_expr(expr.izquierdo)
            tipo_der = self._detectar_tipo_expr(expr.derecho)
            tipo = tipo_izq or tipo_der or 'i32'

            op_map = {
                'i32': {
                    '+': 'i32.add', '-': 'i32.sub', '*': 'i32.mul',
                    '/': 'i32.div_s', '%': 'i32.rem_s',
                    '==': 'i32.eq', '!=': 'i32.ne',
                    '<': 'i32.lt_s', '>': 'i32.gt_s',
                    '<=': 'i32.le_s', '>=': 'i32.ge_s',
                },
                'i64': {
                    '+': 'i64.add', '-': 'i64.sub', '*': 'i64.mul',
                    '/': 'i64.div_s', '%': 'i64.rem_s',
                    '==': 'i64.eq', '!=': 'i64.ne',
                    '<': 'i64.lt_s', '>': 'i64.gt_s',
                    '<=': 'i64.le_s', '>=': 'i64.ge_s',
                },
                'f64': {
                    '+': 'f64.add', '-': 'f64.sub', '*': 'f64.mul',
                    '/': 'f64.div',
                    '==': 'f64.eq', '!=': 'f64.ne',
                    '<': 'f64.lt', '>': 'f64.gt',
                    '<=': 'f64.le', '>=': 'f64.ge',
                },
            }

            if tipo in op_map and op in op_map[tipo]:
                self._emit(op_map[tipo][op])
            elif op in ('==', '!=', '<', '>', '<=', '>='):
                # Comparaciones i32 por defecto
                icmp_map = {
                    '==': 'i32.eq', '!=': 'i32.ne',
                    '<': 'i32.lt_s', '>': 'i32.gt_s',
                    '<=': 'i32.le_s', '>=': 'i32.ge_s',
                }
                self._emit(icmp_map.get(op, 'i32.eq'))
            else:
                self._emit('i32.add')
        elif isinstance(expr, OpUnaria):
            self._generar_expr(expr.expr)
            if expr.operador == '-':
                self._emit('i32.const 0')
                self._emit('i32.sub')
            elif expr.operador == '!':
                self._emit('i32.eqz')
        elif isinstance(expr, LlamadaFuncion):
            for arg in expr.argumentos:
                self._generar_expr(arg)
            self._emit(f'call ${expr.nombre}')
        else:
            self._emit('i32.const 0')

    def _detectar_tipo_expr(self, expr: Nodo) -> Optional[str]:
        """Detecta el tipo WASM de una expresión (estático, best-effort)."""
        if isinstance(expr, LiteralDecimal):
            return 'f64'
        elif isinstance(expr, LiteralNumero):
            return 'i32'
        elif isinstance(expr, LiteralBooleano):
            return 'i32'
        elif isinstance(expr, Identificador):
            return self._var_map.get(expr.nombre, 'i32')
        elif isinstance(expr, LlamadaFuncion):
            # Buscar la función en el AST para obtener su tipo de retorno
            for sent in self.ast.sentencias:
                if isinstance(sent, DefinicionFuncion) and sent.nombre == expr.nombre:
                    return self._tipo_a_wasm(sent.tipo_retorno) or 'i32'
        return 'i32'
