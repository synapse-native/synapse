#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_d3_harden.py — Recomendaciones del code-reviewer para el fix D-3:
  1. _hp_stack[1024] -> _hp_stack[4096] (el FIFO consume el array monotonamente:
     total de sentencias por funcion, no profundidad concurrente; 1024 podia
     descartar sentencias silenciosamente en funciones muy grandes).
  2. Documentar la divergencia intencional de orden en bloques anidados
     (FIFO difiere de S1 _collect_vars que recorre DFS inmediato).
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ruta = "nucleo/generador/orquestador.syn"
with open(ruta, encoding="utf-8") as f:
    s = f.read()

cambios = 0

# 1. Tamanio del array + guardas (6 sitios: 1 decl + 1 inicial + 4 push sub-bloques + 1 para)
pares = [
    ('        asm("    struct Nodo* _hp_stack[1024];")',
     '        asm("    struct Nodo* _hp_stack[4096];  // D-3: FIFO consume el array monotonamente (total sentencias/funcion)")'),
    ("_hp_tail < 1024) { _hp_stack[_hp_tail++]",
     "_hp_tail < 4096) { _hp_stack[_hp_tail++]"),
    ("_hp_tail < 1024) { _hp_stack[_hp_tail++]",
     "_hp_tail < 4096) { _hp_stack[_hp_tail++]"),
    ("_hp_tail < 1024) { _hp_stack[_hp_tail++]",
     "_hp_tail < 4096) { _hp_stack[_hp_tail++]"),
    ("_hp_tail < 1024) { _hp_stack[_hp_tail++]",
     "_hp_tail < 4096) { _hp_stack[_hp_tail++]"),
    ("if (_hp_p->cuerpo && _hp_tail < 1024) { _hp_stack[_hp_tail++] = _hp_p->cuerpo; }",
     "if (_hp_p->cuerpo && _hp_tail < 4096) { _hp_stack[_hp_tail++] = _hp_p->cuerpo; }"),
]
for old, new in pares:
    n = s.count(old)
    if n >= 1:
        s = s.replace(old, new)
        cambios += n
        print(f"[OK] {n} ocurrencia(s): {old[:70]}...")
    else:
        print(f"[WARN] no encontrado: {old[:70]}...")

# 2. Comentario de divergencia documentada tras el bloque D-3 (antes del while principal)
old_commento = (
    '        asm("    // D-3: recorrido FIFO (orden de aparicion) — paridad _collect_vars de S1")\n'
    '        asm("    // (for s in stmts): la PRIMERA declaracion gana; una AsignacionVariable")\n'
    '        asm("    // posterior a un `let` del mismo nombre NO se hoistea como auto=1.")'
)
new_commento = (
    '        asm("    // D-3: recorrido FIFO (orden de aparicion) — paridad _collect_vars de S1")\n'
    '        asm("    // (for s in stmts): la PRIMERA declaracion gana; una AsignacionVariable")\n'
    '        asm("    // posterior a un `let` del mismo nombre NO se hoistea como auto=1.")\n'
    '        asm("    // Divergencia documentada: los bloques anidados (si/mientras/para) se")\n'
    '        asm("    // procesan al final de la cola (no en su posicion de documento como S1);")\n'
    '        asm("    // solo afecta a codigo que cruza ambito (declaracion en bloque + asignacion")\n'
    '        asm("    // fuera), que Synapse no permite — aceptada.")'
)
if old_commento in s:
    s = s.replace(old_commento, new_commento, 1)
    cambios += 1
    print("[OK] comentario de divergencia anadido")
else:
    print("[WARN] comentario D-3 no encontrado")

with open(ruta, "w", encoding="utf-8", newline="") as f:
    f.write(s)

print(f"=== _d3_harden.py: {cambios} cambios aplicados ===")
sys.exit(0 if cambios >= 6 else 1)
