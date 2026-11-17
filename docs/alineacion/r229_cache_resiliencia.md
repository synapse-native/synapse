# Expediente de alineación r229_cache_resiliencia

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 72f57ee447e56c67

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## pipeline.py
- manual: 9
  seccion: 1
  cita: "> **Nota (ubicación de la caché incremental):** Toda caché del compilador —objetos del runtime (`synapse_rt.c`, `runtime/core/*`, `axon/tweetnacl.c`, `vendor/sqlite3/sqlite3.c`, módulos cuánticos/IA) y código de usuario compilado incrementalmente— se almacena **bajo `~/.synapse/cache/`** (coherente con Manual 1 §4: `cache.syn` = "Sistema de caché incremental SHA‑256")."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:179
  oraculo: tests/unit/test_cache_fallback.py
  ejecucion: pytest

- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:182
  oraculo: tests/unit/test_cache_fallback.py
  ejecucion: pytest

