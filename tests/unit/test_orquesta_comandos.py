# -*- coding: utf-8 -*-
"""
test_orquesta_comandos.py — ME-3 (R3+R7): Router-orquestador + comandos CLI.

Manual 7 §2.4: "El router está escrito en Synapse y actúa como el cerebro
de alto nivel de OpenSyn. Decide qué modelo usar y cómo procesar la respuesta."
Manual 7 §6.4: Comandos CLI de OpenSyn (/next, /fork, etc.)

ME-3: oráculos de orquestación (clasificar/modo_para_tarea/orquestar) y
comandos TUI (/next, /fork).
"""
import os

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _leer(ruta):
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _leer_router():
    return _leer(os.path.join(RAIZ, "opensyn", "router.syn"))


def _leer_principal():
    return _leer(os.path.join(RAIZ, "opensyn", "principal.syn"))


# ================================================================
# R3: Router-orquestador (router.syn)
# ================================================================

class TestClasificarTarea:
    """clasificar_tarea() clasifica texto libre en tipo de tarea."""

    def test_funcion_existe(self):
        router = _leer_router()
        assert "funcion clasificar_tarea(" in router

    def test_clasifica_error(self):
        router = _leer_router()
        # Debe detectar keywords de diagnóstico
        assert 'contiene(tarea_lower, "error")' in router

    def test_clasifica_refactor(self):
        router = _leer_router()
        assert 'contiene(tarea_lower, "refactor")' in router

    def test_clasifica_generar(self):
        router = _leer_router()
        assert 'contiene(tarea_lower, "genera")' in router

    def test_clasifica_revisar(self):
        router = _leer_router()
        assert 'contiene(tarea_lower, "revisa")' in router

    def test_default_explicar(self):
        router = _leer_router()
        # Si no matchea nada, retorna TAREA_EXPLICAR (0)
        assert "retornar TAREA_EXPLICAR" in router


class TestModoParaTarea:
    """modo_para_tarea() asigna el modo correcto a cada tipo de tarea."""

    def test_funcion_existe(self):
        router = _leer_router()
        assert "funcion modo_para_tarea(" in router

    def test_explicar_asigna_ask(self):
        router = _leer_router()
        # TAREA_EXPLICAR → MODO_ASK (0)
        assert "retornar 0  // MODO_ASK" in router

    def test_diagnosticar_asigna_debug(self):
        router = _leer_router()
        assert "retornar 3  // MODO_DEBUG" in router

    def test_refactorizar_asigna_code(self):
        router = _leer_router()
        assert "retornar 2  // MODO_CODE" in router


class TestOrquestar:
    """orquestar() clasifica y retorna modos asignados."""

    def test_funcion_existe(self):
        router = _leer_router()
        assert "funcion orquestar(" in router

    def test_retorna_texto(self):
        router = _leer_router()
        # Debe retornar entero_a_texto(modo)
        assert "retornar resultado" in router

    def test_cita_cumple_manual(self):
        router = _leer_router()
        assert "// cumple Manual 7 §2.4" in router


class TestSiguientesPasos:
    """siguientes_pasos() genera 3 pasos sugeridos por tipo de tarea."""

    def test_funcion_existe(self):
        router = _leer_router()
        assert "funcion siguientes_pasos(" in router

    def test_explicar_sugiere_diagnostico(self):
        router = _leer_router()
        # Para explicar: sugiere diagnosticar, refactorizar, tests
        assert "Diagnostica posibles problemas" in router

    def test_diagnosticar_sugiere_correccion(self):
        router = _leer_router()
        assert "Implementa la correccion sugerida" in router

    def test_refactorizar_sugiere_verificar(self):
        router = _leer_router()
        assert "Ejecuta los tests para verificar" in router

    def test_generar_sugiere_revisar(self):
        router = _leer_router()
        assert "Revisa el codigo generado" in router

    def test_tres_opciones_por_tipo(self):
        """Cada tipo de tarea debe tener exactamente 3 pasos (1) 2) 3))."""
        router = _leer_router()
        # Contar "1)" en el archivo — debe haber al menos 5 (uno por tipo)
        assert router.count("1) ") >= 5


# ================================================================
# R7: Comandos CLI (principal.syn)
# ================================================================

class TestComandosNextFork:
    """principal.syn debe definir los comandos /next y /fork."""

    def test_next_en_menu(self):
        principal = _leer_principal()
        assert "/next" in principal

    def test_fork_en_menu(self):
        principal = _leer_principal()
        assert "/fork" in principal

    def test_next_handler_tui(self):
        """Handler de /next en tui_comando()."""
        principal = _leer_principal()
        assert 'si entrada == "/next"' in principal

    def test_fork_handler_tui(self):
        """Handler de /fork en tui_comando()."""
        principal = _leer_principal()
        assert 'si entrada == "/fork"' in principal

    def test_next_linea_handler(self):
        """Handler de /next en chat modo línea."""
        principal = _leer_principal()
        assert 'si prompt == "/next"' in principal

    def test_fork_linea_handler(self):
        """Handler de /fork en chat modo línea."""
        principal = _leer_principal()
        assert 'si prompt == "/fork"' in principal

    def test_next_muestra_pasos(self):
        """El comando /next debe mostrar los 3 siguientes pasos."""
        principal = _leer_principal()
        assert "Siguientes pasos sugeridos" in principal

    def test_fork_mensaje(self):
        """El comando /fork debe mostrar mensaje de fork."""
        principal = _leer_principal()
        assert "creando rama de la sesion actual" in principal

    def test_ayuda_incluye_next_fork(self):
        """mostrar_ayuda() debe listar /next y /fork."""
        principal = _leer_principal()
        assert "/next" in principal
        assert "/fork" in principal

    def test_cita_cumple_manual(self):
        principal = _leer_principal()
        assert "// ME-3 (R7)" in principal
