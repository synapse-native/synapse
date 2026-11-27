# Plan de Micro-Entregable r287_contratos

## Objetivo

Añadir contratos `requiere` + `garantiza` a funciones públicas que faltan, reduciendo la deuda de 590 violaciones a 0 bajo `--estricto`.

- **r287_contratos**: Primer bloque de contratos (10% ~59 funciones)
- Manual references: **Manual 2 §12** (Contratos requiere/garantiza en toda función pública); **Manual 2 §5.1** (Aserciones obligatorias)
- Goal: Reducir violaciones en lote piloto; actualizar baseline después
- Dependencies: r277_contracts_audit (deuda medida), r286_tests_paridad

## Requisitos de los Manuales

### Manual 2 §12 - Contratos requiere/garantiza

- **r287: Añadir `requiere` + `garantiza` a funciones seleccionadas** — Cada función pública debe tener ambos contratos en su firma.
- Punto 5: **Aserciones en tests** — Los tests deben validar que los contratos cumplen su propósito.

### Manual 2 §5.1 - Aserciones obligatorias

- Las funciones deben tener aserciones verificables que garanticen el cumplimiento de los contratos.

## Estado Actual

| Métrica | Valor |
|---|---|
| Violaciones totales (auditar) | 590 |
| Archivos con violations | 68 |
| Funciones por archivo (promedio) | ~8.7 |

### Hallazgo H-R277-1

- **H-R277-1 ABIERTO**: 590 funciones públicas carecen de `requiere` + `garantiza`
- Las funciones mayores por deuda: `nucleo/analizador_semantico.syn` (34), `nucleo/generador/emision_c.syn` (12), `nucleo/coverage.syn` (2), etc.
- Baseline congelada en `auditoria/contratos_baseline.txt`

## Bloque r287: Lote Inicial (59 funciones ~10%)

### Funciones objetivo (nucleo/analizador_semantico.syn)

Añadir contratos a las 34 funciones de `analizador_semantico.syn` identificadas en la violación.

Ejemplo de contrato a añadir a `sem_error`:

```
funcion sem_error(est: AnalizadorSemanticoEst, codigo: entero, idx_nodo: entero, mensaje: cadena) -> nulo:
    requiere:
        est != nulo
        codigo >= 0
    garantiza:
        est.hay_error == verdadero  =>  linea >= 0 && columna >= 0
    // cumple Manual 2 §12: requiere y garantiza en toda función pública
```

### Funciones objetivo (nucleo/generador/emision_c.syn)

Añadir contratos a las 12 funciones de `emision_c.syn`.

### Funciones objetivo (demás archivos prioritarios)

- `nucleo/coverage.syn`: 2 funciones
- `nucleo/diagnostics.syn`: 10 funciones  
- `nucleo/generador/*.syn`: múltiples funciones menores

## Cambios en Producción

### std/agent_skills.syn (referencia)

- Ya tiene `requiere:` añadido (5 funciones como referencia)

### Archivos a modificar (lote r287)

- `nucleo/analizador_semantico.syn`: 34 funciones + contratos
- `nucleo/generador/emision_c.syn`: 12 funciones + contratos
- `nucleo/coverage.syn`: 2 funciones + contratos
- `nucleo/diagnostics.syn`: 10 funciones + contratos
- `nucleo/generador/*.syn`: 1 función cada una

### Comentario manually añadido

- `// cumple Manual 2 §12: requiere y garantiza en toda función pública`
- `// cumple Manual 2 §5.1: aserciones obligatorias`

## Evidencia

| check | resultado esperado |
|---|---|
| `auditar` antes | 590 violaciones |
| `auditar` después r287 | ~531 violaciones (59 reducidas) |
| `contrastar --plan docs/plan_ME_r287_contratos.md` | PASS (0 brechas) |
| `verificar_alineacion.py --verificar --me r287_contratos` | 0 brechas |
| `verificar_contratos.py` | Sin nuevas infracciones |

## Oráculos Ejecutados

- `auditar` baseline → 590 violaciones
- `auditar` post-r287 → < 590 violaciones (mismo conjunto de funciones, contratos añadidos)
- `contrastar --plan docs/plan_ME_r287_contratos.md` → PASS (0 brechas)
- `verificar_alineacion.py --verificar --me r287_contratos` → 0 brechas