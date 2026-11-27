# Plan ME r244 — `lint`/`fmt`/`test` nativos sobre los módulos de Fase 32

**Fase del roadmap:** Ola 4 — paridad nativa (`r244_paridad_lint_fmt_test`).
**Micro-entregable:** `r244_paridad_lint_fmt_test`.
**Depende de:** `r243_native_fase32` (commit `379d978`).
**Alcance:** las herramientas nativas `synapse lint`, `synapse fmt` y `synapse test`
soportan los módulos de Fase 32 (y el propio código del compilador) con el orden
de argumentos que documenta el manual, sin falsos positivos y con paridad
verificable entre el dispatcher Python (`cli.py`) y el binario nativo.

**Defectos medidos antes de codificar** (sobre `release/v8.1.0-industrial`, HEAD
`d447401`):

| # | Comando | Resultado actual | Esperado |
|---|---|---|---|
| D1 | `synapse.exe lint --check opensyn/router.syn` | `[Lint] ERROR: no se pudo leer --check`, rc=1 (el flag se toma como ruta) | lint de la ruta, rc=0 |
| D2 | `synapse.exe lint opensyn/router.syn` | rc=1 con 23 `WARN_LINT_DOUBLE_SPACE` sobre la alineación de comentarios (`//   1. …`) | rc=0: el código del compilador es conforme |
| D3 | `synapse.exe test <programa que importa opensyn/router>` | `synapse_unity.c: error: 'CLOCK_MONOTONIC' undeclared`, rc=1 | compila y ejecuta en el target Windows |

---

requisito: Manual 9 §6.2
texto: "**Nuevo (Fase 31):** `synapse lint --check` sobre el código fuente del compilador para verificar que el linter funciona correctamente."
implementacion: `nucleo/principal.syn` parsea los argumentos de `lint` como flags
  (todo token que empieza por `-` es flag; `--fix` activa la corrección y
  `--check`/otros no) y toma como ruta el primer token que no es flag, de modo
  que la forma canónica `synapse lint --check <archivo>` del manual funciona.
  `nucleo/lint.syn` restringe `lint_doble_espacio` al texto de código
  (corta en el inicio del comentario `//`), porque la alineación dentro de
  comentarios y los comentarios de fin de línea son deliberados: sin esto el
  linter devuelve rc=1 sobre 23 líneas del propio compilador.
oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py

requisito: Manual 8 §4.1
texto: "| **`synapse lint`** (Fase 31) | Ejecuta el linter nativo sobre el código fuente. |"
implementacion: el parser de `lint` acepta el orden canónico (flags antes del
  archivo) y el histórico (archivo antes de los flags) con el mismo resultado:
  la ruta es el primer token sin guion inicial y `--fix` sigue reescribiendo el
  archivo; la regla `WARN_LINT_DOUBLE_SPACE` continúa disparando sobre doble
  espacio real en código (verificado con sonda RED/GREEN en el oráculo).
oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py

requisito: Manual 8 §5.5
texto: "**`synapse fmt`:** El LSP puede ejecutar `synapse fmt --check` para verificar el formato y sugerir correcciones."
implementacion: el parser de `fmt` aplica la misma regla de flags (ningún token
  con guion inicial puede convertirse en la ruta), de modo que
  `synapse fmt --check <archivo>` y `synapse fmt <archivo> --check` coinciden;
  el formateador sigue siendo idempotente y su salida vuelve a compilar.
oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py

requisito: Manual 7 §4.3
texto: "Si el servidor de inferencia no responde en 30 segundos, el LSP devuelve un error al usuario."
implementacion: `opensyn/router.syn` (`ahora_ms_router`) y `opensyn/run_manager.syn`
  (`ahora_ms`) dejan de emitir C solo-POSIX (`clock_gettime(CLOCK_MONOTONIC)` sin
  guarda): el bloque `inseguro` emite `#ifdef _WIN32` con `GetTickCount64` y
  conserva `clock_gettime` en el resto de los targets, asignando a una variable
  local para no saltarse la garantía del contrato. Sin esto, el módulo valida
  con `synapse check` (que no emite C) pero ningún programa que lo importe
  enlaza en Windows: el timeout de 30 s no existe en el binario distribuido.
oraculo: tests/integration/test_paridad_lint_fmt_test_fase32.py
