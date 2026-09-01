# Plan ME — Caché incremental de objetos del runtime (pipeline.py)

## Requisito 1: compilación incremental del runtime

requisito: Manual 1 §4 (Estructura del Repositorio / Monorepo)
texto: "cache.syn  # Sistema de caché incremental SHA-256" — el ecosistema define
  caché incremental SHA-256 como mecanismo estándar de construcción; y Manual 1 §6
  "Regla de hierro: Ninguna característica nueva puede romper el bootstrap (etapas
  0→1→2→3 con diff binario 0)".
implementacion: Nuevo helper `_compilar_objeto_cacheado(compiler, opt_flags,
  base_flags, src_rel, nombre, dir_obj, extra_flags)` en pipeline.py. Calcula
  `hash = SHA-256(fuente) | compilador | opt_flags | base_flags | extra_flags` y
  guarda un sidecar `<obj>.sha`. Recompila el `.o` SOLO si el `.o` o el sidecar no
  existen o el hash cambió. Cableado en `_compilar_runtime_objetos`,
  `_compilar_quantum_objetos` y el bloque IA de `ejecutar_compilador`. El binario
  enlazado es idéntico al recién compilado (la clave incluye flags), por lo que no
  rompe el bootstrap (Regla de hierro). ME-R2 se respeta: sigue compilando el
  runtime modular DESDE FUENTE; solo se omite recompilar cuando la fuente y los
  flags son idénticos a la última compilación.
oraculo: tests/unit/test_aislamiento_gcc.py (verifica que la invocación a gcc sigue
  usando el toolchain interno, no el PATH) + ejecución de `tests/unit` (328 passed,
  2 RED TDD esperados en r3_param_adt).

## Requisito 2: no degradar el aislamiento del toolchain

requisito: Manual 9 §9 (Instalación limpia / toolchain interno)
texto: "Offline-first ... paquetes y modelos se almacenan en caché local" + ME-R2
  (runtime modular compilado desde fuente, sin depender de .o precompilados).
implementacion: El helper conserva la resolución del toolchain interno
  (`_resolver_toolchain_gcc`); cuando una fuente del runtime falta, aún invoca gcc
  con la ruta interna (para que el test de aislamiento lo observe) y falla igual
  que antes. La caché solo se aplica cuando la fuente existe y es idéntica.
oraculo: tests/unit/test_aislamiento_gcc.py
