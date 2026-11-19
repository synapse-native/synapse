# -*- coding: utf-8 -*-
"""Oráculo r270: tamaño y frescura del bootstrap (Manual 1 §6, Manual 9 §6.2).

Complementa test_oraculos_r252_paridad_bootstrap.py con los dos guards que
resuelven H-R252-1: S2/S3 deben coincidir también en tamaño y no pueden ser
artefactos anteriores a `nucleo/principal.syn`.
"""
import importlib.util
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUTA_ORACULO = os.path.join(
    RAIZ, "auditoria", "oraculos", "oraculo_r252_paridad_bootstrap.py"
)


def _cargar():
    especificacion = importlib.util.spec_from_file_location(
        "oraculo_r270", RUTA_ORACULO
    )
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def _escribir(ruta, contenido, mtime=None):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(contenido)
    if mtime is not None:
        os.utime(ruta, (mtime, mtime))


def test_reporta_tamano_de_ambas_etapas(tmp_path):
    oraculo = _cargar()
    _escribir(tmp_path / "synapse_stage2.exe", b"abc")
    _escribir(tmp_path / "synapse_stage3.exe", b"abc")
    ok, lineas = oraculo.comparar_artefactos(str(tmp_path))
    assert ok is True, lineas
    assert any("(3 bytes)" in linea for linea in lineas), lineas


def test_stage2_anterior_a_la_fuente_falla(tmp_path):
    oraculo = _cargar()
    fuente = tmp_path / "nucleo" / "principal.syn"
    _escribir(fuente, b"fuente", mtime=2000)
    _escribir(tmp_path / "synapse_stage2.exe", b"igual", mtime=1000)
    _escribir(tmp_path / "synapse_stage3.exe", b"igual", mtime=1000)
    ok, lineas = oraculo.comparar_artefactos(str(tmp_path))
    assert ok is False, lineas
    assert any("synapse_stage2.exe es anterior" in linea for linea in lineas), lineas


def test_stage3_anterior_a_stage2_falla(tmp_path):
    oraculo = _cargar()
    fuente = tmp_path / "nucleo" / "principal.syn"
    _escribir(fuente, b"fuente", mtime=1000)
    _escribir(tmp_path / "synapse_stage2.exe", b"igual", mtime=2000)
    _escribir(tmp_path / "synapse_stage3.exe", b"igual", mtime=1500)
    ok, lineas = oraculo.comparar_artefactos(str(tmp_path))
    assert ok is False, lineas
    assert any("synapse_stage3.exe es anterior" in linea for linea in lineas), lineas


def test_artefactos_frescos_pasan(tmp_path):
    oraculo = _cargar()
    fuente = tmp_path / "nucleo" / "principal.syn"
    _escribir(fuente, b"fuente", mtime=1000)
    _escribir(tmp_path / "synapse_stage2.exe", b"igual", mtime=2000)
    _escribir(tmp_path / "synapse_stage3.exe", b"igual", mtime=3000)
    ok, lineas = oraculo.comparar_artefactos(str(tmp_path))
    assert ok is True, lineas
