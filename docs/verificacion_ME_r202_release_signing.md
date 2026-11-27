# Verificación ME r202_release_signing — release firmado real

Fecha: 2026-11-06 · Verificador: `auditoria/contrastar.py` (gate MTS fase 4b)
Oráculos: `test_auto_actualizar_firma.py` (9), `test_firma.py` (5),
`test_artifact_signing.py` (35), `test_release_matrix.py` (24),
`test_distribucion.py` (1) — todos PASS.
Alcance: firma Ed25519 de artefactos, verificación fail-closed del actualizador,
workflow de release y claves PEM versionadas (privada solo en Secrets/local).

## R1 — Manual 9 §3.2 (verificación de firma) — CUMPLE
`instaladores/common/auto_actualizar.py:2` cita `cumple Manual 9 §3.2`.
`verificar_version()` expone `url_sig`/`firma_disponible`; el CLI exige el
asset `.sig`, descarga la firma hex, verifica Ed25519 contra
`release_keys/public.pem`, `SYNAPSE_PUBLIC_KEY` o `--clave`, y elimina el
artefacto si la firma no coincide. `obtener_firma_desde_asset()` y
`verificar_firma_actualizacion()` fallan cerrado.
Oráculo: release con/sin `.sig`, firma hex válida/ inválida, PEM/hex y CLI sin
firma PASS.

## R2 — Manual 9 §6.3 (sellado criptográfico) — CUMPLE
`distribuir.py:4` cita `cumple Manual 9 §6.3`.
`distribuir.py --requerir-firma` firma y verifica cada artefacto firmable,
genera `.sig`, `.sha256`, SBOM SPDX, attestation SLSA y firma
`MANIFEST.sha256`. `instaladores/common/verificar_firma.py` firma/verifica PEM,
hex y raw con CLI fail-closed; `scripts/ci_sign.py` usa el mismo verificador.
Oráculo: 35 tests de artifact signing PASS; `distribuir.py --requerir-firma`
genera 19 artefactos y `SIGNATURE_VALID=YES`.

## R3 — Manual 9 §4.1 (GitHub Releases) — CUMPLE
`.github/workflows/release_matrix.yml` construye las 4 plataformas, ejecuta
`distribuir.py --requerir-firma` con `ED25519_PRIVATE_KEY`, verifica cada
`.sig` (`SIGNATURE_VALID=YES`), valida `.sha256`/SBOM/attestation y solo publica
el release en tags `v*`.
Oráculo: 24 tests del workflow PASS (`Sign binary with Ed25519`,
`ED25519_PRIVATE_KEY`, `upload-artifact`, `contents: read`, 4 plataformas).

## R4 — Manual 9 §2.1 (artefactos generados) — CUMPLE
`distribuir.py:3` cita `cumple Manual 9 §2.1-2.5 + §6.3`.
El empaquetado conserva stage2, instaladores y metadatos para Windows, Linux y
macOS, y añade firma/checksum a cada artefacto antes de subirlo.
Oráculo: `test_distribucion.py` PASS.

## R5 — Manual 1 §3.1 (pipeline unificado) — CUMPLE
`instaladores/common/auto_actualizar.py:4` cita `cumple Manual 1 §3.1`.
La herramienta Python del ecosistema verifica el mismo artefacto que produce el
pipeline antes de instalarlo.
Oráculo: 15 tests del actualizador PASS.

## Evidencia ejecutada
- `pytest tests/installers/test_auto_actualizar_firma.py tests/installers/test_auto_actualizar_producto.py tests/installers/test_firma.py tests/integration/test_distribucion.py tests/integration/test_artifact_signing.py tests/integration/test_release_matrix.py -q` — 87 passed.
- `python distribuir.py --requerir-firma` — 19 artefactos, 7 firmas, `SIGNATURE_VALID=YES`.
- `python scripts/ci_sign.py verify instaladores/dist/distribucion/synapse.exe .../synapse.exe.sig .../synapse.pub` — `SIGNATURE_VALID=YES`.
- `contrastar.py --plan r200 --plan r201 --plan r202` — PASS.
- `verificar_alineacion.py` — 0 brechas.
