#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_a53_inferencia.py — A5.3: inferencia de tipo de variables auto-declaradas.

orquestador.syn hardcodeaba "int" (int32) para el tipo C de una variable
creada implicitamente por `x = <expr>`. Con ABI int64_t/double (D-7):
  - OpBinaria no-cadena: si algun operando es LiteralDecimal -> double, sino int64_t
    (paridad tipo_de_expr: decimal gana; el resto hereda el tipo del izquierdo).
  - LlamadaFuncion con retorno desconocido: int64_t.
  - Expresion final (LiteralNumero/Identificador/...): LiteralDecimal -> double,
    resto int64_t.
"""

import io

P = "nucleo/generador/orquestador.syn"


def main() -> int:
    with io.open(P, "r", encoding="utf-8", newline="") as f:
        s = f.read()
    ok = True

    # 1. OpBinaria: else -> int64_t/double (paridad tipo_de_expr)
    viejo_ob = (
        '        asm("                    strcpy(_hvt, \\"CadenaSegura\\");")\n'
        '        asm("                } else { strcpy(_hvt, \\"int\\"); }")'
    )
    nuevo_ob = (
        '        asm("                    strcpy(_hvt, \\"CadenaSegura\\");")\n'
        '        asm("                } else { int _hdec = 0;'
        ' if (_hob && _hob->izquierdo && _hob->izquierdo->tipo.datos'
        ' && strcmp(_hob->izquierdo->tipo.datos, \\"LiteralDecimal\\") == 0) _hdec = 1;'
        ' if (_hob && _hob->derecho && _hob->derecho->tipo.datos'
        ' && strcmp(_hob->derecho->tipo.datos, \\"LiteralDecimal\\") == 0) _hdec = 1;'
        ' if (_hdec) { strcpy(_hvt, \\"double\\"); } else { strcpy(_hvt, \\"int64_t\\"); } }")'
    )
    n1 = s.count(viejo_ob)
    s = s.replace(viejo_ob, nuevo_ob)
    print(f"[OK] OpBinaria else -> int64_t/double: {n1}")
    if n1 != 1:
        ok = False

    # 2. Final: LiteralDecimal -> double, LiteralNumero -> int64_t, resto -> int64_t
    viejo_fin = (
        '        asm("                strcpy(_hvt, \\"Tensor\\");")\n'
        '        asm("            } else { strcpy(_hvt, \\"int\\"); }")'
    )
    nuevo_fin = (
        '        asm("                strcpy(_hvt, \\"Tensor\\");")\n'
        '        asm("            } else if (strcmp(_het, \\"LiteralDecimal\\") == 0) { strcpy(_hvt, \\"double\\"); }")\n'
        '        asm("            } else if (strcmp(_het, \\"LiteralNumero\\") == 0) { strcpy(_hvt, \\"int64_t\\"); }")\n'
        '        asm("            } else { strcpy(_hvt, \\"int64_t\\"); }")'
    )
    n2 = s.count(viejo_fin)
    s = s.replace(viejo_fin, nuevo_fin)
    print(f"[OK] final -> LiteralDecimal double / LiteralNumero int64_t: {n2}")
    if n2 != 1:
        ok = False

    # 3. Resto de `} else { strcpy(_hvt, "int"); }` (LlamadaFuncion, sin expr) -> int64_t
    n3 = s.count('} else { strcpy(_hvt, \\"int\\"); }')
    s = s.replace('} else { strcpy(_hvt, \\"int\\"); }',
                  '} else { strcpy(_hvt, \\"int64_t\\"); }')
    print(f"[OK] resto else int -> int64_t: {n3}")
    if n3 != 2:  # LlamadaFuncion sin retorno + sin expresion
        ok = False

    # 4. Safety nets `if (_hvt[0] == 0) { strcpy(_hvt, "int"); }` -> int64_t
    n4 = s.count('if (_hvt[0] == 0) { strcpy(_hvt, \\"int\\"); }')
    s = s.replace('if (_hvt[0] == 0) { strcpy(_hvt, \\"int\\"); }',
                  'if (_hvt[0] == 0) { strcpy(_hvt, \\"int64_t\\"); }')
    print(f"[OK] safety nets -> int64_t: {n4}")
    if n4 != 2:
        ok = False

    # Verificar que no queden "int" residuales de _hvt
    resto = s.count('strcpy(_hvt, \\"int\\")')
    print(f"[INFO] strcpy(_hvt, \"int\") restantes: {resto}")

    with io.open(P, "w", encoding="utf-8", newline="") as f:
        f.write(s)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
