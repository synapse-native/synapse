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
        # MinGW ld.bfd: cannot write to 'nul' device — use temp file output
        temp_exe = os.path.join(TESTS_DIR, "_test_link_out.exe")
        try:
            gcc = _find_gcc()
            # Manual 1 §4: Linkado debe ser exitoso (sin errores de símbolos)
            cmd = [gcc, main_c, *objs_existentes, "-o", temp_exe,
                   "-lm", "-lpthread", "-lws2_32", "-Wl,--no-keep-memory"]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                pass
            elif "file truncated" in r.stderr:
                # Workaround for MinGW ld.bfd bug #12754:
                # Merge all .o into one relocatable via -r (no symbol
                # resolution → less BFD memory), then final-link merged + main_c.
                temp_obj = os.path.join(TESTS_DIR, "_test_merged.o")
                try:
                    cmd_m = [gcc, "-r", "-o", temp_obj, *objs_existentes,
                             "-Wl,--no-keep-memory"]
                    r_m = subprocess.run(
                        cmd_m, capture_output=True, text=True, timeout=60)
                    if r_m.returncode == 0:
                        cmd_f = [gcc, main_c, temp_obj, "-o", temp_exe,
                                 "-lm", "-lpthread", "-lws2_32"]
                        r_f = subprocess.run(
                            cmd_f, capture_output=True, text=True, timeout=30)
                        assert r_f.returncode == 0, \
                            f"Link final falló: {r_f.stderr[:500]}"
                    else:
                        # Merge of all failed — try incremental 2-stage merge
                        temp2 = os.path.join(TESTS_DIR, "_test_m2.o")
                        try:
                            mid = len(objs_existentes) // 2
                            cmd_s = [gcc, "-r", "-o", temp_obj,
                                     *objs_existentes[:mid],
                                     "-Wl,--no-keep-memory"]
                            r_s = subprocess.run(
                                cmd_s, capture_output=True, text=True,
                                timeout=60)
                            assert r_s.returncode == 0, \
                                f"Merge S1 falló: {r_s.stderr[:500]}"
                            cmd_s2 = [gcc, "-r", "-o", temp2,
                                      temp_obj, *objs_existentes[mid:],
                                      "-Wl,--no-keep-memory"]
                            r_s2 = subprocess.run(
                                cmd_s2, capture_output=True, text=True,
                                timeout=60)
                            assert r_s2.returncode == 0, \
                                f"Merge S2 falló: {r_s2.stderr[:500]}"
                            cmd_f = [gcc, main_c, temp2, "-o", temp_exe,
                                     "-lm", "-lpthread", "-lws2_32"]
                            r_f = subprocess.run(
                                cmd_f, capture_output=True, text=True,
                                timeout=30)
                            assert r_f.returncode == 0, \
                                f"Link final falló: {r_f.stderr[:500]}"
                        finally:
                            if os.path.exists(temp2):
                                os.remove(temp2)
                finally:
                    if os.path.exists(temp_obj):
                        os.remove(temp_obj)
            else:
                assert r.returncode == 0, \
                    f"Linkado falló: {r.stderr[:500]}"
        finally:
            if os.path.exists(main_c):
                os.remove(main_c)
            if os.path.exists(temp_exe):
                os.remove(temp_exe)


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
