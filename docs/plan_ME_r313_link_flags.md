# Plan de Micro-Entregable r313_link_flags

## Objetivo

El run `45170587854` (push `f74e994`) avanza en las cuatro filas pero el link
sigue roto:

- **ubuntu-latest / ubuntu-24.04-arm**: `/usr/bin/x86_64-linux-gnu-ld.bfd:
  unrecognized option '--stack'`. `pipeline.py` añadía `-Wl,--stack,8388608`
  en todo POSIX; esa opción solo existe en el ld de MinGW. Está en tres lugares
  (`platform_flags` del camino normal, `flags_compilacion` de caché y
  `_link_object`).
- **macos-latest**: `<sys/sysctl.h>` incluido bajo `_XOPEN_SOURCE` arrastra
  `sys/ucred.h`/`sys/proc.h`, que usan `u_int`/`u_char` y no compilan en el
  perfil XSI. La solución del r312 (sysctl) es incompatible con la exigencia de
  `ucontext.h`.

## Requisito 1 — flags de link por plataforma

requisito: Manual 9 §6.1
texto: "□ **Compilación sin errores**: todos los targets (Windows, Linux, macOS, WASM) compilan sin errores ni warnings."
implementacion: `pipeline.py` aplica `-Wl,--stack,8388608` (y `-Wl,--gc-sections`) solo cuando `sys.platform == "win32"`, en los tres sitios donde se armaban flags (camino normal, clave de caché de objetos y `_link_object`); en ELF/Mach-O queda solo lo portable.
oraculo: tests/auditoria/test_r313_link_flags.py

## Requisito 2 — CPUs de Darwin sin sysctl

requisito: Manual 5 §2.1
texto: "Pila propia (tamaño configurable, por defecto 64 KB)."
implementacion: `runtime/core/concurrency.c` elimina `<sys/sysctl.h>` y obtiene los núcleos del scheduler M:N con `_syn_cpu_nucleos()` de `runtime/core/detect_hardware.h` (TU sin feature-test macros), manteniendo `_XOPEN_SOURCE 700` por ucontext.
oraculo: tests/auditoria/test_r313_link_flags.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r313_link_flags.py` | 2 passed |
| `build.py --skip-test` (Windows, hash sin cambios) | rc=0, S2==S3 `1b30a488e480` |
| CI matriz tras el push | pendiente de corrida |
| `contrastar.py --plan docs/plan_ME_r313_link_flags.md` | PASS (2/2) |
