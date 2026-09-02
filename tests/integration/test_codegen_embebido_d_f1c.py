"""
tests/test_codegen_embebido_d_f1c.py
F1.2c / D-F1 (Micro-entregable): activa `let` (declaracion_variable) y `delegar`
(propagacion de error) en el frontend embebido y el codegen S1/S2/S3, con paridad
S1 vs S2:

  1. Serializacion canonica de `let`/`delegar` (round-trip .syn.json).
  2. Codegen S1: inferencia de tipo (int/float/CadenaSegura), anotacion explicita,
     y patron `?` para `delegar` (Resultado.tag == err -> return).
  3. E2E S1: programa con `let` compila por el pipeline y ejecuta.
  4. E2E S2 (condicional): si existe synapse_stage*.exe (build bootstrap), el
     generador nativo S2 produce el MISMO comportamiento que S1.

Manuales: Manual 2 seccion 2 L134 (declaracion_variable ::= "let" IDENTIFICADOR
[ ":" tipo ] [ "=" expresion ] NEWLINE) y L132 (delegar ::= "delegar" expresion,
"Para el operador ? en Syquex, traducido a retornar err(...)"); Manual 2 seccion
5.1 (T_LET, T_DELEGAR) y 7.2 (NODO_DELEGAR 55); Manual 3 seccion 7 (Resultado +
operador ?: si es err retorna el error de la funcion actual).
"""
import json
import os
import subprocess
import sys
import tempfile

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from pipeline import compilar_desde_texto
from compilador.canonical import ast_a_canonico, canonico_a_ast
from compilador.generator import GeneradorC
from cli import _resolver_gcc

_PROGRAMA = """\
#lang: es

funcion principal() -> nulo:
    let x = 5
    let edad: entero = 10
    let s = "hola"
    let suma = 2.5
    let m = suma + 1.5
    let f = 3.0 * 2
    escribir_linea(entero_a_texto(x + edad))
    escribir_linea(s)
    escribir_linea(decimal_a_texto(m))
    escribir_linea(decimal_a_texto(f))
    retornar
"""

_SALIDA_ESPERADA = ["15", "hola", "4.000000", "6.000000"]


def _compilar_ast():
    with tempfile.TemporaryDirectory(prefix="synapse_f12c_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA)
        ast, diag = compilar_desde_texto(src, set())
        assert not diag.hay_errores(), "Error compilando el programa F1.2c"
        return ast


def _gcc_disponible() -> bool:
    try:
        gcc = _resolver_gcc()
        subprocess.run([gcc, "--version"], capture_output=True, check=True, timeout=10)
        return True
    except Exception:
        return False


def test_canonico_let_delegar_serializable():
    """F1.2c: el AST con `let`/`delegar` serializa a .syn.json y hace round-trip."""
    src = """#lang: es

tipo Resultado<T, E> = ok(T) | err(E)

funcion f() -> nulo:
    let x = 5
    let edad: entero = 10
    let s = "hola"
    let sin_valor
    delegar f()
    retornar
"""
    with tempfile.TemporaryDirectory(prefix="synapse_f12c_") as tmp:
        path = os.path.join(tmp, "p.syn")
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        ast, diag = compilar_desde_texto(path, set())
        assert not diag.hay_errores(), "Error compilando programa F1.2c canonico"
        can = ast_a_canonico(ast)
        data = json.loads(can)
        assert data["synapse"] == "2.0"
        ast2 = canonico_a_ast(can)
        fn = [s for s in ast2.sentencias
              if type(s).__name__ == "DefinicionFuncion"][0]
        cuerpo = fn.cuerpo
        sent = cuerpo.sentencias if hasattr(cuerpo, "sentencias") else cuerpo
        tipos = [type(s).__name__ for s in sent]
        assert tipos == [
            "DeclaracionVariable", "DeclaracionVariable", "DeclaracionVariable",
            "DeclaracionVariable", "SentenciaDelegar", "SentenciaRetornar"], (
            f"round-trip F1.2c inesperado: {tipos}")
        dvs = [s for s in sent if type(s).__name__ == "DeclaracionVariable"]
        assert dvs[1].tipo == "entero", "anotacion de tipo explicita preservada"
        assert dvs[3].expresion is None, "let sin inicializador"


def test_codegen_s1_let_delegar():
    """F1.2c: el generador de referencia (S1) infiere tipos de `let`, respeta la
    anotacion explicita y emite el patron `?` de Resultado para `delegar`."""
    ast = _compilar_ast()
    codigo = GeneradorC(ast).generar()
    # Manual 2 L134: let IDENT [":" tipo] ["=" expresion]
    assert "int64_t x = 5LL;" in codigo, "let x = 5 -> int64_t x = 5LL;"
    assert "int64_t edad = 10LL;" in codigo, "let edad: entero = 10 -> int64_t edad = 10LL;"
    assert "CadenaSegura s =" in codigo, "let s = \"hola\" -> CadenaSegura s = ..."
    # Manual 3 §7.2: `let suma = 0.0` infiere decimal/float
    assert "double suma = 2.5;" in codigo, "let suma = 2.5 -> double suma = 2.5;"


def test_codegen_s1_delegar_patron():
    """F1.2c: `delegar expr` -> bloque Resultado con propagacion de err (tag 1)."""
    src = """#lang: es

tipo Resultado<T, E> = ok(T) | err(E)

funcion f() -> nulo:
    delegar f()
    retornar
"""
    with tempfile.TemporaryDirectory(prefix="synapse_f12c_") as tmp:
        path = os.path.join(tmp, "p.syn")
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        ast, diag = compilar_desde_texto(path, set())
        assert not diag.hay_errores(), "Error compilando programa delegar S1"
        codigo = GeneradorC(ast).generar()
        assert "Resultado _del = f();" in codigo, "delegar -> Resultado _del = expr;"
        assert "if (_del.tag == 1) return _del;" in codigo, (
            "propagacion de error cuando el tag es err (Manual 3 §7)")


def test_e2e_s1_f12c():
    """F1.2c: el programa con `let` compila por el pipeline (S1) y ejecuta."""
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_f12c_") as tmp:
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
        assert run.returncode == 0, f"programa fallo rc={run.returncode}"
        salida = run.stdout.splitlines()
        assert salida == _SALIDA_ESPERADA, f"salida inesperada: {salida}"


def test_e2e_s2_f12c():
    """F1.2c: el generador nativo S2 (synapse_stage*.exe) produce el mismo
    comportamiento que S1 para `let` (paridad S1/S2)."""
    stages = ["synapse_stage1.exe", "synapse_stage2.exe", "synapse_stage3.exe"]
    disponibles = [s for s in stages if os.path.exists(os.path.join(RAIZ, s))]
    if not disponibles:
        pytest.skip("synapse_stage*.exe no disponible (ejecutar build.bat bootstrap-full)")
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_f12c_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        exe = os.path.join(tmp, "programa.exe")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA)
        for stage in disponibles:
            stg = os.path.join(RAIZ, stage)
            proc = subprocess.run(
                [stg, src, exe], capture_output=True, text=True, timeout=600,
            )
            assert proc.returncode == 0, (
                f"{stage} fallo:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
            run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
            assert run.returncode == 0, (
                f"programa {stage} fallo rc={run.returncode}")
            salida = run.stdout.splitlines()
            assert salida == _SALIDA_ESPERADA, (
                f"salida {stage} inesperada: {salida}")
