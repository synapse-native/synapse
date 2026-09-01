# Plan ME — Corrección de tests: anomalías y preexistentes

## Contexto
Ejecución de tests por etapas reveló:
- 24 tests que fallan como FAILURE en vez de TDD RED o skip
- 6 tests preexistentes con failures reales

## Alcance

### Anomalías (24 tests → TDD RED)
Tests que verifican features no implementadas usando `assert`/`pytest.fail` directo
en vez de `pytest.fail("RED TDD (ME_xx_Tx): ...")`.

| Archivo | Tests | Fix |
|---|---|---|
| test_federated_exec_10.py | 2 (codegen) | → pytest.fail RED TDD ME_29_T1 |
| test_federated_adv_10.py | 3 (codegen) | → pytest.fail RED TDD ME_29_T1 |
| test_quantum_exec_10.py | 3 (.o files) | → pytest.fail RED TDD ME_29_T1 |
| test_quantum_adv_10.py | 5 (headers) | → pytest.fail RED TDD ME_29_T1 |
| test_ai_complete.py | 2 | → pytest.fail RED TDD ME_27_T4 |
| test_ai_correction.py | 2 | → pytest.fail RED TDD ME_27_T4 |
| test_ai_explain.py | 2 | → pytest.fail RED TDD ME_27_T4 |
| test_ai_fix.py | 2 | → pytest.fail RED TDD ME_27_T4 |

### Preexistentes (6 failures)
| ID | Test | Causa | Fix |
|---|---|---|---|
| P1 | test_cobertura_d5 | codegen sin main() | Investigar → fix codegen o TDD RED |
| P2 | test_cli_check | CLI check rc=2 | Investigar → fix CLI o skip |
| P3 | test_lsp_native (3) | LSP server solo initialize | Preexistente conocido, skip |
| P4 | test_r3_param_adt | D-2 ADT param | Deuda conocida, skip |
| P5 | test_federated_exec_10 (2) | import system bug | TDD RED ME_29_T1 |
| P6 | test_quantum_exec_10 (3) | .o files missing | TDD RED ME_29_T1 |

## Requisitos
- Manual 2 §4.2: tests TDD usan pytest.fail("RED TDD (ME_xx_Tx)")
- Manual 2 §10.1: DiagnosticManager
- Cada archivo de producción lleva `// cumple Manual X §Y`
- Tests modificados llevan docstring con cita Manual X §Y

## Oráculo
- Todos los tests corregidos pasan (TDD RED = falla con mensaje correcto)
- Verificar: python -m pytest <tests_afectados> -v
