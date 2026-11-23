# cumple Manual 1 §5.7: cero telemetría y soberanía del usuario — el
# diagnóstico local no puede abrir red propia.
# cumple Manual 7 §7.3: diagnóstico local opt-in.
"""Oráculo del ME r284_observabilidad_local (H-R284-2).

Demuestra por análisis del código de producción que el camino de ejecución de
`synapse observability` no realiza salidas de red:

* el bloque de despacho vive dentro de `asm(...)` (regresión R274);
* sus únicas llamadas son de CLI local (`fprintf`, `strcmp`, `_argv`, `_argc`);
* los helpers `_syn_health_check` y `_syn_diagnostic_info` solo formatean
  estado local.

El test es deliberadamente estático: no depende de que exista un binario
compilado ni de una red disponible, y falla si alguien introduce una llamada
de red en este camino.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PRINCIPAL = RAIZ / "nucleo" / "principal.syn"
DEBUG_C = RAIZ / "runtime" / "core" / "debug.c"

# Símbolos de egreso de red que no deben aparecer en el camino de diagnóstico.
RED_PROHIBIDA = (
    "socket(",
    "connect(",
    "getaddrinfo",
    "gethostbyname",
    "sendto(",
    "recvfrom(",
    "WSAStartup",
    "wininet",
    "curl_easy",
    "http://",
    "https://",
    "inet_addr",
    "inet_pton",
)


def _region_observabilidad() -> str:
    fuente = PRINCIPAL.read_text(encoding="utf-8")
    inicio = fuente.index("// --- Subcomando: observabilidad local")
    fin = fuente.index("// cumple Manual 1 §5.7: fin subcomando observabilidad")
    return fuente[inicio:fin]


def _cuerpo_funcion(fuente: str, nombre: str) -> str:
    """Extrae el cuerpo de una función C por conteo de llaves."""
    inicio = fuente.index(nombre)
    llave = fuente.index("{", inicio)
    nivel = 0
    for i in range(llave, len(fuente)):
        if fuente[i] == "{":
            nivel += 1
        elif fuente[i] == "}":
            nivel -= 1
            if nivel == 0:
                return fuente[llave:i + 1]
    raise AssertionError(f"función {nombre} sin cierre de llaves")


def test_region_observabilidad_no_usa_red():
    region = _region_observabilidad().lower()
    encontrados = [s for s in RED_PROHIBIDA if s.lower() in region]
    assert not encontrados, (
        "el diagnóstico local no puede salir a la red; encontrado: "
        f"{encontrados}"
    )


def test_helpers_de_salud_no_usan_red():
    fuente = DEBUG_C.read_text(encoding="utf-8")
    for nombre in ("_syn_health_check", "_syn_diagnostic_info"):
        cuerpo = _cuerpo_funcion(fuente, nombre).lower()
        encontrados = [s for s in RED_PROHIBIDA if s.lower() in cuerpo]
        assert not encontrados, (
            f"{nombre} no puede salir a la red; encontrado: {encontrados}"
        )


def test_diagnostico_declara_telemetria_apagada():
    fuente = DEBUG_C.read_text(encoding="utf-8")
    cuerpo = _cuerpo_funcion(fuente, "_syn_diagnostic_info")
    assert "telemetry: off" in cuerpo
    assert "modo: opt-in" in cuerpo


def test_despacho_expone_los_cuatro_subcomandos():
    region = _region_observabilidad()
    for sub in ("status", "health", "info", "help", "h"):
        assert f'strcmp(_osub.datos,\\"{sub}\\")' in region, (
            f"el despacho no expone el subcomando {sub!r} (Manual 1 §5.7)"
        )
