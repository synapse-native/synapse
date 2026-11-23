# Expediente de alineación r313_link_flags

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: e9008a4c3d4a259e

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## pipeline.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:182
  oraculo: tests/auditoria/test_r313_link_flags.py

## runtime/core/concurrency.c
- manual: 5
  seccion: 2.1
  cita: "Pila propia (tamaño configurable, por defecto 64 KB)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/concurrency.c:2
  oraculo: tests/auditoria/test_r313_link_flags.py

- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/concurrency.c:1
  oraculo: tests/auditoria/test_r313_link_flags.py
