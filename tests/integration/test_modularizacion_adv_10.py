# -*- coding: utf-8 -*-
"""
test_modularizacion_adv_10.py — ESPECIFICACIÓN EJECUTABLE: Modularización Runtime (Fase 16).

Manual 1 §4: Descomposición de synapse_rt.c en módulos.

Estos tests definen QUÉ DEBE hacer el código cuando se implemente.
"""
import os
import subprocess
import sys
import pytest

from conftest import rt_objs, compilar_texto

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RT_OBJS = rt_objs()
TESTS_DIR = os.path.join(RAIZ, "tests")


def _find_gcc() -> str:
    candidates = [
        os.path.join(RAIZ, "toolchain_gcc12", "mingw64", "bin", "gcc.exe"),
        "gcc", "gcc.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
        try:
            subprocess.run([c, "--version"], capture_output=True)
            return c
        except FileNotFoundError:
            continue
    return candidates[0]


# ---------------------------------------------------------------------------
# 1. MÓDULOS COMPILAN INDEPENDIENTEMENTE — ESPECIFICACIÓN
# ---------------------------------------------------------------------------
class TestModulosIndependientes:
    """Especifica que cada módulo del runtime debe compilar independientemente."""

    def test_memory_c_compila(self):
        """runtime/core/memory.c compila sin errores."""
        ruta = os.path.join(RAIZ, "runtime", "core", "memory.c")
        if not os.path.exists(ruta):
            pytest.skip("memory.c no encontrado")
        gcc = _find_gcc()
        r = subprocess.run(
            [gcc, "-c", ruta, "-o", os.devnull, "-std=c99", "-Wall", "-I", RAIZ],
            capture_output=True, text=True, timeout=30
        )
        assert r.returncode == 0, f"memory.c no compila: {r.stderr[:300]}"

    def test_concurrency_c_compila(self):
        """runtime/core/concurrency.c compila sin errores."""
        ruta = os.path.join(RAIZ, "runtime", "core", "concurrency.c")
        if not os.path.exists(ruta):
            pytest.skip("concurrency.c no encontrado")
        gcc = _find_gcc()
        r = subprocess.run(
            [gcc, "-c", ruta, "-o", os.devnull, "-std=c99", "-Wall", "-I", RAIZ],
            capture_output=True, text=True, timeout=30
        )
        assert r.returncode == 0, f"concurrency.c no compila: {r.stderr[:300]}"

    def test_io_c_compila(self):
        """runtime/core/io.c compila sin errores."""
        ruta = os.path.join(RAIZ, "runtime", "core", "io.c")
        if not os.path.exists(ruta):
            pytest.skip("io.c no encontrado")
        gcc = _find_gcc()
        r = subprocess.run(
            [gcc, "-c", ruta, "-o", os.devnull, "-std=c99", "-Wall", "-I", RAIZ],
            capture_output=True, text=True, timeout=30
        )
        assert r.returncode == 0, f"io.c no compila: {r.stderr[:300]}"


# ---------------------------------------------------------------------------
# 2. HEADERS SEPARADOS DE IMPLEMENTACIÓN — ESPECIFICACIÓN
# ---------------------------------------------------------------------------
class TestHeadersSeparados:
    """Especifica que headers no deben contener implementación."""

    def test_synapse_rt_types_h_es_header(self):
        """synapse_rt_types.h solo tiene declarations, no implementación."""
        ruta = os.path.join(RAIZ, "synapse_rt_types.h")
        if not os.path.exists(ruta):
            pytest.skip("synapse_rt_types.h no encontrado")
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        # Headers no deben tener funciones con cuerpo grande
        import re
        funcs_con_cuerpo = re.findall(r'\w+\s+\w+\s*\([^)]*\)\s*\{[^}]{50,}', contenido)
        assert len(funcs_con_cuerpo) <= 2, \
            f"Header tiene {len(funcs_con_cuerpo)} funciones con cuerpo grande"


# ---------------------------------------------------------------------------
# 3. MÓDULOS SE LINKEAN CORRECTAMENTE — ESPECIFICACIÓN
# ---------------------------------------------------------------------------
class TestLinkadoModulos:
    """Especifica que los módulos se pueden linkar en un solo binario."""

    def test_objetos_se_linkean(self):
        """Todos los .o del runtime se linkean sin errores de símbolos."""
        if not RT_OBJS:
            pytest.skip("No hay objetos runtime compilados")
        objs_existentes = [o for o in RT_OBJS if o and os.path.exists(o)]
        if len(objs_existentes) < 2:
            pytest.skip("Menos de 2 objetos runtime")
        # Crear un main.c mínimo
        main_c = os.path.join(TESTS_DIR, "_test_link_main.c")
        with open(main_c, 'w') as f:
            f.write("int main() { return 0; }\n")
        try:
            gcc = _find_gcc()
            cmd = [gcc, main_c, *objs_existentes, "-o", os.devnull,
                   "-lm", "-lpthread", "-lws2_32"]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            # Manual 1 §4: Linkado debe exitosamente (sin errores de símbolos)
            assert r.returncode == 0, \
                f"Linkado falló: {r.stderr[:500]}"
        finally:
            if os.path.exists(main_c):
                os.remove(main_c)


# ---------------------------------------------------------------------------
# 4. CÓDIGO SYNAPSE USA MÓDULOS — ESPECIFICACIÓN
# ---------------------------------------------------------------------------
class TestCodigoUsaModulos:
    """Especifica que el código Synapse puede importar módulos del runtime."""

    def test_importar_std_compila(self):
        """importar std funciona."""
        fuente = '''#lang: es
importar std.io
funcion principal() -> nulo:
    log("io importado")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_importar_cluster_compila(self):
        """importar std.cluster funciona."""
        fuente = '''#lang: es
importar std.cluster
funcion principal() -> nulo:
    log("cluster importado")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0

    def test_importar_multiples_modulos(self):
        """Múltiples imports compilan."""
        fuente = '''#lang: es
importar std.io
importar std.math
funcion principal() -> nulo:
    log("modulos importados")
'''
        ast, diag = compilar_texto(fuente)
        assert diag.codigo_salida() == 0
