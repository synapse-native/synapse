# cumple Manual 2 4
"""
test_ast_nodos_consistency.py — D-9(e): verificación cross-language
de que runtime/core/ast_nodos.h coincide 1:1 con nucleo/parser_constantes.syn.

Regla 13 (Modularización) + D-9(e) (consolidación de NodoID/TokenID):
El header CANÓNICO C debe reflejar EXACTAMENTE los valores definidos en
parser_constantes.syn (fuente de verdad del compilador Synapse).

Si este test falla, alguien cambió parser_constantes.syn sin regenerar
ast_nodos.h → el runtime C usaría valores STALE → divergencia silenciosa.

Fuente de verdad: nucleo/parser_constantes.syn
Header canónico:  runtime/core/ast_nodos.h
"""
import os
import re
import sys
import pytest

pytestmark = pytest.mark.unit

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SYN_SOURCE = os.path.join(PROJECT_ROOT, "nucleo", "parser_constantes.syn")
C_HEADER = os.path.join(PROJECT_ROOT, "runtime", "core", "ast_nodos.h")

RE_CONSTANTE = re.compile(r"^\s*constante\s+(T_[A-Z_]+|NODO_[A-Z_]+)\s*=\s*(\d+)\s*(?:\#.*)?$")
RE_DEFINE = re.compile(r"^\s*#\s*define\s+(T_[A-Z_]+|NODO_[A-Z_]+)\s+\((\d+)LL\)\s*$")


def _parse_syn(path):
    """Extrae {'T_SI': 1, 'NODO_FUNCION': 2, ...} desde parser_constantes.syn."""
    vals = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = RE_CONSTANTE.match(line)
            if m:
                vals[m.group(1)] = int(m.group(2))
    return vals


def _parse_header(path):
    """Extrae {'T_SI': 1, 'NODO_FUNCION': 2, ...} desde ast_nodos.h."""
    vals = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = RE_DEFINE.match(line)
            if m:
                vals[m.group(1)] = int(m.group(2))
    return vals


def test_header_exists():
    assert os.path.isfile(C_HEADER), f"Header canónico no encontrado: {C_HEADER}"


def test_syn_source_exists():
    assert os.path.isfile(SYN_SOURCE), f"Fuente de verdad no encontrada: {SYN_SOURCE}"


def test_tokenid_consistency():
    syn_vals = _parse_syn(SYN_SOURCE)
    c_vals = _parse_header(C_HEADER)
    syn_tok = {k: v for k, v in syn_vals.items() if k.startswith("T_")}
    bin_tok = {k: v for k, v in c_vals.items() if k.startswith("T_")}
    for name in syn_tok:
        assert name in bin_tok, f"TokenID {name} en parser_constantes.syn pero FALTA en ast_nodos.h"
        assert bin_tok[name] == syn_tok[name], (
            f"TokenID {name}: syn={syn_tok[name]} header={bin_tok[name]} — DIVERGENCIA"
        )
    extra = set(bin_tok) - set(syn_tok)
    assert not extra, f"TokenID en header pero NO en syn: {sorted(extra)}"


def test_nodoid_consistency():
    syn_vals = _parse_syn(SYN_SOURCE)
    c_vals = _parse_header(C_HEADER)
    syn_nodos = {k: v for k, v in syn_vals.items() if k.startswith("NODO_")}
    bin_nodos = {k: v for k, v in c_vals.items() if k.startswith("NODO_")}
    for name in syn_nodos:
        assert name in bin_nodos, f"NodoID {name} en syn pero FALTA en header"
        assert bin_nodos[name] == syn_nodos[name], (
            f"NodoID {name}: syn={syn_nodos[name]} header={bin_nodos[name]} — DIVERGENCIA"
        )
    extra = set(bin_nodos) - set(syn_nodos)
    assert not extra, f"NodoID en header pero NO en syn: {sorted(extra)}"


def test_completeness():
    """Verifica que el header tenga TODOS los T_* y NODO_* de parser_constantes.syn."""
    syn_vals = _parse_syn(SYN_SOURCE)
    c_vals = _parse_header(C_HEADER)
    assert len(c_vals) == len(syn_vals), (
        f"Conteo: syn={len(syn_vals)} header={len(c_vals)} — NO COINCIDE"
    )
