# Plan de Micro-Entregable r319_detect_hardware_mach_consts

## Objetivo

Quinta vuelta sobre `Release Matrix` (run `45210212682`). macOS ya entra en la
rama `__APPLE__` de `_syn_memoria_libre`, pero las constantes elegidas en r318
no existen:

```
runtime/core/detect_hardware.c:68:36: error: 'HOST_VMSTATS64_COUNT' undeclared (first use in this function); did you mean 'HOST_VM_INFO64_COUNT'?
runtime/core/detect_hardware.c:70:33: error: 'HOST_VMSTATS64' undeclared (first use in this function)
```

`mach/host_info.h` define `HOST_VM_INFO64` y `HOST_VM_INFO64_COUNT`.
Linux x64/ARM64 y Windows siguen fallando solo en la firma Ed25519 (H-R276-2).

## Requisito 1 — macOS compila con la API mach real

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: `runtime/core/detect_hardware.c` usa `HOST_VM_INFO64_COUNT` y `host_statistics64(host, HOST_VM_INFO64, ...)`; no queda ningún `HOST_VMSTATS64`.
oraculo: tests/auditoria/test_r319_detect_hardware_mach_consts.py

## Requisito 2 — detección de hardware por FFI intacta

requisito: Manual 9 §5.7
texto: "El módulo `std/os.syn` proporciona funciones de detección de hardware y sistema utilitarias, utilizadas por el instalador de OpenSyn (ver §5.1). Estas funciones están implementadas mediante FFI a llamadas del sistema operativo."
implementacion: `host_page_size` sigue consultando el kernel; las ramas Windows y Linux no cambian.
oraculo: tests/auditoria/test_r319_detect_hardware_mach_consts.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r317_... test_r318_... test_r319_...` | 9 passed |
| `build.py --skip-test` (Windows) + `S2==S3` | OK, sha `9382d8d9c234` |
| `alineacion.py --verificar --me r319_detect_hardware_mach_consts` | OK (`ba28e765940f84b3`) |
| `contrastar.py --plan docs/plan_ME_r319_detect_hardware_mach_consts.md` | PASS |
| CI `Release Matrix` macOS tras el push | pendiente de corrida |
