#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_a53_sufijo_ll.py — A5.3: sufijo LL en literales enteros.

Problema: en C, `2147483647 + 1` se evalua en int (int32) -> overflow -> -2147483648
aunque la variable destino sea int64_t. Con sufijo LL el literal es long long y la
aritmetica se hace en 64 bits. Caso especial: la magnitud 9223372036854775808
(INT64_MIN via unario menos) no es literal long long valido -> se emite
(-9223372036854775807LL - 1).
"""

import io

INT64_MAX_P1 = 9223372036854775808

# --- S2/S3: expr_eval.syn ---
P1 = "nucleo/generador/expr_eval.syn"
with io.open(P1, "r", encoding="utf-8", newline="") as f:
    s1 = f.read()
viejo1 = 'asm("    snprintf(_b, _sz, \\"%lld\\", (long long)_ln->valor);")'
nuevo1 = (
    'asm("    if ((long long)_ln->valor == (long long)9223372036854775807LL + 1)'
    ' { strcpy(_b, \\"(-9223372036854775807LL - 1)\\"); }")\n'
    'asm("    else { snprintf(_b, _sz, \\"%lldLL\\", (long long)_ln->valor); }")'
)
n1 = s1.count(viejo1)
s1 = s1.replace(viejo1, nuevo1)
with io.open(P1, "w", encoding="utf-8", newline="") as f:
    f.write(s1)
print(f"[OK] {P1}: LL suffix: {n1}")

# --- S1: emit_expressions.py ---
P2 = "compilador/generator/emit_expressions.py"
with io.open(P2, "r", encoding="utf-8", newline="") as f:
    s2 = f.read()
viejo2 = "    if isinstance(nodo, LiteralNumero):\n        return str(nodo.valor)"
nuevo2 = (
    "    if isinstance(nodo, LiteralNumero):\n"
    "        # A5.3 D-7: sufijo LL para aritmetica int64 en C; INT64_MIN via\n"
    "        # unario menos emite la magnitud como (-9223372036854775807LL - 1)\n"
    "        if nodo.valor == 9223372036854775808:\n"
    "            return '(-9223372036854775807LL - 1)'\n"
    "        return f'{nodo.valor}LL'"
)
n2 = s2.count(viejo2)
s2 = s2.replace(viejo2, nuevo2)
with io.open(P2, "w", encoding="utf-8", newline="") as f:
    f.write(s2)
print(f"[OK] {P2}: LL suffix: {n2}")

# --- verificar ---
if n1 != 1 or n2 != 1:
    print("[AVISO] conteos inesperados")
    raise SystemExit(1)
