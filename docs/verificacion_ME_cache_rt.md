# Verificación ME — Caché incremental de objetos del runtime (pipeline.py)

## Requisito 1: compilación incremental del runtime

- CUMPLE — `pipeline.py:127` `_compilar_objeto_cacheado` implementa caché SHA-256 por
  fuente+flags; recompila solo si cambia el hash. Cita: `pipeline.py:131-139`
  (`cumple Manual 1 §4 ... / Manual 1 §6 Regla de hierro`).
- Evidencia: `main.py _trivial.syn` frío 93.8s → cálido 1.8s. `test_debug.py` 6
  passed en 9.9s; `test_ast_abi.py` 4 passed en 2.49s (antes timeout 50s).
- Bootstrap preservado: el `.o` cacheado es byte-idéntico al recién compilado porque
  la clave incluye `opt_flags`+`base_flags`; builds release/debug/asan son entradas
  de caché separadas.

## Requisito 2: no degradar el aislamiento del toolchain

- CUMPLE — `pipeline.py:140-151` el helper invoca gcc con la ruta interna aunque la
  fuente falte (observado por el mock del test de aislamiento).
- Evidencia: `tests/unit/test_aislamiento_gcc.py` 4 passed.

## Gate de alineación

- `auditoria/verificar_alineacion.py`: 0 brechas.
- `tests/unit` (salvo RED TDD esperado r3_param_adt): 328 passed.
