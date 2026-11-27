# Plan MTS: Working Tree Fase 31 — Mejoras de auditoría, compilador, runtime y tests

## Contexto

Este plan cubre las mejoras acumuladas en el working tree durante la Fase 31 (Herramientas Nativas), incluyendo:
- Actualizaciones del sistema de auditoría (alineación, contraste, calidad de tests)
- Mejoras en el compilador (emit_declarations, emit_expressions, generator, parser_control, puente_canonico)
- Actualizaciones del runtime (axon, concurrency, sistema)
- Nuevos tests (fmt, lint, pruebas, coverage, reports)
- Documentación de deficiencias Fase 31

## Cambio 1: Sistema de auditoría mejorado

```yaml
requisito: Manual 2 §12
texto: "Toda función pública nueva con requiere/garantiza, todo archivo productivo citado con cumple Manual en sección REAL"
implementacion: Mejoras en alineacion.py, contrastar.py, verificar_alineacion.py, auditar_calidad_tests.py, registrar_lectura.py
oraculo: tests/auditoria/test_gate_mts_oraculos.py
```

## Cambio 2: Compilador — emisión de declaraciones y expresiones

```yaml
requisito: Manual 2 §1.3
texto: "Generación de código C para declaraciones Synapse"
implementacion: Actualizaciones en emit_declarations.py, emit_expressions.py, generator.py, parser_control.py, puente_canonico.py
oraculo: tests/nucleo/test_lint.py
```

## Cambio 3: Runtime — concurrencia y sistema

```yaml
requisito: Manual 5 §2
texto: "Fibras ligeras: concepto, sintaxis en Synapse, semántica de movimiento"
implementacion: Actualizaciones en axon.c, concurrency.c, sistema.c
oraculo: tests/test_auditoria_alineacion.py
```

## Cambio 4: Tests nuevos de Fase 31

```yaml
requisito: Manual 8 §6.3
texto: "Los tests deben ser verificables y reproducibles"
implementacion: Tests fmt, lint, pruebas, coverage, reports
oraculo: tests/nucleo/test_fmt.py
```

## Cambio 5: Documentación de deficiencias Fase 31

```yaml
requisito: Manual 8 §6.3
texto: "Los tests deben ser verificables y reproducibles"
implementacion: Plan y verificación de deficiencias Fase 31
oraculo: tests/auditoria/test_auditar_calidad_cwd.py
```

## Archivos a modificar

### Auditoría
- `auditoria/alineacion.py`
- `auditoria/auditar_calidad_tests.py`
- `auditoria/contrastar.py`
- `auditoria/lecturas.jsonl`
- `auditoria/registrar_lectura.py`

### Compilador
- `compilador/generator/emit_declarations.py`
- `compilador/generator/emit_expressions.py`
- `compilador/generator/generator.py`
- `compilador/parser_control.py`
- `compilador/puente_canonico.py`

### Runtime
- `runtime/core/axon.c`
- `runtime/core/concurrency.c`
- `runtime/core/sistema.c`

### Núcleo
- `nucleo/parser_sentencias.syn`
- `nucleo/principal.syn`

### Syquex
- `syquex/expr.syn`
- `syquex/parser.syn`

### Headers
- `synapse_rt_types.h`
- `axon/axon_rt.c`
- `axon/axon_rt.h` (nuevo)

### Tests
- `tests/conftest.py`
- `tests/fixtures/test_a23_parity.c`
- `tests/test_wasm_extended.c`
- `tests/auditoria/test_auditar_calidad_cwd.py` (nuevo)
- `tests/auditoria/test_gate_mts_oraculos.py` (nuevo)
- `tests/integration/test_coverage.py` (nuevo)
- `tests/integration/test_reports.py` (nuevo)
- `tests/nucleo/test_fmt.py` (nuevo)
- `tests/nucleo/test_lint.py` (nuevo)
- `tests/syquex/test_pruebas.py` (nuevo)

### Documentación
- `docs/alineacion/DEUDA.md`
- `docs/alineacion/f31_deficiencias.md` (nuevo)
- `docs/decisiones/MODULOS_D9.md`
- `docs/gobernancia/mapa_alineacion.md`
- `docs/gobernancia/mapa_manuales.md`
- `docs/manuales/MANUAL_TESTS_OBLIGATORIOS.md`
- `docs/plan_ME_f31_deficiencias.md` (nuevo)
- `docs/verificacion_ME_f31_deficiencias.md` (nuevo)
- `docs/GOBERNANZA_BRANCH_PROTECTION.md` (nuevo)

### CI/CD
- `.github/workflows/ci-tests.yml`
- `scripts/githooks/pre-commit`

### Evidencia
- `auditoria/evidencia/*.json` (5 archivos nuevos)

## Verificación

```bash
.venv\Scripts\python.exe -m pytest tests/auditoria tests/axon tests/nucleo tests/security tests/installers -v
python auditoria/verificar_alineacion.py
python auditoria/contrastar.py --plan docs/plan_ME_f31_deficiencias.md
```
