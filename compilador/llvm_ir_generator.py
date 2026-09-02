# =============================================================================
# compilador/llvm_ir_generator.py — LLVM IR text generator (M12.1.1)
#
# Genera LLVM IR de texto (.ll) a partir del AST canónico de Synapse.
# Sin dependencias externas — emite texto plano usando solo stdlib.
#
# Referencias: Manual 1 §5 (Generador → LLVM IR), §6 (Backend LLVM)
#              Manual 8 §4.2 (--target llvm)
#
# cumple Manual 1 §5: generador LLVM IR
# cumple Manual 8 §4.2: backend LLVM
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


class LLVMIRGenerator:
    """Genera LLVM IR de texto desde el AST de Synapse."""

    _ICMP_TABLE = {
        '==': 'eq', '!=': 'ne', '<': 'slt', '>': 'sgt',
        '<=': 'sle', '>=': 'sge',
    }

    def __init__(self, ast: Programa, diag):
        self.ast = ast
        self.diag = diag
        self._lines: List[str] = []
        self._var_counter = 0
        self._func_counter = 0
        self._vars: dict = {}

    def _emit(self, line: str) -> None:
        self._lines.append(("    " * self._indent) + line if self._indent else line)

    def _label(self, name: str) -> None:
        self._indent = 0
        self._lines.append(f"{name}:")
        self._indent = 1

    def _new_var(self) -> str:
        self._var_counter += 1
        return f"%v{self._var_counter}"

    def _new_label(self, name: str) -> str:
        self._func_counter += 1
        return f"{name}{self._func_counter}"

    def generar(self) -> str:
        self._indent = 0
        self._lines = []
        self._var_counter = 0
        self._func_counter = 0
        self._vars = {}

        self._emit(f'; ModuleID = \'synapse\'')
        self._emit('source_filename = "synapse"')
        self._emit('target datalayout = "e-m:w-i666-32-n32"')
        self._emit('target triple = "unknown-pc-win32"')
        self._emit('')

        for sentencia in self.ast.sentencias:
            if isinstance(sentencia, DefinicionFuncion):
                self._generar_funcion(sentencia)

        self._emit('')
        return '\n'.join(self._lines)

    def _generar_funcion(self, fn: DefinicionFuncion) -> None:
        params_str = ', '.join(
            f'i32 %p{i}' for i in range(len(fn.parametros))
        ) if fn.parametros else ''
        self._emit(f'define i32 @{fn.nombre}({params_str}) {{')
        self._indent = 1
        self._emit('entry:')
        self._indent = 2

        for i, param in enumerate(fn.parametros):
            self._vars[param.nombre] = f'%p{i}'

        for stmt in fn.cuerpo:
            self._generar_sentencia(stmt)

        self._emit('}')
        self._emit('')

    def _generar_sentencia(self, stmt: Nodo) -> None:
        if isinstance(stmt, SentenciaRetornar):
            if stmt.expr:
                val = self._generar_expr(stmt.expr)
                self._emit(f'ret i32 {val}')
            else:
                self._emit('ret i32 0')
        elif isinstance(stmt, SentenciaSi):
            self._generar_si(stmt)
        elif isinstance(stmt, SentenciaMientras):
            self._generar_mientras(stmt)
        elif isinstance(stmt, OpBinaria):
            self._generar_expr(stmt)
        elif isinstance(stmt, SentenciaExpr):
            self._generar_expr(stmt.expr)

    def _generar_si(self, stmt: SentenciaSi) -> None:
        cond_val = self._generar_expr(stmt.condicion)
        icmp_var = self._new_var()
        self._emit(f'{icmp_var} = icmp ne i32 {cond_val}, 0')

        then_label = self._new_label('then')
        else_label = self._new_label('else')
        end_label = self._new_label('endif')

        self._emit(f'br i1 {icmp_var}, label %{then_label}, label %{else_label}')

        self._label(then_label)
        for s in stmt.cuerpo:
            self._generar_sentencia(s)
        self._emit(f'br label %{end_label}')

        self._label(else_label)
        if stmt.cuerpo_sino:
            for s in stmt.cuerpo_sino:
                self._generar_sentencia(s)
        self._emit(f'br label %{end_label}')

        self._label(end_label)

    def _generar_mientras(self, stmt: SentenciaMientras) -> None:
        cond_label = self._new_label('loop_cond')
        body_label = self._new_label('loop_body')
        end_label = self._new_label('loop_end')

        self._emit(f'br label %{cond_label}')
        self._label(cond_label)
        cond_val = self._generar_expr(stmt.condicion)
        icmp_var = self._new_var()
        self._emit(f'{icmp_var} = icmp ne i32 {cond_val}, 0')
        self._emit(f'br i1 {icmp_var}, label %{body_label}, label %{end_label}')

        self._label(body_label)
        for s in stmt.cuerpo:
            self._generar_sentencia(s)
        self._emit(f'br label %{cond_label}')

        self._label(end_label)

    def _generar_expr(self, expr: Nodo) -> str:
        if isinstance(expr, LiteralNumero):
            return str(expr.valor)
        elif isinstance(expr, LiteralBooleano):
            return '1' if expr.valor else '0'
        elif isinstance(expr, Identificador):
            return self._vars.get(expr.nombre, f'%{expr.nombre}')
        elif isinstance(expr, OpBinaria):
            lhs = self._generar_expr(expr.izquierdo)
            rhs = self._generar_expr(expr.derecho)
            result = self._new_var()

            op = expr.operador
            if op == '+':
                self._emit(f'{result} = add i32 {lhs}, {rhs}')
            elif op == '-':
                self._emit(f'{result} = sub i32 {lhs}, {rhs}')
            elif op == '*':
                self._emit(f'{result} = mul i32 {lhs}, {rhs}')
            elif op == '/':
                self._emit(f'{result} = sdiv i32 {lhs}, {rhs}')
            elif op == '%':
                self._emit(f'{result} = srem i32 {lhs}, {rhs}')
            elif op in self._ICMP_TABLE:
                icmp = self._ICMP_TABLE[op]
                cmp_var = self._new_var()
                self._emit(f'{cmp_var} = icmp {icmp} i32 {lhs}, {rhs}')
                self._emit(f'{result} = zext i1 {cmp_var} to i32')
            else:
                self._emit(f'{result} = add i32 {lhs}, {rhs}')
            return result
        elif isinstance(expr, OpUnaria):
            val = self._generar_expr(expr.expr)
            if expr.operador == '-':
                result = self._new_var()
                self._emit(f'{result} = sub i32 0, {val}')
                return result
            elif expr.operador == '!':
                result = self._new_var()
                cmp_var = self._new_var()
                self._emit(f'{cmp_var} = icmp eq i32 {val}, 0')
                self._emit(f'{result} = zext i1 {cmp_var} to i32')
                return result
            return val
        elif isinstance(expr, LlamadaFuncion):
            args_str = ', '.join(
                f'i32 {self._generar_expr(a)}' for a in expr.argumentos
            )
            result = self._new_var()
            self._emit(f'{result} = call i32 @{expr.nombre}({args_str})')
            return result
        elif isinstance(expr, LiteralDecimal):
            return str(int(expr.valor))
        elif isinstance(expr, LiteralCadena):
            return '0'
        else:
            return '0'

    @property
    def _indent(self) -> int:
        return getattr(self, '_indent_level', 0)

    @_indent.setter
    def _indent(self, value: int) -> None:
        self._indent_level = value
