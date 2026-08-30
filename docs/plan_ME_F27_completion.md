# Plan ME-F27-COMPLETION: Fix test_lsp_completion_symbols (FFI RAII)

**Fecha:** 2026-08-30
**Fase:** 27 — Herramientas de Desarrollo (LSP)
**ME:** Fix completion_symbols (último test 9/9)
**Estado:** ✅ CERRADO (commit b6007dd)

---

## CONTEXTO

El test `tests/integration/test_lsp_completion_symbols.py` es un RED TDD que debe implementarse. Actualmente es un placeholder que falla con "RED TDD (ME_27_T6): aun no implementado".

**Problema raíz (Hallazgo 9 de la memoria):** `lsp_extract_doc_functions()` (C puro) funciona en C pero la integración Synapse-FFI genera crash silencioso. La causa es que Synapse RAII libera `CadenaSegura.datos` via shared pointer en parámetros de función C.

**Solución ya aplicada (Hallazgo 13):** Opción A del Arquitecto - eliminar `es_externo` de `CadenaSegura` (16 bytes exactos) y usar `pool_alloc`/`pool_free` consistentemente. Verificado con commit `e79fdcc`.

---

## MTS BLOQUE ESTRICTO

### Requisito 1: completion retorna símbolos reales del documento

```markdown
requisito: Manual 8 §1.4
texto: "textDocument/completion — Autocompletado de símbolos y palabras clave"
implementacion: test验证 completion retorna funciones del documento (calcular)
oraculo: tests/integration/test_lsp_completion_symbols.py
```

### Requisito 2: completion incluye keywords de Synapse

```markdown
requisito: Manual 8 §1.4
texto: "completionProvider\":{\"triggerCharacters\":[\".\",\":\",\"(\"]}"
implementacion: lsp_build_completion_items() retorna keywords hardcoded + símbolos del documento
oraculo: tests/integration/test_lsp_completion.py
```

---

## IMPLEMENTACIÓN PROPUESTA

### Cambio 1: Actualizar test_lsp_completion_symbols.py

Reemplazar el placeholder RED TDD con un test real que:
1. Envíe `textDocument/completion` al LSP
2. Verifique que la respuesta contiene símbolos del documento (funciones definidas)
3. Valide que los items tienen el formato correcto (`label`, `kind`)

### Cambio 2: Verificar que lsp_build_completion_items() retorna símbolos

La función C `lsp_build_completion_items()` en `runtime/core/string_utils.c` ya:
- Agrega keywords hardcoded
- Parsea el documento y extrae funciones
- Retorna `CadenaSegura` con `pool_alloc`

Verificar que el dispatch en `lsp_v3.syn` (línea 976-978) funciona correctamente.

---

## VERIFICACIÓN

1. Ejecutar: `.venv\Scripts\python.exe -m pytest tests/integration/test_lsp_completion_symbols.py -v`
2. Ejecutar: `.venv\Scripts\python.exe -m pytest tests/integration/test_lsp_completion.py -v`
3. Ejecutar: `python auditoria/verificar_alineacion.py` — 0 brechas
4. Ejecutar: `python auditoria/contrastar.py --plan docs/plan_ME_F27_completion.md` — gate MTS

---

## EVIDENCIA ESPERADA

- Test `test_lsp_completion_simbolos` pasa (RED → GREEN)
- Test `test_completion_keywords` pasa
- Test `test_completion_simbolos_documento` pasa
- 0 brechas de alineación
- Gate MTS: PASA

---

## CIERRE

**Commit:** b6007dd
**Fecha cierre:** 2026-08-30
**Resultado:** Test completion_symbols PASS (RED → GREEN)
**Bug raíz:** pool_alloc slab allocator retornaba misma dirección para arrays ParArr/ParJson vivos durante parseo recursivo JSON. Fix: malloc en par_arr_append/nodo_arr_append.
**Estado:** CERRADO ✅
