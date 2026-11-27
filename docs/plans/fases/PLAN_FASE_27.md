# PLAN DE TRABAJO — Fase 27 + Refactorización asm() → Synapse Puro

**Fecha:** 2026-08-26
**Fase actual:** 27 (Herramientas de Desarrollo)
**Hallazgo:** 47 archivos .syn usan `asm()` (~11,861 llamadas). Manual 8 §1.2 muestra LSP en Synapse puro.
**Deuda registrada:** D-14 (M8 §1.2 requiere Synapse puro, stdlib insuficiente)

---

## CONTEXTO

### Auditoría de `asm()` en el codebase

| Directorio | Archivos | Líneas | `asm()` | % Promedio |
|------------|----------|--------|---------|------------|
| nucleo/ (productivos) | 22 | 14,515 | 6,302 | 43% |
| nucleo/generador/ | 11 | 4,331 | 3,195 | 74% |
| nucleo/_tmp_* (test drivers) | 5 | 13,675 | 1,851 | 13% |
| syquex/ | 6 | 3,698 | 479 | 13% |
| opensyn/ | 1 | 276 | 8 | 3% |
| std/ | 2 | 489 | 26 | 5% |
| **TOTAL** | **47** | **36,984** | **~11,861** | — |

### Top 5 archivos más afectados

1. `nucleo/generador/funciones.syn` — 96.4% asm (325/337 líneas)
2. `nucleo/generador/expr_eval.syn` — 95.0% asm (458/482 líneas)
3. `nucleo/principal.syn` — 90.6% asm (767/847 líneas)
4. `nucleo/generador/nodos_flujo.syn` — 88.6% asm (946/1,068 líneas)
5. `nucleo/generador/recorrido.syn` — 88.4% asm (268/303 líneas)

### ¿Por qué hay tanto `asm()`?

El `asm()` de Synapse no es ensamblador — es **emisión de código C literal**. El compilador es auto-alojado: compila su propio código. El generador necesita emitir C, y `asm()` es el mecanismo de transporte. Ejemplo:

```synapse
// generator.syn — esto NO es ensamblador, es código C embebido
asm("fprintf(stderr, \"[DEBUG] token: %s\\n\", _tk.lexema);")
```

### Restricción de stdlib para LSP puro

Para implementar el LSP en Synapse puro (M8 §1.2), faltan primitivas críticas:

1. **Lectura binaria de stdin** — `leer_linea()` lee hasta `\n`, pero el body JSON puede contener `\n`
2. **`snprintf` / strings formateados** — No hay equivalente para construir JSON dinámico
3. **Funciones de string** — `contiene`, `indice_de`, `reemplazar` existen en C pero no como builtins

---

## FASE 27 — PLAN CON MICRO-ENTREGABLES

### Fase 27.1: Extensión de stdlib (prerequisito para LSP puro)

| ME | Descripción | Archivos | Tests | Manual |
|----|-------------|----------|-------|--------|
| ME-F27-S1 | `leer_bytes_stdin(n: entero) -> texto` — lee exactamente N bytes de stdin | `std/io.syn` + `runtime/core/io.c` | 3 | M8 §1.2 |
| ME-F27-S2 | `sprintf(formato: texto, args...) -> texto` — formato de strings | `std/texto.syn` + `runtime/core/texto.c` | 5 | M8 §1.6 |
| ME-F27-S3 | Builtins: `contiene`, `indice_de`, `reemplazar`, `recortar` | `compilador/analizador_semantico.syn` + `runtime/core/texto.c` | 8 | M2 §3 |
| ME-F27-S4 | `leer_linea_stdin() -> texto` — wrapper de `leer_linea` para stdin | `std/io.syn` | 2 | M8 §1.2 |

**Criterio de aceptación 27.1:** Los 18 tests pasan. `std/io.syn` y `std/texto.syn` compilan sin `asm()`.

### Fase 27.2: LSP Synapse puro (M8 §1)

| ME | Descripción | Archivos | Tests | Manual |
|----|-------------|----------|-------|--------|
| ME-F27-L1 | Refactorizar `leer_cabecera()` y `leer_mensaje()` a Synapse puro | `nucleo/lsp.syn` | 3 | M8 §1.2 |
| ME-F27-L2 | Refactorizar `responder_json()` a Synapse puro (sprintf) | `nucleo/lsp.syn` | 2 | M8 §1.2 |
| ME-F27-L3 | Refactorizar `initialize`/`initialized`/`shutdown`/`exit` | `nucleo/lsp.syn` | 4 | M8 §1.3 |
| ME-F27-L4 | Refactorizar `textDocument/didOpen`/`didChange`/`didClose` + diagnostics | `nucleo/lsp.syn` | 3 | M8 §1.3 |
| ME-F27-L5 | Implementar `textDocument/hover` (M8 §1.4) | `nucleo/lsp.syn` | 3 | M8 §1.4 |
| ME-F27-L6 | Implementar `textDocument/completion` (M8 §1.4) | `nucleo/lsp.syn` | 3 | M8 §1.4 |
| ME-F27-L7 | Implementar `textDocument/definition` (M8 §1.4) | `nucleo/lsp.syn` | 3 | M8 §1.4 |
| ME-F27-L8 | Implementar `textDocument/codeAction` + `formatting` + `signatureHelp` | `nucleo/lsp.syn` | 6 | M8 §1.4 |
| ME-F27-L9 | Implementar `workspace/didChangeConfiguration` | `nucleo/lsp.syn` | 2 | M8 §1.4 |
| ME-F27-L10 | Integrar bucle de validación 3 intentos (M7 §6.3) | `nucleo/lsp.syn` | 4 | M7 §6.3 |

**Criterio de aceptación 27.2:** lsp.syn compila via S1 sin errores. 33 tests LSP pasan. 0 `asm()` en lsp.syn.

### Fase 27.3: CLI unificado (M8 §4)

| ME | Descripción | Archivos | Tests | Manual |
|----|-------------|----------|-------|--------|
| ME-F27-C1 | Subcomando `run` — compilar + ejecutar | `cli.py` | 3 | M8 §4.2 |
| ME-F27-C2 | Subcomando `debug` — modo time-travel | `cli.py` | 2 | M8 §5 |
| ME-F27-C3 | Subcomando `opensyn` — asistente IA | `cli.py` | 2 | M7 §6 |

**Criterio de aceptación 27.3:** `synapse run`, `synapse debug`, `synapse opensyn` funcionan. 7 tests CLI pasan.

### Fase 27.4: Extensión VS Code (M8 §2)

| ME | Descripción | Archivos | Tests | Manual |
|----|-------------|----------|-------|--------|
| ME-F27-V1 | Soporte `.syq` en package.json +语法 TextMate | `vscode-synapse/` | 2 | M8 §2.1 |
| ME-F27-V2 | Comandos: `aiStatus`, `aiTranspile`, `aiBindings` | `vscode-synapse/extension.js` | 3 | M8 §2.3 |
| ME-F27-V3 | Configuración `synapse.language`, `synapse.debugger.enabled` | `vscode-synapse/package.json` | 2 | M8 §2.4 |

**Criterio de aceptación 27.4:** Extensión VS Code carga sin errores. 7 tests extensión pasan.

### Fase 27.5: Debugger (M8 §5)

| ME | Descripción | Archivos | Tests | Manual |
|----|-------------|----------|-------|--------|
| ME-F27-D1 | `std/debug.syn` — API de instrumentación | `std/debug.syn` | 4 | M8 §5.2 |
| ME-F27-D2 | Grabación de ejecución + snapshots | `runtime/core/debug.c` | 3 | M8 §5.3 |
| ME-F27-D3 | Reversión + breakpoints reversibles | `runtime/core/debug.c` | 3 | M8 §5.4 |

**Criterio de aceptación 27.5:** 10 tests debugger pasan. Time-travel funciona en ejemplo básico.

### Fase 27.6: E2E + Cierre

| ME | Descripción | Archivos | Tests | Manual |
|----|-------------|----------|-------|--------|
| ME-F27-E1 | Tests E2E: LSP ↔ VS Code ↔ CLI ↔ Debugger | `tests/integration/` | 10 | M8 §9 |
| ME-F27-E2 | Cierre Fase 27 + R121 | `docs/reportes/R121.md` | — | — |

**Criterio de aceptación 27.6:** 10 tests E2E pasan. 0 brechas de alineación. Fase 27 COMPLETADA.

---

## RESUMEN DE MICRO-ENTREGABLES

| Subfase | MEs | Tests | Archivos principales |
|---------|-----|-------|---------------------|
| 27.1 Stdlib | 4 | 18 | `std/io.syn`, `std/texto.syn`, `runtime/core/texto.c` |
| 27.2 LSP | 10 | 33 | `nucleo/lsp.syn` |
| 27.3 CLI | 3 | 7 | `cli.py` |
| 27.4 VS Code | 3 | 7 | `vscode-synapse/` |
| 27.5 Debugger | 3 | 10 | `std/debug.syn`, `runtime/core/debug.c` |
| 27.6 E2E + Cierre | 2 | 10 | `tests/integration/` |
| **TOTAL** | **25** | **85** | — |

---

## REFERENCIA A MANUALES

| Manual | Secciones | Requisitos clave |
|--------|-----------|------------------|
| M2 §3 | Tokens y lexer | Builtins de string, tipos |
| M7 §6.3 | Bucle de validación | 3 intentos, LSP orquesta |
| M8 §1 | Arquitectura LSP | JSON-RPC 2.0, Synapse puro |
| M8 §1.4 | Métodos LSP | hover, completion, definition, codeAction, formatting, signatureHelp |
| M8 §2 | Extensión VS Code | Estructura, comandos, configuración |
| M8 §4 | CLI unificado | build, run, test, check, debug, opensyn |
| M8 §5 | Debugger | time-travel, breakpoints reversibles |
| M8 §9 | Pruebas | E2E, LSP, extensión |

---

## ORDEN DE EJECUCIÓN

```
27.1 (stdlib) → 27.2 (LSP) → 27.3 (CLI) → 27.4 (VS Code) → 27.5 (debugger) → 27.6 (E2E + cierre)
```

Cada ME sigue el ciclo:
1. Leer manual (registrar lectura)
2. Escribir tests (TDD)
3. Implementar
4. Verificar (pytest + verificar_alineacion.py)
5. Entregar reporte + commitear
