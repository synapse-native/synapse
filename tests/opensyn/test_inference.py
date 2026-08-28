# -*- coding: utf-8 -*-
"""
test_inference.py — M7 §7 / M7 §2.2: Inferencia básica OpenSyn.

Manual 7 §7: "Inferencia básica — Respuesta no vacía".
Manual 7 §2.2: llama_client.c envía prompts a llama-server.

CALIDAD TOTAL (regla transversal plan_AUDITORIA_TESTS.md): especificación
COMPLETA. Mientras opensyn/llama_client.h / .c y orchestrator.h (fase F29) no
existan, FALLA en ROJO TDD (pytest.fail) apuntando a ME_29_T1/ME_29_T3 — sin
pytest.skip. La meta de latencia (<1s) es requisito de rendimiento verificable
por benchmark → también ROJO TDD (ME_29_T3), no skip.

Anti-sniff (Manual 7 §2.3): se verifican CONTRATOS de la API ya declarada
(declaración de función en el header fuente), no texto en artefacto generado.
"""
import os
import re

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.tdd]

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ME_INF = "ME_29_T1/ME_29_T3 (fase F29: llama_client / inferencia)"


def _leer_fuente(ruta, manual):
    if not os.path.exists(ruta):
        pytest.fail(
            f"RED TDD {ME_INF}: {ruta} no implementado aún "
            f"({manual}). Implementar en fase F29."
        )
    with open(ruta, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()


def _declara(fuente, simbolo):
    """Contrato: el símbolo debe estar declarado como función (C o Syquex)."""
    if re.search(r"\b" + re.escape(simbolo) + r"\s*\(", fuente):
        return True
    if ("func " + simbolo in fuente) or ("externo funcion " + simbolo in fuente):
        return True
    return False


class TestInferencia:
    """Manual 7 §2.2: Inferencia vía llama_client.c."""

    def test_llama_client_archivos(self):
        """opensyn/llama_client.h y .c deben existir y no estar vacíos (Manual 7 §2.2)."""
        client_h = os.path.join(RAIZ, "opensyn", "llama_client.h")
        client_c = os.path.join(RAIZ, "opensyn", "llama_client.c")
        if not os.path.exists(client_h):
            pytest.fail(
                f"RED TDD {ME_INF}: opensyn/llama_client.h no existe "
                f"(Manual 7 §2.2). Implementar en fase F29."
            )
        if not os.path.exists(client_c):
            pytest.fail(
                f"RED TDD {ME_INF}: opensyn/llama_client.c no existe "
                f"(Manual 7 §2.2). Implementar en fase F29."
            )
        assert os.path.getsize(client_h) > 0
        assert os.path.getsize(client_c) > 0

    def test_llama_client_crear(self):
        """llama_client_crear() debe estar declarado (Manual 7 §2.2)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "llama_client.h"), "Manual 7 §2.2"
        )
        assert _declara(fuente, "llama_client_crear"), \
            "llama_client.h debe declarar llama_client_crear()"

    def test_llama_client_completion(self):
        """llama_client_completion() debe estar declarado (Manual 7 §2.2)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "llama_client.h"), "Manual 7 §2.2"
        )
        assert _declara(fuente, "llama_client_completion"), \
            "llama_client.h debe declarar llama_client_completion()"

    def test_orchestrator_lifecycle(self):
        """orchestrator debe gestionar lifecycle de llama-server (Manual 7 §2.2)."""
        fuente = _leer_fuente(
            os.path.join(RAIZ, "opensyn", "orchestrator.h"), "Manual 7 §2.2"
        )
        assert "iniciar" in fuente.lower() or "create" in fuente.lower() or \
            "start" in fuente.lower(), \
            "orchestrator.h debe tener funcion de inicio"

    def test_latencia_meta(self):
        """Manual 7 §7.2: Latencia < 1s para prompts cortos (7B GPU). Requisito de
        rendimiento verificable por benchmark → ROJO TDD hasta implementar/medir."""
        pytest.fail(
            "RED TDD ME_29_T3 (fase F29): meta de latencia < 1s (Manual 7 §7.2) "
            "pendiente de implementación de inferencia y benchmark. No es skip."
        )
