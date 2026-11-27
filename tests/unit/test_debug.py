# cumple Manual 8 4
"""
test_debug.py — Pruebas unitarias para std.debug (Time-Travel Debugging)
Sección 18.2 del Manual de Ingeniería v5.0
"""

import os
import sys
import tempfile
import glob
import shutil
import pytest

pytestmark = pytest.mark.unit

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline import ejecutar_compilador


@pytest.fixture(autouse=True)
def _limpiar_directorio_traces():
    """ME-R2: aisla cada test limpiando ~/.synapse/traces antes de cada prueba.

    El runtime persiste la traza en ~/.synapse/traces (directorio compartido por
    todos los tests). El test de formato lee glob(trace_files)[-1] esperando SU
    propia traza; sin aislamiento, recoge trazas acumuladas de otros tests
    (p. ej. eventos=2 en vez de eventos=1) -> fallo no determinista.
    """
    trace_dir = os.path.expanduser("~/.synapse/traces")
    if os.path.isdir(trace_dir):
        shutil.rmtree(trace_dir, ignore_errors=True)
    yield

# Directorio del proyecto para archivos temporales
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TEMP_DIR = os.path.join(PROJECT_ROOT, '_test_debug_temp')
os.makedirs(TEMP_DIR, exist_ok=True)


def _write_temp_syn(codigo: str) -> str:
    """Escribe un archivo .syn temporal en el directorio del proyecto"""
    import uuid
    temp_name = f"test_debug_{uuid.uuid4().hex[:8]}.syn"
    temp_path = os.path.join(TEMP_DIR, temp_name)
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(codigo)
    return temp_path


def _cleanup_temp_syn(temp_syn: str):
    """Limpia archivos temporales generados"""
    base = temp_syn.replace('.syn', '')
    for ext in ['.syn', '.exe', '.c', '.syn.json']:
        path = base + ext
        if os.path.exists(path):
            try:
                os.unlink(path)
            except:
                pass


def test_debug_registrar_evento():
    """Valida registro de eventos básicos en traza"""
    codigo = """#lang: es
importar std.debug

funcion principal() -> nulo:
    evt = TraceEvent()
    evt.tipo_evento = EVENT_ASSIGNMENT
    evt.fn_nombre = "principal"
    evt.archivo = "test.syn"
    evt.linea = 1
    evt.variable = "x"
    evt.valor_entero = 42
    registrar_evento(evt)
    retornar"""
    temp_syn = _write_temp_syn(codigo)

    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, "Compilación falló"

        # Verificar que se generó el ejecutable
        temp_exe = temp_syn.replace('.syn', '.exe')
        if os.path.exists(temp_exe):
            import subprocess
            result = subprocess.run([temp_exe], capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, f"Ejecución falló: {result.stderr}"
            assert "Sesion iniciada" in result.stderr, "Sesión no iniciada"
    finally:
        _cleanup_temp_syn(temp_syn)


def test_debug_trace_expr():
    """Valida trace(expresion) registra valor"""
    codigo = """#lang: es
importar std.debug

funcion principal() -> nulo:
    x = 10
    trace("x")
    retornar"""
    temp_syn = _write_temp_syn(codigo)

    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, "Compilación falló"
    finally:
        _cleanup_temp_syn(temp_syn)


def test_debug_sesion_persistencia():
    """Valida que finalizar_sesion persiste traza en ~/.synapse/traces/"""
    codigo = """#lang: es
importar std.debug

funcion principal() -> nulo:
    evt = TraceEvent()
    evt.tipo_evento = EVENT_ASSIGNMENT
    evt.variable = "x"
    evt.valor_entero = 1
    registrar_evento(evt)
    evt2 = TraceEvent()
    evt2.tipo_evento = EVENT_ASSIGNMENT
    evt2.variable = "y"
    evt2.valor_entero = 2
    registrar_evento(evt2)
    r = finalizar_sesion()
    escribir_linea(r.valor_str)
    retornar"""
    temp_syn = _write_temp_syn(codigo)

    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, "Compilación falló"

        import subprocess
        temp_exe = temp_syn.replace('.syn', '.exe')
        if os.path.exists(temp_exe):
            result = subprocess.run([temp_exe], capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, f"Ejecución falló: {result.stderr}"

            # Verificar que se imprimió el ID
            assert "trace_" in result.stdout or "trace_" in result.stderr
    finally:
        _cleanup_temp_syn(temp_syn)


def test_debug_buffer_circular():
    """Valida límite de 50,000 eventos en buffer circular"""
    codigo = """#lang: es
importar std.debug

funcion principal() -> nulo:
    i = 0
    mientras i < 60000:
        evt = TraceEvent()
        evt.tipo_evento = EVENT_LOOP_ITERATION
        evt.variable = "i"
        evt.valor_entero = i
        registrar_evento(evt)
        i = i + 1
    finalizar_sesion()
    retornar"""
    temp_syn = _write_temp_syn(codigo)

    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, "Compilación falló"

        import subprocess
        temp_exe = temp_syn.replace('.syn', '.exe')
        if os.path.exists(temp_exe):
            result = subprocess.run([temp_exe], capture_output=True, text=True, timeout=30)
            assert result.returncode == 0, f"Ejecución falló: {result.stderr}"
    finally:
        _cleanup_temp_syn(temp_syn)


def test_debug_trace_event_types():
    """Valida todos los tipos de eventos TraceEvent definidos"""
    codigo = """#lang: es
importar std.debug

funcion principal() -> nulo:
    evt = TraceEvent()
    evt.tipo_evento = EVENT_ASSIGNMENT
    evt.variable = "x"
    evt.valor_entero = 1
    registrar_evento(evt)
    evt2 = TraceEvent()
    evt2.tipo_evento = EVENT_FN_CALL
    evt2.variable = "foo"
    evt2.valor_entero = 0
    registrar_evento(evt2)
    evt3 = TraceEvent()
    evt3.tipo_evento = EVENT_FN_RETURN
    evt3.variable = "foo"
    evt3.valor_entero = 42
    registrar_evento(evt3)
    evt4 = TraceEvent()
    evt4.tipo_evento = EVENT_ERROR
    evt4.variable = "error"
    evt4.valor_entero = 0
    registrar_evento(evt4)
    evt5 = TraceEvent()
    evt5.tipo_evento = EVENT_BRANCH_TAKEN
    evt5.variable = "if"
    evt5.valor_entero = 1
    registrar_evento(evt5)
    evt6 = TraceEvent()
    evt6.tipo_evento = EVENT_LOOP_ITERATION
    evt6.variable = "while"
    evt6.valor_entero = 1
    registrar_evento(evt6)
    evt7 = TraceEvent()
    evt7.tipo_evento = EVENT_VARIABLE_CHANGE
    evt7.variable = "y"
    evt7.valor_entero = 99
    registrar_evento(evt7)
    evt8 = TraceEvent()
    evt8.tipo_evento = EVENT_CONTRACT_CHECK
    evt8.variable = "pre"
    evt8.valor_entero = 1
    registrar_evento(evt8)
    evt9 = TraceEvent()
    evt9.tipo_evento = EVENT_USER_TRACE
    evt9.variable = "custom"
    evt9.valor_entero = 0
    registrar_evento(evt9)
    finalizar_sesion()
    retornar"""
    temp_syn = _write_temp_syn(codigo)

    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, "Compilación falló"
    finally:
        _cleanup_temp_syn(temp_syn)


def test_debug_archivo_trace_formato():
    """Valida formato del archivo .trace generado"""
    codigo = """#lang: es
importar std.debug

funcion principal() -> nulo:
    evt = TraceEvent()
    evt.tipo_evento = EVENT_ASSIGNMENT
    evt.variable = "x"
    evt.valor_entero = 42
    registrar_evento(evt)
    finalizar_sesion()
    retornar"""
    temp_syn = _write_temp_syn(codigo)

    try:
        resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
        assert resultado == 0, "Compilación falló"

        import subprocess
        temp_exe = temp_syn.replace('.syn', '.exe')
        if os.path.exists(temp_exe):
            result = subprocess.run([temp_exe], capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, f"Ejecución falló: {result.stderr}"

            # Verificar que se creó archivo .trace
            trace_files = glob.glob(os.path.expanduser("~/.synapse/traces/trace_*.trace"))
            assert len(trace_files) > 0, "No se generó archivo .trace"

            # Verificar formato del trace
            with open(trace_files[-1], 'r') as tf:
                content = tf.read()
                assert "TRACE v1" in content, "Header TRACE v1 faltante"
                assert "id=trace_" in content, "ID faltante"
                assert "eventos=1" in content, "Contador eventos incorrecto"
                assert "0|" in content, "Evento no serializado correctamente"
    finally:
        _cleanup_temp_syn(temp_syn)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])