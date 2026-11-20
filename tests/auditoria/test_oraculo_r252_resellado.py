# -*- coding: utf-8 -*-
# cumple Manual 1 §6: el sello de frescura no puede impedir reconstruir el
# bootstrap cuando la fuente cambió y el build regeneró la etapa 2.
"""H-R275-2: re-sellado tras cambiar `nucleo/principal.syn`.

Antes, un sello que no certificaba la fuente abortaba siempre la comparación,
así que `build.py` fallaba de forma permanente en cuanto se editaba la fuente
(punto muerto). El guard anti-stale se conserva: una etapa 2 anterior a la
fuente sigue fallando.
"""

import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "auditoria", "oraculos"))

import oraculo_r252_paridad_bootstrap as oraculo  # noqa: E402


def _preparar(tmp_path, *, etapa2_nueva):
    """Monta fuente, etapas y sello en un directorio temporal."""
    fuente = tmp_path / oraculo.FUENTE
    fuente.parent.mkdir(parents=True, exist_ok=True)
    fuente.write_text("// fuente nueva\n", encoding="utf-8")
    (tmp_path / oraculo.ETAPA2).write_bytes(b"etapa2")
    (tmp_path / oraculo.ETAPA3).write_bytes(b"etapa2")
    if not etapa2_nueva:
        # etapa 2 anterior a la fuente: artefacto stale
        os.utime(str(tmp_path / oraculo.ETAPA2), (1_600_000_000, 1_600_000_000))
    sello = {"sha256_fuente": "0" * 64, "sha256_etapa2": "0" * 64,
             "bytes_etapa2": 6, "fecha": "2026-01-01T00:00:00"}
    (tmp_path / oraculo.SELLO).write_text(json.dumps(sello), encoding="utf-8")
    return str(tmp_path)


def test_resella_cuando_la_etapa2_es_posterior_a_la_fuente(tmp_path):
    raiz = _preparar(tmp_path, etapa2_nueva=True)

    ok, lineas = oraculo.comparar_artefactos(raiz, sellar=True)

    assert ok, "\n".join(lineas)
    assert any("reescrito" in linea for linea in lineas), "\n".join(lineas)


def test_sin_sellar_sigue_fallando(tmp_path):
    raiz = _preparar(tmp_path, etapa2_nueva=True)

    ok, lineas = oraculo.comparar_artefactos(raiz)

    assert not ok, "\n".join(lineas)
    assert any("cambio desde el build" in linea for linea in lineas), "\n".join(lineas)


def test_artefacto_stale_sigue_fallando(tmp_path):
    raiz = _preparar(tmp_path, etapa2_nueva=False)

    ok, lineas = oraculo.comparar_artefactos(raiz, sellar=True)

    assert not ok, "\n".join(lineas)
