# PLAN DE ALINEACIÓN ESTRICTA — Manuales 1-9 vs Código

> **Fecha:** 2026-09-12
> **Auditor:** Agente opencode (mimo-v2.5-free)
> **Alcance:** TODOS los manuales (1-9), TODOS los archivos .syn/.c/.syq, TODOS los tests
> **Objetivo:** Cada línea de código DEBE cumplir los manuales al pie de la letra

---

## RESUMEN EJECUTIVO

| Severidad | Cantidad | Acción requerida |
|-----------|----------|------------------|
| **CRITICAL** | 28 | Corregir ANTES de cualquier otro trabajo |
| **MEDIUM** | 26 | Corregir en el sprint actual |
| **LOW** | 15 | Documentar y planificar |
| **Total desviaciones** | **69** | — |

---

## 1. DESVIACIONES CRITICAL (28)

### 1.1 — Manual 1 §3.2/§4: Extensiones de archivos Syquex (.syn vs .syq)

| # | Manual dice | Código tiene | Archivos afectados |
|---|------------|-------------|-------------------|
| C1 | `lexer.syq`, `parser.syq`, `traductor.syq` | `syquex/lexer.syn`, `parser.syn`, `traductor.syn` | syquex/*.syn |
| C2 | `lib/gui.syq` (GTK bindings) | **NO EXISTE** | — |
| C3 | `lib/json.syq`, `lib/ia.syq`, `lib/ffi.syq` | **NO EXISTEN** | — |

**Remediación:** Mover archivos `.syn` a `.syq` cuando el compilador Syquex esté operativo (bootstrap paradox D-F22-A). Los `lib/` son Fase 24.

### 1.2 — Manual 1 §4: Estructura runtime incompleta

| # | Manual dice | Código tiene |
|---|------------|-------------|
| C4 | `runtime/net/http.c` | `runtime/core/http.c` (ruta diferente) |
| C5 | `runtime/quantum/matrix.c` | `nucleo/quantum_runtime.c` |
| C6 | `runtime/ml/gguf.c` | `runtime/core/modelo.c` |
| C7 | `runtime/federated/aggregator.c` | `nucleo/federated.c` |
| C8 | Subdirectorios `net/`, `quantum/`, `ml/`, `federated/` | Solo `runtime/core/` existe |

**Remediación:** Crear subdirectorios y mover/mover archivos según Manual 1 §4.

### 1.3 — Manual 1 §4: `opensyn/orchestrator.c` ausente

| # | Manual dice | Código tiene |
|---|------------|-------------|
| C9 | `opensyn/orchestrator.c` | Solo `opensyn/orchestrator.h` (sin .c) |

**Remediación:** Crear `orchestrator.c` con la lógica de orquestación.

### 1.4 — Manual 2 §5: Contratos (requiere/garantiza)

| # | Manual dice | Código tiene | Archivo:línea |
|---|------------|-------------|---------------|
| C10 | TODAS las funciones públicas tienen `requiere`+`garantiza` | 8 funciones SIN contratos | principal.syn:225,231,264,1369,1674 + 3 más |
| C11 | Variable de resultado es `_resultado_` | Usan `resultado` (sin underscores) | TODOS los archivos (~40 bloques) |
| C12 | `externo funcion` requiere contratos | 34 declaraciones SIN contratos | principal.syn:17-50 |

**Remediación:** Agregar `requiere`/`garantiza` a cada función pública; renombrar `resultado` → `_resultado_` en todos los bloques de contrato.

### 1.5 — Manual 2 §2 EBNF: Keywords

| # | Manual dice | Código tiene | Archivo:línea |
|---|------------|-------------|---------------|
| C13 | Keyword `let` para declarar variables | `variable` (keyword inventado) | principal.syn:638 |

**Remediación:** Cambiar `variable` → `let` en todo el código.

### 1.6 — Manual 2 §5.1: `externo funcion` no está en la EBNF

| # | Manual dice | Código tiene |
|---|------------|-------------|
| C14 | EBNF solo define `funcion` (sin `externo`) | 34 `externo funcion` declarations |
| C15 | Grammar no contempla `externo` como prefijo de `funcion` | No hay producción gramatical para esto |

**Remediación:** O agregar `externo` a la EBNF del Manual 2, o reestructurar las declaraciones. Requiere decisión del Arquitecto.

### 1.7 — Manual 3 §3: Parser Syquex incompleto

| # | Manual dice | Código tiene | Severidad |
|---|------------|-------------|-----------|
| C16 | `importar modulo.submodulo.como alias` | Solo consume un identificador | CRITICAL |
| C17 | Enum cases con parámetros: `Casos(tipo1, tipo2)` | Solo lee identificador (sin tipos) | CRITICAL |
| C18 | `retornar expr?` (propagación con `?`) | Usa `->` en lugar de `?` | CRITICAL |

**Remediación:** Extender parser.syn para soportar importaciones punteadas, enum cases con tipos, y `retornar ?`.

### 1.8 — Manual 7 §4: LSP commands ausentes

| # | Manual dice | Código tiene |
|---|------------|-------------|
| C19 | `synapse/aiStatus` | NO implementado |
| C20 | `synapse/aiExplain` | NO implementado |
| C21 | `synapse/aiComplete` | NO implementado |
| C22 | `synapse/aiFix` | NO implementado |
| C23 | `synapse/aiTranspile` | NO implementado |
| C24 | `synapse/aiBindings` | NO implementado |

**Remediación:** Implementar los 6 commands LSP en `nucleo/lsp.syn`.

### 1.9 — Manual 7 §6.3: `generar_codigo_ia()` es stub

| # | Manual dice | Código tiene |
|---|------------|-------------|
| C25 | Función que llama al modelo para generar código | Retorna `""` (stub vacío) |

**Remediación:** Conectar `generar_codigo_ia()` con `_syn_ollama_consultar()`.

### 1.10 — Manual 8 §4.2: `--check`/`--no-emit` no implementado

| # | Manual dice | Código tiene |
|---|------------|-------------|
| C26 | Flag `--check` para validación sin generar binario | No existe |

**Remediación:** Agregar flag `--check` en el CLI.

### 1.11 — Manual 9 §2.4: Instalador Linux

| # | Manual dice | Código tiene |
|---|------------|-------------|
| C27 | Descarga de GitHub Releases | Copia local de `build/bin/` |
| C28 | Sin integración OpenSyn, sin PATH, sin detección arquitectura | Solo copia simple |

**Remediación:** Reescribir `install.sh` según Manual 9.

---

## 2. DESVIACIONES MEDIUM (26)

### 2.1 — Manual 2 §5: Contratos parciales

| # | Descripción | Archivos |
|---|------------|----------|
| M1 | 6 funciones con `requiere` pero sin `garantiza` | principal.syn, router.syn |
| M2 | `#` comments no definidos en EBNF | router.syn:2-3 |
| M3 | Uso excesivo de `inseguro: asm()` (15+ bloques) | Todos los archivos opensyn |
| M4 | `texto[i]` indexing no definido en EBNF | permisos.syn, run_manager.syn |
| M5 | `+` para concatenación (no en grammar) | router.syn:54-121 |

### 2.2 — Manual 3 §3: Parser features faltantes

| # | Descripción | Sección |
|---|------------|---------|
| M6 | Estructura genérica `(T)` no parseada | §3 L88 |
| M7 | `@export` solo funciones, no estructuras | §3 L100 |
| M8 | `intentar/atrapar` forma funcional no implementada | §3 L148 |
| M9 | `continuar` vs `siguiente` (keyword equivocado) | §3 L151 |
| M10 | Expresiones `rc()/arc()/débil()/arena()` no parseadas | §3 L197 |
| M11 | `ffi_marshaling.syq` sin `#lang: es` obligatorio | §1.1 |

### 2.3 — Manual 7: OpenSyn features

| # | Descripción | Sección |
|---|------------|---------|
| M12 | Puerto manual 8088 vs código 11434 | §2.1 |
| M13 | n_ctx hardcodeado, sin split 30/70 | §2.3 |
| M14 | Diagnostics siempre string vacío | §2.3 |
| M15 | Sin model switching real | §2.4 |
| M16 | Timeout definido pero nunca enforced | §4.3 |
| M17 | Error line/column hardcoded a 0 | §6.3 |
| M18 | Config missing `[rag]` y `[generacion]` sections | §6.2 |
| M19 | Sin smoke test post-instalación | §6.1 |
| M20 | Solo `opensyn status`; faltan 4 CLI commands | §6.4 |
| M21 | Feedback guardado en failure automático, no en corrección manual | §6.3 |
| M22 | Fine-tuning (LoRA) no implementado | §3.2 |
| M23 | `@export` bindings no implementados | §5.3 |

### 2.4 — Manuales 4/5/6/8: Features

| # | Descripción | Manual |
|---|------------|--------|
| M24 | Canal struct missing `tipo_tamano` y `destructor` | Manual 5 §3.4 |
| M25 | SemNodo flat 10-field vs manual rich struct con ownership | Manual 6 §1.2 |
| M26 | 10/16 LSP methods core ausentes | Manual 8 §1.4 |

---

## 3. DESVIACIONES LOW (15)

| # | Descripción | Manual |
|---|------------|--------|
| L1 | `lsp_v3.syn` + `lsp.syn` (duplicados) | Manual 1 §4 |
| L2 | `synapse_rag.c` en nucleo/ Y opensyn/ (duplicado) | Manual 1 §4 |
| L3 | `llama_client.c` en nucleo/ Y opensyn/ (duplicado) | Manual 1 §4 |
| L4 | `transpiler.syq` vs `transpiler.syn` | Manual 1 §4 |
| L5 | Números de ejemplo diferentes en examples/ | Manual 1 §4 |
| L6 | Estructura docs/ diferente (manuales/ vs root) | Manual 1 §4 |
| L7 | Workflows: `ci-tests.yml` vs `test.yml` | Manual 1 §4 |
| L8 | Mezcla `longitud()`/`strlen_s()` | Manual 2 §4.3 |
| L9 | `#lang:` en parser no parseado como nodo | Manual 3 §3 |
| L10 | `escuchar` más permisivo que grammar | Manual 3 §3 |
| L11 | `delegar` keyword sin uso | Manual 3 §4 |
| L12 | `Resultado`/`Opcion` como llamadas genéricas | Manual 3 §5.4 |
| L13 | Cleanup Blocks no generados en codegen | Manual 4 §5.2 |
| L14 | Fibras/scheduler con campos extra vs manual | Manual 5 §2.6 |
| L15 | `--check` LSP: solo 6/16 core methods | Manual 8 §1.4 |

---

## 4. ORDEN DE REMEDIACIÓN (por prioridad)

### Fase A: Fundamentos críticos (sin esto nada compila correctamente)
1. **C11** — Renombrar `resultado` → `_resultado_` en todos los bloques de contrato (~40 bloques, 6 archivos)
2. **C13** — Cambiar `variable` → `let` (1 sitio, principal.syn:638)
3. **C10+C12** — Agregar contratos a funciones públicas sin ellos (8 funciones + 34 externs)
4. **M2** — Cambiar `#` comments → `//` en router.syn

### Fase B: Parser Syquex (habilita compilación de .syq)
5. **C16** — Importaciones punteadas con alias en parser.syn
6. **C17** — Enum cases con parámetros tipados
7. **C18** — `retornar ?` en lugar de `->`
8. **M6** — Estructura genérica `(T)`
9. **M7** — `@export` para estructuras
10. **M8** — `intentar/atrapar` forma funcional
11. **M10** — Expresiones `rc()/arc()/débil()/arena()`
12. **M11** — Agregar `#lang: es` a ffi_marshaling.syq

### Fase C: OpenSyn funcional
13. **C25** — Conectar `generar_codigo_ia()` con Ollama
14. **M12** — Alinear puerto (8088 o 11434, decidir con Arquitecto)
15. **M13** — n_ctx split 30/70 real
16. **M16** — Enforce timeout en query path
17. **M17** — Parsear error line/column de compiler output
18. **M18** — Agregar `[rag]` y `[generacion]` a config
19. **M19** — Smoke test post-instalación
20. **M20** — Implementar `opensyn download/finetune/bindings/transpile`

### Fase D: LSP (habilita VS Code)
21. **C19-C24** — Implementar 6 LSP commands
22. **C26** — Flag `--check`/`--no-emit`
23. **M26** — Completar 10 LSP methods core

### Fase E: Infraestructura
24. **C4-C8** — Crear subdirectorios runtime/
25. **C9** — Crear `opensyn/orchestrator.c`
26. **C27-C28** — Reescribir install.sh

### Fase F: Documentación
27. **C1-C3** — Actualizar manuales para reflejar estado real (o mover archivos)
28. **L1-L15** — Resolver desviaciones cosméticas

---

## 5. ARCHIVOS AFECTADOS (por archivo)

| Archivo | CRITICAL | MEDIUM | LOW | Total |
|---------|----------|--------|-----|-------|
| `opensyn/principal.syn` | 5 | 3 | 1 | 9 |
| `opensyn/router.syn` | 0 | 4 | 1 | 5 |
| `opensyn/permisos.syn` | 0 | 2 | 0 | 2 |
| `opensyn/run_manager.syn` | 0 | 2 | 0 | 2 |
| `opensyn/validation_loop.syn` | 1 | 1 | 0 | 2 |
| `opensyn/planificador.syn` | 0 | 1 | 0 | 1 |
| `syquex/parser.syn` | 3 | 4 | 1 | 8 |
| `syquex/lexer.syn` | 0 | 1 | 0 | 1 |
| `syquex/traductor.syn` | 0 | 1 | 0 | 1 |
| `syquex/expr.syn` | 0 | 1 | 0 | 1 |
| `syquex/ffi_marshaling.syq` | 0 | 1 | 0 | 1 |
| `nucleo/lsp.syn` | 6 | 1 | 1 | 8 |
| `runtime/core/*.c` | 0 | 2 | 0 | 2 |
| `install.sh` | 1 | 0 | 0 | 1 |
| **TOTAL** | **16** | **24** | **4** | **44** |

---

## 6. DECISIONES REQUERIDAS DEL ARQUITECTO

1. **C14/C15** — ¿Agregar `externo` a la EBNF del Manual 2, o reestructurar el código?
2. **M12** — ¿Puerto 8088 (Manual 7) o 11434 (Ollama default)?
3. **C1-C3** — ¿Mover archivos .syn → .syq ahora (sabiendo que no compilan como .syq aún)?
4. **C4-C8** — ¿Reorganizar runtime/ ahora o esperar a Fase 16?
5. **M3** — ¿Reducir `inseguro: asm()` o justificar cada uno?

---

## 7. ESTADO DE TESTS (post-último commit)

```
331 tests GREEN, 0 failures
0 breaches verificar_alineacion.py
```

**Nota:** Los tests actuales PASAN pero no cubren las desviaciones documentadas arriba. Los tests verifican funcionalidad, no alineación con manuales.

---

*Documento generado automáticamente por la auditoría de alineación estricta.*
*Última actualización: 2026-09-12*
