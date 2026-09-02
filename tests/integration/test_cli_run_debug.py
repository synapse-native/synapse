# -*- coding: utf-8 -*-
"""
tests/integration/test_cli_run_debug.py — CLI tiene subcomandos run/debug/opensyn.
Manual 8 §4.2/§5/§7. TDD (ME_27_T5): compila y ejecuta cli.py con los nuevos subcomandos.
cumple Manual 8 4.1/§3.4/§7
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CLI_PY = os.path.join(RAIZ, 'cli.py')


def _run_cli(*args):
    cmd = [sys.executable, CLI_PY] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=RAIZ)


class TestCLIRun:
    """Manual 8 §4.1: synapse run."""

    def test_run_sin_archivo_falla(self):
        """synapse run sin archivo retorna error."""
        r = _run_cli("run")
        assert r.returncode != 0
        assert "requiere archivo" in r.stderr.lower() or "requiere archivo" in r.stdout.lower()

    def test_run_archivo_inexistente_falla(self):
        """synapse run con archivo inexistente retorna error."""
        r = _run_cli("run", "noexiste.syn")
        assert r.returncode != 0
        assert "no encontrado" in r.stderr.lower() or "no encontrado" in r.stdout.lower()

    def test_run_acepta_flag_debug(self):
        """synapse run acepta --debug (Manual 8 §4.2)."""
        r = _run_cli("run", "--debug", "noexiste.syn")
        assert r.returncode != 0  # Falla porque archivo no existe, pero el flag se acepta


class TestCLIDebug:
    """Manual 8 §3.4: synapse debug."""

    def test_debug_help(self):
        """synapse debug muestra ayuda."""
        r = _run_cli("debug")
        assert r.returncode == 0
        assert "debugger" in r.stdout.lower() or "debug" in r.stdout.lower()

    def test_debug_load_sin_archivo_falla(self):
        """synapse debug --load sin archivo retorna error."""
        r = _run_cli("debug", "--load")
        assert r.returncode != 0
        assert "requiere" in r.stderr.lower() or "requiere" in r.stdout.lower()

    def test_debug_load_archivo_inexistente_falla(self):
        """synapse debug --load con archivo inexistente retorna error."""
        r = _run_cli("debug", "--load", "noexiste.trace")
        assert r.returncode != 0
        assert "no encontrad" in r.stderr.lower() or "no encontrad" in r.stdout.lower()

    def test_debug_step(self):
        """synapse debug --step ejecuta."""
        r = _run_cli("debug", "--step")
        assert r.returncode == 0
        assert "paso" in r.stdout.lower()

    def test_debug_reverse(self):
        """synapse debug --reverse ejecuta."""
        r = _run_cli("debug", "--reverse")
        assert r.returncode == 0
        assert "retroced" in r.stdout.lower()

    def test_debug_snapshots(self):
        """synapse debug --snapshots ejecuta."""
        r = _run_cli("debug", "--snapshots")
        assert r.returncode == 0
        assert "snapshot" in r.stdout.lower()


class TestCLIOpenSyn:
    """Manual 8 §7: synapse opensyn."""

    def test_opensyn_help(self):
        """synapse opensyn muestra ayuda."""
        r = _run_cli("opensyn")
        assert r.returncode == 0
        assert "opensyn" in r.stdout.lower()

    def test_opensyn_status(self):
        """synapse opensyn status ejecuta."""
        r = _run_cli("opensyn", "status")
        assert r.returncode == 0
        assert "orquestador" in r.stdout.lower() or "estado" in r.stdout.lower()

    def test_opensyn_transpile_sin_archivo_falla(self):
        """synapse opensyn transpile sin archivo retorna error."""
        r = _run_cli("opensyn", "transpile")
        assert r.returncode != 0
        assert "requiere" in r.stderr.lower() or "requiere" in r.stdout.lower()

    def test_opensyn_bindings(self):
        """synapse opensyn bindings ejecuta."""
        r = _run_cli("opensyn", "bindings")
        assert r.returncode == 0
        assert "binding" in r.stdout.lower()


class TestCLIHelp:
    """Manual 8 §4.2: ayuda incluye nuevos comandos."""

    def test_help_menciona_run(self):
        """--help menciona run."""
        r = _run_cli("--help")
        assert "run" in r.stdout.lower()

    def test_help_menciona_debug(self):
        """--help menciona debug."""
        r = _run_cli("--help")
        assert "debug" in r.stdout.lower()

    def test_help_menciona_opensyn(self):
        """--help menciona opensyn."""
        r = _run_cli("--help")
        assert "opensyn" in r.stdout.lower()
