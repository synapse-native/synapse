# -*- coding: utf-8 -*-
"""
test_runs_reanudables_opensyn.py — ME-6 (R8+R9): Runs reanudables + planificador.

Oráculos TDD que verifican runs reanudables, checkpoints, timeouts,
y planificación antes de actuar. Cada test cita el requisito (MTO grep-chequeable).

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
# Replicas Python de la lógica Synapse (oráculos funcionales)
# ================================================================

RUN_PENDIENTE = 0
RUN_EN_PROGRESO = 1
RUN_COMPLETADO = 2
RUN_FALLIDO = 3
RUN_PAUSADO = 4

SUBTAREA_PENDIENTE = 0
SUBTAREA_EN_PROGRESO = 1
SUBTAREA_COMPLETADA = 2
SUBTAREA_FALLIDA = 3

MAX_INTENTOS_SUBTAREA = 3
TIMEOUT_INFERENCIA_MS = 30000
TIMEOUT_RUN_ABSOLUTO_MS = 300000
MAX_SUBTAREAS = 20

COMPLEJIDAD_BAJA = 0
COMPLEJIDAD_MEDIA = 1
COMPLEJIDAD_ALTA = 2


class Subtarea:
    def __init__(self, id=0, descripcion="", estado=SUBTAREA_PENDIENTE):
        self.id = id
        self.descripcion = descripcion
        self.estado = estado
        self.resultado = ""
        self.dependencias = ""
        self.intentos = 0


class RunEstado:
    def __init__(self, run_id="", tarea=""):
        self.run_id = run_id
        self.tarea = tarea
        self.subtareas = []
        self.subtarea_actual = 0
        self.estado = RUN_PENDIENTE
        self.checkpoint_path = ""
        self.timestamp_inicio = 0
        self.timestamp_ultimo_checkpoint = 0


def crear_run(tarea, cantidad_subtareas):
    assert len(tarea) > 0
    assert 0 < cantidad_subtareas <= MAX_SUBTAREAS
    run = RunEstado(run_id="run_test", tarea=tarea)
    for i in range(cantidad_subtareas):
        run.subtareas.append(Subtarea(id=i, descripcion="paso %d" % i))
    run.cantidad_subtareas_simulada = cantidad_subtareas
    run.estado = RUN_PENDIENTE
    run.timestamp_inicio = 1000
    return run


def siguiente_subtarea(run):
    i = run.subtarea_actual
    while i < len(run.subtareas):
        if run.subtareas[i].estado == SUBTAREA_PENDIENTE:
            return run.subtareas[i]
        i += 1
    return Subtarea(id=-1)


def marcar_subtarea(run, id_subtarea, resultado_texto):
    for sub in run.subtareas:
        if sub.id == id_subtarea:
            sub.estado = SUBTAREA_COMPLETADA
            sub.resultado = resultado_texto
            run.subtarea_actual += 1
            if run.subtarea_actual >= len(run.subtareas):
                run.estado = RUN_COMPLETADO
            return 0
    return -1


def marcar_subtarea_fallida(run, id_subtarea, error):
    for sub in run.subtareas:
        if sub.id == id_subtarea:
            sub.estado = SUBTAREA_FALLIDA
            sub.resultado = error
            sub.intentos += 1
            if sub.intentos >= MAX_INTENTOS_SUBTAREA:
                run.estado = RUN_FALLIDO
            return 0
    return -1


def run_completado(run):
    return run.estado == RUN_COMPLETADO or run.estado == RUN_FALLIDO


def run_timeout(transcurrido):
    return transcurrido > TIMEOUT_RUN_ABSOLUTO_MS


TIMEOUT_LSP_MS = 30000


def verificar_timeout_lsp(transcurrido):
    return transcurrido > TIMEOUT_LSP_MS


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


def resumen_plan(tarea, complejidad, cantidad_pasos, tokens):
    return "Plan: %s (%s) — %d pasos, ~%d tokens" % (
        tarea, nombre_complejidad(complejidad), cantidad_pasos, tokens)


# ================================================================
# R8: Crear run (Manual 7 §4.3)
# ================================================================

class TestCrearRun:
    """Oráculo R8: Verifica creación de runs reanudables.
    Requisito: Manual 7 §4.3 — 'runs largos con reanudación'"""

    def test_source_funcion_existe(self):
        """Verifica: existe funcion crear_run() en run_manager.syn"""
        rm = _leer_run_manager()
        assert "funcion crear_run(" in rm

    def test_source_estado_pendiente(self):
        """Verifica: run inicia en estado RUN_PENDIENTE"""
        rm = _leer_run_manager()
        assert "RUN_PENDIENTE = 0" in rm

    def test_source_max_subtareas(self):
        """Verifica: constante MAX_SUBTAREAS definida"""
        rm = _leer_run_manager()
        assert "MAX_SUBTAREAS" in rm

    def test_replica_crear_run(self):
        """Verifica: crear_run retorna estado RUN_PENDIENTE"""
        run = crear_run("test tarea", 3)
        assert run.estado == RUN_PENDIENTE
        assert run.tarea == "test tarea"
        assert len(run.subtareas) == 3

    def test_replica_subtareas_iniciales(self):
        """Verifica: todas las subtareas inician en PENDIENTE"""
        run = crear_run("test", 4)
        for sub in run.subtareas:
            assert sub.estado == SUBTAREA_PENDIENTE


# ================================================================
# R8: Siguiente subtarea (Manual 7 §4.3)
# ================================================================

class TestSiguienteSubtarea:
    """Oráculo R8: Verifica selección de siguiente subtarea.
    Requisito: Manual 7 §4.3 — 'reanudación desde la última subtarea OK'"""

    def test_source_funcion_existe(self):
        """Verifica: existe funcion siguiente_subtarea() en run_manager.syn"""
        rm = _leer_run_manager()
        assert "funcion siguiente_subtarea(" in rm

    def test_replica_primera_subtarea(self):
        """Verifica: primera subtarea es la pendiente"""
        run = crear_run("test", 3)
        sub = siguiente_subtarea(run)
        assert sub.id == 0

    def test_replica_saltar_completadas(self):
        """Verifica: salta subtareas completadas"""
        run = crear_run("test", 3)
        marcar_subtarea(run, 0, "hecho")
        sub = siguiente_subtarea(run)
        assert sub.id == 1

    def test_replica_todas_completadas(self):
        """Verifica: retorna id=-1 cuando todas completadas"""
        run = crear_run("test", 2)
        marcar_subtarea(run, 0, "hecho1")
        marcar_subtarea(run, 1, "hecho2")
        sub = siguiente_subtarea(run)
        assert sub.id == -1


# ================================================================
# R8: Marcar subtarea (Manual 7 §4.3)
# ================================================================

class TestMarcarSubtarea:
    """Oráculo R8: Verifica marcado de subtareas.
    Requisito: Manual 7 §4.3 — 'reanudación desde la última subtarea OK'"""

    def test_source_funcion_existe(self):
        """Verifica: existe funcion marcar_subtarea() en run_manager.syn"""
        rm = _leer_run_manager()
        assert "funcion marcar_subtarea(" in rm

    def test_replica_marcar_completada(self):
        """Verifica: marcar_subtarea pone estado COMPLETADA"""
        run = crear_run("test", 3)
        r = marcar_subtarea(run, 0, "resultado")
        assert r == 0
        assert run.subtareas[0].estado == SUBTAREA_COMPLETADA
        assert run.subtareas[0].resultado == "resultado"

    def test_replica_avanzar_actual(self):
        """Verifica: avanza subtarea_actual"""
        run = crear_run("test", 3)
        marcar_subtarea(run, 0, "r1")
        assert run.subtarea_actual == 1

    def test_replica_run_completado(self):
        """Verifica: run pasa a COMPLETADO al terminar todas"""
        run = crear_run("test", 2)
        marcar_subtarea(run, 0, "r1")
        marcar_subtarea(run, 1, "r2")
        assert run.estado == RUN_COMPLETADO

    def test_replica_id_invalido(self):
        """Verifica: id inválido retorna -1"""
        run = crear_run("test", 2)
        r = marcar_subtarea(run, 99, "r")
        assert r == -1


# ================================================================
# R8: Marcar subtarea fallida (Manual 7 §4.3)
# ================================================================

class TestMarcarSubtareaFallida:
    """Oráculo R8: Verifica manejo de fallos en subtareas.
    Requisito: Manual 7 §4.3 — 'Si el código es inválido y se agotan los intentos'"""

    def test_source_funcion_existe(self):
        """Verifica: existe funcion marcar_subtarea_fallida() en run_manager.syn"""
        rm = _leer_run_manager()
        assert "funcion marcar_subtarea_fallida(" in rm

    def test_replica_fallida_incrementa_intentos(self):
        """Verifica: fallo incrementa contador de intentos"""
        run = crear_run("test", 2)
        marcar_subtarea_fallida(run, 0, "error")
        assert run.subtareas[0].intentos == 1

    def test_replica_fallida_estado(self):
        """Verifica: fallo pone estado FALLIDA"""
        run = crear_run("test", 2)
        marcar_subtarea_fallida(run, 0, "error")
        assert run.subtareas[0].estado == SUBTAREA_FALLIDA

    def test_replica_tres_fallos_run_fallido(self):
        """Verifica: 3 fallos → run FALLIDO"""
        run = crear_run("test", 2)
        marcar_subtarea_fallida(run, 0, "e1")
        marcar_subtarea_fallida(run, 0, "e2")
        marcar_subtarea_fallida(run, 0, "e3")
        assert run.estado == RUN_FALLIDO


# ================================================================
# R8: Run completado + timeout (Manual 7 §4.3)
# ================================================================

class TestRunCompletado:
    """Oráculo R8: Verifica estados finales del run.
    Requisito: Manual 7 §4.3 — 'reanudación' — saber cuándo parar"""

    def test_source_run_completado_existe(self):
        """Verifica: existe funcion run_completado() en run_manager.syn"""
        rm = _leer_run_manager()
        assert "funcion run_completado(" in rm

    def test_replica_completado_true(self):
        """Verifica: run COMPLETADO → run_completado = True"""
        run = crear_run("test", 1)
        marcar_subtarea(run, 0, "hecho")
        assert run_completado(run) is True

    def test_replica_fallido_true(self):
        """Verifica: run FALLIDO → run_completado = True"""
        run = crear_run("test", 1)
        marcar_subtarea_fallida(run, 0, "e1")
        marcar_subtarea_fallida(run, 0, "e2")
        marcar_subtarea_fallida(run, 0, "e3")
        assert run_completado(run) is True

    def test_replica_pendiente_false(self):
        """Verifica: run PENDIENTE → run_completado = False"""
        run = crear_run("test", 2)
        assert run_completado(run) is False

    def test_source_timeout_existe(self):
        """Verifica: existe funcion run_timeout() en run_manager.syn"""
        rm = _leer_run_manager()
        assert "funcion run_timeout(" in rm

    def test_replica_timeout_true(self):
        """Verifica: tiempo > 300s → timeout True"""
        assert run_timeout(300001) is True

    def test_replica_timeout_false(self):
        """Verifica: tiempo < 300s → timeout False"""
        assert run_timeout(299999) is False

    def test_source_timeout_constante(self):
        """Verifica: constante TIMEOUT_RUN_ABSOLUTO_MS = 300000"""
        rm = _leer_run_manager()
        assert "TIMEOUT_RUN_ABSOLUTO_MS = 300000" in rm


# ================================================================
# R8: Checkpoint (Manual 7 §4.3)
# ================================================================

class TestCheckpoint:
    """Oráculo R8: Verifica persistencia de checkpoints.
    Requisito: Manual 7 §4.3 — 'reanudación desde la última subtarea OK'"""

    def test_source_guardar_checkpoint(self):
        """Verifica: existe funcion guardar_checkpoint() en run_manager.syn"""
        rm = _leer_run_manager()
        assert "funcion guardar_checkpoint(" in rm

    def test_source_cargar_checkpoint(self):
        """Verifica: existe funcion cargar_checkpoint() en run_manager.syn"""
        rm = _leer_run_manager()
        assert "funcion cargar_checkpoint(" in rm

    def test_source_resumir_run(self):
        """Verifica: existe funcion resumir_run() en run_manager.syn"""
        rm = _leer_run_manager()
        assert "funcion resumir_run(" in rm

    def test_source_serializar_run(self):
        """Verifica: existe funcion serializar_run() en run_manager.syn"""
        rm = _leer_run_manager()
        assert "funcion serializar_run(" in rm

    def test_source_deserializar_run(self):
        """Verifica: existe funcion deserializar_run() en run_manager.syn"""
        rm = _leer_run_manager()
        assert "funcion deserializar_run(" in rm

    def test_source_ruta_checkpoint(self):
        """Verifica: ruta checkpoint en ~/.opensyn/runs/"""
        rm = _leer_run_manager()
        assert "~/.opensyn/runs/" in rm


# ================================================================
# R9: Planificar antes de actuar (Manual 7 §7.2)
# ================================================================

class TestPlanificar:
    """Oráculo R9: Verifica planificación multi-paso antes de ejecutar.
    Requisito: Manual 7 §7.2 — 'planifica multi-paso antes de ejecutar'"""

    def test_source_funcion_existe(self):
        """Verifica: existe funcion planificar() en planificador.syn"""
        pf = _leer_planificador()
        assert "funcion planificar(" in pf

    def test_source_esta_en_router(self):
        """Verifica: planificar_antes_de_actuar existe en router.syn"""
        rt = _leer_router()
        assert "funcion planificar_antes_de_actuar(" in rt

    def test_replica_complejidad_baja(self):
        """Verifica: tarea < 50 chars → complejidad BAJA"""
        assert evaluar_complejidad("explica esto") == COMPLEJIDAD_BAJA

    def test_replica_complejidad_media(self):
        """Verifica: tarea 50-200 chars → complejidad MEDIA"""
        assert evaluar_complejidad("a" * 100) == COMPLEJIDAD_MEDIA

    def test_replica_complejidad_alta(self):
        """Verifica: tarea > 200 chars → complejidad ALTA"""
        assert evaluar_complejidad("a" * 250) == COMPLEJIDAD_ALTA

    def test_replica_modelo_baja(self):
        """Verifica: complejidad BAJA → opensyn-1.3b"""
        assert seleccionar_modelo(COMPLEJIDAD_BAJA) == "opensyn-1.3b"

    def test_replica_modelo_media(self):
        """Verifica: complejidad MEDIA → opensyn-3b"""
        assert seleccionar_modelo(COMPLEJIDAD_MEDIA) == "opensyn-3b"

    def test_replica_modelo_alta(self):
        """Verifica: complejidad ALTA → opensyn-7b"""
        assert seleccionar_modelo(COMPLEJIDAD_ALTA) == "opensyn-7b"

    def test_replica_validar_plan_ok(self):
        """Verifica: plan válido (5 pasos, 1000 tokens) → True"""
        assert validar_plan(5, 1000) is True

    def test_replica_validar_plan_demasiados_pasos(self):
        """Verifica: plan con >10 pasos → False"""
        assert validar_plan(11, 1000) is False

    def test_replica_validar_plan_demasiados_tokens(self):
        """Verifica: plan con >10000 tokens → False"""
        assert validar_plan(5, 10001) is False

    def test_replica_resumen_plan(self):
        """Verifica: resumen contiene tarea y pasos"""
        r = resumen_plan("mi tarea", COMPLEJIDAD_BAJA, 4, 800)
        assert "mi tarea" in r
        assert "4 pasos" in r
        assert "baja" in r


# ================================================================
# R9: Eficiencia de tokens (Manual 7 §7.2)
# ================================================================

class TestEficienciaTokens:
    """Oráculo R9: Verifica eficiencia de tokens.
    Requisito: Manual 7 §7.2 — 'menos contexto = menos alucinación + menos latencia'"""

    def test_source_max_pasos(self):
        """Verifica: constante MAX_PASOS = 10"""
        pf = _leer_planificador()
        assert "MAX_PASOS = 10" in pf

    def test_source_tokens_por_paso(self):
        """Verifica: constante TOKENS_POR_PASO_ESTIMADO definida"""
        pf = _leer_planificador()
        assert "TOKENS_POR_PASO_ESTIMADO" in pf

    def test_source_cita_claude_code(self):
        """Verifica: router.syn menciona Claude Code como origen"""
        rt = _leer_router()
        assert "Claude Code" in rt

    def test_source_cita_token_efficiency(self):
        """Verifica: router.syn menciona eficiencia de tokens"""
        rt = _leer_router()
        assert "token" in rt.lower()


# ================================================================
# R8+R9: Timeout inferencia (Manual 7 §4.3)
# ================================================================

class TestTimeoutInferencia:
    """Oráculo R8: Verifica timeout de 30s del LSP.
    Requisito: Manual 7 §4.3 — 'Si el servidor no responde en 30 segundos, error'"""

    def test_source_verificar_timeout(self):
        """Verifica: existe funcion verificar_timeout() en router.syn"""
        rt = _leer_router()
        assert "funcion verificar_timeout(" in rt

    def test_source_timeout_30s(self):
        """Verifica: constante TIMEOUT_INFERENCIA = 30000"""
        rt = _leer_router()
        assert "TIMEOUT_INFERENCIA = 30000" in rt

    def test_replica_timeout_30s(self):
        """Verifica: 30001 ms → timeout True"""
        assert verificar_timeout_lsp(30001) is True

    def test_replica_no_timeout_29s(self):
        """Verifica: 29999 ms → timeout False"""
        assert verificar_timeout_lsp(29999) is False


# ================================================================
# R8+R9: Citas cumple Manual (grep-chequeable)
# ================================================================

class TestCitasCumpleManual:
    """Oráculo R8+R9: Verifica citas grep-chequeables al manual.
    Requisito: Manual 7 §4.3 + §7.2"""

    def test_run_manager_cita_r8(self):
        """Verifica: run_manager.syn cita §4.3"""
        rm = _leer_run_manager()
        assert "cumple Manual 7 §4.3" in rm

    def test_planificador_cita_r9(self):
        """Verifica: planificador.syn cita §7.2"""
        pf = _leer_planificador()
        assert "cumple Manual 7 §7.2" in pf

    def test_router_cita_r9(self):
        """Verifica: router.syn referencia R9/§7.2"""
        rt = _leer_router()
        assert "§7.2" in rt or "R9" in rt

    def test_router_cita_r8(self):
        """Verifica: router.syn referencia R8/§4.3"""
        rt = _leer_router()
        assert "§4.3" in rt or "R8" in rt


# ================================================================
# R8+R9: Contratos (Manual 2 §12)
# ================================================================

class TestContratosRunManager:
    """Oráculo R8+R9: Verifica contratos requiere/garantiza.
    Requisito: Manual 2 §12 — 'toda función pública tiene contrato'"""

    def test_crear_run_contrato(self):
        """Verifica: crear_run tiene contrato"""
        rm = _leer_run_manager()
        idx = rm.find("funcion crear_run(")
        assert idx >= 0
        bloque = rm[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_guardar_checkpoint_contrato(self):
        """Verifica: guardar_checkpoint tiene contrato"""
        rm = _leer_run_manager()
        idx = rm.find("funcion guardar_checkpoint(")
        assert idx >= 0
        bloque = rm[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_siguiente_subtarea_contrato(self):
        """Verifica: siguiente_subtarea tiene contrato"""
        rm = _leer_run_manager()
        idx = rm.find("funcion siguiente_subtarea(")
        assert idx >= 0
        bloque = rm[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_planificar_contrato(self):
        """Verifica: planificar tiene contrato"""
        pf = _leer_planificador()
        idx = pf.find("funcion planificar(")
        assert idx >= 0
        bloque = pf[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_evaluar_complejidad_contrato(self):
        """Verifica: evaluar_complejidad tiene contrato"""
        pf = _leer_planificador()
        idx = pf.find("funcion evaluar_complejidad(")
        assert idx >= 0
        bloque = pf[idx:idx+200]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_seleccionar_modelo_contrato(self):
        """Verifica: seleccionar_modelo tiene contrato"""
        pf = _leer_planificador()
        idx = pf.find("funcion seleccionar_modelo(")
        assert idx >= 0
        bloque = pf[idx:idx+200]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque
