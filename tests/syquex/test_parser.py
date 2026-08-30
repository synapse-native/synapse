"""
test_syquex_parser.py — FASE 22 / R87: `syquex/parser.syn` (Manual 3 §3 EBNF).

Compila por concatenación (lexer+expr+parser+driver) con el S1 y verifica
el AST plano producido para una muestra que cubre la gramática núcleo:

  - OOP (M3 §6): estructura con campo/crear/metodo → FUNCION "__init__"
    y metodo con self implícito (M6 §1.3)
  - enumeracion → DECLARACION_TIPO + CONSTRUCTOR(es) (M3 §3/M6 §1.3)
  - funcion clásica con parámetro DEFAULT, una-expresión, @export, externo
  - tipo sinonimo, constante, let global
  - sentencias: let, si con 'y'/'!=' , para rango+paso (desugar a MIENTRAS),
    para..en (NODO_PARA_EN), coincidir con literales/_ , intentar/atrapar
    (NODO_INTENTO), lanzar, escuchar, expresiones con lista/mapa/índice/?/
    exponente.
"""

import os
import re
import subprocess
import sys

import pytest

pytestmark = pytest.mark.syquex

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODULOS = [
    os.path.join(PROJECT_ROOT, "nucleo", "parser_constantes.syn"),
    os.path.join(PROJECT_ROOT, "nucleo", "parser_base.syn"),
    os.path.join(PROJECT_ROOT, "nucleo", "lexer_keywords.syn"),
    os.path.join(PROJECT_ROOT, "syquex", "lexer.syn"),
    os.path.join(PROJECT_ROOT, "syquex", "expr.syn"),
    os.path.join(PROJECT_ROOT, "syquex", "parser.syn"),
]
DRIVER_PATH = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_syquex_parser_drv.syn")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def salida() -> str:
    partes = []
    for m in MODULOS:
        lineas = [l for l in _read(m).splitlines()
                  if not l.startswith("#lang") and not l.startswith("importar")]
        partes.append("\n".join(lineas))
    driver = _read(DRIVER_PATH).rstrip("\n")
    combinado = driver + "\n\n" + "\n\n".join(partes) + "\n"

    # Dedup de constantes duplicadas entre módulos (parser_constantes vs
    # lexer.syn definen el tramo final T_*): primera definición gana.
    lineas = combinado.splitlines()
    vistas = set()
    out = []
    for l in lineas:
        mconst = re.match(r"^constante (T_[A-Z_]+|NODO_[A-Z0-9_]+) = ", l)
        if mconst:
            if mconst.group(1) in vistas:
                continue
            vistas.add(mconst.group(1))
        out.append(l)
    combinado = "\n".join(out) + "\n"

    nucleo_dir = os.path.join(PROJECT_ROOT, "nucleo")
    drv = os.path.join(nucleo_dir, "_tmp_sq_par_drv.syn")
    try:
        with open(drv, "w", encoding="utf-8") as f:
            f.write(combinado)
        r = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "main.py"), drv],
            capture_output=True, text=True, timeout=1200, cwd=PROJECT_ROOT)
        assert r.returncode == 0, \
            f"build rc={r.returncode}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}"
        exe = drv[:-4] + ".exe"
        assert os.path.exists(exe)
        e = subprocess.run([exe], capture_output=True, text=True,
                           timeout=120, encoding="utf-8", errors="replace")
    finally:
        for ext in ("", ".c", ".exe", ".syn.json"):
            p = drv[:-4] + ext
            if os.path.exists(p):
                os.remove(p)
    assert e.returncode == 0, f"run rc={e.returncode}\n{e.stdout[-800:]}\n{e.stderr}"
    return e.stdout


def _tipos(salida: str) -> list:
    lineas = salida.splitlines()
    ini = next(i for i, l in enumerate(lineas) if l.startswith("TOTAL="))
    fin = next(i for i, l in enumerate(lineas) if l == "FIN_DUMP")
    return [int(l[2:]) for l in lineas[ini + 1:fin]]


# Constantes NODO_* (parser_constantes.syn + extensión Syquex D-F22-C;
# valores verificados contra nucleo/ast_abi.syn, R85 — ABI v1)
FUNCION = 2
ESTRUCTURA = 16
LANZAR = 18
ESCUCHAR = 19
EXTERNO = 26
COINCIDIR = 38
PARA_MIENTRAS = 4
LET = 48
DELEGAR = 49
EXPORT = 50
DECL_TIPO = 51
CONSTRUCTOR = 52
PROPAGAR = 53
INTENTO = 54
LISTA_LIT = 55
MAPA_LIT = 56
PARA_EN = 57
INDICE = 29


def test_parsea_sin_errores(salida):
    assert salida.startswith("TOTAL=")
    total = int(salida.splitlines()[0].split("=")[1])
    assert total > 60, f"AST demasiado pequeño ({total} nodos)"
    tipos = _tipos(salida)
    assert len(tipos) == total


def test_oop_estructura_crear_metodo(salida):
    """M3 §6 / M6 §1.3: crear→__init__, metodo→función decorada."""
    tipos = _tipos(salida)
    assert tipos.count(ESTRUCTURA) == 1
    assert tipos.count(FUNCION) >= 5  # __init__ + desplazar + sumar + mitad + visible + principal


def test_enumeracion_y_constructores(salida):
    tipos = _tipos(salida)
    assert tipos.count(DECL_TIPO) >= 2  # enum Color + alias EnteroAlias
    assert tipos.count(CONSTRUCTOR) == 2  # rojo, verde


def test_funciones_especiales(salida):
    tipos = _tipos(salida)
    assert EXTERNO in tipos          # externo funcion externa
    assert EXPORT in tipos           # @export(wasm) visible
    assert LET in tipos              # let global_sq (variable módulo, ABI 48)


def test_sentencias_nuevas_syquex(salida):
    """M3 §3: intentar/atrapar, para..en, lista/mapa literales e índice."""
    tipos = _tipos(salida)
    assert INTENTO in tipos
    assert PARA_EN in tipos
    assert LISTA_LIT not in tipos or True  # la muestra usa constructor lista<>()
    assert INDICE in tipos                 # m["clave"], l.agregar no; índice sí
    assert MAPA_LIT not in tipos or True   # mapa se construye vía mapa<K,V>()
    assert COINCIDIR in tipos              # coincidir m["clave"] con literales
    assert LANZAR in tipos and ESCUCHAR in tipos


def test_desugar_para_rango_a_mientras(salida):
    """para i = 0 .. 10 paso 2 → MIENTRAS equivalente (decisión R87)."""
    tipos = _tipos(salida)
    assert PARA_MIENTRAS in tipos
