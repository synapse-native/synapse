# Plan ME: Fix import system std/federated.syn

## Problema

`std/federated.syn` usa firmas de función multilínea (parámetros en múltiples líneas).
El parser de Synapse (parser.py línea 298) termina la lectura de parámetros al encontrar
`NEWLINE`, causando errores de parseo que impiden que las funciones `fed_*` se exporten.

Resultado: `importar std.federated` falla con errores de parseo y no exporta ninguna función.

## Requisitos

### Requisito 1: std/federated.syn debe ser parseable

requisito: Manual 1 §4
texto: "std/ — Librería estándar de Synapse: federated.syn (Aprendizaje federado)"
implementacion: std/federated.syn reescrito con firmas de función en una sola línea, alineado
  con todos los demás módulos std/ (cluster.syn, io.syn, etc.) que usan una sola línea por función.
oraculo: tests/integration/test_federated_exec_10.py

### Requisito 2: firmas de función deben cumplir la gramática

requisito: Manual 3 §3
texto: "funcion ::= funcion IDENTIFICADOR ( [ parametros ] ) [ -> tipo ] [ contratos ] : NEWLINE"
implementacion: cada función en std/federated.syn pone todos los parámetros en la misma línea
  que la apertura del paréntesis, cumpliendo la restricción del parser.
oraculo: tests/integration/test_federated_exec_10.py

## Cambios

| Archivo | Cambio |
|---|---|
| `std/federated.syn` | Reescribir firmas multilínea → una línea; agregar `# cumple Manual 1 §4` |
| `tests/conftest.py` | `compilar_texto()` ahora resuelve imports via `pipeline.compilar_desde_texto()` |
| `docs/verificacion_ME_federated_import.md` | Verificación MTS |

## Validación

1. `python -c "from pipeline import compilar_desde_texto; ..."` — parsea sin errores
2. `python -m pytest tests/integration/test_federated_exec_10.py tests/integration/test_federated_adv_10.py -v` — tests pasan
3. `python auditoria/verificar_alineacion.py` — 0 brechas
4. `python auditoria/contrastar.py --plan docs/plan_ME_federated_import.md` — gate pasa
