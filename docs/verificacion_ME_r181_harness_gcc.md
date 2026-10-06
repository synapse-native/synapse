# Verificación ME r181_harness_gcc (R181) — H-R176-1

**Base:** c5118f5 (R180). **Commit:** (post-commit). **Método:** MTS + TDD + MTO.

## Marcas por requisito

- Manual 9 §6.2 R1 el entorno de la suite resuelve solo sus artefactos (includes de raíz y .o del runtime) sin tocar ningún comando de test: `tests/conftest.py` exporta `CPATH` hacia la raíz del repo (mecanismo canónico de gcc por entorno; raíz al frente, separador `;` en win32) y añade la lista separada `_QUANTUM_OBJS_R181` compilada on-demand en el fixture autouse (paso 1b) (evidencia tests/conftest.py:20, tests/conftest.py:147, tests/conftest.py:333, oráculo tests/auditoria/test_oraculos_harness_gcc.py r1 CPATH standalone y r4 .o quantum): CUMPLE
  - Desviación del plan inicial justificada: los .o quantum NO entran en `_RT_OBJ_DEFS` — `nm -u` muestra dependencias libm (sincos/sqrt/exp/fmax) y meterlos en `rt_objs()` ampliaría el conjunto de enlace de TODOS los tests que lo usan sin `-lm` (p.ej. test_toml_raii.py), riesgo regresivo. Los tests quantum solo exigen existencia (`os.path.exists`), no enlazan los .o.

- Manual 2 §5.1 R2 el prólogo de `main` evalúa sus contratos con símbolos resolvibles en compilación de UN solo archivo: `compilador/generator/generator.py` emite shim weak (`#if defined(__GNUC__)` + `__attribute__((weak))`) de pool_init/pool_alloc/pool_free/pool_destroy/synapse_esperar_hilos/synapse_esperar_fibras/_simd_detectar tras los externs y antes de `emit_contract_header`; semántica weak de GCC: las definiciones fuertes del runtime completo prevalecen si se enlaza (evidencia compilador/generator/generator.py:1108, oráculo test_oraculos_harness_gcc.py r2 hola rc=42 y r3 coincidir rc=42 standalone): CUMPLE

- Manual 2 §5.1 R3 paridad S1↔nativo del shim: `nucleo/generador/orquestador.syn` espejo exacto (mismas líneas emitidas) + H-R180-2 rebuild de `nucleo/generator.syn` via `nucleo/_rebuild_generator.py` (evidencia nucleo/generador/orquestador.syn:492, nucleo/generator.syn:5057, oráculo test_oraculos_harness_gcc.py r5 paridad de emisión S1↔nativo): CUMPLE

- Manual 8 §4 R4 el harness usa el mismo resolver de toolchain canónico que el resto de la suite (sin comandos gcc ad-hoc): la compilación on-demand de quantum reutiliza el resolver/flags del conftest y el oráculo valida el resolver canónico `cli._resolver_gcc` (evidencia tests/auditoria/test_oraculos_harness_gcc.py r1): CUMPLE

- Manual 9 §6.2 R5 oráculo E2E del harness verded: `tests/auditoria/test_oraculos_harness_gcc.py` 5/5 GREEN (r1 CPATH resuelve include de raíz standalone con gcc -c; r2 hola standalone rc=42; r3 coincidir rc=42; r4 los 3 .o quantum existen on-demand; r5 paridad del shim S1↔nativo): CUMPLE

## Bootstrap y regresión ejecutada

- **LECCIÓN HEREDADA (H-R180-2):** `nucleo/generador/orquestador.syn` se concatena en `nucleo/generator.syn` via `python nucleo/_rebuild_generator.py`; rebuild SIEMPRE antes de bootstrapear. Rebuild ejecutado (395901 chars, 5505 líneas).
- Bootstrap final: re-ejecución completa S1→S2→S3 sobre el contenido final (incluye las últimas ediciones de comentarios del 20:37–20:38; los exes previos eran stale — regla "un exe stale parece éxito y no lo es"). S1/S2/S3 rc=0; stage2==stage3 sha256 `c2889554b47db3c2227f3c4cbda087cbc6995f400a22007692efeda573c91d43` (idéntico al sello previo: las ediciones de comentarios no alteran el C). `scripts/bootstrap.sh` NO se usa (bug preexistente ROOT_DIR, deuda aparte).
- Oráculo propio: 5/5 GREEN (`tests/auditoria/test_oraculos_harness_gcc.py`).
- Regresión ejecutada: unit **514 passed** (307 s); micro_bootstrap+nucleo+synapse **30 passed** (148 s); matriz `tests/auditoria/test_matriz_compilacion.py` **35 passed** (69 s); fase2 `-k r11` **5 passed** (316.62 s); quantum **8/8 PASSED** (antes 3 fallos por .o ausentes); TestEjecucionReal **5 passed / 2 failed** (RED por deudas reales H-R181-3/H-R181-4, aserciones migradas via MTO).
- Gates MTS: `alineacion --verificar --me r181_harness_gcc` PASS (cambio_hash `940ab0dead0a47ff`, evidencia auditoria/evidencia/940ab0dead0a47ff.json); `contrastar --plan docs/plan_ME_r181_harness_gcc.md` TODO PASA (oráculo ejecutado con >0 collected y sin SKIP; citas válidas); `verificar_alineacion.py` SIN BRECHAS.

## Hallazgos del ME

- **H-R181-1 (RED asignado, no-harness):** `test_toml_compile_and_run` ahora COMPILA Y ENLAZA (CPATH + shim débil) pero el exe falla en runtime (salida vacía / segfault 0xC0000005): deuda funcional RAII/toml. Resolución: ME futuro.
- **H-R181-2 (cerrado en este ME, MTO):** las 7 aserciones de `TestEjecucionReal` exigían `rc==0` + valor en stdout (convención aspiracional de 8f3f15b/2026-08-24 NUNCA implementada). La convención ratificada es 1c1044c (2026-09-02): "exit code = retorno de principal()". Migradas a `assert rc == <valor>` (42/42/5/55/720/25/42).
- **H-R181-3 (RED asignado):** `y` es keyword AND del lexer S1 (lexer.py L21): `crear_punto(x: entero, y: entero)` no parsea. Deuda lexer/parser → ME futuro.
- **H-R181-4 (RED asignado):** el C generado declara `int64_t abs(int64_t)` en conflicto con `int abs(int)` de stdlib.h incluida incondicionalmente (afecta cualquier función usuario llamada abs/min/max/exit...). Colisión nombres usuario-vs-stdlib en el generador → ME futuro. El test conserva la aserción correcta (`rc == 5`); su RED es el bug, no la aserción.
- **H-R181-5 (cerrado en este ME):** cita fantasma generator.py L~1611 ("Manual 2 §5 e2e", M2 §5 es Contratos Lógicos) corregida a "Decisión ratificada 1c1044c (H-R181-5)".

## Deuda bloqueada restante (decisión Arquitecto)

- H-R181-1 (toml/RAII runtime), H-R181-3 (lexer 'y'), H-R181-4 (colisión stdlib en generador): filas nuevas en `docs/plan_maestro_deudas.md` con ME asignado; NO se reintentan en R181.
- Los 18 RED re-clasificados del diagnóstico (15 federated por firma real `fed_iniciar(puntero,...)` vs literal 0; ai/build/distribución/release/vscode por `pytest.fail` declarados) van a R182 feature gaps, fuera de este ME.
