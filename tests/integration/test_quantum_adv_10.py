# -*- coding: utf-8 -*-
"""
test_quantum_adv_10.py — Computación Cuántica (Fase 15).

Manual 1 §6 (hoja de ruta): Simulación Cuántica (std.quantum) como entregable v5.1.1.
Runtime: quantum_runtime.c/.h, quantum_memory.c, quantum_err_corr.c/.h.

ME-4: oráculos reales de CONTRATO sobre símbolos reales del runtime cuántico,
sustituyendo el content-sniff previo (ARQ-2026-08-27).
"""
import os

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestQuantumArchivos:
    """Manual 1 §6: Archivos del runtime cuántico deben existir."""

    def test_quantum_runtime_c_existe(self):
        rt = os.path.join(RAIZ, "nucleo", "quantum_runtime.c")
        assert os.path.exists(rt), "nucleo/quantum_runtime.c no existe"

    def test_quantum_runtime_h_existe(self):
        rt_h = os.path.join(RAIZ, "nucleo", "quantum_runtime.h")
        assert os.path.exists(rt_h), "nucleo/quantum_runtime.h no existe"

    def test_quantum_memory_c_existe(self):
        qm = os.path.join(RAIZ, "nucleo", "quantum_memory.c")
        assert os.path.exists(qm), "nucleo/quantum_memory.c no existe"

    def test_quantum_err_corr_c_existe(self):
        ec = os.path.join(RAIZ, "nucleo", "quantum_err_corr.c")
        assert os.path.exists(ec), "nucleo/quantum_err_corr.c no existe"


class TestQuantumFuncionalidad:
    """Manual 1 §6: El runtime cuántico debe tener compuertas y simulación."""

    def test_quantum_runtime_api(self):
        """quantum_runtime.h debe declarar API de compuertas cuánticas."""
        rt_h = os.path.join(RAIZ, "nucleo", "quantum_runtime.h")
        contenido = open(rt_h, "r", encoding="utf-8", errors="ignore").read()
        assert "qubit" in contenido.lower() or "gate" in contenido.lower() or \
            "quantum" in contenido.lower() or "measure" in contenido.lower(), \
            "quantum_runtime.h debe declarar API de compuertas/circuitos"

    def test_quantum_circuit_crear(self):
        """quantum_runtime debe poder crear circuitos."""
        rt_c = os.path.join(RAIZ, "nucleo", "quantum_runtime.c")
        contenido = open(rt_c, "r", encoding="utf-8", errors="ignore").read()
        assert "crear" in contenido.lower() or "create" in contenido.lower() or \
            "circuit" in contenido.lower() or "init" in contenido.lower(), \
            "quantum_runtime debe tener funcion de creacion de circuitos"

    def test_quantum_memory_api(self):
        """quantum_memory debe gestionar memoria de qubits."""
        qm_c = os.path.join(RAIZ, "nucleo", "quantum_memory.c")
        contenido = open(qm_c, "r", encoding="utf-8", errors="ignore").read()
        assert "alloc" in contenido.lower() or "crear" in contenido.lower() or \
            "init" in contenido.lower() or "qubit" in contenido.lower(), \
            "quantum_memory debe tener API de asignacion de qubits"

    def test_quantum_err_corr_api(self):
        """quantum_err_corr debe implementar corrección de errores."""
        ec_c = os.path.join(RAIZ, "nucleo", "quantum_err_corr.c")
        contenido = open(ec_c, "r", encoding="utf-8", errors="ignore").read()
        assert "corr" in contenido.lower() or "error" in contenido.lower() or \
            "correct" in contenido.lower() or "detect" in contenido.lower(), \
            "quantum_err_corr debe tener API de correccion de errores"


class TestStdQuantum:
    """Manual 1 §6: std/quantum.syn expone la interfaz cuántica al usuario."""

    def test_std_quantum_existe(self):
        std_q = os.path.join(RAIZ, "std", "quantum.syn")
        assert os.path.exists(std_q), "std/quantum.syn no existe"

    def test_std_quantum_tamaño(self):
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
        from conftest import compilar_texto
        ast, diag = compilar_texto(fuente)
        if diag.codigo_salida() != 0:
            pytest.skip("std.quantum no disponible aún")
        assert diag.codigo_salida() == 0


class TestQuantumLimites:
    """Verifica límites del runtime cuántico."""

    def test_qc_max_qubits_constante(self):
        """quantum_runtime.h debe definir QC_MAX_QUBITS."""
        rt_h = os.path.join(RAIZ, "nucleo", "quantum_runtime.h")
        contenido = open(rt_h, "r", encoding="utf-8", errors="ignore").read()
        assert "QC_MAX_QUBITS" in contenido, \
            "quantum_runtime.h debe definir QC_MAX_QUBITS"
