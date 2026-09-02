"""Paridad .syn vs .syq — cierre formal de Fase 22 (ROADMAP: "mismo AST canónico
para construcciones equivalentes").

Manuales:
  - Manual 1 §3.1 (pipeline compartido tras el traductor)
  - Manual 2 §2 L47-54 (EBNF módulo: funcion, estructura, constante, etc.)
  - Manual 3 §11.1 (mapeo SyQuex → SemNodo[] canónico de Synapse)
  - Manual 3 §11.2 (preservación de metadatos: archivo, línea, columna)

Estrategia:
  - Cada fixture es un PAR (.syn, .syq) con fuentes equivalentes (misma
    estructura canónica, mismo orden de líneas).
  - .syn se parsea vía el pipeline S1 Python (pipeline.compilar_desde_texto →
    Lexer → Parser → Programa).
  - .syq se parsea vía el frontend SyQuex (exe syq_frontend → JSON plano →
    plano_a_programa → Programa).
  - Ambos Programa se serializan con el serializador canónico recursivo
    (basado en dataclasses) y se comparan byte a byte.
"""
import dataclasses
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline import compilar_desde_texto, compilar_desde_syq  # noqa: E402
from compilador.ast_nodes import Programa, DefinicionFuncion, SentenciaSi  # noqa: E402

FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "paridad"


def ser(obj, include_meta=False):
    """Serializador canónico recursivo del Programa AST.

    Produce una representación determinista (DFS, campos en orden de
    declaración del dataclass) que es idéntica para .syn y .syq si los
    ASTs son estructuralmente equivalentes.

    include_meta=True conserva linea/columna (Manual 3 §11.2).
    """
    if obj is None:
        return '()'
    if isinstance(obj, bool):
        return 'T' if obj else 'F'
    if isinstance(obj, str):
        return obj
    if isinstance(obj, int):
        return str(obj)
    if isinstance(obj, float):
        return repr(obj)
    if isinstance(obj, list):
        return '[' + ','.join(ser(x, include_meta) for x in obj) + ']'
    if isinstance(obj, tuple):
        return '(' + ','.join(ser(x, include_meta) for x in obj) + ')'
    if dataclasses.is_dataclass(obj):
        cls = obj.__class__.__name__
        fields = dataclasses.fields(obj)
        parts = []
        for f in fields:
            fname = f.name
            if not include_meta and fname in ('linea', 'columna'):
                continue
            parts.append(fname + '=' + ser(getattr(obj, fname, None), include_meta))
        return cls + '(' + ','.join(parts) + ')'
    return str(obj)


PARITY_PAIRS = [
    "basic_function",
    "struct_and_constant",
    "control_flow",
    "function_call",
    "coincidir_basic",
]


@pytest.mark.parametrize("name", PARITY_PAIRS)
def test_paridad_estructural_syn_vs_syq(name):
    """ROADMAP F22: '.syq genera el mismo AST canónico que Synapse para
    construcciones equivalentes'. Comparación estructural (sin metadata)."""
    syn_path = FIXTURES / f"{name}.syn"
    syq_path = FIXTURES / f"{name}.syq"
    assert syn_path.exists(), f"fixture faltante: {syn_path}"
    assert syq_path.exists(), f"fixture faltante: {syq_path}"

    syn_prog, syn_diag = compilar_desde_texto(str(syn_path), set())
    assert not syn_diag.hay_errores(), \
        f".syn falló: {syn_diag.errores}"

    syq_prog = compilar_desde_syq(str(syq_path))

    syn_dump = ser(syn_prog)
    syq_dump = ser(syq_prog)
    assert syn_dump == syq_dump, (
        f"PARIDAD ESTRUCTURAL FALLÓ para '{name}':\n"
        f"  .syn: {syn_dump}\n  .syq: {syq_dump}"
    )


def test_si_sino_paridad():
    """R94 fix: el frontend SyQuex debe preservar cuerpo_sino de SentenciaSi
    (Bug: syq_json.syn hardcodeaba extra=0 → cuerpo_sino siempre None).

    Manual 3 §11.1: NODO_SI ↔ SentenciaSi con cuerpo_sino.
    Manual 3 §11.2: ptr_extra se serializa en el JSON canónico.
    """
    syn_path = FIXTURES / "control_flow.syn"
    syq_path = FIXTURES / "control_flow.syq"

    syn_prog, syn_diag = compilar_desde_texto(str(syn_path), set())
    assert not syn_diag.hay_errores()
    syq_prog = compilar_desde_syq(str(syq_path))

    # Both should have the same structure
    assert ser(syn_prog) == ser(syq_prog)

    # And cuerpo_sino must be populated (not None) in both
    syn_si = _find_first_si(syn_prog)
    syq_si = _find_first_si(syq_prog)
    assert syn_si is not None, "no SentenciaSi found in .syn AST"
    assert syq_si is not None, "no SentenciaSi found in .syq AST"
    assert syn_si.cuerpo_sino is not None and len(syn_si.cuerpo_sino) > 0, \
        ".syn: cuerpo_sino vacío"
    assert syq_si.cuerpo_sino is not None and len(syq_si.cuerpo_sino) > 0, \
        ".syq: cuerpo_sino vacío (fix R94 no aplicado)"


def _find_first_si(prog: Programa) -> SentenciaSi:
    """Busca recursivamente la primera SentenciaSi en el Programa."""
    def walk(nodes):
        for n in nodes:
            if isinstance(n, SentenciaSi):
                return n
            if isinstance(n, DefinicionFuncion):
                found = walk(n.cuerpo)
                if found:
                    return found
            if isinstance(n, SentenciaSi):
                found = walk(n.cuerpo)
                if found:
                    return found
                if n.cuerpo_sino:
                    found = walk(n.cuerpo_sino)
                    if found:
                        return found
        return None
    return walk(prog.sentencias)
