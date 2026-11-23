# Verificación — ME r318_detect_hardware_macos_mem

CUMPLE.

## Causa y cambio

Run `45185835609`, job `137731068175` (macos-latest, darwin_arm64):

```
runtime/core/detect_hardware.c:61:26: error: '_SC_AVPHYS_PAGES' undeclared (first use in this function)
[ME-R2][ERROR] Fallo al compilar runtime desde fuente
```

`_SC_AVPHYS_PAGES` sólo existe en Linux. En macOS la memoria disponible se pide
al VM del kernel: `host_page_size` + `host_statistics64(HOST_VMSTATS64)` y se
suma `free + inactive + speculative` por el tamaño de página. `mach/mach.h` se
incluye bajo `__APPLE__`; las ramas Windows y Linux quedan intactas y el
`#else` restante devuelve 0 sin fabricar el dato.

## Requisitos y verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.2 — CUMPLE — compila en cada target | `pytest tests/auditoria/test_r317_detect_hardware_macos.py tests/auditoria/test_r318_detect_hardware_macos_mem.py` | 6 passed |
| Manual 9 §5.7 — CUMPLE — detección por FFI | idem | 6 passed |

| check | resultado |
|---|---|
| `build.py --skip-test` (Windows) | S2==S3, sha `9382d8d9c234` |
| `alineacion.py --verificar --me r318_detect_hardware_macos_mem` | OK, evidencia `6e868b39d236f3cf` |
| `contrastar.py --plan docs/plan_ME_r318_detect_hardware_macos_mem.md` | PASS |

## Corrección de oráculo declarada

`tests/auditoria/test_r317_detect_hardware_macos.py` afirmaba que macOS expone
`_SC_AVPHYS_PAGES`; la CI probó que no. Se reemplazó esa aserción por "existe
rama macOS" y la implementación concreta quedó cubierta por r318.

## Limitación declarada

La compilación real en macOS la valida `Release Matrix` tras el push; local no
hay toolchain darwin, sólo se verificó Windows (S2==S3) y las guardas.
