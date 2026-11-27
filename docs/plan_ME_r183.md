# Plan ME r183 — coincidir_bloque_nativo (H-R180-1)

Fila del plan maestro: `docs/plan_maestro_deudas.md` ME R183 (registrado en R180 be5d447).
Base: `0db8973` (sello de lectura `auditoria/r183.antes.json`).

## Diagnóstico (bisección + trazado token a token, sesión R183)

Probes en raíz (borrar antes de commit): b1 (rc=8 línea 8), b2 (PASA), b3 (PASA),
b4 (rc=1 "Error Fatal Generador: Nodo tipo [DefinicionFuncion] no reconocido"),
b5 (PASA), exotic (rc=8 línea 12).

Causa raíz ÚNICA en `parsear_coincidir` (nucleo/parser_sentencias.syn): el
anti-cuelgue del final del bucle de casos
`si token_es_nombre(token_mirar(est)) != 1: token_avanzar(est)`
corre en TODA iteración, incluso después de haber parseado un caso CON ÉXITO:

- b4 (2+ casos con cuerpo-bloque, coincidir al final de la función): tras el
  último cuerpo (r22a consume SU desindentar), el cursor cae en el DESINDENTAR
  que cierra el bloque de casos; el anti-cuelgue se lo come (T_DESINDENTAR no
  es nombre) y la rama `T_DESINDENTAR` del bucle externo se come el
  DESINDENTAR que cierra el CUERPO de la función → `funcion` queda expuesto y
  `parsear_sentencia` (parser_stmt.syn L321 `si t == T_FUNCION:
  retornar parsear_funcion(est)`) lo parsea como def anidada dentro del cuerpo
  → el walk del generador top-level encuentra DefinicionFuncion anidada →
  "Nodo tipo [DefinicionFuncion] no reconocido", rc=1.
- b1 (2 bloques + una-línea): tras el caso 1 el cursor cae en el patrón
  numérico `2` del caso siguiente; `token_es_nombre(T_NUMERO) == 0`
  (predicado de R11 PREVIO a R180, que añadió T_NUMERO solo a
  `token_es_inicio_patron`) → el anti-cuelgue se come el patrón → el
  DESINDENTAR del cuerpo del caso 2 cierra prematuramente el bucle de casos →
  el caso `_ =>` se filtra al cuerpo de la función → rc=8 (error de sintaxis
  en la línea del caso filtrado).
- exotic (coincidir con casos-bloque dentro de `si`): misma mecánica que b1;
  el garbage `2 => let` deja el cursor en `b` → case-parse con
  `token_esperar(T_FLECHA_DER)` falla → rc=8.
- b2/b5/b3 (PASAN): su último caso es de UNA LÍNEA y el anti-cuelgue solo se
  come un NL inofensivo (o un DESINDENTAR que por azar cae bien en la pila del
  bloque externo). El paso es accidental, no correcto por diseño.

## Cambio 1 — el anti-cuelgue del bucle de casos no corre tras un caso parseado

requisito: Manual 3 §3
texto: "caso              ::= patron \"=>\" ( sentencia | NEWLINE INDENT bloque DEDENT )"
implementacion: nucleo/parser_sentencias.syn (parsear_coincidir) — variable
`caso_parseado` reiniciada a 0 en cada iteración del bucle de casos y puesta a
1 cuando la iteración produjo un NODO_CASO completo (patrón + flecha + cuerpo
+ encadenado). El anti-cuelgue `si token_es_nombre(...) != 1:
token_avanzar(est)` pasa a correr SOLO cuando `caso_parseado == 0` (no hubo
progreso: la iteración no parseó caso). Tras un caso parseado el cursor ya
está en el token real siguiente (patrón del caso siguiente o DESINDENTAR que
cierra el bloque de casos) y avanzarlo de más corrompe la contabilidad de
niveles del bloque (b4: se come el cierre del cuerpo de la función; b1/exotic:
se come el patrón numérico del caso siguiente). El anti-cuelgue se conserva
para su propósito original (tokens que no inician patrón y no son consumidos
por nada — paridad A3.1).
oraculo: tests/auditoria/test_oraculos_r183_coincidir_bloques.py

## Cambio 2 — secuencia de casos { caso } con paridad S1↔nativo (oráculo)

requisito: Manual 3 §3
texto: "coincidir         ::= \"coincidir\" expresion \":\" NEWLINE INDENT { caso } DEDENT"
implementacion: verificación de paridad de la secuencia completa de casos con
cuerpo-bloque: 2+ casos-bloque (literal y ADT ok/err), bloque de casos cerrado
en medio de la función (sentencia posterior al coincidir) y coincidir con
casos-bloque dentro de `si`. S1 ya cumple (los probes compilan y corren en
S1); el oráculo fija el contrato y ejecuta la misma salida en ambos pipelines
(M1 §3.1 pipeline compartido).
oraculo: tests/auditoria/test_oraculos_r183_coincidir_bloques.py (test_r6_paridad_s1)

## Pasos

1. TDD RED: oráculo con stage2 actual (sellado cdcc5262, con el bug) —
   test_r1..r5 fallan (b4→rc=1, b1/exotic→rc=8, ADT-2-bloques, medio); test_r6
   (paridad S1) y test_r7 (regresión b2/b3) pasan.
2. Fix en nucleo/parser_sentencias.syn con cita `// cumple Manual 3 §3`.
3. Bootstrap S1→S2→S3; sha256 stage2==stage3 (exe fresco, H-R180-2).
4. Oráculo GREEN + regresión: oráculo r180 (5/5), unit lexer/parser, MTO.
5. Gates MTS (lecturas por archivo según mapa_manuales, alineacion
   --leer/--nuevo/--verificar --me r183, contrastar, verificar_alineacion
   0 brechas) → commit → docs post-commit.

## Verificación de sintaxis Synapse aplicable al cambio

- Asignación simple `caso_parseado = 0/1` (sin declaración: paridad con
  `primer_caso`/`ultimo_caso` que se asignan igual en el mismo bucle).
- `siguiente`/`romper` del anti-cuelgue quedan en el MISMO nivel de bucle
  (`mientras r == 1` de casos), sin anidar bucles nuevos.
