# Verificación ME check_cli — H-R176-2 (`synapse check`)

Fecha: 2026-10-03 · Verificador: `auditoria/contrastar.py` (gate MTS fase 4b)
Base: 4ebd025 (R177). Oráculo: `tests/auditoria/test_oraculos_check_cli.py` —
**GREEN 4/4** (E2E real: stage2 del bootstrap, cli.py, binario synapse.exe,
y el test de integración inmutable test_cli_check 3/3).
Cambio: el subcomando `check --no-emit` (M8 §4.2) implementado en el
dispatcher nativo (`nucleo/principal.syn`), paridad Python (`cli.py`, M8 §4.1)
y binario `synapse` (M8 §4). Cierra los 3 fallos
"Binario synapse no encontrado — implementar CLI (M8 §4)" de
`tests/integration/test_cli_check.py` (test inmutable, deuda del código).

## R1 — Manual 8 §4.2 (modo de validación sin generar código) — CUMPLE
`nucleo/principal.syn`: subcomando `check` en `principal()` (parseo de flags
`--no-emit/--release/--debug/--safe`, primera ruta no-flag, patrón
cli_lint/cli_fmt H-33.5-2) + `cli_check()` delega en `generar_etapa(ruta,
ruta, 1)`; el tercer parámetro `modo_validar` corta el pipeline tras el
análisis semántico (F8) — NUNCA genera C, invoca gcc ni escribe salida
(oráculo r1: válido rc=0 `[Check] validacion exitosa`, inválido rc=1
`[Check] ERROR de validacion`, sin `<probe>.exe` ni `synapse_unity.c`).

## R2 — Manual 8 §4.1 (subcomando del CLI unificado, backend nativo) — CUMPLE
`cli.py`: `check` en la detección de subcomandos →
`_cmd_herramienta_nativa('check', ...)` (backend stage2 del bootstrap con
backing on-demand, patrón R166); rc del backend propagado (oráculo r2:
paridad de rc en válido/inválido).

## R3 — Manual 8 §4 (CLI unificado `synapse`) — CUMPLE
`synapse.exe` = copia byte-idéntica del stage2 (mismo compilador; el runtime
se resuelve junto al exe por GetModuleFileNameA; main de biblioteca sin
efecto colateral, D-R150-4); artefacto ignorado por git (.gitignore) que el
entorno de release despliega (oráculo r3: `synapse check --no-emit` rc=0/1
correctos, sin binario de salida).

## R4 — Manual 2 §12 (pruebas obligatorias de la etapa) — CUMPLE
Oráculo E2E 4/4 GREEN + test inmutable `tests/integration/test_cli_check.py`
3/3 PASSED (antes 3 FAILED "implementar CLI (M8 §4)"). Ancla MTO:
OBL-M8-16 | Manual 8 §9 | Flag --check del CLI | integración | GREEN.

## Regresión (verificación global del ME)
- unit 514✓ (4:47) · micro_bootstrap+nucleo+synapse 30✓ (2:25) ·
  matriz 35✓ + oráculo cli_lint_fmt 6✓ (2:32) · MTO --solo-mto OK.
- Bootstrap S1→S2 reconstruido con el cambio (rc=0/rc=0); synapse.exe fresco.
- `auditoria/verificar_alineacion.py`: 0 brechas (gate contrastar).
