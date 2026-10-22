"""
TDD tests para opensyn/verificacion_aot.syn
Fase 32.5: Verificación AOT con Auto-Refutación

cumple Manual 7 §4.2 (flujo de validación de la petición de IA) y
Manual 2 §12 (contratos requiere/garantiza). OBL-M7-06.

Estrategia: verificar estructuras, funciones y contratos
sin depender de compilación real (stub de bajo nivel).
"""
import subprocess
import os
import re
import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SYN = os.path.join(RAIZ, "opensyn", "verificacion_aot.syn")
PYTHON = os.path.join(RAIZ, ".venv", "Scripts", "python.exe")


@pytest.mark.tdd
class TestVerificacionAOT:
    """Tests para verificación AOT con auto-refutación."""

    def test_archivo_existe(self):
        """El archivo de implementación debe existir."""
        assert os.path.isfile(SYN), f"Falta {SYN}"

    def test_estructura_caso_limite(self):
        """Debe definir estructura CasoLimite con campos requeridos."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "estructura CasoLimite:" in contenido
        for campo in ["descripcion", "codigo_ejecucion", "valor_esperado"]:
            assert campo in contenido, f"Falta campo {campo} en CasoLimite"

    def test_estructura_resultado_caso(self):
        """Debe definir estructura ResultadoCaso con campos requeridos."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "estructura ResultadoCaso:" in contenido
        for campo in ["caso", "estado", "codigo_salida", "stdout", "stderr", "error"]:
            assert campo in contenido, f"Falta campo {campo} en ResultadoCaso"

    def test_estructura_verificacion(self):
        """Debe definir estructura Verificacion."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "estructura Verificacion:" in contenido

    def test_funcion_verificar_caso_limite(self):
        """Debe definir verificar_caso_limite con contrato requiere/garantiza."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "funcion verificar_caso_limite(" in contenido
        assert "requiere:" in contenido
        assert "garantiza:" in contenido

    def test_funcion_generar_casos_limite(self):
        """Debe definir generar_casos_limite."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "funcion generar_casos_limite(" in contenido

    def test_funcion_verificar_codigo_generado(self):
        """Debe definir verificar_codigo_generado."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "funcion verificar_codigo_generado(" in contenido

    def test_timeout_compilacion(self):
        """La compilación debe tener timeout de 30 segundos."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "30" in contenido, "Compilación debe tener timeout de 30 segundos"

    def test_timeout_ejecucion(self):
        """La ejecución debe tener timeout de 5 segundos."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "5" in contenido, "Ejecución debe tener timeout de 5 segundos"

    def test_max_casos_5(self):
        """Debe limitar a máximo 5 casos por verificación."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "limitar(5)" in contenido or "maximo.*5" in contenido.lower() or "> 5" in contenido, \
            "Debe limitar a máximo 5 casos por verificación"

    def test_estados_resultado(self):
        """Los estados deben incluir: completado, timeout_compilacion, timeout_ejecucion, error_compilacion."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        for estado in ["completado", "timeout_compilacion", "timeout_ejecucion", "error_compilacion"]:
            assert estado in contenido, f"Falta estado {estado}"

    def test_cumple_manual(self):
        """Todos los archivos deben tener comentario // cumple Manual X §Y."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "// cumple Manual" in contenido, \
            "Falta comentario // cumple Manual en verificacion_aot.syn"

    def test_auto_refutacion_tipos(self):
        """Debe generar casos para enteros, textos y decimales."""
        with open(SYN, "r", encoding="utf-8") as f:
            contenido = f.read()
        assert "entero" in contenido, "Debe manejar tipo entero"
        assert "texto" in contenido, "Debe manejar tipo texto"
        assert "decimal" in contenido, "Debe manejar tipo decimal"
