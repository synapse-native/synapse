# Verificación — ME r309_ci_crossplatform

CUMPLE.

## Requisitos del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §6.1 — CUMPLE — compilar en todos los targets | oráculo + `build.py --skip-test` | 3 passed; build rc=0, S2==S3 `1b30a488e480` |
| Manual 9 §6.2 — CUMPLE — dependencias declaradas para el CI | oráculo (requirements) | `cryptography>=41.0.0` declarada |

## Causa y cambio

El primer run de CI tras el push expuso dos fallos reales y previos:

1. **`runtime/core/debug.c`**: `(void)mkdir(".synapse")` con un solo argumento.
   POSIX exige `mkdir(path, mode)`; el runtime **no compilaba en Linux/macOS**
   (`too few arguments to function 'mkdir'; expected 2, have 1`). El mismo
   archivo ya tenía el patrón portable en `_ensure_trace_dir`. Se añadió
   `_debug_asegurar_dir_synapse()` (`_mkdir` en `_WIN32`, `mkdir(p, 0755)` en
   POSIX) y ambas llamadas lo usan. De paso, `cumprir` → `cumple` en la cita.
2. **`requirements.txt`**: faltaba `cryptography`, importada a nivel de módulo
   por `instaladores/common/verificar_firma.py` y por tests de firma. En macOS
   la recolección abortaba con `ModuleNotFoundError` y no se colectaba ninguno
   de los 3430 tests. Declarada `cryptography>=41.0.0`.

## Otros checks

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r309_ci_crossplatform.py` | 3 passed |
| `build.py --skip-test` | rc=0, S2==S3 `1b30a488e480` |
| `oraculo_r252_paridad_bootstrap.py --estricto` | PASS (S2==S3; binarios distribuidos al día) |
| `verificar_alineacion.py` | 0 brechas |
| `alineacion.py --verificar --me r309_ci_crossplatform` | OK, evidencia `90b67df9b1f3d9f3` |
| `contrastar.py --plan docs/plan_ME_r309_ci_crossplatform.md` | PASS (2/2) |

## Nota

El hash del bootstrap cambia (`ad65693a51c2` → `1b30a488e480`) porque
`runtime/core/debug.c` se enlaza en el runtime; los binarios distribuidos se
refrescaron desde la etapa 2 y el oráculo `--estricto` confirma la
correspondencia. La compilación efectiva en Linux/macOS se confirma con el run
de CI del push siguiente.
