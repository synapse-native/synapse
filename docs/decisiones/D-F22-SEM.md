# D-F22-SEM — ABI SemNodo flat format derivado de Manual 6 §1.2 + metadata `es_mutable`

**Tipo:** Decisión arquitectónica  
**Fase:** Fase 22  
**Fecha:** 2026-08-24  
**Status:** ✅ Resuelta  
**Autor:** Auditor Externo → implementado  
**Referencias:** Manual 6 §1.2, Manual 6 §1.3, Manual 3 §9.1/§9.3

---

## Problema

El Manual 6 §1.2 define `SemNodo` como un struct rico con metadata de ownership/borrow:

```c
typedef struct {
    int tipo, linea, columna;
    char* archivo;
    int owner_id, scope_id;
    bool es_owned, es_prestado_inmutable, es_prestado_mutable;
    bool es_transferido, es_exportado;
    char* export_lang;
    union { ... };  // layouts tipados por tipo de nodo
} SemNodo;
```

La implementación actual usa un **formato flat de 10 elementos** `[tipo, linea, columna, valor_int, hijo_izq, hijo_der, hermano, extra, txt1, txt2]` que carece de `archivo`, `owner_id`, `scope_id`, `es_owned`, `es_prestado_inmutable`, `es_prestado_mutable`, `es_transferido`, `es_exportado`, `export_lang` y del `union`.

Esto bloquearía OpenSyn LSP (Fase 25, Manual 1 §3.1 L464) que "tiene acceso al AST canónico".

## Decisión

El formato flat es **intencional**. El struct rico de Manual 6 §1.2 es el **modelo conceptual**; el formato flat de 10 campos es la **representación canónica** compartida entre el runtime C nativo y el puente Python SyQuex. La documentación existente en `nucleo/ast_abi.syn:27-38` lo reconoce pero no está formalizada como decisión.

### Resolución

1. **`valor_int` (slot [3]) reserva bit 0 para `es_mutable`** en NODO_PUNTERO (t=36):
   - `vi & 1 == 0` → referencia inmutable (`&`)
   - `vi & 1 == 1` → referencia mutable (`&mut`)
   - El puente lee `bool(vi & 1)` → `ExprObtenerDireccion.es_mutable`

2. **Parser SyQuex corrige `&mut`** — verifica literalmente "mut" (no consume cualquier identificador de 3 letras) y establece `valor_int = 1` en el NODO_PUNTERO resultante.

3. **`archivo` se añade como header JSON** (no por nodo) en la versión "2" del formato — futuro LSP puede usarlo para diagnostics.

4. **Los nodos `NODO_PARRAFO` (33) y `NODO_VACIO` (44)** se añaden al verificador ABI (`ast_abi_verificar`).

### No se modifica

- La ABI v1 (AST_ABI_VERSION=1, AST_ABI_NODOS_CAMPOS=10) **NO cambia** — los nuevos bits/metadata se codifican dentro de campos existentes.
- El `union` tipado del Manual 6 §1.2 no se implementa — el puente S1 ya resuelve tipos dinámicamente.
