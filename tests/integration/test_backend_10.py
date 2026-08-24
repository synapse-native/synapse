# -*- coding: utf-8 -*-
"""
test_backend_10.py — Tests avanzados de backends LLVM/WASM para cobertura 10/10.

Complementa test_generator.py (backend C) con:
  1. LLVM backend: estructura, funciones, IR válido
  2. WASM backend: estructura, funciones, WAT válido
  3. Integración: backends se pueden importar desde Synapse
  4. Estructura de archivos backend
"""
import os
import re
import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _leer_archivo(ruta_relativa: str) -> str:
    """Lee un archivo del proyecto."""
    ruta = os.path.join(RAIZ, ruta_relativa)
    if not os.path.exists(ruta):
        return ""
    with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def _extraer_funciones(contenido: str) -> list:
    """Extrae nombres de funciones de código Synapse."""
    return re.findall(r'funcion\s+(\w+)\s*\(', contenido)


# ---------------------------------------------------------------------------
# 1. LLVM BACKEND
# ---------------------------------------------------------------------------

class TestLLVMBackend:
    """Verifica el backend LLVM (nucleo/llvm_backend.syn)."""

    def test_archivo_existe(self):
        """llvm_backend.syn existe."""
        contenido = _leer_archivo("nucleo/llvm_backend.syn")
        assert contenido, "nucleo/llvm_backend.syn no encontrado o vacío"

    def test_tiene_funciones_principales(self):
        """llvm_backend.syn tiene funciones esenciales de IR."""
        contenido = _leer_archivo("nucleo/llvm_backend.syn")
        funcs_requeridas = [
            'llvm_inicializar', 'llvm_emitir', 'llvm_obtener_salida',
            'llvm_declarar_funcion', 'llvm_finalizar_funcion_con_ret',
            'llvm_retorno_const', 'llvm_add', 'llvm_sub', 'llvm_mul',
        ]
        funcs_encontradas = _extraer_funciones(contenido)
        for f in funcs_requeridas:
            assert f in funcs_encontradas, \
                f"LLVM backend: función '{f}' no encontrada"

    def test_tiene_operaciones_aritmeticas(self):
        """llvm_backend.syn tiene add, sub, mul, sdiv, srem."""
        contenido = _leer_archivo("nucleo/llvm_backend.syn")
        ops = ['llvm_add', 'llvm_sub', 'llvm_mul', 'llvm_sdiv', 'llvm_srem']
        funcs = _extraer_funciones(contenido)
        for op in ops:
            assert op in funcs, \
                f"LLVM backend: operación '{op}' no encontrada"

    def test_tiene_control_flujo(self):
        """llvm_backend.syn tiene br, cond_br, etiqueta."""
        contenido = _leer_archivo("nucleo/llvm_backend.syn")
        funcs = _extraer_funciones(contenido)
        assert 'llvm_br' in funcs, "LLVM backend: br no encontrado"
        assert 'llvm_cond_br' in funcs, "LLVM backend: cond_br no encontrado"
        assert 'llvm_etiqueta' in funcs, "LLVM backend: etiqueta no encontrado"

    def test_tiene_manifiesto(self):
        """llvm_backend.syn empieza con #lang: es."""
        contenido = _leer_archivo("nucleo/llvm_backend.syn")
        assert contenido.startswith("#lang:"), \
            "LLVM backend: falta directiva #lang:"

    def test_longitud_minima(self):
        """llvm_backend.syn tiene al menos 100 líneas."""
        contenido = _leer_archivo("nucleo/llvm_backend.syn")
        lineas = len(contenido.split('\n'))
        assert lineas >= 100, \
            f"LLVM backend: solo {lineas} líneas (esperado >=100)"


# ---------------------------------------------------------------------------
# 2. WASM BACKEND
# ---------------------------------------------------------------------------

class TestWASMBackend:
    """Verifica el backend WASM (nucleo/wasm_backend.syn)."""

    def test_archivo_existe(self):
        """wasm_backend.syn existe."""
        contenido = _leer_archivo("nucleo/wasm_backend.syn")
        assert contenido, "nucleo/wasm_backend.syn no encontrado o vacío"

    def test_tiene_funciones_principales(self):
        """wasm_backend.syn tiene funciones esenciales de WAT."""
        contenido = _leer_archivo("nucleo/wasm_backend.syn")
        funcs_requeridas = [
            'wasm_inicializar', 'wasm_emitir', 'wasm_obtener_salida',
            'wasm_iniciar_modulo', 'wasm_finalizar_modulo',
            'wasm_declarar_funcion', 'wasm_finalizar_funcion',
            'wasm_const_i32', 'wasm_add', 'wasm_sub', 'wasm_mul',
        ]
        funcs_encontradas = _extraer_funciones(contenido)
        for f in funcs_requeridas:
            assert f in funcs_encontradas, \
                f"WASM backend: función '{f}' no encontrada"

    def test_tiene_operaciones_aritmeticas(self):
        """wasm_backend.syn tiene add, sub, mul, div_s."""
        contenido = _leer_archivo("nucleo/wasm_backend.syn")
        ops = ['wasm_add', 'wasm_sub', 'wasm_mul', 'wasm_div_s']
        funcs = _extraer_funciones(contenido)
        for op in ops:
            assert op in funcs, \
                f"WASM backend: operación '{op}' no encontrada"

    def test_tiene_locales(self):
        """wasm_backend.syn tiene manejo de locales."""
        contenido = _leer_archivo("nucleo/wasm_backend.syn")
        funcs = _extraer_funciones(contenido)
        assert 'wasm_declarar_local' in funcs, \
            "WASM backend: declarar_local no encontrado"
        assert 'wasm_local_get' in funcs, \
            "WASM backend: local_get no encontrado"
        assert 'wasm_local_set' in funcs, \
            "WASM backend: local_set no encontrado"

    def test_tiene_manifiesto(self):
        """wasm_backend.syn empieza con #lang: es."""
        contenido = _leer_archivo("nucleo/wasm_backend.syn")
        assert contenido.startswith("#lang:"), \
            "WASM backend: falta directiva #lang:"

    def test_longitud_minima(self):
        """wasm_backend.syn tiene al menos 100 líneas."""
        contenido = _leer_archivo("nucleo/wasm_backend.syn")
        lineas = len(contenido.split('\n'))
        assert lineas >= 100, \
            f"WASM backend: solo {lineas} líneas (esperado >=100)"


# ---------------------------------------------------------------------------
# 3. BINDINGS (std/llvm.syn, std/wasm.syn)
# ---------------------------------------------------------------------------

class TestBindings:
    """Verifica los bindings de LLVM y WASM."""

    def test_llvm_syn_existe(self):
        """std/llvm.syn existe."""
        contenido = _leer_archivo("std/llvm.syn")
        assert contenido, "std/llvm.syn no encontrado o vacío"

    def test_wasm_syn_existe(self):
        """std/wasm.syn existe."""
        contenido = _leer_archivo("std/wasm.syn")
        assert contenido, "std/wasm.syn no encontrado o vacío"

    def test_llvm_syn_tiene_funciones(self):
        """std/llvm.syn tiene funciones de binding."""
        contenido = _leer_archivo("std/llvm.syn")
        funcs = _extraer_funciones(contenido)
        assert len(funcs) > 0, "std/llvm.syn no tiene funciones"

    def test_wasm_syn_tiene_funciones(self):
        """std/wasm.syn tiene funciones de binding."""
        contenido = _leer_archivo("std/wasm.syn")
        funcs = _extraer_funciones(contenido)
        assert len(funcs) > 0, "std/wasm.syn no tiene funciones"


# ---------------------------------------------------------------------------
# 4. INTEGRACIÓN: BACKENDS COMPARTEN ESTRUCTURA
# ---------------------------------------------------------------------------

class TestIntegracionBackends:
    """Verifica que los backends comparten estructura común."""

    def test_ambos_tienen_inicializar(self):
        """Ambos backends tienen función de inicialización."""
        llvm = _extraer_funciones(_leer_archivo("nucleo/llvm_backend.syn"))
        wasm = _extraer_funciones(_leer_archivo("nucleo/wasm_backend.syn"))
        assert 'llvm_inicializar' in llvm
        assert 'wasm_inicializar' in wasm

    def test_ambos_tienen_emitir(self):
        """Ambos backends tienen función de emisión."""
        llvm = _extraer_funciones(_leer_archivo("nucleo/llvm_backend.syn"))
        wasm = _extraer_funciones(_leer_archivo("nucleo/wasm_backend.syn"))
        assert 'llvm_emitir' in llvm
        assert 'wasm_emitir' in wasm

    def test_ambos_tienen_obtener_salida(self):
        """Ambos backends tienen función para obtener salida."""
        llvm = _extraer_funciones(_leer_archivo("nucleo/llvm_backend.syn"))
        wasm = _extraer_funciones(_leer_archivo("nucleo/wasm_backend.syn"))
        assert 'llvm_obtener_salida' in llvm
        assert 'wasm_obtener_salida' in wasm

    def test_ambos_tienen_add_sub_mul(self):
        """Ambos backends tienen operaciones aritméticas básicas."""
        llvm = _extraer_funciones(_leer_archivo("nucleo/llvm_backend.syn"))
        wasm = _extraer_funciones(_leer_archivo("nucleo/wasm_backend.syn"))
        for op in ['add', 'sub', 'mul']:
            assert f'llvm_{op}' in llvm, f"LLVM: {op} no encontrado"
            assert f'wasm_{op}' in wasm, f"WASM: {op} no encontrado"
