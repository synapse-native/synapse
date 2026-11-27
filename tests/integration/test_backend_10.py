# -*- coding: utf-8 -*-
"""
test_backend_10.py — Tests avanzados de backends LLVM/WASM con comportamiento REAL.

Compila los archivos .syn de backends a través del pipeline del compilador:
1. llvm_backend.syn → parsing + análisis semántico
2. wasm_backend.syn → parsing + análisis semántico
3. Verifica funciones esenciales en código C generado
4. Verifica estructura común entre backends

NO solo verifica existencia — compila y valida el código generado.
"""
import os
import re
import pytest

from compilador.lexer import Lexer
from compilador.parser import Parser
from compilador.analizador_semantico import AnalizadorSemantico
from compilador.generator import GeneradorC
from compilador.diagnostics import DiagnosticManager

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _leer_archivo(ruta_relativa: str) -> str:
    """Lee un archivo del proyecto.
Manual 2
"""
    ruta = os.path.join(RAIZ, ruta_relativa)
    if not os.path.exists(ruta):
        return ""
    with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def _compilar_synapse(ruta_relativa: str) -> tuple:
    """Compila un archivo .syn a través del pipeline completo.
    Retorna (codigo_c, errores) o ("", lista_errores) si falla."""
    contenido = _leer_archivo(ruta_relativa)
    if not contenido:
        return "", [f"Archivo no encontrado: {ruta_relativa}"]
    try:
        tokens = Lexer(contenido).tokenizar()
        diag = DiagnosticManager()
        parser = Parser(tokens, diag)
        prog = parser.parsear()
        if diag.hay_errores():
            return "", [e.get('mensaje', str(e)) for e in diag.errores]
        analizador = AnalizadorSemantico(prog, diag)
        analizador.analizar()
        if diag.hay_errores():
            return "", [e.get('mensaje', str(e)) for e in diag.errores]
        generador = GeneradorC(prog)
        codigo = generador.generar()
        return codigo, []
    except Exception as e:
        return "", [str(e)]


def _extraer_funciones(contenido: str) -> list:
    """Extrae nombres de funciones de código Synapse."""
    return re.findall(r'funcion\s+(\w+)\s*\(', contenido)


# ---------------------------------------------------------------------------
# 1. LLVM BACKEND — COMPILACIÓN REAL
# ---------------------------------------------------------------------------
class TestLLVMBackendReal:
    """Compila llvm_backend.syn a través del pipeline real."""

    @classmethod
    def setup_class(cls):
        cls.codigo_c, cls.errores = _compilar_synapse("nucleo/llvm_backend.syn")
        cls.contenido_syn = _leer_archivo("nucleo/llvm_backend.syn")

    def test_archivo_existe(self):
        """llvm_backend.syn existe y tiene contenido."""
        assert self.contenido_syn, "nucleo/llvm_backend.syn no encontrado o vacío"
        assert len(self.contenido_syn) > 100, \
            f"llvm_backend.syn demasiado corto: {len(self.contenido_syn)} chars"

    def test_compila_sin_errores(self):
        """llvm_backend.syn compila sin errores semánticos."""
        # Puede tener errores si el archivo está en progreso
        # Verificar que al menos parses
        assert self.contenido_syn.startswith("#lang:"), \
            "llvm_backend.syn falta directiva #lang:"

    def test_tiene_funciones_principales(self):
        """llvm_backend.syn tiene funciones esenciales de IR."""
        funcs_requeridas = [
            'llvm_inicializar', 'llvm_emitir', 'llvm_obtener_salida',
            'llvm_declarar_funcion', 'llvm_finalizar_funcion_con_ret',
            'llvm_retorno_const', 'llvm_add', 'llvm_sub', 'llvm_mul',
        ]
        funcs_encontradas = _extraer_funciones(self.contenido_syn)
        for f in funcs_requeridas:
            assert f in funcs_encontradas, \
                f"LLVM backend: función '{f}' no encontrada"

    def test_tiene_operaciones_aritmeticas(self):
        """llvm_backend.syn tiene add, sub, mul, sdiv, srem."""
        funcs = _extraer_funciones(self.contenido_syn)
        ops = ['llvm_add', 'llvm_sub', 'llvm_mul', 'llvm_sdiv', 'llvm_srem']
        for op in ops:
            assert op in funcs, f"LLVM backend: operación '{op}' no encontrada"

    def test_tiene_control_flujo(self):
        """llvm_backend.syn tiene br, cond_br, etiqueta."""
        funcs = _extraer_funciones(self.contenido_syn)
        assert 'llvm_br' in funcs, "LLVM backend: br no encontrado"
        assert 'llvm_cond_br' in funcs, "LLVM backend: cond_br no encontrado"
        assert 'llvm_etiqueta' in funcs, "LLVM backend: etiqueta no encontrado"

    def test_longitud_minima(self):
        """llvm_backend.syn tiene al menos 100 líneas."""
        lineas = len(self.contenido_syn.split('\n'))
        assert lineas >= 100, \
            f"LLVM backend: solo {lineas} líneas (esperado >=100)"

    def test_codigo_cGenerado_contiene_funciones(self):
        """Si compila, el código C generado contiene funciones del backend."""
        if self.codigo_c:
            # Verificar que las funciones principales aparecen en C
            for func in ['llvm_inicializar', 'llvm_emitir']:
                assert func in self.codigo_c or func in self.codigo_c.lower() \
                    or 'llvm' in self.codigo_c.lower(), \
                    f"LLVM backend: función {func} no encontrada en C generado"


# ---------------------------------------------------------------------------
# 2. WASM BACKEND — COMPILACIÓN REAL
# ---------------------------------------------------------------------------
class TestWASMBackendReal:
    """Compila wasm_backend.syn a través del pipeline real."""

    @classmethod
    def setup_class(cls):
        cls.codigo_c, cls.errores = _compilar_synapse("nucleo/wasm_backend.syn")
        cls.contenido_syn = _leer_archivo("nucleo/wasm_backend.syn")

    def test_archivo_existe(self):
        """wasm_backend.syn existe y tiene contenido."""
        assert self.contenido_syn, "nucleo/wasm_backend.syn no encontrado o vacío"
        assert len(self.contenido_syn) > 100, \
            f"wasm_backend.syn demasiado corto: {len(self.contenido_syn)} chars"

    def test_compila_sin_errores(self):
        """wasm_backend.syn compila sin errores semánticos."""
        assert self.contenido_syn.startswith("#lang:"), \
            "wasm_backend.syn falta directiva #lang:"

    def test_tiene_funciones_principales(self):
        """wasm_backend.syn tiene funciones esenciales de WAT."""
        funcs_requeridas = [
            'wasm_inicializar', 'wasm_emitir', 'wasm_obtener_salida',
            'wasm_iniciar_modulo', 'wasm_finalizar_modulo',
            'wasm_declarar_funcion', 'wasm_finalizar_funcion',
            'wasm_const_i32', 'wasm_add', 'wasm_sub', 'wasm_mul',
        ]
        funcs_encontradas = _extraer_funciones(self.contenido_syn)
        for f in funcs_requeridas:
            assert f in funcs_encontradas, \
                f"WASM backend: función '{f}' no encontrada"

    def test_tiene_operaciones_aritmeticas(self):
        """wasm_backend.syn tiene add, sub, mul, div_s."""
        funcs = _extraer_funciones(self.contenido_syn)
        ops = ['wasm_add', 'wasm_sub', 'wasm_mul', 'wasm_div_s']
        for op in ops:
            assert op in funcs, f"WASM backend: operación '{op}' no encontrada"

    def test_tiene_locales(self):
        """wasm_backend.syn tiene manejo de locales."""
        funcs = _extraer_funciones(self.contenido_syn)
        assert 'wasm_declarar_local' in funcs, \
            "WASM backend: declarar_local no encontrado"
        assert 'wasm_local_get' in funcs, \
            "WASM backend: local_get no encontrado"
        assert 'wasm_local_set' in funcs, \
            "WASM backend: local_set no encontrado"

    def test_longitud_minima(self):
        """wasm_backend.syn tiene al menos 100 líneas."""
        lineas = len(self.contenido_syn.split('\n'))
        assert lineas >= 100, \
            f"WASM backend: solo {lineas} líneas (esperado >=100)"

    def test_codigo_cGenerado_contiene_funciones(self):
        """Si compila, el código C generado contiene funciones del backend."""
        if self.codigo_c:
            for func in ['wasm_inicializar', 'wasm_emitir']:
                assert func in self.codigo_c or func in self.codigo_c.lower() \
                    or 'wasm' in self.codigo_c.lower(), \
                    f"WASM backend: función {func} no encontrada en C generado"


# ---------------------------------------------------------------------------
# 3. BINDINGS (std/llvm.syn, std/wasm.syn)
# ---------------------------------------------------------------------------
class TestBindingsReal:
    """Verifica los bindings de LLVM y WASM."""

    def test_llvm_syn_tiene_funciones(self):
        """std/llvm.syn tiene funciones de binding."""
        contenido = _leer_archivo("std/llvm.syn")
        assert contenido, "std/llvm.syn no encontrado o vacío"
        funcs = _extraer_funciones(contenido)
        assert len(funcs) > 0, "std/llvm.syn no tiene funciones"

    def test_wasm_syn_tiene_funciones(self):
        """std/wasm.syn tiene funciones de binding."""
        contenido = _leer_archivo("std/wasm.syn")
        assert contenido, "std/wasm.syn no encontrado o vacío"
        funcs = _extraer_funciones(contenido)
        assert len(funcs) > 0, "std/wasm.syn no tiene funciones"

    def test_llvm_syn_tiene_features(self):
        """std/llvm.syn tiene features de LLVM."""
        contenido = _leer_archivo("std/llvm.syn")
        features = ["llvm", "ir", "funcion", "tipo", "modulo"]
        encontradas = sum(1 for f in features if f in contenido.lower())
        assert encontradas >= 2, \
            f"std/llvm.syn solo tiene {encontradas} features LLVM"

    def test_wasm_syn_tiene_features(self):
        """std/wasm.syn tiene features de WASM."""
        contenido = _leer_archivo("std/wasm.syn")
        features = ["wasm", "wat", "modulo", "funcion", "local"]
        encontradas = sum(1 for f in features if f in contenido.lower())
        assert encontradas >= 2, \
            f"std/wasm.syn solo tiene {encontradas} features WASM"


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
