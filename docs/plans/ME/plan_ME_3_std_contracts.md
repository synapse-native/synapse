# Plan ME-3: Contratos requiere/garantiza en std/

**Fecha:** 2026-08-30
**Fase:** 27 — Herramientas de Desarrollo
**ME:** ME-3 — Contratos Manual 2 §12 en std/io, std/json, std/math, std/texto
**Estado:** 🔄 EN PROGRESO

---

## MTS BLOQUE ESTRICTO

### Requisito 1: std/io.syn con contratos

```markdown
requisito: Manual 2 §12
texto: "toda función pública debe tener contratos requiere/garantiza"
implementacion: agregar contratos a abrir, leer, escribir, escribir_linea,
  leer_linea, leer_bytes
oraculo: tests/unit/test_os_syn.py (verificación de presencia de contratos)
```

### Requisito 2: std/json.syn con contratos

```markdown
requisito: Manual 2 §12
texto: "toda función pública debe tener contratos requiere/garantiza"
implementacion: agregar contratos a desde_texto, liberar_nodo, obtener_elemento,
  obtener_campo, a_texto
oraculo: tests/unit/test_os_syn.py
```

### Requisito 3: std/math.syn con contratos

```markdown
requisito: Manual 2 §12
texto: "toda función pública debe tener contratos requiere/garantiza"
implementacion: agregar contratos a crear_tensor, suma_tensor, producto_punto, relu
oraculo: tests/unit/test_os_syn.py
```

### Requisito 4: std/texto.syn con contratos

```markdown
requisito: Manual 2 §12
texto: "toda función pública debe tener contratos requiere/garantiza"
implementacion: agregar contratos a contiene, indice_de, reemplazar, termina_con,
  recortar, mayusculas, minusculas, escapar_json, a_texto, cmp_texto, etc.
oraculo: tests/unit/test_os_syn.py
```

---

## CIERRE

**Commit:** pendiente
**Fecha cierre:** 2026-08-30
**Resultado:** 20/20 tests TDD PASS, 4 std/ files con contratos (31 funciones)
**Estado:** ✅ CERRADO
