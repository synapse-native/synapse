# Módulos registrados en D-9 (regla 13)
# Formato: - ruta/al/modulo
#
# Fuente de verdad del verificador auditoria/verificar_alineacion.py.
# Antes hard-codeado en el script; ahora vive aqui. Todo modulo de produccion
# .syn/.py/.c de mas de 1200 lineas debe estar listado aqui (con resolucion
# asignada en D-9), o el verificador lo reporta como brecha de deuda.
#
# Cobertura completa desde el endurecimiento del sistema de control: el
# escaneo incluye nucleo/, opensyn/, syquex/, runtime/core/ y
# compilador/generator/ (antes solo nucleo/*.syn + generator/*.py).

- nucleo/lexer.syn
- nucleo/analizador_semantico.syn
- nucleo/lsp_v3.syn
- syquex/parser.syn
- compilador/generator/generator.py
- compilador/generator/emit_expressions.py
- synapse_rt.c
- opensyn/principal.syn
- nucleo/principal.syn
- runtime/core/cluster.c
- runtime/core/debug.c
- runtime/core/modelo.c
- runtime/core/ollama.c
- runtime/core/tui.c
