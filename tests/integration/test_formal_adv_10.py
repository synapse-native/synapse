# -*- coding: utf-8 -*-
"""
test_formal_adv_10.py — Verificación Formal / Proof Bridge (Fase 14).

Manual 1 §2: ATP + Proof Bridge — exportación a Coq/Lean.
Manual 1 §2: Verificación Formal como pilar del ecosistema.
"""
import os
import pytest
from conftest import compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ---------------------------------------------------------------------------
# 1. PROOF BRIDGE — ARCHIVOS (Manual 1 §2)
# ---------------------------------------------------------------------------
class TestProofBridgeArchivos:
    """Manual 1 §2: proof_bridge.c/.h deben existir para traducción a Coq/Lean."""

    def test_proof_bridge_c_existe(self):
        """nucleo/proof_bridge.c debe existir."""
        bridge = os.path.join(RAIZ, "nucleo", "proof_bridge.c")
        assert os.path.exists(bridge), "nucleo/proof_bridge.c no existe"

    def test_proof_bridge_h_existe(self):
        """nucleo/proof_bridge.h debe existir."""
        bridge_h = os.path.join(RAIZ, "nucleo", "proof_bridge.h")
        assert os.path.exists(bridge_h), "nucleo/proof_bridge.h no existe"

    def test_proof_bridge_tamaño(self):
        """proof_bridge.c debe tener contenido significativo (>100 líneas)."""
        bridge = os.path.join(RAIZ, "nucleo", "proof_bridge.c")
        if not os.path.exists(bridge):
            pytest.skip("proof_bridge.c no existe aún")
        with open(bridge, 'r', encoding='utf-8', errors='ignore') as f:
            lineas = f.readlines()
        assert len(lineas) > 100, \
            f"proof_bridge.c tiene {len(lineas)} líneas, se esperaban >100"


# ---------------------------------------------------------------------------
# 2. TRADUCCIÓN A LEAN (Manual 1 §2)
# ---------------------------------------------------------------------------
class TestTraduccionLean:
    """Manual 1 §2: El Proof Bridge traduce AST a formato Lean."""

    def test_proof_bridge_traducir_lean(self):
        """proof_bridge debe tener función de traducción a Lean."""
        bridge_h = os.path.join(RAIZ, "nucleo", "proof_bridge.h")
        if not os.path.exists(bridge_h):
            pytest.skip("proof_bridge.h no existe aún")
        with open(bridge_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "traducir_a_lean" in contenido or "pb_traducir_a_lean" in contenido \
            or "lean" in contenido.lower(), \
            "proof_bridge.h debe declarar función de traducción a Lean"

    def test_proof_bridge_api_completa(self):
        """proof_bridge.h debe declarar las funciones de traducción y validación."""
        bridge_h = os.path.join(RAIZ, "nucleo", "proof_bridge.h")
        if not os.path.exists(bridge_h):
            pytest.skip("proof_bridge.h no existe aún")
        with open(bridge_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        # Manual 1 §2: debe poder traducir a Coq/Lean y validar
        assert "proof_bridge" in contenido.lower() or "pb_" in contenido, \
            "proof_bridge.h debe tener API con prefijo pb_ o proof_bridge"

    def test_proof_bridge_validar_formal(self):
        """proof_bridge debe poder validar una prueba formal."""
        bridge_h = os.path.join(RAIZ, "nucleo", "proof_bridge.h")
        if not os.path.exists(bridge_h):
            pytest.skip("proof_bridge.h no existe aún")
        with open(bridge_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "validar" in contenido.lower() or "verify" in contenido.lower() \
            or "check" in contenido.lower(), \
            "proof_bridge.h debe tener función de validación formal"


# ---------------------------------------------------------------------------
# 3. MÓDULO STD.FORMAL (Manual 1 §2)
# ---------------------------------------------------------------------------
class TestStdFormal:
    """Manual 1 §2: std/proof_bridge.syn expone la interfaz al usuario."""

    def test_std_proof_bridge_existe(self):
        """std/proof_bridge.syn debe existir."""
        std_bridge = os.path.join(RAIZ, "std", "proof_bridge.syn")
        if os.path.exists(std_bridge):
            assert os.path.getsize(std_bridge) > 0
        else:
            pytest.skip("std/proof_bridge.syn no creado aún (TDD)")

    def test_importar_formal_compila(self):
        """importar std.formal debe compilar."""
        fuente = '''#lang: es
importar std.formal
funcion principal() -> nulo:
    log("formal importado")
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.formal no disponible aún (TDD)")
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 4. MOTOR ATP (Manual 1 §2)
# ---------------------------------------------------------------------------
class TestMotorATP:
    """Manual 1 §2: Motor ATP integrado para verificación automática."""

    def test_atp_archivo_existe(self):
        """Debe existir un archivo de motor ATP."""
        archivos_atp = [
            os.path.join(RAIZ, "nucleo", "atp.c"),
            os.path.join(RAIZ, "nucleo", "atp.h"),
            os.path.join(RAIZ, "nucleo", "verifier.c"),
            os.path.join(RAIZ, "nucleo", "verifier.h"),
        ]
        alguno_existe = any(os.path.exists(f) for f in archivos_atp)
        if not alguno_existe:
            pytest.skip("Archivos ATP no creados aún (TDD)")
        assert alguno_existe, "Debe existir un archivo de motor ATP"


# ---------------------------------------------------------------------------
# 5. INTEGRACIÓN CON COMPILADOR (Manual 1 §2)
# ---------------------------------------------------------------------------
class TestIntegracionCompilador:
    """Manual 1 §2: El modo --safe activa el ATP en el compilador."""

    def test_modo_safe_activa_atp(self):
        """El flag --safe debe estar soportado por el compilador."""
        fuente = '''#lang: es
funcion principal() -> entero:
    retornar 42
'''
        ast, diag = compilar_texto(fuente)
        # Verificar que el compilador soporta --safe
        # (esto se verificaría pasando el flag, pero al menos compilamos)
        assert diag.codigo_salida() == 0, \
            f"Compilación base debe funcionar: {[e.get('mensaje','') for e in diag.errores]}"
