# -*- coding: utf-8 -*-
"""test_tool_ejecutar.py - ME r216: TOOL ejecutar de OpenSyn.

Oráculos de comportamiento REAL: los probes .syn se compilan con el pipeline S1
(`python main.py`) y se ejecutan como binarios.

Requisitos:
- Manual 32 §6.4: ejecución de subprocesos con timeout; un bucle infinito se
  termina y no bloquea al agente.
- Manual 7 §7.3: sandboxing y permisos mínimos; allowlist de comandos y rechazo
  de metacaracteres de shell, rutas absolutas y flags peligrosos.
- Manual 2 §5.1: contratos requiere/garantiza booleanos en funciones públicas.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

RAIZ = Path(__file__).resolve().parents[2]
PYTHON = sys.executable


PROBE_RECHAZOS = r'''#lang: es
importar std.io
importar std.texto
importar std.sistema
importar opensyn.herramientas

funcion principal() -> entero:
    escribir_linea(herramienta_ejecutar("git status; echo pwned"))
    escribir_linea(herramienta_ejecutar("pytest && echo pwned"))
    escribir_linea(herramienta_ejecutar("git diff --ext-diff"))
    escribir_linea(herramienta_ejecutar("pytest ../fuera.txt"))
    escribir_linea(herramienta_ejecutar("pytest C:\\Windows\\win.ini"))
    escribir_linea(herramienta_ejecutar("rm -rf /"))
    retornar 0
'''


PROBE_MODOS = r'''#lang: es
importar std.io
importar std.texto
importar std.sistema
importar opensyn.principal

funcion principal() -> entero:
    cwd = _syn_obtener_cwd()
    escribir_linea(ejecutar_tool_aprobado("TOOL ejecutar git status", _syn_strcpy(cwd), 0, 1))
    escribir_linea(ejecutar_tool_aprobado("TOOL ejecutar git status", _syn_strcpy(cwd), 2, 1))
    retornar 0
'''


PROBE_TIMEOUT = r'''#lang: es
importar std.io
importar std.texto
importar std.sistema
importar opensyn.herramientas

funcion principal() -> entero:
    escribir_linea(herramienta_ejecutar("pytest"))
    retornar 0
'''


def _compilar(fuente: str, nombre: str, td: Path) -> Path:
    """Compila con el pipeline real S1 y retorna el ejecutable."""
    src = td / f"{nombre}.syn"
    src.write_text(fuente, encoding="utf-8")
    exe = td / f"{nombre}.exe"
    p = subprocess.run(
        [str(PYTHON), str(RAIZ / "main.py"), str(src), "-o", str(exe)],
        capture_output=True, text=True, cwd=str(RAIZ), timeout=900,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, (
        f"Compilacion de {nombre} fallo: {p.stdout[-2000:]} {p.stderr[-2000:]}"
    )
    assert exe.exists(), f"El binario {nombre}.exe no fue generado"
    return exe


def _ejecutar(exe: Path, cwd: Path, env=None):
    return subprocess.run(
        [str(exe)], capture_output=True, text=True, cwd=str(cwd), timeout=120,
        encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, env=env,
    )


def _compilar_shim_pytest(td: Path) -> Path:
    """Compila un pytest.exe que duerme, para probar el timeout real."""
    gcc = shutil.which("gcc") or shutil.which("gcc.exe")
    if not gcc:
        pytest.skip("gcc no disponible para compilar el shim de timeout")
    if os.name == "nt":
        fuente = "#include <windows.h>\nint main(void) { Sleep(60000); return 0; }\n"
        exe = td / "pytest.exe"
    else:
        fuente = "#include <unistd.h>\nint main(void) { sleep(60); return 0; }\n"
        exe = td / "pytest"
    src = td / "shim_pytest.c"
    src.write_text(fuente, encoding="utf-8")
    p = subprocess.run(
        [gcc, "-O2", "-o", str(exe), str(src)],
        capture_output=True, text=True, timeout=120,
        encoding="utf-8", errors="replace",
    )
    assert p.returncode == 0, f"gcc fallo: {p.stdout} {p.stderr}"
    return exe


def test_fuente_declara_ejecutar_y_citas():
    """Manual 2 §5.1 / MTS: tool, timeout y citas en producción."""
    fuente = (RAIZ / "opensyn" / "herramientas.syn").read_text(encoding="utf-8")
    assert "funcion herramienta_ejecutar(" in fuente
    assert "HERR_EJECUTAR_TIMEOUT_MS" in fuente
    assert "Manual FASE 32 §6.4" in fuente
    assert "cumple Manual 7 §7.3" in fuente
    assert "cumple Manual 2 §5.1" in fuente
    principal = (RAIZ / "opensyn" / "principal.syn").read_text(encoding="utf-8")
    assert "TOOL ejecutar" in principal
    assert 'nombre == "ejecutar"' in principal
    assert "ejecutar" in (RAIZ / "opensyn" / "principal.syn").read_text(encoding="utf-8")


@pytest.mark.slow
@pytest.mark.timeout(900)
def test_e2e_allowlist_rechaza_inyeccion_y_rutas(tmp_path):
    """Manual 7 §7.3: shell, .., unidad absoluta y flags peligrosos se rechazan."""
    exe = _compilar(PROBE_RECHAZOS, "probe_ejecutar_rechazos", tmp_path)
    p = _ejecutar(exe, tmp_path)
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-500:]} {p.stderr[-300:]}"
    lineas = [l for l in p.stdout.splitlines() if l.strip()]
    assert len(lineas) == 6, f"salida inesperada: {p.stdout!r}"
    for linea in lineas:
        assert "[TOOL_ERROR] comando no permitido" in linea, linea


@pytest.mark.slow
@pytest.mark.timeout(900)
def test_e2e_modo_y_ejecucion_permitida(tmp_path):
    """Manual 7 §7.3: ASK deniega; Code ejecuta y reporta rc."""
    exe = _compilar(PROBE_MODOS, "probe_ejecutar_modos", tmp_path)
    p = _ejecutar(exe, tmp_path)
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-500:]} {p.stderr[-300:]}"
    lineas = [l for l in p.stdout.splitlines() if l.strip()]
    assert len(lineas) >= 2, f"salida inesperada: {p.stdout!r}"
    assert "no permitida" in lineas[0], lineas[0]
    assert "[TOOL_RESULT] rc=" in lineas[1], lineas[1]


@pytest.mark.slow
@pytest.mark.timeout(120)
def test_e2e_timeout_mata_bucle_infinito(tmp_path):
    """Manual 32 §6.4: un comando colgado se termina a los 5 s."""
    _compilar_shim_pytest(tmp_path)
    exe = _compilar(PROBE_TIMEOUT, "probe_ejecutar_timeout", tmp_path)
    env = os.environ.copy()
    env["PATH"] = str(tmp_path) + os.pathsep + env.get("PATH", "")
    p = _ejecutar(exe, tmp_path, env=env)
    assert p.returncode == 0, f"rc={p.returncode}: {p.stdout[-500:]} {p.stderr[-300:]}"
    assert "[TOOL_ERROR] timeout" in p.stdout, p.stdout
    assert "124" in p.stdout, p.stdout
