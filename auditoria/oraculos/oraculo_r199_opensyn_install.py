# -*- coding: utf-8 -*-
"""Oráculo del ME r199_opensyn_install.

Verifica:
  1. El orquestador resuelve el directorio real del binario y busca
     llama-server/*.gguf en el layout instalado (Manual 7 §2.1), sin rutas
     fijas C:\\Program Files\\Synapse.
  2. El modelo configurado se compara por nombre base (Manual 7 §4.2).
  3. La CLI responde --version/--help/status sin abrir la TUI.
  4. El instalador expone OpenSyn con WorkingDir={app} (Manual 9 §2.5) y el
     wrapper delega en opensyn.exe.
  5. E2E de layout: copia el exe a {tmp}\\bin, crea {tmp}\\opensyn\\models con
     un .gguf de prueba y comprueba que `status` descubre esa ruta.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
EXE = RAIZ / "dist" / "bin" / "opensyn.exe"
PRINCIPAL = RAIZ / "opensyn" / "principal.syn"
BAT = RAIZ / "opensyn" / "opensyn.bat"
ISS = RAIZ / "instaladores" / "windows" / "synapse.iss"

FALLOS = []
TOTAL = 0


def chequeo(nombre, cond, detalle=""):
    global TOTAL
    TOTAL += 1
    print(("PASS" if cond else "FAIL") + " - " + nombre)
    if not cond and detalle:
        print("  -> " + detalle[-400:])
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
        timeout=60,
        env=env,
    )


def main():
    src = PRINCIPAL.read_text(encoding="utf-8")
    chequeo("sin ruta fija C:\\Program Files\\Synapse",
            "C:\\Program Files\\Synapse" not in src)
    chequeo("directorio real del exe (GetModuleFileNameA)",
            "GetModuleFileNameA" in src and "funcion dir_opensyn" in src)
    chequeo("arranque no bloqueante (Start-Process oculto)",
            "Start-Process" in src and "-WindowStyle Hidden" in src
            and "start /WAIT" not in src)
    chequeo("readiness via API (no parser netstat)",
            "funcion llama_server_corriendo" in src
            and "_syn_ollama_modelos(\"127.0.0.1\", 8088)" in src)
    chequeo("busqueda del layout {app}\\opensyn",
            "funcion buscar_llama_server" in src
            and "funcion buscar_modelo_instalado" in src)
    chequeo("modelo por nombre base (config vs id del server)",
            "funcion nombre_base_ruta" in src
            and "funcion sin_extension_gguf" in src)
    chequeo("CLI --version/--help/status",
            '"--version"' in src and '"--help"' in src
            and "retornar cmd_status()" in src)

    bat = BAT.read_text(encoding="utf-8", errors="replace")
    chequeo("wrapper delega en opensyn.exe", "opensyn.exe" in bat and "%*" in bat)

    iss = ISS.read_text(encoding="utf-8", errors="replace")
    chequeo("instalador crea acceso OpenSyn con WorkingDir={app}",
            'OpenSyn (IA local)' in iss and 'WorkingDir: "{app}"' in iss)

    chequeo("binario dist/bin/opensyn.exe presente", EXE.exists())
    if not EXE.exists():
        print("OK: %d checks, %d FAIL" % (TOTAL, len(FALLOS)))
        return 1

    r = _run(EXE, ["--version"], RAIZ)
    chequeo("--version rc=0 y version correcta",
            r.returncode == 0 and "OpenSyn 1.1.0" in r.stdout,
            r.stdout + r.stderr)
    r = _run(EXE, ["--help"], RAIZ)
    chequeo("--help rc=0 y uso visible",
            r.returncode == 0 and "opensyn status" in r.stdout,
            r.stdout + r.stderr)

    tmp = Path(tempfile.mkdtemp(prefix="opensyn_r199_"))
    try:
        (tmp / "bin").mkdir()
        (tmp / "opensyn" / "ia").mkdir(parents=True)
        (tmp / "opensyn" / "models").mkdir()
        shutil.copy2(EXE, tmp / "bin" / "opensyn.exe")
        (tmp / "opensyn" / "ia" / "llama-server.exe").write_bytes(b"")
        (tmp / "opensyn" / "models" / "probe.gguf").write_bytes(b"GGUF")
        r = _run(tmp / "bin" / "opensyn.exe", ["status"], tmp.parent)
        chequeo("status resuelve {app}\\opensyn desde {app}\\bin",
                str(tmp / "opensyn") in r.stdout, r.stdout + r.stderr)
        chequeo("status descubre modelo en {app}\\opensyn\\models",
                "probe.gguf" in r.stdout, r.stdout + r.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("OK: %d checks ejecutados" % TOTAL)
    return 0 if not FALLOS else 1


if __name__ == "__main__":
    sys.exit(main())
