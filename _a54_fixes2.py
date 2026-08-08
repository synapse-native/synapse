#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_a54_fixes2.py — A5.4:
  1) ADT tagged union: `int tag;` -> `int64_t tag;` en S1 (emit_declarations.py)
     y self-hosted (orquestador.syn -> generator.syn).
  2) Aserciones de tests afectadas por el sufijo LL (A5.3).
"""

import io


def remplazar(ruta, pares, crlf=False):
    with io.open(ruta, "r", encoding="utf-8", newline="") as f:
        s = f.read()
    for viejo, nuevo in pares:
        n = s.count(viejo)
        s = s.replace(viejo, nuevo)
        print(f"[{'OK' if n == 1 else 'AVISO:'+str(n)}] {ruta}: {viejo[:55]}...")
    with io.open(ruta, "w", encoding="utf-8", newline="") as f:
        f.write(s)


# 1. ADT int tag -> int64_t tag (S1)
remplazar("compilador/generator/emit_declarations.py", [
    ('      `typedef struct X { int tag; union {...} dato; } X;` compatible con',
     '      `typedef struct X { int64_t tag; union {...} dato; } X;` compatible con'),
    ('        td = (f"typedef struct {nodo.nombre} {{ int tag; "',
     '        td = (f"typedef struct {nodo.nombre} {{ int64_t tag; "'),
])

# 2. ADT int tag -> int64_t tag (self-hosted)
remplazar("nucleo/generador/orquestador.syn", [
    ('        asm("    // -> tagged union `typedef struct X { int tag; union {...} dato; } X;`")',
     '        asm("    // -> tagged union `typedef struct X { int64_t tag; union {...} dato; } X;`")'),
    ('        asm("            snprintf(_dth, 4096, \\"typedef struct %s { int tag; union {\\", _dtx->nombre.datos);")',
     '        asm("            snprintf(_dth, 4096, \\"typedef struct %s { int64_t tag; union {\\", _dtx->nombre.datos);")'),
])

# 3. Aserciones LL
remplazar("tests/test_codegen_embebido_d_f1.py", [
    ('    assert "crear_tensor(2, 3)" in codigo, "ExprTensor -> crear_tensor(2, 3)"',
     '    assert "crear_tensor(2LL, 3LL)" in codigo, "ExprTensor -> crear_tensor(2LL, 3LL)"'),
])
remplazar("tests/test_codegen_embebido_d_f1c.py", [
    ('    assert "int64_t x = 5;" in codigo, "let x = 5 -> int64_t x = 5;"',
     '    assert "int64_t x = 5LL;" in codigo, "let x = 5 -> int64_t x = 5LL;"'),
    ('    assert "int64_t edad = 10;" in codigo, "let edad: entero = 10 -> int64_t edad = 10;"',
     '    assert "int64_t edad = 10LL;" in codigo, "let edad: entero = 10 -> int64_t edad = 10LL;"'),
])
remplazar("tests/test_codegen_embebido_d_f1d.py", [
    ('        assert "void* nodo = crear_nodo(1);" in codigo, (',
     '        assert "void* nodo = crear_nodo(1LL);" in codigo, ('),
])
remplazar("tests/test_codegen_embebido_d_f1_4.py", [
    ('        assert "int64_t rc = 0;" in codigo or "rc = 0;" in codigo, (',
     '        assert "int64_t rc = 0LL;" in codigo or "rc = 0LL;" in codigo, ('),
])
remplazar("tests/test_a23_parity.py", [
    ('    assert "Tensor t = crear_tensor(2, 3);" in c',
     '    assert "Tensor t = crear_tensor(2LL, 3LL);" in c'),
    ('    assert "int x = 5;" in s1 and "int x = 5;" in s2',
     '    assert "int64_t x = 5LL;" in s1 and "int64_t x = 5LL;" in s2'),
])

print("[OK] A5.4 fixes aplicados")
