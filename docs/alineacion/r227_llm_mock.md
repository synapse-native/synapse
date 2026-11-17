# Expediente de alineación r227_llm_mock

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 562bf8f4ab0371e0

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## runtime/core/ollama.c
- manual: 7
  seccion: 2.2
  cita: "Enviar un POST a `http://127.0.0.1:8088/completion` con el JSON."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/ollama.c:630
  oraculo: tests/auditoria/test_oraculos_r227_llm_mock.py
  ejecucion: pytest

- manual: 7
  seccion: 2.2
  cita: "Extraer el campo `content` o `completion` de la respuesta JSON."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/ollama.c:669
  oraculo: tests/auditoria/test_oraculos_r227_llm_mock.py
  ejecucion: pytest
