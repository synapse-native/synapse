# Plan de Micro-Entregable r323_darwin_bootstrap_selfhost

## Objetivo

r322 hizo que `pipeline.py` use un GCC real en macOS y el workflow exporte
`SYNAPSE_GCC_PATH`, pero el compilador autohospedado (stage1, generado por
`nucleo/principal.syn`) seguía invocando el literal `gcc` al compilar
`principal.syn` a stage2. En macOS `gcc` es un shim de clang, que rechaza las
funciones anidadas (extensión GNU) del C emitido, así que el bootstrap moría en
`synapse_unity.c` con `function definition is not allowed here`. Este ME cierra
esa brecha: stage1 resuelve `SYNAPSE_GCC_PATH` (y `SYNAPSE_GCC` como respaldo)
y lo cita en POSIX; además usa `-dead_strip` donde ld64 no conoce
`--gc-sections`. El mismo cambio se aplica a `nucleo/generador/compilar.syn`.

## Requisito 1 — el compilador autohospedado honra SYNAPSE_GCC_PATH

requisito: Manual 9 §6.2
texto: "La verificación del bootstrap (diff 0 bytes)."
implementacion: `nucleo/principal.syn` resuelve `_gcc_env` con prioridad `SYNAPSE_GCC_PATH` -> `SYNAPSE_GCC` en Windows y POSIX; en POSIX cita `_gcc_exe` en `_gcc_cmd` y usa `-dead_strip` si `__APPLE__`; el probe de sanitizadores y el comando final usan `_gcc_cmd`.
oraculo: tests/auditoria/test_r322_darwin_gcc.py

## Requisito 2 — compilar.syn usa el mismo GCC real

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: `nucleo/generador/compilar.syn` resuelve `_gcc_cmd` desde `SYNAPSE_GCC_PATH`/`SYNAPSE_GCC` en POSIX, usa `_gc_flag` (`-Wl,--gc-sections` o `-Wl,-dead_strip`) y cita la ruta en el comando final.
oraculo: tests/auditoria/test_r322_darwin_gcc.py

## Evidencia

| check | resultado |
|---|---|
| `build.py --skip-test` (Windows) + `S2==S3` | OK, sha `8e9e60f83c39` |
| `auditoria/verificar_alineacion.py` | 0 brechas |
| CI `Release Matrix` macOS tras el push | (se completa tras ejecutar) |
