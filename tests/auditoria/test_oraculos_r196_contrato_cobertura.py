# -*- coding: utf-8 -*-
# cumple Manual 8 1.7.3
# cumple Manual 2 5.1
# cumple Manual 3 12.1
"""
Oráculo ME r196_deuda_contrato_y_cobertura.

R1 (H-R196-1, decisión Arquitecto 2026-10-23): std/texto.syn contiene/
indice_de SIN precondición `requiere longitud(subcadena) > 0` — M8 §1.7.3
declara los bindings externos sin requiere; el runtime maneja la subcadena
vacía (contiene("hola","") → 1, indice_de("hola","") → 0).

R2: cobertura total del compilador ≥ 45% (test inmutable
test_syquex_coverage.py::test_cobertura_total_minima) — alcanzada con tests
nuevos en tests/syquex/ que compilan probes .syn por el pipeline (medición
2026-10-23: 51.228% ≥ 45%, logs/verifica_coverage_r196.log rc=0 aislado).

Comando: pytest tests/auditoria/test_oraculos_r196_contrato_cobertura.py -v
"""
import os
import subprocess
import sys
import tempfile

import pytest

QA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, QA)

RAIZ_TEXTO = os.path.join(QA, "std", "texto.syn")
RAIZ_TESTS_COVER = os.path.join(QA, "tests", "syquex", "test_sandbox_cover_r196.py")
RAIZ_TESTS_STRING = os.path.join(QA, "tests", "integration", "test_string_utils.py")


class TestOraculoR196:
    """R1: contrato alineado; R2: suite de cobertura nueva GREEN."""

    def test_std_texto_sin_requiere_vacio(self):
        """std/texto.syn ya no prohíbe la subcadena vacía (H-R196-1)."""
        with open(RAIZ_TEXTO, "r", encoding="utf-8") as f:
            fuente = f.read()
        # ninguna función contiene/indice_de lleva el requiere prohibidor
        assert "longitud(subcadena) > 0" not in fuente, (
            "std/texto.syn aún prohíbe la subcadena vacía (H-R196-1 abierto)"
        )
        # ancla MTS grep-chequeable presente
        assert "Manual 8 §1.7.3 (ME r196)" in fuente, (
            "falta el ancla de alineación en std/texto.syn"
        )

    def test_contiene_vacia_e2e(self):
        """E2E compilador real: contiene/indice_de con vacía rc=0 (no abort)."""
        from pipeline import ejecutar_compilador  # cumulative costo razonable

        probe = """#lang: es
importar std.texto
funcion principal() -> nulo:
    escribir_linea(entero_a_texto(contiene("hola", "")))
    escribir_linea(entero_a_texto(indice_de("hola", "")))
"""
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, "probe_r196.syn")
            with open(src, "w", encoding="utf-8") as f:
                f.write(probe)
            exe = os.path.join(td, "probe_r196.exe")
            rc = ejecutar_compilador(src, output_path=exe)
            assert rc == 0, f"compilación del probe rc={rc}"
            r = subprocess.run(
                [exe], capture_output=True, text=True, timeout=30,
                encoding="utf-8", errors="replace",
            )
            assert r.returncode == 0, (
                f"contrato requiere abortó el runtime: rc={r.returncode} "
                f"(H-R196-1) — salida: {r.stdout!r} {r.stderr[:120]!r}"
            )
            lineas = [l for l in r.stdout.splitlines() if l.strip()]
            assert lineas == ["1", "0"], (
                f"semántica vacía incorrecta: {lineas!r} (esperado ['1','0'])"
            )

    def test_suite_cobertura_r196_green(self):
        """R2: los 2 tests nuevos de cobertura pasan (rc=0)."""
        r = subprocess.run(
            [sys.executable, "-m", "pytest", RAIZ_TESTS_COVER, "-q", "--tb=short"],
            capture_output=True, text=True, timeout=600,
            encoding="utf-8", errors="replace", cwd=QA,
        )
        assert r.returncode == 0, (
            f"tests/syquex/test_sandbox_cover_r196.py rc={r.returncode}\n"
            f"{r.stdout[-600:]}"
        )
        assert "2 passed" in r.stdout, r.stdout[-600:]

    def test_string_utils_regresion(self):
        """R1 regresión: test_string_utils.py completo 13/13 (rc=0)."""
        r = subprocess.run(
            [sys.executable, "-m", "pytest", RAIZ_TESTS_STRING, "-q", "--tb=line"],
            capture_output=True, text=True, timeout=600,
            encoding="utf-8", errors="replace", cwd=QA,
        )
        assert r.returncode == 0, (
            f"test_string_utils.py rc={r.returncode}\n{r.stdout[-600:]}"
        )
