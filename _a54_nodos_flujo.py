#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A5.4: inferencia int64_t/double en nodos_flujo.syn (declaracion + asignacion)."""

import io

P = "nucleo/generador/nodos_flujo.syn"
with io.open(P, "r", encoding="utf-8", newline="") as f:
    s = f.read()

# 1. default int -> int64_t (2 sitios: declaracion L150 y asignacion L267)
n1 = s.count('asm("const char* _var_type = \\"int \\";")')
s = s.replace('asm("const char* _var_type = \\"int \\";")',
              'asm("const char* _var_type = \\"int64_t \\";")')
print(f"[OK] default int -> int64_t: {n1}")

# 2. LiteralDecimal float -> double (declaracion)
n2 = s.count('asm("    _var_type = \\"float \\";")')
s = s.replace('asm("    _var_type = \\"float \\";")',
              'asm("    _var_type = \\"double \\";")')
print(f"[OK] float -> double: {n2}")

# 3. Asignacion: anadir caso LiteralDecimal -> double (despues del caso LiteralCadena)
viejo = (
    'asm("if (_a->expresion && _a->expresion->tipo.datos && strcmp(_a->expresion->tipo.datos, \\"LiteralCadena\\") == 0) {")\n'
    '        asm("    _var_type = \\"CadenaSegura \\";")\n'
    '        asm("}")'
)
nuevo = (
    'asm("if (_a->expresion && _a->expresion->tipo.datos && strcmp(_a->expresion->tipo.datos, \\"LiteralCadena\\") == 0) {")\n'
    '        asm("    _var_type = \\"CadenaSegura \\";")\n'
    '        asm("} else if (_a->expresion && _a->expresion->tipo.datos && strcmp(_a->expresion->tipo.datos, \\"LiteralDecimal\\") == 0) {")\n'
    '        asm("    _var_type = \\"double \\";")\n'
    '        asm("}")'
)
n3 = s.count(viejo)
s = s.replace(viejo, nuevo)
print(f"[OK] asignacion LiteralDecimal -> double: {n3}")

with io.open(P, "w", encoding="utf-8", newline="") as f:
    f.write(s)

if n1 != 2 or n2 != 1 or n3 != 1:
    raise SystemExit(1)
