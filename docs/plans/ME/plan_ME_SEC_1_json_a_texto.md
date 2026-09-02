# Plan ME-SEC-1: _json_a_texto sin buffer estático

**Fecha:** 2026-08-30
**Fase:** 27 — Herramientas de Desarrollo
**ME:** ME-SEC-1 — _json_a_texto buffer overflow handling (Manual 4 §2.1)
**Estado:** 🔄 EN PROGRESO

---

## CONTEXTO

`_json_a_texto` en `runtime/core/json.c` ya copia el resultado a `pool_alloc` (fix previo).
Sin embargo, cuando el JSON excede 64KB, trunca silenciosamente en vez de retornar error.
Faltan tests TDD que verifiquen el comportamiento correcto.

---

## MTS BLOQUE ESTRICTO

### Requisito 1: dos serializaciones retienen valores distintos

```markdown
requisito: Manual 4 §2.1
texto: "buffer propio que el llamador libera; no usar buffer estático compartido"
implementacion: _json_a_texto copia a pool_alloc; test verifica que dos llamadas
  consecutivas con nodos diferentes retienen valores distintos
oraculo: tests/unit/test_json_serialization.py
```

### Requisito 2: >64KB retorna CadenaSegura vacía

```markdown
requisito: Manual 4 §2.1
texto: "Sobre 64 KB: devolver error/Resultado vacío, no truncar silenciosamente"
implementacion: cuando _ser_pos >= _SER_BUF_SIZE, retornar (CadenaSegura){0,""}
oraculo: tests/unit/test_json_serialization.py
```

---

## CIERRE

**Commit:** pendiente
**Fecha cierre:** 2026-08-30
**Resultado:** 3/3 tests TDD PASS, >64KB retorna vacio (no truncar)
**Estado:** ✅ CERRADO
