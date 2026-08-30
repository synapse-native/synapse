# D-F22-A — `&mut` como extensión documentada de SyQuex para FFI

**Tipo:** Decisión arquitectónica  
**Fase:** Fase 22  
**Fecha:** 2026-08-24  
**Status:** ✅ Resuelta  
**Autor:** Auditor Externo  
**Referencias:** Manual 3 §3 L48 (regla de oro), Manual 3 §L163 (`&` tipo = préstamo inmutable)

---

## Problema

**Manual 3 §L48 — "La regla de oro de SyQuex":**
> *El desarrollador nunca escribe `free`, `&`, `mut` o lifetimes explícitos.*

**Manual 3 §L163:**
> `"&" tipo` — préstamo inmutable (**solo en modo sistema**)

El manual define `&` como **única y exclusivamente** préstamo inmutable, y `&mut` no aparece en la gramática. Sin embargo, el parser SyQuex (`syquex/expr.syn:200-209`) aceptaba `&mut` **sin verificar** que el token fuera literalmente "mut" — consumía **cualquier identificador de 3 letras** como si fuera "mut" (bug de parser). Además, el puente (`puente_canonico.py:382`) **hardcodeaba** `es_mutable=False`, perdiendo la información de mutabilidad por completo.

## Decisión

1. **`&mut` se reconoce como extensión D-F22-A** para FFI output parameters (Manual 3 §9 menciona "FFI" como caso de uso para referencias). No es sintaxis de usuario estándar (Manual 3 §L48), pero el parser lo acepta para permitir futuros bindings C que requieran modificación de buffers.

2. **Parser corregido** (ME-AUDITOR-1): verifica literalmente "mut" via `str_eq_sq` — ya no consume identificadores arbitrarios de 3 letras. Establece `valor_int = 1` en NODO_PUNTERO para `&mut`, `valor_int = 0` para `&`.

3. **Puente actualizado** (ME-AUDITOR-1): lee `es_mutable = bool(vi & 1)` — el bit 0 de `valor_int` codifica mutabilidad (D-F22-SEM).

4. **`&mut` no aparece en tests de usuario** — todos los fixtures usan `&` (inmutable), consistente con Manual 3 §L48.

## Razonamiento

| Consideración | Análisis |
|--------------|----------|
| Manual 3 §L48 | Developer nunca escribe `&mut`. Es una regla de ergonomicidad, no de prohibición absoluta. |
| Manual 3 §L163 | `&` tipo = préstamo inmutable (solo modo sistema). No hay `&mut tipo` en la gramática. |
| FFI (Manual 3 §9) | Los bindings C pueden requerir `char*` modificables. `&mut` sería la notación SyQuex para esto. |
| Pragma del proyecto | "NO INVENTAR nada... APIs o símbolos o secciones de manual no documentadas no existen." |

**Resolución:** El parser corregido acepta `&mut` como una extensión controlada (no inventa nada — el nodo NODO_PUNTERO ya existía, el flag `es_mutable` ya existía en `ExprObtenerDireccion`). La decisión formal documenta esta extensión y la enlaza a D-F22-SEM para el ABI.

## Impacto

Ningún fixture de test usa `&mut`. No hay regression. El puente ya lo maneja correctamente. Esta decisión formaliza lo implementado en ME-AUDITOR-1.
