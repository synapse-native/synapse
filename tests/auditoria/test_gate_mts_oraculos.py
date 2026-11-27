# -*- coding: utf-8 -*-
"""tests/auditoria/test_gate_mts_oraculos.py — Oráculo del endurecimiento del
sistema de control (ME-control_solido).

Manual 7 §2.3 (los tests validan comportamiento real) — OBL-MCTRL-01.
Manual 2 §12 (trazabilidad anti-fabricación) — OBL-MCTRL-02.
Manual 7 §2.3 (MTO autenticado) — OBL-MCTRL-03.
Manual 6 §5 (evidencia atada al contenido) — OBL-MCTRL-04.

Los gates deben FALLAR CERRADO: base CI vacía, oráculo vacío/saltado, cita
decorativa, sello eterno o evidencia desanclada no pueden pasar como verdes.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
AUD = RAIZ / "auditoria"


def _cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, AUD / archivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ct = _cargar("contrastar_oraculo", "contrastar.py")
va = _cargar("verificar_alineacion_oraculo", "verificar_alineacion.py")
al = _cargar("alineacion_oraculo", "alineacion.py")
aq = _cargar("auditar_calidad_oraculo", "auditar_calidad_tests.py")


# --- OBL-MCTRL-01: la base CI vacía nunca produce diff nulo -----------------
def test_nonnull_base_en_ambos_gates():
    assert ct.nonnull_base("") == "HEAD~1"
    assert ct.nonnull_base("   ") == "HEAD~1"
    assert ct.nonnull_base("origin/main") == "origin/main"
    assert va.nonnull_base("") == "HEAD~1"


# --- OBL-MCTRL-01: el oráculo se EJECUTA y lo vacío/saltado no es evidencia --
def test_oraculo_vacio_no_es_evidencia(tmp_path):
    t = tmp_path / "test_vacio_oraculo.py"
    t.write_text("# archivo sin tests\n", encoding="utf-8")
    assert ct.ejecutar_oraculo(str(t)) is False


def test_oraculo_skip_no_es_evidencia(tmp_path):
    t = tmp_path / "test_skip_oraculo.py"
    t.write_text("import pytest\n\ndef test_x():\n    pytest.skip('n/a')\n",
                 encoding="utf-8")
    assert ct.ejecutar_oraculo(str(t)) is False


def test_oraculo_verde_es_evidencia(tmp_path):
    t = tmp_path / "test_ok_oraculo.py"
    t.write_text("def test_ok():\n    assert 1 + 1 == 2\n", encoding="utf-8")
    assert ct.ejecutar_oraculo(str(t)) is True


def test_oraculo_fallido_no_es_evidencia(tmp_path):
    t = tmp_path / "test_fail_oraculo.py"
    t.write_text("def test_mal():\n    assert 1 == 2\n", encoding="utf-8")
    assert ct.ejecutar_oraculo(str(t)) is False


# --- OBL-MCTRL-02: vínculo ESTRICTO plan<->archivo ---------------------------
def test_cubre_req_exige_manual_coincidente():
    citas_validas = [("8", "1.2"), ("9", "5.7")]
    citas_ajenas = [("4", "2")]
    assert ct.cubre_req("8", "1.2", citas_validas) is True
    assert ct.cubre_req("8", "1.2", citas_ajenas) is False


def test_parsear_plan_mantiene_oraculos_por_bloque():
    plan = ("requisito: Manual 7 §2.3\ntexto: t1\noraculo: tests/a.py\n\n"
            "requisito: Manual 2 §12\ntexto: t2\noraculo: tests/b.py\n")
    reqs = ct.parsear_plan(plan)
    assert [r["oraculo"] for r in reqs] == ["tests/a.py", "tests/b.py"]
    assert reqs[1]["manual"] == "2" and reqs[1]["seccion"] == "12"


def test_d9_acepta_runtime_c():
    mods = va.cargar_modulos_d9()
    assert "runtime/core/cluster.c" in mods
    assert "opensyn/principal.syn" in mods


# --- OBL-MCTRL-02: lectura previa VINCULADA a los archivos -------------------
def test_lectura_sin_vinculo_de_archivos_no_cubre():
    rl = _cargar("registrar_lectura_oraculo", "registrar_lectura.py")
    reqs = {"nucleo/foo.syn": ["Manual 2 §12"]}
    entradas = [{"fecha": "2026-09-14", "cita": "Manual 2 §12",
                 "archivos": ["otros/archivo.syn"]}]
    assert rl.vinculacion_archivos(reqs, entradas) == ["nucleo/foo.syn"]
    entradas_ok = [{"fecha": "2026-09-14", "cita": "Manual 2 §12",
                    "archivos": ["nucleo/foo.syn"]}]
    assert rl.vinculacion_archivos(reqs, entradas_ok) == []


# --- OBL-MCTRL-03: el MTO se autentica ---------------------------------------
def test_mto_valido_pasaria_solo_mto():
    r = subprocess.run([sys.executable, str(AUD / "auditar_calidad_tests.py"),
                        "--solo-mto"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "[MTO]" in r.stdout


def test_sin_obl_detectado_en_modo_incremental(tmp_path):
    t = tmp_path / "test_sin_obl_fixture.py"
    t.write_text('# Manual 2 §12\ndef test_x():\n    assert True\n',
                 encoding="utf-8")
    issues = aq.scan_file(t)
    kinds = [k for k, _p, _m in issues]
    assert "SIN_OBL" in kinds


def test_con_obl_no_reporta_sin_obl(tmp_path):
    t = tmp_path / "test_con_obl_fixture.py"
    t.write_text('# OBL-MCTRL-01 — Manual 7 §2.3\ndef test_x():\n    assert True\n',
                 encoding="utf-8")
    kinds = [k for k, _p, _m in aq.scan_file(t)]
    assert "SIN_CITA" not in kinds and "SIN_OBL" not in kinds


# --- OBL-MCTRL-04: evidencia atada al contenido ------------------------------
def test_sello_expirado_rechazado(tmp_path):
    sello = tmp_path / "ME-VIEJO.antes.json"
    sello.write_text(json.dumps({"me": "ME-VIEJO", "fecha": "2020-01-01",
                                 "base": "", "archivos": []}),
                     encoding="utf-8")
    errores = al.sello_previo_a_cambio(sello, [])
    assert any("EXPIRADO" in e for e in errores)


def test_sello_corrupto_rechazado(tmp_path):
    sello = tmp_path / "ME-ROTO.antes.json"
    sello.write_text("no-json{{{", encoding="utf-8")
    errores = al.sello_previo_a_cambio(sello, [])
    assert any("ILEGIBLE" in e for e in errores)


def test_evidencia_ci_ausente_bloquea():
    # Un cambio_hash aleatorio no tiene evidencia comiteada => debe fallar.
    errores = al.evidencia_ci_ok("0123456789abcdef0123456789abcdef")
    assert errores
    assert "COMITEADA" in errores[0] or "cambio_hash" in errores[0]
