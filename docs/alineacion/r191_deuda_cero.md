# Expediente de alineación r191_deuda_cero

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: #
 94bbe469d3b2788a

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## compilador/diagnostics.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/diagnostics.py:11
  oraculo: tests/auditoria/test_oraculos_r191.py

## compilador/parser_expressions.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/parser_expressions.py:317
  oraculo: tests/auditoria/test_oraculos_r191.py

## compilador/semantic_checker.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/semantic_checker.py:405
  oraculo: tests/auditoria/test_oraculos_r191.py
