# -*- coding: utf-8 -*-
"""
tests/opensyn/test_os_syn_hw.py — std/os.syn expone deteccion de hardware.
Manual 9 §5.7 / F29. TDD GREEN (ME_29_T4).
cumple Manual 9 §5.7
"""
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.opensyn

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FIXTURES = os.path.join(RAIZ, 'tests', 'fixtures')


def _compilar_syq(nombre):
    fuente = os.path.join(RAIZ, nombre) if nombre.startswith('std/') else os.path.join(FIXTURES, nombre)
    out = os.path.join(FIXTURES, nombre.replace('.syq', '.exe'))
    cmd = [sys.executable, 'pipeline.py', fuente, '--output', out]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=120,
        encoding='utf-8', errors='replace', cwd=RAIZ,
    )
    return proc.returncode, proc.stdout + proc.stderr, out


def test_os_syn_compila():
    """M9 §5.7: std/os.syn compila sin errores (módulo con externos C)."""
    rc, out, _ = _compilar_syq('std/os.syn')
    assert rc == 0, f"std/os.syn no compiló (rc={rc}): {out[-500:]}"


def test_os_syn_detect_hw_compila():
    """M9 §5.7: test_os_hw.syq compila (funciones inline, sin importar)."""
    rc, out, exe = _compilar_syq('test_os_hw.syq')
    assert rc == 0, f"test_os_hw.syq no compiló (rc={rc}): {out[-500:]}"
    assert os.path.exists(exe) and os.path.getsize(exe) > 0


def test_os_syn_ejecuta():
    """M9 §5.7: test_os_hw.syq ejecuta y produce salida."""
    rc, out, exe = _compilar_syq('test_os_hw.syq')
    assert rc == 0, f"Compilación falló: {out[-300:]}"
    proc = subprocess.run(
        [exe], capture_output=True, text=True, timeout=10,
        encoding='utf-8', errors='replace',
    )
    assert proc.returncode == 0, f"Ejecución falló: {proc.stderr[-200:]}"
    assert 'RAM:' in proc.stdout, f"Sin RAM en salida: {proc.stdout}"
    assert 'CPU:' in proc.stdout, f"Sin CPU en salida: {proc.stdout}"
    assert 'Arch:' in proc.stdout, f"Sin Arch en salida: {proc.stdout}"
