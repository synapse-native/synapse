# tests/auditoria/test_oraculos_r242_opensyn_nativo.py
# Oraculo del ME r242_native_opensyn_cli: el binario distribuido expone
# `synapse opensyn <subcomando>` (Manual 8 §4.1) en vez de tratar el literal
# "opensyn" como archivo fuente.
# OBL-R242-R1 | Manual 8 §4.1 | despacho de los cinco subcomandos de OpenSyn en
#   el CLI nativo | auditoria | TDD
# OBL-R242-R2 | Manual 8 §4.2 | el subcomando nunca entra en la pipeline de
#   compilacion (no hay "Compilando archivo: opensyn") | auditoria | TDD
"""Requisitos:
1. Ejecutar desde la raiz del repo:
   .venv/Scripts/python.exe -m pytest tests/auditoria/test_oraculos_r242_opensyn_nativo.py -v
2. Las pruebas usan SOLO `dist/bin/synapse.exe` (binario de usuario final) y su
   companero `dist/bin/opensyn.exe`; no requieren red, servidor de inferencia ni
   modelo descargado.
3. `synapse opensyn status` debe devolver el estado REAL que reporta el binario
   OpenSyn nativo (delegacion), no un texto fijo inventado en el dispatcher.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
BIN = RAIZ / "dist" / "bin"
SYNAPSE = BIN / "synapse.exe"
OPENSYN = BIN / "opensyn.exe"

SUBCOMANDOS = {"status", "download", "finetune", "bindings", "transpile"}


def _requiere_binarios():
    if not SYNAPSE.exists():
        pytest.skip("falta dist/bin/synapse.exe (compilar con main.py)")
    if not OPENSYN.exists():
        pytest.skip("falta dist/bin/opensyn.exe (compilar con main.py)")


def _correr(*args, cwd=None):
    _requiere_binarios()
    return subprocess.run(
        [str(SYNAPSE), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(cwd or RAIZ), timeout=300)


def _salida(proc):
    return (proc.stdout or "") + (proc.stderr or "")


# OBL-R242-R1 | Manual 8 §4.1
def test_opensyn_help_lista_los_cinco_subcomandos():
    """`synapse opensyn --help` enumera status/download/finetune/bindings/transpile."""
    proc = _correr("opensyn", "--help")
    salida = _salida(proc)
    assert proc.returncode == 0, salida
    for sub in SUBCOMANDOS:
        assert f"opensyn {sub}" in salida, f"falta '{sub}' en la ayuda:\n{salida}"
    assert "Comandos OpenSyn" in salida


# OBL-R242-R1 | Manual 8 §4.1
def test_opensyn_sin_subcomando_muestra_ayuda():
    """`synapse opensyn` sin argumentos no compila nada: muestra la ayuda (rc=0)."""
    proc = _correr("opensyn")
    salida = _salida(proc)
    assert proc.returncode == 0, salida
    assert "opensyn status" in salida
    assert "Compilando archivo: opensyn" not in salida


# OBL-R242-R1 + R2 | Manual 8 §4.1, §4.2
def test_opensyn_status_delega_en_el_binario_nativo():
    """`synapse opensyn status` devuelve 0 y el estado real de OpenSyn."""
    proc = _correr("opensyn", "status")
    salida = _salida(proc)
    assert proc.returncode == 0, salida
    assert "Estado del Sistema" in salida, salida
    assert "OpenSyn:" in salida, salida
    # OBL-R242-R2: el subcomando ya NO cae en la pipeline de compilacion.
    assert "Compilando archivo: opensyn" not in salida, salida
    assert "Error de compilacion" not in salida, salida


# OBL-R242-R1 | Manual 8 §4.1
def test_opensyn_doctor_delega_en_el_binario_nativo():
    """`synapse opensyn doctor` ejecuta el diagnostico real (rc=0 sin fallos)."""
    proc = _correr("opensyn", "doctor")
    salida = _salida(proc)
    assert "Error de compilacion" not in salida, salida
    assert "Compilando archivo: opensyn" not in salida, salida
    assert proc.returncode in (0, 1), salida


# OBL-R242-R1 | Manual 8 §4.1
def test_opensyn_subcomando_desconocido_falla():
    """Subcomando inexistente: rc=1 y mensaje explicito, sin compilar nada."""
    proc = _correr("opensyn", "inexistente")
    salida = _salida(proc)
    assert proc.returncode == 1, salida
    assert "Subcomando OpenSyn desconocido: inexistente" in salida, salida
    assert "Error de compilacion" not in salida, salida


# OBL-R242-R1 | Manual 8 §4.1
def test_ayuda_global_menciona_opensyn():
    """`synapse --help` (Manual 8 §4.1: CLI unificado) lista el subcomando opensyn."""
    proc = _correr("--help")
    salida = _salida(proc)
    assert proc.returncode == 0, salida
    assert "opensyn" in salida, salida


# OBL-R242-R1 | Manual 8 §4.1
def test_paridad_de_subcomandos_con_el_cli_python():
    """El dispatcher nativo y cli.py declaran el MISMO juego de subcomandos."""
    cli = (RAIZ / "cli.py").read_text(encoding="utf-8", errors="replace")
    bloque = cli[cli.index("if subcommand == 'opensyn':"):]
    bloque = bloque[:bloque.index("if opensyn_subcmd == 'status':")]
    declarados = set(re.findall(r"synapse opensyn (\w+)", bloque))
    assert declarados == SUBCOMANDOS, declarados

    proc = _correr("opensyn", "--help")
    salida = _salida(proc)
    for sub in declarados:
        assert f"opensyn {sub}" in salida, f"el nativo no despacha '{sub}':\n{salida}"


# OBL-R242-R1 | Manual 8 §4.1
def test_opensyn_sin_binario_companero_falla_claro(tmp_path):
    """Sin opensyn.exe al lado, `status` no finge exito: rc=1 con error claro."""
    _requiere_binarios()
    solo = tmp_path / "synapse.exe"
    shutil.copy2(SYNAPSE, solo)
    proc = subprocess.run(
        [str(solo), "opensyn", "status"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(tmp_path), timeout=300)
    salida = _salida(proc)
    assert proc.returncode == 1, salida
    assert "opensyn.exe" in salida, salida
    assert "Error de compilacion" not in salida, salida


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-v"]))
