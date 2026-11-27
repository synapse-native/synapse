# Plan de Micro-Entregable r306_hook_generados

## Objetivo

Cerrar las dos lecciones de r302 que quedaron sin cambio de código:

1. **Paso no bloqueante**: el hook regeneraba `lib/runtime_bindings.syq` y, si
   el generador fallaba, imprimía `⚠️ no bloqueante` y dejaba commitear. Por eso
   tres generadores estuvieron rotos desde r288 sin que nadie lo notara.
2. **Ruido con borrados**: `check_pattern` del hook corre `sed` sobre cada
   archivo staged, incluidos los borrados (`git rm`), y escupe
   `sed: can't read ...` en cada commit que retira archivos.

Además, el SBOM determinista de r304 queda sin gate en el commit: un alta de
archivo lo deja desactualizado y `--check` solo se ejecuta si alguien lo llama.

## Requisito 1 — ningún generador roto puede llegar al commit

requisito: Manual 1 §7.4
texto: "Aprobación del 100% de los tests unitarios, de integración y fuzzing sin regresiones."
implementacion: en `scripts/githooks/pre-commit` la regeneración de `lib/runtime_bindings.syq` pasa a bloquear el commit si el generador falla, y se añade el mismo patrón para `synapse.spdx.json` (`nucleo/sbom.py --versionados --check`; si deriva, se regenera y se stagea; si falla, bloquea). `check_pattern` ignora archivos borrados (`[ -f "$f" ] || continue`).
oraculo: tests/auditoria/test_r306_hook_generados.py

## Evidencia

| check | resultado |
|---|---|
| `bash -n scripts/githooks/pre-commit` | OK |
| `pytest tests/auditoria/test_r306_hook_generados.py` | 4 passed |
| commit de prueba con un borrado | sin ruido de sed (r305) |
| `contrastar.py --plan docs/plan_ME_r306_hook_generados.md` | PASS (1/1) |
