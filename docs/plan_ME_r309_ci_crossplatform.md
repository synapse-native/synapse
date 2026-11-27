# Plan de Micro-Entregable r309_ci_crossplatform

## Objetivo

El primer run de CI tras el push expuso dos fallos reales, ajenos a los cambios
de deuda, que impiden cualquier evidencia verde por plataforma (y por tanto
H-R276-2):

1. **`runtime/core/debug.c:478,485`** llama `mkdir(".synapse")` con un solo
   argumento. En POSIX `mkdir` exige `(path, mode)`, así que el runtime **no
   compila en Linux/macOS**. En Windows/MinGW la declaración acepta un
   argumento, por eso nunca se vio localmente. El mismo archivo ya usa el
   patrón `#ifdef _WIN32` en `_ensure_trace_dir`.
2. **`cryptography` falta en `requirements.txt`**: `instaladores/common/
   verificar_firma.py` la importa a nivel de módulo, y dos módulos de test la
   importan directamente. En macOS la recolección de pytest aborta con
   `ModuleNotFoundError` (3430 tests ni siquiera se colectan).

## Requisito 1 — compilar en todos los targets

requisito: Manual 9 §6.1
texto: "□ **Compilación sin errores**: todos los targets (Windows, Linux, macOS, WASM) compilan sin errores ni warnings."
implementacion: se sustituyen los dos `mkdir(".synapse")` de una sola llamada por un helper portable `_debug_asegurar_dir_synapse` con `_mkdir` en `_WIN32` y `mkdir(p, 0755)` en POSIX, igual que el patrón ya usado en el archivo; la cita `cumprir` se corrige a `cumple Manual 8 §3.4`.
oraculo: tests/auditoria/test_r309_ci_crossplatform.py

## Requisito 2 — dependencias declaradas para el CI

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: `requirements.txt` declara `cryptography>=41.0.0`, usada por `instaladores/common/verificar_firma.py` y por los tests de firma, para que la recolección de la suite no aborte en macOS/Linux.
oraculo: tests/auditoria/test_r309_ci_crossplatform.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r309_ci_crossplatform.py` | 3 passed |
| `build.py --skip-test` | rc=0, S2==S3 `1b30a488e480` |
| `gh run list` tras el push | compilación Linux/macOS en verificación |
| `contrastar.py --plan docs/plan_ME_r309_ci_crossplatform.md` | PASS (2/2) |
