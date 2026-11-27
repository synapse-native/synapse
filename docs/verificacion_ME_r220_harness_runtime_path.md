# Verificación ME r220_harness_runtime_path

**Base:** 33320c9 (R219). **Método:** MTS + TDD + MTO. **Tests existentes:** no
modificados. **Alcance:** harness de tests (`tests/conftest.py`) + oráculo nuevo.

## Marcas por requisito

- Manual 9 §6.2 R1 la suite completa se ejecuta en cada target con el toolchain canónico: el harness antepone `toolchain_gcc12/mingw64/bin` a `PATH` antes de ejecutar cualquier binario (evidencia `tests/conftest.py:29`, `tests/conftest.py:34`, `tests/conftest.py:39`; oráculo `tests/auditoria/test_oraculos_r220_harness_runtime_path.py` r1 y r3): CUMPLE

- Manual 9 §2.3 R2 el pipeline de pruebas por target no depende de variables exportadas manualmente: el mismo import del harness deja PATH listo y resuelve `ffi_marshaling.h` con un `-I runtime/core` dirigido, sin meter `runtime/core` en CPATH (evita sombrear `<math.h>`) (evidencia `tests/conftest.py:19`, `tests/conftest.py:262`, `tests/conftest.py:265`; oráculo `tests/auditoria/test_oraculos_r220_harness_runtime_path.py` r2 y r4): CUMPLE

## Validación ejecutada

- Oráculo propio: `tests/auditoria/test_oraculos_r220_harness_runtime_path.py`
  4/4 GREEN (PATH, CPATH sin sombra de math.h, ejecución pthread, FFI con
  include dirigido).
- Regresión afectada, con entorno normal de pytest:
  - `tests/integration/test_axon_e2e.py` + `test_binario_real_10.py` +
    `test_canales_fibras.py`: 15 passed.
  - `tests/integration/test_cache_audit.py`: 4 passed (240.99 s).
  - `tests/integration/test_cluster_discovery.py` +
    `test_cluster_multicast.py` + `test_cluster_handshake_e2e.py`: 38 passed
    (41.63 s); el timeout previo de handshake no se reproduce.
  - `tests/syquex/test_ffi_marshaling_auto.py`: 11 passed; el warning de
    `ffi_marshaling.h` desaparece tras reconstruir el exe.
- Baseline adicional (no cambia código de R220):
  - `tests/integration/test_build_py.py` 2/2 GREEN (S2==S3).
  - `tests/integration/test_release_unificado.py` GREEN tras refrescar la
    distribución con `python distribuir.py` (el binario empaquetado estaba
    stale desde el 6/11; ahora coincide con `synapse_stage2.exe`, firma
    verificada).
- Gates:
  - `python auditoria/contrastar.py --plan docs/plan_ME_r220_harness_runtime_path.md`:
    todos los chequeos pasan.
  - `python auditoria/verificar_alineacion.py`: sin brechas (reportado por
    contrastar).

## Hallazgos

- H-R220-1 (resuelto): PATH sin toolchain producía `0xC000014B` al ejecutar
  binarios de test; el harness ahora lo resuelve.
- H-R220-2 (resuelto): el `-I runtime/core` global vía CPATH rompía
  `runtime/core/math.c` al sombrear `<math.h>`; se cambió a include dirigido
  solo para el fuente FFI.
- H-R220-3 (resuelto/observación): el timeout de
  `test_cluster_handshake_e2e.py` no se reprodujo; cluster completo 38/38
  GREEN. Queda como verificación de frío si reaparece.
