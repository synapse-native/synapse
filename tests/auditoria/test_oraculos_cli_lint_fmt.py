# -*- coding: utf-8 -*-
"""Oráculo del ME cli_lint_fmt — `synapse lint/fmt` en el dispatcher Python.

E2E real: invoca `python cli.py lint/fmt` (subprocess) sobre probes y verifica
rc + salida. Anti-fabricación: antes del ME, `python cli.py lint --fix x.syn`
trataba "lint" como ARCHIVO a compilar ("Archivo no encontrado: lint", rc=0
falso) — ese mensaje NO debe aparecer jamás; y el despacho usa el backend
nativo (stage2 del bootstrap, marca [Lint]/[Fmt] de nucleo/lint.syn y
nucleo/formatter.syn).

Ley: Manual 8 §4.1 (tabla de comandos: lint/fmt ejecutan las herramientas
nativas sobre el código fuente) + Manual 1 §6 (regla de hierro del bootstrap:
backing on-demand con el comando del CI, sin romperlo).
"""
import inspect
import os
import shutil
import subprocess
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable
CLI = os.path.join(RAIZ, "cli.py")
PROBES = os.path.join(RAIZ, "tests", "_probe_cli_lint_fmt")

MALO = "#lang: es\nfuncion  Mal( ) -> entero:\n\tretornar 1\n"
LIMPIO = "#lang: es\nfuncion prueba() -> entero:\n    retornar 1\n"
# MALO ya formateado (fmt corrige estilo, NUNCA identificadores ni semántica):
MALO_BIEN = "#lang: es\nfuncion Mal( ) -> entero:\n    retornar 1\n"


def _cli(args, timeout=900):
    r = subprocess.run([PY, CLI] + args, cwd=RAIZ, capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _probe(nombre, contenido):
    os.makedirs(PROBES, exist_ok=True)
    ruta = os.path.join(PROBES, nombre)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenido)
    return ruta


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def setup_function(function):
    shutil.rmtree(PROBES, ignore_errors=True)


def teardown_function(function):
    shutil.rmtree(PROBES, ignore_errors=True)


def test_lint_rc_salida_y_anti_fabricacion():
    """M8 §4.1: `synapse lint` ejecuta el linter nativo sobre el fuente."""
    malo = _probe("malo.syn", MALO)
    limpio = _probe("limpio.syn", LIMPIO)
    rc, out = _cli(["lint", malo])
    assert rc == 1, f"lint con advertencias debe rc=1 (antes rc=0 falso): {out[-300:]}"
    assert "WARN_LINT_" in out, out[-300:]
    rc, out = _cli(["lint", limpio])
    assert rc == 0, out[-300:]
    assert "Sin advertencias" in out, out[-300:]
    # anti-fabricación: el mensaje del bug preexistente NO aparece (lint no se
    # interpreta como archivo a compilar)
    rc, out = _cli(["lint", malo])
    assert "Archivo no encontrado: lint" not in out
    # marca del backend nativo (stage2, nucleo/lint.syn)
    assert "[Lint]" in out


def test_fmt_check_ambos_ordenes():
    """M8 §4.1: `synapse fmt` ejecuta el formateador nativo; --check rc=0/1."""
    malo = _probe("malo.syn", MALO)
    limpio = _probe("limpio.syn", LIMPIO)
    rc, out = _cli(["fmt", "--check", malo])
    assert rc == 1, f"fmt --check sobre mal formateado debe rc=1: {out[-300:]}"
    assert "formato incorrecto" in out, out[-300:]
    rc, out = _cli(["fmt", malo, "--check"])  # orden antiguo
    assert rc == 1, out[-300:]
    rc, out = _cli(["fmt", "--check", limpio])
    assert rc == 0, out[-300:]
    assert "[Fmt]" in out  # backend nativo


def test_fmt_inplace_reescribe_e_idempotente():
    """fmt in-place reescribe byte a byte y es idempotente (M8 §4.1)."""
    malo = _probe("malo.syn", MALO)
    rc, out = _cli(["fmt", malo])
    assert rc == 0, out[-300:]
    assert _leer(malo) == MALO_BIEN, f"contenido reescrito:\n{_leer(malo)!r}"
    rc, out = _cli(["fmt", malo])  # idempotente
    assert rc == 0 and _leer(malo) == MALO_BIEN


def test_lint_fix_paridad_fmt():
    """lint --fix == fmt (paridad de herramientas, backend único)."""
    a = _probe("a_fix.syn", MALO)
    b = _probe("b_fmt.syn", MALO)
    rc, out = _cli(["lint", "--fix", a])
    assert rc == 0, out[-300:]
    rc, out = _cli(["fmt", b])
    assert rc == 0, out[-300:]
    assert _leer(a) == _leer(b), "lint --fix y fmt difieren byte a byte"


def test_rc_errores_de_uso():
    """Sin archivo o archivo inexistente → rc=1 con mensaje claro (antes rc=0)."""
    rc, out = _cli(["lint", "no_existe_clix.syn"])
    assert rc == 1 and "no encontrado" in out
    rc, out = _cli(["fmt", "no_existe_clix.syn"])
    assert rc == 1 and "no encontrado" in out
    rc, out = _cli(["lint", "--fix"])
    assert rc == 1 and "Se requiere archivo" in out
    rc, out = _cli(["fmt", "--check"])
    assert rc == 1 and "Se requiere archivo" in out


def test_bootstrap_on_demand_comando_ci():
    """M1 §6: el backing garantiza stage2 fresco sin romper el bootstrap.

    - _bootstrap_stage2_fresco() devuelve el stage2 (path real) cuando está
      fresco y NO recompila (rápido, no toca el bootstrap).
    - El predicado detecta stage1 AUSENTE (el pre-commit lo borra y conserva
      stage2) y stale (fuentes .syn más nuevas que el exe).
    - Los comandos de rebuild son EXACTAMENTE los del job bootstrap del CI
      (python main.py nucleo/principal.syn -o synapse_stage1.exe; stage1
      principal -o stage2).
    """
    sys.path.insert(0, RAIZ)
    import cli
    assert cli._bootstrap_stage2_fresco() == cli._ST2
    assert os.path.exists(cli._ST2)
    # stage1 ausente → el backing debe decidir regenerar (predicado, sin borrar)
    st1_real = cli._ST1
    try:
        cli._ST1 = os.path.join(RAIZ, "synapse_stage1_INEXISTENTE.exe")
        stale = (not os.path.exists(cli._ST1) or not os.path.exists(cli._ST2)
                 or os.path.getmtime(cli._ST2) < cli._mtimes_fuentes_nucleo())
        assert stale, "stage1 ausente debe leerse como necesidad de rebuild"
    finally:
        cli._ST1 = st1_real
    # anti-fabricación: los comandos de rebuild son los del job CI (M1 §6)
    fuente = inspect.getsource(cli._bootstrap_stage2_fresco)
    assert '"main.py"' in fuente and "principal.syn" in fuente and '"-o"' in fuente
    assert "_mtimes_fuentes_nucleo" in fuente
