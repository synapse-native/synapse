#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_a53_literales.py — A5.3: literales 64-bit y decimal double.

Causa raiz de la truncacion (rango64d: 2147483648 -> -2147483648):
  - nucleo/puente_ast.syn: NODO_NUMERO se convierte con atoi() (int32) y
    NODO_DECIMAL con (float)atof (float). Con ABI int64_t/double deben ser
    atoll() y atof() (double).
  - nucleo/generador/expr_eval.syn: emision LiteralNumero con %d (int32) ->
    %lld + cast; LiteralDecimal anade sufijo 'f' (float) -> sufijo '.0' solo
    si falta punto/exponente (literal double C).
  - compilador/generator/emit_expressions.py (S1): LiteralDecimal emite
    f"{valor}f" -> forma double (paridad A5.3).
"""

import io


def main() -> int:
    ok = True

    # ---- 1. puente_ast.syn ----
    p = "nucleo/puente_ast.syn"
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        s = f.read()
    r1 = s.replace(
        '_p->valor = atoi((const char*)puente_str(idx));',
        '_p->valor = atoll((const char*)puente_str(idx));')
    r2 = r1.replace(
        '_p->valor = (float)atof((const char*)puente_str(idx));',
        '_p->valor = atof((const char*)puente_str(idx));')
    n1 = s.count('_p->valor = atoi((const char*)puente_str(idx));')
    n2 = s.count('_p->valor = (float)atof((const char*)puente_str(idx));')
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(r2)
    print(f"[OK] {p}: atoi->atoll={n1}, (float)atof->atof={n2}")
    if n1 != 1 or n2 != 1:
        ok = False

    # ---- 2. expr_eval.syn (generador S2/S3) ----
    p2 = "nucleo/generador/expr_eval.syn"
    with io.open(p2, "r", encoding="utf-8", newline="") as f:
        s2 = f.read()
    v1 = s2.count('asm("    snprintf(_b, _sz, \\"%d\\", _ln->valor);")')
    s2 = s2.replace(
        'asm("    snprintf(_b, _sz, \\"%d\\", _ln->valor);")',
        'asm("    snprintf(_b, _sz, \\"%lld\\", (long long)_ln->valor);")')
    v2 = s2.count(
        'asm("    if (!strchr(_b, \'.\') && !strchr(_b, \'e\') && !strchr(_b, \'E\')) strcat(_b, \\".f\\");")')
    s2 = s2.replace(
        'asm("    if (!strchr(_b, \'.\') && !strchr(_b, \'e\') && !strchr(_b, \'E\')) strcat(_b, \\".f\\");")',
        'asm("    if (!strchr(_b, \'.\') && !strchr(_b, \'e\') && !strchr(_b, \'E\')) strcat(_b, \\".0\\");")')
    v3 = s2.count('asm("    else strcat(_b, \\"f\\");")')
    s2 = s2.replace(
        'asm("    else strcat(_b, \\"f\\");")',
        'asm("    else { }")')
    with io.open(p2, "w", encoding="utf-8", newline="") as f:
        f.write(s2)
    print(f"[OK] {p2}: %d->%lld={v1}, '.f'->'.0'={v2}, 'f'->removido={v3}")
    if v1 != 1 or v2 != 1 or v3 != 1:
        ok = False

    # ---- 3. emit_expressions.py (S1, paridad) ----
    p3 = "compilador/generator/emit_expressions.py"
    with io.open(p3, "r", encoding="utf-8", newline="") as f:
        s3 = f.read()
    v4 = s3.count('        return f"{nodo.valor}f"')
    s3 = s3.replace(
        '        return f"{nodo.valor}f"',
        '        # A5.3: decimal -> double (sin sufijo f); agregar .0 si falta\n'
        '        v = str(nodo.valor)\n'
        '        if "." not in v and "e" not in v and "E" not in v:\n'
        '            v += ".0"\n'
        '        return v')
    with io.open(p3, "w", encoding="utf-8", newline="") as f:
        f.write(s3)
    print(f"[OK] {p3}: decimal f->double={v4}")
    if v4 != 1:
        ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
