# -*- coding: utf-8 -*-
# Oráculo del ME r252_bootstrap_parity — sello de bootstrap reproducible.
# cumple Manual 1 §6: la regla de hierro es "etapas 0->1->2->3 con diff binario
#   0" y el determinismo se verifica con los SHA-256 de las etapas 2 y 3.
# cumple Manual 9 §6.2: "La verificación del bootstrap (diff 0 bytes)."
# cumple Manual 9 §2.3: "Verificar el bootstrap (diff 0 bytes entre Stage 2 y
#   Stage 3)" como parte del pipeline de compilación.
# cumple Manual 1 §6 (ME r270b, H-R252-5): la frescura de la etapa 2 se certifica
#   por el hash del CONTENIDO de la fuente, no por su mtime.
"""Sello de bootstrap S2==S3 y guard de deriva de los binarios distribuidos.

Uso:
    python auditoria/oraculos/oraculo_r252_paridad_bootstrap.py --artefactos
    python auditoria/oraculos/oraculo_r252_paridad_bootstrap.py --construir
    python auditoria/oraculos/oraculo_r252_paridad_bootstrap.py --artefactos --estricto
    python auditoria/oraculos/oraculo_r252_paridad_bootstrap.py --artefactos --sellar

- `--artefactos` (por defecto): compara hash y tamaño de los artefactos que ya
  existen y rechaza una etapa 2 que no corresponda a `nucleo/principal.syn`.
  Es el modo que usa `build.py` y el job `bootstrap` de CI, para que el sello
  tenga una sola implementación.
  La frescura se decide por **contenido**: si existe `synapse_stage2.stamp`
  (H-R252-5) y el SHA-256 de la fuente coincide con el sellado, tocar el
  archivo sin cambiarlo no invalida nada; si difiere, el sello falla. Sin
  sello se conserva el criterio de `mtime` con un aviso.
- `--sellar`: escribe `synapse_stage2.stamp` con el hash de la fuente y de la
  etapa 2, **sólo si la verificación ya pasó**.
- `--construir`: lanza `build.py` (3 etapas) antes de comparar, de modo que el
  determinismo se puede reproducir desde un checkout limpio.
- `--estricto`: además de S2==S3, exige que `synapse.exe` y
  `dist/bin/synapse.exe` coincidan con la etapa 2. Sin esta bandera una deriva
  se reporta como `[WARN]`, porque en un checkout de trabajo el binario puede
  ser anterior a la última edición de `nucleo/`.

rc=0 cuando pasa, rc=1 con el motivo concreto cuando no.
"""

import hashlib
import json
import os
import subprocess
import sys
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
# Sello de frescura por contenido (H-R252-5): un artefacto de máquina, no se
# versiona; lo escribe `--sellar` después de verificar.
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
    """requiere: raiz es un directorio existente
    garantiza: devuelve el dict del sello de frescura, o None si no existe,
      no es JSON válido o no es un objeto
    """
    try:
        with open(os.path.join(raiz, SELLO), "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        return None
    return datos if isinstance(datos, dict) else None


def _escribir_sello(raiz: str, sha_fuente: str, sha_etapa2: str,
                    bytes_etapa2: int) -> None:
    """requiere: la verificación S2==S3 ya pasó y las etapas existen
    garantiza: deja `synapse_stage2.stamp` con el SHA-256 del contenido de la
      fuente que produjo la etapa 2 (H-R252-5), nunca antes de verificar
    """
    datos = {
        "sha256_fuente": sha_fuente,
        "sha256_etapa2": sha_etapa2,
        "bytes_etapa2": bytes_etapa2,
        "fecha": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with open(os.path.join(raiz, SELLO), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _mas_nuevo(raiz: str, artefacto: str, fuente: str) -> bool:
    """True si el artefacto existe y no es anterior a la fuente."""
    try:
        return os.path.getmtime(os.path.join(raiz, artefacto)) >= os.path.getmtime(
            os.path.join(raiz, fuente)
        )
    except OSError:
        return False


def comparar_artefactos(raiz: str, estricto: bool = False,
                        sellar: bool = False):
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
                      f"(corre `python build.py` o `--construir`)")
        return False, lineas
    if not h3:
        lineas.append(f"[FAIL] falta {ETAPA3}: no se puede verificar "
                      f"S2==S3 (corre `python build.py` o `--construir`)")
        return False, lineas

    lineas.append(f"[i] {ETAPA2} sha256 {h2[:16]} ({t2} bytes)")
    lineas.append(f"[i] {ETAPA3} sha256 {h3[:16]} ({t3} bytes)")
    if h2 != h3:
        ok = False
        lineas.append("[FAIL] Manual 1 §6 / Manual 9 §6.2 VIOLADO: "
                      "el bootstrap no es determinista (S2 != S3)")
    elif t2 != t3:
        ok = False
        lineas.append(f"[FAIL] Manual 1 §6 / Manual 9 §6.2 VIOLADO: "
                      f"S2 y S3 difieren en tamaño ({t2} != {t3} bytes)")
    else:
        lineas.append(f"[OK] bootstrap determinista: S2==S3 "
                      f"(diff 0 bytes, {t2} bytes, {h2[:16]})")

    # Guard de artefactos stale: un stage2 de una corrida anterior puede tener
    # el mismo hash que stage3 por casualidad y ocultar que no se reconstruyó.
    # cumple Manual 1 §6 (ME r270b, H-R252-5): el criterio es el CONTENIDO de la
    # fuente que produjo la etapa 2. El mtime sólo decide cuando no hay sello,
    # para que un checkout limpio (sin `.stamp`) siga funcionando igual que antes.
    fuente = FUENTE
    if os.path.isfile(os.path.join(raiz, fuente)):
        h_fuente = sha256(os.path.join(raiz, fuente))
        sello = _leer_sello(raiz)
        h_sellada = (sello or {}).get("sha256_fuente", "")
        h2_sellada = (sello or {}).get("sha256_etapa2", "")
        certifica = bool(h_sellada) and h_sellada == h_fuente
        if h_sellada and not certifica:
            # H-R275-2 (cumple Manual 1 §6): cambiar la fuente dejaba el sello
            # obsoleto y el oráculo se negaba a re-sellar, de modo que el
            # bootstrap no se podía reconstruir nunca tras editar principal.syn.
            # Si el build de esta corrida regeneró la etapa 2 (mtime posterior a
            # la fuente) y S2==S3, el sello viejo sólo describe la fuente
            # anterior: se re-sella en vez de abortar. Un artefacto stale sigue
            # fallando, porque no es posterior a la fuente.
            if sellar and h2 == h3 and _mas_nuevo(raiz, ETAPA2, fuente):
                lineas.append(f"[OK] sello de frescura reescrito: {fuente} cambio "
                              f"(sello {h_sellada[:16]}) y la {ETAPA2} es "
                              f"posterior al build")
                certifica = True
            else:
                ok = False
                lineas.append(f"[FAIL] {fuente} cambio desde el build (sello "
                              f"{h_sellada[:16]} != actual {h_fuente[:16]}): "
                              f"reconstruye el bootstrap")
        elif certifica and h2_sellada and h2_sellada != h2:
            # El sello certifica la fuente, no el binario: si la etapa 2 no es la
            # sellada (otra corrida la reescribió), no se puede dar por fresca
            # sin volver a sellar y se cae al criterio conservador de mtime.
            certifica = False
            lineas.append(f"[WARN] {SELLO} no corresponde a la {ETAPA2} actual "
                          f"({h2_sellada[:16]} != {h2[:16]}): vuelve a sellar")
        if certifica:
            lineas.append(f"[OK] sello de frescura: la fuente no cambio desde el "
                          f"build (sha256 {h_fuente[:16]})")
        else:
            if not h_sellada:
                lineas.append(f"[WARN] sin {SELLO}: se usa mtime como criterio de "
                              f"frescura; un `build.py` lo sella")
            if not _mas_nuevo(raiz, ETAPA2, fuente):
                ok = False
                lineas.append(f"[FAIL] {ETAPA2} es anterior a {fuente}: artefacto "
                              f"stale; reconstruye el bootstrap")
        if not _mas_nuevo(raiz, ETAPA3, ETAPA2):
            ok = False
            lineas.append(f"[FAIL] {ETAPA3} es anterior a {ETAPA2}: artefacto "
                          f"stale; reconstruye el bootstrap")

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
    ok, lineas = comparar_artefactos(RAIZ, estricto=estricto,
                                     sellar="--sellar" in argv)
    for linea in lineas:
        print(f"[r252] {linea}")
    if ok and "--sellar" in argv:
        # cumple Manual 9 §6.2 / Manual 1 §6: sólo se sella lo ya verificado.
        h_fuente = sha256(os.path.join(RAIZ, FUENTE))
        if h_fuente:
            ruta2 = os.path.join(RAIZ, ETAPA2)
            _escribir_sello(RAIZ, h_fuente, sha256(ruta2), tamano(ruta2))
            print(f"[r252] [OK] sello de frescura escrito: {SELLO} "
                  f"(fuente sha256 {h_fuente[:16]})")
    if not ok:
        print("[r252] FAIL: sello de bootstrap NO verificado", file=sys.stderr)
        return 1
    print("[r252] PASS: bootstrap determinista S2==S3 (Manual 1 §6, Manual 9 §6.2)")
    if estricto:
        print("[r252] PASS: los binarios distribuidos corresponden a la etapa 2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
