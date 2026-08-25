"""
test_ast_abi.py — Fase 22.B (ROADMAP): definición formal del SemNodo ABI v1.

Manual 6 §1.1-§1.2 (AST canónico unificado, política de congelado) y
Manual 2 §7.3 (AST aplanado). Verifica:

  1. `nucleo/ast_abi.syn` existe, declara AST_ABI_VERSION=1 y
     AST_ABI_MAX_NODOS=65536 (capacidad del SemNodo[], Manual 2 §7.3).
  2. Las funciones públicas llevan contratos requiere/garantiza
     (regla 4 de la auditoría / Manual 2 §12).
  3. La tabla canónica embebida en ast_abi.syn coincide EXACTAMENTE con la
     numeración vigente de `nucleo/parser_constantes.syn`
     (fuente única de verdad del toolchain).
  4. E2E nativo: el driver tests/fixtures/test_ast_abi.syn compila con el S1,
     imprime ABI_OK:0 y retorna rc=0.
"""

import os
import re
import subprocess
import sys

import pytest

pytestmark = pytest.mark.unit

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ABI_PATH = os.path.join(PROJECT_ROOT, "nucleo", "ast_abi.syn")
CONSTS_PATH = os.path.join(PROJECT_ROOT, "nucleo", "parser_constantes.syn")
FIXTURE = os.path.join(PROJECT_ROOT, "tests", "fixtures", "test_ast_abi.syn")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _find_gcc() -> str:
    candidates = [
        os.path.join(PROJECT_ROOT, "toolchain_gcc12", "mingw64", "bin"),
        "",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return ""


def test_archivo_y_constantes_de_version():
    src = _read(ABI_PATH)
    assert re.search(r"^constante AST_ABI_VERSION = 1\b", src, re.M), \
        "AST_ABI_VERSION=1 ausente"
    assert re.search(r"^constante AST_ABI_MAX_NODOS = 65536\b", src, re.M), \
        "AST_ABI_MAX_NODOS ausente (Manual 2 §7.3)"
    # Política de ABI documentada (Manual 6 §1.2)
    assert "ABI v1" in src and "CONGELADA" in src.upper()


def test_contratos_en_funciones_publicas():
    """Regla 4 de auditoría: funciones públicas con requiere/garantiza."""
    src = _read(ABI_PATH)
    for fn in ("ast_abi_verificar", "ast_abi_version"):
        m = re.search(
            rf"funcion {fn}\(\) -> entero:\s*\n\s*requiere:\s*\n.*?garantiza:",
            src, re.S)
        assert m, f"{fn} sin bloque requiere/garantiza"


def _tabla_canonica() -> dict:
    """Tabla esperada embebida en ast_abi.syn: NODO_X != <n> → valor n."""
    src = _read(ABI_PATH)
    return {
        nombre: int(valor)
        for nombre, valor in re.findall(
            r"si (NODO_[A-Z0-9_]+) != (\d+):", src)
    }


def test_tabla_coincide_con_parser_constantes():
    """Fuente única de verdad: parser_constantes.syn debe coincidir 1:1."""
    esperados = _tabla_canonica()
    assert len(esperados) >= 50, f"tabla ABI incompleta ({len(esperados)})"

    consts = dict(re.findall(
        r"^constante (NODO_[A-Z0-9_]+) = (\d+)$",
        _read(CONSTS_PATH), re.M))
    consts = {k: int(v) for k, v in consts.items()}

    faltantes = set(esperados) - set(consts)
    assert not faltantes, f"nodos en ABI ausentes en parser_constantes: {faltantes}"
    divergencias = {
        k: (esperados[k], consts[k])
        for k in esperados if consts[k] != esperados[k]
    }
    assert not divergencias, f"divergencias ABI vs toolchain: {divergencias}"


@pytest.mark.skipif(not os.path.exists(
    os.path.join(PROJECT_ROOT, "main.py")), reason="S1 no disponible")
def test_e2e_nativo_abi_ok():
    """Concatena módulo+driver en nucleo/ (para que dir_base resuelva
    `importar parser_constantes`) y compila con el S1."""
    import tempfile
    modulo = _read(ABI_PATH)
    driver = _read(FIXTURE)
    lineas_mod = [l for l in modulo.splitlines() if not l.startswith("#lang")]
    combinado = driver.rstrip("\n") + "\n\n" + "\n".join(lineas_mod) + "\n"

    nucleo_dir = os.path.join(PROJECT_ROOT, "nucleo")
    drv = os.path.join(nucleo_dir, "_tmp_ast_abi_drv.syn")
    try:
        with open(drv, "w", encoding="utf-8") as f:
            f.write(combinado)
        r = subprocess.run(
            [sys.executable, os.path.join(PROJECT_ROOT, "main.py"), drv],
            capture_output=True, text=True, timeout=900, cwd=PROJECT_ROOT)
        assert r.returncode == 0, \
            f"build rc={r.returncode}\n{r.stdout[-1500:]}\n{r.stderr[-500:]}"
        exe = drv[:-4] + ".exe"
        assert os.path.exists(exe), "S1 no generó el ejecutable"
        e = subprocess.run([exe], capture_output=True, text=True, timeout=120)
    finally:
        for ext in ("", ".c", ".exe", ".syn.json"):
            p = drv[:-4] + ext
            if os.path.exists(p):
                os.remove(p)
    assert e.returncode == 0, f"run rc={e.returncode}\n{e.stdout}\n{e.stderr}"
    assert "ABI_OK:0" in e.stdout, f"sin ABI_OK:0:\n{e.stdout}"
    assert "AST_ABI_VERSION=1" in e.stdout
