# Plan ME-2 — File-finder + catálogo APIs locales (R2)

FASE: 30-c ME_opensyn_best
ID: ME-2
ESTADO: implementacion
ORIGEN: R2 del plan ME_opensyn_best.md (freebuff file-finder + Kilo Context7)

## 1. Resumen del micro-entregable

### Requisito R2 — File-finder + índice semántico antes de editar (anti-alucinación)

requisito: Manual 7 §2.3
texto: "El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn. Extrae el contexto más relevante del código fuente para construir un prompt eficiente y preciso."
implementacion:
  - Origen: freebuff (file-picker mapea ANTES de editar) + Kilo (indice semantico + Context7 docs).
  - En `opensyn/router.syn`: fase 0 OBLIGATORIA de localizacion (que archivos tocan la tarea) antes de generar codigo. Fuentes por prioridad: nodo AST actual > lineas cercanas al cursor > diagnosticos > std/lib reglas > feedback.jsonl.
  - Catalogo local de APIs reales de `std/*.syn` y `lib/*.syq` (generado del repo, no del modelo) para que el modelo no invente funciones .syn/.syq. Es el equivalente local al Context7 de Kilo.
  - Negociacion n_ctx 30/70 existente se conserva; el file-finder recorte por cercania al cursor (ya prescrito en §2.3 punto 4).
oraculo: tests/opensyn/test_rag.py

## 2. Archivos a modificar

- `opensyn/router.syn` — agregar `file_finder()`, `catalogo_api`, integrar en `construir_prompt()`
- `tests/opensyn/test_rag.py` — actualizar oráculo con tests de file-finder y catálogo
- `tests/unit/test_modos_opensyn.py` — NO se toca (ME-1 completado)

## 3. Cita del manual (grep-chequeable)

```c
// cumple Manual 7 §2.3: file-finder localiza archivos relevantes ANTES de generar código
// cumple Manual 7 §2.3: catálogo de APIs std impide alucinaciones de funciones
```

## 4. Verificacion

- `python auditoria/verificar_alineacion.py` — 0 brechas
- `python auditoria/contrastar.py --plan docs/plan_ME_2_opensyn_best.md` — verde
- `python -m pytest tests/opensyn/test_rag.py -v` — GREEN
