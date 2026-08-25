import os
import sys
import tempfile
import pytest

pytestmark = pytest.mark.integration

# Usar directorio del script + tempdir para compatibilidad cross-platform
_base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(_base_dir, '..'))
sys.path.insert(0, '.')
from pipeline import ejecutar_compilador

codigo = """#lang: es
importar std.debug

funcion principal() -> nulo:
    evt = TraceEvent()
    evt.tag = EVENT_ASSIGNMENT
    evt.fn_nombre = "principal"
    evt.archivo = "test.syn"
    evt.linea = 1
    evt.variable = "x"
    evt.valor_entero = 42
    registrar_evento(evt)
    retornar"""

temp_dir = os.path.join(tempfile.gettempdir(), '_synapse_test_debug')
temp_syn = os.path.join(temp_dir, 'test_debug_manual.syn')
os.makedirs(temp_dir, exist_ok=True)

with open(temp_syn, 'w') as f:
    f.write(codigo)

print('Archivo:', temp_syn)
print('Existe:', os.path.exists(temp_syn))

resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
print('Resultado:', resultado)