# -*- coding: utf-8 -*-
# cumple Manual 2 §8.2: el emisor nativo infiere el tipo de la expresion desde
#   el AST (ExprIndice sobre texto -> CadenaSegura), paridad con el emisor S1.
# cumple Manual 2 §4.1: "texto / cadena / string | Cadena UTF-8 segura
#   (longitud + buffer)"; indexar un texto produce un texto de 1 caracter.
# cumple Manual 7 §7.3: el sandbox de OpenSyn decide ASK/DENY/ALLOW sobre rutas
#   reales; la sonda E2E debe compilar con el emisor nativo (S2), no caer a S1.
# cumple Manual 8 §4.1: `synapse build` resuelve sus modulos y las fuentes del
#   runtime tambien cuando se invoca desde otro directorio de trabajo.
"""Oráculo del ME r275b — emisión nativa de `str_eq`/indexado de texto.

H-R275-1: el emisor autohospedado (S2) emitía `int64_t` para `texto[i]`, de modo
que `opensyn/permisos.syn` no compilaba (`incompatible type for argument 1 of
'str_eq'`) y la sonda E2E caía al emisor S1 con `[R275][WARN]`.

Este oráculo es determinista y NO necesita modelo: compila dos sondas con el
binario nativo, las ejecuta y valida su salida.

1. Indexado de texto: `let c = s[3]` debe declararse `CadenaSegura`, con
   `longitud(c) == 1`, comparación con literal (`== "/"`, `!= "x"`) y `str_eq`
   sin conversiones.
2. Sandbox de OpenSyn compilado con S2 desde un directorio temporal (igual que
   el test E2E): ASK dentro del workspace, DENY fuera, ALLOW lectura. Además
   comprueba que el binario resuelve `std.io`/`opensyn.permisos` y las fuentes
   del runtime fuera del repo.

Uso:
    python auditoria/oraculos/oraculo_r275b_texto_indexado.py [--verbose]

rc=0 cuando ambas sondas compilan con el binario nativo y su salida es la
esperada; rc=1 con el motivo concreto cuando no.
"""

import os
import subprocess
import sys
import tempfile

for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Binario nativo: el distribuido es el que usa el E2E; se acepta la etapa 2
# como respaldo para un checkout recién construido.
NATIVOS = (
    os.path.join("dist", "bin", "synapse.exe"),
    "synapse.exe",
    "synapse_stage2.exe",
)

SONDA_TEXTO = """#lang: es
// cumple Manual 2 §4.1: indexar un texto devuelve un texto de un caracter
importar std.io

funcion principal() -> entero:
    let s = "abc/def"
    let c = s[3]
    escribir_linea(concat("len=", entero_a_texto(longitud(c))))
    escribir_linea(concat("car=", c))
    si c == "/":
        escribir_linea("eq=ok")
    si c != "x":
        escribir_linea("ne=ok")
    retornar 0
"""

SONDA_PERMISOS = """#lang: es
// cumple Manual 7 §7.3: sonda del sandbox de herramientas de OpenSyn
importar opensyn.permisos
importar std.io

funcion principal() -> entero:
    let m = matriz_permisos_crear()
    let base = _syn_obtener_cwd()
    let dentro = concat(base, "/r275_workspace/x.txt")
    escribir_linea(concat("editar_dentro=", entero_a_texto(verificar_permiso_completo(m, "editar", dentro))))
    escribir_linea(concat("editar_fuera=", entero_a_texto(verificar_permiso_completo(m, "editar", "C:/Windows/System32/x.txt"))))
    escribir_linea(concat("leer_dentro=", entero_a_texto(verificar_permiso_completo(m, "leer", dentro))))
    retornar 0
"""


def _nativo():
    """requiere: nada
    garantiza: devuelve la ruta absoluta del binario nativo, o None si no hay
    """
    for rel in NATIVOS:
        ruta = os.path.join(RAIZ, rel)
        if os.path.isfile(ruta):
            return ruta
    return None


def _compilar_y_ejecutar(nativo, tmp, nombre, fuente, verbose=False):
    """requiere: nativo es un ejecutable existente y tmp un directorio
    garantiza: compila `fuente` en tmp y devuelve (rc_compilacion, salida,
      rc_ejecucion); nunca lanza por fallo de gcc
    """
    src = os.path.join(tmp, nombre + ".syn")
    with open(src, "w", encoding="utf-8") as f:
        f.write(fuente)
    exe = os.path.join(tmp, nombre + ".exe")
    r = subprocess.run([nativo, os.path.basename(src), "-o", os.path.basename(exe)],
                       cwd=tmp, capture_output=True, text=True, timeout=600,
                       encoding="utf-8", errors="replace")
    if verbose:
        print("  compilacion rc=%d" % r.returncode)
        print("  " + (r.stdout or "").strip()[-600:])
        print("  " + (r.stderr or "").strip()[-600:])
    if r.returncode != 0:
        return r.returncode, (r.stdout or "") + (r.stderr or ""), None
    e = subprocess.run([exe], cwd=tmp, capture_output=True, text=True,
                       timeout=300, encoding="utf-8", errors="replace")
    return 0, (e.stdout or ""), e.returncode


def _lineas(salida):
    """requiere: salida es texto
    garantiza: devuelve el conjunto de lineas no vacias, sin espacios extra
    """
    return {l.strip() for l in (salida or "").splitlines() if l.strip()}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    verbose = "--verbose" in argv
    nativo = _nativo()
    if nativo is None:
        print("[FAIL] no hay binario nativo (dist/bin/synapse.exe, synapse.exe): "
              "construye el bootstrap con `python build.py`", file=sys.stderr)
        return 1
    print("[i] binario nativo: %s" % os.path.relpath(nativo, RAIZ))

    fallos = []
    with tempfile.TemporaryDirectory(prefix="r275b_") as tmp:
        rc, salida, rc_ej = _compilar_y_ejecutar(
            nativo, tmp, "sonda_texto", SONDA_TEXTO, verbose)
        if rc != 0:
            fallos.append("la sonda de indexado de texto no compila con el "
                          "emisor nativo (H-R275-1):\n" + salida[-1500:])
        elif rc_ej != 0:
            fallos.append("la sonda de indexado de texto falla al ejecutar "
                          "(rc=%d):\n%s" % (rc_ej, salida[-1500:]))
        else:
            obtenido = _lineas(salida)
            esperado = {"len=1", "car=/", "eq=ok", "ne=ok"}
            faltan = esperado - obtenido
            if faltan:
                fallos.append("indexado de texto con semantica incorrecta: "
                              "faltan %s\n%s" % (sorted(faltan), salida[-1500:]))
            else:
                print("[OK] texto[i] se emite como CadenaSegura: len=1, car=/, "
                      "== y != con literal")

        rc, salida, rc_ej = _compilar_y_ejecutar(
            nativo, tmp, "sonda_permisos", SONDA_PERMISOS, verbose)
        if rc != 0:
            fallos.append("opensyn/permisos.syn no compila con el emisor "
                          "nativo (S2):\n" + salida[-1500:])
        elif rc_ej != 0:
            fallos.append("la sonda del sandbox falla al ejecutar (rc=%d):\n%s"
                          % (rc_ej, salida[-1500:]))
        else:
            obtenido = _lineas(salida)
            esperado = {"editar_dentro=1", "editar_fuera=2", "leer_dentro=0"}
            faltan = esperado - obtenido
            if faltan:
                fallos.append("sandbox de OpenSyn con semantica incorrecta: "
                              "faltan %s\n%s" % (sorted(faltan), salida[-1500:]))
            else:
                print("[OK] sandbox OpenSyn con S2: editar dentro=ASK, fuera=DENY, "
                      "leer dentro=ALLOW")

    for fallo in fallos:
        print("[FAIL] " + fallo, file=sys.stderr)
    if fallos:
        return 1
    # Marca explícita de PASS: la ÚLTIMA línea la lee `alineacion.py`/`contrastar.py`.
    print("OK: r275b emision nativa de str_eq/indexado de texto (Manual 2 §4.1, "
          "Manual 7 §7.3, Manual 8 §4.1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
