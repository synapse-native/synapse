#!/usr/bin/env python3
"""Debug: find the exact location of the int==texto type error"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Monkey-patch the OpBinaria type inference
import compilador.semantic_types as st
import compilador.ast_nodes as ast_nodes
from compilador.diagnostics import ErrorCodes

_original_inferir = st.AnalizadorSemanticoTypes._inferir_tipo

def _patched_inferir(self, nodo):
    if isinstance(nodo, ast_nodes.OpBinaria) and nodo.operador in ('==', '!='):
        tipo_izq = self._inferir_tipo(nodo.izquierdo)
        tipo_der = self._inferir_tipo(nodo.derecho)
        if tipo_izq and tipo_der:
            # Log BEFORE type checking
            print(f"[DEBUG] OpBinaria '{nodo.operador}' L{nodo.linea}:{nodo.columna} tipo_izq={tipo_izq!r} tipo_der={tipo_der!r}")
            with open('nucleo/principal.syn', 'r') as f:
                lines = f.readlines()
                if 1 <= nodo.linea <= len(lines):
                    print(f"[DEBUG]   Line {nodo.linea}: {lines[nodo.linea-1].rstrip()}")
    return _original_inferir(self, nodo)

st.AnalizadorSemanticoTypes._inferir_tipo = _patched_inferir

# Now also patch the type checker
_original_check = st.AnalizadorSemanticoTypes._inferir_tipo_llamada

def _patched_inferir_llamada(self, nodo):
    if nodo.nombre in ('len', 'subcadena', 'empieza_con', '==', '!='):
        print(f"[DEBUG] LlamadaFuncion '{nodo.nombre}' L{nodo.linea}:{nodo.columna}")
        for i, arg in enumerate(nodo.argumentos):
            tipo = self._inferir_tipo(arg)
            print(f"[DEBUG]   arg[{i}]: tipo={tipo!r}")
    return _original_check(self, nodo)

st.AnalizadorSemanticoTypes._inferir_tipo_llamada = _patched_inferir_llamada

# Run compilation
from pipeline import ejecutar_compilador
sys.exit(ejecutar_compilador('nucleo/principal.syn'))
