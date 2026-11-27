# Verificación ME r229_cache_resiliencia

## Marcas por requisito

- Manual 9 §1 R1: CUMPLE. La única caché persistente es `~/.synapse/cache/`; si no es escribible, no se crea una caché persistente en workspace/temp y se compila con objetos efímeros en `build/obj/runtime_ephemeral`. Evidencia `pipeline.py:179`; oráculo `tests/unit/test_cache_fallback.py`.
- Manual 1 §3.1 R1: CUMPLE. El pipeline compartido conserva compilación y enlace aun sin caché persistente. Evidencia `pipeline.py:182`; oráculo `tests/unit/test_cache_fallback.py`.

## Oráculo

`tests/unit/test_cache_fallback.py` — 3/3 passed. Evidencia de alineación:
`auditoria/evidencia/72f57ee447e56c67.json`.

- R1: con `~/.synapse/cache` no escribible, `_compilar_objeto_cacheado()`
  compila en `build/obj/runtime_ephemeral`, avisa y no crea `.synapse_cache`
  ni caché persistente alternativa.
- R2: con caché escribible, conserva el objeto en
  `~/.synapse/cache/runtime_obj/mini.o` y su sidecar `.sha`.
- R3: `_cache_ensure_dirs()` no lanza excepción y marca la caché como no
  disponible.

## Evidencia

- `3 passed` en `tests/unit/test_cache_fallback.py`.
- `4 passed` en `tests/integration/test_cache_audit.py` (regresión de caché
  incremental, HIT/STALE/determinismo y lock de Axon).
- `python auditoria/alineacion.py --verificar --me r229_cache_resiliencia
  --archivos pipeline.py`: PASS, evidencia `e368a00d663e8cee`.
- `git add pipeline.py` previo al sello para que `cambio_hash` corresponda al
  blob del índice (lección R188/d948cab).

## Límites

- No se modificó `nucleo/cache.syn`: el fallo reproducido está en el pipeline
  Python y el caché nativo no es invocado por la ruta de compilación afectada.
  La caché nativa sigue usando `~/.synapse/cache/` y no crea una caché
  persistente alternativa.
- La degradación efímera prioriza correctitud sobre rendimiento: en un home no
  escribible el runtime se recompila una vez por proceso; el memo evita
  recompilar dentro de la misma ejecución.
