
"""
Manual 2
"""
"""
FASE 25 - Test del WATGenerator extendido (i64/f64/memory/imports/exports).
"""
import os
import subprocess
import sys
import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

try:
    from compilador.wat_generator import WATGenerator
    from compilador.ast_nodes import (
        Programa, DefinicionFuncion, Parametro,
        LiteralNumero, LiteralDecimal, LiteralCadena, LiteralBooleano,
        Identificador, OpBinaria, OpUnaria, LlamadaFuncion,
        SentenciaRetornar, SentenciaSi, SentenciaExpr,
        SentenciaMientras, DeclaracionVariable, AsignacionVariable,
    )
    HAS_WAT_GEN = True
    _IMPORT_ERROR = None
except ImportError as e:
    HAS_WAT_GEN = False
    _IMPORT_ERROR = str(e)


def _make_param(nombre, tipo='entero'):
    return Parametro(nombre=nombre, tipo=tipo)


def _make_fn(nombre, params, body, tipo_ret='entero'):
    return DefinicionFuncion(
        nombre=nombre, parametros=params, cuerpo=body,
        tipo_retorno=tipo_ret
    )


def _make_program(fns):
    return Programa(sentencias=fns)


class _DummyDiag:
    def reportar(self, *a, **kw):
        pass


def _gen_wat(fns):
    ast = _make_program(fns)
    gen = WATGenerator(ast, _DummyDiag())
    return gen.generar()


def _find_wat2wasm():
    import shutil
    for c in ("wat2wasm", "wat2wasm.exe", "wat2wasm.CMD"):
        try:
            r = subprocess.run([c, "--version"], capture_output=True, timeout=5)
            if r.returncode == 0:
                return c
        except FileNotFoundError:
            continue
    # Fallback: check common locations
    for p in ["C:/emsdk/node/24.19.0_64bit/wat2wasm.exe",
              "C:/emsdk/node/24.19.0_64bit/wat2wasm.CMD"]:
        if os.path.exists(p):
            return p
    found = shutil.which('wat2wasm')
    if found:
        return found
    return None


@pytest.mark.skipif(not HAS_WAT_GEN, reason=f"WATGenerator import failed: {_IMPORT_ERROR}")
class TestWATGeneratorExtended:

    def test_basic_i32(self):
        wat = _gen_wat([
            _make_fn('main', [], [
                SentenciaRetornar(expr=LiteralNumero(valor=42))
            ], 'entero'),
        ])
        assert '(func $main' in wat
        assert 'i32.const 42' in wat
        assert 'return' in wat
        assert '(result i32)' in wat

    def test_i64_function(self):
        wat = _gen_wat([
            _make_fn('big', [], [
                SentenciaRetornar(expr=LiteralNumero(valor=1000000))
            ], 'entero64'),
        ])
        assert '(result i64)' in wat

    def test_f64_function(self):
        wat = _gen_wat([
            _make_fn('pi', [], [
                SentenciaRetornar(expr=LiteralDecimal(valor=3.14))
            ], 'decimal'),
        ])
        assert '(result f64)' in wat
        assert 'f64.const 3.14' in wat

    def test_binary_i32_ops(self):
        wat = _gen_wat([
            _make_fn('add', [_make_param('a'), _make_param('b')], [
                SentenciaRetornar(expr=OpBinaria(
                    operador='+',
                    izquierdo=Identificador(nombre='a'),
                    derecho=Identificador(nombre='b')
                ))
            ], 'entero'),
        ])
        assert 'i32.add' in wat
        assert 'local.get $a' in wat
        assert 'local.get $b' in wat

    def test_binary_f64_ops(self):
        wat = _gen_wat([
            _make_fn('mul', [_make_param('x', 'decimal')], [
                SentenciaRetornar(expr=OpBinaria(
                    operador='*',
                    izquierdo=Identificador(nombre='x'),
                    derecho=LiteralDecimal(valor=2.0)
                ))
            ], 'decimal'),
        ])
        assert 'f64.mul' in wat
        assert 'f64.const 2.0' in wat

    def test_comparison_ops(self):
        wat = _gen_wat([
            _make_fn('gt', [_make_param('a'), _make_param('b')], [
                SentenciaRetornar(expr=OpBinaria(
                    operador='>',
                    izquierdo=Identificador(nombre='a'),
                    derecho=Identificador(nombre='b')
                ))
            ], 'entero'),
        ])
        assert 'i32.gt_s' in wat

    def test_string_literal(self):
        wat = _gen_wat([
            _make_fn('greet', [], [
                SentenciaRetornar(expr=LiteralCadena(valor='hello'))
            ], 'entero'),
        ])
        assert 'data' in wat
        assert 'hello' in wat
        assert 'i32.const 0' in wat

    def test_imports(self):
        ast = _make_program([])
        gen = WATGenerator(ast, _DummyDiag())
        gen.agregar_import('env', 'console_log', ['i32'], [])
        gen.agregar_import('env', 'read_i32', [], ['i32'])
        wat = gen.generar()
        assert '(import "env" "console_log"' in wat
        assert '(import "env" "read_i32"' in wat

    def test_exports(self):
        ast = _make_program([
            _make_fn('main', [], [
                SentenciaRetornar(expr=LiteralNumero(valor=0))
            ], 'entero'),
        ])
        gen = WATGenerator(ast, _DummyDiag())
        gen.agregar_export('main')
        wat = gen.generar()
        assert '(export "main"' in wat

    def test_globals(self):
        ast = _make_program([])
        gen = WATGenerator(ast, _DummyDiag())
        gen.agregar_global('counter', 'i32', True, '0')
        gen.agregar_global('pi', 'f64', False, '3.14')
        wat = gen.generar()
        assert '(global $counter (mut i32) (i32.const 0))' in wat
        assert '(global $pi f64 (f64.const 3.14))' in wat

    def test_memory(self):
        ast = _make_program([])
        gen = WATGenerator(ast, _DummyDiag())
        gen.set_memory(2)
        wat = gen.generar()
        assert '(memory 2)' in wat
        assert '(export "memory" (memory 0))' in wat

    def test_while_loop(self):
        wat = _gen_wat([
            _make_fn('count', [_make_param('n')], [
                SentenciaMientras(
                    condicion=OpBinaria(
                        operador='>',
                        izquierdo=Identificador(nombre='n'),
                        derecho=LiteralNumero(valor=0)
                    ),
                    cuerpo=[SentenciaRetornar(expr=LiteralNumero(valor=1))]
                )
            ], 'entero'),
        ])
        assert 'loop $loop' in wat
        assert 'if' in wat
        assert 'br $loop' in wat

    def test_if_else(self):
        wat = _gen_wat([
            _make_fn('abs', [_make_param('x')], [
                SentenciaSi(
                    condicion=OpBinaria(
                        operador='<',
                        izquierdo=Identificador(nombre='x'),
                        derecho=LiteralNumero(valor=0)
                    ),
                    cuerpo=[SentenciaRetornar(expr=OpUnaria(
                        operador='-',
                        expr=Identificador(nombre='x')
                    ))],
                    cuerpo_sino=[SentenciaRetornar(expr=Identificador(nombre='x'))]
                )
            ], 'entero'),
        ])
        assert 'if' in wat
        assert 'else' in wat
        assert 'end' in wat

    def test_function_call(self):
        wat = _gen_wat([
            _make_fn('double', [_make_param('x')], [
                SentenciaRetornar(expr=OpBinaria(
                    operador='*',
                    izquierdo=Identificador(nombre='x'),
                    derecho=LiteralNumero(valor=2)
                ))
            ], 'entero'),
            _make_fn('main', [], [
                SentenciaRetornar(expr=LlamadaFuncion(
                    nombre='double',
                    argumentos=[LiteralNumero(valor=21)]
                ))
            ], 'entero'),
        ])
        assert 'call $double' in wat
        assert 'i32.const 21' in wat


@pytest.mark.skipif(not HAS_WAT_GEN, reason=f"WATGenerator import failed")
class TestWATToWASM:

    def test_wat_compiles_to_wasm(self, tmp_path):
        wat2wasm = _find_wat2wasm()
        if not wat2wasm:
            pytest.skip("wat2wasm no disponible")

        ast = _make_program([
            _make_fn('main', [], [
                SentenciaRetornar(expr=LiteralNumero(valor=42))
            ], 'entero'),
        ])
        gen = WATGenerator(ast, _DummyDiag())
        wat = gen.generar()

        wat_path = str(tmp_path / "test.wat")
        wasm_path = str(tmp_path / "test.wasm")
        with open(wat_path, 'w') as f:
            f.write(wat)

        r = subprocess.run([wat2wasm, wat_path, '-o', wasm_path],
                           capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, f"wat2wasm fallo: {r.stderr}"
        assert os.path.exists(wasm_path)

        with open(wasm_path, 'rb') as f:
            magic = f.read(4)
        assert magic == b'\x00asm', "No es WASM valido"

    def test_pipeline_end_to_end(self, tmp_path):
        wat2wasm = _find_wat2wasm()
        if not wat2wasm:
            pytest.skip("wat2wasm no disponible")

        ast = _make_program([
            _make_fn('add', [_make_param('a'), _make_param('b')], [
                SentenciaRetornar(expr=OpBinaria(
                    operador='+',
                    izquierdo=Identificador(nombre='a'),
                    derecho=Identificador(nombre='b')
                ))
            ], 'entero'),
        ])
        gen = WATGenerator(ast, _DummyDiag())
        gen.agregar_export('add')
        wat = gen.generar()

        assert '(export "add"' in wat

        wat_path = str(tmp_path / "add.wat")
        wasm_path = str(tmp_path / "add.wasm")
        with open(wat_path, 'w') as f:
            f.write(wat)

        r = subprocess.run([wat2wasm, wat_path, '-o', wasm_path],
                           capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, f"wat2wasm fallo: {r.stderr}"

        size = os.path.getsize(wasm_path)
        assert size > 50, f"WASM demasiado pequeno: {size} bytes"
