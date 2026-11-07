# -*- coding: utf-8 -*-
"""Oráculo del ME r200_opensyn_doctor.

Verifica que OpenSyn exponga `doctor` como prueba de humo accionable
(Manual 7 §6.1) y que el comando:
  1. figure en `--help` y en el dispatcher;
  2. pase en un layout instalado completo (bin/opensyn.exe + opensyn/ia +
     opensyn/models);
  3. falle de forma cerrada (rc=1) cuando falta llama-server, señalando el
     [FAIL] concreto.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PRINCIPAL = RAIZ / "opensyn" / "principal.syn"
EXE = RAIZ / "dist" / "bin" / "opensyn.exe"

FALLOS = []
TOTAL = 0


def chequeo(nombre, cond, detalle=""):
    global TOTAL
    TOTAL += 1
    print(("PASS" if cond else "FAIL") + " - " + nombre)
    if not cond and detalle:
        print("  -> " + detalle[-500:])
    if not cond:
        FALLOS.append(nombre)


def _run(exe, args, cwd):
    env = dict(os.environ)
    env.pop("OPENSN_TUI_TEST", None)
    return subprocess.run(
        [str(exe)] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
        env=env,
    )


def main():
    src = PRINCIPAL.read_text(encoding="utf-8")
    chequeo("funcion cmd_doctor con contrato", "funcion cmd_doctor() -> entero:" in src)
    chequeo("cita Manual 7 §6.1 en el diagnostico",
            "cumple Manual 7 §6.1" in src)
    chequeo("dispatcher atiende doctor/diagnostico",
            'si a1 == "doctor" o a1 == "diagnostico":' in src
            and "retornar cmd_doctor()" in src)
    chequeo("ayuda CLI expone opensyn doctor", "opensyn doctor" in src)
    chequeo("status sugiere doctor cuando falla la IA",
            'escribir_linea("    opensyn doctor")' in src)

    chequeo("binario dist/bin/opensyn.exe presente", EXE.exists())
    if not EXE.exists():
        print("OK: %d checks, %d FAIL" % (TOTAL, len(FALLOS)))
        return 1

    r = _run(EXE, ["--help"], RAIZ)
    chequeo("--help rc=0 e incluye doctor",
            r.returncode == 0 and "opensyn doctor" in r.stdout,
            r.stdout + r.stderr)

    tmp = Path(tempfile.mkdtemp(prefix="opensyn_r200_ok_"))
    try:
        bin_dir = tmp / "bin"
        ia_dir = tmp / "opensyn" / "ia"
        models_dir = tmp / "opensyn" / "models"
        bin_dir.mkdir()
        ia_dir.mkdir(parents=True)
        models_dir.mkdir(parents=True)
        exe = bin_dir / "opensyn.exe"
        shutil.copy2(EXE, exe)
        (ia_dir / "llama-server.exe").write_bytes(b"stub")
        (models_dir / "modelo-prueba.gguf").write_bytes(b"stub")

        r = _run(exe, ["doctor"], tmp)
        chequeo("layout completo: doctor rc=0", r.returncode == 0,
                r.stdout + r.stderr)
        chequeo("layout completo: reporta llama-server y modelo",
                "llama-server: " + str(ia_dir) in r.stdout
                and "Modelo GGUF: " + str(models_dir / "modelo-prueba.gguf") in r.stdout,
                r.stdout)
        chequeo("layout completo: resultado OK",
                "Resultado: OK" in r.stdout, r.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    tmp = Path(tempfile.mkdtemp(prefix="opensyn_r200_fail_"))
    try:
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        exe = bin_dir / "opensyn.exe"
        shutil.copy2(EXE, exe)
        r = _run(exe, ["doctor"], tmp)
        chequeo("sin runtime: doctor rc=1", r.returncode == 1,
                r.stdout + r.stderr)
        chequeo("sin runtime: identifica llama-server ausente",
                "llama-server.exe no encontrado" in r.stdout, r.stdout)
        chequeo("sin runtime: no declara exito",
                "Resultado: OK" not in r.stdout, r.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if FALLOS:
        print("FAIL: %d checks, %d FAIL" % (TOTAL, len(FALLOS)))
        return 1
    print("OK: %d checks, 0 FAIL" % TOTAL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
