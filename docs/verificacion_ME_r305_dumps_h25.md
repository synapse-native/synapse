# Verificación — ME r305_dumps_h25

CUMPLE. Cierra H25.

## Requisitos del plan y su verificación

| requisito | verificación | resultado |
|---|---|---|
| Manual 1 §7.4 — CUMPLE — ninguna regresión por el retiro | `pytest tests/auditoria/test_r305_dumps_h25_retirados.py` + `build.py --skip-test` | 4 passed; build rc=0; S2==S3 `ad65693a51c2` |
| Manual 9 §6.1 — CUMPLE — inventario SPDX coherente | `pytest tests/auditoria/test_r304_sbom_determinista.py` | 5 passed |

## Qué se retiró

Ocho dumps del compilador S1 (eliminados del repo; git conserva su historia),
todos con `.syn` homónimo como fuente de verdad:

`nucleo/generator.c`, `nucleo/generator_pgo.c`, `nucleo/lexer.c`,
`nucleo/memoria.c`, `nucleo/parser.c`, `nucleo/principal.c`,
`nucleo/resolvedor_axon.c`, `nucleo/tabla_simbolos.c`.

Se conservan los tres `.c` que sí empaqueta el instalador y **no** tienen
`.syn`: `nucleo/ai_orchestrator.c`, `nucleo/federated.c`,
`nucleo/llama_client.c`.

`scripts/migrate_to_canonical_header.py` (migración D-9(e), ya aplicada) tenía
`nucleo/lexer.c` en `TARGETS` y habría fallado al abrirlo: se quita de la lista
y del docstring.

## Oráculo

`tests/auditoria/test_r305_dumps_h25_retirados.py` (4 casos): los ocho no están
en git ni en disco; sus `.syn` existen; **ningún** `.c` versionado bajo
`nucleo/` tiene `.syn` homónimo (regla general, sin allowlist); el script de
migración no apunta a archivos retirados.

El `DEUDA_H25` del oráculo r303 queda como lista histórica: los archivos ya no
existen, así que la comprobación sigue pasando y no se modificó ningún test
existente (los tests son inmutables).

## Otros checks

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r305_dumps_h25_retirados.py` | 4 passed |
| `pytest tests/auditoria/test_r304_sbom_determinista.py` | 5 passed |
| `nucleo/sbom.py --versionados --check` | rc=0 |
| `build.py --skip-test` | rc=0, S2==S3 `ad65693a51c2` |
| `verificar_alineacion.py` | 0 brechas |
| `verificar_encoding.py --estricto` | OK (2389 archivos) |
| `contrastar.py --plan docs/plan_ME_r305_dumps_h25.md` | PASS (2/2) |

## Deuda

Ninguna nueva.
