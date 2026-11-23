# Verificación — ME r310_compilacion_posix

CUMPLE.

## Requisitos del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 5 §1 — CUMPLE — sin estado mutable compartido | `pytest tests/auditoria/test_r310_compilacion_posix.py` | 2 passed |
| Manual 5 §2.1 — CUMPLE — runtime de concurrencia | `pytest tests/auditoria/test_r310_compilacion_posix.py` | 2 passed |
| Manual 2 §1.2 — CUMPLE — UTF-8 sin BOM | oráculo + edición sin BOM | 2 passed |

## Causa y cambio

| target | error de CI | cambio |
|---|---|---|
| ubuntu-latest, ubuntu-24.04-arm | `tui.c:1863: unknown type name 'DIR'`; `struct dirent` y `struct stat` desconocidos | `tui.c` incluye `<dirent.h>` y `<sys/stat.h>` en la rama no-Windows |
| macos-latest (darwin_arm64) | `concurrency.c:901: '_SC_NPROCESSORS_ONLN' undeclared` | `concurrency.c` define `_XOPEN_SOURCE 700` solo fuera de Darwin; en `__APPLE__` incluye `ucontext.h`+`unistd.h` con el perfil completo |

Ninguno de los dos se reprodujo en Windows, donde la rama `_WIN32` evita todo
el código afectado: por eso el proyecto compilaba localmente y no en la matriz.

## Otros checks

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r310_compilacion_posix.py` | 2 passed |
| `alineacion.py --verificar --me r310_compilacion_posix` | OK, evidencia `82edd61d35986c71` |
| `contrastar.py --plan docs/plan_ME_r310_compilacion_posix.md` | PASS (3/3) |
| `verificar_alineacion.py` | 0 brechas |

## Limitación declarada

La compilación efectiva en Linux y macOS solo puede confirmarse en CI: en
Windows no hay toolchain POSIX completo que reproduzca `opendir`/`sysconf`.
El run del push siguiente es la verificación real.
