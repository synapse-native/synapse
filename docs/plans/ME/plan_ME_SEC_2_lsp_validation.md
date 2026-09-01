# Plan ME-SEC-2: Validación de protocolo LSP siempre activa

**Fecha:** 2026-08-30
**Fase:** 27 — Herramientas de Desarrollo
**ME:** ME-SEC-2 — Validación protocolo LSP (Manual 8 §1.2, Manual 2 §5.3)
**Estado:** 🔄 EN PROGRESO

---

## CONTEXTO

`leer_cabecera()` en `_lsp_v3.c` extrae Content-Length sin validar:
- Negativo → `leer_mensaje` retorna vacío (silencioso, no error)
- Sin tope → un Content-Length gigante causaría DoS (asignación masiva)
- Cuerpo no JSON → `desde_texto` retorna nodo tipo=-1, el loop ignora

Los contratos `requiere/garantiza` son debug-only (Manual 2 §5.3), así que la
validación debe ser EXPLÍCITA y funcionar en TODOS los builds.

---

## MTS BLOQUE ESTRICTO

### Requisito 1: Content-Length positivo con tope

```markdown
requisito: Manual 8 §1.2
texto: "Content-Length presente, positivo y con tope máximo"
implementacion: cuando content_length <= 0 o > MAX_LSP_MSG (1MB),
  retornar error -32600 (Invalid Request) al cliente
oraculo: tests/integration/test_lsp_protocol_validation.py
```

### Requisito 2: Cuerpo JSON parseable

```markdown
requisito: Manual 8 §1.2
texto: "cuerpo JSON parseable"
implementacion: cuando desde_texto retorna tipo < 0, retornar error -32700
oraculo: tests/integration/test_lsp_protocol_validation.py
```

### Requisito 3: Respuesta de error en todos los builds

```markdown
requisito: Manual 2 §5.3
texto: "contratos debug-only; validación explícita en todos los builds"
implementacion: validación con if/return, no assert
oraculo: build --release no crash con Content-Length inválido
```

---

## CIERRE

**Commit:** pendiente
**Fecha cierre:** 2026-08-30
**Resultado:** 5/5 tests TDD PASS, 31/31 LSP suite PASS, 0 brechas
**Estado:** ✅ CERRADO
