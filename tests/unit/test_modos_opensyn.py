# -*- coding: utf-8 -*-
"""
test_modos_opensyn.py — TDD del sistema de modos del agente (Manual 7 §1.1).

Valida la lógica de permisos por modo: ASK=solo lectura, PLAN=diseño,
CODE=edición, DEBUG=diagnóstico, ORCHESTRATOR=delegación.

Réplica en Python de las funciones Synapse de principal.syn para poder
ejecutar assertions en CI sin compilar el binario. Cuando principal.syn
cambie, este test debe mantenerse sincronizado (regla: el test es la fuente
de verdad de la semántica de permisos).

Cumple MTO §3: cada requisito del manual se convierte en test ejecutable.
requisito: Manual 7 §1.1
texto: "OpenSyn es el asistente de inteligencia artificial local del ecosistema
  Synapse. Es el equivalente a un «Copilot» o «OpenCode»... Validación
  automática y bucle de corrección"
oraculo: tests/unit/test_modos_opensyn.py
"""

import pytest

pytestmark = pytest.mark.unit

# --- Constantes réplica de principal.syn (MUST keep in sync) ---
MODO_ASK = 0
MODO_PLAN = 1
MODO_CODE = 2
MODO_DEBUG = 3
MODO_ORCHESTRATOR = 4
MODO_DEFAULT = MODO_ASK


# --- Funciones réplica de principal.syn ---

def herramientas_permitidas(modo: int) -> str:
    """Tabla de permisos por modo. Replica principal.syn:640-660."""
    if modo == MODO_ASK:
        return "listar,leer,git"
    if modo == MODO_PLAN:
        return "listar,leer,git,plan"
    if modo == MODO_CODE:
        return "listar,leer,git,plan,editar,compilar"
    if modo == MODO_DEBUG:
        return "listar,leer,git,diagnosticar"
    if modo == MODO_ORCHESTRATOR:
        return "delegar"
    return "listar,leer,git"


def herramienta_permitida(modo: int, herramienta: str) -> int:
    """Verifica si una herramienta está permitida en el modo actual.
    Replica principal.syn:663-701."""
    permitidas = herramientas_permitidas(modo)
    # orchestrator: verificar la lista en vez de retornar 0 directamente
    if modo == MODO_ORCHESTRATOR:
        # buscar "delegar" en la lista
        items = permitidas.split(",")
        return 1 if herramienta in items else 0
    items = permitidas.split(",")
    return 1 if herramienta in items else 0


def nombre_modo(modo: int) -> str:
    """Nombre legible del modo. Replica principal.syn:704-717."""
    nombres = {
        MODO_ASK: "ASK (solo lectura)",
        MODO_PLAN: "PLAN (diseño)",
        MODO_CODE: "CODE (edición)",
        MODO_DEBUG: "DEBUG (diagnóstico)",
        MODO_ORCHESTRATOR: "ORCHESTRATOR (delegación)",
    }
    return nombres.get(modo, "DESCONOCIDO")


def pct_contexto(sys_bytes: int) -> int:
    """% del presupuesto de system prompt (3500 bytes). Replica principal.syn:938-946."""
    if sys_bytes > 3500:
        sys_bytes = 3500
    return (sys_bytes * 100) // 3500


# ============================================================
# Tests TDD — Manual 7 §1.1 (modos del agente)
# ============================================================


class TestHerramientasPermitidas:
    """herramientas_permitidas() retorna la lista correcta por modo."""

    def test_ask_solo_lectura(self):
        assert herramientas_permitidas(MODO_ASK) == "listar,leer,git"

    def test_plan_incluye_plan(self):
        assert herramientas_permitidas(MODO_PLAN) == "listar,leer,git,plan"

    def test_code_incluye_edicion(self):
        assert herramientas_permitidas(MODO_CODE) == "listar,leer,git,plan,editar,compilar"

    def test_debug_incluye_diagnosticar(self):
        assert herramientas_permitidas(MODO_DEBUG) == "listar,leer,git,diagnosticar"

    def test_orchestrator_solo_delegar(self):
        assert herramientas_permitidas(MODO_ORCHESTRATOR) == "delegar"

    def test_default_ask(self):
        assert herramientas_permitidas(999) == "listar,leer,git"


class TestHerramientaPermitida:
    """herramienta_permitida() retorna 1 si la herramienta está en la lista."""

    # --- ASK: solo listar, leer, git ---
    @pytest.mark.parametrize("herramienta", ["listar", "leer", "git"])
    def test_ask_permite_herramientas_base(self, herramienta):
        assert herramienta_permitida(MODO_ASK, herramienta) == 1

    @pytest.mark.parametrize("herramienta", ["editar", "compilar", "plan", "diagnosticar"])
    def test_ask_bloquea_herramientas_escritura(self, herramienta):
        assert herramienta_permitida(MODO_ASK, herramienta) == 0

    # --- PLAN: base + plan ---
    @pytest.mark.parametrize("herramienta", ["listar", "leer", "git", "plan"])
    def test_plan_permite_herramientas_plan(self, herramienta):
        assert herramienta_permitida(MODO_PLAN, herramienta) == 1

    @pytest.mark.parametrize("herramienta", ["editar", "compilar", "diagnosticar"])
    def test_plan_bloquea_escritura(self, herramienta):
        assert herramienta_permitida(MODO_PLAN, herramienta) == 0

    # --- CODE: todas excepto delegar ---
    @pytest.mark.parametrize("herramienta", ["listar", "leer", "git", "plan", "editar", "compilar"])
    def test_code_permite_todo_edicion(self, herramienta):
        assert herramienta_permitida(MODO_CODE, herramienta) == 1

    def test_code_bloquea_delegar(self):
        assert herramienta_permitida(MODO_CODE, "delegar") == 0

    # --- DEBUG: base + diagnosticar ---
    @pytest.mark.parametrize("herramienta", ["listar", "leer", "git", "diagnosticar"])
    def test_debug_permite_diagnostico(self, herramienta):
        assert herramienta_permitida(MODO_DEBUG, herramienta) == 1

    @pytest.mark.parametrize("herramienta", ["editar", "compilar", "plan"])
    def test_debug_bloquea_escritura(self, herramienta):
        assert herramienta_permitida(MODO_DEBUG, herramienta) == 0

    # --- ORCHESTRATOR: solo delegar ---
    def test_orchestrator_permite_delegar(self):
        assert herramienta_permitida(MODO_ORCHESTRATOR, "delegar") == 1

    @pytest.mark.parametrize("herramienta", ["listar", "leer", "git", "editar", "compilar"])
    def test_orchestrator_bloquea_directas(self, herramienta):
        assert herramienta_permitida(MODO_ORCHESTRATOR, herramienta) == 0

    # --- Anti-substring: "plan" no es "planificar" ---
    def test_no_falso_positivo_substring(self):
        """herramienta 'plan' no debe matchear si la lista tiene 'planificar'."""
        # Si la lista fuera "listar,planificar,leer", "plan" no debe pasar
        # (este test documenta el comportamiento esperado)
        assert herramienta_permitida(MODO_ASK, "li") == 0
        assert herramienta_permitida(MODO_ASK, "liste") == 0

    # --- Casos borde ---
    def test_herramienta_vacia(self):
        assert herramienta_permitida(MODO_ASK, "") == 0

    def test_herramienta_desconocida(self):
        assert herramienta_permitida(MODO_CODE, "teletransportar") == 0


class TestNombreModo:
    """nombre_modo() retorna la cadena correcta."""

    def test_ask(self):
        assert nombre_modo(MODO_ASK) == "ASK (solo lectura)"

    def test_plan(self):
        assert nombre_modo(MODO_PLAN) == "PLAN (diseño)"

    def test_code(self):
        assert nombre_modo(MODO_CODE) == "CODE (edición)"

    def test_debug(self):
        assert nombre_modo(MODO_DEBUG) == "DEBUG (diagnóstico)"

    def test_orchestrator(self):
        assert nombre_modo(MODO_ORCHESTRATOR) == "ORCHESTRATOR (delegación)"

    def test_desconocido(self):
        assert nombre_modo(999) == "DESCONOCIDO"


class TestPctContexto:
    """pct_contexto() calcula el % del presupuesto de system prompt."""

    def test_cero_bytes(self):
        assert pct_contexto(0) == 0

    def test_mitad(self):
        assert pct_contexto(1750) == 50

    def test_lleno(self):
        assert pct_contexto(3500) == 100

    def test_excedido(self):
        assert pct_contexto(7000) == 100

    def test_casi_lleno(self):
        assert pct_contexto(3499) == 99


class TestIntegracionModos:
    """Flujos de integración: cambiar de modo y verificar permisos."""

    def test_flujo_ask_a_code(self):
        modo = MODO_DEFAULT
        assert modo == MODO_ASK
        assert herramienta_permitida(modo, "editar") == 0
        modo = MODO_CODE
        assert herramienta_permitida(modo, "editar") == 1

    def test_flujo_code_a_orchestrator(self):
        modo = MODO_CODE
        assert herramienta_permitida(modo, "delegar") == 0
        modo = MODO_ORCHESTRATOR
        assert herramienta_permitida(modo, "delegar") == 1
        assert herramienta_permitida(modo, "listar") == 0

    def test_orchestrator_no_ejecuta_nada(self):
        """ORCHESTRATOR solo delega, no ejecuta herramientas directas."""
        for h in ["listar", "leer", "git", "editar", "compilar", "plan", "diagnosticar"]:
            assert herramienta_permitida(MODO_ORCHESTRATOR, h) == 0
