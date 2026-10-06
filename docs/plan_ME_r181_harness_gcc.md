# Plan ME r181_harness_gcc — Harness GCC del entorno de integración (H-R176-1)

**Fecha:** 2026-10-05 · **Base:** c5118f5 (R180) · **Mandato:** "repara y corrige
todo; los tests solo se modifican si es para alinear al manual; nunca dejamos
deuda nueva o antigua; autorizado a decidir siguiendo las reglas".

## Diagnóstico (R176 clasificación C = 27 → re-clasificado en este ME)

Reproducción aislada de la familia GCC entorno (H-R176-1) sobre c5118f5:

- **6 link-real** (5 de `tests/integration/test_e2e_adv_10.py::TestEjecucionReal`
  + `test_toml_raii.py::test_toml_compile_and_run`): el C generado por el
  generador S1 incluye `#include "librerias/embedded_libs.h"` y
  `"runtime/core/ast_nodos.h"` (rutas relativas a la RAÍZ del repo) y llama
  `pool_init/pool_free/pool_alloc/pool_destroy/synapse_esperar_hilos/
  synapse_esperar_fibras/_simd_detectar` en el prólogo de `main()` — pero el
  comando gcc de esos tests no pasa `-I<raíz>` ni enlaza objetos del runtime.
- **3 quantum .o** (`test_quantum_exec_10.py::TestQuantumRuntimeC`): exigen
  `nucleo/quantum_runtime.o`, `nucleo/quantum_memory.o`,
  `nucleo/quantum_err_corr.o` — las FUENTES existen; nadie construye los .o.
- **18 RED TDD re-clasificados (hallazgo H-R181-3):** los 15 de federated
  (`test_federated_adv_10.py`/`test_federated_exec_10.py`) fallan por tipos
  `int`/`puntero` en el semántico con `std/federated.syn` presente (firma real
  `fed_iniciar(pesos: puntero, ...)` vs test que pasa `0` literal); los RED de
  ai/build/distribución/release/vscode son `pytest.fail` incondicional
  (feature gaps declarados → cola R182). NO son deuda de harness: se excluyen
  de este ME y se documentan.

## Plan (bloque MTS estricto)

requisito: Manual 9 §6.2 — "La suite de tests completa en cada target" debe
ejecutarse en CI reproducible; los artefactos del entorno (.o del runtime,
includes de raíz) se construyen/resuelven solos. Manual 1 §3.2 — el pipeline
genera binario ejecutable. Manual 8 §4 — CLI unificado; el harness usa el
mismo resolver de toolchain canónico (toolchain_gcc12) que el conftest ya usa
para los .o del runtime.
texto: M9 §6.2 L560: "La suite de tests completa en cada target."; M1 §3.2:
pipeline completo compila → linkea → ejecuta.
implementacion:
  1. `tests/conftest.py` (HARNESS, tests NO se tocan): (a) exportar `CPATH`
     hacia la raíz del repo en el fixture autouse — gcc lo honra para
     `#include "..."` sin tocar ningún comando de test (probado: resuelve
     `librerias/embedded_libs.h` y `ffi_marshaling.h`, este último rompía el
     propio auto-compilador del conftest); (b) lista separada
     `_QUANTUM_OBJS_R181` = [("nucleo/quantum_runtime.o", "nucleo/
     quantum_runtime.c"), ("nucleo/quantum_memory.o", ...),
     ("nucleo/quantum_err_corr.o", ...)] compilada on-demand en el fixture
     autouse (paso 1b). DESVIACIÓN DEL PLAN INICIAL justificada: NO entra en
     `_RT_OBJ_DEFS` porque `nm -u` muestra dependencias libm
     (sincos/sqrt/exp/fmax) y meterlos en rt_objs() ampliaría el conjunto de
     enlace de TODOS los tests que lo usan sin -lm (p.ej.
     test_toml_raii.py) — riesgo de undefined reference regresivo. Los tests
     quantum solo exigen que los .o EXISTAN (os.path.exists), no los enlazan.
  2. `compilador/generator/generator.py` (paridad con el nativo): tras los
     externs del prólogo emitir definiciones `__attribute__((weak))` (solo
     `#if defined(__GNUC__)`) de pool_init/pool_free/pool_alloc/pool_destroy/
     synapse_esperar_hilos/synapse_esperar_fibras/_simd_detectar con defaults
     inocuos (pool_alloc→malloc/free) — el binario del generador S1 enlaza
     standalone; si se enlaza con el runtime completo, los símbolos fuertes de
     runtime/core/*.c prevalecen (semántica weak de GCC). Probado: hola rc=42,
     coincidir rc=42 standalone.
  3. `nucleo/generador/orquestador.syn` (paridad M1 §3.1 con generator.py):
     mismo shim débil tras los externs (orquestador.syn L423-490).
     **H-R180-2: rebuild generator.syn via `nucleo/_rebuild_generator.py` y
     re-bootstrapear S1→S2.**
oraculo: tests/auditoria/test_oraculos_harness_gcc.py — 5/5 GREEN (r1 CPATH
resuelve include de raíz standalone; r2 hola/coincidir generados standalone
ejecutan rc=42 por exit code; r3 los 3 .o quantum existen on-demand; r4
paridad del shim weak S1↔nativo). Validación adicional en sesión:
test_toml_compile_and_run llega a EJECUTAR (fallo restante funcional
H-R181-1, no de harness); bootstrap S1→S2→S3 rc=0 con stage2==stage3
byte-idénticos (sha256 c2889554…); regresión (unit + matriz + fase2 -k r11)
sin cambios; TestEjecucionReal 5 GREEN / 2 RED por deudas reales
(H-R181-3/H-R181-4).
impacto: 6 link-real pasan su fase de compilación (7 e2e alcanzan ejecución),
3 quantum pasan; 18 RED re-clasificados con hallazgo. Tests NO se tocan.

## Desviaciones registradas durante la implementación (2026-10-05)

- **H-R181-2 (MTO, modificación de aserciones en
  tests/integration/test_e2e_adv_10.py::TestEjecucionReal):** al quedar el
  harness reparado, los 6 tests de ejecución exponen una capa de aserción
  STALE: exigen `rc == 0` + `"<valor>" in stdout`, convención escrita en
  8f3f15b (2026-08-24, aspiracional) que NUNCA se implementó (el main nunca
  imprimió el retorno: verificado en git show 1c1044c — el código previo
  también descartaba el retorno). La convención vigente y RATIFICADA es
  1c1044c (2026-09-02, posterior a R98/d47d400-2026-08-25): "exit code =
  retorno de principal()". Bajo el mandato del Arquitecto ("si el código
  está alineado y el test no, se modifica el test aplicando TDD y MTO") las
  7 aserciones de TestEjecucionReal migran a `assert rc == <valor esperado>`
  (42/42/5/55/720/25/42), canal ratificado y MÁS preciso (verifica el valor
  real). RED quedan: test_programa_si_sino_ejecuta y
  test_programa_estructura_ejecuta por causas REALES documentadas abajo.
- **H-R181-4 (RED asignado):** `test_programa_si_sino_ejecuta` — el C
  generado declara `int64_t abs(int64_t x);` (prototipo de función de
  usuario `abs`) en conflicto con `int abs(int)` de stdlib.h (incluido
  incondicionalmente). Colisión de nombres usuario-vs-stdlib en el generador
  (afecta a cualquier función llamada min/max/abs/exit...). Resolución: ME
  futuro (espaciado de nombres o no-emisión de prototipos innecesarios).
  El test queda con la aserción correcta (`rc == 5`) para el contrato
  ratificado; su RED es el bug, no la aserción.
- **H-R181-3 (RED asignado, ya en R181 diagnóstico):**
  `  test_programa_estructura_ejecuta` — `y` es keyword AND del lexer S1
  (lexer.py L21) y `crear_punto(x: entero, y: entero)` no se parsea.
  Deuda lexer/parser, NO harness. Resolución: ME futuro.
- **H-R181-1 (RED asignado, no-harness):** `test_toml_compile_and_run`
  ahora COMPILA Y ENLAZA (CPATH + shim débil) pero el exe falla en runtime
  (salida vacía / segfault 0xC0000005 con toolchain canónico): deuda
  funcional RAII/toml. Resolución: ME futuro.
- **H-R181-5 (cita fantasma):** generator.py L1611 cita "Manual 2 §5 e2e"
  como respaldo del exit code — M2 §5 es Contratos Lógicos; la fuente real
  de la decisión es el commit 1c1044c. Corregido el comentario en este ME.
- **Guard GNUC:** el plan pedía `#if defined(__GNUC__)` alrededor del shim;
  implementado en ambos generadores (emisión idéntica, paridad),
  re-rebuild + re-bootstrap verificado (stage2==stage3 sha256 c2889554…).
