# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v8.1.0-industrial] - 2026-11-21

### Added
- **r299_codigo_muerto**: `auditoria/verificar_codigo_muerto.py` (barrido de funciones sin referencias en los módulos alcanzables desde el build) + gate en pre-commit y oráculo `tests/auditoria/test_codigo_muerto.py`
- **r282_docs_informativos**: Added "Documento informativo; la ley es docs/manuales/" header to documentation files
- **r282_docs_informativos**: Mapped and categorized all documentation in docs/book2-desarrollo/, docs/reportes/, and docs/auditorias/
- **r281_d9_dead_code**: Removed 12 duplicated functions from std/texto.syn (lines 108-187)
- **r278_ide_debugger**: Implemented debugger time-travel CLI (`synapse debug --load/--step/--reverse/--snapshots`)
- **r278_ide_debugger**: Native C fixture test (`tests/test_debugger_time_travel.c`) with 31 verifications
- **r278_ide_debugger**: VS Code extension with 15 debug commands
- **r278_ide_debugger**: Integration tests (5/5 passed: load/step/reverse/snapshots/sin traza)

### Changed
- **nucleo/*.c (6 dumps de S1)**: retirados del repo (no son insumos de build; la fuente de verdad son sus .syn) y podados del SBOM; `.sha256` recalculado y oráculo contra dumps nuevos — H-R302-1 RESUELTO
- **opensyn/generate_runtime_bindings.py, bindings_generator.py, full_pipeline.py**: reparadas citas `//` inválidas en Python que rompían la generación de bindings desde r288; `librerias/embedded_libs.h` regenerado y con `--check` — H-R302-2 RESUELTO
- **nucleo/generator.syn + nucleo/generador/**: reconciliación generador↔submódulos; los bloques H-R275-1 y los contratos viven en su origen y el rebuild es idempotente — H-R300-1 RESUELTO
- **nucleo/formatter.syn**: `fmt` preserva los comentarios `//` verbatim (incluida la alineación deliberada) — H-R299-1 RESUELTO
- **nucleo/cache.syn / nucleo/formatter.syn**: eliminadas 6 funciones sin ninguna referencia (`_calcular_hash_archivo`, `_obtener_hashes_dependencias`, `_leer_flags_compilacion`, `_resolver_ruta_import`, `formatear_archivo`, `fmt_directorio`) — H-R285-2 RESUELTO
- **std/texto.syn**: Removed duplicate block (12 functions H-R196-2), 275→129 líneas, 28→10 funciones únicas
- **docs/book2-desarrollo/** (20 files): Added "Documento informativo; la ley es docs/manuales/" header
- **docs/reportes/** (244 files): Added "Documento informativo; la ley es docs/manuales/" header  
- **docs/auditorias/** (3 files): Added "Documento informativo; la ley es docs/manuales/" header
- **runtime/core/debug.c**: Fixed debugger persist loading, off-by-one error in tr_grabar_error, `rp_ir_a_pre_error` API
- **runtime/core/debug.h**: Declared `_syn_debug_cargar_traza_persistida`
- **nucleo/principal.syn**: Added `debug --load/--step/--reverse/--snapshots` subcommand (lines 1321-1333)
- **tests/test_debugger_time_travel.c**: Native fixture 31 verifications, stubs pool_alloc y cluster_canal_remoto_enviar
- **tests/integration/test_debugger_cli_r278.py**: 5 tests (load/step/reverse/snapshots/sin traza)
- **tests/integration/test_vscode_extension_r278.py**: VS Code extension test harness
- **tests/fixtures/vscode_harness/harness.js**: 15 comandos registrados
- **vscode-synapse/extension.js**: 15 comandos registrados
- **vscode-synapse/package.json**: 15 comandos registrados
- **docs/plan_ME_r278_ide_debugger.md**: Micro-entregable plan
- **docs/verificacion_ME_r278_ide_debugger.md**: Verification record
- **docs/alineacion/r278_ide_debugger.md**: Alignment anchors
- **docs/gobernancia/mapa_alineacion.md**: Updated alignment map
- **docs/reportes/R278.md**: Report for r278
- **auditoria/suite_baseline.json**: Updated baseline (+6 tests, +3 skips)

### Fixed
- Debugger time-travel: trace load now restores events correctly
- Debugger CLI: multi-invocación now resumes persisted trace
- Off-by-one fix: `tr_grabar_error` índice `(cabeza-1+TRACE_MAX_EVENTS)%TRACE_MAX_EVENTS`
- `rp_ir_a_pre_error` now uses correct `_tr_ultimo_error_idx`

### Deprecated
- `std/texto.syn` duplicate functions H-R196-2 (removed, replaced by 10 unique functions)
- Documentation without "Documento informativo; la ley es docs/manuales/" header (now standardized)

### Security
- Cero telemetría forzada en todos los cambios
- Sin dependencias opacas añadidas
- Sin conexiones de red ocultas

---

Pre-v8.1.0 changes are tracked in the git history. For detailed per-commit changes, refer to `git log --oneline -20`.