# Verificación — ME r313_link_flags

CUMPLE.

## Requisitos del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.1 — CUMPLE — flags de link por plataforma | `pytest tests/auditoria/test_r313_link_flags.py` | 2 passed |
| Manual 5 §2.1 — CUMPLE — CPUs de Darwin sin sysctl | idem | 2 passed |

## Causa y cambio

| fila | error del run `45170587854` | cambio |
|---|---|---|
| ubuntu-latest, ubuntu-24.04-arm | `ld.bfd: unrecognized option '--stack'` | `pipeline.py` aplica `-Wl,--stack` solo en `win32`, en los tres sitios: camino normal, `flags_compilacion` (clave de caché) y `_link_object` |
| macos-latest | `sys/ucred.h:101: unknown type name 'u_int'` (por `<sys/sysctl.h>` bajo `_XOPEN_SOURCE`) | `concurrency.c` no incluye sysctl; usa `_syn_cpu_nucleos()` de `detect_hardware.h` |

## Otros checks

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r310_compilacion_posix.py tests/auditoria/test_r312_compilacion_matrix.py tests/auditoria/test_r313_link_flags.py` | 7 passed |
| `build.py --skip-test` (Windows) | rc=0, S2==S3 `1b30a488e480` (sin cambios: la rama win32 conserva sus flags) |
| `oraculo_r252_paridad_bootstrap.py --estricto` | PASS |
| `alineacion.py --verificar --me r313_link_flags` | OK, evidencia `e9008a4c3d4a259e` |
| `contrastar.py --plan docs/plan_ME_r313_link_flags.md` | PASS (2/2) |

## Limitación declarada

El link efectivo en ELF/Mach-O se confirma en CI; en Windows no hay `ld.bfd`
ni Mach-O para reproducirlo. La rama Windows conserva exactamente los flags
anteriores, por eso el hash del bootstrap no cambia.
