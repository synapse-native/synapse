# Plan ME r222b_wrappers_regression - deduplicacion de helpers de texto

**Fecha:** 2026-11-15 - **Base:** 10ccda8 - **Tipo:** produccion
(`opensyn/router.syn`, `nucleo/lsp_v3.syn`) + fixture de baseline + oraculo
nuevo.

## Diagnostico reproducible

R222 restauro en `std/texto.syn` los envoltorios historicos `cmp_texto`,
`strstr_f` y `atoi_f`. Dos modulos que importan `std.texto` conservaban
definiciones locales de esos mismos nombres y ahora fallan al compilar:

- `opensyn/router.syn:29,36,43`: redefinicion de `cmp_texto`, `strstr_f` y
  `atoi_f`.
- `nucleo/lsp_v3.syn:1107`: redefinicion de `cmp_texto`.
- `tests/integration/test_compilacion_fase32.py`: `DEUDA NUEVA` por router y
  `TRIQUETE` por `opensyn/verificacion_aot.syn`, que ya compila y sigue en el
  baseline.

El comportamiento de los helpers locales es equivalente al de `std.texto`; la
correccion es eliminar la duplicacion y consumir la unica definicion publica.

## Plan (bloque MTS estricto)

requisito: Manual 7 §2.4
texto: "El router está escrito en Synapse y actúa como el cerebro de alto nivel de OpenSyn. Decide qué modelo usar y cómo procesar la respuesta."
implementacion: `opensyn/router.syn` deja de redeclarar `cmp_texto`,
`strstr_f` y `atoi_f`; usa los envoltorios publicos de `std.texto` ya
importados. No cambia el enrutamiento ni la seleccion de modelo.
oraculo: tests/auditoria/test_oraculos_r222b_wrappers.py

requisito: Manual 7 §4.2
texto: "La respuesta se procesa (router) para extraer el código (si lo hay)."
implementacion: el router conserva sus llamadas de comparacion y busqueda de
texto, pero resueltas por `std.texto`; el modulo vuelve a compilar con
`main.py --check --no-emit`.
oraculo: tests/auditoria/test_oraculos_r222b_wrappers.py

requisito: Manual 8 §1
texto: "El LSP es nativo, sin telemetría y sin dependencias externas (excepto el binario synapse.exe para compilar y analizar código)."
implementacion: `nucleo/lsp_v3.syn` deja de redeclarar `cmp_texto` y usa la
funcion publica de `std.texto`; no se altera el protocolo JSON-RPC ni el ciclo
de vida del LSP.
oraculo: tests/auditoria/test_oraculos_r222b_wrappers.py

requisito: Manual 1 §6
texto: "El compilador debe compilar todos los módulos de producción sin deuda oculta."
implementacion: se retira `opensyn/verificacion_aot.syn` de
`tests/fixtures/compilacion_baseline.txt`, porque R219 lo dejo compilando; el
baseline queda vacio y el gate de Fase 32 vuelve a verde.
oraculo: tests/auditoria/test_oraculos_r222b_wrappers.py

## Archivos previstos

- `opensyn/router.syn`: eliminar los tres helpers duplicados.
- `nucleo/lsp_v3.syn`: eliminar el helper `cmp_texto` duplicado.
- `tests/fixtures/compilacion_baseline.txt`: retirar
  `opensyn/verificacion_aot.syn`.
- `tests/auditoria/test_oraculos_r222b_wrappers.py`: oraculo nuevo de
  compilacion real y baseline vacio.
- `docs/verificacion_ME_r222b_wrappers_regression.md`: marcas CUMPLE.
- `docs/alineacion/r222b_wrappers_regression.md`: expediente de alineacion.

## Impacto esperado

- `main.py opensyn/router.syn --check --no-emit`: rc=0.
- `main.py nucleo/lsp_v3.syn --check --no-emit`: rc=0.
- `test_compilacion_fase32.py`: 2/2 GREEN y baseline vacio.
- Sin cambios en tests existentes; solo se agrega el oraculo nuevo.

## Riesgos y mitigacion

- `nucleo/lsp_v3.syn` fue tocado por R205b; el cambio se limita a eliminar una
  funcion identica a la de `std.texto`, sin tocar el protocolo ni el ciclo de
  vida. Si el autor del LSP conserva una variante divergente, el oraculo de
  compilacion y la suite LSP lo detectan.
- No se modifica ningun test existente ni se relaja el gate: el baseline se
  vacia porque el modulo ya compila, no para ocultar deuda.
