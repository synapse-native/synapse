# -*- coding: utf-8 -*-
"""
tests/integration/test_syquex_benchmarks.py — Benchmarks de rendimiento Syquex (FASE 28 ME_28_T5).
Manual 3 (certificacion).

Mide tiempos de compilacion y ejecucion de Syquex vs Python para verificar
que Syquex es competitivo en rendimiento (roadmap F28: "10-50x mas rapido que Python").

cumple Manual 3 3
"""
import os
import subprocess
import sys
import time
import tempfile

import pytest

pytestmark = pytest.mark.integration

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, RAIZ)

from pipeline import ejecutar_compilador

FIXTURES = os.path.join(RAIZ, "tests", "fixtures")


def _compilar_syq(nombre_archivo, tmp_path):
    ruta = os.path.join(FIXTURES, nombre_archivo)
    if not os.path.exists(ruta):
        pytest.fail(f"Fixture no encontrado: {nombre_archivo}")
    out = str(tmp_path / nombre_archivo.replace('.syq', '.exe'))
    inicio = time.perf_counter()
    rc = ejecutar_compilador(ruta, output_path=out)
    duracion = time.perf_counter() - inicio
    return rc, out, duracion


def _ejecutar(exe_path, timeout=30):
    inicio = time.perf_counter()
    proc = subprocess.run(
        [exe_path], capture_output=True, text=True, timeout=timeout,
        encoding="utf-8", errors="replace",
    )
    duracion = time.perf_counter() - inicio
    return proc, duracion


def _ejecutar_python(codigo, timeout=30):
    fd, path = tempfile.mkstemp(suffix='.py')
    try:
        os.write(fd, codigo.encode('utf-8'))
        os.close(fd)
        fd = None
        inicio = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, path], capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        duracion = time.perf_counter() - inicio
        return proc, duracion
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            os.remove(path)
        except OSError:
            pass


# ============================================================
# BENCHMARKS DE COMPILACION
# ============================================================

class TestSyquexBenchCompilation:
    """Benchmarks de tiempo de compilacion Syquex."""

    def test_compila_r91_fullstack(self, tmp_path):
        """Compila R91 fullstack y mide tiempo."""
        rc, out, duracion = _compilar_syq("test_r91_fullstack.syq", tmp_path)
        assert rc == 0, f"Compilacion falló (rc={rc})"
        assert duracion < 30, f"Compilacion muy lenta: {duracion:.2f}s"
        print(f"\n  [BENCH] R91 fullstack compilation: {duracion:.3f}s")

    def test_compila_r90_compila(self, tmp_path):
        """Compila R90 (coincidir+mientras) y mide tiempo."""
        rc, out, duracion = _compilar_syq("test_r90_compila.syq", tmp_path)
        assert rc == 0
        assert duracion < 30
        print(f"\n  [BENCH] R90 compilation: {duracion:.3f}s")

    def test_compila_f24_lista_mapa(self, tmp_path):
        """Compila F24 lista+mapa y mide tiempo."""
        rc, out, duracion = _compilar_syq("test_f24_lista_mapa.syq", tmp_path)
        assert rc == 0
        assert duracion < 30
        print(f"\n  [BENCH] F24 lista+mapa compilation: {duracion:.3f}s")

    def test_compila_range_loop(self, tmp_path):
        """Compila range loop y mide tiempo."""
        rc, out, duracion = _compilar_syq("test_range_loop.syq", tmp_path)
        assert rc == 0
        assert duracion < 30
        print(f"\n  [BENCH] range loop compilation: {duracion:.3f}s")


# ============================================================
# BENCHMARKS DE EJECUCION: Syquex vs Python
# ============================================================

class TestSyquexVsPython:
    """Benchmarks comparativos Syquex vs Python."""

    SYQ_FIB = """#lang: es
funcion fib(n: entero) -> entero:
    si n <= 1:
        retornar n
    retornar fib(n - 1) + fib(n - 2)

funcion principal() -> entero:
    let resultado = fib(30)
    escribir_linea(entero_a_texto(resultado))
    retornar 0
"""

    PY_FIB = """import sys
sys.setrecursionlimit(10000)
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
print(fib(30))
"""

    SYQ_LOOP = """#lang: es
funcion principal() -> entero:
    let acc = 0
    let i = 0
    mientras i < 1000000:
        acc = acc + i
        i = i + 1
    escribir_linea(entero_a_texto(acc))
    retornar 0
"""

    PY_LOOP = """acc = 0
for i in range(1000000):
    acc += i
print(acc)
"""

    def test_fibonacci_30(self, tmp_path):
        """Fibonacci(30): ejecucion Syquex compilado vs Python interpretado."""
        fd, syq_path = tempfile.mkstemp(suffix='.syq')
        try:
            os.write(fd, self.SYQ_FIB.encode('utf-8'))
            os.close(fd)
            fd = None
            out = str(tmp_path / "fib.exe")
            rc = ejecutar_compilador(syq_path, output_path=out)
            assert rc == 0, f"Compilacion Syquex falló"

            proc_syq, t_syq = _ejecutar(out)
            assert proc_syq.returncode == 0, f"Syquex exec falló: {proc_syq.stderr}"

            proc_py, t_py = _ejecutar_python(self.PY_FIB)
            assert proc_py.returncode == 0, f"Python exec falló: {proc_py.stderr}"

            assert proc_syq.stdout.strip() == proc_py.stdout.strip(), \
                f"Resultados difieren: Syquex={proc_syq.stdout.strip()} Python={proc_py.stdout.strip()}"

            speedup = t_py / t_syq if t_syq > 0 else float('inf')
            print(f"\n  [BENCH] Fibonacci(30) exec only: Syquex={t_syq:.3f}s Python={t_py:.3f}s speedup={speedup:.1f}x")
            assert speedup > 0.5, f"Syquex demasiado lento vs Python: {speedup:.2f}x"
        finally:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            try:
                os.remove(syq_path)
            except OSError:
                pass

    def test_loop_1M(self, tmp_path):
        """Loop 1M iteraciones: ejecucion Syquex compilado vs Python."""
        fd, syq_path = tempfile.mkstemp(suffix='.syq')
        try:
            os.write(fd, self.SYQ_LOOP.encode('utf-8'))
            os.close(fd)
            fd = None
            out = str(tmp_path / "loop.exe")
            rc = ejecutar_compilador(syq_path, output_path=out)
            assert rc == 0

            proc_syq, t_syq = _ejecutar(out)
            assert proc_syq.returncode == 0

            proc_py, t_py = _ejecutar_python(self.PY_LOOP)
            assert proc_py.returncode == 0

            assert proc_syq.stdout.strip() == proc_py.stdout.strip()

            speedup = t_py / t_syq if t_syq > 0 else float('inf')
            print(f"\n  [BENCH] Loop 1M exec only: Syquex={t_syq:.3f}s Python={t_py:.3f}s speedup={speedup:.1f}x")
            assert speedup > 0.5, f"Syquex demasiado lento: {speedup:.2f}x"
        finally:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            try:
                os.remove(syq_path)
            except OSError:
                pass

    def test_ejecuta_r91_completo(self, tmp_path):
        """R91 fullstack: compila + ejecuta en tiempo razonable."""
        rc, out, t_comp = _compilar_syq("test_r91_fullstack.syq", tmp_path)
        assert rc == 0
        proc, t_exec = _ejecutar(out)
        assert proc.returncode == 0
        total = t_comp + t_exec
        print(f"\n  [BENCH] R91 total (compile+exec): {total:.3f}s (compile={t_comp:.3f}s exec={t_exec:.3f}s)")
        assert total < 30, f"R91 total excesivo: {total:.2f}s"


# ============================================================
# BENCHMARKS DE MEMORIA (basic)
# ============================================================

class TestSyquexMemoryBasic:
    """Tests basicos de uso de memoria (sin fugas aparentes)."""

    def test_compila_ejecuta_10_iteraciones(self, tmp_path):
        """Compilar y ejecutar 10 veces no acumula tiempo (sin fugas)."""
        rc0, out0, t0 = _compilar_syq("test_r90_compila.syq", tmp_path)
        assert rc0 == 0

        tiempos = []
        for _ in range(10):
            _, _, t = _compilar_syq("test_r90_compila.syq", tmp_path)
            tiempos.append(t)

        promedio = sum(tiempos) / len(tiempos)
        max_t = max(tiempos)
        assert max_t < promedio * 3, \
            f"Posible fuga: max={max_t:.3f}s vs promedio={promedio:.3f}s"
        print(f"\n  [BENCH] 10 iteraciones: promedio={promedio:.3f}s max={max_t:.3f}s")
