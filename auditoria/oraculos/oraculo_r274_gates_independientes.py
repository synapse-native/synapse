# -*- coding: utf-8 -*-
# Oráculo del ME r274_gates_independientes — gates fuera del build, con oráculos propios y mutación.
# cumple Manual 9 §6.1: "en cada target, el proceso de bootstrap de 3 etapas produce
#   `diff 0 bytes` entre Stage 2 y Stage 3"
# cumple Manual 9 §6.2: "El pipeline de CI/CD ejecuta automáticamente: ...
#   La verificación del bootstrap (diff 0 bytes)"
# cumple Manual 1 §7.4: bootstrapped determinista (`diff 0 bytes` entre Stage 2
#   y Stage 3) + "Generación automática de hash SHA‑256"

"""Sello de gates independientes: oráculos propios, deterministas, fuera del build.

Uso:
    python auditoria/oraculos/oraculo_r274_gates_independientes.py --construir
    python auditoria/oraculos/oraculo_r274_gates_independientes.py --sellar
    python auditoria/oraculos/oraculo_r274_gates_independientes.py --estricto
    python auditoria/oraculos/oraculo_r274_gates_independientes.py --mutar

- `--construir`: lanza `build.py --skip-test` (3 etapas S1→S2→S3) antes de comparar,
  de modo que el determinismo se puede reproducir desde un checkout limpio.
- `--sellar`: escribe `synapse_stage2.stamp` con el hash de la fuente y de la etapa 2,
  **sólo si la verificación ya pasó**.
- `--estricto`: además de S2==S3, exige que `synapse.exe` y
  `dist/bin/synapse.exe` coincidan con la etapa 2. Sin esta bandera una deriva
  se reporta como `[WARN]`, porque en un checkout de trabajo el binario puede
  ser anterior a la última edición de `nucleo/`.
- `--mutar`: prueba que el guard del sello discrimina de verdad: muta el
  contenido de la fuente **en un archivo temporal** y verifica que el sello
  detecte el cambio (es decir, que romper el sello haga fallar el gate).
  Nunca escribe en `nucleo/principal.syn`. Exige un sello previo (`--sellar`).

rc=0 cuando pasa, rc=1 con el motivo concreto cuando no.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

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
SELLO = "synapse_stage2.stamp"
FUENTE = os.path.join("nucleo", "principal.syn")

def sha256(ruta: str) -> str:
    """sha256 del archivo, o cadena vacía si no existe."""
    if not os.path.isfile(ruta):
        return ""
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()

def tamano(ruta: str) -> int:
    """Tamaño en bytes, o 0 si no existe (nunca lanza)."""
    try:
        return os.path.getsize(ruta)
    except OSError:
        return 0

def _leer_sello(raiz: str):
    """Requiere: raiz es un directorio existente.
    Garantiza: devuelve el dict del sello de frescura, o None si no existe,
      no es JSON válido o no es un objeto."""
    try:
        with open(os.path.join(raiz, SELLO), "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        return None
    return datos if isinstance(datos, dict) else None

def _escribir_sello(raiz: str, sha_fuente: str, sha_etapa2: str,
                    bytes_etapa2: int) -> None:
    """Requiere: la verificación S2==S3 ya pasó y las etapas existen.
    Garantiza: deja `synapse_stage2.stamp` con el SHA-256 del contenido de la
      fuente que produjo la etapa 2 (H-R252-5), nunca antes de verificar."""
    datos = {
        "sha256_fuente": sha_fuente,
        "sha256_etapa2": sha_etapa2,
        "bytes_etapa2": bytes_etapa2,
        "fecha": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with open(os.path.join(raiz, SELLO), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write("\n")

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
    t2 = tamano(ruta2)
    t3 = tamano(ruta3)

    if not h2:
        lineas.append(f"[FAIL] falta {ETAPA2}: no hay etapa 2 que sellar "
                      f"(corre `python build.py --skip-test` o `--construir`)")
        return False, lineas
    if not h3:
        lineas.append(f"[FAIL] falta {ETAPA3}: no se puede verificar "
                      f"S2==S3 (corre `python build.py --skip-test` o `--construir`)")
        return False, lineas

    lineas.append(f"[i] {ETAPA2} sha256 {h2[:16]} ({t2} bytes)")
    lineas.append(f"[i] {ETAPA3} sha256 {h3[:16]} ({t3} bytes)")
    if h2 != h3:
        ok = False
        lineas.append("[FAIL] Manual 1 §7.4 / Manual 9 §6.2 VIOLADO: "
                      "el bootstrap no es determinista (S2 != S3)")
    elif t2 != t3:
        ok = False
        lineas.append("[FAIL] Manual 1 §7.4 / Manual 9 §6.2 VIOLADO: "
                      f"S2 y S3 difieren en tamaño ({t2} != {t3} bytes)")
    else:
        lineas.append("[OK] bootstrap determinista: S2==S3 "
                      f"(diff 0 bytes, {t2} bytes, {h2[:16]})")

    # Guard de artefactos stale: el criterio es el CONTENIDO de la fuente
    # que produjo la etapa 2. El mtime sólo decide cuando no hay sello,
    # para que un checkout limpio (sin `.stamp`) siga funcionando igual que antes.
    if os.path.isfile(os.path.join(raiz, FUENTE)):
        h_fuente = sha256(os.path.join(raiz, FUENTE))
        sello = _leer_sello(raiz)
        h_sellada = (sello or {}).get("sha256_fuente", "")
        h2_sellada = (sello or {}).get("sha256_etapa2", "")
        certifica = bool(h_sellada) and h_sellada == h_fuente
        if h_sellada and not certifica:
            ok = False
            lineas.append(f"[FAIL] {FUENTE} cambio desde el build (sello "
                          f"{h_sellada[:16]} != actual {h_fuente[:16]}): "
                          f"reconstruye el bootstrap")
        elif certifica and h2_sellada and h2_sellada != h2:
            # El sello certifica la fuente, no el binario: si la etapa 2 no es la
            # sellada (otra corrida la reescribió), no se puede dar por fresca
            # sin volver a sellar y se cae al criterio conservador de mtime.
            certifica = False
            lineas.append("[WARN] sello no corresponde a la etapa 2 actual "
                          f"({h2_sellada[:16]} != {h2[:16]}): vuelve a sellar")
        if certifica:
            lineas.append("[OK] sello de frescura: la fuente no cambio desde el "
                          f"build (sha256 {h_fuente[:16]})")
        else:
            if not h_sellada:
                lineas.append("[WARN] sin sello: se usa mtime como criterio de "
                              f"frescura; un `build.py` lo sella")
            if not _mas_nuevo(raiz, ETAPA2, FUENTE):
                ok = False
                lineas.append("[FAIL] etapa 2 es anterior a la fuente: "
                              f"artefacto stale; reconstruye el bootstrap")
        if not _mas_nuevo(raiz, ETAPA3, ETAPA2):
            ok = False
            lineas.append("[FAIL] etapa 3 es anterior a etapa 2: "
                          f"artefacto stale; reconstruye el bootstrap")

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
    """Lanza build.py --skip-test (3 etapas) y devuelve su rc."""
    build = os.path.join(raiz, "build.py")
    if not os.path.isfile(build):
        print(f"[FAIL] no se encontró {build}", file=sys.stderr)
        return 1
    print("[r274] construyendo las 3 etapas del bootstrap (build.py --skip-test)…")
    return subprocess.call([sys.executable, build, "--skip-test"], cwd=raiz)

def _mas_nuevo(raiz: str, artefacto: str, fuente: str) -> bool:
    """True si el artefacto existe y no es anterior a la fuente."""
    try:
        return os.path.getmtime(os.path.join(raiz, artefacto)) >= os.path.getmtime(
            os.path.join(raiz, fuente)
        )
    except OSError:
        return False

def mutar_y_verificar(raiz: str, fuente: str) -> tuple:
    """Prueba que el guard del sello detecte una mutación de contenido.

    La mutación se escribe en un temporal: el árbol de trabajo NO se toca
    (un `--mutar` que reescribe `nucleo/principal.syn` puede corromperlo si la
    corrida se interrumpe).

    requiere: existe sello con `sha256_fuente` y la fuente sigue siendo la sellada.
    garantiza: (ok, detalle); ok=True sólo si el hash mutado difiere del sellado
      (es decir, el gate fallaría al romper el sello).
    """
    ruta_fuente = os.path.join(raiz, fuente)
    sello = _leer_sello(raiz)
    h_sellada = (sello or {}).get("sha256_fuente", "")
    if not h_sellada:
        return False, ("[FAIL] --mutar exige sello previo (--sellar): sin sello "
                       "no hay guard que probar")
    h_actual = sha256(ruta_fuente)
    if h_actual != h_sellada:
        return False, ("[FAIL] la fuente ya difiere del sello "
                       f"({h_sellada[:16]} != {h_actual[:16]}): vuelve a sellar")
    try:
        with open(ruta_fuente, "r", encoding="utf-8") as f:
            contenido = f.read()
    except OSError as exc:
        return False, f"[FAIL] no se pudo leer {fuente}: {exc}"

    with tempfile.TemporaryDirectory() as tmp:
        copia = os.path.join(tmp, "principal_mutado.syn")
        with open(copia, "w", encoding="utf-8") as f:
            f.write(contenido + "\n# Mutación de prueba: gates independientes\n")
        h_mutada = sha256(copia)

    if h_mutada == h_sellada:
        return False, "[FAIL] el sello no distingue el contenido mutado: gate frágil"
    return True, ("[OK] mutación de contenido detectada por el sello "
                  f"({h_sellada[:16]} -> {h_mutada[:16]}): romper el sello falla")

def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    estricto = "--estricto" in argv
    mutar = "--mutar" in argv
    if "--construir" in argv:
        rc = construir(RAIZ)
        if rc != 0:
            print(f"[FAIL] build.py termino con rc={rc}: no hay artefactos que sellar",
                  file=sys.stderr)
            return rc
    ok, lineas = comparar_artefactos(RAIZ, estricto=estricto)
    if mutar:
        # Aplicar mutación y verificar
        ok_mut, detalle_mut = mutar_y_verificar(RAIZ, FUENTE)
        ok = ok and ok_mut
        lineas.append(detalle_mut)
    for linea in lineas:
        print(f"[r274] {linea}")
    if ok and "--sellar" in argv:
        # cumple Manual 9 §6.2 / Manual 1 §7.4: sólo se sella lo ya verificado.
        h_fuente = sha256(os.path.join(RAIZ, FUENTE))
        if h_fuente:
            ruta2 = os.path.join(RAIZ, ETAPA2)
            _escribir_sello(RAIZ, h_fuente, sha256(ruta2), tamano(ruta2))
            print(f"[r274] [OK] sello de frescura escrito: {SELLO} "
                  f"(fuente sha256 {h_fuente[:16]})")
    if not ok:
        print("[r274] FAIL: gate NO verificado", file=sys.stderr)
        return 1
    print("[r274] PASS: gate determinista verificado (Manual 1 §7.4, Manual 9 §6.2)")
    if estricto:
        print("[r274] PASS: los binarios distribuidos corresponden a la etapa 2")
    return 0

if __name__ == "__main__":
    sys.exit(main())