#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""empaquetar_toolchain.py — prepara el toolchain MinGW que viaja en el instalador.

cumple Manual 9 §2.5: el instalador copia {app}\\toolchain_gcc12\\mingw64\\* (componente
`toolchain`) y `synapse.exe` lo resuelve por sí mismo desde {app}\\bin (ME r236).

El toolchain completo del repo pesa ~936 MB (cmake, gdb, doxygen, cc1plus...).
`synapse` sólo necesita un compilador C con su linker, así que este script copia
el subset mínimo que compila y enlaza un programa C real, y después lo verifica
compilando con PATH reducido a System32.

Uso:
    python instaladores/windows/empaquetar_toolchain.py            # stagea
    python instaladores/windows/empaquetar_toolchain.py --verificar
    python instaladores/windows/empaquetar_toolchain.py --limpiar

Contratos:
- requiere: el origen contiene mingw64/bin/gcc.exe.
- garantiza: el destino contiene gcc.exe, cc1.exe, as.exe, ld.exe, collect2.exe,
  headers y librerías, y (con --verificar) compila y ejecuta un C de prueba sin
  ningún gcc en el PATH.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ORIGEN_DEFECTO = os.path.join(RAIZ, 'toolchain_gcc12', 'mingw64')
DESTINO_DEFECTO = os.path.join(RAIZ, 'instaladores', 'windows', 'dist',
                               'toolchain_gcc12', 'mingw64')

# Binarios del compilador C y del linker (sin g++, gdb, cmake ni docs).
BIN_EXE = ('gcc.exe', 'as.exe', 'ld.exe', 'dlltool.exe')  # collect2 vive en libexec/

# DLLs de las que dependen gcc/cc1/ld en MinGW-w64 (se copian todas las de bin/:
# son 117 MB incluyendo toolchains ajenos al compilador C, así que se filtran).
BIN_DLL = ('libwinpthread-1.dll', 'libgcc_s_seh-1.dll', 'libgmp-10.dll',
           'libmpfr-6.dll', 'libmpc-3.dll', 'libisl-23.dll', 'libiconv-2.dll',
           'libintl-8.dll', 'libz.dll', 'libzstd.dll', 'zlib1.dll')

# Directorios que se copian completos (headers + import libs + soporte de gcc).
DIRS_COMPLETOS = ('x86_64-w64-mingw32/include', 'x86_64-w64-mingw32/lib',
                  'lib/gcc')


def _log(msg):
    print('[toolchain] ' + msg)


def _copiar(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return os.path.getsize(dst)


def _version_gcc(origen):
    """Devuelve (triple, version) de la rama lib/gcc/<triple>/<version>."""
    base = os.path.join(origen, 'lib', 'gcc')
    if not os.path.isdir(base):
        return None, None
    for triple in sorted(os.listdir(base)):
        ruta = os.path.join(base, triple)
        if not os.path.isdir(ruta):
            continue
        versiones = [v for v in sorted(os.listdir(ruta))
                     if os.path.isdir(os.path.join(ruta, v))]
        if versiones:
            return triple, versiones[-1]
    return None, None


def empaquetar(origen, destino, limpiar=False):
    """Stagea el subset mínimo. Contratos: ver docstring del módulo."""
    gcc = os.path.join(origen, 'bin', 'gcc.exe')
    if not os.path.isfile(gcc):
        raise SystemExit('[toolchain] ERROR: no existe %s (¿toolchain ausente?)' % gcc)
    if limpiar and os.path.isdir(destino):
        shutil.rmtree(destino)

    total = 0
    archivos = 0

    for nombre in BIN_EXE:
        src = os.path.join(origen, 'bin', nombre)
        if os.path.isfile(src):
            total += _copiar(src, os.path.join(destino, 'bin', nombre))
            archivos += 1

    for nombre in BIN_DLL:
        src = os.path.join(origen, 'bin', nombre)
        if os.path.isfile(src):
            total += _copiar(src, os.path.join(destino, 'bin', nombre))
            archivos += 1

    triple, version = _version_gcc(origen)
    if not triple:
        raise SystemExit('[toolchain] ERROR: no se encontró lib/gcc/<triple>/<version>')
    libexec = os.path.join(destino, 'libexec', 'gcc', triple, version)
    cc1 = os.path.join(origen, 'libexec', 'gcc', triple, version, 'cc1.exe')
    if not os.path.isfile(cc1):
        raise SystemExit('[toolchain] ERROR: no existe %s' % cc1)
    total += _copiar(cc1, os.path.join(libexec, 'cc1.exe'))
    archivos += 1
    # cc1.exe se ejecuta desde libexec/, y Windows busca sus DLLs primero en el
    # directorio del ejecutable: sin copiarlas ahí, gcc muere con
    # 0xC0000135 (DLL no encontrada) cuando bin/ no está en el PATH.
    for nombre in BIN_DLL + ('liblto_plugin.dll', 'collect2.exe'):
        src = os.path.join(origen, 'bin', nombre)
        if not os.path.isfile(src):
            src = os.path.join(origen, 'libexec', 'gcc', triple, version, nombre)
        if os.path.isfile(src):
            total += _copiar(src, os.path.join(libexec, nombre))
            archivos += 1

    for rel in DIRS_COMPLETOS:
        base = os.path.join(origen, rel.replace('/', os.sep))
        if not os.path.isdir(base):
            continue
        for raiz, _dirs, ficheros in os.walk(base):
            for f in ficheros:
                src = os.path.join(raiz, f)
                rel_dentro = os.path.relpath(src, origen)
                total += _copiar(src, os.path.join(destino, rel_dentro))
                archivos += 1

    _log('staged %d archivos, %.1f MB en %s' % (archivos, total / (1024.0 * 1024.0),
                                               destino))
    _log('gcc %s (%s)' % (version, triple))
    return archivos, total


def verificar(destino):
    """Compila y ejecuta un C con PATH reducido a System32. Devuelve el stdout."""
    # cumple Manual 9 §7: criterio "instalación en Windows (limpiamente)" — el
    # toolchain que viaja en el setup compila y ejecuta sin MinGW del sistema.
    gcc = os.path.join(destino, 'bin', 'gcc.exe')
    if not os.path.isfile(gcc):
        raise SystemExit('[toolchain] ERROR: no hay gcc staged en %s' % gcc)
    tmp = tempfile.mkdtemp(prefix='synapse_toolchain_')
    try:
        fuente = os.path.join(tmp, 'hola.c')
        exe = os.path.join(tmp, 'hola.exe')
        with open(fuente, 'w', encoding='utf-8') as fh:
            fh.write('#include <stdio.h>\nint main(void) { printf("toolchain ok\\n"); return 0; }\n')
        # PATH del hijo = bin/ staged + System32: así lo deja el resolver de
        # nucleo/principal.syn antes de invocar gcc (gcc llama a `as` y `ld`
        # por nombre si no están en COMPILER_PATH).
        env = dict(os.environ)
        env['PATH'] = os.pathsep.join([
            os.path.join(destino, 'bin'),
            os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32'),
        ])
        comp = subprocess.run([gcc, '-O2', fuente, '-o', exe], cwd=tmp, env=env,
                              capture_output=True, text=True)
        if comp.returncode != 0:
            raise SystemExit('[toolchain] ERROR: gcc staged no compila rc=%d\n%s\n%s'
                             % (comp.returncode, comp.stdout, comp.stderr))
        run = subprocess.run([exe], cwd=tmp, env=env, capture_output=True, text=True)
        if run.returncode != 0 or 'toolchain ok' not in run.stdout:
            raise SystemExit('[toolchain] ERROR: el .exe staged no ejecuta rc=%d out=%r'
                             % (run.returncode, run.stdout))
        _log('verificado: gcc staged compila y ejecuta con PATH=System32')
        return run.stdout
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Empaqueta el subset mínimo de MinGW.')
    ap.add_argument('--origen', default=ORIGEN_DEFECTO)
    ap.add_argument('--destino', default=DESTINO_DEFECTO)
    ap.add_argument('--limpiar', action='store_true', help='borra el destino antes')
    ap.add_argument('--verificar', action='store_true',
                    help='compila un C de prueba con PATH=System32')
    args = ap.parse_args(argv)

    if args.limpiar and os.path.isdir(args.destino):
        shutil.rmtree(args.destino)
        _log('limpiado %s' % args.destino)

    if args.verificar:
        if not os.path.isdir(args.destino):
            empaquetar(args.origen, args.destino)
        verificar(args.destino)
    elif not args.limpiar:
        empaquetar(args.origen, args.destino)
    return 0


if __name__ == '__main__':
    sys.exit(main())
