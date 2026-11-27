# Verificación — ME r306_hook_generados

CUMPLE.

## Requisito del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 1 §7.4 — CUMPLE — ningún generador roto llega al commit | `pytest tests/auditoria/test_r306_hook_generados.py` + `bash -n` | 4 passed; sintaxis OK |

## Qué cambió en `scripts/githooks/pre-commit`

1. **Regeneración de bindings ahora bloquea**: si
   `opensyn/generate_runtime_bindings.py` falla, el commit se aborta con
   instrucciones. Antes imprimía `⚠️ no bloqueante` y seguía — así estuvieron
   rotos tres generadores desde r288 (lección de r302).
2. **`check_pattern` ignora borrados staged**: `git rm` de archivos ya no
   produce `sed: can't read ...` en cada commit.
3. **Gate de SBOM (r304)**: si `nucleo/sbom.py --versionados --check` detecta
   deriva, el hook regenera `synapse.spdx.json`, recalcula su `.sha256`, lo
   stagea y vuelve a verificar; si no puede, bloquea el commit. El inventario
   no puede quedar desactualizado.

## Oráculo

`tests/auditoria/test_r306_hook_generados.py` (4 casos): el hook es bash
válido; no queda ningún `no bloqueante`; `check_pattern` salta archivos
inexistentes; y el hook invoca verificación + regeneración + checksum del SBOM.

## Otros checks

| check | resultado |
|---|---|
| `bash -n scripts/githooks/pre-commit` | OK |
| `pytest tests/auditoria/test_r306_hook_generados.py` | 4 passed |
| commit de r306 (usa el hook nuevo) | pasa con regeneración de SBOM automática |
| `contrastar.py --plan docs/plan_ME_r306_hook_generados.md` | PASS (1/1) |

## Deuda

Ninguna nueva.
