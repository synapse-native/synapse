# Verificación — ME r329_installer_prewarm_runtime_cache

CUMPLE.

## Cambios

- `instaladores/windows/prewarm_runtime_cache.ps1` (nuevo): compila
  `synapse_rt.c`, `runtime/core/*.c`, `axon/tweetnacl.c`,
  `vendor/sqlite3/sqlite3.c` y las fuentes de IA con el `gcc` del toolchain
  incluido y escribe `<sha256>|<gcc>|-O2|...` en el sidecar `.sha`, dentro de
  `%USERPROFILE%\.synapse\cache\runtime_obj` (la ruta que resuelve
  `nucleo/principal.syn`).
- `instaladores/windows/synapse.iss`: `[Files]` envía el script a `{app}`;
  `[Run]` lo ejecuta tras la instalación (`runhidden`, con `StatusMsg`).

## Verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 9 §7 — CUMPLE — instalación operativa | ejecución del script en staging ({app} + toolchain) | 39 objetos compilados, 0 fallos |
| Manual 9 §2.5 — CUMPLE — patrón Inno Setup | `ISCC.exe instaladores/windows/synapse.iss` | compilación exitosa |

| check | resultado |
|---|---|
| `contrastar.py --plan docs/plan_ME_r329_installer_prewarm_runtime_cache.md` | PASS |
| `python -m pytest tests/auditoria/test_oraculos_r329_prewarm_runtime_cache.py -v` | 3 passed |
| `verificar_alineacion.py` | SIN BRECHAS |
| `build.py` | S2==S3 `2ecf367cae98df91` |
