# Plan ME r229 - Resiliencia de caché sin caché persistente fuera de home

## Contexto

En entornos con permisos restringidos (sandboxes de agentes, runners CI sin
elevación o usuarios sin permisos sobre `USERPROFILE`), la invocación del
compilador falla con:
`PermissionError: [WinError 5] Acceso denegado: 'C:\Users\marce\.synapse\cache'`
al ejecutar `os.makedirs(dir_obj, exist_ok=True)` en `pipeline.py`.

El fallo no se corrige creando una caché persistente en el workspace o en el
directorio temporal: el Manual 9 §1 exige que toda caché del compilador viva
bajo `~/.synapse/cache/` y declara efímeros los directorios de build. La
solución es degradar sin caché persistente: si el home no es escribible, se
compila con objetos efímeros en `build/obj/runtime_ephemeral` y un memo en
proceso, sin escribir una caché paralela.

## Requisitos (MTS)

requisito: Manual 9 §1
texto: "> **Nota (ubicación de la caché incremental):** Toda caché del compilador —objetos del runtime (`synapse_rt.c`, `runtime/core/*`, `axon/tweetnacl.c`, `vendor/sqlite3/sqlite3.c`, módulos cuánticos/IA) y código de usuario compilado incrementalmente— se almacena **bajo `~/.synapse/cache/`** (coherente con Manual 1 §4: `cache.syn` = \"Sistema de caché incremental SHA‑256\")."
implementacion: `pipeline.py` mantiene `_cache_dir()` apuntando a `~/.synapse/cache` como única caché persistente. `_cache_disponible()` prueba escritura real; si falla, desactiva la caché persistente, emite un aviso y `_compilar_objeto_cacheado()` compila en `build/obj/runtime_ephemeral` (artefacto efímero) con memo en proceso. No se crea `.synapse_cache` ni caché persistente en workspace/temp, porque el Manual 9 §1 declara efímeros los directorios de build y prohíbe usarlos para cachés persistentes.
oraculo: tests/unit/test_cache_fallback.py

requisito: Manual 1 §3.1
texto: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
implementacion: el pipeline compartido conserva la compilación y el enlace aun cuando la caché persistente no esté disponible; la degradación no altera el código generado ni el backend GCC/Clang.
oraculo: tests/unit/test_cache_fallback.py

## Archivos

- `pipeline.py` - caché persistente solo en home; degradación a objetos efímeros y memo en proceso.
- `tests/unit/test_cache_fallback.py` - oráculo que valida compilación sin permisos de caché y ausencia de caché persistente alternativa.
- `docs/alineacion/r229_cache_resiliencia.md` - expediente de trazabilidad MTS.
- `docs/verificacion_ME_r229_cache_resiliencia.md` - reporte de verificación.

