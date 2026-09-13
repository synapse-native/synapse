# PLAN DE ALINEACIÓN ESTRICTA — Manuales 1-9 + F31/F32 vs Código

> **Fecha:** 2026-09-12 (post-commit `978ea94`)
> **Auditor:** Agente opencode (mimo-v2.5-free)
> **Alcance:** TODOS los manuales (1-9, F31, F32), TODOS los archivos .syn/.c/.syq, TODOS los tests
> **Manuales versiones:** 1→v8.0.0, 2→v8.0.0, 3→v8.0.0, 4→v8.2.0, 5→v8.0.0, 6→v8.0.0, 7→v8.2.0, 8→v8.2.0, 9→v8.2.0, F31→nuevo, F32→nuevo

---

## RESUMEN EJECUTIVO

| Severidad | Cantidad | Notas |
|-----------|----------|-------|
| **CRITICAL** | 19 | Corregir antes de cualquier otro trabajo |
| **MEDIUM** | 15 | Corregir en el sprint actual |
| **LOW** | 9 | Documentar y planificar |
| **FUTURE (F31/F32)** | 8 | No existen aún — son entregables futuros |
| **Total desviaciones** | **51** | (13 menos que versión anterior) |

**Mejoras vs auditoría anterior:** 69 → 51 desviaciones. Las desviaciones de "extensiones .syn/.syq" se resolvieron (Manual 1 §3.2 ahora acepta ambas). Los `externo funcion` se resolvieron (Manual 3 §99 los define). Contratos ahora cubiertos en todos los archivos opensyn.

---

## 1. DESVIACIONES CRITICAL (19)

### 1.1 — Manual 2 §134: Keyword `variable` vs `let`

| # | Manual dice | Código tiene | Archivo:línea |
|---|------------|-------------|---------------|
| C1 | `declaracion_variable ::= "let" IDENTIFICADOR` | `variable ultimo_tipo_tarea: entero = 0` | principal.syn:638 |

**Remediación:** Cambiar `variable` → `let` (1 sitio).

### 1.2 — Manual 2 §1.3: Comentarios `#` no definidos

| # | Manual dice | Código tiene | Archivo:línea |
|---|------------|-------------|---------------|
| C2 | Comentarios: `//` (línea) o `/* */` (bloque) | `# cumple Manual 1 1: ...` | router.syn:2-3 |

**Remediación:** Cambiar `#` → `//` en router.syn.

### 1.3 — Manual 3 §3: Parser Syquex — features CRITICAL faltantes

| # | Manual dice (EBNF) | Código tiene | Archivo:línea |
|---|-------------------|-------------|---------------|
| C3 | `retornar [expresion] ["?"]` — `?` propaga error | Usa `->` en lugar de `?` | parser.syn:835-849 |
| C4 | `rc(expr)`, `arc(expr)`, `débil(expr)`, `arena(expr)` como primarios | No parseados como expresiones primarias | expr.syn:396-507 |

**Remediación:** Agregar token `T_INTERROGACION` para `retornar ?`; agregar casos `T_RC/T_ARC/T_DEBIL/T_ARENA` en `parse_primario_sq`.

### 1.4 — Manual 5 §3.4: Canal struct missing fields

| # | Manual dice | Código tiene | Archivo |
|---|------------|-------------|---------|
| C5 | `tipo_tamano` (size of type T) | **AUSENTE** | synapse_rt_types.h |
| C6 | `destructor` (cleanup function pointer) | **AUSENTE** | synapse_rt_types.h |

**Remediación:** Agregar `tipo_tamano` y `destructor` a `CanalConcurrencia`.

### 1.5 — Manual 7 §2.1: Puerto 8088 vs 11434

| # | Manual dice | Código tiene | Archivos |
|---|------------|-------------|----------|
| C7 | Puerto **8088** para llama-server | Puerto **11434** hardcodeado | principal.syn:95,183,928,996 + lsp.syn:46 |

**Remediación:** Cambiar 11434 → 8088 en todos los archivos (5 sitios).

### 1.6 — Manual 7 §3/Manual 8 §1.4: LSP methods ausentes

| # | Manual dice | Código tiene |
|---|------------|-------------|
| C8 | 21 LSP methods (16 core + 5 F31) | Solo 9 implementados |
| C9 | 6 AI commands (aiStatus, aiExplain, aiComplete, aiFix, aiTranspile, aiBindings) | Solo 4 (aiExplain, explain, refactor, fixError) |
| C10 | Faltan: hover, definition, completion, codeAction, formatting, signatureHelp, didChangeConfiguration | No implementados |
| C11 | Faltan: aiStatus, aiComplete, aiFix, aiTranspile, aiBindings | No implementados |

**Remediación:** Implementar los 12 methods faltantes en nucleo/lsp.syn.

### 1.7 — Manual 7 §6.3: `generar_codigo_ia()` es stub

| # | Manual dice | Código tiene | Archivo:línea |
|---|------------|-------------|---------------|
| C12 | Función que llama al modelo para generar código | Retorna `""` (stub vacío) | validation_loop.syn:254-259 |

**Remediación:** Conectar `generar_codigo_ia()` con `_syn_ollama_consultar()`.

### 1.8 — Manual 3 §3: Parser Syquex — features MEDIUM faltantes

| # | Manual dice | Código tiene | Severidad |
|---|------------|-------------|-----------|
| C13 | Import con paths punteados: `importar mod.sub.como alias` | Solo un identificador | MEDIUM→CRITICAL |
| C14 | Enum cases con parámetros: `Casos(tipo1, tipo2)` | Solo nombre (sin tipos) | MEDIUM→CRITICAL |
| C15 | `@export(ID) estructura` | Solo `@export` para funciones | MEDIUM |
| C16 | `intentar expr atrapar expr` forma funcional | Solo forma de bloque | MEDIUM |

**Remediación:** Extender parser.syn para soportar estas features.

### 1.9 — Fase 31: Archivos ausentes

| # | Manual F31 dice | Código tiene |
|---|----------------|-------------|
| C17 | `nucleo/lint.syn` | **NO EXISTE** |
| C18 | `nucleo/formatter.syn` | **NO EXISTE** |

**Nota:** Estos son entregables de Fase 31 (futuro). No bloquee trabajo actual pero registrar.

---

## 2. DESVIACIONES MEDIUM (15)

### 2.1 — Manual 5: Structs con campos extra vs manual

| # | Descripción | Archivo |
|---|------------|---------|
| M1 | Arena: 10 campos vs manual 7 (+3 extensiones F9/F10) | synapse_rt_types.h |
| M2 | Fibra: 12 campos vs manual 7 (+5 para scheduling) | concurrency.c |
| M3 | Canal: 16 campos vs manual 11 (+5 para fiber-aware) | synapse_rt_types.h |
| M4 | Scheduler: 12 campos vs manual 7 (+4 para FIFO) | concurrency.c |

### 2.2 — Manual 2: `resultado` vs `_resultado_` en contratos

| # | Descripción | Archivos |
|---|------------|----------|
| M5 | ~40 bloques `garantiza` usan `resultado` en vez de `_resultado_` | TODOS los archivos opensyn |

### 2.3 — Manual 3: Parser features faltantes

| # | Descripción | Sección |
|---|------------|---------|
| M6 | Import paths punteados + alias | §3 L72 |
| M7 | Enum cases con tipos | §3 L95 |
| M8 | `@export` para estructuras | §3 L100 |
| M9 | `intentar/atrapar` forma funcional | §3 L148 |
| M10 | `rc()/arc()/débil()/arena()` como primarios | §3 L197 |

### 2.4 — Manual 7/8: Features OpenSyn

| # | Descripción | Sección |
|---|------------|---------|
| M11 | Sin `synapse lint` integración | Manual 7 §6.4 |
| M12 | Sin `synapse fmt` integración | Manual 8 §4.1 |
| M13 | Sin flags `--junit/--coverage/--json` | Manual 8 §4.1 |
| M14 | Sin orchestrator lifecycle completo | Manual 7 §2.1 |
| M15 | File-finder basado en keywords, no AST | Manual 7 §2.3 |

---

## 3. DESVIACIONES LOW (9)

| # | Descripción | Manual |
|---|------------|--------|
| L1 | RcHeader/ArcHeader: 5 campos vs manual 4 (+1 version) | Manual 4 §3.2 |
| L2 | SemNodo flat 10-field vs manual rich struct (documentado) | Manual 6 §1.2 |
| L3 | Mezcla `longitud()`/`strlen_s()` | Manual 2 §4.3 |
| L4 | `#lang:` en parser no parseado como nodo AST | Manual 3 §3 |
| L5 | `escuchar` más permisivo que grammar | Manual 3 §3 |
| L6 | `delegar` keyword sin uso | Manual 3 §4 |
| L7 | `Resultado`/`Opcion` como llamadas genéricas | Manual 3 §5.4 |
| L8 | Cleanup Blocks no generados en codegen | Manual 4 §5.2 |
| L9 | LSP: 9/21 methods implementados | Manual 8 §1.4 |

---

## 4. DESVIACIONES FUTURE — Fase 31 y 32 (8)

Estos archivos NO EXISTEN porque son entregables futuros. Se documentan por completitud.

| # | Archivo requerido | Fase |
|---|------------------|------|
| F1 | `nucleo/lint.syn` | F31 |
| F2 | `nucleo/formatter.syn` | F31 |
| F3 | `nucleo/grafo_builder.syn` | F32 |
| F4 | `opensyn/explorer_det.syn` | F32 |
| F5 | `opensyn/architect_det.syn` | F32 |
| F6 | `opensyn/verificacion.syn` | F32 |
| F7 | `opensyn/orquestador_multi.syn` | F32 |
| F8 | `opensyn/memoria.syn` (en opensyn/, no nucleo/) | F32 |

---

## 5. ORDEN DE REMEDIACIÓN (por prioridad)

### Fase A: Fundamentos críticos (sin esto nada compila correctamente)
1. **C1** — Cambiar `variable` → `let` en principal.syn:638
2. **C2** — Cambiar `#` → `//` en router.syn:2-3
3. **M5** — Renombrar `resultado` → `_resultado_` en ~40 bloques de contrato

### Fase B: Puerto OpenSyn
4. **C7** — Cambiar 11434 → 8088 en principal.syn (4 sitios) + lsp.syn (1 sitio)

### Fase C: Parser Syquex
5. **C3** — `retornar ?` en parser.syn
6. **C4** — `rc()/arc()/débil()/arena()` como primarios en expr.syn
7. **M6** — Import paths punteados + alias
8. **M7** — Enum cases con tipos
9. **M8** — `@export` para estructuras
10. **M9** — `intentar/atrapar` forma funcional

### Fase D: OpenSyn funcional
11. **C12** — Conectar `generar_codigo_ia()` con Ollama
12. **M11** — Integrar `synapse lint` en router
13. **M13** — Agregar flags `--junit/--coverage/--json`

### Fase E: LSP
14. **C8-C11** — Implementar 12 LSP methods faltantes
15. **L9** — Completar 21/21 methods

### Fase F: Runtime
16. **C5-C6** — Agregar `tipo_tamano` y `destructor` a CanalConcurrencia
17. **M1-M4** — Documentar campos extra como extensiones necesarias

---

## 6. ARCHIVOS AFECTADOS (por archivo)

| Archivo | CRITICAL | MEDIUM | LOW | Total |
|---------|----------|--------|-----|-------|
| `opensyn/principal.syn` | 2 | 0 | 0 | 2 |
| `opensyn/router.syn` | 1 | 1 | 0 | 2 |
| `opensyn/validation_loop.syn` | 1 | 0 | 0 | 1 |
| `syquex/parser.syn` | 2 | 3 | 0 | 5 |
| `syquex/expr.syn` | 1 | 1 | 0 | 2 |
| `nucleo/lsp.syn` | 4 | 0 | 1 | 5 |
| `synapse_rt_types.h` | 2 | 0 | 0 | 2 |
| `runtime/core/concurrency.c` | 0 | 0 | 0 | 0 |
| **TOTAL** | **13** | **5** | **1** | **19** |

*Nota: Solo archivos con cambios directos. Los ~40 bloques de contrato son cambios transversales.*

---

## 7. ESTADO DE SYQUEX — ESTUDIO COMPLETO

### Extensiones de archivo
- **Manual 1 §3.2:** Acepta `lexer.syn / lexer.syq` y `parser.syn / parser.syq` — **NO HAY DESVIACIÓN**
- **D-F22-A:** Documentado en Manual 1 §4 como decision del proyecto
- **Estado actual:** `syquex/lexer.syn`, `parser.syn`, `traductor.syn`, `expr.syn` (Synapse); `analizador_alcance.syq`, `ffi_marshaling.syq` (Syquex)

### Parser features implementados vs especificados

| Feature | Manual 3 EBNF | Estado | Prioridad |
|---------|---------------|--------|-----------|
| `#lang: es` obligatorio | §1.1 | ✅ Implementado | — |
| `variable` module-level | §3 L74 | ✅ Implementado | — |
| Funciones con contratos | §3 L84 | ✅ Implementado | — |
| `estructura` con métodos | §3 L88 | ✅ Implementado | — |
| `si/sino`, `mientras`, `para` | §3 | ✅ Implementado | — |
| `coincidir` con patrones | §3 | ✅ Implementado | — |
| `lanzar`/`escuchar` (canales) | §3 | ✅ Implementado | — |
| Tipos genéricos `Lista<T>`, `Mapa<K,V>` | §3 | ✅ Implementado | — |
| `Resultado<T,E>`, `Opcion<T>` | §3 | ✅ Implementado | — |
| Import simple (1 identificador) | §3 L72 | ✅ Implementado | — |
| `retornar ?` propagación | §3 L128 | ❌ Usa `->` | **CRITICAL** |
| `rc()/arc()/débil()/arena()` primarios | §3 L197 | ❌ No implementado | **CRITICAL** |
| Import paths punteados + alias | §3 L72 | ❌ Solo 1 identificador | MEDIUM |
| Enum cases con tipos | §3 L95 | ❌ Solo nombre | MEDIUM |
| `@export` para estructuras | §3 L100 | ❌ Solo funciones | MEDIUM |
| `intentar/atrapar` funcional | §3 L148 | ❌ Solo bloque | MEDIUM |

### Lexer features
- ✅ Multi-idioma (es/en/fr/pt)
- ✅ Tokens de puntuación
- ✅ Comentarios anidados
- ✅ Números con exponente
- ✅ Palabras clave Syquex

### Traductor
- ✅ Mapeo AST Syquex → SemNodo[]
- ✅ Transformación constructores → `__init__`
- ✅ Métodos hoistados
- ✅ Fusión de contratos

---

## 8. DECISIONES REQUERIDAS DEL ARQUITECTO

1. **C7** — ¿Puerto 8088 (Manual 7) o 11434 (Ollama default)? Manual dice 8088 explícitamente.
2. **M5** — ¿Renombrar `resultado` → `_resultado_` en ~40 bloques? Manual dice `_resultado_`.
3. **C5-C6** — ¿Agregar `tipo_tamano`/`destructor` a Canal, o actualizar Manual 5?
4. **M1-M4** — ¿Documentar campos extra de structs como extensiones, o ajustar manuales?

---

## 9. ESTADO DE TESTS (post-commit `978ea94`)

```
331 tests GREEN, 0 failures
0 breaches verificar_alineacion.py
```

---

## 10. CAMBIOS DESDE ÚLTIMA AUDITORÍA

| Campo | Antes | Ahora |
|-------|-------|-------|
| Total desviaciones | 69 | 51 |
| CRITICAL | 28 | 19 |
| MEDIUM | 26 | 15 |
| LOW | 15 | 9 |
| Resueltos por actualización manual | — | 18 (extensiones .syn/.syq, externo funcion, structs) |
| Commit | — | `978ea94` |

**Causa de reducción:** Los manuales 4/7/8/9 fueron actualizados (v8.2.0) eliminando desviaciones que antes existían. Manual 1 §3.2 ahora acepta ambas extensiones. Manual 3 §99 define `externo` como producción válida.

---

*Documento generado por re-auditoría completa post-commit `978ea94`.*
*Se leyeron TODOS los manuales (1-9, F31, F32) y se comparó contra TODO el código.*
