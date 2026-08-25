"""
tests/test_codegen_embebido_d_f1.py
F1.2b / D-F1 (Micro-entregable): valida el CODEGEN de la Fase B en el
generador embebido S2/S3 (espejo de visitar_declaracion_tipo, _oo_expr_a_c
y traducir_tipo_c), con paridad S1 vs S2:

  1. Serializacion canonica de declaracion_tipo (alias/ADT con genericos) —
     regression del fix ConstructorTipo(Nodo) (ast_nodes.py): el AST canonico
     .syn.json debe poder generarse y round-trip-ease.
  2. Codegen S1 (GeneradorC 'completo'): typedef de alias, tagged-union del ADT,
     `nulo` -> macro nulo, `tensor(filas, cols)` -> crear_tensor(filas, cols),
     y hoisting de tipos (LiteralNulo -> void*, ExprTensor -> Tensor).
  3. E2E S1: el programa compilado por el pipeline ejecuta y produce la salida
     esperada.
  4. E2E S2 (condicional): si existe synapse_stage*.exe (build bootstrap), el
     generador nativo S2 produce el MISMO comportamiento que S1.

Manuales: Manual 2 seccion 2 (declaracion_tipo ::= "tipo" IDENTIFICADOR "=" ...)
y seccion 4 (nulo: ausencia de valor; tensor(filas, columnas) crea un tensor
de dimensiones [filas, columnas]); Manual 9 S9.7 (determinismo S2 vs S3).
"""
import json
import os
import subprocess
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from pipeline import compilar_desde_texto
from compilador.canonical import ast_a_canonico, canonico_a_ast
from compilador.generator import GeneradorC
from cli import _resolver_gcc

_PROGRAMA = """\
#lang: es

tipo Edad = entero

tipo Resultado<T, E> = ok(T) | err(E)

funcion principal() -> nulo:
    p = nulo
    t = tensor(2, 3)
    escribir_linea(entero_a_texto(t.filas))
    escribir_linea(entero_a_texto(t.columnas))
    escribir_linea("f12b ok")
"""

_SALIDA_ESPERADA = ["2", "3", "f12b ok"]


def _compilar_ast():
    with tempfile.TemporaryDirectory(prefix="synapse_f12b_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA)
        ast, diag = compilar_desde_texto(src, set())
        assert not diag.hay_errores(), "Error compilando el programa F1.2b"
        return ast


def _gcc_disponible() -> bool:
    try:
        gcc = _resolver_gcc()
        subprocess.run([gcc, "--version"], capture_output=True, check=True, timeout=10)
        return True
    except Exception:
        return False


def test_canonico_declaracion_tipo_serializable():
    """F1.2b: el AST con declaracion_tipo serializa a .syn.json y hace round-trip."""
    ast = _compilar_ast()
    declaraciones = [s for s in ast.sentencias
                     if type(s).__name__ == "DeclaracionTipo"]
    assert len(declaraciones) == 2, "Se esperan 2 declaracion_tipo (alias + ADT)"
    can = ast_a_canonico(ast)
    data = json.loads(can)
    assert data["synapse"] == "2.0"
    ast2 = canonico_a_ast(can)
    assert len(ast2.sentencias) == len(ast.sentencias) == 3
    assert [type(s).__name__ for s in ast2.sentencias] == [
        "DeclaracionTipo", "DeclaracionTipo", "DefinicionFuncion"]


def test_codegen_s1_declaracion_tipo():
    """F1.2b: el generador de referencia (S1) emite typedefs de alias/ADT,
    nulo -> macro nulo, tensor() -> crear_tensor() y hoisting de tipos."""
    ast = _compilar_ast()
    codigo = GeneradorC(ast).generar()
    # Manual 2 L74/L279-280: alias (`tipo Edad = entero`) y ADT con genericos.
    assert "typedef int64_t Edad;" in codigo, "alias -> typedef int64_t Edad;"
    assert "typedef struct Resultado { int64_t tag; union {" in codigo, "ADT -> tagged union"
    assert "void* ok;" in codigo and "void* err;" in codigo, (
        "genericos T/E -> placeholder puntero (void*)")
    assert "} Resultado;" in codigo, "cierre del typedef ADT"
    # Manual 2 L194-195: tensor(filas, columnas) crea un tensor [filas, columnas].
    assert "crear_tensor(2LL, 3LL)" in codigo, "ExprTensor -> crear_tensor(2LL, 3LL)"
    # Manual 2 L272: nulo = ausencia de valor -> macro nulo.
    assert "p = nulo;" in codigo, "LiteralNulo -> macro nulo"
    # Hoisting: LiteralNulo -> void*, ExprTensor -> Tensor (paridad tipo_de_expr).
    assert "void* p" in codigo and "Tensor t" in codigo, "hoisting de tipos"


def test_e2e_s1_f12b():
    """F1.2b: el programa completo compila por el pipeline (S1) y ejecuta."""
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_f12b_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        exe = os.path.join(tmp, "programa.exe")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA)
        proc = subprocess.run(
            [sys.executable, os.path.join(RAIZ, "main.py"), src, "-o", exe],
            capture_output=True, text=True, timeout=600,
        )
        assert proc.returncode == 0, (
            f"main.py fallo:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
        run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, f"programa fallo rc={run.returncode}\n{run.stdout}\n{run.stderr}"
        assert run.stdout.splitlines() == _SALIDA_ESPERADA


def test_e2e_s2_f12b_paridad():
    """F1.2b: el generador nativo S2 (synapse_stage*.exe) produce el mismo
    comportamiento que S1 (Manual 9 S9.7 determinismo). Condicional: requiere
    haber ejecutado el bootstrap (build.bat bootstrap-full)."""
    s2 = None
    for nombre in ("synapse_stage1.exe", "synapse_stage2.exe", "synapse_stage3.exe"):
        candidato = os.path.join(RAIZ, nombre)
        if os.path.isfile(candidato):
            s2 = candidato
            break
    if not s2:
        pytest.skip("synapse_stage*.exe no disponible (ejecutar build.bat bootstrap-full)")
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_f12b_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        exe = os.path.join(tmp, "programa_s2.exe")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA)
        try:
            proc = subprocess.run(
                [s2, src, exe],
                cwd=RAIZ, capture_output=True, text=True, timeout=600,
            )
            assert proc.returncode == 0, (
                f"S2 fallo:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
            run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
            assert run.returncode == 0, (
                f"programa S2 fallo rc={run.returncode}\n{run.stdout}\n{run.stderr}")
            assert run.stdout.splitlines() == _SALIDA_ESPERADA, (
                "salida S2 distinta a la esperada (paridad S1/S2)")
        finally:
            for artefacto in ("synapse_unity.c",):
                ruta = os.path.join(RAIZ, artefacto)
                try:
                    if os.path.isfile(ruta):
                        os.remove(ruta)
                except OSError:
                    pass
