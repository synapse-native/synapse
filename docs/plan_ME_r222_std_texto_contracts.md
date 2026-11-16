# Plan ME r222_std_texto_contracts - contratos y API de std/texto

**Fecha:** 2026-11-14 - **Base:** 33320c9 (R219) - **Tipo:** produccion
(`std/texto.syn`) + oraculo nuevo.

## Diagnostico reproducible

`tests/unit/test_std_contracts.py` tiene 3 RED en HEAD:

- `contiene()` sin `requiere:` (la clausula fue retirada por la decision
  ratificada H-R196-1: `Manual 8 §1.7.3` no impone precondicion y la subcadena
  vacia es valida).
- `cmp_texto()` y `strcpy_f()` no existen en `std/texto.syn`; existian en
  `d022ad8`/`4c82469` y se perdieron en `a2d0ca3` (r199).

## Plan (bloque MTS estricto)

requisito: Manual 2 §5.1
texto: "requiere: Se evalua antes de la primera instruccion del cuerpo. Todas las expresiones deben ser booleanas."
implementacion: en `std/texto.syn`, las dos definiciones de `contiene()` declaran
`requiere: verdadero` (clausula booleana sin precondicion). No se reintroduce
`longitud(subcadena) > 0`: H-R196-1 sigue vigente y la subcadena vacia sigue
siendo valida.
oraculo: tests/auditoria/test_oraculos_r222_std_texto.py

requisito: Manual 2 §5.1
texto: "garantiza: Se evalua inmediatamente antes de cada retornar. La variable _resultado_ contiene el valor que se va a retornar."
implementacion: se restauran en `std/texto.syn` los envoltorios publicos
`cmp_texto`, `strlen_s`, `strstr_f`, `strchr_f`, `atoi_f`, `strcpy_f` y
`strncpy_f`, cada uno con `garantiza` observable sobre `_resultado_`.
oraculo: tests/auditoria/test_oraculos_r222_std_texto.py

requisito: Manual 6 §3.1
texto: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave externo."
implementacion: los envoltorios llaman a los `externo funcion _syn_str*` ya
declarados al final de `std/texto.syn`; no se agregan simbolos no documentados
ni se altera el runtime C.
oraculo: tests/auditoria/test_oraculos_r222_std_texto.py

requisito: Manual 8 §1.7.3
texto: "Las funciones contiene, indice_de y reemplazar se implementan como builtins en C y se exponen en Synapse"
implementacion: se conserva el binding de `contiene` a
`_syn_texto_contiene`; el oraculo E2E verifica que `contiene(texto, "")`
devuelve 1 y que `cmp_texto`/`strcpy_f` compilan y ejecutan.
oraculo: tests/auditoria/test_oraculos_r222_std_texto.py

## Archivos previstos

- `std/texto.syn`: `requiere: verdadero` en `contiene` y bloque de envoltorios
  historicos de bajo nivel.
- `tests/auditoria/test_oraculos_r222_std_texto.py`: oraculo nuevo (contratos
  estaticos + compilacion/ejecucion real).
- `docs/verificacion_ME_r222_std_texto_contracts.md`: marcas CUMPLE.
- `docs/alineacion/r222_std_texto_contracts.md`: expediente de alineacion.

## Impacto esperado

- `tests/unit/test_std_contracts.py`: 20/20 GREEN (antes 17/20).
- La API historica de `std/texto.syn` vuelve a estar disponible para LSP,
  OpenSyn y codigo de usuario.
- Sin cambio de comportamiento de `contiene` con subcadenas vacias.

## Riesgos y mitigacion

- Duplicados de `contiene`/`indice_de` en el archivo: el oraculo exige que
  TODAS las definiciones de `contiene` tengan `requiere` y `garantiza`, no solo
  la primera.
- Tests existentes inmutables: no se modifica `tests/unit/test_std_contracts.py`;
  el cambio se limita a produccion y a un oraculo nuevo.
- `atoi_f` conserva su `requiere` historico y declara `garantiza: verdadero`
  para cumplir la regla de contratos en funciones publicas sin inventar una
  semantica no documentada.
