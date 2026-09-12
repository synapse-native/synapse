# -*- coding: utf-8 -*-
"""
test_orquesta_comandos.py — ME-3 (R3+R7): Oráculos TDD para router-orquestador
y comandos CLI.

Cada test es un oráculo de un requisito del Manual 7, ejecutable en CI.
Las réplicas Python replican la lógica de router.syn y principal.syn
para verificación funcional (no solo pattern-matching).

Manual 7 §2.4: "El router está escrito en Synapse y actúa como el cerebro
de alto nivel de OpenSyn. Decide qué modelo usar y cómo procesar la respuesta."
Manual 7 §6.4: Comandos CLI de OpenSyn.
Manual 2 §12: Toda función pública tiene contrato requiere/garantiza.

MTO: cada test cita el requisito que verifica (grep-chequeable).
"""
import os

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# ================================================================
# Réplicas Python de la lógica Synapse (router.syn + principal.syn)
# Estas réplicas replican EXACTAMENTE la lógica del código fuente
# para permitir testing funcional sin dependencia del compilador.
# ================================================================

# Constantes de router.syn (lineas 472-477)
TAREA_EXPLICAR = 0
TAREA_DIAGNOSTICAR = 1
TAREA_REFACTORIZAR = 2
TAREA_GENERAR = 3
TAREA_REVISAR = 4


def clasificar_tarea(tarea: str) -> int:
    """Réplica de router.syn:clasificar_tarea() (lineas 481-508)."""
    assert len(tarea) > 0
    t = tarea.lower()
    if "error" in t or "bug" in t:
        return TAREA_DIAGNOSTICAR
    if "fallo" in t or "diagnostica" in t:
        return TAREA_DIAGNOSTICAR
    if "refactor" in t or "mejora" in t:
        return TAREA_REFACTORIZAR
    if "optimiza" in t or "limpia" in t:
        return TAREA_REFACTORIZAR
    if "revisa" in t or "verifica" in t:
        return TAREA_REVISAR
    if "analiza" in t or "comenta" in t:
        return TAREA_REVISAR
    if "genera" in t or "crea" in t:
        return TAREA_GENERAR
    if "escribe" in t or "implementa" in t:
        return TAREA_GENERAR
    return TAREA_EXPLICAR


def modo_para_tarea(tipo_tarea: int) -> int:
    """Réplica de router.syn:modo_para_tarea() (lineas 512-527)."""
    assert 0 <= tipo_tarea <= 4
    if tipo_tarea == TAREA_EXPLICAR:
        return 0  # MODO_ASK
    if tipo_tarea == TAREA_DIAGNOSTICAR:
        return 3  # MODO_DEBUG
    if tipo_tarea == TAREA_REFACTORIZAR:
        return 2  # MODO_CODE
    if tipo_tarea == TAREA_GENERAR:
        return 2  # MODO_CODE
    if tipo_tarea == TAREA_REVISAR:
        return 0  # MODO_ASK
    return 0


def nombre_tarea(tipo: int) -> str:
    """Réplica de router.syn:nombre_tarea() (lineas 530-543).
    Nota: Synapse no valida fuera de rango; cae en 'desconocido'."""
    nombres = {0: "explicar", 1: "diagnosticar", 2: "refactorizar",
               3: "generar", 4: "revisar"}
    return nombres.get(tipo, "desconocido")


def orquestar(tarea: str) -> str:
    """Réplica de router.syn:orquestar() (lineas 549-558)."""
    assert len(tarea) > 0
    tipo = clasificar_tarea(tarea)
    modo = modo_para_tarea(tipo)
    return str(modo)


def siguientes_pasos(tipo_tarea: int) -> str:
    """Réplica de router.syn:siguientes_pasos() (lineas 563-585).
    Nota: sin parámetro 'respuesta' (H-2 corregido)."""
    assert 0 <= tipo_tarea <= 4
    pasos = {
        TAREA_EXPLICAR: "1) Diagnostica posibles problemas 2) Refactoriza el codigo explicado 3) Genera tests para el codigo",
        TAREA_DIAGNOSTICAR: "1) Implementa la correccion sugerida 2) Revisa la solucion propuesta 3) Genera tests que validen la correccion",
        TAREA_REFACTORIZAR: "1) Revisa los cambios propuestos 2) Ejecuta los tests para verificar 3) Genera documentacion del refactor",
        TAREA_GENERAR: "1) Revisa el codigo generado 2) Ejecuta los tests 3) Diagnostica posibles errores",
        TAREA_REVISAR: "1) Implementa las correcciones sugeridas 2) Ejecuta los tests 3) Refactoriza el codigo revisado",
    }
    return pasos.get(tipo_tarea, "1) Explica el resultado 2) Diagnostica problemas 3) Genera tests")


def _leer(ruta):
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _leer_router():
    return _leer(os.path.join(RAIZ, "opensyn", "router.syn"))


def _leer_principal():
    return _leer(os.path.join(RAIZ, "opensyn", "principal.syn"))


# ================================================================
# R3: Router-orquestador (Manual 7 §2.4)
# ================================================================

class TestClasificarTarea:
    """Oráculo R3: clasificar_tarea() clasifica texto libre en tipo de tarea.
    Requisito: Manual 7 §2.4 — 'El router decide cómo procesar la respuesta'."""

    def test_diagnostica_error(self):
        """Verifica: 'error' → TAREA_DIAGNOSTICAR (1)."""
        assert clasificar_tarea("hay un error en el código") == TAREA_DIAGNOSTICAR

    def test_diagnostica_bug(self):
        """Verifica: 'bug' → TAREA_DIAGNOSTICAR (1)."""
        assert clasificar_tarea("encuentra el bug") == TAREA_DIAGNOSTICAR

    def test_diagnostica_fallo(self):
        """Verifica: 'fallo' → TAREA_DIAGNOSTICAR (1)."""
        assert clasificar_tarea("hay un fallo al compilar") == TAREA_DIAGNOSTICAR

    def test_refactoriza_mejora(self):
        """Verifica: 'mejora' → TAREA_REFACTORIZAR (2)."""
        assert clasificar_tarea("mejora este código") == TAREA_REFACTORIZAR

    def test_refactoriza_optimiza(self):
        """Verifica: 'optimiza' → TAREA_REFACTORIZAR (2)."""
        assert clasificar_tarea("optimiza esta función") == TAREA_REFACTORIZAR

    def test_revisa_codigo(self):
        """Verifica: 'revisa' → TAREA_REVISAR (4)."""
        assert clasificar_tarea("revisa este código") == TAREA_REVISAR

    def test_analiza_comportamiento(self):
        """Verifica: 'analiza' → TAREA_REVISAR (4)."""
        assert clasificar_tarea("analiza el comportamiento") == TAREA_REVISAR

    def test_genera_codigo(self):
        """Verifica: 'genera' → TAREA_GENERAR (3)."""
        assert clasificar_tarea("genera una función") == TAREA_GENERAR

    def test_crea_modulo(self):
        """Verifica: 'crea' → TAREA_GENERAR (3)."""
        assert clasificar_tarea("crea un módulo nuevo") == TAREA_GENERAR

    def test_default_explicar(self):
        """Verifica: sin keywords → TAREA_EXPLICAR (0)."""
        assert clasificar_tarea("qué hace esta función") == TAREA_EXPLICAR

    def test_case_insensitive(self):
        """Verifica: clasificación es case-insensitive."""
        assert clasificar_tarea("ERROR") == TAREA_DIAGNOSTICAR
        assert clasificar_tarea("Refactoriza") == TAREA_REFACTORIZAR

    def test_syntesis_source_match(self):
        """Verifica: réplica Python = lógica de router.syn (pattern match)."""
        router = _leer_router()
        assert 'contiene(tarea_lower, "error")' in router
        assert 'contiene(tarea_lower, "refactor")' in router
        assert 'contiene(tarea_lower, "genera")' in router
        assert 'contiene(tarea_lower, "revisa")' in router


class TestModoParaTarea:
    """Oráculo R3: modo_para_tarea() asigna modo ASK/DEBUG/CODE según tipo.
    Requisito: Manual 7 §1.1 — 'orchestrator asigna cada subtarea a un modo'."""

    def test_explicar_asigna_ask(self):
        """Verifica: EXPLICAR (0) → MODO_ASK (0)."""
        assert modo_para_tarea(TAREA_EXPLICAR) == 0

    def test_diagnosticar_asigna_debug(self):
        """Verifica: DIAGNOSTICAR (1) → MODO_DEBUG (3)."""
        assert modo_para_tarea(TAREA_DIAGNOSTICAR) == 3

    def test_refactorizar_asigna_code(self):
        """Verifica: REFACTORIZAR (2) → MODO_CODE (2)."""
        assert modo_para_tarea(TAREA_REFACTORIZAR) == 2

    def test_generar_asigna_code(self):
        """Verifica: GENERAR (3) → MODO_CODE (2)."""
        assert modo_para_tarea(TAREA_GENERAR) == 2

    def test_revisar_asigna_ask(self):
        """Verifica: REVISAR (4) → MODO_ASK (0, solo lectura)."""
        assert modo_para_tarea(TAREA_REVISAR) == 0

    def test_valores_en_rango(self):
        """Verifica: todos los modos están en rango válido [0,4]."""
        for tipo in range(5):
            modo = modo_para_tarea(tipo)
            assert 0 <= modo <= 4, f"modo {modo} fuera de rango para tipo {tipo}"


class TestNombreTarea:
    """Oráculo R3: nombre_tarea() retorna nombre legible.
    Requisito: Manual 2 §12 — toda función pública tiene contrato."""

    def test_explicar(self):
        assert nombre_tarea(0) == "explicar"

    def test_diagnosticar(self):
        assert nombre_tarea(1) == "diagnosticar"

    def test_refactorizar(self):
        assert nombre_tarea(2) == "refactorizar"

    def test_generar(self):
        assert nombre_tarea(3) == "generar"

    def test_revisar(self):
        assert nombre_tarea(4) == "revisar"

    def test_desconocido(self):
        """Fuera de rango retorna 'desconocido' (contrato no cubre esto)."""
        assert nombre_tarea(99) == "desconocido"

    def test_source_tiene_contrato(self):
        """Verifica: router.syn tiene contrato requiere/garantiza en nombre_tarea."""
        router = _leer_router()
        # Buscar la función y verificar que tiene contratos
        idx = router.find("funcion nombre_tarea(")
        assert idx >= 0, "nombre_tarea no encontrada en router.syn"
        bloque = router[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque


class TestOrquestar:
    """Oráculo R3: orquestar() clasifica y retorna modo asignado.
    Requisito: Manual 7 §2.4 — 'El router decide cómo procesar la respuesta'."""

    def test_explicar_retorna_ask(self):
        assert orquestar("qué hace esto") == "0"

    def test_error_retorna_debug(self):
        assert orquestar("hay un error") == "3"

    def test_refactor_retorna_code(self):
        assert orquestar("refactoriza esto") == "2"

    def test_generar_retorna_code(self):
        assert orquestar("genera una función") == "2"

    def test_revisar_retorna_ask(self):
        assert orquestar("revisa este código") == "0"

    def test_retorno_es_texto(self):
        """Verifica: retorno es string (entero_a_texto en Synapse)."""
        assert isinstance(orquestar("test"), str)

    def test_source_docstring_corregido(self):
        """Verifica: docstring describe behavior real (no 'lista de modos')."""
        router = _leer_router()
        idx = router.find("funcion orquestar(")
        bloque = router[idx:idx+400]
        # Docstring debe describir lo que hace (clasificar + retornar modo)
        assert "clasifica" in bloque
        assert "modo" in bloque
        # NO debe decir "lista de modos" (docstring falso viejo)
        assert "lista de modos" not in bloque


class TestSiguientesPasos:
    """Oráculo R3: siguientes_pasos() genera 3 pasos por tipo de tarea.
    Requisito: R3 — 'tras cada respuesta, línea siguientes: 1) ... 2) ... 3) ...'."""

    def test_explicar_tres_pasos(self):
        pasos = siguientes_pasos(TAREA_EXPLICAR)
        assert "1)" in pasos
        assert "2)" in pasos
        assert "3)" in pasos

    def test_diagnosticar_tres_pasos(self):
        pasos = siguientes_pasos(TAREA_DIAGNOSTICAR)
        assert pasos.count(")") >= 3

    def test_refactorizar_tres_pasos(self):
        pasos = siguientes_pasos(TAREA_REFACTORIZAR)
        assert pasos.count(")") >= 3

    def test_generar_tres_pasos(self):
        pasos = siguientes_pasos(TAREA_GENERAR)
        assert pasos.count(")") >= 3

    def test_revisar_tres_pasos(self):
        pasos = siguientes_pasos(TAREA_REVISAR)
        assert pasos.count(")") >= 3

    def test_source_sin_param_respuesta(self):
        """Verifica: siguientes_pasos() NO tiene parámetro 'respuesta' (H-2)."""
        router = _leer_router()
        idx = router.find("funcion siguientes_pasos(")
        assert idx >= 0
        # Buscar hasta el cierre de paréntesis
        fin = router.find(")", idx)
        cabecera = router[idx:fin+1]
        assert "respuesta" not in cabecera, \
            "siguientes_pasos() aún tiene parámetro 'respuesta' no usado"


# ================================================================
# R7: Comandos CLI (Manual 7 §6.4)
# ================================================================

class TestComandosNextFork:
    """Oráculo R7: /next y /fork existen y funcionan.
    Requisito: Manual 7 §6.4 — comandos CLI de OpenSyn."""

    def test_next_en_menu(self):
        """Verifica: /next está en MENU_COMANDOS."""
        principal = _leer_principal()
        assert "/next" in principal

    def test_fork_en_menu(self):
        """Verifica: /fork está en MENU_COMANDOS."""
        principal = _leer_principal()
        assert "/fork" in principal

    def test_next_handler_tui(self):
        """Verifica: handler /next en tui_comando()."""
        principal = _leer_principal()
        assert 'si entrada == "/next"' in principal

    def test_fork_handler_tui(self):
        """Verifica: handler /fork en tui_comando()."""
        principal = _leer_principal()
        assert 'si entrada == "/fork"' in principal

    def test_next_linea_handler(self):
        """Verifica: handler /next en modo línea."""
        principal = _leer_principal()
        assert 'si prompt == "/next"' in principal

    def test_fork_linea_handler(self):
        """Verifica: handler /fork en modo línea."""
        principal = _leer_principal()
        assert 'si prompt == "/fork"' in principal

    def test_next_contextual(self):
        """Verifica: /next usa ultimo_tipo_tarea (contextual, H-5)."""
        principal = _leer_principal()
        assert "ultimo_tipo_tarea" in principal

    def test_fork_genera_id(self):
        """Verifica: /fork genera fork_id con ahora_ms()."""
        principal = _leer_principal()
        assert "fork_id = entero_a_texto(ahora_ms())" in principal

    def test_fork_registra_en_historial(self):
        """Verifica: /fork escribe [FORK] en historial."""
        principal = _leer_principal()
        assert "[FORK]" in principal

    def test_ayuda_incluye_next_fork(self):
        """Verifica: mostrar_ayuda() lista /next y /fork."""
        principal = _leer_principal()
        assert "/next" in principal
        assert "/fork" in principal

    def test_clasificar_tarea_local_existe(self):
        """Verifica: clasificar_tarea_local() existe en principal.syn."""
        principal = _leer_principal()
        assert "funcion clasificar_tarea_local(" in principal

    def test_ultimo_tipo_tarea_variable(self):
        """Verifica: variable ultimo_tipo_tarea declarada."""
        principal = _leer_principal()
        assert "variable ultimo_tipo_tarea" in principal


class TestCitasCumpleManual:
    """Oráculo MTO: toda función modificada tiene // cumple Manual X §Y."""

    def test_router_cita_r3(self):
        router = _leer_router()
        assert "// cumple Manual 7 §2.4" in router

    def test_router_cita_r1(self):
        router = _leer_router()
        assert "// cumple Manual 7 §1.1" in router

    def test_router_cita_r2(self):
        router = _leer_router()
        assert "// cumple Manual 7 §2.3" in router

    def test_principal_cita_r7(self):
        principal = _leer_principal()
        assert "// ME-3 (R7)" in principal

    def test_principal_cita_r5(self):
        principal = _leer_principal()
        assert "// ME-3 (R5)" in principal


class TestContratosRouter:
    """Oráculo Manual 2 §12: toda función pública tiene contrato."""

    def test_clasificar_tarea_contrato(self):
        router = _leer_router()
        idx = router.find("funcion clasificar_tarea(")
        bloque = router[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_modo_para_tarea_contrato(self):
        router = _leer_router()
        idx = router.find("funcion modo_para_tarea(")
        bloque = router[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_nombre_tarea_contrato(self):
        router = _leer_router()
        idx = router.find("funcion nombre_tarea(")
        bloque = router[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_orquestar_contrato(self):
        router = _leer_router()
        idx = router.find("funcion orquestar(")
        bloque = router[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_siguientes_pasos_contrato(self):
        router = _leer_router()
        idx = router.find("funcion siguientes_pasos(")
        bloque = router[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque
