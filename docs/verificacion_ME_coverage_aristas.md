# Verificación ME coverage_aristas — Fase 33.2 (H-R152-1)

Fecha: 2026-09-27 · Verificador: `auditoria/contrastar.py` (gate MTS fase 4b)
Oráculo: `tests/auditoria/test_oraculos_coverage.py` — **GREEN 4/4**
(2 builds E2E reales vía main.py + ejecución de exes + MTO `--solo-mto`).
Cambio: `--coverage` con instrumentación de aristas en ambas capas (S1 Python
y generador nativo), runtime `runtime/core/coverage.c` que registra aristas y
vuelca JSON, informe HTML desde `nucleo/coverage.syn`, cableado en
`synapse test --coverage` (cli_test formato 3).

## M1 — Manual 9 §6.1 (checklist DoD: bootstrap exitoso diff 0) — CUMPLE
Sin `--coverage` el C emitido es byte-idéntico (bandera OFF por defecto):
oráculo `test_sin_coverage_c_emitido_igual` GREEN; bootstrap S1→S2 regenerado
en esta sesión (stage1/stage2 compilan y enlazan con `coverage.o`).

## M2 — Manual 8 §4.2 (informe de cobertura en HTML en `synapse test`) — CUMPLE
`cli_test` formato 3 en `nucleo/principal.syn:806`: con `--coverage` ejecuta
`covrep_parsear(nombre_base + ".coverage.json")` y `coverage_generar_html` →
`<fuente>.coverage.html`. E2E nativo verificado: JSON `total_estimado:3,
aristas_cubiertas:2` y HTML `Coverage: 66%` + `<li>rama 2</li>`.

## M3 — Manual 1 §6 (regla de hierro: no romper el bootstrap) — CUMPLE
Sondas `_syn_cov(` OFF por defecto en ambas capas (S1 `emit_control.py`,
nativo `nodos_flujo.syn`); sin la bandera ni el runtime ni las sondas alteran
el programa. Oráculo GREEN + stage1/stage2 reconstruidos sin regresión
(test_r3_param_adt 2/2, unit 514 passed).

## M4 — Manual 9 §6.2 (reportes de tests y cobertura para CI/CD) — CUMPLE
JSON de aristas del runtime (`_syn_cov_volcar` atexit) alimenta el informe
HTML (`covrep_parsear` + `coverage_generar_html` en `nucleo/coverage.syn`);
oráculos `test_coverage_json_y_sondas_reales` y `test_coverage_html_desde_json`
GREEN (3 ramas, 2 cubiertas, 1 no cubierta listada).

## M5 — Manual 2 §12 (pruebas obligatorias de la etapa) — CUMPLE
Oráculo del ME en la tabla de pruebas: `pytest tests/auditoria/
test_oraculos_coverage.py` (4/4) + `tests/integration/test_coverage.py` (6/6)
+ MTO `--solo-mto` GREEN (lección R160: envoltorio, no full-scan).
