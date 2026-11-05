# Plan ME-r198b3 — fmt/lint del dispatcher nativo (cierre de H-R198b2-2)

Contexto del barrido r198b2 (docs/reportes/R198b2_barrido.md): la familia
fmt/lint de stage2 queda rota por dos causas raíz y un estado stale:
1. H-CFG-2 (r194) enraiza TODAS las lecturas de `leer_archivo`/`existe_archivo`
   en `_syn_ruta_validar` con contención del cwd → los subcomandos
   fmt/lint/test/check del compilador (nucleo/principal.syn) NO pueden leer
   rutas del Temp (fuera del cwd): `fmt --check Temp/probe.syn` reporta
   "formato correcto" FALSO (vacío==vacío) y `lint Temp/probe.syn`
   "no se pudo leer" (2 tests de la familia).
2. `formatear_texto`/`normalizar_espacios` concentran per-char concat +
   acumulador O(n²): `fmt --check nucleo/generator.syn` excede 120 s →
   timeout de test_nucleo_formateado (H-R198b2-2 clásico, sorteado en r198b2
   porque el archivo skip del test).

Decisiones vigentes respetadas: H-CFG-2 (mandato 2026-10-22) se MANTIENE para
programas de usuario; el dispatcher CLI del compilador es una herramienta de
desarrollo (M8 §4.1) que opera sobre rutas nombradas por el usuario en argv,
y el código usuario NUNCA corre en el proceso del compilador (cli_test ejecuta
el exe compilado como SUBPROCESO) → el escape del sandbox es seguro y acotado.

## Ley citada (MTS: requisito / texto / implementacion / oraculo)

requisito: Manual 7 §7.3 (Pruebas de Privacidad y Seguridad — sandbox con permisos mínimos, sin regresar H-CFG-2)
texto: "Sandboxing: El servidor de inferencia se ejecuta con permisos mínimos."
implementacion: runtime/core/sistema.c añade el modo del sandbox: global `_syn_sandbox_modo = 1` (ESTRICTO por defecto — H-CFG-2 intacto para todo binario de usuario, que nunca llama al setter) y `_syn_sandbox_set(modo)`; `_syn_ruta_validar` salta solo la contención del cwd con `if (_syn_sandbox_modo && ...)`, preservando los asserts estructurales del oráculo r194 (OBL-CFG-194-02: `_syn_ruta_validar(CadenaSegura ruta)`, `_syn_ruta_en_directorio(norm, cwd)`, `// cumple Manual 7 §7.3`). nucleo/principal.syn: cli_lint/cli_fmt/cli_check/cli_test se auto-desactivan la contención con `asm("extern void _syn_sandbox_set(int64_t); _syn_sandbox_set(0);")` (cumple Manual 8 §4.1: el compilador lee las rutas NOMBRADAS por el usuario en argv; el código usuario corre como subproceso, nunca en este proceso).
oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py (lint/fmt Temp/probe.syn + regresión H-CFG-2 del sandbox; el detalle de tests queda en el reporte del ME).

requisito: Manual 6 §3.1 (Declaración de Funciones Externas — `externo`) y Manual 2 §5.1 (contratos: `_resultado_` contiene el valor a retornar)
texto: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
texto: "La variable `_resultado_` contiene el valor que se va a retornar."
implementacion: runtime/core/texto.c + runtime/core/texto.h añaden el builder de texto O(1) amortizado por anexión (`_syn_texto_builder_crear/_anexar/_construir/_liberar`, patrón id-store precedente `_syn_texto_dividir`; contratos requiere/garantiza en comentarios, Manual 2 §12). nucleo/formatter.syn declara los externos y reescribe formatear_texto (slicing por índices de fin de línea + builder, sin `linea_actual` per-char) y normalizar_espacios (builder en lugar de concat per-char); nucleo/lint.syn reescribe lint_fix con el mismo patrón. Complejidad: O(n) amortizado vs O(n²) — elimina el timeout de `fmt --check nucleo/generator.syn`.
oraculo: auditoria/oraculos/oraculo_r198b3_fmt_lint.py (NUEVO) — benchmark `fmt --check nucleo/generator.syn` < 60 s + paridad del resultado del formateo (idempotencia) + regresión tests/auditoria/test_oraculos_formatter_fix.py::test_nucleo_formateado (sin timeout, todos los .syn del nucleo en formato correcto).

## Fuera de alcance (registrar, no abrir ME propio aquí)
- test_oraculos_eof_runtime.py::test_r2_binding_std_io_syn — el test exige el
  substring `resultado == 0 o resultado == 1` en std/io.syn stdin_eof, pero M2
  §5.1 canóniza `_resultado_`: test desalineado del manual → DETENER Y PREGUNTAR
  al Arquitecto (tests inmutables sin ratificación; PREGUNTA en el reporte).
- test_oraculos_r198b1_resello.py::test_resane_end_to_end… — dominio del ME
  r198b1 (resane), se re-ejecuta como regresión para confirmar no-regresión.
- test_oraculos_opensyn_exe.py::test_guard_frescura… y
  test_oraculos_check_cli.py::test_r3_binario_synapse_check — se cierran con la
  REGENERACIÓN de artefactos (paso operativo del ME, no código): stage2 + copia
  synapse.exe + dist/bin/opensyn.exe con mtime > último commit de su fuente.

## Pasos de regeneración (obligatorios, exe stale parece éxito y no lo es)
1. Borrar cachés: `~/.synapse/cache/runtime_obj/*.o`, `nucleo/_*.c*` y
   objetos `.o` raíz del nucleo (el stage2 del 10-29 enlazó el C stale del
   10-05 — lección H-R198b2-2).
2. Regenerar: `python main.py nucleo/principal.syn -o synapse_stage2.exe`;
   copiar a `synapse.exe`; regenerar `dist/bin/opensyn.exe`
   (`python main.py opensyn/principal.syn -o dist/bin/opensyn.exe`).
3. Verificar timestamps > fuentes de nucleo/*.syn y de opensyn/principal.syn.

## Gates (fase 4b: contrastar.py es obligatorio)
- `python auditoria/contrastar.py --plan docs/plan_ME_r198b3_fmt_lint.md`
- `python auditoria/alineacion.py --nuevo --me r198b3_fmt_lint` y `--verificar`
- `python auditoria/verificar_alineacion.py` — 0 brechas
- Regresión ligera: familia fmt/lint + r194 sandbox + check_cli + eof_runtime
  (solo confirmación de no-regresión del conjunto del barrido r198b2).

## No-go / riesgos
- El modo estricto del sandbox es el DEFAULT: cualquier binario compilado por
  main.py/tests de usuario conserva contención del cwd (oráculos r194 deben
  seguir GREEN — si alguno falla, el fix está mal acotado, no se relaja más).
- Los asm de `_syn_sandbox_set` viven SOLO en los 4 cli_* del dispatcher; el
  pipeline de compilación (`synapse <archivo.syn>`) NO toca el flag (misma
  paridad de comportamiento que hoy).
- Tests inmutables: ninguna modificación de tests en este ME.
