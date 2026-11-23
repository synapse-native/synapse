# Plan de Micro-Entregable r318_detect_hardware_macos_mem

## Objetivo

Cuarta vuelta sobre `Release Matrix`. Tras r317, la fila macOS pasó el
`#include <sys/sysinfo.h>` y murió un paso más adelante (run `45185835609`,
job `137731068175`):

```
runtime/core/detect_hardware.c:61:26: error: '_SC_AVPHYS_PAGES' undeclared (first use in this function)
[ME-R2][ERROR] Fallo al compilar runtime desde fuente
[build][ERROR] rc=1
```

`_SC_AVPHYS_PAGES` es una extensión de `sysconf` **solo de Linux**; macOS no la
declara. Linux x64/ARM64 y Windows ya solo fallan en la firma Ed25519
(secreto ausente, H-R276-2).

## Requisito 1 — macOS obtiene la memoria disponible sin constantes Linux-only

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: en `runtime/core/detect_hardware.c`, `_syn_memoria_libre` gana rama `#elif defined(__APPLE__)` que consulta el VM del kernel con `host_page_size` + `host_statistics64` (`mach/mach.h`) y devuelve `(free + inactive + speculative) * page_size`; el `#else` POSIX restante devuelve 0 (no se fabrica el dato) y la cabecera `mach/mach.h` se incluye solo bajo `__APPLE__`.
oraculo: tests/auditoria/test_r318_detect_hardware_macos_mem.py

## Requisito 2 — detección de hardware por FFI intacta

requisito: Manual 9 §5.7
texto: "El módulo `std/os.syn` proporciona funciones de detección de hardware y sistema utilitarias, utilizadas por el instalador de OpenSyn (ver §5.1). Estas funciones están implementadas mediante FFI a llamadas del sistema operativo."
implementacion: `mach_host_self`/`host_statistics64` son llamadas al SO vía FFI, igual que `GlobalMemoryStatusEx` (Windows) y `sysinfo` (Linux); las ramas Windows y Linux quedan byte-idénticas.
oraculo: tests/auditoria/test_r318_detect_hardware_macos_mem.py

## Corrección de oráculo r317

`tests/auditoria/test_r317_detect_hardware_macos.py` afirmaba que macOS expone
`_SC_AVPHYS_PAGES`; la CI demostró lo contrario. Se sustituye esa aserción por
"existe rama macOS" (la implementación concreta la cubre r318). Queda declarado
en `docs/reportes/R318.md` y en la bitácora para el Arquitecto.

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r317_... test_r318_...` | 6 passed |
| `build.py --skip-test` (Windows) + `S2==S3` | OK, sha `9382d8d9c234` |
| `alineacion.py --verificar --me r318_detect_hardware_macos_mem` | OK (`6e868b39d236f3cf`) |
| `contrastar.py --plan docs/plan_ME_r318_detect_hardware_macos_mem.md` | PASS |
| CI `Release Matrix` macOS tras el push | pendiente de corrida |
