# Verificación ME — Fix std/federated.syn firmas multilínea

## Requisito 1: std/federated.syn es parseable (Manual 1 §4)

- CUMPLE: `std/federated.syn` parsea sin errores con `compilar_desde_texto()`. 18 funciones
  exportadas (9 externas + 9 wrappers públicos). Comentario `# cumple Manual 1 §4` en línea 4.
  - archivo: std/federated.syn:4

## Requisito 2: firmas cumplen gramática (Manual 3 §3)

- CUMPLE: todas las funciones tienen parámetros en una sola línea, cumpliendo la EBNF
  `funcion ::= funcion IDENTIFICADOR ( [ parametros ] ) [ -> tipo ] : NEWLINE` y la
  restricción del parser (parser.py:298: `while self._mirar().tipo not in (RPAREN, EOF, NEWLINE)`).
  - archivo: std/federated.syn:29 (_syn_fed_registrar_worker, 6 parámetros en una línea)
