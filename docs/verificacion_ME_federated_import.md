# Verificación ME — Fix import system std/federated.syn

## Requisito 1: std/federated.syn debe ser parseable

- CUMPLE: `std/federated.syn` parsea sin errores con `compilar_desde_texto()`.
  Todas las firmas de función están en una sola línea, alineado con la restricción
  del parser (parser.py línea 298: `while self._mirar().tipo not in (TokenID.RPAREN, TokenID.EOF, TokenID.NEWLINE)`).
  - archivo: `std/federated.syn:1` — comentario `# cumple Manual 1 §4`

## Requisito 2: firmas de función cumplen la gramática

- CUMPLE: 18 funciones exportadas (9 externas + 9 wrappers públicos) parsean
  correctamente. La EBNF (Manual 3 §3) define `funcion ::= "funcion" IDENTIFICADOR "(" [ parametros ] ")"` sin
  especificar multi-línea; el parser actual implementa una sola línea por firma.
  - archivo: `std/federated.syn:29` — `_syn_fed_registrar_worker` (6 parámetros, una línea)

## Requisito 3: importar std.federated funciona

- CUMPLE: `importar std.federated` en un programa Synapse compila sin errores
  y exporta las funciones `fed_iniciar`, `fed_cerrar`, `fed_registrar_worker`,
  `fed_eliminar_worker`, `fed_ronda_fedavg`, `fed_entrenar`, `fed_guardar`,
  `fed_cargar`, `fed_verificar_firma`.
  - oráculo: `tests/integration/test_federated_exec_10.py` (12/12 passed)
  - oráculo: `tests/integration/test_federated_adv_10.py` (12/12 passed)

## Requisito 4: compilar_texto resuelve imports (Manual 3 §3)

- CUMPLE: `tests/conftest.py` `compilar_texto()` ahora usa `pipeline.compilar_desde_texto()`
  que resuelve `importar std.*` y ejecuta el analizador semántico.
  - archivo: `tests/conftest.py:23`
  - verificación: ownership 21/21 passed (sin regresión)

## Requisito 5: tests alineados con Manual 2 §4.1 (puntero)

- CUMPLE: los tests federados ahora usan `inseguro:` para llamadas con
  parámetros `puntero`, y pasan `nulo` en vez de literal `0`.
  - Manual 2 §4.1: `puntero` es "Solo dentro de `inseguro`"
