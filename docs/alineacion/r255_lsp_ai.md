# Expediente de alineación r255_lsp_ai

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: a8cbf72acbcb1bfc

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/lsp_v3.syn
- manual: 8
  seccion: 2.3
  cita: "Synapse: Verificar estado de IA local → `synapse/aiStatus`"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:905
  oraculo: tests/integration/test_ai_commands_opensyn.py


## nucleo/lsp_v3.syn
- manual: 8
  seccion: 1.1
  cita: "El LSP es nativo, sin telemetría y sin dependencias externas (excepto el binario synapse.exe para compilar y analizar código)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:2
  oraculo: tests/integration/test_ai_commands_opensyn.py
