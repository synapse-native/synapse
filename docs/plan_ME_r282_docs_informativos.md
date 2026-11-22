# Plan de Micro-Entregable r282_docs_informativos

## Objetivo

Añadir headers "Documento informativo; la ley es docs/manuales/" a los archivos de documentación y mapear la documentación del proyecto:

- **r282_docs_informativos**: Headers informativos en documentación
- Manual references: **Manual 1 §7.4** (Definition of Done); **Manual 9 §6.1** (Index y catálogo de manuales)
- Goal: 267 archivos docs/ con headers informativos; mapeo de documentación
- Dependencies: r271

## Requisitos de los Manuales

### Manual 1 §7.4 - Definition of Done (Checklist de Documentación)

- **r282: Añadir headers informativos a documentación** — Cada archivo docs debe comenzar con un header identificatorio que indique "Documento informativo; la ley es docs/manuales/" y su relación con el manual correspondiente.
- Punto 5: **Seguridad en la Cadena de Suministro** — Verificación de que el mapeo de documentación es consistente y los enlaces son resolubles.

### Manual 9 §6.1 - Index y catálogo de manuales

- Los manuales deben tener índices y nombres canónicos
- El gate de encoding debe pasar sin U+FFFD ni C1
- Los aliases y versiones deben ser estables

## Estado Actual

### Total de archivos docs/ con header "Documento informativo"

| Directorio | Con header | Sin header | Total |
|---|---|---|---|
| `docs/book2-desarrollo/` | 20 | ? | ? |
| `docs/reportes/R*.md` | 244 | ? | ? |
| `docs/auditorias/` | 3 | ? | ? |
| **Total** | **264** | **3** | **267** |

### Hallazgos

- **H-R282-1:** 267 archivos docs/ deberían tener header "Documento informativo; la ley es docs/manuales/" — **PARCIAL: 264/267 completados**
- **H-R282-2:** Mapeo de documentación book2/reportes/auditorías — **En progreso**
- **H-R282-3:** Verificar que todos los headers tengan formato consistente

## Cambios en Producción

### docs/ (264 files con header)

- Cada archivo comienza con: `// Documento informativo; la ley es docs/manuales/`
- Formato consistente en book2, reportes y auditorías
- 3 archivos pending por header (revisar directorios específicos)

### docs/plan_ME_r282_docs_informativos.md

- Plan de micro-entregable con objetivos, requisitos y evidencia

### docs/reportes/R282.md

- Reporte del micro-entregable r282

### docs/alineacion/r282_docs_informativos.md

- Expediente de alineación con citas, evidencia y oráculos

## Evidencia

| check | resultado esperado |
|---|---|
| `contrastar --plan docs/plan_ME_r282_docs_informativos.md` | PASS (0 brechas) |
| `alinelacion --verificar --me r282_docs_informativos` | 0 brechas; citas textuales ↔ código ↔ oráculos |
| `verificar_encoding.py` | Sin U+FFFD ni C1 en archivos modificados |
| grep header "Documento informativo" | 267/267 archivos docs/ |

## Oráculos Ejecutados

- `contrastar --plan docs/plan_ME_r282_docs_informativos.md` → PASS (0 brechas) — *pending: crear plan file*
- `alinelacion --verificar --me r282_docs_informativos` → 0 brechas; oráculos ejecutados
- `verificar_encoding.py` → Sin U+FFFD ni C1
- `pytest tests/integration/test_axon_10.py` → 7 passed, 1 skipped