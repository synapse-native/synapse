# tests/auditoria/test_oraculos_r236_toolchain_gcc.py
# Oraculo del ME r236 (H-R234-1): el compilador nativo resuelve el toolchain C
# por si mismo, sin depender de que `gcc` este en el PATH.
# OBL-R236-R1 | Manual 9 §7 | instalacion limpia: el binario compila con el
#   toolchain resuelto por el propio ejecutable | auditoria | TDD
# OBL-R236-R2 | Manual 9 §6.2 | la suite de tests valida la resolucion en el
#   layout del checkout y en el de instalacion, con PATH sin gcc | auditoria | TDD
"""
Requisitos:
1. Ejecutar desde la raiz del repo:
   .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r236_toolchain_gcc.py -v
2. Las pruebas usan SOLO `dist/bin/synapse.exe` (binario de usuario final) con un
   PATH reducido a System32: ningun `gcc` visible.
3. `SYNAPSE_GCC` tiene prioridad sobre la busqueda por cercania (se verifica con
   una ruta inexistente: la compilacion debe fallar en vez de usar el toolchain
   del arbol).
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="resolucion de toolchain MinGW (Windows)")

RAIZ = Path(__file__).resolve().parents[2]
SYNAPSE = RAIZ / "dist" / "bin" / "synapse.exe"
TOOLCHAIN = RAIZ / "toolchain_gcc12"
FUENTE = RAIZ / "tests" / "e2e" / "e2e_hola.syn"
SYSTEM32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"


def _env(path_extra=None, synapse_gcc=None):
    """Entorno con PATH sin gcc (solo System32), como una maquina recien instalada."""
    env = {k: v for k, v in os.environ.items()
           if k.upper() not in ("SYNAPSE_GCC", "PATH", "CPATH")}
    rutas = [str(SYSTEM32)]
    if path_extra:
        rutas = [str(path_extra), str(SYSTEM32)]
    env["PATH"] = os.pathsep.join(rutas)
    if synapse_gcc is not None:
        env["SYNAPSE_GCC"] = str(synapse_gcc)
    return env


def _requiere_binario():
    if not SYNAPSE.exists():
        pytest.skip("falta dist/bin/synapse.exe (compilar con main.py)")
    if not (TOOLCHAIN / "mingw64" / "bin" / "gcc.exe").exists():
        pytest.skip("falta toolchain_gcc12/mingw64/bin/gcc.exe en el arbol")


def _compilar(synapse, destino, env):
    return subprocess.run(
        [str(synapse), str(FUENTE), "-o", str(destino)],
        capture_output=True, text=True, env=env, cwd=RAIZ,
        encoding="utf-8", errors="replace", timeout=600)


def _verificar_ejecutable(exe):
    assert exe.exists(), "no se genero el ejecutable"
    r = subprocess.run([str(exe)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Hola Mundo" in r.stdout, r.stdout


def test_compila_con_path_sin_gcc(tmp_path):
    """OBL-R236-R1: layout del checkout (dist/bin) con PATH sin gcc."""
    _requiere_binario()
    exe = tmp_path / "sin_gcc.exe"
    p = _compilar(SYNAPSE, exe, _env())
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-800:]} {p.stderr[-800:]}"
    assert "Compilacion nativa exitosa" in (p.stdout + p.stderr), p.stderr[-800:]
    _verificar_ejecutable(exe)


def test_compila_en_layout_de_instalador(tmp_path):
    """OBL-R236-R2: bin/synapse.exe + ..\\toolchain_gcc12 (lo que instala el setup)."""
    _requiere_binario()
    instalacion = tmp_path / "Synapse"
    (instalacion / "bin").mkdir(parents=True)
    shutil.copy2(SYNAPSE, instalacion / "bin" / "synapse.exe")

    enlace = instalacion / "toolchain_gcc12"
    creacion = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(enlace), str(TOOLCHAIN)],
        capture_output=True, text=True,
        encoding="utf-8", errors="replace")
    if creacion.returncode != 0 or not (enlace / "mingw64" / "bin" / "gcc.exe").exists():
        pytest.skip(f"no se pudo crear el enlace de directorio: {creacion.stderr or creacion.stdout}")

    exe = tmp_path / "instalado.exe"
    p = _compilar(instalacion / "bin" / "synapse.exe", exe, _env())
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-800:]} {p.stderr[-800:]}"
    _verificar_ejecutable(exe)


def test_synapse_gcc_tiene_prioridad(tmp_path):
    """OBL-R236-R2: SYNAPSE_GCC manda; una ruta invalida no cae al toolchain del arbol."""
    _requiere_binario()
    exe = tmp_path / "prioridad.exe"
    p = _compilar(SYNAPSE, exe, _env(synapse_gcc=tmp_path / "no_existe_gcc.exe"))
    assert p.returncode != 0, (
        "SYNAPSE_GCC invalido deberia impedir la compilacion, no usar el "
        f"toolchain descubierto: {p.stdout[-400:]}")
    assert not exe.exists(), "no deberia haberse generado el ejecutable"
