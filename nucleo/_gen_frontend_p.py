#!/usr/bin/env python3
"""
_gen_frontend_p.py — Regenera nucleo/generador/frontend_p.syn (paridad S1/S2/S3).

El front-end canonico _P_* del compilador auto-hospedado (S2/S3) se emite desde
los emisores Python de Stage1 (S1). Cada linea C se espeja en el bloque Synapse
`_G_fpN[]` / `_G_tkN[]` dentro de frontend_p.syn, que luego _rebuild_generator.py
ensambla en nucleo/generator.syn.

  - gen_emitir_frontend_p <- emitir_parsear   (compilador/generator/emit_selfhost.py)
  - gen_emitir_tokenizar  <- emitir_tokenizar (compilador/generator/emit_expressions.py)

El contenido se almacena con DOBLE escapado (escapado C del literal `_G_XXN[] = "..."`
mas escapado de la cadena Synapse dentro del bloque asm("...")). Por lo tanto, la
decodificacion correcta de una linea del bloque requiere dos pasadas de unescape.

USO:
    python nucleo/_gen_frontend_p.py           # regenera frontend_p.syn
    python nucleo/_rebuild_generator.py        # reensambla nucleo/generator.syn
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from compilador.ast_nodes import Programa
from compilador.generator.context import GeneratorContext
from compilador.generator.emit_selfhost import emitir_parsear
from compilador.generator.emit_expressions import emitir_tokenizar

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "generador", "frontend_p.syn")

HEADER = (
    "// ==========================================================\n"
    "// frontend_p.syn — Front-end canonico _P_* embebido\n"
    "// GENERADO AUTOMATICAMENTE por nucleo/_gen_frontend_p.py\n"
    "// NO editar a mano. Re-generar tras cambios en\n"
    "// compilador/generator/emit_selfhost.py / emit_expressions.py\n"
    "// (y recompilar Stage1 para refrescar _parser.c / _lexer.c).\n"
    "// =========================================================="
)

FP_HEADER = (
    "// ----------------------------------------------------------\n"
    "// gen_emitir_frontend_p — emite el front-end _P_* canonico +\n"
    "// wrapper 'struct Programa parsear(CadenaSegura fuente)'.\n"
    "// Paridad: emitir_parsear (compilador/generator/emit_selfhost.py).\n"
    "// Se emite UNA sola vez (flag static).\n"
    "// ----------------------------------------------------------"
)

TK_HEADER = (
    "// ----------------------------------------------------------\n"
    "// gen_emitir_tokenizar — funcion tokenizar canonica (contador).\n"
    "// Paridad: emitir_tokenizar (compilador/generator/emit_expressions.py).\n"
    "// ----------------------------------------------------------"
)


def _escapar(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _doblemente_escapar(s: str) -> str:
    return _escapar(_escapar(s))


def _quitar_blancas_finales(lineas):
    lineas = list(lineas)
    while lineas and lineas[-1] == "":
        lineas.pop()
    return lineas


def _cuerpo_asm(prefijo: str, lineas_c):
    """Convierte cada linea C en el par asm('static char _G_XXN[] = ...') / gen_emitir_str."""
    salida = []
    for i, ln in enumerate(lineas_c):
        esc = _doblemente_escapar(ln)
        salida.append('        asm("static char {p}{i}[] = \\"{e}\\";")'.format(p=prefijo, i=i, e=esc))
        salida.append('        asm("gen_emitir_str(est, {p}{i});")'.format(p=prefijo, i=i))
    return salida


def _generar_frontend_p() -> str:
    # Paridad S1: el parser _P_* embebido (emitir_parsear).
    ctx = GeneratorContext(Programa(sentencias=[], is_no_std=False))
    emitir_parsear(ctx, None)
    lineas_fp = _quitar_blancas_finales(ctx.lineas)

    # Paridad S1: el contador tokenizar canonico (emitir_tokenizar).
    ctx2 = GeneratorContext(Programa(sentencias=[], is_no_std=False))
    emitir_tokenizar(ctx2, None)
    lineas_tk = _quitar_blancas_finales(ctx2.lineas)

    partes = [
        HEADER,
        "",
        FP_HEADER,
        "funcion gen_emitir_frontend_p(est: GeneradorCEst) -> nulo:",
        "    inseguro:",
        '        asm("static int _G_fp_emitido = 0;")',
        '        asm("if (_G_fp_emitido) return; _G_fp_emitido = 1;")',
    ]
    partes.extend(_cuerpo_asm("_G_fp", lineas_fp))
    partes.extend(["", "", TK_HEADER,
                   "funcion gen_emitir_tokenizar(est: GeneradorCEst) -> nulo:",
                   "    inseguro:"])
    partes.extend(_cuerpo_asm("_G_tk", lineas_tk))

    # Termina con una linea en blanco para que el ensamblado de
    # _rebuild_generator.py mantenga el espaciado canonico.
    return "\n".join(partes) + "\n\n"


def regenerar() -> int:
    contenido = _generar_frontend_p()
    directorio = os.path.dirname(SALIDA)
    if not os.path.isdir(directorio):
        print(f"[ERROR] Directorio no existe: {directorio}")
        return 1
    previo = ""
    if os.path.isfile(SALIDA):
        with open(SALIDA, "r", encoding="utf-8") as f:
            previo = f.read()
    with open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenido)
    if previo == contenido:
        print(f"[OK] frontend_p.syn sin cambios ({len(contenido)} caracteres)")
    else:
        print(f"[OK] frontend_p.syn regenerado ({len(contenido)} caracteres, antes {len(previo)})")
        print("     Ejecuta ahora: python nucleo/_rebuild_generator.py")
    return 0


if __name__ == "__main__":
    print("=== _gen_frontend_p.py ===")
    print(f"  Salida: {SALIDA}\n")
    sys.exit(regenerar())
