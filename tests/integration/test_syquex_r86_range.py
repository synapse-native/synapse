"""
test_syquex_r86_range.py — FASE 22 / R86: valida que el lexer/paser de Syquex
maneja correctamente el operador de rango `..` y el bucle `para i = a .. b`.

CRIT-1 (lexer): `0..5` debe tokenizar como T_NUMERO(0) + T_PUNTOPUNTO(..) + T_NUMERO(5),
no como T_FLOTANTE("0.") + T_PUNTO(".") + T_NUMERO("5"). Verificado indirectamente:
el frontend produce rc=0 y AST correcto (si el lexer fallara, rc != 0).
CRIT-2 (parser): `para i = 0 .. 4` desugara a:
  init(i=0) → mientras(i<4): cuerpo → incr(i=i+1)
(el init NO se pierde; el incremento va DESPUÉS del cuerpo).
"""

import json
import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from compilador.puente_canonico import plano_a_programa  # noqa: E402
from compilador.ast_nodes import (  # noqa: E402
    DefinicionFuncion,
    AsignacionVariable,
    SentenciaMientras,
    LiteralNumero,
)

FIXTURE = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_range_loop.syq")


@pytest.fixture(scope="module")
def flat_output():
    exe = os.path.join(PROJECT_ROOT, "build", "syq_frontend.exe")
    assert os.path.exists(exe), "ejecutar scripts/build_syquex_frontend.py"
    r = subprocess.run([exe, FIXTURE], capture_output=True, text=True,
                       timeout=120, encoding="utf-8", errors="replace")
    assert r.returncode == 0, f"frontend rc={r.returncode}\n{r.stderr}"
    return json.loads(r.stdout)


def test_lexer_no_float_en_rango(flat_output):
    """CRIT-1: `0..4` no produce T_FLOTANTE. Verificado indirectamente:
    el frontend produce rc=0 (si el lexer consumiera '.' como float,
    el parser fallaría con SYQ_JSON_ERROR=-3)."""
    nodos = flat_output["nodos"]
    # Buscar nodo tipo=4 (MIENTRAS)
    mientras_idx = None
    for i, n in enumerate(nodos):
        if n[0] == 4:  # NODO_MIENTRAS
            mientras_idx = i
            break
    assert mientras_idx is not None, "debe existir NODO_MIENTRAS en el AST"
    # El condition (hijo_izq del mientras) debe contener 0..4 como límites
    # No debe haber T_FLOTANTE (tipo 10) en los nodos
    for i, n in enumerate(nodos):
        assert n[0] != 10, f"T_FLOTANTE (tipo 10) inesperado en nodo {i}"


def test_ast_init_no_perdida(flat_output):
    """CRIT-2: el `init` (i = 0) debe estar presente como primer statement
    del cuerpo, con el MIENTRAS como hermano."""
    prog = plano_a_programa(flat_output)
    fn = prog.sentencias[0]
    assert isinstance(fn, DefinicionFuncion), f"esperaba función, got {type(fn)}"
    stmts = fn.cuerpo
    assert len(stmts) >= 2, f"esperaba >= 2 statements, got {len(stmts)}"
    # El primer statement debe ser la inicialización i=0 (AsignacionVariable)
    assert isinstance(stmts[0], AsignacionVariable), \
        f"primer stmt debe ser init (AsignacionVariable), got {type(stmts[0])}"
    assert stmts[0].nombre == "i", \
        f"init debe asignar a 'i', got {stmts[0].nombre!r}"
    assert isinstance(stmts[0].expresion, LiteralNumero), \
        f"init debe asignar 0, got {type(stmts[0].expresion)}"
    assert stmts[0].expresion.valor == 0


def test_ast_incremento_despues_cuerpo(flat_output):
    """CRIT-2: el incremento (i = i + 1) debe estar dentro del cuerpo del
    mientras, DESPUÉS de las sentencias originales del cuerpo."""
    prog = plano_a_programa(flat_output)
    fn = prog.sentencias[0]
    stmts = fn.cuerpo
    # stmts[1] debe ser el MIENTRAS (el traductor desenrolla BLOQUE_SQ)
    mientras = stmts[1]
    assert isinstance(mientras, SentenciaMientras), \
        f"esperaba SentenciaMientras, got {type(mientras)}"
    # El cuerpo del mientras debe contener: escribir_linea + incremento
    assert len(mientras.cuerpo) >= 2, \
        f"cuerpo mientras debe tener >=2 stmts, got {len(mientras.cuerpo)}"
    # El último statement del cuerpo del mientras debe ser el incremento
    assert isinstance(mientras.cuerpo[-1], AsignacionVariable), \
        f"último stmt de mientras debe ser incr, got {type(mientras.cuerpo[-1])}"
    assert mientras.cuerpo[-1].nombre == "i", \
        f"incr debe asignar a 'i', got {mientras.cuerpo[-1].nombre}"
