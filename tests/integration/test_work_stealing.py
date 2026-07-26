"""
test_work_stealing.py — Pruebas de integración para M8.2 (Scheduler Work-Stealing Distribuido)
Valida colas locales de tareas, protocolo de robo WSTEAL/WSTOLEN/WNONE,
redistribución de carga, ownership de tareas y ausencia de condiciones de carrera.
"""

import os
import sys
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline import ejecutar_compilador

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TESTS_DIR = os.path.join(PROJECT_ROOT, 'tests')
TOOLCHAIN_GCC = os.path.join(PROJECT_ROOT, 'toolchain_gcc12', 'mingw64', 'bin')
GCC = os.path.join(TOOLCHAIN_GCC, 'gcc.exe')
BIN_WS = os.path.join(TESTS_DIR, 'test_work_stealing.exe')
BIN_C_SRC = os.path.join(TESTS_DIR, 'test_work_stealing.c')
TEMP_DIR = os.path.join(PROJECT_ROOT, '_test_ws_temp')
os.makedirs(TEMP_DIR, exist_ok=True)


def _write_temp_syn(codigo: str) -> str:
    import uuid
    temp_name = f"test_ws_{uuid.uuid4().hex[:8]}.syn"
    temp_path = os.path.join(TEMP_DIR, temp_name)
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(codigo)
    return temp_path


def _cleanup_temp_syn(temp_syn: str):
    base = temp_syn.replace('.syn', '')
    for ext in ['.syn', '.exe', '.c', '.syn.json']:
        path = base + ext
        if os.path.exists(path):
            try:
                os.unlink(path)
            except:
                pass


def _ejecutar_binario(path: str) -> tuple:
    """Ejecuta binario y retorna (rc, stdout, stderr)."""
    env = os.environ.copy()
    env['PATH'] = TOOLCHAIN_GCC + os.pathsep + env.get('PATH', '')
    try:
        r = subprocess.run([path], capture_output=True, text=True, timeout=30, env=env)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, '', 'TIMEOUT'
    except FileNotFoundError:
        return -1, '', f'Binary not found: {path}'


# ── Test 1: C binary exists and runs ───────────────────────────────

def test_binario_existe():
    """El binario de test C debe existir y ser ejecutable"""
    assert os.path.exists(BIN_WS), f"Binary not found: {BIN_WS}"
    rc, out, err = _ejecutar_binario(BIN_WS)
    assert rc == 0, f"Binary execution failed (rc={rc}): {err[:200]}"
    assert "43 passed, 0 failed" in out, "Missing success summary in output"


# ── Test 2: C binary passes all tests ──────────────────────────

def test_todas_las_validaciones_c_pasan():
    """El binario de test C reporta 0 fallos en todos los escenarios"""
    rc, out, err = _ejecutar_binario(BIN_WS)
    assert rc == 0, f"Work-stealing binary returned {rc}: {err[:200]}"
    # Count PASS/FAIL lines
    passes = out.count("[PASS]")
    fails = out.count("[FAIL]")
    assert fails == 0, f"Se encontraron {fails} fallos en {passes} tests"
    assert passes >= 43, f"Solo {passes} tests pasaron (se esperaban 43+)"


# ── Test 3: Synapse module compila con ws_* functions ──────────

def test_modulo_cluster_ws_importa():
    """El módulo std.cluster con funciones ws_* se importa correctamente"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> nulo:
    retornar"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Importación de std.cluster con ws falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


# ── Test 4: Compilación de programa Synapse con ws_encolar ─────

def test_ws_encolar_compila():
    """Programa Synapse que llama ws_encolar compila correctamente"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> entero:
    r = ws_inicializar(100)
    t = ws_encolar(42, "datos")
    retornar t"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Compilación de ws_encolar falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


# ── Test 5: Compilación de programa Synapse con ws_desencolar ──

def test_ws_desencolar_compila():
    """Programa Synapse que llama ws_desencolar compila correctamente"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> entero:
    ws_inicializar(100)
    ws_encolar(1, "a")
    t = ws_desencolar()
    retornar 0"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Compilación de ws_desencolar falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


# ── Test 6: Compilación de ws_profundidad y ws_carga_estimada ──

def test_ws_metricas_compilan():
    """Programa Synapse que llama ws_profundidad y ws_carga_estimada compila"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> entero:
    ws_inicializar(100)
    p = ws_profundidad()
    c = ws_carga_estimada()
    retornar 0"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Compilación de métricas falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


# ── Test 7: Compilación de ws_procesar_mensaje ─────────────────

def test_ws_procesar_compila():
    """Programa Synapse que llama ws_procesar_mensaje compila"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> entero:
    ws_inicializar(100)
    ws_encolar(1, "test")
    r = ws_procesar_mensaje("WSTEAL:1")
    t = ws_ultima_robada()
    retornar 0"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Compilación de ws_procesar_mensaje falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])