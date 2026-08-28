# PLAN MAESTRO — FORTALECIMIENTO Y ALINEACIÓN DE TESTS (F27→F30)

**Doc maestro.** Basado en la Auditoría de tests 2026-08-28 (hallazgos H1–H7).
Cada micro-entregable tiene su `docs/plan_ME_<id>.md` (MTS). Orden de ejecución: A → B → C → E → D.

## Criterio rector
El test nace del **MANUAL** (especificación) y valida *comportamiento*; debe FALLAR (RED) hasta que
el código implemente lo que el manual dice. Toda prueba cita `Manual X §Y`.

## Principios (no negociables)
1. Trazabilidad obligatoria: todo `test_*.py` cita `Manual X §Y`.
2. Sin desviación: cada ME = un objetivo; el agente no toca fuera del bloque `implementacion:`.
3. Oráculo conductual: prohibido afirmar solo presencia de substring en artefacto sin compilar/ejecutar.
4. TDD real para F27 residual + F28–F30: `def test_*` con asserts reales que fallan (no `pytest.skip`),
   marcados `@pytest.mark.tdd`, seguidos en `tests/tdd/REGISTRO_TDD.md`.
5. Gate MTS: al integrar, `auditoria/contrastar.py --plan docs/plan_ME_<id>.md` debe pasar.

## Mapa de cobertura de hallazgos
| Hallazgo | MEs |
|---|---|
| H1 (manuales sin Tests Obligatorios) | ME_Q1 |
| H2 (404 sniff) | ME_S1…ME_S6 |
| H3/H5 (62 sin cita; M8 infra-citado) | ME_T1…ME_T4 |
| H4 (83 TDD skip) | ME_X1 |
| H6 (verificador no audita calidad) | ME_Q2 |
| TDD F27→F30 | ME_27_T*, ME_28_T*, ME_29_T*, ME_30_T* |

## Workstream A — Gobernanza, herramientas y especificación
- **ME_Q1** — Crear `docs/manuales/MANUAL_TESTS_OBLIGATORIOS.md`.
- **ME_Q2** — Crear `auditoria/auditar_calidad_tests.py` + self-test.

## Workstream B — Conversión sniff → oráculo conductual (H2: 404 tests)
- **ME_S1** tests/ raíz · **ME_S2** tests/opensyn/ restantes · **ME_S3** tests/integration/ lote1
- **ME_S4** tests/integration/ lote2 · **ME_S5** tests/syquex/ + tests/unit/ · **ME_S6** security/fuzz/stress

## Workstream C — Trazabilidad al manual (H3/H5)
- **ME_T1** LSP/diagnostics · **ME_T2** bootstrap/frontend · **ME_T3** cluster/release/signing · **ME_T4** barrido 62 archivos + M8 >90%

## Workstream D — Tests TDD REALES (F27 residual + F28–F30)
- **ME_27_T1…T6** (Manual 8): codeAction/formatting/signatureHelp, workspace/didChangeConfiguration,
  comandos VS Code, debugger time-travel, CLI run/debug/opensyn, completion_symbols.
- **ME_28_T1…T3** (Manual 3): certificación Syquex v1.0 (Hito 7).
- **ME_29_T1…T3** (Manual 9 §5.7 / F29): detección hardware, installer, gestión modelos.
- **ME_30_T1…T4** (Manual 9 §9 / F30): .iss/.sh/.dmg, Makefile/build.py, distribución, release unificado.

## Workstream E — Saneamiento de TDD-feature (H4)
- **ME_X1** — 83 `pytest.skip('...no existe aún (TDD)')` → `pytest.mark.xfail(strict=True)`.

## Gates de calidad (CI)
- `auditoria/auditar_calidad_tests.py` rc=0 (sin sniff nuevo, sin archivo sin cita).
- `auditoria/verificar_alineacion.py` 0 brechas.
- Job `tdd-gate`: los `ME_2x-T*` marcados siguen RED hasta su ME de código.

## Riesgos
- ME_Q1 crea un manual nuevo (aditivo, autorizado); no modifica M1–M9.
- Los TDD de F28–F30 dependen de que ME_Q1 defina las secciones de certificación/distribución en M3/M9.
- Volumen B (404 tests) es alto: los MEs S* son los más largos; paralelizables por directorio.
