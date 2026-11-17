# tests/auditoria/test_oraculos_r237_instalador_toolchain.py
# Oraculo del ME r237 (H-R234-2): el instalador de Windows empaqueta el toolchain
# C para que una VM limpia compile sin que el usuario instale MinGW.
# OBL-R237-R1 | Manual 9 §2.5 | el .iss declara el componente `toolchain` y copia
#   dist\toolchain_gcc12\mingw64 a {app}\toolchain_gcc12\mingw64 | auditoria | TDD
# OBL-R237-R2 | Manual 9 §7 | el subset staged compila y linkea un C real, y
#   synapse.exe instalado compila un .syn con el toolchain incluido | auditoria | TDD
"""Requisitos:
1. Ejecutar desde la raiz del repo:
   .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r237_instalador_toolchain.py -v
2. El staging usa el toolchain del arbol (toolchain_gcc12/mingw64) igual que el
   pipeline de release: `instaladores/windows/empaquetar_toolchain.py`.
3. La compilacion de .syn usa SOLO `dist/bin/synapse.exe` con PATH reducido a
   System32, en un layout `{app}\\bin` + `{app}\\toolchain_gcc12` que replica el
   instalador.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
SYNAPSE = RAIZ / "dist" / "bin" / "synapse.exe"
TOOLCHAIN = RAIZ / "toolchain_gcc12" / "mingw64"
ISS = RAIZ / "instaladores" / "windows" / "synapse.iss"
PS1 = RAIZ / "instaladores" / "windows" / "scripts" / "install.ps1"
FUENTE = RAIZ / "tests" / "e2e" / "e2e_hola.syn"
SYSTEM32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"

sys.path.insert(0, str(RAIZ / "instaladores" / "windows"))
import empaquetar_toolchain as et  # noqa: E402

pytestmark = pytest.mark.skipif(
    sys.platform != "win32" or not (TOOLCHAIN / "bin" / "gcc.exe").exists(),
    reason="staging del toolchain MinGW (Windows + toolchain_gcc12)")


@pytest.fixture(scope="module")
def staged(tmp_path_factory):
    """Staging real del subset, igual que el pipeline de release."""
    destino = tmp_path_factory.mktemp("instalador") / "mingw64"
    et.empaquetar(str(TOOLCHAIN), str(destino))
    return destino


def test_subset_minimo_esta_completo(staged):
    """OBL-R237-R2: el subset incluye compilador, ensamblador, linker y headers."""
    triple = next(p.name for p in (staged / "lib" / "gcc").iterdir() if p.is_dir())
    version = next(p.name for p in (staged / "lib" / "gcc" / triple).iterdir())
    obligatorios = [
        staged / "bin" / "gcc.exe",
        staged / "bin" / "as.exe",
        staged / "bin" / "ld.exe",
        staged / "libexec" / "gcc" / triple / version / "collect2.exe",
        staged / "libexec" / "gcc" / triple / version / "cc1.exe",
        staged / "libexec" / "gcc" / triple / version / "liblto_plugin.dll",
        staged / "x86_64-w64-mingw32" / "include" / "stdio.h",
        staged / "x86_64-w64-mingw32" / "lib" / "libmingwex.a",
    ]
    faltan = [str(p.relative_to(staged)) for p in obligatorios if not p.exists()]
    assert not faltan, "el subset staged no es autosuficiente, faltan: %s" % faltan


def test_subset_minimo_compila_y_ejecuta(staged):
    """OBL-R237-R2: gcc staged compila y linkea con PATH = bin staged + System32."""
    salida = et.verificar(str(staged))
    assert "toolchain ok" in salida


def test_synapse_instalado_compila_con_toolchain_incluido(staged, tmp_path):
    """OBL-R237-R2: layout del instalador ({app}\\bin + {app}\\toolchain_gcc12)."""
    if not SYNAPSE.exists():
        pytest.skip("falta dist/bin/synapse.exe (compilar con main.py)")
    app = tmp_path / "Synapse"
    (app / "bin").mkdir(parents=True)
    shutil.copy2(SYNAPSE, app / "bin" / "synapse.exe")
    shutil.copytree(staged, app / "toolchain_gcc12" / "mingw64")

    exe = tmp_path / "instalado.exe"
    env = {k: v for k, v in os.environ.items()
           if k.upper() not in ("SYNAPSE_GCC", "PATH", "CPATH")}
    env["PATH"] = str(SYSTEM32)  # sin ningun gcc visible
    p = subprocess.run([str(app / "bin" / "synapse.exe"), str(FUENTE), "-o", str(exe)],
                       capture_output=True, text=True, env=env, cwd=RAIZ,
                       encoding="utf-8", errors="replace", timeout=900)
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-800:]} {p.stderr[-800:]}"
    assert "Compilacion nativa exitosa" in (p.stdout + p.stderr), p.stderr[-800:]
    assert exe.exists(), "no se genero el ejecutable"
    r = subprocess.run([str(exe)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode == 0 and "Hola Mundo" in r.stdout, r.stdout + r.stderr


def test_iss_declara_componente_y_destino():
    """OBL-R237-R1: componente `toolchain` + [Files] hacia {app}\\toolchain_gcc12\\mingw64."""
    iss = ISS.read_text(encoding="utf-8", errors="replace")
    assert 'Name: "toolchain"' in iss, "falta el componente toolchain en [Components]"
    assert 'DestDir: "{app}\\toolchain_gcc12\\mingw64"' in iss, (
        "el [Files] del toolchain debe instalar en {app}\\toolchain_gcc12\\mingw64 "
        "(el directorio que resuelve nucleo/principal.syn desde {app}\\bin)")
    assert "dist\\toolchain_gcc12\\mingw64" in iss, "el Source debe ser el staging dist/"
    assert "Components: toolchain" in iss
    ps1 = PS1.read_text(encoding="utf-8", errors="replace")
    assert "toolchain_gcc12\\mingw64\\bin\\gcc.exe" in ps1, (
        "install.ps1 debe verificar el toolchain incluido")
