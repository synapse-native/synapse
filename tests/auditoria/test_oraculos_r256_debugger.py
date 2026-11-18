# -*- coding: utf-8 -*-
"""Oráculo de ME r241/r256: CLI `synapse debug` (Manual 8 §3.4)."""
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def _binario():
    for cand in (RAIZ / "dist" / "bin" / "synapse.exe",
                 RAIZ / "synapse.exe",
                 RAIZ / "synapse_bootstrap.exe"):
        if cand.exists():
            return cand
    return None


def test_debug_help():
    bin_ = _binario()
    assert bin_ is not None, "no se encontro binario synapse"
    r = subprocess.run([str(bin_), "debug"], capture_output=True, text=True,
                       cwd=str(RAIZ), timeout=60)
    out = (r.stdout or "") + (r.stderr or "")
    assert "--load" in out and "--step" in out and "--reverse" in out
    assert "--snapshots" in out


def test_debug_snapshots():
    bin_ = _binario()
    assert bin_ is not None
    r = subprocess.run([str(bin_), "debug", "--snapshots"], capture_output=True,
                       text=True, cwd=str(RAIZ), timeout=60)
    out = (r.stdout or "") + (r.stderr or "")
    assert "eventos en traza" in out
    assert r.returncode == 0


def test_debug_load_traza():
    bin_ = _binario()
    assert bin_ is not None
    traza = RAIZ / ".synapse" / "traces"
    candidatas = list(traza.glob("*.trace")) if traza.exists() else []
    if not candidatas:
        # crear traza minima
        traza.mkdir(parents=True, exist_ok=True)
        p = traza / "oracle.trace"
        p.write_text("TRACE v1\nid=oracle\nprograma=oracle\n"
                     "eventos=0\ncapacidad=50000\n---\n", encoding="utf-8")
        candidatas = [p]
    r = subprocess.run([str(bin_), "debug", "--load", str(candidatas[0])],
                       capture_output=True, text=True, cwd=str(RAIZ), timeout=60)
    out = (r.stdout or "") + (r.stderr or "")
    assert "Traza cargada" in out
    assert r.returncode == 0
