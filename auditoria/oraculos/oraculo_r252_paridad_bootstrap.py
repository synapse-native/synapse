# -*- coding: utf-8 -*-
# Oráculo del ME r252_bootstrap_parity — sello de bootstrap reproducible.
# cumple Manual 1 §6: la regla de hierro es "etapas 0->1->2->3 con diff binario
#   0" y el determinismo se verifica con los SHA-256 de las etapas 2 y 3.
# cumple Manual 9 §6.2: "La verificación del bootstrap (diff 0 bytes)."
# cumple Manual 9 §2.3: "Verificar el bootstrap (diff 0 bytes entre Stage 2 y
#   Stage 3)" como parte del pipeline de compilación.
"""Sello de bootstrap S2==S3 y guard de deriva de los binarios distribuidos.

Uso:
    python auditoria/oraculos/oraculo_r252_paridad_bootstrap.py --artefactos
    python auditoria/oraculos/oraculo_r252_paridad_bootstrap.py --construir
    python auditoria/oraculos/oraculo_r252_paridad_bootstrap.py --artefactos --estricto

- `--artefactos` (por defecto): compara los artefactos que ya existen.
  Es el modo que usa `build.py` y el job `bootstrap` de CI, para que el sello
  tenga una sola implementación.
- `--construir`: lanza `build.py` (3 etapas) antes de comparar, de modo que el
  determinismo se puede reproducir desde un checkout limpio.
- `--estricto`: además de S2==S3, exige que `synapse.exe` y
  `dist/bin/synapse.exe` coincidan con la etapa 2. Sin esta bandera una deriva
  se reporta como `[WARN]`, porque en un checkout de trabajo el binario puede
  ser anterior a la última edición de `nucleo/`.

rc=0 cuando pasa, rc=1 con el motivo concreto cuando no.
"""

import hashlib
import os
import subprocess
import sys

# La salida lleva «§» y acentos: sin esto, una consola cp1252 imprime «?» y el
# log de CI queda ilegible justo en el mensaje del sello.
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ETAPA2 = "synapse_stage2.exe"
ETAPA3 = "synapse_stage3.exe"
DISTRIBUIDOS = ("synapse.exe", os.path.join("dist", "bin", "synapse.exe"))


def sha256(ruta: str) -> str:
    """sha256 del archivo, o cadena vacía si no existe."""
    if not os.path.isfile(ruta):
        return ""
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def comparar_artefactos(raiz: str, estricto: bool = False):
    """Compara stage2/stage3 (y los distribuidos si `estricto`).

    requiere: raiz es un directorio existente
    garantiza: devuelve (ok, detalle) con una línea por comprobación y nunca
      lanza por artefactos ausentes
    """
    lineas = []
    ok = True

    ruta2 = os.path.join(raiz, ETAPA2)
    ruta3 = os.path.join(raiz, ETAPA3)
    h2 = sha256(ruta2)
    h3 = sha256(ruta3)

    if not h2:
        lineas.append(f"[FAIL] falta {ETAPA2}: no hay etapa 2 que sellar "
                      f"(corre `python build.py` o `--construir`)")
        return False, lineas
    if not h3:
        lineas.append(f"[FAIL] falta {ETAPA3}: no se puede verificar "
                      f"S2==S3 (corre `python build.py` o `--construir`)")
        return False, lineas

    lineas.append(f"[i] {ETAPA2} sha256 {h2[:16]}")
    lineas.append(f"[i] {ETAPA3} sha256 {h3[:16]}")
    if h2 != h3:
        ok = False
        lineas.append("[FAIL] Manual 1 §6 / Manual 9 §6.2 VIOLADO: "
                      "el bootstrap no es determinista (S2 != S3)")
    else:
        lineas.append(f"[OK] bootstrap determinista: S2==S3 (diff 0 bytes, {h2[:16]})")

    for rel in DISTRIBUIDOS:
        hd = sha256(os.path.join(raiz, rel))
        if not hd:
            etiqueta = "[FAIL]" if estricto else "[WARN]"
            if estricto:
                ok = False
            lineas.append(f"{etiqueta} no existe el binario distribuido {rel}")
            continue
        if hd != h2:
            etiqueta = "[FAIL]" if estricto else "[WARN]"
            if estricto:
                ok = False
            lineas.append(f"{etiqueta} {rel} NO corresponde al bootstrap actual "
                          f"({hd[:16]} != {h2[:16]}); refresca los binarios")
        else:
            lineas.append(f"[OK] {rel} corresponde al bootstrap actual")

    return ok, lineas


def construir(raiz: str) -> int:
    """Lanza build.py (3 etapas) y devuelve su rc."""
    build = os.path.join(raiz, "build.py")
    if not os.path.isfile(build):
        print(f"[FAIL] no se encontro {build}", file=sys.stderr)
        return 1
    print("[r252] construyendo las 3 etapas del bootstrap (build.py)…")
    return subprocess.call([sys.executable, build], cwd=raiz)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    estricto = "--estricto" in argv
    if "--construir" in argv:
        rc = construir(RAIZ)
        if rc != 0:
            print(f"[FAIL] build.py termino con rc={rc}: no hay artefactos que sellar",
                  file=sys.stderr)
            return rc
    ok, lineas = comparar_artefactos(RAIZ, estricto=estricto)
    for linea in lineas:
        print(f"[r252] {linea}")
    if not ok:
        print("[r252] FAIL: sello de bootstrap NO verificado", file=sys.stderr)
        return 1
    print("[r252] PASS: bootstrap determinista S2==S3 (Manual 1 §6, Manual 9 §6.2)")
    if estricto:
        print("[r252] PASS: los binarios distribuidos corresponden a la etapa 2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
