# Plan ME r220_harness_runtime_path - PATH/CPATH canonico del harness

**Fecha:** 2026-11-13 - **Base:** 33320c9 (R219) - **Tipo:** harness de tests
(no cambia codigo de produccion ni tests existentes).

## Diagnostico reproducible

- Sin `toolchain_gcc12\mingw64\bin` en PATH, los binarios de test fallan al
  cargar `libwinpthread-1.dll` con `3221225595` (`0xC000014B`): la compilacion
  pasa, la ejecucion no arranca. Afecta a cluster, axon, binario_real, canales
  y cache_audit.
- Con el bin del toolchain al frente de PATH, los mismos subsets pasan
  (19/19 y 38/38; el timeout de compilacion de handshake no se reprodujo en la
  corrida de cierre).
- `tests/conftest.py` compila `test_ffi_marshaling_auto.c` con `-I<raiz>` pero
  `ffi_marshaling.h` vive en `runtime/core/`; el header no se resuelve y el
  harness emite un WARNING persistente.

## Plan (bloque MTS estricto)

requisito: Manual 9 §6.2
texto: "La suite de tests completa en cada target."
implementacion: en `tests/conftest.py`, al importar el modulo (antes de
cualquier fixture/subprocess), anteponer `toolchain_gcc12/mingw64/bin` a
`PATH` si existe, y agregar `runtime/core` a `CPATH` despues de la raiz. No se
tocan comandos de test ni archivos de test. El bin del toolchain es el mismo
que resuelve `cli._resolver_gcc`, por lo que los binarios que compila el
harness encuentran sus DLLs al ejecutarse.
oraculo: tests/auditoria/test_oraculos_r220_harness_runtime_path.py

requisito: Manual 9 §2.3
texto: "Ejecutar la suite de tests completa para cada target."
implementacion: la misma inicializacion de entorno (PATH + CPATH) hace que el
target Windows ejecute la suite compilada sin depender de que el operador
exporte variables antes de pytest; el oraculo compila y ejecuta un binario que
usa `pthread`/`libwinpthread` y compila el C de FFI sin `-I runtime/core`.
oraculo: tests/auditoria/test_oraculos_r220_harness_runtime_path.py

## Archivos previstos

- `tests/conftest.py`: inicializacion de PATH y CPATH en el import del harness.
  Comentario `# cumple Manual 9 §6.2` junto al cambio.
- `tests/auditoria/test_oraculos_r220_harness_runtime_path.py`: oraculo nuevo
  con cuatro comprobaciones (PATH, CPATH, ejecucion pthread, FFI header).
- `docs/verificacion_ME_r220_harness_runtime_path.md`: marcas CUMPLE con
  archivo:linea tras ejecutar los gates.
- `docs/alineacion/r220_harness_runtime_path.md`: expediente de alineacion.
- `docs/reportes/R220.md` y `MEMORIA_PROYECTO.md`: cierre post-commit.

## Impacto esperado

- Los tests que compilan y ejecutan binarios con el toolchain canonico dejan
  de fallar por DLL ausente sin cambiar ningun test.
- El warning de `ffi_marshaling.h` desaparece y el binario FFI se construye
  con el entorno normal de la suite.
- No hay cambio de comportamiento del compilador ni del runtime.

## Riesgos y mitigacion

- PATH demasiado largo o con entradas duplicadas: se inserta una sola vez al
  frente y se conserva el resto.
- CPATH existente: se conserva y solo se anteponen raiz y `runtime/core`.
- Si el bin del toolchain no existe, no se altera PATH y el oraculo falla con
  mensaje explicito (no se inventa un gcc alternativo).
- Tests inmutables: no se modifica ningun archivo bajo `tests/integration/` ni
  `tests/syquex/`; solo el harness y un oraculo nuevo.
