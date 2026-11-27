# Plan de Micro-Entregable r316_link_flags_posix

## Objetivo

Segunda vuelta sobre `Release Matrix` (run `45179123189`): el bootstrap ya
compila el C en Linux, pero el **enlace** falla porque el comando `gcc` del
bootstrap nativo incluye opciones exclusivas de MinGW en una sola línea:

```
/usr/bin/x86_64-linux-gnu-ld.bfd: unrecognized option '--no-insert-timestamp'
[Synapse] ERROR: GCC fallo con codigo 256
[build][ERROR] rc=5: ['./synapse_stage1.exe', 'nucleo/principal.syn']
```

`nucleo/principal.syn` emite `-Wl,--no-insert-timestamp -Wl,--stack,8388608`
y `-lws2_32` fijos; `nucleo/generador/compilar.syn` y
`librerias/compiler/generator.c` tienen el mismo patrón, y `cli.py` enlaza las
variantes con sanitizadores con `-lws2_32` sin condición.

## Requisito 1 — el enlace del bootstrap usa sólo flags de la plataforma

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: en `nucleo/principal.syn`, `--no-insert-timestamp`/`--stack` y `-lws2_32` se arman en las variables `_win_ld`/`_win_libs` bajo `#ifdef _WIN32` y el `snprintf` del enlace las interpola; en win32 el comando queda byte-idéntico al anterior.
oraculo: tests/auditoria/test_r316_link_flags_posix.py

## Requisito 2 — Axon y el compilador de librerías también

requisito: Manual 9 §6.2
texto: "La verificación del bootstrap (diff 0 bytes)."
implementacion: `nucleo/generador/compilar.syn` arma sus flags con rama `#ifdef _WIN32`; `librerias/compiler/generator.c` bifurca el `snprintf` con `#ifdef _WIN32`/`#else`; `cli.py` agrega `-lws2_32` sólo si `sys.platform == "win32"`.
oraculo: tests/auditoria/test_r316_link_flags_posix.py

## Mapa de alineación

Se agregan entradas explícitas para `nucleo/generador/compilar.syn`,
`librerias/compiler/generator.c` y `cli.py` (antes caían al mapa legacy y el
gate reportaba `Manual 1 §`/`Manual 2 §`, secciones inexistentes).

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r316_link_flags_posix.py` | 3 passed |
| `build.py --skip-test` (Windows) + `S2==S3` | OK, sha `9382d8d9c234` |
| `alineacion.py --verificar --me r316_link_flags_posix` | OK (`4d6c9a16972af6fc`) |
| `contrastar.py --plan docs/plan_ME_r316_link_flags_posix.md` | PASS (2/2) |
| CI `Release Matrix` en Linux x64/ARM64 y macOS tras el push | pendiente de corrida |
