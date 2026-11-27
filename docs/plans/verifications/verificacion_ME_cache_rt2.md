# Verificación ME — Caché de runtime en ubicación sancionada por el manual

## Requisito 1: la caché incremental vive en `~/.synapse/cache/`, no en build/

- CUMPLE — `pipeline.py:144-145` `dir_obj = os.path.join(_cache_dir(), "runtime_obj")`
  (`_cache_dir()` = `~/.synapse/cache/`). Ya no usa `SYNAPSE_BIN/build/obj/`.
  Cita: `pipeline.py:133-141` (`cumple Manual 1 §4 ... y Manual 9 §9 ...`).
- Evidencia: tras commit, el hook "Limpiando artefactos de build" ya NO borra la
  caché de runtime (está fuera del repo). Verificación: compilar dos veces un .syn
  trivial → 2ª corrida cálida (~1.8s) aunque hubo commit intermedio.

## Requisito 2: caché incremental SHA-256 (mecanismo estándar)

- CUMPLE — `pipeline.py:149` la clave es `SHA-256(fuente)|compilador|opt_flags|
  base_flags|extra_flags`; sidecar `<obj>.sha`. Recompila solo si cambia.
- Bootstrap preservado (Manual 1 §6): el `.o` cacheado es byte-idéntico al nuevo
  porque la clave incluye flags; builds release/debug/asan son entradas separadas.

## Gate de alineación

- `auditoria/verificar_alineacion.py`: 0 brechas.
- `tests/unit/test_aislamiento_gcc.py`: 4 passed (aislamiento de toolchain intacto).
