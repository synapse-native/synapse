# Plan ME coverage_aristas — Fase 33.2: --coverage con instrumentación de aristas (H-R152-1)

**Fuente:** ROADMAP.md §33.2 (2026-09-26). **Base:** 22f7562.
**Alcance:** instrumentación de aristas generada por el compilador en AMBAS capas
(S1 Python + nativo), runtime que registra aristas y vuelca JSON, informe HTML
real desde `synapse test --coverage` (fin del rc=1 honesto de H-R152-1).

## R1 — Runtime: registro y volcado de aristas (runtime/core/coverage.c NUEVO)
requisito: Manual 9 §6.1
texto: "synapse test --coverage` genera informes de cobertura" (M9 §6.1 — checklist
DoD Fase 31: las herramientas nativas generan informes de cobertura).
implementacion: `runtime/core/coverage.c` (NUEVO) + `runtime/core/coverage.h`:
contador global `int _syn_cov_habilitado` (ON por `SYNAPSE_COVERAGE=1`, activado
por constructor GCC `__attribute__((constructor))`), buffer de aristas
`{archivo, linea, destino}` como enteros internados (punteros a literales/estáticos
vivos del programa — sin gestión propia), dedup con búsqueda lineal (los programas
de test son pequeños; el patrón de trace-lifetime ya existe en debug.c), volcado
JSON `{aristas:[{a:LINEA,b:LINEA}], total_aristas:N}` a `<salida>.coverage.json`
vía `atexit` + hook en los manejadores de error del runtime (patrón
ESCAPA_DEL_ALCANCE). Registrado en `synapse_rt_types.h` o su propio header
incluido por los probes: los `.o` se enlazan AUTOMÁTICAMENTE (glob
`runtime/core/*.c` en pipeline.py, D-9(d) regla 13 — sin hardcoding, paridad
S1/nativo garantizada).
// cumple Manual 9 §6.1
oraculo: tests/auditoria/test_oraculos_coverage.py

## R2 — Emisor S1: bandera y sondas en los saltos de control
requisito: Manual 8 §4.2
texto: "Genera informe de cobertura en HTML en `synapse test`" (M8 §4.2 tabla de
flags: --coverage pertenece al CLI unificado).
implementacion: `compilador/generator/context.py`: `enable_coverage_mode()` +
`_coverage_on` + `_coverage_file` (nombre de archivo del FUENTE en
compilación). `compilador/generator/generator.py`: si coverage, registrar
atexit ANTES de pool_init en `main()` y prototipo de las 2 API en el header
común. `compilador/generator/emit_control.py`: en cada `si/sino` (después de
evaluar condición, ambos brazos), `mientras`, `para` (rango), `para-en` y
`coincidir` (cada caso): emitir `SYN_COV(l, d);` — macro prototipada en el
header común. `pipeline.py`: propagar `SYNAPSE_COVERAGE=1` desde `cli.py` hacia
GeneradorC (`enable_coverage_mode(ruta_fuente)`), OFF por defecto (bootstrap
determinista intacto). `cli.py`: `--coverage` del CLI Python configura el
generador (M8 §4.2).
// cumple Manual 8 §4.2
oraculo: tests/auditoria/test_oraculos_coverage.py

## R3 — Emisor NATIVO: sondas paritarias (generator.syn, UNITY regenerado)
requisito: Manual 1 §6
texto: "**Regla de hierro:** Ninguna característica nueva puede romper el
*bootstrap* (etapas 0→1→2→3 con diff binario 0)." — la paridad S1↔nativo se
verifica con el bootstrap apagado por defecto; el oráculo re-verifica el diff.
implementacion: `nucleo/generador/nodos_flujo.syn`: en emitir_si/sino,
mientras, para, para-en, coincidir: emitir `SYN_COV(l, d);` en el mismo orden
que el S1 (paridad de formato de volcado). Bandera: `SYNAPSE_COVERAGE=1` leída
por getenv en el compilador nativo; al estar OFF el C emitido es byte-idéntico
(sin ramas nuevas). REGENERAR `nucleo/generator.syn` con
`python nucleo/_rebuild_generator.py` tras editar. `nucleo/principal.syn`:
`generar_etapa` reenvía el entorno (heredado por system()).
// cumple Manual 1 §6
oraculo: tests/auditoria/test_oraculos_coverage.py

## R4 — cli_test --coverage: JSON → HTML con % de aristas (fin de H-R152-1)
requisito: Manual 9 §6.2; Manual 8 §4.2
texto: "`synapse test --junit --coverage` para generar reportes de tests y
cobertura" (M9 §6.2 — validación cruzada CI/CD Fase 31).
implementacion: `nucleo/coverage.syn` (NUEVO, importado por nucleo/principal.syn):
1) `coverage_leer_json(ruta)` — parser mínimo de líneas "a":N,"b":N SIN depender
de std/json (principal.syn compila sin std en bootstrap; lectura/parseo con
inseguro fread; retorno: cadena formateada de pares a|b). 2)
`coverage_generar_html(ruta_fuente, ruta_json, total_estimado)` — suma pares
únicos (aristas cubiertas), compara contra aristas ESTÁTICAS contadas del
fuente `.syn` (número de if/while/para/casos — escaneo texto inseguro strstr),
HTML con h1 Coverage, % de aristas cubiertas y LISTA de aristas no ejecutadas
(extiende generar_coverage de reports.syn, que hoy solo recibe contadores —
se mantiene intacta para OBL-M8-15).
// cumple Manual 9 §6.2
// cumple Manual 8 §4.2
oraculo: tests/auditoria/test_oraculos_coverage.py

## R5 — Cableado cli_test + volcado en error
requisito: Manual 9 §6.1
texto: "synapse test --coverage` genera informes de cobertura" (M9 §6.1).
implementacion: `nucleo/principal.syn` `cli_test`: formato==3 deja de responder
rc=1: (1) instrumenta (generar_etapa con SYNAPSE_COVERAGE=1), (2) ejecuta el
exe, (3) `coverage_generar_html` consume el JSON y escribe `<fuente>.coverage.html`
con escribir_reporte, (4) rc=0 con instrumentación+ejecución exitosas (fin del
rc=1 honesto de H-R152-1).
// cumple Manual 9 §6.1
oraculo: tests/auditoria/test_oraculos_coverage.py

## R6 — Oráculo del ME
requisito: Manual 2 §12
texto: "| Coverage | `pytest tests/integration/test_coverage.py -v` | Genera informe de cobertura |" (M2 §12 — pruebas obligatorias de la etapa; el oráculo del
ME añade la verificación E2E de aristas reales).
implementacion: `tests/auditoria/test_oraculos_coverage.py` (NUEVO): E2E —
compila probe .syn con ramas tomadas/no-tomadas via subprocess main.py
(SYNAPSE_COVERAGE=1), ejecuta el exe, verifica: JSON existe con aristas,
HTML existe con h1 Coverage + %, aristas NO ejecutadas listadas, rc=0; y
regresión: el mismo probe compilado SIN la bandera emite C sin SYN_COV
(bootstrap determinista); envoltorio `auditar_calidad_tests --solo-mto` (lección
R160: jamás el full-scan como oráculo directo). Tests inmutables intactos:
test_coverage.py (OBL-M8-15) y su fixture reports.syn/principal.syn NO cambian
de comportamiento observable.
// cumple Manual 2 §12
oraculo: tests/auditoria/test_oraculos_coverage.py

## Archivos a modificar
- runtime/core/coverage.c, runtime/core/coverage.h (R1 — NUEVOS)
- compilador/generator/context.py, generator.py, emit_control.py (R2)
- pipeline.py, cli.py (R2)
- nucleo/generador/nodos_flujo.syn + nucleo/generator.syn regenerado (R3)
- nucleo/coverage.syn (R4 — NUEVO) + nucleo/principal.syn (R4/R5)
- tests/auditoria/test_oraculos_coverage.py (R6 — NUEVO)

## Notas de riesgo
- Bandera OFF por defecto: el C emitido sin --coverage es byte-idéntico →
  bootstrap determinista intacto; el oráculo re-verifica diff.
- El volcado atexit corre a salida limpia; los errores del runtime no vuelcan
  (aceptable para el alcance de R1 — el probe del oráculo termina limpio).
- coverage.syn usa parser JSON mínimo propio (sin std/json) para no añadir
  dependencias al bootstrap nativo.
- El ejecutable instrumentado sigue determinista: las sondas solo registran
  aristas en memoria, el volcado es al final.
