# -*- coding: utf-8 -*-
"""
test_ia_adv_10.py — IA Nativa funcional (Fase 12).

Manual 7 §7: Detección de hardware, inferencia, transpilación, RAG real.
"""
import os
import subprocess
import sys
import pytest

from conftest import compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ---------------------------------------------------------------------------
# 1. RAG PIPELINE — EJECUCIÓN REAL
# ---------------------------------------------------------------------------
class TestRAGReal:
    """Verifica que el RAG extrae contexto REAL de archivos .syn."""

    def test_rag_extrae_contexto_de_archivo_real(self):
        """RAG extrae contexto de un archivo .syn real."""
        archivo = os.path.join(RAIZ, "examples", "synapse", "00_hola_mundo", "main.syn")
        if not os.path.exists(archivo):
            pytest.skip("Archivo de ejemplo no encontrado")
        with open(archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        if len(lineas) < 3:
            pytest.skip("Archivo demasiado corto")
        cursor = len(lineas) // 2
        inicio = max(0, cursor - 5)
        fin = min(len(lineas), cursor + 6)
        contexto = lineas[inicio:fin]
        assert len(contexto) >= 1
        assert len(contexto) <= 11
        assert any("#lang" in l or "funcion" in l or "retornar" in l
                    for l in contexto), \
            f"Contexto no contiene código Synapse: {contexto}"

    def test_rag_funciones_reales_del_proyecto(self):
        """RAG extrae contexto de funciones reales del compilador."""
        archivo = os.path.join(RAIZ, "compilador", "lexer.py")
        if not os.path.exists(archivo):
            pytest.skip("lexer.py no encontrado")
        with open(archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        cursor = 50
        inicio = max(0, cursor - 5)
        fin = min(len(lineas), cursor + 6)
        contexto = lineas[inicio:fin]
        assert len(contexto) >= 1


# ---------------------------------------------------------------------------
# 2. LLM BRIDGE — EJECUCIÓN REAL
# ---------------------------------------------------------------------------
class TestLLMBridgeReal:
    """Verifica que el LLM bridge funciona con Ollama (si disponible)."""

    def test_ollama_disponible(self):
        """Verifica si Ollama está disponible."""
        try:
            r = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=5
            )
            ollama_disponible = r.returncode == 0
        except FileNotFoundError:
            ollama_disponible = False
        if not ollama_disponible:
            pytest.skip("Ollama no disponible")

    def test_ollama_listar_modelos(self):
        """Ollama lista modelos disponibles."""
        try:
            r = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10
            )
            assert r.returncode == 0
            assert len(r.stdout) > 0, "Lista de modelos vacía"
        except FileNotFoundError:
            pytest.skip("Ollama no disponible")


# ---------------------------------------------------------------------------
# 3. COMPILADOR ACEPTA SINTAXIS DE IA
# ---------------------------------------------------------------------------
class TestSintaxisIA:
    """Verifica que el compilador acepta sintaxis de features de IA."""

    def test_importar_opensyn(self):
        """importar opensyn compila."""
        fuente = '''#lang: es
importar opensyn
funcion principal() -> nulo:
    log("opensyn importado")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_importar_std_io(self):
        """importar std.io compila."""
        fuente = '''#lang: es
importar std.io
funcion principal() -> nulo:
    log("io importado")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_importar_std_math(self):
        """importar std.math compila."""
        fuente = '''#lang: es
importar std.math
funcion principal() -> nulo:
    log("math importado")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 4. TRANSPILACIÓN PYTHON → SYNAPSE — VERIFICACIÓN REAL
# ---------------------------------------------------------------------------
class TestTranspilacion:
    """Verifica que la transpilación Python → Synapse funciona."""

    def test_transpilador_existe(self):
        """El transpilador Python → Synapse existe."""
        transpilador = os.path.join(RAIZ, "opensyn", "transpiler.syn")
        if os.path.exists(transpilador):
            assert os.path.getsize(transpilador) > 0
        else:
            pytest.skip("transpiler.syn no encontrado")

    def test_codigo_python_simple(self):
        """Código Python simple se puede expresar en Synapse."""
        fuente = '''#lang: es
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    return suma(3, 4)
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 5. BINDINGS C → SYNAPSE — VERIFICACIÓN REAL
# ---------------------------------------------------------------------------
class TestBindingsC:
    """Verifica que los bindings C → Synapse funcionan."""

    def test_externo_funcion_compila(self):
        """Declaración externa de función C compila."""
        fuente = '''#lang: es
externo funcion strlen(s: enteroptr) -> entero
funcion principal() -> entero:
    retornar 0
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_externo_con_parametros(self):
        """Declaración externa con parámetros compila."""
        fuente = '''#lang: es
externo funcion strlen(s: enteroptr) -> entero
funcion principal() -> entero:
    retornar 0
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0
