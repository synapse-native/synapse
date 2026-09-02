# -*- coding: utf-8 -*-
"""
tests/integration/test_syquex_coverage.py — Análisis de cobertura Syquex (FASE 28 ME_28_T6).
Manual 3 §3.

Ejecuta pytest-cov una sola vez y valida cobertura de módulos core.
cumple Manual 3 3
"""
import os
import subprocess
import sys
import json

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

CORE_MODULES = {
    'lexer.py': 50,
    'parser.py': 30,
    'puente_canonico.py': 50,
    'analizador_semantico.py': 80,
    'semantic_checker.py': 50,
    'semantic_scope.py': 80,
    'diagnostics.py': 80,
    'generator.py': 50,
    'context.py': 50,
    'emit_control.py': 30,
    'emit_declarations.py': 30,
    'emit_expressions.py': 30,
}

UMBRAL_TOTAL = 45

_cache = None


def _ejecutar_coverage():
    global _cache
    if _cache is not None:
        return _cache

    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/syquex/',
        'tests/integration/test_syquex_cert_1.py',
        'tests/integration/test_syquex_cert_2.py',
        'tests/integration/test_syquex_cert_3.py',
        'tests/integration/test_syquex_fuzz.py',
        'tests/integration/test_syquex_benchmarks.py',
        '--cov=compilador',
        '--cov-report=json:.coverage_tmp.json',
        '--tb=no', '-q',
    ]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=600,
        encoding='utf-8', errors='replace', cwd=RAIZ,
    )

    json_path = os.path.join(RAIZ, '.coverage_tmp.json')
    coberturas = {}
    total_cover = 0.0
    total_stmts = 0
    total_miss = 0

    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for fname, info in data.get('files', {}).items():
            basename = os.path.basename(fname)
            summary = info.get('summary', {})
            coberturas[basename] = summary.get('percent_covered', 0)
        totals = data.get('totals', {})
        total_cover = totals.get('percent_covered', 0)
        total_stmts = totals.get('num_statements', 0)
        total_miss = totals.get('missing_lines', 0)
        os.remove(json_path)
    else:
        for line in (proc.stdout + proc.stderr).split('\n'):
            line = line.strip()
            if line.startswith('TOTAL'):
                parts = line.split()
                if len(parts) >= 4:
                    total_cover = float(parts[3].replace('%', ''))
                    total_stmts = int(parts[1])
                    total_miss = int(parts[2])

    _cache = {
        'coberturas': coberturas,
        'total_cover': total_cover,
        'total_stmts': total_stmts,
        'total_miss': total_miss,
    }
    return _cache


class TestSyquexCoverage:
    """ME_28_T6: Cobertura de código Syquex."""

    def test_cobertura_total_minima(self):
        """M3 §3: Cobertura total del compilador supera umbral."""
        data = _ejecutar_coverage()
        assert data['total_cover'] >= UMBRAL_TOTAL, (
            f"Cobertura total {data['total_cover']}% < {UMBRAL_TOTAL}% "
            f"({data['total_stmts']} stmts, {data['total_miss']} miss)"
        )

    def test_cobertura_lexer(self):
        """M3 §3: El lexer tiene cobertura mínima."""
        data = _ejecutar_coverage()
        cover = data['coberturas'].get('lexer.py', 0)
        assert cover >= CORE_MODULES['lexer.py'], (
            f"lexer.py: {cover}% < {CORE_MODULES['lexer.py']}%"
        )

    def test_cobertura_puente(self):
        """M3 §3: El puente canónico tiene cobertura mínima."""
        data = _ejecutar_coverage()
        cover = data['coberturas'].get('puente_canonico.py', 0)
        assert cover >= CORE_MODULES['puente_canonico.py'], (
            f"puente_canonico.py: {cover}% < {CORE_MODULES['puente_canonico.py']}%"
        )

    def test_cobertura_generator(self):
        """M3 §3: El generador de código tiene cobertura mínima."""
        data = _ejecutar_coverage()
        cover = data['coberturas'].get('generator.py', 0)
        assert cover >= CORE_MODULES['generator.py'], (
            f"generator.py: {cover}% < {CORE_MODULES['generator.py']}%"
        )

    def test_reporte_cobertura(self):
        """M3 §3: Imprime reporte de cobertura de módulos core."""
        data = _ejecutar_coverage()
        print(f"\n  [COVERAGE] Total: {data['total_cover']}%")
        for mod, umbral in CORE_MODULES.items():
            cover = data['coberturas'].get(mod, 0)
            status = "OK" if cover >= umbral else "BAJO"
            print(f"  [COVERAGE] {mod}: {cover}% (min {umbral}%) [{status}]")
