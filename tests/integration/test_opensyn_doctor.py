"""Tests del comando `opensyn doctor` (Manual 7 6.1 / 2.1).

El binario se compila con `python main.py opensyn/principal.syn -o
dist/bin/opensyn.exe`; si no existe se omite la prueba para no acoplar la suite
Python a un build nativo previo.
"""
import os
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
EXE = RAIZ / "dist" / "bin" / "opensyn.exe"


def _run(args, cwd, exe=EXE):
    return subprocess.run(
        [str(exe)] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )


@pytest.mark.skipif(not EXE.exists(), reason="requiere dist/bin/opensyn.exe compilado")
class TestOpenSynDoctor:
    def test_help_exposes_doctor(self):
        r = _run(["--help"], RAIZ)
        assert r.returncode == 0, r.stderr
        assert "opensyn doctor" in r.stdout

    def test_doctor_reports_actionable_diagnostic(self):
        r = _run(["doctor"], RAIZ)
        assert r.returncode in (0, 1), r.stderr
        assert "=== OpenSyn: Diagnostico ===" in r.stdout
        assert "[OK]" in r.stdout
        assert ("Resultado: OK" in r.stdout) or ("[FAIL]" in r.stdout)

    def test_doctor_passes_on_complete_layout(self, tmp_path):
        bin_dir = tmp_path / "bin"
        ia_dir = tmp_path / "opensyn" / "ia"
        models_dir = tmp_path / "opensyn" / "models"
        bin_dir.mkdir()
        ia_dir.mkdir(parents=True)
        models_dir.mkdir(parents=True)

        exe = bin_dir / "opensyn.exe"
        exe.write_bytes(EXE.read_bytes())
        (ia_dir / "llama-server.exe").write_bytes(b"stub")
        (models_dir / "modelo-prueba.gguf").write_bytes(b"stub")

        r = _run(["doctor"], tmp_path, exe=exe)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "Resultado: OK" in r.stdout
        assert "llama-server: " + str(ia_dir) in r.stdout
        assert "Modelo GGUF: " + str(models_dir / "modelo-prueba.gguf") in r.stdout

    def test_doctor_fails_closed_without_runtime(self, tmp_path):
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        exe = bin_dir / "opensyn.exe"
        exe.write_bytes(EXE.read_bytes())

        r = _run(["doctor"], tmp_path, exe=exe)
        assert r.returncode == 1, r.stdout + r.stderr
        assert "llama-server.exe no encontrado" in r.stdout
        assert "problema(s) critico(s)" in r.stdout
