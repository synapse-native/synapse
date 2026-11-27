# Plan de Micro-Entregable r312_compilacion_matrix

## Objetivo

El run `45167812091` (push `b6544b1`) ya pasa el setup y corrige `tui.c`, pero
la matriz sigue en rojo por tres causas distintas:

| fila | error | causa |
|---|---|---|
| ubuntu-latest, ubuntu-24.04-arm | `web.c:64: 'PATH_MAX' undeclared` | falta `<limits.h>` |
| macos-latest | `ucontext.h:51: #error ... require _XOPEN_SOURCE to be defined` | r310 quitó `_XOPEN_SOURCE` en Darwin; el SDK lo exige para `ucontext` |
| windows-latest (installer) | `Source file dist\bin\opensyn.exe does not exist` | el workflow nunca construía OpenSyn |
| windows-latest (sign) | `ED25519_PRIVATE_KEY no configurada` | falta el secreto del repositorio (bloquea H-R276-2) |

## Requisito 1 — PATH_MAX declarado

requisito: Manual 9 §6.1
texto: "□ **Compilación sin errores**: todos los targets (Windows, Linux, macOS, WASM) compilan sin errores ni warnings."
implementacion: `runtime/core/web.c` incluye `<limits.h>` antes de usar `PATH_MAX` en las estructuras del servidor HTTP (linux_x64 y linux_arm64 no lo recibían de forma transitiva).
oraculo: tests/auditoria/test_r312_compilacion_matrix.py

## Requisito 2 — conteo de CPUs en Darwin

requisito: Manual 5 §2.1
texto: "Pila propia (tamaño configurable, por defecto 64 KB)."
implementacion: `runtime/core/concurrency.c` vuelve a definir `_XOPEN_SOURCE 700` en todo POSIX (exigido por `ucontext.h` del SDK de macOS) y resuelve el número de hilos del scheduler M:N con `sysctlbyname("hw.ncpu")` en `__APPLE__`, con supresión local de la advertencia de deprecación.
oraculo: tests/auditoria/test_r312_compilacion_matrix.py

## Requisito 3 — OpenSyn en el instalador

requisito: Manual 9 §6.1
texto: "□ **Instaladores multiplataforma**: se generan instaladores para Windows (.exe), Linux (.deb, .AppImage) y macOS (.dmg) desde el mismo código fuente."
implementacion: el paso de build de `.github/workflows/cross-compile.yml` compila además `dist\bin\opensyn.exe` con `python main.py opensyn/principal.syn -o dist\bin\opensyn.exe`, porque `instaladores/windows/synapse.iss` lo exige sin `skipifsourcedoesntexist`.
oraculo: tests/auditoria/test_r312_compilacion_matrix.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r312_compilacion_matrix.py` | 3 passed |
| `pytest tests/auditoria/test_r310_compilacion_posix.py` | 2 passed |
| CI matriz tras el push | pendiente de corrida |
| `contrastar.py --plan docs/plan_ME_r312_compilacion_matrix.md` | PASS (3/3) |
