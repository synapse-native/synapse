# -*- coding: utf-8 -*-
"""test_opensyn_sin_red.py — r275: privacidad de red de OpenSyn.

cumple Manual 7 §7.3: "Cero telemetría: Verificado con monitoreo de red (sin
conexiones salientes)." / "Modelos firmados: Todos los modelos descargados se
verifican con SHA-256." / "Sandboxing: El servidor de inferencia se ejecuta
con permisos mínimos."

Oráculo estático y determinista: recorre el código real de `opensyn/` y exige
que cualquier endpoint HTTP literal sea loopback, salvo las descargas de
modelos documentadas por el instalador (Manual 9 §5.3) y el enlace de ayuda
impreso por el CLI. También rechaza rastreadores/telemetría sin descargo
explícito. No requiere red, modelo ni binario: corre siempre en CI.
"""
import os
import re
from urllib.parse import urlparse

import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OPEN_SYN = os.path.join(RAIZ, "opensyn")

pytestmark = [pytest.mark.integration, pytest.mark.opensyn]

HOSTS_LOCALES = {"127.0.0.1", "localhost", "::1", "[::1]", "0.0.0.0"}
# Manual 9 §5.3: el instalador descarga los GGUF desde el catálogo firmado.
INSTALADORES = {"installer.syn", "installer.c", "_installer.c", "modelos.toml"}
HOSTS_INSTALADOR = {"huggingface.co"}
# Enlace de documentación que el CLI imprime; no se consulta por red.
AYUDA_DOC = "synapse-native.github.io"

URL_RE = re.compile(r"https?://[^\s\"'<>]+")
TELEMETRIA_RE = re.compile(
    r"\b(telemetry|analytics|tracking|sentry|posthog|mixpanel|segment\.io)\b",
    re.IGNORECASE,
)
DESCARGOS = (
    "zero-telemetry", "zero telemetry", "no telemetry", "sin telemetr",
    "cero telemetr", "no_telemetry", "cero_telemetria", "sin telemetría",
    "cero telemetría",
)


def _fuentes_opensyn():
    for raiz, _dirs, archivos in os.walk(OPEN_SYN):
        for nombre in sorted(archivos):
            if nombre.endswith((".syn", ".c", ".h", ".toml")):
                yield os.path.join(raiz, nombre)


def test_endpoints_http_solo_locales_o_descargas_documentadas():
    """Manual 7 §7.3: sin conexiones salientes ocultas en el código de OpenSyn."""
    violaciones = []
    for ruta in _fuentes_opensyn():
        with open(ruta, "r", encoding="utf-8", errors="replace") as fh:
            texto = fh.read()
        nombre = os.path.basename(ruta)
        for match in URL_RE.finditer(texto):
            url = match.group(0).rstrip(").,;")
            host = urlparse(url).hostname or ""
            if not host or "%" in host:
                continue
            if host in HOSTS_LOCALES:
                continue
            if nombre in INSTALADORES and host in HOSTS_INSTALADOR:
                continue
            if nombre == "principal.syn" and host == AYUDA_DOC:
                continue
            linea = texto.count("\n", 0, match.start()) + 1
            violaciones.append(f"{os.path.relpath(ruta, RAIZ)}:{linea} -> {host}")
    assert not violaciones, (
        "endpoints no locales en opensyn/ (Manual 7 §7.3):\n"
        + "\n".join(violaciones)
    )


def test_sin_telemetria_ni_rastreadores_sin_descargo():
    """Manual 7 §7.3: ningún rastreador/telemetría sin descargo explícito."""
    violaciones = []
    for ruta in _fuentes_opensyn():
        with open(ruta, "r", encoding="utf-8", errors="replace") as fh:
            texto = fh.read()
        if not TELEMETRIA_RE.search(texto):
            continue
        bajo = texto.lower()
        if any(marca in bajo for marca in DESCARGOS):
            continue
        violaciones.append(os.path.relpath(ruta, RAIZ))
    assert not violaciones, (
        "archivos de opensyn/ mencionan telemetría/analytics sin descargo "
        "(Manual 7 §7.3):\n" + "\n".join(violaciones)
    )
