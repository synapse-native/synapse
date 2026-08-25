"""
tests/test_frontend_embebido_d_f1.py
F1.2 / D-F1 (Micro-entregable): valida que el front-end embebido _P_*
(S2/S3, espejo de emitir_parsear) reconoce declaracion_tipo (alias, ADT con
genericos y con parentesis), 'nulo' -> LiteralNulo y 'tensor(filas, columnas)'
-> ExprTensor, generando los nodos correctos en el arbol.

El harness compila un unico .c con:
  1) las structs reales del AST (generadas desde nucleo/ast_nodes.syn,
     mismas que usa el build S2/S3),
  2) el parser embebido _P_* (emitir_parsear),
y verifica el arbol resultante de parsear varios fragmentos.
"""
import os
import subprocess
import sys
import tempfile

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from compilador.ast_nodes import Programa
from compilador.generator.context import GeneratorContext
from compilador.generator.emit_selfhost import emitir_parsear
from compilador.generator import GeneradorC
from pipeline import compilar_desde_texto
from cli import _resolver_gcc


def _codigo_header() -> str:
    ast, diag = compilar_desde_texto(
        os.path.join(RAIZ, "nucleo", "ast_nodes.syn"), set())
    assert not diag.hay_errores(), "Error al compilar ast_nodes.syn"
    return GeneradorC(ast).generar(modo='header')


def _codigo_parser() -> str:
    ctx = GeneratorContext(Programa(sentencias=[], is_no_std=False))
    emitir_parsear(ctx, None)
    return "\n".join(ctx.lineas)


_MAIN_C = r"""
static int _n_fails = 0;
static void _chk(int cond, const char* msg) {
    if (!cond) { printf("FAIL: %s\n", msg); _n_fails++; }
    else { printf("OK: %s\n", msg); }
}
static int _len(struct ListaNodo* l) { int n = 0; while (l) { n++; l = l->cola; } return n; }
static struct Nodo* _at(struct ListaNodo* l, int i) { while (l && i > 0) { l = l->cola; i--; } return l ? l->cabeza : NULL; }
static const char* _cs(CadenaSegura s) { return s.datos ? s.datos : ""; }

int main(void) {
    {
        CadenaSegura f = { (int)strlen("tipo Edad = entero\n"), "tipo Edad = entero\n" };
        struct Programa p = parsear(f);
        _chk(_len(p.sentencias) == 1, "alias: 1 sentencia");
        struct DeclaracionTipo* d = (struct DeclaracionTipo*)_at(p.sentencias, 0);
        _chk(d && strcmp(_cs(d->tipo), "DeclaracionTipo") == 0, "alias: nodo DeclaracionTipo");
        _chk(d && strcmp(_cs(d->nombre), "Edad") == 0, "alias: nombre Edad");
        _chk(d && strcmp(_cs(d->tipo_base), "entero") == 0, "alias: tipo_base entero");
        _chk(d && d->constructores == NULL && d->parametros_tipo == NULL, "alias: sin constructores ni genericos");
    }
    {
        CadenaSegura f = { (int)strlen("tipo Resultado<T, E> = ok(T) | err(E)\n"), "tipo Resultado<T, E> = ok(T) | err(E)\n" };
        struct Programa p = parsear(f);
        _chk(_len(p.sentencias) == 1, "adt: 1 sentencia");
        struct DeclaracionTipo* d = (struct DeclaracionTipo*)_at(p.sentencias, 0);
        _chk(d && strcmp(_cs(d->tipo), "DeclaracionTipo") == 0, "adt: nodo DeclaracionTipo");
        _chk(d && strcmp(_cs(d->nombre), "Resultado") == 0, "adt: nombre Resultado");
        _chk(d && _len(d->parametros_tipo) == 2, "adt: 2 parametros tipo");
        _chk(d && _len(d->constructores) == 2, "adt: 2 constructores");
        struct ConstructorTipo* c0 = d ? (struct ConstructorTipo*)_at(d->constructores, 0) : NULL;
        _chk(c0 && strcmp(_cs(c0->tipo), "ConstructorTipo") == 0, "adt: ctor0 es ConstructorTipo");
        _chk(c0 && strcmp(_cs(c0->nombre), "ok") == 0 && _len(c0->tipos) == 1, "adt: ctor0 ok(T)");
        struct Identificador* t0 = c0 ? (struct Identificador*)_at(c0->tipos, 0) : NULL;
        _chk(t0 && strcmp(_cs(t0->nombre), "T") == 0, "adt: tipo T");
        struct ConstructorTipo* c1 = d ? (struct ConstructorTipo*)_at(d->constructores, 1) : NULL;
        _chk(c1 && strcmp(_cs(c1->nombre), "err") == 0 && _len(c1->tipos) == 1, "adt: ctor1 err(E)");
    }
    {
        CadenaSegura f = { (int)strlen("tipo R = (ok(entero) | err(texto))\n"), "tipo R = (ok(entero) | err(texto))\n" };
        struct Programa p = parsear(f);
        struct DeclaracionTipo* d = (struct DeclaracionTipo*)_at(p.sentencias, 0);
        _chk(d && strcmp(_cs(d->nombre), "R") == 0, "adt-parentesis: nombre R");
        _chk(d && _len(d->constructores) == 2, "adt-parentesis: 2 constructores");
        struct ConstructorTipo* c0 = d ? (struct ConstructorTipo*)_at(d->constructores, 0) : NULL;
        struct Identificador* e0 = c0 ? (struct Identificador*)_at(c0->tipos, 0) : NULL;
        _chk(e0 && strcmp(_cs(e0->nombre), "entero") == 0, "adt-parentesis: ok(entero)");
    }
    {
        CadenaSegura f = { (int)strlen("funcion f() -> nulo:\n    x = nulo\n    t = tensor(4, 5)\n"),
                           "funcion f() -> nulo:\n    x = nulo\n    t = tensor(4, 5)\n" };
        struct Programa p = parsear(f);
        _chk(_len(p.sentencias) == 1, "func: 1 sentencia");
        struct DefinicionFuncion* fn = (struct DefinicionFuncion*)_at(p.sentencias, 0);
        _chk(fn && strcmp(_cs(fn->tipo), "DefinicionFuncion") == 0, "func: nodo funcion");
        _chk(fn && strcmp(_cs(fn->tipo_retorno), "nulo") == 0, "func: retorno nulo");
        struct AsignacionVariable* a0 = fn ? (struct AsignacionVariable*)_at(fn->cuerpo, 0) : NULL;
        _chk(a0 && strcmp(_cs(a0->tipo), "AsignacionVariable") == 0, "func: stmt0 asignacion");
        _chk(a0 && a0->expresion && strcmp(_cs(a0->expresion->tipo), "LiteralNulo") == 0, "func: nulo -> LiteralNulo");
        struct AsignacionVariable* a1 = fn ? (struct AsignacionVariable*)_at(fn->cuerpo, 1) : NULL;
        _chk(a1 && a1->expresion && strcmp(_cs(a1->expresion->tipo), "ExprTensor") == 0, "func: tensor -> ExprTensor");
        struct ExprTensor* te = a1 ? (struct ExprTensor*)a1->expresion : NULL;
        _chk(te && te->filas && strcmp(_cs(te->filas->tipo), "LiteralNumero") == 0, "func: tensor.filas es numero");
        _chk(te && te->filas && ((struct LiteralNumero*)te->filas)->valor == 4, "func: tensor.filas = 4");
        _chk(te && te->columnas && ((struct LiteralNumero*)te->columnas)->valor == 5, "func: tensor.columnas = 5");
    }
    printf(_n_fails == 0 ? "ALL PASS\n" : "FAILURES: %d\n", _n_fails);
    return _n_fails == 0 ? 0 : 1;
}
"""


def _gcc_disponible() -> bool:
    try:
        gcc = _resolver_gcc()
        subprocess.run([gcc, "--version"], capture_output=True, check=True, timeout=10)
        return True
    except Exception:
        return False


def test_frontend_embebido_d_f1():
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    codigo = _codigo_header() + "\n" + _codigo_parser() + "\n" + _MAIN_C
    with tempfile.TemporaryDirectory(prefix="synapse_df1_") as tmpdir:
        c_path = os.path.join(tmpdir, "harness.c")
        exe_path = os.path.join(tmpdir, "harness.exe")
        with open(c_path, "w", encoding="utf-8") as f:
            f.write(codigo)
        gcc = _resolver_gcc()
        compile_proc = subprocess.run(
            [gcc, "-I", RAIZ, "-o", exe_path, c_path],
            capture_output=True, text=True, timeout=180,
        )
        assert compile_proc.returncode == 0, (
            f"gcc fallo:\n{compile_proc.stdout}\n{compile_proc.stderr}"
        )
        run_proc = subprocess.run(
            [exe_path], capture_output=True, text=True, timeout=30,
        )
        assert run_proc.returncode == 0, (
            f"harness fallo rc={run_proc.returncode}\n{run_proc.stdout}\n{run_proc.stderr}"
        )
