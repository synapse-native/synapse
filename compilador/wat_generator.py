# =============================================================================
# compilador/wat_generator.py — WebAssembly WAT text generator (M12.1.2)
#
# Genera WAT de texto (.wat) a partir del AST canónico de Synapse.
# Sin dependencias externas — emite texto plano usando solo stdlib.
#
# Referencias: Manual 1 §5 (Generador → WAT), §6 (Backend WASM)
#              Manual 8 §4.2 (--target wasm)
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
    """Genera WAT de texto desde el AST de Synapse."""

    def __init__(self, ast: Programa, diag):
        self.ast = ast
        self.diag = diag
        self._lines: List[str] = []
        self._indent = 0
        self._var_map: dict = {}

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

    def generar(self) -> str:
        self._lines = []
        self._indent = 0
        self._var_map = {}

        self._emit('(module')
        self._push_indent()

        for sentencia in self.ast.sentencias:
            if isinstance(sentencia, DefinicionFuncion):
                self._generar_funcion(sentencia)

        self._pop_indent()
        self._emit(')')

        return '\n'.join(self._lines) + '\n'

    def _generar_funcion(self, fn: DefinicionFuncion) -> None:
        params = ' '.join('(param i32)' for _ in fn.parametros)
        results = '(result i32)' if fn.tipo_retorno == 'entero' or not fn.tipo_retorno else ''
        self._emit(f'(func ${fn.nombre} {params} {results}'.strip())
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
        elif isinstance(stmt, SentenciaExpr):
            self._generar_expr(stmt.expr)

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
        elif isinstance(expr, Identificador):
            self._emit(f'local.get ${expr.nombre}')
        elif isinstance(expr, OpBinaria):
            self._generar_expr(expr.izquierdo)
            self._generar_expr(expr.derecho)
            op = expr.operador
            op_map = {
                '+': 'i32.add', '-': 'i32.sub', '*': 'i32.mul',
                '/': 'i32.div_s', '%': 'i32.rem_s',
            }
            if op in op_map:
                self._emit(op_map[op])
            elif op in ('==', '!=', '<', '>', '<=', '>='):
                icmp_map = {
                    '==': 'i32.eq', '!=': 'i32.ne',
                    '<': 'i32.lt_s', '>': 'i32.gt_s',
                    '<=': 'i32.le_s', '>=': 'i32.ge_s',
                }
                self._emit(icmp_map[op])
                self._emit('i32.const 0')
                self._emit('i32.ne')
            else:
                self._emit('i32.add')
        elif isinstance(expr, OpUnaria):
            self._generar_expr(expr.expr)
            if expr.operador == '-':
                self._emit('i32.const 0')
                self._emit('i32.sub')
            elif expr.operador == '!':
                self._emit('i32.eq')
        elif isinstance(expr, LlamadaFuncion):
            for arg in expr.argumentos:
                self._generar_expr(arg)
            self._emit(f'call ${expr.nombre}')
        elif isinstance(expr, LiteralDecimal):
            self._emit(f'i32.const {int(expr.valor)}')
        elif isinstance(expr, LiteralCadena):
            self._emit('i32.const 0')
        else:
            self._emit('i32.const 0')
