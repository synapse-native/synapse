# -*- coding: utf-8 -*-
"""
test_inference.py — Manual 7 §2.2: Inferencia básica OpenSyn.

Manual 7 §2.2: llama_client.c envía prompts al servidor de inferencia
(127.0.0.1:8088) y recibe respuestas; soporta timeouts, reintentos y manejo
de errores. API: llama_client_crear / llama_client_completion.

Nota de trazabilidad (2026-09-19, H-R151-1): las citas históricas "Manual 7
§7 / §7.2" eran inexistentes (Manual 7 termina en §4.2) — fabricación
heredada del plan ME_29_T3, eliminada conforme al MTO (OBL-MCTRL-03: Manual
§ real). El umbral de latencia < 1.0 s no tiene ancla manual y se conserva
como criterio autorizado por el Arquitecto (MTO, plan_ME_29_T3).

Anti-sniff (Manual 7 §2.3): se verifican CONTRATOS de la API ya declarada
(declaración de función en el header fuente), no texto en artefacto generado.

Benchmark test_latencia_meta: si no hay llama-server en :8088 hace skip
(dependencia externa de entorno; suite CI en verde); con servidor, mide una
request real a /v1/chat/completions con time.perf_counter() y exige < 1 s.
"""
import json
import os
import re
import time
import socket
import urllib.error
import urllib.request

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.tdd]

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ME_INF = "ME_29_T1/ME_29_T3 (fase F29: llama_client / inferencia)"
LATENCIA_MAXIMA_SEG = 1.0  # criterio MTO plan_ME_29_T3 (sin ancla manual, H-R151-1)


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


def _servidor_activo(host, port, timeout=1.0):
    """Anti-sniff: verifica si hay un servidor llama-server activo en el puerto."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except (socket.error, OSError):
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
        """cumple Manual 7 §2.2: el cliente envía prompts al servidor de
        inferencia (127.0.0.1:8088) y recibe respuestas. Benchmark real: mide
        el tiempo de una request a /v1/chat/completions con un prompt corto.
        Sin llama-server activo hace skip (dependencia externa de entorno).
        """
        if not _servidor_activo("127.0.0.1", 8088):
            pytest.skip(
                "Benchmark de latencia requiere llama-server activo en puerto 8088 "
                "(Manual 7 §2.2). Iniciar con: opensyn/orchestrator --iniciar"
            )
        cuerpo = json.dumps({
            "model": "default",
            "messages": [{"role": "user", "content": "Di hola"}],
            "max_tokens": 8,
            "temperature": 0.0,
        }).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:8088/v1/chat/completions",
            data=cuerpo,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        inicio = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            pytest.fail(f"llama-server respondio HTTP {e.code} (Manual 7 §2.2)")
        latencia = time.perf_counter() - inicio
        contenido = ((payload.get("choices") or [{}])[0].get("message") or {}).get("content", "")
        assert isinstance(contenido, str) and contenido.strip(), (
            f"Respuesta vacia del servidor (Manual 7 §2.2): {payload!r}"
        )
        assert latencia < LATENCIA_MAXIMA_SEG, (
            f"Latencia {latencia:.3f}s excede el limite de {LATENCIA_MAXIMA_SEG}s "
            f"(criterio MTO plan_ME_29_T3)"
        )
