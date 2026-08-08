#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Muestra el cuerpo de la funcion principal en el C generado por S2 para el fixture a23."""
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'tests')
import test_a23_parity as t

s2 = t._compilar_s2('stage2')
lines = s2.splitlines()
for i, l in enumerate(lines):
    if 'void principal' in l:
        for j in range(i, min(i + 32, len(lines))):
            print(lines[j])
        break
