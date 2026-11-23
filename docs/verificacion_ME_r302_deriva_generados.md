# Verificación — ME r302_deriva_generados

CUMPLE. Cierra H-R302-2; registra H-R302-1.

## Requisitos del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 6 §3.1 — CUMPLE — generador de bindings operativo | `pytest tests/auditoria/test_r302_generados_sin_deriva.py` + diff contra `lib/runtime_bindings.syq` | 4 passed; 0 bytes |
| Manual 7 §2.1 — CUMPLE — pipeline de OpenSyn ejecutable | parseo AST de todos los `.py` versionados | OK |
| Manual 1 §3.1 — CUMPLE — librerías embebidas sincronizadas | `tests/_gen_embedded.py --check` | sincronizado (11) |
| Manual 1 §7.4 — CUMPLE — ningún generador roto | oráculo de sintaxis + `--check` de artefactos | OK |

## Otros checks

| check | resultado |
|---|---|
| `scripts/gen_ast_nodos_h.py --check` | sincronizado (134 constantes) |
| `python build.py --skip-test` | rc=0, S2==S3 `ad65693a51c2` |
| `pytest` harness gcc + r301 + r302 | 13 passed |
| `python auditoria/verificar_alineacion.py` | 0 brechas |
| `python auditoria/verificar_encoding.py --estricto` | OK (2391 archivos) |
| `python auditoria/contrastar.py --plan docs/plan_ME_r302_deriva_generados.md` | PASS (4/4) |
| `python auditoria/alineacion.py --verificar --me r302_deriva_generados` | OK, evidencia `42ec57da65bfb713` |

## Deuda registrada

- **H-R302-1** (requiere decisión de Arquitecto): 6 `.c` generados por S1 y
  versionados (`nucleo/analizador_semantico.c`, `ast_nodes.c`, `diagnostics.c`,
  `errores.c`, `estado_global.c`, `generator_constants.c`) están congelados en
  sept-2026 mientras sus `.syn` evolucionaron hasta nov-2026. No se enlazan en
  el build, pero figuran en `auditoria/contratos_baseline.txt` y en
  `synapse.spdx.json`. Resolución asignada: ME `r303_artefactos_c_generados`
  (regenerar o retirar, actualizando baseline y SPDX).
