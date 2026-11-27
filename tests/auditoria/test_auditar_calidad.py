# -*- coding: utf-8 -*-
"""Self-test del auditor de calidad de tests (ME_Q2).

Manual 7 §2.3 / Manual 3 §12.1. Valida que el auditor detecta SNIFF y SIN_CITA
en fixtures aislados (no en el repo real, para no acoplar al deuda existente).
"""
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUD = os.path.join(REPO, "auditoria", "auditar_calidad_tests.py")


def _w(tmp_path, name, content):
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_detecta_sniff_y_no_falsa_alarma(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    # SNIFF: assert substring en artefacto sin ejecutar
    _w(d, "test_sniff.py", 'def test_foo():\n    c = "funcion suma"\n    assert "funcion" in c\n')
    # CLEAN: ejecuta el artefacto (subprocess) y cita Manual -> no SNIFF, no SIN_CITA
    _w(d, "test_clean.py",
       '# Manual 3 §3\n'
       'import subprocess\n'
       'def test_bar():\n'
       '    out = subprocess.run(["echo", "hi"], capture_output=True, text=True)\n'
       '    assert out.stdout.strip() == "hi"\n')
    r = subprocess.run([sys.executable, AUD, "--root", str(d)],
                       capture_output=True, text=True)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "[SNIFF] test_sniff.py" in r.stdout
    assert "[SNIFF] test_clean.py" not in r.stdout
    assert "[SIN_CITA] test_clean.py" not in r.stdout


def test_detecta_sin_cita(tmp_path):
    d = tmp_path / "sub2"
    d.mkdir()
    _w(d, "test_nocita.py", "def test_x():\n    assert True\n")
    r = subprocess.run([sys.executable, AUD, "--root", str(d)],
                       capture_output=True, text=True)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "[SIN_CITA] test_nocita.py" in r.stdout


def test_mto_valido(tmp_path):
    vacio = tmp_path / "vacio"
    vacio.mkdir()
    r = subprocess.run([sys.executable, AUD, "--root", str(vacio)],
                       capture_output=True, text=True)
    # sin tests -> solo valida MTO (debe ser valido -> rc=0)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "[MTO]" in r.stdout
