"""
tests/test_codegen_embebido_d_f1d.py
F1.2d / D-F1 (Micro-entregable): activa `@export` (declaracion_export) y los tipos
`arc<T>`/`debil<T>` (conteo de referencias) en el frontend embebido y el codegen
S1/S2/S3, con paridad S1 vs S2 y determinismo de bootstrap (diff 0):

  1. Serializacion canonica de `@export ( IDENT ) funcion` y de tipos arc/debil
     (round-trip .syn.json).
  2. Codegen S1: `arc<T>`/`debil<T>` -> `void*` (ABI placeholder, Manual 2 S4.3;
     runtime real en Fase 23), la funcion envuelta se emite con su cuerpo
     (visibilidad FFI), y `let ref: debil<X>` respeta la anotacion.
  3. E2E S1: programa con `@export` + arc/debil compila por el pipeline y ejecuta.
  4. E2E S2 (condicional): si existe synapse_stage*.exe (build bootstrap), el
     generador nativo S2 produce el MISMO comportamiento que S1.

Manuales: Manual 2, Seccion 2 L81 (declaracion_export ::= "@export" "(" IDENTIFICADOR
")" declaracion_funcion) y L151-153 ("arc" tipo, "debil" tipo); Manual 2, Seccion
3 L254-257 (T_EXPORT / T_ARC / T_DEBIL multi-idioma: debil/weak/faible/fraco); Manual
2, Seccion 4.3 L290-292 (conteo de referencias rc/arc/debil); Manual 6, Seccion 4
(directiva @export para bindings FFI); Manual 9, Seccion 9.7 (determinismo: diff 0
bytes S2 vs S3). Hito: D-F1 / F1.2 / F1.2d (cierre de FASE B).
"""
import json
import os
import subprocess
import sys
import tempfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from pipeline import compilar_desde_texto
from compilador.canonical import ast_a_canonico, canonico_a_ast
from compilador.generator import GeneradorC
from cli import _resolver_gcc

_PROGRAMA = """\
#lang: es

estructura NodoLista:
    valor: entero
    siguiente: arc<NodoLista>

@export ( python ) funcion sumar(a: entero, b: entero) -> entero:
    let r = a + b
    retornar r

funcion principal() -> nulo:
    let ref: d\u00e9bil<NodoLista> = nulo
    escribir_linea(entero_a_texto(sumar(2, 3)))
    retornar
"""

_SALIDA_ESPERADA = ["5"]

# F1.2d: funciones @export que se llaman entre si — el llamador (duplicar) precede
# al callejero (sumar) en el fuente, por lo que el prototipo de la funcion exportada
# es necesario (Manual 2 §2 L81; paridad S1/S2 con _emit_prototipos_funciones y el
# bucle de prototipos del orquestador).
_PROGRAMA_CRUZADA = """\
#lang: es

@export ( python ) funcion duplicar(v: entero) -> entero:
    retornar sumar(v, v)

@export ( python ) funcion sumar(a: entero, b: entero) -> entero:
    retornar a + b

funcion principal() -> nulo:
    escribir_linea(entero_a_texto(duplicar(4)))
    retornar
"""

_SALIDA_CRUZADA = ["8"]


def _compilar_ast():
    with tempfile.TemporaryDirectory(prefix="synapse_f12d_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA)
        ast, diag = compilar_desde_texto(src, set())
        assert not diag.hay_errores(), "Error compilando el programa F1.2d"
        return ast


def _gcc_disponible() -> bool:
    try:
        gcc = _resolver_gcc()
        subprocess.run([gcc, "--version"], capture_output=True, check=True, timeout=10)
        return True
    except Exception:
        return False


def test_canonico_export_arc_debil_serializable():
    """F1.2d: `@export ( IDENT ) funcion` y los tipos arc/debil serializan a
    .syn.json y hacen round-trip sin perdida (destino y anotaciones)."""
    src = """#lang: es

estructura NodoLista:
    valor: entero
    siguiente: arc<NodoLista>

@export ( python ) funcion sumar(a: entero, b: entero) -> entero:
    retornar a + b
"""
    with tempfile.TemporaryDirectory(prefix="synapse_f12d_") as tmp:
        path = os.path.join(tmp, "p.syn")
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        ast, diag = compilar_desde_texto(path, set())
        assert not diag.hay_errores(), "Error compilando programa F1.2d canonico"
        can = ast_a_canonico(ast)
        data = json.loads(can)
        assert data["synapse"] == "2.0"
        ast2 = canonico_a_ast(can)
        tipos = [type(s).__name__ for s in ast2.sentencias]
        assert tipos == ["DefinicionEstructura", "DeclaracionExport"], (
            f"round-trip F1.2d inesperado: {tipos}")
        exp = [s for s in ast2.sentencias
               if type(s).__name__ == "DeclaracionExport"][0]
        assert exp.destino == "python", "destino de @export preservado"
        assert type(exp.funcion).__name__ == "DefinicionFuncion", (
            "funcion envuelta preservada")
        assert exp.funcion.nombre == "sumar"
        est = [s for s in ast2.sentencias
               if type(s).__name__ == "DefinicionEstructura"][0]
        tipos_campos = [c.tipo for c in est.campos]
        assert tipos_campos == ["entero", "arc<NodoLista>"], (
            f"tipo arc en campo preservado: {tipos_campos}")


def test_codegen_s1_export_arc_debil():
    """F1.2d: el generador de referencia (S1) traduce arc/debil a void* (ABI
    placeholder, Manual 2 S4.3 / Manual 4) y emite la funcion envuelta de
    @export con su cuerpo (visibilidad para bindings FFI, Manual 6 S4)."""
    ast = _compilar_ast()
    codigo = GeneradorC(ast).generar()
    # Manual 2 S4.3 L151-153 + S4.1: arc<T>/debil<T> -> void* (placeholder ABI)
    assert "void* siguiente;" in codigo, (
        "campo arc<NodoLista> -> void* siguiente;")
    assert "void* ref = nulo;" in codigo, (
        "let ref: debil<NodoLista> = nulo -> void* ref = nulo;")
    # Manual 2 S2 L81 + Manual 6 S4: la funcion de @export se emite con cuerpo
    assert "int sumar(int a, int b) {" in codigo, (
        "@export ( python ) funcion sumar -> int sumar(int a, int b) {")
    assert "return a + b;" in codigo or "return r;" in codigo, (
        "cuerpo de la funcion exportada presente en el C de salida")


def test_codegen_s1_export_varias_posiciones():
    """F1.2d: arc/debil como tipo de retorno, parametro y variable con
    anotacion explicita (cobertura del mapeo en todas las posiciones)."""
    src = """#lang: es

estructura NodoLista:
    valor: entero
    siguiente: arc<NodoLista>

funcion crear_nodo(v: entero) -> arc<NodoLista>:
    retornar nulo

funcion principal() -> nulo:
    let nodo: arc<NodoLista> = crear_nodo(1)
    let debil_ref: d\u00e9bil<NodoLista> = nulo
    retornar
"""
    with tempfile.TemporaryDirectory(prefix="synapse_f12d_") as tmp:
        path = os.path.join(tmp, "p.syn")
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        ast, diag = compilar_desde_texto(path, set())
        assert not diag.hay_errores(), "Error compilando programa arc/debil S1"
        codigo = GeneradorC(ast).generar()
        assert "void* crear_nodo(int v) {" in codigo, (
            "retorno arc<NodoLista> -> void* crear_nodo(int v) {")
        assert "void* nodo = crear_nodo(1);" in codigo, (
            "let nodo: arc<NodoLista> -> void* nodo = ...;")
        assert "void* debil_ref = nulo;" in codigo, (
            "let debil_ref: debil<NodoLista> -> void* debil_ref = nulo;")


def test_e2e_s1_f12d():
    """F1.2d: el programa con @export + arc/debil compila por el pipeline (S1)
    y ejecuta con la salida esperada."""
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_f12d_") as tmp:
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


def test_codegen_s1_export_llamadas_cruzadas():
    """F1.2d: funciones @export que se llaman entre si obtienen prototipos
    (el llamador precede al callejero en el fuente; sin prototipo el C fallaria
    por 'implicit declaration')."""
    with tempfile.TemporaryDirectory(prefix="synapse_f12d_") as tmp:
        path = os.path.join(tmp, "p.syn")
        with open(path, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA_CRUZADA)
        ast, diag = compilar_desde_texto(path, set())
        assert not diag.hay_errores(), "Error compilando programa cruzado F1.2d"
        codigo = GeneradorC(ast).generar()
        assert "int sumar(int a, int b);" in codigo, (
            "prototipo de la funcion exportada llamada antes de su definicion")


def test_e2e_s1_f12d_cruzada():
    """F1.2d: el programa con llamadas cruzadas entre funciones @export compila
    por el pipeline (S1) y ejecuta con la salida esperada."""
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_f12d_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        exe = os.path.join(tmp, "programa.exe")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA_CRUZADA)
        proc = subprocess.run(
            [sys.executable, os.path.join(RAIZ, "main.py"), src, "-o", exe],
            capture_output=True, text=True, timeout=600,
        )
        assert proc.returncode == 0, (
            f"main.py fallo:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")
        run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, f"programa fallo rc={run.returncode}"
        assert run.stdout.splitlines() == _SALIDA_CRUZADA, (
            f"salida inesperada: {run.stdout.splitlines()}")


def test_e2e_s2_f12d_cruzada():
    """F1.2d: los generadores nativos S2/S3 emiten prototipos para funciones
    @export cruzadas y el programa ejecuta con la salida esperada (paridad S1)."""
    stages = ["synapse_stage1.exe", "synapse_stage2.exe", "synapse_stage3.exe"]
    disponibles = [s for s in stages if os.path.exists(os.path.join(RAIZ, s))]
    if not disponibles:
        pytest.skip("synapse_stage*.exe no disponible (ejecutar build.bat bootstrap-full)")
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_f12d_") as tmp:
        src = os.path.join(tmp, "programa.syn")
        exe = os.path.join(tmp, "programa.exe")
        with open(src, "w", encoding="utf-8") as f:
            f.write(_PROGRAMA_CRUZADA)
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
            assert run.stdout.splitlines() == _SALIDA_CRUZADA, (
                f"salida {stage} inesperada: {run.stdout.splitlines()}")


def test_e2e_s2_f12d():
    """F1.2d: el generador nativo S2 (synapse_stage*.exe) produce el mismo
    comportamiento que S1 para @export + arc/debil (paridad S1/S2/S3)."""
    stages = ["synapse_stage1.exe", "synapse_stage2.exe", "synapse_stage3.exe"]
    disponibles = [s for s in stages if os.path.exists(os.path.join(RAIZ, s))]
    if not disponibles:
        pytest.skip("synapse_stage*.exe no disponible (ejecutar build.bat bootstrap-full)")
    if not _gcc_disponible():
        pytest.skip("gcc no disponible en este entorno")
    with tempfile.TemporaryDirectory(prefix="synapse_f12d_") as tmp:
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
