# Plan ME: Fix std/federated.syn firmas multilínea

## Problema

`std/federated.syn` usa firmas de función multilínea (parámetros en múltiples líneas).
El parser de Synapse (parser.py línea 298) termina la lectura de parámetros al encontrar
`NEWLINE`, causando errores de parseo que impiden la exportación de funciones fed_*.

## Requisitos

requisito: Manual 1 §4
texto: "std/ — Librería estándar de Synapse. std/federated.syn listado como módulo del std."
implementacion: std/federated.syn reescrito con firmas de función en una sola línea, alineado
  con todos los demás módulos std/ (cluster.syn, io.syn, etc.) que usan una sola línea.
oraculo: tests/integration/test_federated_exec_10.py

requisito: Manual 3 §3
texto: "funcion ::= funcion IDENTIFICADOR ( [ parametros ] ) [ -> tipo ] [ contratos ] : NEWLINE"
implementacion: cada función en std/federated.syn pone todos los parámetros en la misma línea
  que la apertura del paréntesis, cumpliendo la restricción del parser (parser.py:298).
oraculo: tests/integration/test_federated_exec_10.py

## Cambios

| Archivo | Cambio |
|---|---|
| `std/federated.syn` | Reescribir firmas multilínea → una línea; agregar `# cumple Manual 1 §4` |

## NO se modifican

- `tests/conftest.py` — sin cambios
- `tests/integration/test_federated_*.py` — sin cambios
- Ningún test — permisos de modificación de tests: NO AUTORIZADOS

## Validación

1. `python -c "from pipeline import compilar_desde_texto; ..."` — parsea sin errores
2. `python auditoria/verificar_alineacion.py` — 0 brechas
3. `python auditoria/contrastar.py --plan docs/plan_ME_federated_fix.md` — gate pasa
