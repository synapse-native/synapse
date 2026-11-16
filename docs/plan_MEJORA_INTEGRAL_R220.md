# Plan integral de continuidad post-R219 (R220+)

**Fecha:** 2026-11-13 - **Base:** 33320c9 (R219) - **Mandato:** "crea un plan
que cubra todo, trabaja con ME y asegurate de que todo este alineado, y
funcional".

**Regla de direccion:** cada ME se ejecuta con MTS, cita manual en el plan y en
el codigo de produccion, oraculo ejecutable, gates y reporte post-commit. Los
tests existentes no se modifican sin aprobacion explicita del Arquitecto.

## Baseline verificado en esta sesion

- `build.py` completo: bootstrap S1->S2->S3 rc=0; Stage 2 == Stage 3
  (`5FA2C432E2998036D629123B6E93567D2428F397DA1C20192D4AF5F425A97288`).
- LSP/IA (`nucleo/lsp_v3.syn`): 11 tests reales GREEN; 5 skips TDD obsoletos en
  `tests/integration/test_ai_commands_opensyn.py`.
- Fallos de integracion sin toolchain en PATH: los binarios de test terminan con
  `3221225595` / `-1073741701` porque no encuentran `libwinpthread-1.dll`.
  Con `toolchain_gcc12\mingw64\bin` al frente de PATH: 19/19 en
  axon/binario_real/canales/cache y 38/38 en cluster (el timeout de handshake
  no se reprodujo en la corrida de cierre de R220).
- Warning resuelto en R220: `test_ffi_marshaling_auto.c` ya resuelve
  `ffi_marshaling.h` con `-I runtime/core` dirigido; 11/11 GREEN.
- Release: `test_build_py.py` 2/2 y `test_release_unificado.py` GREEN tras
  refrescar la distribucion stale con `distribuir.py` (firma verificada).
- La suite `tests/integration` completa no tiene baseline: el run se corto por
  timeout de herramienta (~25% de 1628 tests recolectados).

## Cola de MEs

### R220 - Harness runtime PATH/CPATH (IMPLEMENTADO 2026-11-14)

- Objetivo: que el harness de tests resuelva solo el toolchain canonico
  (`toolchain_gcc12`) y los headers de `runtime/core`, sin tocar comandos de
  test ni tests inmutables.
- Cambios: `tests/conftest.py` (PATH + include dirigido para FFI), oraculo nuevo
  `tests/auditoria/test_oraculos_r220_harness_runtime_path.py`.
- Cierre: subsets afectados GREEN (15+4+38+11), oraculo 4/4, gates MTS verdes.
  Commit y docs post-commit pendientes.

### R221 - Baseline por bloques y triage (EN CURSO)

- Objetivo: obtener baseline sin depender de un unico run de 40 min.
- Resultado actual: `tests/unit` + `tests/syquex` = 796 tests, 795 passed,
  1 skipped, 0 failed. Integration dirigida: 57 GREEN; build/release 3 GREEN.
- Los 13 RED originales quedaron cerrados por R222 (3 contratos) y R223
  (10 Syquex). No se modifico ningun test.
- `tests/auditoria`: 230 tests; el run completo excede 30 min. Subset fallido
  (19 tests) dejo 6 RED ambientales/prexistentes: `synapse.exe` stale por un
  `_tmp_ast_abi_drv.syn` temporal, `dist/bin/opensyn.exe` anterior a
  `opensyn/principal.syn`, chat OpenSyn sin `modelo_synapse.gguf`, y el
  contrato de `std/io.syn::stdin_eof` que el test busca como `resultado` pero
  el codigo escribe `_resultado_`. Asignados a R226/R228.
- Pendiente: baseline de `tests/integration` completa.

### R222 - Contratos std/texto (IMPLEMENTADO 2026-11-14)

- Objetivo: cerrar los 3 RED de `test_std_contracts.py` con contratos
  semanticamente correctos del Manual 2 §5/§12; si el test esta desalineado,
  detenerse y pedir aprobacion (regla 5).
- Resultado: 7 envoltorios historicos restaurados con contratos y
  `requiere: verdadero` en `contiene` (sin revertir H-R196-1). Contratos 20/20;
  oraculo `test_oraculos_r222_std_texto.py` 4/4; gates PASS.
- Deuda H-R222-3: duplicados de `contiene`/`indice_de`/`reemplazar` para R228.

### R223 - Syquex Canal/Resultado/intentar (IMPLEMENTADO 2026-11-14)

- Objetivo: reparar el frontend Syquex para aceptar `Canal<T>`, `Resultado<T,E>`,
  `intentar/atrapar` y `?` segun Manual 3 §7-§8.
- Causa raiz: `importar std` sin punto leia `est->nodos[sub]` con `sub` sin
  inicializar; `T_CANAL` no era primario y `sq_args(est, -1)` escribia
  `est->nodos[-1]`.
- Resultado: `test_concurrency.py` 5/5 y `test_result.py` 5/5; gates PASS.
- No se modificaron los tests: son la especificacion TDD.

### R224 - Deuda LSP/IA y skips TDD obsoletos

- Objetivo: retirar los 5 skips de `test_ai_commands_opensyn.py` solo con
  autorizacion explicita (regla 5), o reemplazarlos por E2E contra el binario
  nativo que ya dispatcha `synapse ai*`.
- Verificar `aiStatus/aiExplain/aiComplete/aiFix/aiTranspile/aiBindings` por
  CLI y LSP, no solo por tests unitarios.

### R225 - OpenSyn nativo y sesiones

- Objetivo: cerrar la deuda historica de `synapse opensyn` (R149): evaluar
  dispatch nativo de `status/download/finetune/bindings/transpile` y sesiones
  persistentes.
- Priorizar paridad CLI y errores claros; no inventar APIs no documentadas.

### R226 - Release, CI y secretos

- Objetivo: verificar `release`/CI sin depender de secretos locales.
- Documentar que pasos requieren credenciales; dejar el resto reproducible.
- No introducir secretos ni cambiar firmas/flags sin manual.
- Baseline R221: `synapse.exe` queda stale frente a `nucleo/_tmp_ast_abi_drv.syn`
  (archivo temporal de un oraculo) y `dist/bin/opensyn.exe` es anterior a
  `opensyn/principal.syn`; regenerar ambos como parte de release y limpiar el
  temporal que enmascara la frescura.

### R227 - LLM real y E2E de comportamiento

- Objetivo: prueba real con `llama-server` cuando el entorno lo permita;
  degradacion controlada y mensajes verificables cuando no.
- Agregar oraculos de comportamiento (no solo presencia de simbolos).
- Baseline R221: los E2E de chat (`test_oraculos_eof_cierre.py`,
  `test_oraculos_eof_runtime.py`) fallan sin `modelo_synapse.gguf`; el oraculo
  debe separar "sin modelo" de una regresion de EOF.

### R228 - Barrido de deuda cero

- Objetivo: revisar `docs/plan_maestro_deudas.md`, `docs/reportes/` y
  hallazgos H-*; cerrar o asignar resolucion a cada uno.
- Actualizar `MEMORIA_PROYECTO.md`, roadmap y reporte final de fase.
- H-R222-3: eliminar las definiciones duplicadas de
  `contiene`/`indice_de`/`reemplazar` en `std/texto.syn` (posteriores a
  `importar std.sistema`) o documentar por que se conservan.
- Alinear `tests/auditoria/test_oraculos_eof_runtime.py` con el contrato real
  `_resultado_` de `std/io.syn::stdin_eof` (el test busca `resultado`).

## Fuera de alcance / ya verificado

- WASM Fase 25: tests dirigidos verdes.
- Federated/quantum: tests dirigidos verdes.
- Handlers IA LSP: implementados en `nucleo/lsp_v3.syn`; la evaluacion
  `EVALUACION_AVANCE_2026-11-08.md` esta parcialmente obsoleta.
- H-R90-5: resuelto (handsake reversible).
- Fase 32: modulos presentes; no se reabre sin evidencia nueva.

## Criterio de cierre de la continuidad

1. `build.py` con S2==S3 fresco.
2. Suite completa ejecutable sin fallos inexplicados; skips solo de
   infraestructura documentada.
3. `verificar_alineacion.py` sin brechas y `contrastar.py` RC=0 en cada ME.
4. Cada ME con plan, expediente, evidencia, verificacion, reporte y memoria.
5. Cero deuda nueva sin fila de seguimiento con resolucion asignada.
