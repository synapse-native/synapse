#!/usr/bin/env python3
# build.py — Build unificado y reproducible del compilador (Manual 9 §2.3/F30).
# cumple Manual 9 §2.3 + Manual 9 §6.2 (bootstrap diff 0 bytes, ME_30_T2).
# cumple Manual 9 §6.2: cada corrida verifica S2==S3 (diff determinista).
# cumple Manual 9 §2.3: pipeline del CI/CD reproducible (build/pruebas/sellado).
# Corre el bootstrap de 3 etapas y despliega el compilador instalable:
#   stage1 (main.py) compila nucleo/principal.syn -> synapse_stage1.exe
#   stage2 (stage1)  autocompila                  -> synapse_stage2.exe
#   stage3 (stage2)  autocompila                  -> synapse_stage3.exe
# Determinismo: stage2 == stage3 (diff 0 bytes, Manual 9 §6.1 checklist).
#   python build.py [--skip-test]
import hashlib
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
FUENTE = os.path.join(RAIZ, "nucleo", "principal.syn")


def _sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _correr(cmd):
    print(f"[build] {' '.join(cmd[1:]) if len(cmd) > 1 else cmd[0]}")
    rc = subprocess.call(cmd, cwd=RAIZ)
    if rc != 0:
        print(f"[build][ERROR] rc={rc}: {cmd}", file=sys.stderr)
        sys.exit(rc)


def main():
    venv = os.path.join(RAIZ, ".venv")
    py = os.path.join(venv, "Scripts", "python.exe") if os.path.isdir(venv) \
        else sys.executable

    etapas = {
        "synapse_stage1.exe": [py, "main.py", "nucleo/principal.syn"],
        "synapse_stage2.exe": ["./synapse_stage1.exe", "nucleo/principal.syn"],
        "synapse_stage3.exe": ["./synapse_stage2.exe", "nucleo/principal.syn"],
    }
    # etapas 1 (python) produce synapse_bootstrap.exe que renombramos
    _correr([py, "main.py", "nucleo/principal.syn"])
    bootstrap = os.path.join(RAIZ, "synapse_bootstrap.exe")
    if not os.path.exists(bootstrap):
        print("[build][ERROR] main.py no produjo synapse_bootstrap.exe", file=sys.stderr)
        sys.exit(1)
    os.replace(bootstrap, os.path.join(RAIZ, "synapse_stage1.exe"))

    for exe in ("synapse_stage2.exe", "synapse_stage3.exe"):
        _correr([f"./synapse_stage{1 if exe.endswith('2.exe') else 2}.exe",
                 "nucleo/principal.syn"])
        nuevo = os.path.join(RAIZ, "principal.exe")
        if not os.path.exists(nuevo):
            print(f"[build][ERROR] {exe} no produjo principal.exe", file=sys.stderr)
            sys.exit(1)
        os.replace(nuevo, os.path.join(RAIZ, exe))

    # Determinismo: S2 == S3 (Manual 1 §6, Manual 9 §6.2, Manual 9 §2.3).
    # El cálculo del sello vive en un solo lugar: el oráculo del ME r252, que
    # también usa el job `bootstrap` de CI. Antes había una copia aquí y otra
    # en el workflow, así que el sello podía divergir sin que nadie lo notara.
    sello = os.path.join(RAIZ, "auditoria", "oraculos",
                         "oraculo_r252_paridad_bootstrap.py")
    # cumple Manual 9 §2.3: verificar el bootstrap como paso del pipeline
    # cumple Manual 1 §6: un bootstrap no determinista aborta el build
    # cumple Manual 1 §6 (ME r270b, H-R252-5): `--sellar` certifica el hash del
    # contenido de la fuente, de modo que un `touch` o un checkout posterior no
    # invalide la etapa 2 con el mismo contenido.
    # cumple Manual 9 §6.2: el build verifica y sella el bootstrap en cada corrida.
    rc_sello = subprocess.call([py, sello, "--artefactos", "--sellar"], cwd=RAIZ)
    if rc_sello != 0:
        print("[build][ERROR] sello de bootstrap S2==S3 NO verificado "
              "(Manual 1 §6 / Manual 9 §6.2)", file=sys.stderr)
        sys.exit(rc_sello)
    print(f"[build] OK determinismo S2==S3 sha "
          f"{_sha256(os.path.join(RAIZ, 'synapse_stage2.exe'))[:12]}")


if __name__ == "__main__":
    main()
