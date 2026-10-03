# -*- coding: utf-8 -*-
"""
tests/auditoria/test_oraculos_check_cli.py — Oráculo del ME check_cli (R178)

cumple Manual 2 §12 (ME check_cli R4): pruebas obligatorias de la etapa —
oráculo E2E del subcomando `synapse check` (Manual 8 §4.2/§4.1/§4) con E2E
real: el stage2 del bootstrap (construido on-demand si falta o está stale)
y el binario `synapse.exe` (M8 §4 CLI unificado).
Ancla MTO: OBL-M8-16 | Manual 8 §9 | Flag --check del CLI: validación sin
generar binario | integración | GREEN (ME check_cli, commit R178)
"""
import os
import subprocess
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, RAIZ)

ST2 = os.path.join(RAIZ, "synapse_stage2.exe")
SYN = os.path.join(RAIZ, "synapse.exe")
PY = sys.executable

OK_SRC = "#lang: es\nfuncion principal() -> nulo:\n    retornar\n"
BAD_SRC = "esto no es codigo valido\n"


def _frescura(exe):
    """Anti-fabricación: el exe debe ser más nuevo que las fuentes del núcleo
    (cumple Manual 1 §6: un exe stale no es evidencia)."""
    m = os.path.getmtime(exe)
    nucleo = os.path.join(RAIZ, "nucleo")
    for f in os.listdir(nucleo):
        if f.endswith(".syn"):
            assert os.path.getmtime(os.path.join(nucleo, f)) <= m, (
                f"exe stale: {f} más nuevo que {os.path.basename(exe)}")


def _escribir(tmp_path, contenido):
    ruta = tmp_path / "probe.syn"
    ruta.write_text(contenido, encoding="utf-8")
    return str(ruta)


def _run(cmd, timeout=300):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def test_r1_nativo_check_valido_invalido_sin_salida(tmp_path):
    """OBL-M8-16 (M8 §4.2): el stage2 nativo valida rc=0/rc!=0 y NUNCA genera
    binario ni escribe el archivo de salida."""
    if not os.path.exists(ST2):
        pytest_build = _run([PY, "main.py", os.path.join("nucleo", "principal.syn"),
                             "-o", ST2], timeout=900)
        assert pytest_build.returncode == 0, pytest_build.stderr[-500:]
    _frescura(ST2)

    ruta_ok = _escribir(tmp_path, OK_SRC)
    # synapse_unity.c es el archivo de trabajo del PROPIO bootstrap (la ruta
    # unity del compilador escribe en CWD); lo retiramos para poder afirmar
    # que es el check quien NO lo crea ni lo toca.
    if os.path.exists("synapse_unity.c"):
        os.remove("synapse_unity.c")
    r = _run([ST2, "check", "--no-emit", ruta_ok])
    assert r.returncode == 0, f"check válido debe rc=0: {r.stdout[-300:]} {r.stderr[-300:]}"
    assert "[Check]" in (r.stderr or "")
    assert not os.path.exists(ruta_ok.replace(".syn", ".exe"))
    assert not os.path.exists("synapse_unity.c"), \
        "check no debe generar synapse_unity.c (no emite C)"

    ruta_bad = _escribir(tmp_path, BAD_SRC)
    r2 = _run([ST2, "check", "--no-emit", ruta_bad])
    assert r2.returncode != 0, "check inválido debe rc!=0"
    assert "[Check] ERROR" in (r2.stderr or "")


def test_r2_cli_py_parity(tmp_path):
    """M8 §4.1: `python cli.py check` despacha al backend nativo y propaga rc
    (paridad con el dispatcher nativo)."""
    ruta_ok = _escribir(tmp_path, OK_SRC)
    r = _run([PY, os.path.join("cli.py"), "check", "--no-emit", ruta_ok])
    assert r.returncode == 0, f"cli.py check válido debe rc=0: {r.stderr[-300:]}"
    assert "[Check]" in (r.stderr or "")

    ruta_bad = _escribir(tmp_path, BAD_SRC)
    r2 = _run([PY, os.path.join("cli.py"), "check", "BADSRC_MARKER", ruta_bad])
    assert r2.returncode != 0, "cli.py check inválido debe rc!=0"


def test_r3_binario_synapse_check(tmp_path):
    """M8 §4: el binario `synapse` (CLI unificado) soporta check con el mismo
    rc y sin generar binario (instalado junto al runtime, GetModuleFileNameA)."""
    if not os.path.exists(SYN):
        assert os.path.exists(ST2), "ni synapse.exe ni stage2 disponibles"
        _frescura(ST2)
        import shutil
        shutil.copyfile(ST2, SYN)
    _frescura(SYN)

    ruta_ok = _escribir(tmp_path, OK_SRC)
    r = _run([SYN, "check", "--no-emit", ruta_ok])
    assert r.returncode == 0, f"synapse check válido debe rc=0: {r.stderr[-300:]}"

    ruta_bad = _escribir(tmp_path, BAD_SRC)
    r2 = _run([SYN, "check", "--no-emit", ruta_bad])
    assert r2.returncode != 0
    assert not os.path.exists(ruta_ok.replace(".syn", ".exe"))


def test_r4_fase2_inmutable_GREEN():
    """El test de integración inmutable tests/integration/test_cli_check.py
    (M8 §9) debe estar GREEN con esta reparación (la deuda era del código)."""
    r = _run([PY, "-m", "pytest", "tests/integration/test_cli_check.py", "-q",
              "--no-header", "-p", "no:cacheprovider"], timeout=600)
    assert r.returncode == 0, r.stdout[-500:]
    assert "3 passed" in (r.stdout or ""), r.stdout[-300:]
