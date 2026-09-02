# cumple Manual 4 1: pipeline completo OpenSyn
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
opensyn/pipeline.py — Pipeline completo Python -> Syquex -> C -> Ejecutable
================================================================================
Propósito: Orquestar el pipeline end-to-end de transpilación y compilación.

Uso:
    python opensyn/pipeline.py input.py
    python opensyn/pipeline.py input.py -o output.exe
"""
import os
import sys
import subprocess
import tempfile
import time
from typing import Optional, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.join(PROJECT_ROOT, "opensyn") not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))


def transpilar_py_a_syq(ruta_py: str, ruta_syq: Optional[str] = None) -> str:
    """Paso 1: Transpilar .py -> .syq."""
    from transpiler import transpilar_archivo

    if ruta_syq is None:
        ruta_syq = os.path.splitext(ruta_py)[0] + ".syn"

    resultado = transpilar_archivo(ruta_py)
    with open(ruta_syq, "w", encoding="utf-8") as f:
        f.write(resultado)

    return ruta_syq


def compilar_syq_a_exe(ruta_syq: str, ruta_exe: Optional[str] = None,
                       modo_release: bool = False, modo_debug: bool = False) -> int:
    """Paso 2: Compilar .syq -> .c -> .exe usando el compilador S1."""
    # Importar el pipeline del compilador
    sys.path.insert(0, PROJECT_ROOT)
    import importlib
    import pipeline as _root_pipeline
    ejecutar_compilador = _root_pipeline.ejecutar_compilador

    if ruta_exe is None:
        base = os.path.splitext(ruta_syq)[0]
        if sys.platform == "win32":
            ruta_exe = base + ".exe"
        else:
            ruta_exe = base

    codigo = ejecutar_compilador(
        ruta_syq,
        mostrar_tokens=False,
        output_lang=None,
        dump_ast=False,
        modo_safe=False,
        output_path=ruta_exe,
        incremental=False,
        generar_sbom=False,
        firmar_binario=False,
        clave_sbom="",
        target="native",
        modo_release=modo_release,
        modo_debug=modo_debug,
        check_only=False,
    )

    return codigo


def ejecutar_pipeline(ruta_py: str, ruta_exe: Optional[str] = None,
                      modo_release: bool = False, modo_debug: bool = False,
                      keep_syq: bool = False) -> Tuple[int, Optional[str], Optional[str]]:
    """
    Pipeline completo: .py -> .syq -> .c -> .exe

    Retorna: (codigo_retorno, ruta_syq_generada, ruta_exe_generada)
    """
    ruta_py = os.path.abspath(ruta_py)
    if not os.path.exists(ruta_py):
        print(f"ERROR: Archivo '{ruta_py}' no encontrado", file=sys.stderr)
        return 1, None, None

    # Paso 1: .py -> .syq
    ruta_syq = os.path.splitext(ruta_py)[0] + ".syn"
    print(f"[PIPELINE] .py -> .syq: {os.path.basename(ruta_py)}")
    try:
        transpilar_py_a_syq(ruta_py, ruta_syq)
    except Exception as e:
        print(f"ERROR: Fallo en transpilación: {e}", file=sys.stderr)
        return 1, None, None

    # Paso 2: .syq -> .c -> .exe
    if ruta_exe is None:
        base = os.path.splitext(ruta_py)[0]
        if sys.platform == "win32":
            ruta_exe = base + ".exe"
        else:
            ruta_exe = base

    print(f"[PIPELINE] .syq -> .exe: {os.path.basename(ruta_syq)}")
    t0 = time.time()
    codigo = compilar_syq_a_exe(ruta_syq, ruta_exe, modo_release, modo_debug)
    elapsed = time.time() - t0

    if codigo == 0:
        size_kb = os.path.getsize(ruta_exe) / 1024
        print(f"[PIPELINE] ✅ {os.path.basename(ruta_py)} -> {os.path.basename(ruta_exe)} ({size_kb:.1f} KB, {elapsed:.1f}s)")
    else:
        print(f"[PIPELINE] ❌ Fallo en compilación (código {codigo})")

    # Limpiar .syq temporal si no se pide conservar
    if not keep_syq and os.path.exists(ruta_syq):
        os.remove(ruta_syq)

    return codigo, ruta_syq, ruta_exe


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Pipeline completo: .py -> .syq -> .c -> .exe"
    )
    parser.add_argument("input", help="Archivo Python de entrada (.py)")
    parser.add_argument("-o", "--output", help="Ruta del ejecutable de salida")
    parser.add_argument("--release", action="store_true",
                        help="Compilar con optimizaciones -O3 -flto")
    parser.add_argument("--debug", action="store_true",
                        help="Compilar con -O0 -g -fsanitize")
    parser.add_argument("--keep-syq", action="store_true",
                        help="Conservar el archivo .syq generado")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: Archivo '{args.input}' no encontrado", file=sys.stderr)
        sys.exit(1)

    codigo, _, _ = ejecutar_pipeline(
        args.input,
        ruta_exe=args.output,
        modo_release=args.release,
        modo_debug=args.debug,
        keep_syq=args.keep_syq,
    )

    sys.exit(codigo)


if __name__ == "__main__":
    main()
