# Plan de Micro-Entregable r284_observabilidad_local

## Objetivo

Diagnóstico local *opt-in* sin telemetría forzada: subcomando
`synapse observability [status|health|info]` despachado desde el binario, con
helpers locales en el runtime y cero salidas de red.

## Requisito 1 — cero telemetría y cero conexiones ocultas

requisito: Manual 1 §5.7
texto: "Los binarios compilados y las herramientas del ecosistema no realizan ninguna conexión en red oculta, recolección de datos de uso ni analíticas."
implementacion: el bloque `observability` de `nucleo/principal.syn` se ejecuta dentro de `asm(...)` y solo usa `strcmp`/`fprintf`/`_argv`/`_argc`; `runtime/core/debug.c` implementa `_syn_health_check` y `_syn_diagnostic_info` formateando estado local (`snprintf`) sin sockets ni HTTP. Citas `// cumple Manual 1 §5.7` en el bloque. Corrige además el despacho roto: `status` era inalcanzable, `info` no existía y un `--status` caía en "desconocido".
oraculo: tests/auditoria/test_r284_observabilidad_sin_red.py

## Requisito 2 — diagnóstico local sin salir del equipo

requisito: Manual 7 §7.3
texto: "- **Cero telemetría:** ningún binario realiza conexiones en red ocultas."
implementacion: `synapse observability status|health|info` reporta únicamente estado local (`telemetry: off`, `modo: opt-in`, arena/memoria) desde `_syn_health_check`/`_syn_diagnostic_info`; no hay ruta de código que exporte contexto.
oraculo: tests/auditoria/test_r284_observabilidad_sin_red.py

## Evidencia

| check | resultado |
|---|---|
| `pytest tests/auditoria/test_r284_observabilidad_sin_red.py` | 4 passed |
| `synapse_bootstrap.exe observability status\|health\|info` | rc=0, salida local |
| `auditoria/verificar_encoding.py --estricto` | OK |

## Hallazgos

- **H-R284-1** (CHANGELOG): cubierto en `CHANGELOG.md` (`554210a`).
- **H-R284-2** (test de no-salida): **RESUELTO** — `tests/auditoria/test_r284_observabilidad_sin_red.py`.
- **H-R284-3** (Manual 32 §1.3): sin acción; la cita se conserva como referencia de alcance.
