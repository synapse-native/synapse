# -*- coding: utf-8 -*-
# tests/auditoria/test_oraculos_r198b1_resello.py — Oráculo del ME
# r198b1_resello (H-R198b-1, Manual 6 §5 / OBL-MCTRL-04: la evidencia queda
# atada al contenido; Manual 7 §2.3 / OBL-MCTRL-01: los tests validan
# comportamiento real). Verifica que el re-sello de cambio_hash ya no es un
# círculo: ante la única brecha de hash stale, `--verificar --me` re-sella
# in-proceso y converge en una pasada; los demás errores NO se enmascaran y
# el sello sin stage se advierte.
# cumple Manual 6 §5; ME r198b1_resello
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
AUD = RAIZ / "auditoria"


def _cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, AUD / archivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


al = _cargar("alineacion_resello", "alineacion.py")

MSG_SOLO_HASH = ("cambio_hash del expediente (aabb) no coincide con el "
                 "actual (ccdd) — re-ejecutá --verificar")


# --- A1: helper re-sella un expediente con hash stale y es idempotente ------
def test_resellar_hash_expediente_resella_y_es_idempotente(
        tmp_path, monkeypatch):
    exp = tmp_path / "r198b1_prueba.md"
    exp.write_text("# Expediente de alineación r198b1_prueba\n\n"
                   "base: HEAD\n"
                   "cambio_hash: 0000000000000000\n", encoding="utf-8")
    monkeypatch.setattr(al, "EXPEDIENTES_DIR", tmp_path)
    assert al.resellar_hash_expediente("r198b1_prueba", "cafe") is True
    assert "cambio_hash: cafe" in exp.read_text(encoding="utf-8")
    # idempotente: si la línea ya lleva la huella no reescribe
    assert al.resellar_hash_expediente("r198b1_prueba", "cafe") is False
    # sin expediente o sin huella: no-op seguro
    assert al.resellar_hash_expediente("inexistente", "cafe") is False
    assert al.resellar_hash_expediente("", "cafe") is False
    assert al.resellar_hash_expediente("r198b1_prueba", "") is False


# --- A3: el resane NO se dispara con errores reales (no enmascara) ----------
def test_solo_brecha_hash_stale_no_enmascara_otros_errores():
    assert al._solo_brecha_hash_stale([]) is False
    assert al._solo_brecha_hash_stale([MSG_SOLO_HASH]) is True
    assert al._solo_brecha_hash_stale([
        MSG_SOLO_HASH,
        "el expediente no tiene bloque para: x.py"]) is False
    assert al._solo_brecha_hash_stale(["cita inexistente"]) is False


# --- A4: aviso de sello sin stage (huella sobre blobs del INDEX) -------------
def test_aviso_sin_stage_solo_cuando_hay_diff(monkeypatch):
    capturado = {}

    def fake_run(cmd):
        capturado["cmd"] = cmd
        return ("std/sistema.syn\n", 0)

    monkeypatch.setattr(al, "_run", fake_run)
    avisos = al._avisos_sin_stage(["std/sistema.syn", "x/py.py"])
    assert len(avisos) == 1
    assert "INDEX" in avisos[0]
    assert capturado["cmd"][:4] == ["git", "diff", "--name-only", "--"]

    monkeypatch.setattr(al, "_run", lambda cmd: ("", 0))
    assert al._avisos_sin_stage(["x.py"]) == []
    # sin producción: ni siquiera ejecuta git
    capturado.clear()
    assert al._avisos_sin_stage([]) == []
    assert "cmd" not in capturado


# --- A2: integración end-to-end en el repo real — el círculo ya no existe ----
# Expediente r198b_contratos con hash ANULADO: antes del ME esto era
# RC=1 para siempre (el re-sello solo corría tras pasar); ahora
# `--verificar --me` re-sella in-proceso, retorna RC=0 y deja el expediente
# byte-a-byte igual al commiteado (la huella atada al contenido real).
EXPEDIENTE = RAIZ / "docs" / "alineacion" / "r198b_contratos.md"
EVIDENCIA = RAIZ / "auditoria" / "evidencia" / "ca4229aa1e9364ab.json"
HASH_CANONICO = b"ca4229aa1e9364ab"
HASH_NULO = b"0000000000000000"


def test_resane_end_to_end_expediente_con_hash_anulado():
    original = EXPEDIENTE.read_bytes()
    evidencia_original = EVIDENCIA.read_bytes() if EVIDENCIA.exists() else None
    anulado = original.replace(b"cambio_hash: " + HASH_CANONICO,
                               b"cambio_hash: " + HASH_NULO)
    assert anulado != original, "el expediente debe llevar la línea cambio_hash"
    r = None
    try:
        EXPEDIENTE.write_bytes(anulado)
        r = subprocess.run(
            [sys.executable, str(AUD / "alineacion.py"),
             "--verificar", "--me", "r198b_contratos",
             "--archivos", "std/sistema.syn,opensyn/principal.syn"],
            capture_output=True, text=True, cwd=str(RAIZ), timeout=880)
        salida = r.stdout + r.stderr
        # el resane se ejecutó y el gate pasó SIN edición manual
        assert "[resane]" in salida, salida
        assert r.returncode == 0, salida
        # la evidencia quedó atada al contenido real (huella canónica)
        assert ("cambio_hash: " + HASH_CANONICO.decode()) in \
            EXPEDIENTE.read_text(encoding="utf-8")
        assert EXPEDIENTE.read_bytes() == original
    finally:
        # el oráculo nunca deja el repo sucio
        EXPEDIENTE.write_bytes(original)
        if evidencia_original is not None:
            EVIDENCIA.write_bytes(evidencia_original)
