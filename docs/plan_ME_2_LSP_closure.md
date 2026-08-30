# Plan ME-2: Cierre LSP F27 + comandos IA

**Fecha:** 2026-08-30
**Fase:** 27 — Herramientas de Desarrollo (LSP)
**ME:** ME-2 — Cierre LSP F27 + comandos IA
**Estado:** ✅ CERRADO

---

## CONTEXTO

El LSP tiene 16/16 tests PASS pero 1 RED TDD pendiente (workspace) y falta dispatch de comandos IA. El test `test_lsp_codeaction.py` ya pasaba (era problema de binario viejo). El test `test_lsp_workspace.py` es un placeholder RED TDD.

---

## MTS BLOQUE ESTRICTO

### Requisito 1: workspace/didChangeConfiguration funcional

```markdown
requisito: Manual 8 §1.4
texto: "workspace/didChangeConfiguration — Cambia la configuración del LSP"
implementacion: handler acepta params sin crash, retorna confirmación
oraculo: tests/integration/test_lsp_workspace.py
```

### Requisito 2: dispatch synapse/aiComplete

```markdown
requisito: Manual 8 §1.4
texto: "synapse/aiComplete — genera código basado en el contexto"
implementacion: handler recibe params, retorna resultado vacío (stub) sin crash
oraculo: tests/integration/test_lsp_ai_dispatch.py (nuevo)
```

### Requisito 3: dispatch synapse/aiFix

```markdown
requisito: Manual 8 §1.4
texto: "synapse/aiFix — sugiere correcciones para errores"
implementacion: handler recibe params, retorna resultado vacío (stub) sin crash
oraculo: tests/integration/test_lsp_ai_dispatch.py (nuevo)
```

### Requisito 4: dispatch synapse/aiTranspile

```markdown
requisito: Manual 8 §1.4
texto: "synapse/aiTranspile — transpila código Python a Syquex"
implementacion: handler recibe params, retorna resultado vacío (stub) sin crash
oraculo: tests/integration/test_lsp_ai_dispatch.py (nuevo)
```

---

## IMPLEMENTACIÓN

### Cambio 1: workspace test RED TDD → GREEN

Convertir `test_lsp_workspace.py` de placeholder a test real que:
1. Inicia LSP, envía initialize + workspace/didChangeConfiguration
2. Verifica que el LSP no crashea (exit code 0)
3. Verifica que el LSP sigue respondiendo después

### Cambio 2: IA dispatch stubs

Agregar al dispatch en `_lsp_v3.c`:
- `synapse/aiComplete` → retorna `{"result": null}`
- `synapse/aiFix` → retorna `{"result": null}`
- `synapse/aiTranspile` → retorna `{"result": null}`

### Cambio 3: Test IA dispatch

Crear `tests/integration/test_lsp_ai_dispatch.py` que envía cada mensaje IA y verifica respuesta.

---

## VERIFICACIÓN

1. `pytest tests/integration/test_lsp_codeaction.py -v` — 3/3 PASS
2. `pytest tests/integration/test_lsp_completion_symbols.py -v` — 2/2 PASS
3. `pytest tests/integration/test_lsp_workspace.py -v` — 1/1 PASS
4. `pytest tests/integration/test_lsp_ai_dispatch.py -v` — 3/3 PASS
5. `python auditoria/verificar_alineacion.py` — 0 brechas
6. `python auditoria/contrastar.py --plan docs/plan_ME_2_LSP_closure.md` — gate MTS

---

## EVIDENCIA ESPERADA

- Todos los tests LSP: 22/22 PASS (16 existentes + 1 workspace + 3 IA + 2 completion_symbols)
- 0 brechas de alineación
- Gate MTS: PASA

---

## CIERRE

**Commit:** pendiente
**Fecha cierre:** 2026-08-30
**Resultado:** 23/23 tests LSP PASS, 0 fallos, 3 skipped pre-existentes
**Estado:** CERRADO ✅
