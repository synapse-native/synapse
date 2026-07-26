"""
test_cluster_raft.py — Pruebas de integración para M8.3 (Consenso Raft)
Valida elección de líder, heartbeats, re-elección tras caída,
replicación de log y consistencia linealizable en cluster de 5 nodos.
"""

import os
import sys
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline import ejecutar_compilador

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TESTS_DIR = os.path.join(PROJECT_ROOT, 'tests')
TOOLCHAIN_GCC = os.path.join(PROJECT_ROOT, 'toolchain_gcc12', 'mingw64', 'bin')
BIN_RAFT = os.path.join(TESTS_DIR, 'test_cluster_raft.exe')
TEMP_DIR = os.path.join(PROJECT_ROOT, '_test_raft_temp')
os.makedirs(TEMP_DIR, exist_ok=True)


def _write_temp_syn(codigo: str) -> str:
    import uuid
    temp_name = f"test_raft_{uuid.uuid4().hex[:8]}.syn"
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
    env = os.environ.copy()
    env['PATH'] = TOOLCHAIN_GCC + os.pathsep + env.get('PATH', '')
    try:
        r = subprocess.run([path], capture_output=True, text=True, timeout=30, env=env)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, '', 'TIMEOUT'
    except FileNotFoundError:
        return -1, '', f'Binary not found: {path}'


def test_binario_raft_existe():
    """El binario de test Raft debe existir y ejecutarse correctamente"""
    assert os.path.exists(BIN_RAFT), f"Binary not found: {BIN_RAFT}"
    rc, out, err = _ejecutar_binario(BIN_RAFT)
    assert rc == 0, f"Binary execution failed (rc={rc}): {err[:200]}"
    assert "77 passed, 0 failed" in out, "Missing success summary in output"


def test_todas_las_validaciones_raft_pasan():
    """El binario Raft debe reportar 0 fallos"""
    rc, out, err = _ejecutar_binario(BIN_RAFT)
    assert rc == 0, f"Raft binary returned {rc}"
    passes = out.count("[PASS]")
    fails = out.count("[FAIL]")
    assert fails == 0, f"Se encontraron {fails} fallos"
    assert passes >= 77, f"Solo {passes} tests pasaron (se esperaban 77+)"


def test_modulo_cluster_raft_importa():
    """El módulo std.cluster con funciones raft_* se importa correctamente"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> nulo:
    retornar"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Importación falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


def test_raft_inicializar_compila():
    """Programa Synapse que llama raft_inicializar compila correctamente"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> entero:
    r = raft_inicializar(0, 5, 42)
    retornar r"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Compilación raft_inicializar falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


def test_raft_estado_compila():
    """Programa Synapse que llama raft_estado compila correctamente"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> entero:
    raft_inicializar(0, 5, 42)
    e = raft_estado(0)
    retornar e"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Compilación raft_estado falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


def test_raft_tick_compila():
    """Programa Synapse que llama raft_tick compila correctamente"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> entero:
    raft_inicializar(0, 5, 42)
    raft_iniciar(0, 0)
    e = raft_tick(1000000000, 0)
    retornar e"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Compilación raft_tick falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


def test_raft_info_compila():
    """Programa Synapse que llama raft_info compila correctamente"""
    codigo = """#lang: es
importar std.cluster

funcion principal() -> entero:
    raft_inicializar(0, 5, 42)
    i = raft_info(0)
    retornar 0"""
    temp_syn = _write_temp_syn(codigo)
    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, f"Compilación raft_info falló (código {resultado})"
    finally:
        _cleanup_temp_syn(temp_syn)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])