# Verificación ME r295 — Contratos reales en std/ (Bloque 2)

Fecha: 2026-11-24 · Verificador: `auditoria/contrastar.py` (gate MTS fase 4b)
Oráculo: `auditoria/verificar_contratos.py` — OK: 1022 funciones públicas auditadas, 461 deuda en baseline (0 nuevas), 561 FFI exentas.

## R1 — Manual 2 §5.1 (requiere/garantiza con expresiones booleanas de dominio) — CUMPLE
Archivos modificados: std/modelo.syn, std/surface_code.syn, std/quantum_err_corr.syn, std/simd.syn, std/federated.syn, std/quantum_memory.syn.
Deuda de contratos reducida de 493 a 461 (32 funciones contratadas).
Oráculo `auditoria/verificar_contratos.py` ejecutado en release: rc=0.

## R2 — Manual 2 §12 (contratos obligatorios en funciones públicas) — CUMPLE
Todos los archivos de producción modificados llevan comentario `// cumple Manual X §Y`.
Gate MTS `contrastar.py --plan docs/plan_ME_r295.md`: PASADO.
`alineacion.py --verificar --me r295`: 0 brechas (evidencia `auditoria/evidencia/1e77765005ea1ab5.json`).
`verificar_alineacion.py`: SIN BRECHAS.
