# tests/e2e/test_smoke_usuario_final.py
# Arnes de certificacion de usuario final (ME r234_certificacion_usuario_final).
# OBL-R234-R1 | Manual 9 §7 | la suite de humo opera sobre los binarios de
#   `dist/bin` sin depender de Python en el PATH | e2e | TDD
# OBL-R234-R2 | Manual 7 §7.3 | OpenSyn reporta su estado local (servidor y
#   modelo en 127.0.0.1, sin servicio externo configurado) | e2e | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo:
   .venv/Scripts/python.exe -m pytest tests/e2e/test_smoke_usuario_final.py -v
2. El arnes usa SOLO los binarios de `dist/bin` (synapse.exe, opensyn.exe,
   synapse_lsp.exe), como los usaria un usuario final: no invoca main.py ni
   importa modulos del compilador.
3. Los chequeos de autonomia ejecutan los binarios con un PATH reducido a
   System32 + dist/bin, demostrando que no dependen de Python.
4. La compilacion nativa requiere `gcc` (toolchain del repo o del sistema);
   si falta, el test falla con un mensaje explicito: es el hallazgo H-R234-1.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.skipif(
    sys.platform != "win32", reason="certificacion de usuario final Windows")]

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "dist" / "bin"
SYNAPSE = BIN / "synapse.exe"
OPENSYN = BIN / "opensyn.exe"
LSP = BIN / "synapse_lsp.exe"

TOOLCHAIN = RAIZ / "toolchain_gcc12" / "mingw64" / "bin"

SALIDA_CERT = RAIZ / "build" / "r234_certificacion"


def _entorno(limpio: bool) -> dict:
    """PATH sin Python para los chequeos de autonomia (H-R234-1)."""
    env = dict(os.environ)
    system32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    if limpio:
        env["PATH"] = os.pathsep.join([str(BIN), str(system32)])
    else:
        env["PATH"] = os.pathsep.join(
            [str(TOOLCHAIN), str(BIN), str(system32)])
    return env


def _ejecutar(cmd, timeout=300, limpio=False):
    return subprocess.run(
        [str(c) for c in cmd], capture_output=True, text=True,
        timeout=timeout, env=_entorno(limpio), cwd=RAIZ,
        encoding="utf-8", errors="replace",
    )


def _exigir_gcc():
    if not (TOOLCHAIN / "gcc.exe").exists() and not _hay_gcc_en_sistema():
        pytest.fail(
            "H-R234-1: no hay 'gcc' disponible para la compilacion nativa. "
            "El binario dist/bin/synapse.exe lo busca en el PATH y no resuelve "
            f"el toolchain del repo ({TOOLCHAIN}).")


def _hay_gcc_en_sistema() -> bool:
    for base in os.environ.get("PATH", "").split(os.pathsep):
        if base and (Path(base) / "gcc.exe").exists():
            return True
    return False


@pytest.fixture(scope="module")
def salida():
    SALIDA_CERT.mkdir(parents=True, exist_ok=True)
    return SALIDA_CERT


def test_binarios_de_usuario_final_presentes():
    """Los tres binarios que recibe el usuario existen en `dist/bin`."""
    for exe in (SYNAPSE, OPENSYN, LSP):
        assert exe.exists(), f"Falta el binario de usuario final: {exe}"


def test_synapse_version_sin_python_ni_gcc():
    """Manual 9 §7: `synapse --version` responde con PATH sin Python ni GCC."""
    p = _ejecutar([SYNAPSE, "--version"], limpio=True)
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout} {p.stderr}"
    assert "Synapse Compiler" in p.stdout, p.stdout


def test_synapse_check_sin_python_ni_gcc():
    """Manual 9 §7: la validacion (`check`) es autonoma del entorno Python."""
    p = _ejecutar([SYNAPSE, "check", RAIZ / "tests" / "e2e" / "e2e_hola.syn"],
                  limpio=True)
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout} {p.stderr}"
    # `check` reporta el pipeline por stderr y el veredicto final ahi tambien.
    assert "validacion exitosa" in (p.stdout + p.stderr), p.stdout + p.stderr


def test_compila_y_ejecuta_synapse(salida):
    """Manual 9 §7: `synapse <archivo.syn>` produce un ejecutable que corre."""
    _exigir_gcc()
    exe = salida / "hola_certificacion.exe"
    if exe.exists():
        exe.unlink()
    p = _ejecutar([SYNAPSE, RAIZ / "tests" / "e2e" / "e2e_hola.syn",
                   "-o", exe])
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-1500:]} {p.stderr[-1500:]}"
    assert exe.exists(), "El compilador no genero el ejecutable"
    r = subprocess.run([str(exe)], capture_output=True, text=True, timeout=120,
                       encoding="utf-8", errors="replace")
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout} {r.stderr}"
    assert "Hola Mundo" in r.stdout, r.stdout


def test_compila_y_ejecuta_syquex(salida):
    """Manual 9 §7: el frontend Syquex compila y ejecuta con el mismo binario."""
    _exigir_gcc()
    exe = salida / "syquex_certificacion.exe"
    if exe.exists():
        exe.unlink()
    p = _ejecutar([SYNAPSE, RAIZ / "examples" / "syquex" / "04_resultado.syq",
                   "-o", exe])
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-1500:]} {p.stderr[-1500:]}"
    assert exe.exists(), "El compilador no genero el ejecutable Syquex"
    r = subprocess.run([str(exe)], capture_output=True, text=True, timeout=120,
                       encoding="utf-8", errors="replace")
    assert r.returncode == 0, f"rc={r.returncode}: {r.stdout} {r.stderr}"
    assert "10/3 = 3" in r.stdout, r.stdout
    assert "Error" in r.stdout, r.stdout


def test_opensyn_cli_version_y_estado_local():
    """Manual 9 §7 + Manual 7 §7.3: OpenSyn arranca y reporta estado local."""
    v = _ejecutar([OPENSYN, "--version"], limpio=True)
    assert v.returncode == 0, f"rc={v.returncode}: {v.stdout} {v.stderr}"
    assert "OpenSyn" in v.stdout, v.stdout

    s = _ejecutar([OPENSYN, "status"], limpio=True)
    assert s.returncode == 0, f"rc={s.returncode}: {s.stdout} {s.stderr}"
    assert "Servidor IA" in s.stdout, s.stdout
    assert "Modelo IA" in s.stdout, s.stdout
    # 127.0.0.1 (o un modelo local) => inferencia local, sin servicio remoto.
    assert "http://" not in s.stdout.replace("http://127.0.0.1", ""), s.stdout


def test_lsp_nativo_responde_initialize():
    """Manual 9 §7: el LSP nativo responde `initialize` (base del .vsix)."""
    mensaje = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"processId": None, "rootUri": None, "capabilities": {}},
    }).encode("utf-8")
    proc = subprocess.Popen(
        [str(LSP)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, cwd=RAIZ,
    )
    try:
        proc.stdin.write(
            f"Content-Length: {len(mensaje)}\r\n\r\n".encode() + mensaje)
        proc.stdin.flush()
        time.sleep(1.5)
        proc.stdin.close()
        salido = proc.stdout.read()
    finally:
        proc.kill()
        proc.wait(timeout=10)
    assert b"Content-Length" in salido, salido[:400]
    assert b'"capabilities"' in salido, salido[:400]
    assert b"synapse-lsp-native" in salido, salido[:400]
