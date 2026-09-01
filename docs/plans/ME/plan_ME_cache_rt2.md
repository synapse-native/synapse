# Plan ME — Caché de runtime en ubicación sancionada por el manual

## Requisito 1: la caché incremental vive en `~/.synapse/cache/`, no en build/

requisito: Manual 9 §9 (Offline-first)
texto: "Los paquetes y modelos se descargan una vez y se almacenan en caché local
  (`~/.synapse/cache/`, `~/.opensyn/models/`)."
implementacion: En `pipeline.py`, `_compilar_objeto_cacheado` usa como directorio
  por defecto `os.path.join(_cache_dir(), "runtime_obj")` donde `_cache_dir()`
  retorna `~/.synapse/cache/`. Antes usaba `SYNAPSE_BIN/build/obj/`, que es un
  directorio de build del repositorio (CLASE I en .gitignore) y es eliminado por
  el hook "Limpiando artefactos de build" en cada commit, invalidando la caché.
  Moverla fuera del repo la hace durable entre commits y sesiones, cumpliendo
  Manual 9 §9.
oraculo: tests/unit/test_aislamiento_gcc.py

## Requisito 2: caché incremental SHA-256 (mecanismo estándar)

requisito: Manual 1 §4 (Estructura del Repositorio)
texto: "cache.syn  # Sistema de caché incremental SHA-256"
implementacion: El helper conserva la clave SHA-256 (hash de la fuente + compilador
  + flags) y el sidecar `<obj>.sha`; recompila solo si cambia. La ubicación
  `~/.synapse/cache/runtime_obj/` es coherente con `cache.syn`. El binario
  enlazado es idéntico al recién compilado (clave incluye flags) → no rompe el
  bootstrap (Manual 1 §6, Regla de hierro).
oraculo: tests/unit/test_aislamiento_gcc.py
