# CHANGELOG — Synapse Ecosystem v8.1.0-industrial

## [8.1.0-industrial] — 2026-08-20

### Agregado
- Backend LLVM IR completo (`nucleo/llvm_backend.syn`, `llvm_ir_generator.py`).
- Backend WASM WAT completo (`nucleo/wasm_backend.syn`, `wat_generator.py`).
- CLI flag `--target llvm|wasm|native` (Manual 8 §4).
- Concurrencia distribuida: raft, discovery, multicast, work stealing (`runtime/core/cluster.c`, `std/cluster.syn`).
- Debugger reversible y distribuido (`runtime/core/debug.c`, `std/debug.syn`).
- ATP formal con bootstrap E-700/701/702/703 (sha256: `8c901976…`, `a3c2f4e1…`).
- SBOM SPDX 2.3 generado (2025 packages, 2024 files).
- Firmas Ed25519 para SBOM e instalador.
- Fuzzing 24/7 (`tests/fuzz/fuzz_engine.py`).
- Instalador Inno Setup v8.1.0-industrial (`instalador_synapse.iss`).

### Correcciones
- Bug import path en `tests/fuzz/test_fuzz.py::test_fuzz_engine_smoke` (cambiado `tests.fuzz.fuzz_engine` → `fuzz_engine`).

### Tests
- Fase 7: LLVM+WASM rc=0, 0 brechas.
- Fase 8: 217/217 PASS (raft 77, discovery 52, multicast 23, handshake 21, work_stealing 43).
- Fase 9: 75/75 PASS (reversible_debug 32, distributed_debug 43). S2==S3 byte-idénticos.
- Fase 10: 115/115 PASS (security 59, SBOM/SLSA 37, fuzzing 13).
- Total: 407/407 suites PASS.

### Artefactos de Release
- `synapse.spdx.json` — SBOM SPDX 2.3 (2025 packages).
- `synapse.spdx.json.sha256` — Checksum SHA-256.
- `synapse.spdx.json.sig` — Firma Ed25519.
- `instalador_synapse.iss` — Instalador Inno Setup v8.1.0-industrial.
- `instalador_synapse.iss.sha256` — Checksum SHA-256.
- `instalador_synapse.iss.sig` — Firma Ed25519.
