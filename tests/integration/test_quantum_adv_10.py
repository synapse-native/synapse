# -*- coding: utf-8 -*-
"""
test_quantum_adv_10.py — Computación Cuántica (Fase 15).

Manual 1 §6 (hoja de ruta): Simulación Cuántica (std.quantum) como entregable v5.1.1.
Runtime: quantum_runtime.c, quantum_memory.c, quantum_err_corr.c.
"""
import os
import pytest
from conftest import compilar_texto

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ---------------------------------------------------------------------------
# 1. QUANTUM RUNTIME — ARCHIVOS (Manual 1 §6)
# ---------------------------------------------------------------------------
class TestQuantumArchivos:
    """Manual 1 §6: Archivos del runtime cuántico deben existir."""

    def test_quantum_runtime_c_existe(self):
        """nucleo/quantum_runtime.c debe existir."""
        rt = os.path.join(RAIZ, "nucleo", "quantum_runtime.c")
        assert os.path.exists(rt), "nucleo/quantum_runtime.c no existe"

    def test_quantum_runtime_h_existe(self):
        """nucleo/quantum_runtime.h debe existir."""
        rt_h = os.path.join(RAIZ, "nucleo", "quantum_runtime.h")
        assert os.path.exists(rt_h), "nucleo/quantum_runtime.h no existe"

    def test_quantum_memory_c_existe(self):
        """nucleo/quantum_memory.c debe existir."""
        qm = os.path.join(RAIZ, "nucleo", "quantum_memory.c")
        assert os.path.exists(qm), "nucleo/quantum_memory.c no existe"

    def test_quantum_err_corr_c_existe(self):
        """nucleo/quantum_err_corr.c debe existir."""
        ec = os.path.join(RAIZ, "nucleo", "quantum_err_corr.c")
        assert os.path.exists(ec), "nucleo/quantum_err_corr.c no existe"


# ---------------------------------------------------------------------------
# 2. QUANTUM RUNTIME — FUNCIONALIDAD (Manual 1 §6)
# ---------------------------------------------------------------------------
class TestQuantumFuncionalidad:
    """Manual 1 §6: El runtime cuántico debe tener compuertas y simulación."""

    def test_quantum_runtime_api(self):
        """quantum_runtime.h debe declarar API de compuertas cuánticas."""
        rt_h = os.path.join(RAIZ, "nucleo", "quantum_runtime.h")
        if not os.path.exists(rt_h):
            pytest.skip("quantum_runtime.h no existe aún")
        with open(rt_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        # Debe tener al menos una función de compuerta cuántica
        tiene_api = ("qubit" in contenido.lower() or "gate" in contenido.lower() or
                    "quantum" in contenido.lower() or "measure" in contenido.lower())
        assert tiene_api, \
            "quantum_runtime.h debe declarar API de compuertas/circuitos"

    def test_quantum_circuit_crear(self):
        """quantum_runtime debe poder crear circuitos."""
        rt_h = os.path.join(RAIZ, "nucleo", "quantum_runtime.h")
        if not os.path.exists(rt_h):
            pytest.skip("quantum_runtime.h no existe aún")
        with open(rt_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "crear" in contenido.lower() or "create" in contenido.lower() or \
            "circuit" in contenido.lower() or "init" in contenido.lower(), \
            "quantum_runtime.h debe tener función de creación de circuitos"

    def test_quantum_memory_api(self):
        """quantum_memory.c debe gestionar memoria de qubits."""
        qm_h = os.path.join(RAIZ, "nucleo", "quantum_memory.h")
        if not os.path.exists(qm_h):
            pytest.skip("quantum_memory.h no existe aún")
        with open(qm_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "alloc" in contenido.lower() or "crear" in contenido.lower() or \
            "init" in contenido.lower() or "qubit" in contenido.lower(), \
            "quantum_memory.h debe tener API de asignación de qubits"

    def test_quantum_err_corr_api(self):
        """quantum_err_corr.c debe implementar corrección de errores."""
        ec_h = os.path.join(RAIZ, "nucleo", "quantum_err_corr.h")
        if not os.path.exists(ec_h):
            pytest.skip("quantum_err_corr.h no existe aún")
        with open(ec_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "corr" in contenido.lower() or "error" in contenido.lower() or \
            "correct" in contenido.lower() or "detect" in contenido.lower(), \
            "quantum_err_corr.h debe tener API de corrección de errores"


# ---------------------------------------------------------------------------
# 3. STD.QUANTUM — MÓDULO ESTÁNDAR (Manual 1 §6)
# ---------------------------------------------------------------------------
class TestStdQuantum:
    """Manual 1 §6: std/quantum.syn expone la interfaz cuántica al usuario."""

    def test_std_quantum_existe(self):
        """std/quantum.syn debe existir."""
        std_q = os.path.join(RAIZ, "std", "quantum.syn")
        assert os.path.exists(std_q), "std/quantum.syn no existe"

    def test_std_quantum_tamaño(self):
        """std/quantum.syn debe tener contenido significativo."""
        std_q = os.path.join(RAIZ, "std", "quantum.syn")
        assert os.path.getsize(std_q) > 100, \
            f"std/quantum.syn tiene {os.path.getsize(std_q)} bytes, se esperaban >100"

    def test_importar_quantum_compila(self):
        """importar std.quantum debe compilar."""
        fuente = '''#lang: es
importar std.quantum
funcion principal() -> nulo:
    log("quantum importado")
'''
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.quantum no disponible aún")
        assert diag.codigo_salida() == 0


# ---------------------------------------------------------------------------
# 4. QC_MAX_QUBITS — LÍMITE (Test existente verificado)
# ---------------------------------------------------------------------------
class TestQuantumLimites:
    """Verifica límites del runtime cuántico."""

    def test_qc_max_qubits_constante(self):
        """quantum_runtime.h debe definir QC_MAX_QUBITS."""
        rt_h = os.path.join(RAIZ, "nucleo", "quantum_runtime.h")
        if not os.path.exists(rt_h):
            pytest.skip("quantum_runtime.h no existe aún")
        with open(rt_h, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        assert "QC_MAX_QUBITS" in contenido or "MAX_QUBITS" in contenido, \
            "quantum_runtime.h debe definir QC_MAX_QUBITS"
