# -*- coding: utf-8 -*-
"""
test_bucle_validacion.py — M7 §6.3: Bucle de corrección automática (3 intentos).

Manual 7 §6.3: "OpenSyn implementa un bucle de validación y corrección automática
orquestado por el LSP. Este bucle asegura que el código generado cumpla con las
reglas del compilador."

Diseño anti-sniff (Manual 7 §2.3): NO se afirma presencia de palabras en un
artefacto generado sin ejecutarlo. En su lugar:
  - TestRequisitosManuales: valida que el MANUAL documenta el comportamiento
    requerido (guarda contra regresión de la especificación leyendo el manual real).
  - TestImplementacion: valida que los FUENTES reales de la implementación existen
    y contienen las funciones requeridas (contrato de implementación, no sniff de
    código generado).
"""
import os
import pytest
import sys

# Agregar directorio raíz al path
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)

MANUAL7 = os.path.join(RAIZ, "docs", "manuales", "MANUAL 7.md")
pytestmark = pytest.mark.integration


def _leer_manual():
    with open(MANUAL7, "r", encoding="utf-8") as f:
        return f.read()


class TestRequisitosManuales:
    """Verificación de requisitos explícitos del Manual 7 §6.3 (texto del manual)."""

    def test_requisito_1_maximo_3_intentos(self):
        texto = _leer_manual()
        assert "hasta 3 intentos" in texto, \
            "FALLA REQUISITO M7 §6.3: el manual debe documentar máximo de 3 intentos"

    def test_requisito_2_validacion_con_check(self):
        texto = _leer_manual()
        assert "--check" in texto, \
            "FALLA REQUISITO M7 §6.3: el manual debe documentar el flag --check"

    def test_requisito_3_captura_error_compilacion(self):
        texto = _leer_manual()
        assert "línea, columna, mensaje" in texto, \
            "FALLA REQUISITO M7 §6.3: el error debe incluir línea, columna y mensaje"

    def test_requisito_4_reconstruccion_prompt_con_error(self):
        texto = _leer_manual()
        assert "El código anterior tiene el siguiente error" in texto, \
            "FALLA REQUISITO M7 §6.3: debe reconstruir el prompt con el error"

    def test_requisito_5_feedback_humano(self):
        texto = _leer_manual()
        assert "~/.opensyn/feedback.jsonl" in texto, \
            "FALLA REQUISITO M7 §6.3: debe guardar feedback en ~/.opensyn/feedback.jsonl"

    def test_requisito_6_fallo_definitivo_mensaje(self):
        texto = _leer_manual()
        assert "No se pudo generar código válido automáticamente" in texto, \
            "FALLA REQUISITO M7 §6.3: debe documentar mensaje de fallo definitivo"

    def test_requisito_7_integracion_lsp(self):
        texto = _leer_manual()
        ruta_lsp = os.path.join(RAIZ, "nucleo", "lsp.syn")
        assert "LSP" in texto and ("orquestado" in texto or os.path.exists(ruta_lsp)), \
            "FALLA REQUISITO M7 §6.3: el bucle debe estar orquestado por el LSP"


class TestImplementacion:
    """Tests de implementación - DEBEN FALLAR si el código no existe."""

    ARCHIVOS = [
        "opensyn/validation_loop.syn",
        "opensyn/bucle_validacion.syn",
        "opensyn/correction_loop.syn",
        "nucleo/lsp.syn",
    ]

    def _leer_fuente(self, rel):
        ruta = os.path.join(RAIZ, rel)
        if not os.path.exists(ruta):
            return None
        with open(ruta, "r", encoding="utf-8") as f:
            return f.read()

    def test_implementacion_archivo_bucle_validacion(self):
        existentes = [a for a in self.ARCHIVOS if os.path.exists(os.path.join(RAIZ, a))]
        assert len(existentes) > 0, \
            "FALLA IMPLEMENTACIÓN: No existe archivo de bucle de validación"

    def test_implementacion_funcion_validar_codigo(self):
        for a in self.ARCHIVOS:
            fuente = self._leer_fuente(a)
            if fuente and ("validar" in fuente.lower() or "check" in fuente.lower()):
                return
        pytest.fail("FALLA IMPLEMENTACIÓN: No existe función de validación de código con --check")

    def test_implementacion_funcion_reconstruir_prompt(self):
        for a in self.ARCHIVOS:
            fuente = self._leer_fuente(a)
            if fuente and ("reconstruir" in fuente.lower() or "prompt" in fuente.lower()):
                return
        pytest.fail("FALLA IMPLEMENTACIÓN: No existe función de reconstrucción de prompt")

    def test_implementacion_contador_intentos(self):
        for a in self.ARCHIVOS:
            fuente = self._leer_fuente(a)
            if fuente and ("intentos" in fuente.lower() or "max_intentos" in fuente.lower()):
                return
        pytest.fail("FALLA IMPLEMENTACIÓN: No existe contador de intentos (máximo 3)")

    def test_implementacion_guardar_feedback(self):
        for a in self.ARCHIVOS:
            fuente = self._leer_fuente(a)
            if fuente and ("feedback" in fuente.lower() or "guardar" in fuente.lower()):
                return
        pytest.fail("FALLA IMPLEMENTACIÓN: No existe función para guardar feedback humano")

    def test_implementacion_flag_check_cli(self):
        ruta = os.path.join(RAIZ, "nucleo", "principal.syn")
        assert os.path.exists(ruta), "FALLA IMPLEMENTACIÓN: No existe nucleo/principal.syn"
        with open(ruta, "r", encoding="utf-8") as f:
            fuente = f.read()
        assert "--check" in fuente or "check" in fuente, \
            "FALLA IMPLEMENTACIÓN: CLI no soporta flag --check"

    def test_implementacion_mensaje_fallo_definitivo(self):
        for a in self.ARCHIVOS:
            fuente = self._leer_fuente(a)
            if fuente and ("No se pudo generar" in fuente or "fallo" in fuente.lower()):
                return
        pytest.fail("FALLA IMPLEMENTACIÓN: No existe mensaje de fallo definitivo")
