#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_d3_fix.py — Cierra la deuda D-3 (divergencia cosmética S1 vs S2 en la declaración
de variables de struct/Tensor sin inicializador).

Bug (S2, orquestador.syn): para `let t: Tensor` + `t = crear_tensor(...)` el pre-pass
de hoisting (ME-B7) procesa el cuerpo en orden INVERSO (pila LIFO: `--_hp_top`), así
que la AsignacionVariable `t = ...` se registra como auto=1 ANTES que la
DeclaracionVariable `t` (auto=0) -> el hoisting emite `int64_t t = {0};` (tipo por
defecto) Y `gen_visitar_declaracion` emite `Tensor t = ;` (sin {0}) -> C invalido
(doble declaracion + sintaxis).

Fix:
  1. Pre-pass -> recorrido FIFO (orden de aparicion), paridad _collect_vars de S1
     (`for s in stmts`): la primera declaracion gana.
  2. gen_visitar_declaracion sin expresion -> `= {0};` (paridad visitar_declaracion S1).

Fuentes a editar:
  - nucleo/generador/orquestador.syn   (pre-pass de hoisting)
  - nucleo/generador/nodos_flujo.syn   (gen_visitar_declaracion)
Luego _rebuild_generator.py regenera nucleo/generator.syn (dualidad sincronizada A4).
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def aplicar(ruta, reemplazos, nombre):
    with open(ruta, encoding="utf-8") as f:
        s = f.read()
    ok = 0
    for old, new, esperado in reemplazos:
        n = s.count(old)
        if n == esperado:
            s = s.replace(old, new)
            ok += 1
            print(f"[OK] {nombre}: {n} ocurrencia(s) reemplazada(s)")
        else:
            print(f"[WARN] {nombre}: esperaba {esperado}, encontre {n} — NO aplicado: {old[:90]}...")
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        f.write(s)
    return ok


# ---------------------------------------------------------------- orquestador.syn
reemplazos_orq = []

# 1. Zona de apertura del pre-pass (incluye mi edicion a medias previa): FIFO.
old_zona = (
    '        asm("    // Registra TODAS las variables auto-declaradas del cuerpo (recursivo en si/mientras/inseguro/para).")\n'
    '        asm("    struct Nodo* _hp_stack[1024];")\n'
    '        asm("    int _hp_top = 0;")\n'
    '        asm("    struct ListaNodo* _hp0 = _f->cuerpo;")\n'
    '        asm("    while (_hp0) { if (_hp0->cabeza && _hp_top < 1024) { _hp_stack[_hp_top++] = _hp0->cabeza; } _hp0 = _hp0->cola; }")\n'
    '        asm("    // D-3: paridad _collect_vars S1 — primera declaracion gana en ORDEN de aparicion.")\n'
    '        asm("    // Pre-pasada: registrar TODAS las DeclaracionVariable (auto=0) ANTES de las")\n'
    '        asm("    // AsignacionVariable (auto=1), para que una asignacion posterior a un `let`")\n'
    '        asm("    // no se hoistee como auto-declarada (S1: _explicit_vars).")\n'
    '        asm("    int _hp_exp_count = _G_fn_vars_count;")\n'
    '        asm("    while (_hp_top > 0) {")\n'
    '        asm("        struct Nodo* _hp_n = _hp_stack[_hp_top - 1];")'
)
new_zona = (
    '        asm("    // Registra TODAS las variables auto-declaradas del cuerpo (recursivo en si/mientras/inseguro/para).")\n'
    '        asm("    // D-3: recorrido FIFO (orden de aparicion) — paridad _collect_vars de S1")\n'
    '        asm("    // (for s in stmts): la PRIMERA declaracion gana; una AsignacionVariable")\n'
    '        asm("    // posterior a un `let` del mismo nombre NO se hoistea como auto=1.")\n'
    '        asm("    struct Nodo* _hp_stack[1024];")\n'
    '        asm("    int _hp_head = 0, _hp_tail = 0;")\n'
    '        asm("    struct ListaNodo* _hp0 = _f->cuerpo;")\n'
    '        asm("    while (_hp0) { if (_hp0->cabeza && _hp_tail < 1024) { _hp_stack[_hp_tail++] = _hp0->cabeza; } _hp0 = _hp0->cola; }")\n'
    '        asm("    while (_hp_head < _hp_tail) {")\n'
    '        asm("        struct Nodo* _hp_n = _hp_stack[_hp_head++];")'
)
reemplazos_orq.append((old_zona, new_zona, 1))

# 2. Push de sub-bloques: _hp_top++ -> _hp_tail++ (5 sitios: si cuerpo, si sino,
#    mientras, inseguro, para).
for pat in [
    ("_hp_sl->cabeza && _hp_top < 1024) { _hp_stack[_hp_top++] = _hp_sl->cabeza; }",
     "_hp_sl->cabeza && _hp_tail < 1024) { _hp_stack[_hp_tail++] = _hp_sl->cabeza; }"),
    ("_hp_el->cabeza && _hp_top < 1024) { _hp_stack[_hp_top++] = _hp_el->cabeza; }",
     "_hp_el->cabeza && _hp_tail < 1024) { _hp_stack[_hp_tail++] = _hp_el->cabeza; }"),
    ("_hp_ml->cabeza && _hp_top < 1024) { _hp_stack[_hp_top++] = _hp_ml->cabeza; }",
     "_hp_ml->cabeza && _hp_tail < 1024) { _hp_stack[_hp_tail++] = _hp_ml->cabeza; }"),
    ("_hp_bl->cabeza && _hp_top < 1024) { _hp_stack[_hp_top++] = _hp_bl->cabeza; }",
     "_hp_bl->cabeza && _hp_tail < 1024) { _hp_stack[_hp_tail++] = _hp_bl->cabeza; }"),
    ("if (_hp_p->cuerpo && _hp_top < 1024) { _hp_stack[_hp_top++] = _hp_p->cuerpo; }",
     "if (_hp_p->cuerpo && _hp_tail < 1024) { _hp_stack[_hp_tail++] = _hp_p->cuerpo; }"),
]:
    reemplazos_orq.append((pat[0], pat[1], 1))

ok1 = aplicar("nucleo/generador/orquestador.syn", reemplazos_orq, "orquestador.syn")

# Verificacion: no debe quedar _hp_top como indice de pila (salvo head/tail nuevos)
with open("nucleo/generador/orquestador.syn", encoding="utf-8") as f:
    s = f.read()
if "_hp_top" in s:
    # solo puede quedar en comentarios; listar
    for i, ln in enumerate(s.splitlines(), 1):
        if "_hp_top" in ln and "asm(" in ln:
            print(f"[CHECK] orquestador.syn:{i} aun tiene _hp_top: {ln.strip()[:100]}")

# ---------------------------------------------------------------- nodos_flujo.syn
reemplazos_nf = [
    (
        '        asm("_buf2[0] = 0;")\n'
        '        asm("if (_dv->expresion) { _oo_expr_a_c(est, _dv->expresion, _buf2, 4096); }")\n'
        '        asm("strcat(_buf, _buf2);")',
        '        asm("_buf2[0] = 0;")\n'
        '        asm("// D-3: sin expresion -> `= {0};` (paridad visitar_declaracion S1: `{tipo} {nombre} = {0};`)")\n'
        '        asm("if (_dv->expresion) { _oo_expr_a_c(est, _dv->expresion, _buf2, 4096); } else { strcpy(_buf2, \\"{0}\\"); }")\n'
        '        asm("strcat(_buf, _buf2);")',
        1,
    ),
]
ok2 = aplicar("nucleo/generador/nodos_flujo.syn", reemplazos_nf, "nodos_flujo.syn")

print(f"\n=== _d3_fix.py: orquestador={ok1}/{len(reemplazos_orq)} aplicados, nodos_flujo={ok2}/{len(reemplazos_nf)} ===")
sys.exit(0 if (ok1 == len(reemplazos_orq) and ok2 == len(reemplazos_nf)) else 1)
