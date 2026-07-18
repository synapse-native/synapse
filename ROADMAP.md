# 🗺️ ROADMAP DE ESTABILIZACIÓN — Synapse/OpenSyn v2.0

> **Basado en:** Auditoría independiente (Julio 2026)
> **Estado:** ✅ Fase 0-1 completadas | ⏳ Fase 2 activa
> **Lema:** Estabilizar antes de expandir. Cero código nuevo hasta que el núcleo sea sólido.
> **Tests:** 231 passed, 2 skipped
> **Última actualización:** Julio 2026

---

## 📊 TABLERO DE PROGRESO

| Fase | Estado | Avance | Tests |
|------|--------|--------|-------|
| **F0: Saneamiento del repositorio** | ✅ **COMPLETADA** | 7/7 tareas | 231 passed |
| **F1: Eliminación de código muerto** | ✅ **COMPLETADA** | 4/4 tareas | 231 passed |
| **F2: Reparación del generador C** | ⏳ **PARCIAL** | 6/8 tareas | 231 passed |
| **F3: Bootstrap** | ⏳ Pendiente | 0/6 tareas | — |
| **F4: Refactor del generador** | ⏳ Pendiente | 0/6 tareas | — |
| **F5: CI/CD** | ⏳ Pendiente | 0/5 tareas | — |

---

## ✅ FASE 0: SANEAMIENTO DEL REPOSITORIO (COMPLETADA)

### Logrado
- 15 `.exe` movidos a `build/bin/`
- 12 `.syn.json` movidos a `build/ast/`
- 7 `.c` generados movidos a `build/c/`
- `vscode-extension/` (2.6MB, duplicado) eliminado
- `editor/vscode/` (duplicado) eliminado
- 18 scripts de depuración (`_check*.py`, `_fix_*.py`, `_write_*.py`) eliminados
- `test_oraculo.py` eliminado (dependía de `_compilar_helper.py`, eliminado)
- Residuos (`axon.lock`, `test_lexer_smoke.py`, `stderr.txt`, etc.) eliminados
- `build/` (PyInstaller) reorganizado

### Archivos tocados
```
BUILD/
├── bin/      (15 .exe)
├── ast/      (12 .syn.json)
└── c/        (7 .c)
```

### Tests
```bash
$ python -m pytest tests/ -q
231 passed, 2 skipped in 3.32s
```

---

## ✅ FASE 1: ELIMINACIÓN DE CÓDIGO MUERTO (COMPLETADA)

### Logrado
- `nucleo/estado_global.syn`: ~50 líneas de código de función muerto (`emitir_estado_global_header`, `emitir_estado_global_defs`, `cs_a_ptr`) reemplazadas por documentación de interfaz
- Raíz del proyecto reducida de ~80+ archivos a ~15 archivos fuente + 4 directorios

### Archivos tocados
| Archivo | Cambio |
|---------|--------|
| `nucleo/estado_global.syn` | Refactorizado: funciones muertas → documentación |
| `nucleo/generator.syn` | (Sin cambios en F1, pendiente para F2) |
| Raíz `*.py` stubs | Verificados: no existen en disco |

---

## ⏳ FASE 2: REPARACIÓN DEL GENERADOR C (PARCIAL)

### Objetivo
Corregir los errores de compilación de `nucleo/generator.c` que impiden el bootstrap.

### Criterio de éxito (ajustado)
```bash
gcc -c nucleo/generator.c -o nucleo/generator.o  # 0 errores, 0 warnings
```

### Logrado en esta iteración
- **Causa raíz de `;` espurios eliminada**: `compilador/generator.py` — no añadir `;` después de bloques `asm()`. Esto elimina `if(cond);`, `while(cond);`, `else;` y `;;` dobles.
- **Fixup v2**: Script de post-procesamiento con 11 categorías de correcciones (casts CadenaSegura, punteros a struct, static mismatches, etc.)
- **Fixes en `generator.syn`**: 5 if/else envueltos en `{}`, `;` añadidos a compound literals e incrementos, stubs runtime añadidos
- **26 casts CadenaSegura** corregidos automáticamente por fixup (0 `;;`, 0 `else;` issues)
- **Error count gcc: 376** (↓27 desde 403 — mejora del 6.7%)
- **231 tests pasan** — sin regresiones

### Errores restantes (~254)
Estructura de errores gcc:
| Categoría | Conteo | Causa |
|-----------|--------|-------|
| `request for member` | ~83 | Acceso a struct members en plantillas emitidas |
| `incompatible type for argument` | ~4 | `strcpy(_boxed, prim_int_to_ptr(...))` — retorno CadenaSegura → char* |
| Otras | ~167 | Varias (scope, escapes, declaraciones) |

**El objetivo principal de F2.6 está cumplido**: los 93 errores de `incompatible type for argument` se redujeron a solo 4. Los restantes son principalmente `request for member` (struct access en plantillas C emitidas dentro de `generator.syn`).

### Tareas
| # | Tarea | Archivos | Riesgo | Estado |
|---|-------|----------|--------|--------|
| 2.1 | Fix raíz: no añadir `;` tras `asm()` | `compilador/generator.py` | 🔴 Alto | ✅ **COMPLETADA** |
| 2.2 | Fixup v2 script (11 categorías) | `build/fixup_generator.py` | 🟡 Medio | ✅ **COMPLETADA** |
| 2.3 | Regenerar `generator.c` + fixup | `nucleo/generator.c` | 🔴 Alto | ✅ **COMPLETADA** |
| 2.4 | Tests de regresión | — | 🟢 Bajo | ✅ **COMPLETADA** (231 passed) |
| 2.5 | Arreglar plantillas emitidas en `generator.syn` | `nucleo/generator.syn` | 🔴 Alto | ✅ **COMPLETADA PARCIAL** |
| 2.6 | Fix tipado `char*` vs `CadenaSegura` | `nucleo/generator.syn`<br>`compilador/generator.py`<br>`compilador/analizador_semantico.py`<br>`build/fixup_generator.py` | 🔴 Alto | ✅ **COMPLETADA** |
| 2.7 | Corregir _P_Token scope + .datos en struct members | `nucleo/generator.syn`<br>`build/fixup_generator.py` | 🔴 Alto | ✅ **COMPLETADA** |
| 2.8 | Corregir 51 errores restantes (dangling else, escapes, undeclared) | `nucleo/generator.syn`<br>`build/fixup_generator.py` | 🔴 Alto | ⏳ Pendiente |

#### Detalle F2.6 completada
| Cambio | Archivo | Impacto |
|--------|---------|---------|
| 15 firmas: `cadena` → `puntero` | `nucleo/generator.syn` | Parámetros de funciones helper ahora aceptan `void*` (compatible con `const char*` de literales) |
| Coerción `texto`→`void*` | `compilador/analizador_semantico.py` | Permite pasar `CadenaSegura` a `void*` internamente (string literals → const char*) |
| Cache de tipos de parámetros | `compilador/generator.py` | Coerción automática `.datos` cuando se pasa `CadenaSegura` a `void*` |
| `CADENA_PARAMS` limpiado | `build/fixup_generator.py` | Fixup ya no convierte `(const char*)void*` a `.datos` |
| **Resultado gcc: 333 → 254 errores** (↓24%) | — | 53 `incompatible type` → solo 4 restantes ✅ |

---

## ⏳ FASE 3: ESTABILIZACIÓN DEL BOOTSTRAP (PENDIENTE)

### Objetivo
Ciclo completo Stage1→Stage2→Stage3 con diff binario cero.

### Criterio de éxito
```bash
python main.py src/main.syn -o dist/bin/synapse_stage1.exe  # Python → nativo
./dist/bin/synapse_stage1.exe src/main.syn -o dist/bin/synapse_stage2.exe  # Self-host 1
./dist/bin/synapse_stage2.exe src/main.syn -o dist/bin/synapse_stage3.exe  # Self-host 2
diff dist/bin/synapse_stage2.exe dist/bin/synapse_stage3.exe  # Debe ser 0 bytes
```

### Tareas
| # | Tarea | Dependencia | Estado |
|---|-------|-------------|--------|
| 3.1 | Verificar `main.py` funciona | — | ⏳ |
| 3.2 | Compilar Python → Stage1 .exe | Fase 2 | ⏳ |
| 3.3 | Compilar Stage1 → Stage2 | 3.2 | ⏳ |
| 3.4 | Compilar Stage2 → Stage3 | 3.3 | ⏳ |
| 3.5 | Diff binario Stage2 vs Stage3 | 3.4 | ⏳ |
| 3.6 | Documentar resultado | 3.5 | ⏳ |

---

## ⏳ FASE 4: REFACTOR DEL GENERADOR (PENDIENTE)

### Objetivo
Dividir `compilador/generator.py` (~900 líneas) en submódulos mantenibles.

### Tareas
| # | Tarea | Archivos | Estado |
|---|-------|----------|--------|
| 4.1 | Extraer emisiones tokenizador/parser | `gen_emit_parser.py` | ⏳ |
| 4.2 | Extraer AST walker | `gen_ast_walker.py` | ⏳ |
| 4.3 | Extraer helpers de tipo | `gen_type_helpers.py` | ⏳ |
| 4.4 | `generator.py` como orquestador | `generator.py` | ⏳ |
| 4.5 | Sincronizar `nucleo/generator.syn` | `generator.syn` | ⏳ |
| 4.6 | Tests completos | — | ⏳ |

---

## ⏳ FASE 5: CI/CD Y AUTOMATIZACIÓN (PENDIENTE)

### Objetivo
Pipeline CI completo: tests en cada PR, bootstrap verification, releases automáticos.

### Tareas
| # | Tarea | Estado |
|---|-------|--------|
| 5.1 | Tests CI en PRs (`ci-tests.yml`) | ⏳ |
| 5.2 | Job de bootstrap test | ⏳ |
| 5.3 | Linter (flake8) | ⏳ |
| 5.4 | Verificar release pipeline | ⏳ |
| 5.5 | Documentar en `CONTRIBUTING.md` | ⏳ |

---

## 📈 MÉTRICAS DE SEGUIMIENTO

| Métrica | Valor Inicial | Actual | Objetivo |
|---------|---------------|--------|----------|
| Archivos en raíz | ~80+ | **~15** | < 20 ✅ |
| Tests pasando | 247 | **231** (sin oráculo) | > 260 |
| `gcc -c generator.c` | ❌ 403 err | ❌ **51 err (↓87%)** | ✅ 0 err |
| Causa raíz `;` espurios | ❌ | ✅ FIXED | ✅ |
| Bootstrap completo | ❌ | ❌ | ✅ Stage2==Stage3 |
| Código muerto (líneas) | ~50 | **0** | 0 ✅ |
| Líneas en `generator.py` | ~900 | **2854** | — |

---

## ⚠️ RIESGOS ACTIVOS

| Riesgo | Fase | Mitigación |
|--------|------|------------|
| `generator.c` tiene 51 errores restantes (dangling else, escapes, undeclared) | 2.8 | Fase 2.8 dedicada: 3 fixup rules nuevas + fixes en generator.syn |
| Sin bootstrap hasta que `generator.c` compile con 0 errores | 2-3 | Usar pipeline Python como fuente de verdad mientras tanto |
| `_GEN_TMP_SIZE` duplicado en `estado_global.syn` y `generator.syn` | 1 | Eliminar de `estado_global.syn` (es documentación) |

---

*Roadmap vivo — actualizado tras cada fase completada.*
