# -*- coding: utf-8 -*-
"""test_oraculo_r274_firmas.py — verificación Ed25519 de la distribución (H-R274-1).

cumple Manual 9 §6.1: "Firmas Ed25519: todos los artefactos distribuidos están
firmados y verificados."
cumple Manual 9 §6.3: "Archivo de firma (`.sig`) para cada binario/instalador."

El oráculo r274 debe distinguir una distribución firmada de una manipulada:
un byte cambiado en un artefacto, o un artefacto sin `.sig`, es fallo del gate.
"""
import importlib.util
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
ORACULO = RAIZ / "auditoria" / "oraculos" / "oraculo_r274_gates_independientes.py"

pytestmark = [pytest.mark.integration]


def _cargar_oraculo():
    spec = importlib.util.spec_from_file_location("oraculo_r274", ORACULO)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _distribucion(tmp_path):
    """Crea una distribución mínima firmada con un par Ed25519 temporal."""
    from instaladores.common.verificar_firma import (
        cargar_clave_publica,
        firmar_archivo,
        generar_claves,
        guardar_claves,
    )

    claves = tmp_path / "claves"
    privada, publica = generar_claves()
    guardar_claves(privada, publica, str(claves))

    dist = tmp_path / "instaladores" / "dist" / "distribucion"
    dist.mkdir(parents=True)
    (dist / "synapse.pub").write_text(cargar_clave_publica(claves / "public.pem").hex(),
                                      encoding="ascii")
    for nombre in ("synapse.exe", "install.sh", "synapse.spdx.json"):
        artefacto = dist / nombre
        artefacto.write_bytes(b"contenido de " + nombre.encode())
        firmar_archivo(artefacto, claves / "private.pem", str(artefacto) + ".sig")
    return tmp_path, dist


def test_distribucion_firmada_pasa(tmp_path):
    raiz, _ = _distribucion(tmp_path)
    ok, lineas = _cargar_oraculo().verificar_firmas_distribucion(str(raiz))
    assert ok, "\n".join(lineas)
    assert any("3 artefactos" in linea for linea in lineas)


def test_artefacto_manipulado_falla(tmp_path):
    raiz, dist = _distribucion(tmp_path)
    with open(dist / "install.sh", "ab") as fh:
        fh.write(b"tampered")
    ok, lineas = _cargar_oraculo().verificar_firmas_distribucion(str(raiz))
    assert not ok
    assert any("INVÁLIDA" in linea and "install.sh" in linea for linea in lineas)


def test_artefacto_sin_firma_falla(tmp_path):
    raiz, dist = _distribucion(tmp_path)
    (dist / "synapse.spdx.json.sig").unlink()
    ok, lineas = _cargar_oraculo().verificar_firmas_distribucion(str(raiz))
    assert not ok
    assert any("sin firma" in linea for linea in lineas)


def test_sin_distribucion_falla(tmp_path):
    ok, lineas = _cargar_oraculo().verificar_firmas_distribucion(str(tmp_path))
    assert not ok
    assert any("falta la distribución firmada" in linea for linea in lineas)
