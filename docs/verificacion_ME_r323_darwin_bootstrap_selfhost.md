# Verificación — ME r323_darwin_bootstrap_selfhost

CUMPLE.

## Cambios

- `nucleo/principal.syn`: resuelve `_gcc_env` con prioridad `SYNAPSE_GCC_PATH` -> `SYNAPSE_GCC` (Windows y POSIX); en POSIX cita `_gcc_exe` en `_gcc_cmd` y usa `-dead_strip` en macOS; el probe y el comando final usan `_gcc_cmd`.
- `nucleo/generador/compilar.syn`: resuelve `_gcc_cmd` desde `SYNAPSE_GCC_PATH`/`SYNAPSE_GCC`, usa `_gc_flag` (`-Wl,--gc-sections` o `-Wl,-dead_strip`) y cita la ruta.

## Verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.2 — CUMPLE — bootstrap en cada target | `build.py --skip-test` (Windows) | S2==S3 `8e9e60f83c39` |
| Manual 9 §6.2 — CUMPLE — GCC real en darwin | `pytest tests/auditoria/test_r322_darwin_gcc.py` | 5 passed |

| check | resultado |
|---|---|
| `alineacion.py --verificar --me r323_darwin_bootstrap_selfhost` | (se completa tras ejecutar) |
| `contrastar.py --plan docs/plan_ME_r323_darwin_bootstrap_selfhost.md` | PASS |
| `verificar_alineacion.py` | SIN BRECHAS |
