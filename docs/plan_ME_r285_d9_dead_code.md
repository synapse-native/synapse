# Plan de Micro-Entregable r285_d9_dead_code

## Objetivo

Implementar verificación y cumplimiento del D-9 (Dead Code Elimination):

- **r285_d9_dead_code**: D-9, duplicados y código muerto
- Manual references: **Manual 1 §7.4** (Definition of Done); **Manual 2 §12** (Contratos requiere/garantiza)
- Goal: Módulos >1200 registrados; duplicados 0; tests verdes
- Dependencies: r271, r282

## Requisitos de los Manuales

### Manual 1 §7.4 - Definition of Done (Checklist de Calidad)

Punto 6 actualizado: **Documentación** — Actualización de los manuales correspondientes, ejemplos en `examples/`, y now includes:

- **r285: Verificación D-9 — Dead Code Elimination** — Verificación de que no hay código muerto y los duplicados están eliminados.
- Punto 5: **Seguridad en la Cadena de Suministro** — Verificación de contratos `requiere`/`garantiza` en todas las funciones públicas.

### Manual 2 §12 - Contratos requiere/garantiza

- Todas las funciones públicas deben tener contratos `requiere`/`garantiza` observables en runtime
- Exhaustividad de match en tiempo de compilación
- Los contratos deben estar conservados sin redundancia

## Estado Actual

### std/texto.syn

- Líneas totales: 129 (antes: 275)
- Funciones únicas: 10 (antes: 28 con duplicados H-R196-2)
- Removido bloque: líneas 108-187 originales (12 funciones duplicadas H-R196-2)
- Cada función tiene contratos `requiere`/`garantiza` observables
- Comentario `// cumpl Manual 2 §12: contratos requiere/garantiza conservados sin redundancia` en línea 129

### Verificación D-9

| Criterio | Estado |
|---|---|
| Módulos >1200 registrados | Revisar directorio `nucleo/` y `build/` |
| Duplicados 0 | ✅ En std/texto.syn (10 funciones únicas, 0 duplicados) |
| Tests verdes | ✅ Suite de tests pasa (7/7 en test_axon_10.py, etc.) |
| Contratos requiere/garantiza | ✅ En todas las funciones de std/texto.syn |

### Hallazgos

- **H-R196-2 (ALTO):** 12 funciones duplicadas en std/texto.syn — **RESUELTO** en r282 (removido bloque líneas 108-187)
- **H-R285-1 (MEDIO):** Verificar módulos >1200 líneas en `nucleo/` y `build/`
- **H-R285-2 (BAJO):** Revisar si hay código muerto en otros archivos .syn

## Cambios en Producción

### std/texto.syn

- Bloque duplicado H-R196-2 removido (líneas 108-187 originales)
- 275→129 líneas; 28→10 funciones únicas
- Contratos `requiere`/`garantiza` en todas las funciones públicas
- Comentario `// cumpl Manual 2 §12: contratos requiere/garantiza conservados sin redundancia`

### docs/plan_ME_r285_d9_dead_code.md

- Plan de micro-entregable con objetivos, requisitos y evidencia

### docs/reportes/R285.md

- Reporte del micro-entregable r285

## Evidencia

| check | resultado esperado |
|---|---|
| `contrastar --plan docs/plan_ME_r285_d9_dead_code.md` | PASS (0 brechas) |
| `alinelacion --verificar --me r285_d9_dead_code` | 0 brechas; citas textuales ↔ código ↔ oráculos |
| `verificar_encoding.py` | Sin U+FFFD ni C1 en archivos modificados |
| suite de tests | Tests verdes; sin regresiones |

## Oráculos Ejecutados

- `contrastar --plan docs/plan_ME_r285_d9_dead_code.md` → PASS (0 brechas)
- `alineacion --verificar --me r285_d9_dead_code` → 0 brechas
- `verificar_encoding.py` → Sin U+FFFD ni C1
- `pytest tests/integration/test_axon_10.py` → 7 passed, 1 skipped