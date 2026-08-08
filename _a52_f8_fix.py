#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_a52_f8_fix.py — Fix del segfault S2 tras A5.2 (ABI int64_t/double).

El struct SemNodo paso de 11xint (44 B) a int64_t/double (88 B). El flatten F8
(principal.syn) usaba indices int de 4 bytes:
  - [10] (antes ptr_extra, offset 40) ahora cae en los bytes BAJOS de ptr_str
    (offset 40) -> corrompe la mitad baja del puntero -> strdup segfault.
    Los high bits ya viven en _f8_ptr_hi (lo que leen todos los readers via
    _phi / parser_ptr_hi). El write [10] es redundancia muerta: se elimina.
  - [6] (antes len_str, offset 24) ahora cae en valor_int (offset 24). El unico
    nodo que escribe valor_int Y [6] es ExprObtenerDireccion (es_mutable + hijo
    expr). Se mueve el hijo a .hijo_izq (campo libre para este nodo) y el
    reader NODO_PUNTERO lee nodo_hijo_izq. Ademas alinea flatten<->puente
    (puente ya lee hi=hijo_izq para ExprObtenerDireccion).
"""

import io

PRINCIPAL = "nucleo/principal.syn"
ANALIZADOR = "nucleo/analizador_semantico.syn"


def main() -> int:
    # ---- 1. principal.syn: eliminar writes [10] ----
    with io.open(PRINCIPAL, "r", encoding="utf-8", newline="") as f:
        p = f.read()
    n10 = p.count("; ((int*)&_f8_nodos[idx])[10]=(int)(_tp>>32)")
    p = p.replace("; ((int*)&_f8_nodos[idx])[10]=(int)(_tp>>32)", "")
    # ---- 2. principal.syn: ExprObtenerDireccion hijo a .hijo_izq ----
    viejo = 'asm("        if(_eod->expr){ int _ci=_f8_flatten(_eod->expr); ((int*)&_f8_nodos[idx])[6]=_ci; }")'
    nuevo = 'asm("        if(_eod->expr){ int _ci=_f8_flatten(_eod->expr); _f8_nodos[idx].hijo_izq=_ci; }")'
    n6 = p.count(viejo)
    p = p.replace(viejo, nuevo)
    with io.open(PRINCIPAL, "w", encoding="utf-8", newline="") as f:
        f.write(p)

    # ---- 3. analizador_semantico.syn: NODO_PUNTERO lee nodo_hijo_izq ----
    with io.open(ANALIZADOR, "r", encoding="utf-8", newline="") as f:
        a = f.read()
    viejo_h = "        hijo = nodo_expr(est, idx)"
    nuevo_h = "        hijo = nodo_hijo_izq(est, idx)"
    nh = a.count(viejo_h)
    a = a.replace(viejo_h, nuevo_h)
    with io.open(ANALIZADOR, "w", encoding="utf-8", newline="") as f:
        f.write(a)

    print(f"[OK] principal.syn: [10] removidos={n10}, ExprObtenerDireccion hijo_izq={n6}")
    print(f"[OK] analizador_semantico.syn: NODO_PUNTERO nodo_hijo_izq={nh}")
    if n10 != 10:
        print(f"[AVISO] esperaba 10 writes [10], encontre {n10}")
    if n6 != 1:
        print(f"[AVISO] esperaba 1 ExprObtenerDireccion, encontre {n6}")
    if nh != 1:
        print(f"[AVISO] esperaba 1 NODO_PUNTERO, encontre {nh}")
    return 0 if (n10 == 10 and n6 == 1 and nh == 1) else 1


if __name__ == "__main__":
    raise SystemExit(main())
