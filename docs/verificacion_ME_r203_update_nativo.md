# Verificación ME r203 — `synapse update` nativo

Detalle: `docs/plans/verifications/verificacion_ME_r203_update_nativo.md`.
Plan: `docs/plan_ME_r203_update_nativo.md`.
Expediente: `docs/alineacion/r203_update_nativo.md`.

- Manual 9 §3.1 sin argumentos actualiza a la última versión — CUMPLE (`nucleo/actualizador.syn:351`).
- Manual 9 §3.1 `--version <version>` actualiza a una versión específica — CUMPLE (`nucleo/actualizador.syn:346`).
- Manual 9 §3.1 `--check` solo consulta, no instala — CUMPLE (`nucleo/actualizador.syn:363`).
- Manual 9 §3.2 verificación de versión contra GitHub Releases — CUMPLE (`nucleo/actualizador.syn:329`).
- Manual 9 §3.2 descarga del asset con transporte TLS — CUMPLE (`nucleo/actualizador.syn:242`).
- Manual 9 §3.2 verificación de firma Ed25519 — CUMPLE (`runtime/core/actualizador.c:156`).
- Manual 9 §3.2 backup en `~/.synapse/backup/` — CUMPLE (`runtime/core/actualizador.c:246`).
- Manual 9 §3.2 instalación/reemplazo de binarios — CUMPLE (`runtime/core/actualizador.c:340`).
- Manual 9 §4.1 `.sig` y `.sha256` obligatorios por release — CUMPLE (`nucleo/actualizador.syn:343`).
- Manual 2 §5.1 contratos `requiere`/`garantiza` — CUMPLE (`nucleo/actualizador.syn:317`).

Oráculo: `tests/integration/test_update_nativo.py` → 10 passed.
