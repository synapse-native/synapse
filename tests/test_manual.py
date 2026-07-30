import os
os.chdir('D:\\proyecto_synapse')
import sys
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

temp_syn = 'D:\\proyecto_synapse\\_test_debug_temp\\test_debug_manual.syn'
os.makedirs(os.path.dirname(temp_syn), exist_ok=True)

with open(temp_syn, 'w') as f:
    f.write(codigo)

print('Archivo:', temp_syn)
print('Existe:', os.path.exists(temp_syn))

resultado = ejecutar_compilador(temp_syn, mostrar_tokens=False)
print('Resultado:', resultado)