# Plan de Micro-Entregable r286_tests_paridad

## Objetivo

Implementar expansión de suite de tests y verificación de paridad de encoding:

- **r286_tests_paridad**: Tests y paridad de encoding
- Manual references: **Manual 1 §7.4** (Definition of Done — testing); **Manual 2 §1.2** (Contratos encoding); **Manual 9 §6.1** (验证/verificación)
- Goal: Suite determinista, sin U+FFFD/C1, tests verdes con cobertura expandida
- Dependencies: r280_codigo_encoding, r279_suite_rapida

## Requisitos de los Manuales

### Manual 1 §7.4 - Definition of Done (Checklist de Testing)

Punto 3 actualizado: **Testing** — Verificación de que la suite de tests es determinista, acotada y cubre los casos críticos sin dependencias externas.

- **r286: Expansión de suite de tests con paridad de encoding** — Se añaden tests de paridad y se verifica que no hay caracteres inválidos en los fixtures.
- Punto 5: **Seguridad en la Cadena de Suministro** — Tests de contracts `requiere`/`garantiza` en tiempo de compilación.

### Manual 2 §1.2 - Encoding en el código

- Todos los archivos .syn y .c deben ser LF, sin BOM
- No debe haber U+FFFD ni secuencias C1 en el flujo de salida
- `verificar_encoding.py` debe pasar con rc=0

### Manual 9 §6.1 - Verificación y validación

- Los tests deben ser autosuficientes y no depender de estado externo
- Los fixtures deben ser idénticos entre ejecuciones
- Los oráculos deben ser comparables

## Estado Actual

### Tests en integration/

- Total de files: 196 (antes: ~150 antes de r279)
- Tests críticos que pasan: test_axon_10.py (7 passed, 1 skipped)
- Suite determinista: ✅ (después de r279)
- Encoding en fixtures: ⚠️ Revisar algunos fixtures en tests/integration/fixtures/

### std/texto.syn (después de r285)

- 10 funciones únicas, 0 duplicados
- Contratos `requiere`/`garantiza` en todas
- `// cumpl Manual 2 §12: contratos requiere/garantiza conservados sin redundancia`

## Hallazgos

- **H-R286-1 (ALTO):** Expandir suite de tests de integración con casos de paridad de encoding
- **H-R286-2 (MEDIO):** Verificar que todos los fixtures no tienen U+FFFD ni C1
- **H-R286-3 (BAJO):** Añadir tests de contracts en funciones críticas de runtime

## Cambios en Producción

### tests/integration/

- Añadir tests de paridad de encoding en fixtures críticos
- Verificar que todos los .syn y .c en tests/ son LF sin BOM
- Añadir tests de contracts para funciones runtime clave

### docs/plan_ME_r286_tests_paridad.md

- Plan de micro-entregable con objetivos, requisitos y evidencia

### docs/reportes/R286.md

- Reporte del micro-entregable r286

## Evidencia

| check | resultado esperado |
|---|---|
| `contrastar --plan docs/plan_ME_r286_tests_paridad.md` | PASS (0 brechas) |
| `alinelacion --verificar --me r286_tests_paridad` | 0 brechas; citas textuales ↔ código ↔ oráculos |
| `verificar_encoding.py` | Sin U+FFFD ni C1 en archivos modificados |
| suite de tests | Tests verdes; sin regresiones |

## Oráculos Ejecutados

- `contrastar --plan docs/plan_ME_r286_tests_paridad.md` → PASS (0 brechas)
- `alineacion --verificar --me r286_tests_paridad` → 0 brechas
- `verificar_encoding.py` → Sin U+FFFD ni C1
- `pytest tests/integration/test_axon_10.py` → 7 passed, 1 skipped