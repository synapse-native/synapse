# Plan de Modularizacion (Regla 8)

## Objetivo
Reducir archivos del nucleo por debajo de 1,000 lineas para cumplir
con la Regla 8 (Modularizacion como Prioridad).

## Archivos Identificados

| Archivo | Lineas | Estado |
|---------|--------|--------|
| `generator_legacy.syn` | 1,423 → 1,347 (76 extraidas) | EN CURSO (cuarentena) |
| `parser.syn` | 1,382 | PENDIENTE |

## Estrategia de Particionamiento

### 1. generator_legacy.syn (EN CURSO)
- ✅ Constantes extraidas a `nucleo/generator_constants.syn` (76 lineas)
- Pendiente: Estructura GeneradorCEst → `nucleo/generator_state.syn` (~50 lineas)
- Pendiente: Helpers → `nucleo/generator_helpers.syn` (~200 lineas)
- Riesgo: BAJO (archivo en cuarentena, no compilado)

### 2. parser.syn (PENDIENTE - requiere planificacion)
- Extraer constantes de tipo token: ~40 lineas
- Extraer helpers de creacion de nodos: ~60 lineas
- Extraer parseo de expresiones: ~300 lineas → `nucleo/parser_expr.syn`
- Extraer parseo de tipos: ~100 lineas → `nucleo/parser_tipos.syn`
- Riesgo: ALTO (archivo activo, bootstrap puede romperse si las
  dependencias de importacion no son correctas)

### Mitigacion de Riesgo
1. Cada extraccion se verifica con bootstrap completo de 4 etapas
2. Los archivos extraidos se IMPORTAN (no copian) desde el original
3. Commits atomicos por cada extraccion
