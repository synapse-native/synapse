# Verificación — ME r312_compilacion_matrix

CUMPLE.

## Requisitos del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.1 — CUMPLE — PATH_MAX | `pytest tests/auditoria/test_r312_compilacion_matrix.py` | 3 passed |
| Manual 5 §2.1 — CUMPLE — CPUs en Darwin | idem | 3 passed |
| Manual 9 §6.1 — CUMPLE — OpenSyn en el instalador | idem | 3 passed |

## Causa y cambio

| fila | error del run `45167812091` | cambio |
|---|---|---|
| ubuntu-latest, ubuntu-arm | `web.c:64: 'PATH_MAX' undeclared` | `<limits.h>` en `web.c` |
| macos-latest | `ucontext.h:51: #error ... require _XOPEN_SOURCE` | se restaura `_XOPEN_SOURCE 700` en todo POSIX y Darwin cuenta CPUs con `sysctlbyname("hw.ncpu")` |
| windows-latest (installer) | `Source file dist\bin\opensyn.exe does not exist` | el workflow compila `dist\bin\opensyn.exe` con `main.py opensyn/principal.syn -o` |

### Corrección de la hipótesis de r310

r310 supuso que en Darwin se podía prescindir de `_XOPEN_SOURCE`. El CI lo
desmintió: el SDK de macOS aborta con `#error The deprecated ucontext routines
require _XOPEN_SOURCE to be defined`. El oráculo de r310 codificaba esa
suposición; se reescribió esa aserción (`test_concurrency_posix_define_xopen_source`)
para reflejar el comportamiento real y el oráculo nuevo de r312 verifica la vía
`sysctl`.

## Otros checks

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r310_compilacion_posix.py tests/auditoria/test_r312_compilacion_matrix.py` | 5 passed |
| `build.py --skip-test` (Windows) | rc=0, S2==S3 `1b30a488e480` |
| `oraculo_r252_paridad_bootstrap.py --estricto` | PASS |
| `alineacion.py --verificar --me r312_compilacion_matrix` | OK, evidencia `5b1540c98febd3a2` |
| `contrastar.py --plan docs/plan_ME_r312_compilacion_matrix.md` | PASS (3/3) |

## Pendiente fuera de alcance

`windows-latest` firma con `ED25519_PRIVATE_KEY`; el secreto no está
configurado en el repositorio y el workflow falla a propósito antes de publicar
un release sin firma. Eso es **H-R276-2** y requiere que el Arquitecto cargue el
secreto.
