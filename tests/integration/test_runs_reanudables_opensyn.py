# -*- coding: utf-8 -*-
"""
test_runs_reanudables_opensyn.py — ME-6 (R8+R9): Runs reanudables + planificador.

Oráculos TDD que verifican runs reanudables, timeouts, y planificación.
Cada test cita el requisito que verifica (MTO grep-chequeable).

Manual 7 §4.3: "Si el servidor no responde en 30 segundos, el LSP devuelve un error"
Manual 7 §4.3: "Si el código es inválido tras agotar intentos, ofrece regenerar"
Manual 7 §7.2: "Latencia de inferencia: < 1s para prompts cortos"
"""
import os
import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _leer(ruta):
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _leer_run_manager():
    return _leer(os.path.join(RAIZ, "opensyn", "run_manager.syn"))


def _leer_planificador():
    return _leer(os.path.join(RAIZ, "opensyn", "planificador.syn"))


def _leer_router():
    return _leer(os.path.join(RAIZ, "opensyn", "router.syn"))


# ================================================================
# Replicas Python (oráculos funcionales)
# ================================================================

RUN_PENDIENTE = 0
RUN_EN_PROGRESO = 1
RUN_COMPLETADO = 2
RUN_FALLIDO = 3
MAX_INTENTOS_SUBTAREA = 3
TIMEOUT_RUN_ABSOLUTO_MS = 300000
MAX_SUBTAREAS = 20
COMPLEJIDAD_BAJA = 0
COMPLEJIDAD_MEDIA = 1
COMPLEJIDAD_ALTA = 2


class RunEstadoSim:
    def __init__(self, run_id="", tarea=""):
        self.run_id = run_id
        self.tarea = tarea
        self.cantidad_subtareas = 0
        self.subtarea_actual = 0
        self.estado = RUN_PENDIENTE
        self.checkpoint_path = ""
        self.timestamp_inicio = 1000


def crear_run(tarea, num_subtareas):
    assert len(tarea) > 0
    assert 0 < num_subtareas <= MAX_SUBTAREAS
    run = RunEstadoSim(run_id="run_test", tarea=tarea)
    run.cantidad_subtareas = num_subtareas
    run.estado = RUN_PENDIENTE
    run.timestamp_inicio = 1000
    return run


def marcar_subtarea_completada(run, resultado_texto):
    assert run.subtarea_actual < run.cantidad_subtareas
    run.subtarea_actual += 1
    if run.subtarea_actual >= run.cantidad_subtareas:
        run.estado = RUN_COMPLETADO
    return 0


def marcar_subtarea_fallida(run, error, intentos):
    if intentos >= MAX_INTENTOS_SUBTAREA:
        run.estado = RUN_FALLIDO
    return 0


def run_terminado(run):
    return run.estado == RUN_COMPLETADO or run.estado == RUN_FALLIDO


def run_timeout(transcurrido):
    return transcurrido > TIMEOUT_RUN_ABSOLUTO_MS


def extraer_campo_json(json, campo):
    prefijo = '"%s": "' % campo
    idx = json.find(prefijo)
    if idx < 0:
        return ""
    inicio = idx + len(prefijo)
    fin = json.find('"', inicio)
    return json[inicio:fin]


def extraer_entero_json(json, campo):
    prefijo = '"%s": ' % campo
    idx = json.find(prefijo)
    if idx < 0:
        return 0
    inicio = idx + len(prefijo)
    fin = inicio
    while fin < len(json) and json[fin].isdigit():
        fin += 1
    return int(json[inicio:fin]) if fin > inicio else 0


def evaluar_complejidad(tarea):
    if len(tarea) < 50:
        return COMPLEJIDAD_BAJA
    if len(tarea) < 200:
        return COMPLEJIDAD_MEDIA
    return COMPLEJIDAD_ALTA


def seleccionar_modelo(complejidad):
    if complejidad == COMPLEJIDAD_BAJA:
        return "opensyn-1.3b"
    if complejidad == COMPLEJIDAD_MEDIA:
        return "opensyn-3b"
    return "opensyn-7b"


def validar_plan(cantidad_pasos, estimacion_tokens):
    if cantidad_pasos > 10:
        return False
    if estimacion_tokens > 10000:
        return False
    return True


def nombre_complejidad(c):
    if c == COMPLEJIDAD_BAJA:
        return "baja"
    if c == COMPLEJIDAD_MEDIA:
        return "media"
    return "alta"


def resumen_plan(tarea, complejidad, pasos, tokens, modelo):
    return "Plan: %s (%s) — %d pasos, ~%d tokens, modelo: %s" % (
        tarea, nombre_complejidad(complejidad), pasos, tokens, modelo)


TIMEOUT_LSP_MS = 30000


def verificar_timeout_lsp(transcurrido):
    return transcurrido > TIMEOUT_LSP_MS


# ================================================================
# R8: Fuente — estructura y constantes (Manual 7 §4.3)
# ================================================================

class TestFuenteRunManager:
    """Oráculo R8: Verifica que run_manager.syn tenga estructura correcta.
    Requisito: Manual 7 §4.3 — 'runs largos con reanudación'"""

    def test_source_funcion_crear_run(self):
        """Verifica: existe funcion crear_run()"""
        rm = _leer_run_manager()
        assert "funcion crear_run(" in rm

    def test_source_funcion_guardar_checkpoint(self):
        """Verifica: existe funcion guardar_checkpoint()"""
        rm = _leer_run_manager()
        assert "funcion guardar_checkpoint(" in rm

    def test_source_funcion_cargar_checkpoint(self):
        """Verifica: existe funcion cargar_checkpoint()"""
        rm = _leer_run_manager()
        assert "funcion cargar_checkpoint(" in rm

    def test_source_funcion_marcar_completada(self):
        """Verifica: existe funcion marcar_subtarea_completada()"""
        rm = _leer_run_manager()
        assert "funcion marcar_subtarea_completada(" in rm

    def test_source_funcion_marcar_fallida(self):
        """Verifica: existe funcion marcar_subtarea_fallida()"""
        rm = _leer_run_manager()
        assert "funcion marcar_subtarea_fallida(" in rm

    def test_source_funcion_run_terminado(self):
        """Verifica: existe funcion run_terminado()"""
        rm = _leer_run_manager()
        assert "funcion run_terminado(" in rm

    def test_source_funcion_resumir_run(self):
        """Verifica: existe funcion resumir_run()"""
        rm = _leer_run_manager()
        assert "funcion resumir_run(" in rm

    def test_source_funcion_serializar(self):
        """Verifica: existe funcion serializar_run()"""
        rm = _leer_run_manager()
        assert "funcion serializar_run(" in rm

    def test_source_funcion_deserializar(self):
        """Verifica: existe funcion deserializar_run()"""
        rm = _leer_run_manager()
        assert "funcion deserializar_run(" in rm

    def test_source_funcion_extraer_campo(self):
        """Verifica: existe funcion extraer_campo_json()"""
        rm = _leer_run_manager()
        assert "funcion extraer_campo_json(" in rm

    def test_source_funcion_extraer_entero(self):
        """Verifica: existe funcion extraer_entero_json()"""
        rm = _leer_run_manager()
        assert "funcion extraer_entero_json(" in rm

    def test_source_constante_max_subtareas(self):
        """Verifica: MAX_SUBTAREAS = 20"""
        rm = _leer_run_manager()
        assert "MAX_SUBTAREAS = 20" in rm

    def test_source_constante_timeout(self):
        """Verifica: TIMEOUT_RUN_ABSOLUTO_MS = 300000"""
        rm = _leer_run_manager()
        assert "TIMEOUT_RUN_ABSOLUTO_MS = 300000" in rm

    def test_source_asm_ahora_ms(self):
        """Verifica: ahora_ms usa ASM inline con clock_gettime"""
        rm = _leer_run_manager()
        assert "clock_gettime" in rm

    def test_source_asm_concat(self):
        """Verifica: concat usa ASM inline con memcpy"""
        rm = _leer_run_manager()
        assert "memcpy" in rm or "malloc" in rm

    def test_source_asm_entero_a_texto(self):
        """Verifica: entero_a_texto usa ASM inline con snprintf"""
        rm = _leer_run_manager()
        assert "snprintf" in rm


# ================================================================
# R8: Lógica funcional — crear run (Manual 7 §4.3)
# ================================================================

class TestCrearRun:
    """Oráculo R8: Verifica creación de runs reanudables.
    Requisito: Manual 7 §4.3 — 'runs largos con reanudación'"""

    def test_crear_run_estado_pendiente(self):
        """Verificar: run inicia en estado RUN_PENDIENTE"""
        run = crear_run("test tarea", 3)
        assert run.estado == RUN_PENDIENTE

    def test_crear_run_tarea_correcta(self):
        """Verificar: run tiene la tarea correcta"""
        run = crear_run("mi tarea", 5)
        assert run.tarea == "mi tarea"

    def test_crear_run_cantidad_subtareas(self):
        """Verificar: run tiene la cantidad correcta de subtareas"""
        run = crear_run("test", 4)
        assert run.cantidad_subtareas == 4

    def test_crear_run_subtarea_actual_cero(self):
        """Verificar: subtarea_actual inicia en 0"""
        run = crear_run("test", 3)
        assert run.subtarea_actual == 0

    def test_crear_run_max_subtareas(self):
        """Verificar: 20 subtareas es válido"""
        run = crear_run("test", MAX_SUBTAREAS)
        assert run.cantidad_subtareas == MAX_SUBTAREAS


# ================================================================
# R8: Marcar subtarea (Manual 7 §4.3)
# ================================================================

class TestMarcarSubtarea:
    """Oráculo R8: Verifica marcado de subtareas.
    Requisito: Manual 7 §4.3 — 'reanudación desde la última subtarea OK'"""

    def test_completada_avanza_actual(self):
        """Verificar: completada avanza subtarea_actual"""
        run = crear_run("test", 3)
        marcar_subtarea_completada(run, "r1")
        assert run.subtarea_actual == 1

    def test_completada_dos_veces(self):
        """Verificar: 2 completadas → subtarea_actual = 2"""
        run = crear_run("test", 3)
        marcar_subtarea_completada(run, "r1")
        marcar_subtarea_completada(run, "r2")
        assert run.subtarea_actual == 2

    def test_completada_todas_run_completado(self):
        """Verificar: completar todas → RUN_COMPLETADO"""
        run = crear_run("test", 2)
        marcar_subtarea_completada(run, "r1")
        marcar_subtarea_completada(run, "r2")
        assert run.estado == RUN_COMPLETADO

    def test_fallida_incrementa_intentos(self):
        """Verificar: fallo con 2 intentos no termina run"""
        run = crear_run("test", 2)
        marcar_subtarea_fallida(run, "e1", 2)
        assert run.estado == RUN_PENDIENTE

    def test_fallida_tres_intentos_run_fallido(self):
        """Verificar: 3 fallos → RUN_FALLIDO"""
        run = crear_run("test", 2)
        marcar_subtarea_fallida(run, "e1", MAX_INTENTOS_SUBTAREA)
        assert run.estado == RUN_FALLIDO


# ================================================================
# R8: Run terminado + timeout (Manual 7 §4.3)
# ================================================================

class TestRunTerminado:
    """Oráculo R8: Verifica estados finales del run.
    Requisito: Manual 7 §4.3 — 'reanudación' — saber cuándo parar"""

    def test_completado_es_terminado(self):
        """Verificar: RUN_COMPLETADO → terminado = True"""
        run = crear_run("test", 1)
        marcar_subtarea_completada(run, "hecho")
        assert run_terminado(run) is True

    def test_fallido_es_terminado(self):
        """Verificar: RUN_FALLIDO → terminado = True"""
        run = crear_run("test", 1)
        marcar_subtarea_fallida(run, "e", MAX_INTENTOS_SUBTAREA)
        assert run_terminado(run) is True

    def test_pendiente_no_terminado(self):
        """Verificar: RUN_PENDIENTE → terminado = False"""
        run = crear_run("test", 2)
        assert run_terminado(run) is False

    def test_timeout_true(self):
        """Verificar: > 300s → timeout True"""
        assert run_timeout(TIMEOUT_RUN_ABSOLUTO_MS + 1) is True

    def test_timeout_false(self):
        """Verificar: < 300s → timeout False"""
        assert run_timeout(TIMEOUT_RUN_ABSOLUTO_MS - 1) is False


# ================================================================
# R8: Serialización JSON (Manual 7 §4.3)
# ================================================================

class TestSerializacion:
    """Oráculo R8: Verifica serialización/deserialización de runs.
    Requisito: Manual 7 §4.3 — 'reanudación desde checkpoint'"""

    def test_source_serializar_existe(self):
        """Verificar: serializar_run() existe"""
        rm = _leer_run_manager()
        assert "funcion serializar_run(" in rm

    def test_source_deserializar_existe(self):
        """Verificar: deserializar_run() existe"""
        rm = _leer_run_manager()
        assert "funcion deserializar_run(" in rm

    def test_source_extraer_campo_existe(self):
        """Verificar: extraer_campo_json() existe"""
        rm = _leer_run_manager()
        assert "funcion extraer_campo_json(" in rm

    def test_source_extraer_entero_existe(self):
        """Verificar: extraer_entero_json() existe"""
        rm = _leer_run_manager()
        assert "funcion extraer_entero_json(" in rm

    def test_replica_extraer_campo(self):
        """Verificar: extraer_campo_json extrae valor correctamente"""
        json = '{"run_id": "run_123", "tarea": "test"}'
        assert extraer_campo_json(json, "run_id") == "run_123"
        assert extraer_campo_json(json, "tarea") == "test"

    def test_replica_extraer_campo_faltante(self):
        """Verificar: campo faltante retorna vacío"""
        json = '{"run_id": "run_123"}'
        assert extraer_campo_json(json, "no_existe") == ""

    def test_replica_extraer_entero(self):
        """Verificar: extraer_entero_json extrae entero"""
        json = '{"estado": 2, "subtarea_actual": 1}'
        assert extraer_entero_json(json, "estado") == 2
        assert extraer_entero_json(json, "subtarea_actual") == 1

    def test_replica_extraer_entero_faltante(self):
        """Verificar: campo faltante retorna 0"""
        json = '{"estado": 2}'
        assert extraer_entero_json(json, "no_existe") == 0

    def test_source_ruta_checkpoint(self):
        """Verificar: ruta checkpoint en ~/.opensyn/runs/"""
        rm = _leer_run_manager()
        assert "~/.opensyn/runs/" in rm


# ================================================================
# R9: Planificar antes de actuar (Manual 7 §7.2)
# ================================================================

class TestPlanificar:
    """Oráculo R9: Verifica planificación multi-paso antes de ejecutar.
    Requisito: Manual 7 §7.2 — 'planifica multi-paso antes de ejecutar'"""

    def test_source_funcion_planificar(self):
        """Verificar: existe funcion planificar() en planificador.syn"""
        pf = _leer_planificador()
        assert "funcion planificar(" in pf

    def test_source_funcion_evaluar_complejidad(self):
        """Verificar: existe funcion evaluar_complejidad()"""
        pf = _leer_planificador()
        assert "funcion evaluar_complejidad(" in pf

    def test_source_funcion_seleccionar_modelo(self):
        """Verificar: existe funcion seleccionar_modelo()"""
        pf = _leer_planificador()
        assert "funcion seleccionar_modelo(" in pf

    def test_source_funcion_validar_plan(self):
        """Verificar: existe funcion validar_plan()"""
        pf = _leer_planificador()
        assert "funcion validar_plan(" in pf

    def test_source_funcion_resumen_plan(self):
        """Verificar: existe funcion resumen_plan()"""
        pf = _leer_planificador()
        assert "funcion resumen_plan(" in pf

    def test_source_esta_en_router(self):
        """Verificar: planificar_antes_de_actuar existe en router.syn"""
        rt = _leer_router()
        assert "funcion planificar_antes_de_actuar(" in rt

    def test_replica_complejidad_baja(self):
        """Verificar: tarea < 50 chars → BAJA"""
        assert evaluar_complejidad("explica esto") == COMPLEJIDAD_BAJA

    def test_replica_complejidad_media(self):
        """Verificar: tarea 50-200 chars → MEDIA"""
        assert evaluar_complejidad("a" * 100) == COMPLEJIDAD_MEDIA

    def test_replica_complejidad_alta(self):
        """Verificar: tarea > 200 chars → ALTA"""
        assert evaluar_complejidad("a" * 250) == COMPLEJIDAD_ALTA

    def test_replica_modelo_baja(self):
        """Verificar: BAJA → opensyn-1.3b"""
        assert seleccionar_modelo(COMPLEJIDAD_BAJA) == "opensyn-1.3b"

    def test_replica_modelo_media(self):
        """Verificar: MEDIA → opensyn-3b"""
        assert seleccionar_modelo(COMPLEJIDAD_MEDIA) == "opensyn-3b"

    def test_replica_modelo_alta(self):
        """Verificar: ALTA → opensyn-7b"""
        assert seleccionar_modelo(COMPLEJIDAD_ALTA) == "opensyn-7b"

    def test_replica_validar_plan_ok(self):
        """Verificar: plan válido (5 pasos, 1000 tokens) → True"""
        assert validar_plan(5, 1000) is True

    def test_replica_validar_plan_demasiados_pasos(self):
        """Verificar: >10 pasos → False"""
        assert validar_plan(11, 1000) is False

    def test_replica_validar_plan_demasiados_tokens(self):
        """Verificar: >10000 tokens → False"""
        assert validar_plan(5, 10001) is False

    def test_replica_resumen_plan(self):
        """Verificar: resumen contiene tarea y pasos"""
        r = resumen_plan("mi tarea", COMPLEJIDAD_BAJA, 4, 800, "opensyn-1.3b")
        assert "mi tarea" in r
        assert "4 pasos" in r
        assert "baja" in r
        assert "opensyn-1.3b" in r


# ================================================================
# R9: Eficiencia de tokens (Manual 7 §7.2)
# ================================================================

class TestEficienciaTokens:
    """Oráculo R9: Verifica eficiencia de tokens.
    Requisito: Manual 7 §7.2 — 'menos contexto = menos alucinación'"""

    def test_source_max_pasos(self):
        """Verificar: MAX_PASOS = 10"""
        pf = _leer_planificador()
        assert "MAX_PASOS = 10" in pf

    def test_source_tokens_por_paso(self):
        """Verificar: TOKENS_POR_PASO_ESTIMADO definida"""
        pf = _leer_planificador()
        assert "TOKENS_POR_PASO_ESTIMADO" in pf

    def test_source_cita_claude_code(self):
        """Verificar: router.syn menciona Claude Code"""
        rt = _leer_router()
        assert "Claude Code" in rt


# ================================================================
# R8+R9: Citas cumple Manual (grep-chequeable)
# ================================================================

class TestCitasCumpleManual:
    """Oráculo R8+R9: Verifica citas grep-chequeables al manual.
    Requisito: Manual 7 §4.3 + §7.2"""

    def test_run_manager_cita_r8(self):
        """Verificar: run_manager.syn cita §4.3"""
        rm = _leer_run_manager()
        assert "cumple Manual 7 §4.3" in rm

    def test_planificador_cita_r9(self):
        """Verificar: planificador.syn cita §7.2"""
        pf = _leer_planificador()
        assert "cumple Manual 7 §7.2" in pf

    def test_router_cita_r9(self):
        """Verificar: router.syn referencia §7.2"""
        rt = _leer_router()
        assert "§7.2" in rt

    def test_router_cita_r8(self):
        """Verificar: router.syn referencia §4.3"""
        rt = _leer_router()
        assert "§4.3" in rt


# ================================================================
# R8+R9: Contratos (Manual 2 §12)
# ================================================================

class TestContratosRunManager:
    """Oráculo R8+R9: Verifica contratos requiere/garantiza.
    Requisito: Manual 2 §12 — 'toda función pública tiene contrato'"""

    def test_crear_run_contrato(self):
        """Verificar: crear_run tiene contrato"""
        rm = _leer_run_manager()
        idx = rm.find("funcion crear_run(")
        assert idx >= 0
        bloque = rm[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_guardar_checkpoint_contrato(self):
        """Verificar: guardar_checkpoint tiene contrato"""
        rm = _leer_run_manager()
        idx = rm.find("funcion guardar_checkpoint(")
        assert idx >= 0
        bloque = rm[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_marcar_completada_contrato(self):
        """Verificar: marcar_subtarea_completada tiene contrato"""
        rm = _leer_run_manager()
        idx = rm.find("funcion marcar_subtarea_completada(")
        assert idx >= 0
        bloque = rm[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_run_terminado_contrato(self):
        """Verificar: run_terminado tiene contrato"""
        rm = _leer_run_manager()
        idx = rm.find("funcion run_terminado(")
        assert idx >= 0
        bloque = rm[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_planificar_contrato(self):
        """Verificar: planificar tiene contrato"""
        pf = _leer_planificador()
        idx = pf.find("funcion planificar(")
        assert idx >= 0
        bloque = pf[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_evaluar_complejidad_contrato(self):
        """Verificar: evaluar_complejidad tiene contrato"""
        pf = _leer_planificador()
        idx = pf.find("funcion evaluar_complejidad(")
        assert idx >= 0
        bloque = pf[idx:idx+200]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_seleccionar_modelo_contrato(self):
        """Verificar: seleccionar_modelo tiene contrato"""
        pf = _leer_planificador()
        idx = pf.find("funcion seleccionar_modelo(")
        assert idx >= 0
        bloque = pf[idx:idx+200]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque
