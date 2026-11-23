# Verificación — ME r319_detect_hardware_mach_consts

CUMPLE.

## Causa y cambio

Run `45210212682`, job `137816676952` (macos-latest):

```
runtime/core/detect_hardware.c:68:36: error: 'HOST_VMSTATS64_COUNT' undeclared; did you mean 'HOST_VM_INFO64_COUNT'?
runtime/core/detect_hardware.c:70:33: error: 'HOST_VMSTATS64' undeclared
```

`mach/host_info.h` expone `HOST_VM_INFO64` y `HOST_VM_INFO64_COUNT`; r318 había
usado nombres inventados. El cambio sustituye ambos (y sólo eso): la lógica de
`free + inactive + speculative` por `host_page_size` queda igual.

## Requisitos y verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.2 — CUMPLE — compila en cada target | `pytest tests/auditoria/test_r317_... test_r318_... test_r319_...` | 9 passed |
| Manual 9 §5.7 — CUMPLE — detección por FFI | idem | 9 passed |

| check | resultado |
|---|---|
| `build.py --skip-test` (Windows) | S2==S3, sha `9382d8d9c234` |
| `alineacion.py --verificar --me r319_detect_hardware_mach_consts` | OK |
| `contrastar.py --plan docs/plan_ME_r319_detect_hardware_mach_consts.md` | PASS |

## Limitación declarada

Sin toolchain darwin local: la compilación real de macOS la decide
`Release Matrix` tras el push.
