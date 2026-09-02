# REPORTE FASE 11 — Liberación y Distribución (R72/C1)

**Manual referenciado:** Manual 9 §4 (Distribución), §6 (SBOM SPDX), §6.2 (firmas Ed25519), ROADMAP Fase 11.

---

## 1. RESUMEN EJECUTIVO

La Fase 11 del ROADMAP exige generar y firmar los artefactos de release v8.1.0-industrial, validar el workflow de CI y documentar el proceso. Resultado:

| # | Entregable | Estado |
|---|-----------|--------|
| 11.1 | SBOM SPDX 2.3 (`synapse.spdx.json`) | ✅ `generar_sbom()` regenerada — 2025 packages, 2024 files, SHA-256 verificado |
| 11.2 | Checksums SHA-256 (`.sha256`) | ✅ Para SBOM + instalador |
| 11.3 | Firmas Ed25519 (`.sig`) | ✅ Verificables con `release_keys/public.pem` |
| 11.4 | CHANGELOG | ✅ `CHANGELOG_v8.1.0.md` — notas, checksums, hashes S2==S3 |
| 11.5 | Clave de release | ✅ `release_keys/` — Ed25519 RFC 8032, 0 dependencias externas |
| 11.6 | CI release_matrix | ✅ 4 targets, sha256/SBOM/upload-artifact steps validados |

## 2. MATRIZ DE ENTREGABLES (evidencia)

| Entregable | Manual | Estado | Evidencia |
|------------|--------|--------|-----------|
| SBOM SPDX 2.3 | Manual 9 §6 | ✅ | `nucleo/sbom.py` — `generar_sbom()`; 2025 packages, 2024 files; `spdxVersion: SPDX-2.3` |
| SHA-256 checksums | Manual 9 §6.1 | ✅ | `synapse.spdx.json.sha256`, `instalador_synapse.iss.sha256` |
| Ed25519 signing | Manual 9 §6.2 | ✅ | `nucleo/ed25519_signer.py` — RFC 8032 puro, 0 deps externas |
| CHANGELOG | Manual 9 §4.1 | ✅ | `CHANGELOG_v8.1.0.md` — notas de versión, hashes de bootstrap |
| GitHub Releases workflow | Manual 9 §4.1 | ✅ | `.github/workflows/release_matrix.yml` — 4 targets |

## 3. VALIDACIÓN

- `tests/integration/test_release_matrix.py`: **23/23 PASSED** (platforms, checksums, SBOM, workflow triggers)
- `tests/security/test_slsa_sbom.py`: **37/37 PASSED** (SPDX, SHA-256, Ed25519, SLSA attestation)
- `python auditoria/verificar_alineacion.py`: **0 brechas**
