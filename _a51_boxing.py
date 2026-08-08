#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A5.1 (D-7): migra los 4 helpers de boxing de S1 a int64_t/double.

generator.py usa CRLF. Leemos con newline='' (preserva los saltos) y
reemplazamos construyendo las cadenas con el salto real del archivo.
"""
import io

RUTA = "compilador/generator/generator.py"

with io.open(RUTA, "r", encoding="utf-8", newline="") as f:
    src = f.read()

NL = "\r\n" if "\r\n" in src else "\n"

def jun(*partes):
    return NL.join(partes)

# --- Reemplazo 1: _synapse_box_int / _synapse_unbox_int (int -> int64_t) ---
viejo_int = jun(
    '        ctx.write_line("static inline void* _synapse_box_int(int v) "',
    '            "{ return (void*)(intptr_t)v; }"',
    "        )",
    "        ctx.write_line(",
    '            "static inline int _synapse_unbox_int(void* p) "',
    '            "{ return (int)(intptr_t)p; }"',
    "        )",
)
nuevo_int = jun(
    '        ctx.write_line("static inline void* _synapse_box_int(int64_t v) "',
    '            "{ return (void*)(intptr_t)v; }"',
    "        )",
    "        ctx.write_line(",
    '            "static inline int64_t _synapse_unbox_int(void* p) "',
    '            "{ return (int64_t)(intptr_t)p; }"',
    "        )",
)
assert viejo_int in src, "no se encontro el bloque box/unbox int"
src = src.replace(viejo_int, nuevo_int)

# --- Reemplazo 2: _synapse_box_float / _synapse_unbox_float (float -> double) ---
viejo_flt = jun(
    '        ctx.write_line(',
    '            "static inline void* _synapse_box_float(float v) {"',
    "        )",
    "        ctx.inc_indent()",
    '        ctx.write_line("float* _p = (float*)malloc(sizeof(float));")',
    "        ctx.write_line(",
    "            'if (!_p) { fprintf(stderr, '",
    "            '\"ESCAPA_DEL_ALCANCE: malloc fallo\\\\\\\\n\"); exit(1); }'",
    "        )",
    '        ctx.write_line("*_p = v;")',
    '        ctx.write_line("return (void*)_p;")',
    "        ctx.dec_indent()",
    '        ctx.write_line("}")',
    "        ctx.write_line(",
    '            "static inline float _synapse_unbox_float(void* p) {"',
    "        )",
    "        ctx.inc_indent()",
    '        ctx.write_line("float _v = *(float*)p;")',
    '        ctx.write_line("free(p);")',
    '        ctx.write_line("return _v;")',
    "        ctx.dec_indent()",
    '        ctx.write_line("}")',
)
nuevo_flt = jun(
    '        ctx.write_line(',
    '            "static inline void* _synapse_box_float(double v) {"',
    "        )",
    "        ctx.inc_indent()",
    '        ctx.write_line("double* _p = (double*)malloc(sizeof(double));")',
    "        ctx.write_line(",
    "            'if (!_p) { fprintf(stderr, '",
    "            '\"ESCAPA_DEL_ALCANCE: malloc fallo\\\\\\\\n\"); exit(1); }'",
    "        )",
    '        ctx.write_line("*_p = v;")',
    '        ctx.write_line("return (void*)_p;")',
    "        ctx.dec_indent()",
    '        ctx.write_line("}")',
    "        ctx.write_line(",
    '            "static inline double _synapse_unbox_float(void* p) {"',
    "        )",
    "        ctx.inc_indent()",
    '        ctx.write_line("double _v = *(double*)p;")',
    '        ctx.write_line("free(p);")',
    '        ctx.write_line("return _v;")',
    "        ctx.dec_indent()",
    '        ctx.write_line("}")',
)
assert viejo_flt in src, "no se encontro el bloque box/unbox float"
src = src.replace(viejo_flt, nuevo_flt)

with io.open(RUTA, "w", encoding="utf-8", newline="") as f:
    f.write(src)

print("[OK] boxing S1 migrado: _synapse_box_int(int64_t), _synapse_unbox_int(int64_t), "
      "_synapse_box_float(double), _synapse_unbox_float(double)")
