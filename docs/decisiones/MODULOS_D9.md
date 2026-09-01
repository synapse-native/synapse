# Módulos registrados en D-9 (regla 13)
# Formato: - ruta/al/modulo.syn
#
# Fuente de verdad del verificador auditoria/verificar_alineacion.py.
# Antes hard-codeado en el script; ahora vive aqui. Todo modulo de produccion
# .syn/.py de mas de 1200 lineas debe estar listado aqui (con resolucion
# asignada en D-9), o el verificador lo reporta como brecha de deuda.

- nucleo/lexer.syn
- nucleo/analizador_semantico.syn
- compilador/generator/generator.py
- synapse_rt.c
