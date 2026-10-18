# Expediente de alineación r190_debug_cli

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 63f5b931daef652e

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## cli.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: cli.py:1187
  oraculo: tests/auditoria/test_oraculos_r190.py
