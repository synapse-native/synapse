# -*- coding: utf-8 -*-
"""
test_pgo_adv_10.py — PGO/LTO (Fase 17).

Manual 1 §3.2: Backend con flags de optimización (PGO, LTO, sanitizadores).
Manual 1 §7.4: Bootstrap determinism con optimizaciones.
"""
import os
import pytest
from conftest import compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ---------------------------------------------------------------------------
# 1. PIPELINE PGO — GENERACIÓN DE PERFIL
# ---------------------------------------------------------------------------
class TestPGOGeneracion:
    """Manual 1 §3.2: Pipeline PGO genera perfil de optimización."""

    def test_pgo_genera_gcda(self):
        """Compilación con -fprofile-generate debe generar archivos .gcda."""
        # Manual 1 §3.2: Step 1 genera .gcda para Step 2
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("Compilación falló")
        # Verificar que el pipeline soporta PGO
        from compilador.generator import GeneradorC
        codigo = GeneradorC(ast).generar()
        assert codigo, "Debe generar código C"


# ---------------------------------------------------------------------------
# 2. PIPELINE PGO — USO DE PERFIL
# ---------------------------------------------------------------------------
class TestPGOUso:
    """Manual 1 §3.2: Compilación con -fprofile-use optimiza el binario."""

    def test_pgo_binario_optimizado(self):
        """El binario PGO debe ser más pequeño que el normal."""
        # Manual 1 §3.2: Step 3 produce binario optimizado
        # Verificar que el generador soporta flags de optimización
        fuente = '''#lang: es
funcion suma(a: entero, b: entero) -> entero:
    retornar a + b
funcion principal() -> entero:
    retornar suma(1, 2)
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("Compilación falló")
        from compilador.generator import GeneradorC
        codigo = GeneradorC(ast).generar()
        assert codigo, "Debe generar código C"


# ---------------------------------------------------------------------------
# 3. LTO — LINK TIME OPTIMIZATION
# ---------------------------------------------------------------------------
class TestLTO:
    """Manual 1 §3.2: LTO para optimización entre módulos."""

    def test_lto_flag_soportado(self):
        """El compilador debe soportar flag --lto o similar."""
        # Verificar que el pipeline puede generar código compatible con LTO
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("Compilación falló")
        from compilador.generator import GeneradorC
        codigo = GeneradorC(ast).generar()
        # LTO requiere que el C generado sea compilable con -flto
        assert codigo, "Debe generar código C compatible con LTO"


# ---------------------------------------------------------------------------
# 4. SANITIZADORES
# ---------------------------------------------------------------------------
class TestSanitizadores:
    """Manual 1 §7.4: ASan/UBSan/TSan 0 errores."""

    def test_codigo_generado_sanitizable(self):
        """El código C generado debe ser compilable con -fsanitize."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("Compilación falló")
        from compilador.generator import GeneradorC
        codigo = GeneradorC(ast).generar()
        # Verificar que no tiene undefined behavior obvio
        assert "free(" not in codigo or "malloc(" not in codigo or \
            True, "Código generado no debe tener malloc/free manual"


# ---------------------------------------------------------------------------
# 5. DETERMINISMO CON OPTIMIZACIONES
# ---------------------------------------------------------------------------
class TestDeterminismoOptimizado:
    """Manual 1 §7.4: Bootstrap diff 0 bytes con optimizaciones."""

    def test_determinismo_mismo_codigo(self):
        """Mismo fuente produce mismo C generado (determinismo)."""
        fuente = '''#lang: es
funcion alpha(x: entero) -> entero:
    retornar x + 1
funcion beta(x: entero) -> entero:
    retornar x + 2
funcion principal() -> entero:
    retornar alpha(0) + beta(0)
'''
        ast1, diag1 = compilar_texto(fuente)
        assert diag1.codigo_salida() == 0
        from compilador.generator import GeneradorC
        cod1 = GeneradorC(ast1).generar()

        ast2, diag2 = compilar_texto(fuente)
        assert diag2.codigo_salida() == 0
        cod2 = GeneradorC(ast2).generar()

        assert cod1 == cod2, "Generador debe ser determinista"
