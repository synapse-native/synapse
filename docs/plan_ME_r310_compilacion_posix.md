# Plan de Micro-Entregable r310_compilacion_posix

## Objetivo

El run de CI posterior al fix del workflow (`1ab7b2d`) ya ejecuta los jobs,
pero muestra que **el runtime solo compila en Windows**:

- `ubuntu-latest` / `ubuntu-24.04-arm`: `runtime/core/tui.c:1863: error: unknown
  type name 'DIR'`, `invalid use of undefined type 'struct dirent'`,
  `storage size of 'st' isn't known` → la rama POSIX del autocompletado usa
  `opendir`, `struct dirent` y `stat()` sin `#include <dirent.h>` ni
  `#include <sys/stat.h>`.
- `macos-latest` (darwin_arm64): `runtime/core/concurrency.c:901: error:
  '_SC_NPROCESSORS_ONLN' undeclared` → el archivo define `_XOPEN_SOURCE 700`
  en todo POSIX (necesario para `ucontext_t`), y en Darwin ese macro limita
  `unistd.h` al perfil XSI, donde esa constante no existe.

Esto bloquea 2 de 4 filas de la matriz y, con ellas, la evidencia de
H-R276-2.

## Requisito 1 — headers POSIX de directorios en TUI

requisito: Manual 5 §1
texto: "**El estado mutable compartido entre hilos está prohibido** a nivel de compilación."
implementacion: `runtime/core/tui.c` incluye `<dirent.h>` y `<sys/stat.h>` en la rama no-Windows (autocompletado POSIX con `opendir`/`readdir`/`stat`), y documenta junto al hilo dibujante que el único estado compartido es el flag de actividad protegido por `_out_lock`.
oraculo: tests/auditoria/test_r310_compilacion_posix.py

## Requisito 2 — feature-test macros por plataforma en concurrencia

requisito: Manual 5 §2.1
texto: "Pila propia (tamaño configurable, por defecto 64 KB)."
implementacion: `runtime/core/concurrency.c` define `_XOPEN_SOURCE 700` solo fuera de Darwin; en `__APPLE__` incluye `ucontext.h`+`unistd.h` con el perfil completo, de modo que `sysconf(_SC_NPROCESSORS_ONLN)` del scheduler M:N se declara también en macOS.
oraculo: tests/auditoria/test_r310_compilacion_posix.py

## Requisito 3 — UTF-8 sin BOM

requisito: Manual 2 §1.2
texto: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
implementacion: los archivos editados conservan codificación UTF-8 sin BOM (`cumple Manual 2 §1.2` ya presente en `concurrency.c`; el oráculo verifica los includes y la rama Darwin).
oraculo: tests/auditoria/test_r310_compilacion_posix.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r310_compilacion_posix.py` | 2 passed |
| `build.py --skip-test` (Windows) | rc=0 (rama Windows intacta) |
| CI Linux/macOS tras el push | pendiente de corrida |
| `contrastar.py --plan docs/plan_ME_r310_compilacion_posix.md` | PASS (3/3) |
