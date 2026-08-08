#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A5.5: bindings texto<->numero al ABI int64_t/double."""

import io

# --- synapse_rt.c ---
p = "synapse_rt.c"
with io.open(p, "r", encoding="utf-8", newline="") as f:
    s = f.read()
pares = [
    ("int texto_a_entero(CadenaSegura str) {",
     "int64_t texto_a_entero(CadenaSegura str) {"),
    ("    if (str.datos == NULL || str.longitud == 0) return 0;",
     "    if (str.datos == NULL || str.longitud == 0) return 0;"),
    ("    return (int)strtol(str.datos, NULL, 10);",
     "    return (int64_t)strtoll(str.datos, NULL, 10);"),
    ("float texto_a_decimal(CadenaSegura str) {",
     "double texto_a_decimal(CadenaSegura str) {"),
    ("    if (str.datos == NULL || str.longitud == 0) return 0.0f;",
     "    if (str.datos == NULL || str.longitud == 0) return 0.0;"),
    ("    return (float)strtod(str.datos, NULL);",
     "    return strtod(str.datos, NULL);"),
]
for v, n in pares:
    c = s.count(v)
    s = s.replace(v, n)
    print(f"[{'OK' if c == 1 else 'AVISO:'+str(c)}] rt.c: {v[:48]}...")
with io.open(p, "w", encoding="utf-8", newline="") as f:
    f.write(s)

# --- synapse_rt.h ---
p = "synapse_rt.h"
with io.open(p, "r", encoding="utf-8", newline="") as f:
    s = f.read()
pares = [
    ("int texto_a_entero(CadenaSegura str);",
     "int64_t texto_a_entero(CadenaSegura str);"),
    ("float texto_a_decimal(CadenaSegura str);",
     "double texto_a_decimal(CadenaSegura str);"),
]
for v, n in pares:
    c = s.count(v)
    s = s.replace(v, n)
    print(f"[{'OK' if c == 1 else 'AVISO:'+str(c)}] rt.h: {v[:40]}...")
with io.open(p, "w", encoding="utf-8", newline="") as f:
    f.write(s)

# --- generator.py (externs S1) ---
p = "compilador/generator/generator.py"
with io.open(p, "r", encoding="utf-8", newline="") as f:
    s = f.read()
pares = [
    ('"int texto_a_entero(CadenaSegura str)"',
     '"int64_t texto_a_entero(CadenaSegura str)"'),
    ('"float texto_a_decimal(CadenaSegura str)"',
     '"double texto_a_decimal(CadenaSegura str)"'),
]
for v, n in pares:
    c = s.count(v)
    s = s.replace(v, n)
    print(f"[{'OK' if c == 1 else 'AVISO:'+str(c)}] generator.py: {v[:44]}...")
with io.open(p, "w", encoding="utf-8", newline="") as f:
    f.write(s)

# --- orquestador.syn (externs S2/S3) ---
p = "nucleo/generador/orquestador.syn"
with io.open(p, "r", encoding="utf-8", newline="") as f:
    s = f.read()
pares = [
    ('gen_emitir_linea(est, "extern int texto_a_entero(CadenaSegura str);")',
     'gen_emitir_linea(est, "extern int64_t texto_a_entero(CadenaSegura str);")'),
    ('gen_emitir_linea(est, "extern float texto_a_decimal(CadenaSegura str);")',
     'gen_emitir_linea(est, "extern double texto_a_decimal(CadenaSegura str);")'),
]
for v, n in pares:
    c = s.count(v)
    s = s.replace(v, n)
    print(f"[{'OK' if c == 1 else 'AVISO:'+str(c)}] orquestador.syn: {v[:52]}...")
with io.open(p, "w", encoding="utf-8", newline="") as f:
    f.write(s)
