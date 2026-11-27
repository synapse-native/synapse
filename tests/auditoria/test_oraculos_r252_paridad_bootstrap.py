# -*- coding: utf-8 -*-
"""Oráculo del ME r252_bootstrap_parity (Manual 1 §6, Manual 9 §6.2, §2.3).

Comprueba la lógica del sello de bootstrap con artefactos sintéticos, de modo
que el test es hermético y corre en segundos: no depende de que el checkout
tenga `synapse_stage2.exe` / `synapse_stage3.exe`. La verificación sobre los
artefactos reales la ejecuta el propio oráculo en CI (job `bootstrap`) y en
local con `python auditoria/oraculos/oraculo_r252_paridad_bootstrap.py`.
"""
import importlib.util
import os

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUTA_ORACULO = os.path.join(RAIZ, "auditoria", "oraculos",
                            "oraculo_r252_paridad_bootstrap.py")


def _cargar_oraculo():
    especificacion = importlib.util.spec_from_file_location("oraculo_r252", RUTA_ORACULO)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def _escribir(ruta, contenido):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(contenido)


def test_sin_etapa2_falla_con_motivo_accionable(tmp_path):
    oraculo = _cargar_oraculo()
    ok, lineas = oraculo.comparar_artefactos(str(tmp_path))
    assert ok is False
    assert any("falta synapse_stage2.exe" in linea for linea in lineas), lineas
    assert any("build.py" in linea for linea in lineas), lineas


def test_sin_etapa3_no_declara_determinismo(tmp_path):
    oraculo = _cargar_oraculo()
    _escribir(tmp_path / "synapse_stage2.exe", b"etapa2")
    ok, lineas = oraculo.comparar_artefactos(str(tmp_path))
    assert ok is False
    assert any("falta synapse_stage3.exe" in linea for linea in lineas), lineas


def test_etapas_identicas_pasan_el_sello(tmp_path):
    oraculo = _cargar_oraculo()
    _escribir(tmp_path / "synapse_stage2.exe", b"binario determinista")
    _escribir(tmp_path / "synapse_stage3.exe", b"binario determinista")
    ok, lineas = oraculo.comparar_artefactos(str(tmp_path))
    assert ok is True, lineas
    assert any("[OK] bootstrap determinista" in linea for linea in lineas), lineas


def test_etapas_distintas_violan_la_regla_de_hierro(tmp_path):
    oraculo = _cargar_oraculo()
    _escribir(tmp_path / "synapse_stage2.exe", b"etapa 2")
    _escribir(tmp_path / "synapse_stage3.exe", b"etapa 3")
    ok, lineas = oraculo.comparar_artefactos(str(tmp_path))
    assert ok is False
    assert any("VIOLADO" in linea for linea in lineas), lineas


def test_deriva_de_distribuidos_avisa_por_defecto(tmp_path):
    """Un binario distribuido viejo se reporta como WARN sin romper el sello."""
    oraculo = _cargar_oraculo()
    _escribir(tmp_path / "synapse_stage2.exe", b"actual")
    _escribir(tmp_path / "synapse_stage3.exe", b"actual")
    _escribir(tmp_path / "synapse.exe", b"viejo")
    ok, lineas = oraculo.comparar_artefactos(str(tmp_path))
    assert ok is True, lineas
    assert any("[WARN] synapse.exe NO corresponde" in linea for linea in lineas), lineas


def test_deriva_de_distribuidos_falla_en_modo_estricto(tmp_path):
    """`--estricto` es el guard que impide publicar un binario stale."""
    oraculo = _cargar_oraculo()
    _escribir(tmp_path / "synapse_stage2.exe", b"actual")
    _escribir(tmp_path / "synapse_stage3.exe", b"actual")
    _escribir(tmp_path / "synapse.exe", b"actual")
    _escribir(tmp_path / "dist" / "bin" / "synapse.exe", b"viejo")
    ok, lineas = oraculo.comparar_artefactos(str(tmp_path), estricto=True)
    assert ok is False
    assert any("[FAIL] dist" in linea for linea in lineas), lineas


def test_distribuidos_al_dia_pasan_el_modo_estricto(tmp_path):
    oraculo = _cargar_oraculo()
    _escribir(tmp_path / "synapse_stage2.exe", b"actual")
    _escribir(tmp_path / "synapse_stage3.exe", b"actual")
    _escribir(tmp_path / "synapse.exe", b"actual")
    _escribir(tmp_path / "dist" / "bin" / "synapse.exe", b"actual")
    ok, lineas = oraculo.comparar_artefactos(str(tmp_path), estricto=True)
    assert ok is True, lineas
    assert sum(linea.startswith("[OK] ") for linea in lineas) == 3, lineas


def test_main_falla_sin_artefactos(tmp_path, monkeypatch, capsys):
    """El punto de entrada devuelve rc=1 y no lanza excepción."""
    oraculo = _cargar_oraculo()
    monkeypatch.setattr(oraculo, "RAIZ", str(tmp_path))
    assert oraculo.main(["--artefactos"]) == 1
    salida = capsys.readouterr().out
    assert "falta synapse_stage2.exe" in salida, salida


def _cargar_build():
    especificacion = importlib.util.spec_from_file_location(
        "build_r252", os.path.join(RAIZ, "build.py"))
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def test_build_py_aborta_si_el_sello_falla(tmp_path, monkeypatch, capsys):
    """Si el oráculo devuelve rc!=0, el build termina en error (Manual 1 §6)."""
    build = _cargar_build()
    monkeypatch.setattr(build, "RAIZ", str(tmp_path))
    llamadas = {"sello": None}

    def _call_falso(cmd, cwd=None):
        del cwd
        if any("oraculo_r252_paridad_bootstrap" in str(parte) for parte in cmd):
            llamadas["sello"] = cmd
            return 1
        destino = tmp_path / "principal.exe"
        destino.write_bytes(b"etapa")
        return 0

    monkeypatch.setattr(build.subprocess, "call", _call_falso)
    (tmp_path / "synapse_bootstrap.exe").write_bytes(b"etapa 1")

    with pytest.raises(SystemExit) as salida:
        build.main()
    assert salida.value.code == 1
    assert llamadas["sello"] is not None, "build.py no invocó el oráculo"
    assert "--artefactos" in llamadas["sello"]
