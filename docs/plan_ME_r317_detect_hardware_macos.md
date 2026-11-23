# Plan de Micro-Entregable r317_detect_hardware_macos

## Objetivo

Tercera vuelta sobre `Release Matrix` (run `45183357177`): Linux x64/ARM64 y
Windows ya llegan al paso de firma, pero la fila macOS sigue cayendo en el
bootstrap:

```
runtime/core/detect_hardware.c:12:10: fatal error: sys/sysinfo.h: No such file or directory
[ME-R2][ERROR] Fallo al compilar runtime desde fuente: .../runtime/core/detect_hardware.c
[build][ERROR] rc=1: ['python', 'main.py', 'nucleo/principal.syn']
```

`sys/sysinfo.h` y `/proc/*` son de Linux. Tanto `runtime/core/detect_hardware.c`
como `nucleo/detect_hardware.c` (el runtime legacy también se compila en el
bootstrap) los usan sin guarda de plataforma.

## Requisito 1 — el runtime detecta hardware sin cabeceras Linux-only

requisito: Manual 9 §5.7
texto: "El módulo `std/os.syn` proporciona funciones de detección de hardware y sistema utilitarias, utilizadas por el instalador de OpenSyn (ver §5.1). Estas funciones están implementadas mediante FFI a llamadas del sistema operativo."
implementacion: `runtime/core/detect_hardware.c` incluye `<sys/sysinfo.h>` sólo bajo `__linux__`; `_syn_memoria_libre` gana rama `#elif defined(__linux__)` (sysinfo) y `#else` con `sysconf(_SC_AVPHYS_PAGES) * sysconf(_SC_PAGE_SIZE)` para macOS/POSIX, devolviendo 0 si el kernel no lo soporta.
oraculo: tests/auditoria/test_r317_detect_hardware_macos.py

## Requisito 2 — el bootstrap compila en macOS

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: `nucleo/detect_hardware.c` incluye `<sys/sysinfo.h>` sólo bajo `__linux__`; el perfil de hardware usa `#elif defined(__linux__)` (sysinfo + `/proc/mtrr`, `/proc/iomem`, `nvidia-smi`) y un `#else` POSIX con `sysconf(_SC_PHYS_PAGES)`/`_SC_NPROCESSORS_CONF`, sin `/proc`.
oraculo: tests/auditoria/test_r317_detect_hardware_macos.py

## Mapa de alineación

Se agregan `runtime/core/detect_hardware.c` y `nucleo/detect_hardware.c` con
`["Manual 9 §5.7", "Manual 9 §6.2"]` (caían al mapa legacy y el gate reportaba
`Manual 5 §` / `Manual 2 §`, secciones inexistentes).

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r317_detect_hardware_macos.py` | 3 passed |
| `build.py --skip-test` (Windows) + `S2==S3` | OK, sha `9382d8d9c234` |
| `alineacion.py --verificar --me r317_detect_hardware_macos` | OK (`a7bc8befac4de0b0`) |
| `contrastar.py --plan docs/plan_ME_r317_detect_hardware_macos.md` | PASS (2/2) |
| CI `Release Matrix` en macOS tras el push | pendiente de corrida |
