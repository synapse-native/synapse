#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_a54_aserciones.py — A5.4: actualiza las aserciones de los tests de codegen
embebido f1/f1c/f1d/f1_4 al ABI int64_t/double (D-7).
"""

import io

CAMBIOS = [
    ("tests/test_codegen_embebido_d_f1.py", [
        ('assert "typedef int Edad;" in codigo, "alias -> typedef int Edad;"',
         'assert "typedef int64_t Edad;" in codigo, "alias -> typedef int64_t Edad;"'),
        ('assert "typedef struct Resultado { int tag; union {" in codigo, "ADT -> tagged union"',
         'assert "typedef struct Resultado { int64_t tag; union {" in codigo, "ADT -> tagged union"'),
    ]),
    ("tests/test_codegen_embebido_d_f1c.py", [
        ('assert "int x = 5;" in codigo, "let x = 5 -> int x = 5;"',
         'assert "int64_t x = 5;" in codigo, "let x = 5 -> int64_t x = 5;"'),
        ('assert "int edad = 10;" in codigo, "let edad: entero = 10 -> int edad = 10;"',
         'assert "int64_t edad = 10;" in codigo, "let edad: entero = 10 -> int64_t edad = 10;"'),
        ('assert "float suma = 2.5f;" in codigo, "let suma = 2.5 -> float suma = 2.5f;"',
         'assert "double suma = 2.5;" in codigo, "let suma = 2.5 -> double suma = 2.5;"'),
    ]),
    ("tests/test_codegen_embebido_d_f1d.py", [
        ('assert "int sumar(int a, int b) {" in codigo, (\n        "@export ( python ) funcion sumar -> int sumar(int a, int b) {")',
         'assert "int64_t sumar(int64_t a, int64_t b) {" in codigo, (\n        "@export ( python ) funcion sumar -> int64_t sumar(int64_t a, int64_t b) {")'),
        ('assert "void* crear_nodo(int v) {" in codigo, (\n            "retorno arc<NodoLista> -> void* crear_nodo(int v) {")',
         'assert "void* crear_nodo(int64_t v) {" in codigo, (\n            "retorno arc<NodoLista> -> void* crear_nodo(int64_t v) {")'),
        ('assert "int sumar(int a, int b);" in codigo, (\n            "prototipo de la funcion exportada llamada antes de su definicion")',
         'assert "int64_t sumar(int64_t a, int64_t b);" in codigo, (\n            "prototipo de la funcion exportada llamada antes de su definicion")'),
    ]),
    ("tests/test_codegen_embebido_d_f1_4.py", [
        ('assert "int sumar_rc(int rc, int modulo) {" in codigo, (\n            "parametros rc/modulo preservados en la firma C")',
         'assert "int64_t sumar_rc(int64_t rc, int64_t modulo) {" in codigo, (\n            "parametros rc/modulo preservados en la firma C")'),
        ('assert "int rc = 0;" in codigo or "rc = 0;" in codigo, (',
         'assert "int64_t rc = 0;" in codigo or "rc = 0;" in codigo, ('),
    ]),
]

for ruta, pares in CAMBIOS:
    with io.open(ruta, "r", encoding="utf-8", newline="") as f:
        s = f.read()
    for viejo, nuevo in pares:
        n = s.count(viejo)
        s = s.replace(viejo, nuevo)
        print(f"[{'OK' if n == 1 else 'AVISO'} {ruta}] {n} -> {viejo[:60]}...")
    with io.open(ruta, "w", encoding="utf-8", newline="") as f:
        f.write(s)

print("[OK] A5.4 aserciones actualizadas")
