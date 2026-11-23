# Verificación — ME r317_detect_hardware_macos

CUMPLE.

## Requisitos y verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §5.7 — CUMPLE — detección de hardware por FFI | `pytest tests/auditoria/test_r317_detect_hardware_macos.py` | 3 passed |
| Manual 9 §6.2 — CUMPLE — compila en cada target | idem | 3 passed |

## Causa y cambio

Run `45183357177`, job `release_matrix (macos-latest, darwin_arm64)`:

```
runtime/core/detect_hardware.c:12:10: fatal error: sys/sysinfo.h: No such file or directory
[ME-R2][ERROR] Fallo al compilar runtime desde fuente: .../core/detect_hardware.c
```

- `runtime/core/detect_hardware.c`: `<sys/sysinfo.h>` sólo bajo `__linux__`;
  `_syn_memoria_libre` conserva la rama Linux (`struct sysinfo`) y añade `#else`
  con `sysconf(_SC_AVPHYS_PAGES) * sysconf(_SC_PAGE_SIZE)` (macOS), 0 si el
  kernel no lo expone.
- `nucleo/detect_hardware.c`: mismo guard de cabecera; el perfil usa
  `#elif defined(__linux__)` para sysinfo, `/proc/mtrr`, `/proc/iomem` y
  `nvidia-smi`, y un `#else` POSIX con `sysconf(_SC_PHYS_PAGES)` y
  `_SC_NPROCESSORS_CONF` (sin `/proc`).

## Otros checks

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r317_detect_hardware_macos.py` | 3 passed |
| `build.py --skip-test` (Windows) | S2==S3, sha `9382d8d9c234` |
| `alineacion.py --verificar --me r317_detect_hardware_macos` | OK, evidencia `a7bc8befac4de0b0` |
| `contrastar.py --plan docs/plan_ME_r317_detect_hardware_macos.md` | PASS (2/2) |

## Limitación declarada

La compilación en macOS la valida la matriz de CI tras el push. Localmente sólo
se verificó que Windows sigue compilando y que las cabeceras Linux-only quedan
guardadas.
