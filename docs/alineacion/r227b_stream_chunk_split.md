# Expediente de alineacion r227b_stream_chunk_split

base: HEAD
cambio_hash: 8d697386e8e7dfef

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## runtime/core/ollama.c
- manual: 7
  seccion: 2.2
  cita: "Soporta timeouts, reintentos y manejo de errores."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/ollama.c:1435
  oraculo: tests/auditoria/test_oraculos_r227b_stream_chunk_split.py
  ejecucion: pytest

- manual: 7
  seccion: 2.2
  cita: "Esperar la respuesta (con timeout)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/ollama.c:1435
  oraculo: tests/auditoria/test_oraculos_r227b_stream_chunk_split.py
  ejecucion: pytest
