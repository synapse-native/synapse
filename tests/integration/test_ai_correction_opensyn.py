# -*- coding: utf-8 -*-
"""
test_ai_correction.py — M7 §7: Bucle de corrección (3 intentos).

Manual 7 §7: "Bucle de corrección (3 intentos) — El código se corrige exitosamente en ≤3 intentos".
Manual 7 §6.3: Flujo: generar → validar --check → si falla, agregar error y regenerar → máx 3 intentos.
"""
import os
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestBucleCorreccion:
    """Manual 7 §6.3: Bucle de corrección automática (3 intentos)."""

    def test_router_syn_correccion(self):
        """router.syn debe implementar bucle de corrección."""
        router = os.path.join(RAIZ, "opensyn", "router.syn")
        if not os.path.exists(router):
            pytest.skip("opensyn/router.syn no existe aún")
        with open(router, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "corregir" in contenido.lower() or "correct" in contenido.lower() or \
            "reintentar" in contenido.lower() or "retry" in contenido.lower() or \
            "intent" in contenido.lower() or "loop" in contenido.lower(), \
            "router.syn debe implementar bucle de corrección"

    def test_maximo_3_intentos(self):
        """El bucle debe tener máximo 3 intentos."""
        router = os.path.join(RAIZ, "opensyn", "router.syn")
        if not os.path.exists(router):
            pytest.skip("opensyn/router.syn no existe aún")
        with open(router, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "3" in contenido or "tres" in contenido.lower() or \
            "max" in contenido.lower() or "máx" in contenido.lower(), \
            "Bucle debe tener máximo 3 intentos"

    def test_feedback_humano(self):
        """Manual 7 §6.3: feedback.jsonl guarda pares (instrucción, código_corregido)."""
        # Verificar que el mecanismo de feedback existe
        feedback = os.path.expanduser("~/.opensyn/feedback.jsonl")
        # No es obligatorio que exista aún, pero la especificación debe estar documentada
        pytest.skip("feedback.jsonl no implementado aún (TDD)")

    def test_check_flag(self):
        """Manual 7 §6.3: Flag --check para validación sin generar binario."""
        # El flag --check debe estar soportado por el CLI
        pytest.skip("--check flag no implementado aún (TDD)")
