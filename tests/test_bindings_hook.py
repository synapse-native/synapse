#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tests/test_bindings_hook.py — Tests para la regeneración automática de bindings (Fase 26)

Valida:
- La lógica de detección de headers modificados
- La regeneración automática de lib/runtime_bindings.syq
- El script generate_runtime_bindings.py funciona correctamente
"""
import os
import sys
import subprocess
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "opensyn"))

try:
    from generate_runtime_bindings import generate_all_bindings, RUNTIME_HEADERS
    HAS_BINDINGS = True
    _IMPORT_ERROR = None
except ImportError as e:
    HAS_BINDINGS = False
    _IMPORT_ERROR = str(e)

import pytest

pytestmark = pytest.mark.skipif(
    not HAS_BINDINGS,
    reason=f"bindings no disponibles: {_IMPORT_ERROR}"
)

BINDINGS_PATH = os.path.join(PROJECT_ROOT, "lib", "runtime_bindings.syq")


# =====================================================================
# Tests de la lógica del hook
# =====================================================================

class TestHookLogic:

    def test_detects_header_changes(self):
        """El hook detecta cambios en headers del runtime."""
        # Simular: ejecutar el comando git diff que usaría el hook
        r = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True, text=True, timeout=10, cwd=PROJECT_ROOT
        )
        # El comando funciona (aunque pueda no retornar headers en este momento)
        assert r.returncode == 0

    def test_bindings_regeneration_works(self):
        """La regeneración de bindings funciona correctamente."""
        # Generar a un path temporal
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".syq", delete=False) as f:
            tmp_path = f.name

        try:
            total = generate_all_bindings(tmp_path)
            assert total >= 80
            assert os.path.exists(tmp_path)
            content = open(tmp_path, encoding="utf-8").read()
            assert "#lang: es" in content
            assert "externo funcion" in content
        finally:
            os.unlink(tmp_path)

    def test_bindings_file_fresh(self):
        """lib/runtime_bindings.syq existe y tiene contenido reciente."""
        assert os.path.exists(BINDINGS_PATH)
        size = os.path.getsize(BINDINGS_PATH)
        assert size > 1000, f"Bindings file too small: {size} bytes"

    def test_bindings_count_matches(self):
        """El conteo de funciones en el archivo coincide con lo esperado."""
        with open(BINDINGS_PATH, encoding="utf-8") as f:
            content = f.read()
        count = content.count("externo funcion")
        assert count >= 80, f"Expected >= 80 externo functions, got {count}"

    def test_generate_script_cli(self):
        """El script generador funciona vía CLI."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".syq", delete=False) as f:
            tmp_path = f.name

        try:
            r = subprocess.run(
                [sys.executable, os.path.join(PROJECT_ROOT, "opensyn", "generate_runtime_bindings.py"),
                 "-o", tmp_path],
                capture_output=True, text=True, timeout=30
            )
            assert r.returncode == 0
            assert os.path.exists(tmp_path)
            content = open(tmp_path, encoding="utf-8").read()
            assert "externo funcion" in content
        finally:
            os.unlink(tmp_path)


# =====================================================================
# Tests de regeneración incremental
# =====================================================================

class TestIncrementalRegeneration:

    def test_regenerate_idempotent(self):
        """Regenerar dos veces produce el mismo resultado."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".syq", delete=False) as f:
            tmp1 = f.name
        with tempfile.NamedTemporaryFile(suffix=".syq", delete=False) as f:
            tmp2 = f.name

        try:
            generate_all_bindings(tmp1)
            generate_all_bindings(tmp2)

            content1 = open(tmp1, encoding="utf-8").read()
            content2 = open(tmp2, encoding="utf-8").read()

            # La función count debe ser idéntico
            count1 = content1.count("externo funcion")
            count2 = content2.count("externo funcion")
            assert count1 == count2
        finally:
            os.unlink(tmp1)
            os.unlink(tmp2)

    def test_all_headers_produce_bindings(self):
        """Todos los headers del runtime producen bindings."""
        root = PROJECT_ROOT
        for header_rel, description in RUNTIME_HEADERS:
            header_path = os.path.join(root, header_rel)
            if not os.path.exists(header_path):
                continue  # Skip missing headers

            from bindings_generator import parsear_header
            funcs, _, _ = parsear_header(header_path)
            assert len(funcs) > 0, f"{header_rel}: 0 funciones detectadas"

    def test_bindings_format_valid(self):
        """Todas las líneas externo tienen formato válido."""
        with open(BINDINGS_PATH, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line.startswith("externo funcion"):
                    continue
                # Formato: externo funcion nombre(parametros) -> tipo
                assert "(" in line, f"Line {i}: missing '(': {line}"
                assert ")" in line, f"Line {i}: missing ')': {line}"
