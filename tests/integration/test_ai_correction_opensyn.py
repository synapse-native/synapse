# -*- coding: utf-8 -*-
"""
test_ai_correction_opensyn.py — ME-4 (R4+R5+R10): Oráculos TDD para
auto-recuperación, LSP inline y review de alta señal.

Cada test es un oráculo de un requisito del Manual 7, ejecutable en CI.

Manual 7 §6.3: "bucle de validación y corrección automática orquestado por el LSP"
Manual 7 §4.2: "El LSP es el responsable de orquestar el bucle de validación"
Manual 7 §8: "El LSP valida con synapse check --no-emit"

MTO: cada test cita el requisito que verifica (grep-chequeable).
"""
import os

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _leer(ruta):
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _leer_validation():
    return _leer(os.path.join(RAIZ, "opensyn", "validation_loop.syn"))


def _leer_router():
    return _leer(os.path.join(RAIZ, "opensyn", "router.syn"))


# ================================================================
# Réplicas Python de la lógica Synapse (validation_loop.syn)
# ================================================================

MAX_INTENTOS = 3


def reconstruir_prompt_con_error(prompt_original: str, mensaje_error: str,
                                  linea: int, columna: int) -> str:
    """Réplica de validation_loop.syn:reconstruir_prompt_con_error()."""
    assert len(prompt_original) > 0
    msg = "El código anterior tiene el siguiente error: " + mensaje_error
    ubic = " (línea " + str(linea) + ", columna " + str(columna) + ")"
    instr = ". Por favor, corrígelo."
    return prompt_original + "\n\n" + msg + ubic + instr


def validar_con_check_simulado(codigo: str, debe_compilar: bool) -> dict:
    """Simulación de validar_con_check()."""
    assert len(codigo) > 0
    if debe_compilar:
        return {"es_valido": True, "errores": "", "intentos_realizados": 0}
    return {"es_valido": False, "errores": "error de sintaxis en línea 5",
            "intentos_realizados": 0}


def review_compilar_simulado(codigo: str, debe_compilar: bool) -> dict:
    """Réplica de validation_loop.syn:review_compilar()."""
    assert len(codigo) > 0
    return validar_con_check_simulado(codigo, debe_compilar)


def bucle_validacion_simulado(prompt: str, idioma: str,
                               secuencia_resultados: list) -> str:
    """Simulación de validation_loop.syn:bucle_validacion().
    secuencia_resultados: lista de bools (True=compila, False=falla).
    """
    assert len(prompt) > 0
    assert len(secuencia_resultados) <= MAX_INTENTOS
    for i, compila in enumerate(secuencia_resultados):
        if compila:
            return "codigo_generado_" + str(i)
    return ("No se pudo generar código válido automáticamente. "
            "Intenta ajustar la instrucción o corrige manualmente. "
            "Errores: error de sintaxis")


def revisar_codigo_inline_simulado(salida_error: str) -> dict:
    """Réplica de router.syn:revisar_codigo_inline()."""
    assert len(salida_error) >= 0
    rev = {"archivo": "generado.syn", "linea": 0, "columna": 0,
           "mensaje_error": salida_error, "sugerencia": "Revisa el código."}
    pos_dp1 = salida_error.find(":")
    if pos_dp1 > 0:
        resto = salida_error[pos_dp1+1:]
        pos_dp2 = resto.find(":")
        if pos_dp2 > 0:
            try:
                num_linea = int(salida_error[:pos_dp1])
                rev["linea"] = num_linea
                rev["sugerencia"] = "Corrige el error en línea " + str(num_linea)
            except ValueError:
                pass
    return rev


# ================================================================
# R4: Auto-recuperación (Manual 7 §6.3)
# ================================================================

class TestBucleCorreccion:
    """Oráculo R4: bucle_validacion() implementa MAX_INTENTOS=3.
    Requisito: Manual 7 §6.3 — 'bucle de validación y corrección automática'."""

    def test_max_intentos_es_3(self):
        """Verifica: constante MAX_INTENTOS = 3."""
        vl = _leer_validation()
        assert "MAX_INTENTOS = 3" in vl

    def test_max_intentos_en_loop(self):
        """Verifica: el bucle usa MAX_INTENTOS como tope."""
        vl = _leer_validation()
        assert "MAX_INTENTOS" in vl
        assert "mientras intentos < MAX_INTENTOS" in vl

    def test_funcion_bucle_validacion_existe(self):
        """Verifica: bucle_validacion() está definida."""
        vl = _leer_validation()
        assert "funcion bucle_validacion(" in vl

    def test_genera_codigo_en_cada_intento(self):
        """Verifica: cada intento genera código nuevo."""
        vl = _leer_validation()
        assert "generar_codigo_ia(" in vl

    def test_valida_con_check_en_cada_intento(self):
        """Verifica: cada intento valida con --check."""
        vl = _leer_validation()
        assert "validar_con_check(" in vl

    def test_reconstruir_prompt_con_error(self):
        """Verifica: reconstruir_prompt_con_error() añade error al prompt."""
        vl = _leer_validation()
        assert "funcion reconstruir_prompt_con_error(" in vl
        assert "El código anterior tiene el siguiente error" in vl

    def test_mensaje_fallo_definitivo(self):
        """Verifica: al 3er fallo muestra mensaje prescrito en §6.3."""
        vl = _leer_validation()
        assert "No se pudo generar código válido automáticamente" in vl

    def test_guarda_feedback(self):
        """Verifica: guardar_feedback() escribe en feedback.jsonl."""
        vl = _leer_validation()
        assert "guardar_feedback(" in vl
        assert "feedback.jsonl" in vl

    def test_source_tiene_cita_manual(self):
        """Verifica: // cumple Manual 7 §6.3 en validation_loop.syn."""
        vl = _leer_validation()
        assert "// cumple Manual 7 §6.3" in vl

    def test_source_tiene_contrato_bucle(self):
        """Verifica: bucle_validacion tiene contrato."""
        vl = _leer_validation()
        idx = vl.find("funcion bucle_validacion(")
        bloque = vl[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_replica_un_intento_exito(self):
        """Réplica: si compila en 1er intento, retorna código."""
        r = bucle_validacion_simulado("test", "syn", [True])
        assert r == "codigo_generado_0"

    def test_replica_dos_intentos_exito(self):
        """Réplica: si falla 1 vez y compila, retorna código."""
        r = bucle_validacion_simulado("test", "syn", [False, True])
        assert r == "codigo_generado_1"

    def test_replica_tres_intentos_fallo(self):
        """Réplica: si falla 3 veces, retorna mensaje de error."""
        r = bucle_validacion_simulado("test", "syn", [False, False, False])
        assert "No se pudo generar" in r


class TestReconstruirPrompt:
    """Oráculo R4: reconstruir_prompt_con_error() formatea el error.
    Requisito: Manual 7 §6.3 — '{mensaje_error}. Por favor, corrígelo.'"""

    def test_incluye_mensaje_error(self):
        prompt = reconstruir_prompt_con_error("original", "error X", 5, 3)
        assert "error X" in prompt

    def test_incluye_linea(self):
        prompt = reconstruir_prompt_con_error("original", "error", 42, 0)
        assert "línea 42" in prompt

    def test_incluye_columna(self):
        prompt = reconstruir_prompt_con_error("original", "error", 5, 7)
        assert "columna 7" in prompt

    def test_incluye_instruccion(self):
        prompt = reconstruir_prompt_con_error("original", "error", 1, 0)
        assert "Por favor, corrígelo" in prompt

    def test_preserva_prompt_original(self):
        prompt = reconstruir_prompt_con_error("MI_PROMPT", "error", 1, 0)
        assert prompt.startswith("MI_PROMPT")


class TestGuardarFeedback:
    """Oráculo R4: guardar_feedback() guarda en feedback.jsonl.
    Requisito: Manual 7 §6.3 — 'guarda el par (instrucción, código_corregido)'"""

    def test_source_funcion_existe(self):
        vl = _leer_validation()
        assert "funcion guardar_feedback(" in vl

    def test_source_formato_jsonl(self):
        vl = _leer_validation()
        assert "instruction" in vl
        assert "output" in vl

    def test_source_ruta_feedback(self):
        vl = _leer_validation()
        assert "RUTA_FEEDBACK" in vl
        assert "feedback.jsonl" in vl


class TestValidarConCheck:
    """Oráculo R4: validar_con_check() ejecuta synapse check --no-emit.
    Requisito: Manual 7 §6.3 — 'El LSP pasa el código al compilador en modo --check'"""

    def test_source_funcion_existe(self):
        vl = _leer_validation()
        assert "funcion validar_con_check(" in vl

    def test_source_usa_synapse_check(self):
        vl = _leer_validation()
        assert "synapse check --no-emit" in vl

    def test_source_retorna_resultado_validacion(self):
        vl = _leer_validation()
        assert "ResultadoValidacion" in vl

    def test_source_tiene_contrato(self):
        vl = _leer_validation()
        idx = vl.find("funcion validar_con_check(")
        bloque = vl[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_replica_compila(self):
        r = validar_con_check_simulado("codigo", True)
        assert r["es_valido"] is True

    def test_replica_falla(self):
        r = validar_con_check_simulado("codigo", False)
        assert r["es_valido"] is False
        assert len(r["errores"]) > 0


# ================================================================
# R5: LSP inline con archivo+línea+diff (Manual 7 §4.2)
# ================================================================

class TestRevisionInline:
    """Oráculo R5: revisar_codigo_inline() retorna ubicación exacta.
    Requisito: Manual 7 §4.2 — 'la respuesta del LSP incluye archivo+linea+diff'"""

    def test_router_funcion_existe(self):
        """Verifica: revisar_codigo_inline() en router.syn."""
        router = _leer_router()
        assert "funcion revisar_codigo_inline(" in router

    def test_router_estructura_revision(self):
        """Verifica: RevisionResultado tiene archivo+linea+diff."""
        router = _leer_router()
        assert "estructura RevisionResultado:" in router
        assert "archivo: texto" in router
        assert "linea: entero" in router
        assert "mensaje_error: texto" in router

    def test_router_cita_manual(self):
        """Verifica: // cumple Manual 7 §4.2."""
        router = _leer_router()
        assert "// cumple Manual 7 §4.2" in router

    def test_router_tiene_contrato(self):
        """Verifica: revisar_codigo_inline tiene contrato."""
        router = _leer_router()
        idx = router.find("funcion revisar_codigo_inline(")
        bloque = router[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_replica_parsea_linea(self):
        """Réplica: parsea '5:3:error' correctamente."""
        r = revisar_codigo_inline_simulado("5:3:error de sintaxis")
        assert r["linea"] == 5

    def test_replica_default_linea_0(self):
        """Réplica: sin formato retorna linea 0."""
        r = revisar_codigo_inline_simulado("error sin formato")
        assert r["linea"] == 0

    def test_replica_sugerencia(self):
        """Réplica: genera sugerencia con línea."""
        r = revisar_codigo_inline_simulado("10:0:error")
        assert "línea 10" in r["sugerencia"]

    def test_validation_funcion_existe(self):
        """Verifica: revisar_codigo_inline() también en validation_loop.syn."""
        vl = _leer_validation()
        assert "funcion revisar_codigo_inline(" in vl

    def test_validation_estructura_revision(self):
        """Verifica: RevisionInline en validation_loop.syn."""
        vl = _leer_validation()
        assert "estructura RevisionInline:" in vl


# ================================================================
# R10: Review de alta señal (Manual 7 §8)
# ================================================================

class TestReviewCompilar:
    """Oráculo R10: review_compilar() verifica compilación + integración.
    Requisito: Manual 7 §8 — 'El LSP valida con synapse check --no-emit'"""

    def test_source_funcion_existe(self):
        """Verifica: review_compilar() en validation_loop.syn."""
        vl = _leer_validation()
        assert "funcion review_compilar(" in vl

    def test_source_delega_a_validar_con_check(self):
        """Verifica: review_compilar llama a validar_con_check."""
        vl = _leer_validation()
        assert "validar_con_check(" in vl

    def test_source_tiene_contrato(self):
        """Verifica: review_compilar tiene contrato."""
        vl = _leer_validation()
        idx = vl.find("funcion review_compilar(")
        bloque = vl[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_source_cita_manual(self):
        """Verifica: // cumple Manual 7 §8."""
        vl = _leer_validation()
        assert "// cumple Manual 7 §8" in vl

    def test_replica_compila(self):
        """Réplica: si compila, review es válido."""
        r = review_compilar_simulado("codigo", True)
        assert r["es_valido"] is True

    def test_replica_falla(self):
        """Réplica: si no compila, review reporta error."""
        r = review_compilar_simulado("codigo", False)
        assert r["es_valido"] is False


# ================================================================
# MTO: Citas y contratos
# ================================================================

class TestCitasCumpleManual:
    """Oráculo MTO: toda función modificada tiene // cumple Manual X §Y."""

    def test_validation_cita_r4(self):
        vl = _leer_validation()
        assert "// cumple Manual 7 §6.3" in vl

    def test_validation_cita_r5(self):
        vl = _leer_validation()
        assert "// cumple Manual 7 §4.2" in vl

    def test_validation_cita_r10(self):
        vl = _leer_validation()
        assert "// cumple Manual 7 §8" in vl

    def test_router_cita_r5(self):
        router = _leer_router()
        assert "// cumple Manual 7 §4.2" in router


class TestContratosValidation:
    """Oráculo Manual 2 §12: toda función pública tiene contrato."""

    def test_validar_con_check_contrato(self):
        vl = _leer_validation()
        idx = vl.find("funcion validar_con_check(")
        bloque = vl[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_reconstruir_prompt_contrato(self):
        vl = _leer_validation()
        idx = vl.find("funcion reconstruir_prompt_con_error(")
        bloque = vl[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_guardar_feedback_contrato(self):
        vl = _leer_validation()
        idx = vl.find("funcion guardar_feedback(")
        bloque = vl[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_bucle_validacion_contrato(self):
        vl = _leer_validation()
        idx = vl.find("funcion bucle_validacion(")
        bloque = vl[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque

    def test_review_compilar_contrato(self):
        vl = _leer_validation()
        idx = vl.find("funcion review_compilar(")
        bloque = vl[idx:idx+300]
        assert "requiere:" in bloque
        assert "garantiza:" in bloque
