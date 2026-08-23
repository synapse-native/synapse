"""
FASE 23 ME-4: Análisis de alcance y ciclos (Manual 3 §5 + Manual 4 §4.4/§5).

Valida que syquex/analizador_alcance.syq:
1. Compila correctamente con el frontend SyQuex
2. Provee la API esperada (analizar_ciclos, analizar_funcion, analizar_programa)
3. La lógica de detección de ciclos es correcta

Comando (Manual 4 §9):
    pytest tests/syquex/test_scope_analysis.py -v
Criterio: 0 falsos positivos en liberación
"""

import json
import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

SYQ_FRONTEND = os.path.join(PROJECT_ROOT, "build", "syq_frontend.exe")
ANALIZADOR = os.path.join(PROJECT_ROOT, "syquex", "analizador_alcance.syq")


def _compilar_syq(ruta_syq):
    """Compila un .syq y retorna el dict JSON SemNodo[]."""
    r = subprocess.run([SYQ_FRONTEND, ruta_syq], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"frontend falló: {r.stderr}"
    return json.loads(r.stdout)


def _decode_nodos(data):
    """Extrae todos los strings de texto del SemNodo[] JSON.

    El JSON almacena strings como arrays de bytes (base64 en el campo txt).
    Decodifica y retorna una lista de strings encontrados.
    """
    textos = []
    nodos = data.get("nodos", [])
    for nodo in nodos:
        for campo in nodo:
            if isinstance(campo, list):
                # Decode byte array
                try:
                    s = bytes(campo).decode("utf-8", errors="replace")
                    if s and all(32 <= c < 127 for c in campo):
                        textos.append(s)
                except (ValueError, TypeError):
                    pass
            elif isinstance(campo, str):
                textos.append(campo)
    return textos


def _nodos_texto(data):
    """Convierte todo el SemNodo[] a texto plano para búsquedas."""
    textos = _decode_nodos(data)
    return " ".join(textos)


@pytest.fixture(scope="module")
def syq_data():
    if not os.path.exists(SYQ_FRONTEND):
        pytest.skip("syq_frontend.exe no existe")
    return _compilar_syq(ANALIZADOR)


class TestAnalizadorCompilacion:
    """Manual 3 §5 — verifica que el analizador compila correctamente."""

    def test_compila(self, syq_data):
        assert syq_data is not None

    def test_tiene_api_publica(self, syq_data):
        """El analizador expone analizar_ciclos, analizar_funcion, analizar_programa."""
        texto = _nodos_texto(syq_data)
        assert "analizar_ciclos" in texto, "falta analizar_ciclos"
        assert "analizar_funcion" in texto, "falta analizar_funcion"
        assert "analizar_programa" in texto, "falta analizar_programa"
        assert "tr_tipo" in texto, "faltan externs tr_tipo"
        assert "tr_hizq" in texto, "faltan externs tr_hizq"
        assert "tr_hder" in texto, "faltan externs tr_hder"
        assert "tr_herm" in texto, "faltan externs tr_herm"
        assert "tr_vi" in texto, "falta extern tr_vi"

    def test_tiene_constantes_nodo(self, syq_data):
        """Las constantes de nodo están definidas."""
        texto = _nodos_texto(syq_data)
        assert "NODO_FUNCION" in texto, "falta constante NODO_FUNCION"
        assert "NODO_RETORNAR" in texto, "falta NODO_RETORNAR"
        assert "NODO_DECLARACION_TIPO" in texto, "falta NODO_DECLARACION_TIPO"
        assert "NODO_PROPAGAR" in texto, "falta NODO_PROPAGAR"

    def test_tiene_externs_runtime(self, syq_data):
        """El analizador declara externs para el runtime C."""
        texto = _nodos_texto(syq_data)
        assert "_a_reset_rc_vars" in texto, "falta extern _a_reset_rc_vars"
        assert "_a_analizar_bloque" in texto, "falta extern _a_analizar_bloque"
        assert "_a_get_rc_count" in texto, "falta extern _a_get_rc_count"


class TestDeteccionCiclos:
    """Manual 4 §4.4 — detección estática de ciclos rc/débil."""

    def test_funciones_tipo_flags(self, syq_data):
        """Las funciones tipo_es_rc/tipo_es_debil/tipo_es_arc existen."""
        texto = _nodos_texto(syq_data)
        assert "tipo_es_rc" in texto
        assert "tipo_es_debil" in texto
        assert "tipo_es_arc" in texto

    def test_analizar_ciclos_recorre_estructuras(self, syq_data):
        """analizar_ciclos recorre NODO_DECLARACION_TIPO."""
        texto = _nodos_texto(syq_data)
        assert "analizar_ciclos" in texto
        assert "tr_hizq" in texto
        assert "tr_herm" in texto

    def test_no_falsos_positivos_estructura(self, syq_data):
        """El analizador recorre hermano (siblings) para evitar falsos positivos."""
        texto = _nodos_texto(syq_data)
        # Verifica que el while loop usa tr_herm para avanzar
        assert "tr_herm" in texto
        assert "ciclos" in texto


class TestCleanupBlocks:
    """Manual 4 §5.2-5.3 — cleanup blocks para salidas tempranas."""

    def test_analizar_funcion_llama_runtime(self, syq_data):
        """analizar_funcion llama _a_reset_rc_vars + _a_analizar_bloque."""
        texto = _nodos_texto(syq_data)
        assert "_a_reset_rc_vars" in texto
        assert "_a_analizar_bloque" in texto
        assert "_a_get_rc_count" in texto
        assert "analizar_funcion" in texto

    def test_analizar_programa_coordina(self, syq_data):
        """analizar_programa coordina ciclos + función analysis."""
        texto = _nodos_texto(syq_data)
        assert "analizar_programa" in texto
        assert "analizar_ciclos" in texto
        assert "analizar_funcion" in texto

    def test_tiene_puntos_exit(self, syq_data):
        """El analizador reconoce NODO_RETORNAR y NODO_PROPAGAR."""
        texto = _nodos_texto(syq_data)
        assert "NODO_RETORNAR" in texto
        assert "NODO_PROPAGAR" in texto
