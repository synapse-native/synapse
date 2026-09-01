# -*- coding: utf-8 -*-
"""
tests/opensyn/test_installer.py — opensyn/installer.syn implementa instalacion.
Manual 7 §2.3 / Manual 9 §5.2-5.4 / F29. TDD GREEN (ME_29_T5).
cumple Manual 7 §2.3
cumple Manual 8 §1.2 (entry point: main.py no pipeline.py)
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.opensyn

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FIXTURES = os.path.join(RAIZ, 'tests', 'fixtures')


def _compilar_syq(nombre):
    fuente = os.path.join(RAIZ, nombre)
    nombre_base = os.path.basename(nombre).rsplit('.', 1)[0] + '.exe'
    out = os.path.join(RAIZ, 'tests', 'fixtures', nombre_base)
    # cumple Manual 8 §1.2: entry point es main.py (cli.py delega a pipeline.ejecutar_compilador)
    # pipeline.py no tiene __main__ → debe usarse main.py como entry point
    cmd = [sys.executable, 'main.py', fuente, '--output', out]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=120,
        encoding='utf-8', errors='replace', cwd=RAIZ,
    )
    return proc.returncode, proc.stdout + proc.stderr, out


def test_installer_opensyn():
    """M7 §2.3: opensyn/installer.syn compila y ejecuta."""
    rc, out, exe = _compilar_syq('opensyn/installer.syn')
    assert rc == 0, f"opensyn/installer.syn no compiló (rc={rc}): {out[-500:]}"
    assert os.path.exists(exe) and os.path.getsize(exe) > 0
    proc = subprocess.run(
        [exe], capture_output=True, text=True, timeout=10,
        encoding='utf-8', errors='replace',
    )
    assert proc.returncode == 0, f"Ejecución falló: {proc.stderr[-200:]}"
    assert 'Hardware:' in proc.stdout, f"Sin Hardware en salida: {proc.stdout}"
    assert 'Modelo:' in proc.stdout, f"Sin Modelo en salida: {proc.stdout}"
    assert 'Hilos:' in proc.stdout, f"Sin Hilos en salida: {proc.stdout}"
    assert 'Capas GPU:' in proc.stdout, f"Sin Capas GPU en salida: {proc.stdout}"
