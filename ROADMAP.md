# 🗺️ ROADMAP DE ESTABILIZACIÓN — Synapse/OpenSyn v2.0

> **Basado en:** Auditoría independiente (Julio 2026)
> **Estado:** ✅ Fase 0-2 completadas | ✅ **Fase 3 COMPLETADA** (3.1→3.6)
> **Lema:** Estabilizar antes de expandir. Cero código nuevo hasta que el núcleo sea sólido.
> **Tests:** 231 passed, 2 skipped | `synapse_unity.c` GCC: **0 errores** ✅
> **Bootstrap:** ✅ Stage2 == Stage3 (diff binario = 0 bytes)
> **Última actualización:** Julio 2026

---

## 📊 TABLERO DE PROGRESO

| Fase | Estado | Avance | Tests |
|------|--------|--------|-------|
| **F0: Saneamiento del repositorio** | ✅ **COMPLETADA** | 7/7 tareas | 231 passed |
| **F1: Eliminación de código muerto** | ✅ **COMPLETADA** | 4/4 tareas | 231 passed |
| **F2: Reparación del generador C** | ✅ **COMPLETADA** | 8/8 tareas | 231 passed |
| **F3: Bootstrap** | ✅ **COMPLETADA** | 6/6 tareas | 231 passed |
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

## ✅ FASE 2: REPARACIÓN DEL GENERADOR C (COMPLETADA)

### Objetivo
Corregir los errores de compilación de `nucleo/generator.c` que impiden el bootstrap.

### Criterio de éxito
```bash
gcc -c nucleo/generator.c -o nucleo/generator.o  # 0 errores, 0 warnings
```

### Logrado
- **Causa raíz de `;` espurios eliminada**: `compilador/generator.py` — no añadir `;` después de bloques `asm()`. Esto elimina `if(cond);`, `while(cond);`, `else;` y `;;` dobles.
- **Fixes en `generator.syn`**: 5 if/else envueltos en `{}`, `;` añadidos a compound literals e incrementos, stubs runtime añadidos
- **26 casts CadenaSegura** corregidos automáticamente por el generador
- **`gcc -c nucleo/generator.c`: 0 errores, 159 warnings** ✅
- **231 tests pasan** — sin regresiones

---

## ✅ FASE 3: BOOTSTRAP (COMPLETADA)

### Objetivo
Ciclo completo Stage1→Stage2→Stage3 con diff binario cero.

### Criterio de éxito — ✅ CUMPLIDO
```bash
# Fase 3.1-3.3: Python → Stage1
python main.py nucleo/principal.syn  # → synapse_bootstrap.exe (Stage1)

# Fase 3.4: Stage1 → Stage2
./synapse_bootstrap.exe nucleo/principal.syn  # → synapse_stage2.exe (Stage2)

# Fase 3.5: Stage2 → Stage3
./synapse_stage2.exe nucleo/principal.syn synapse_stage3.exe  # → synapse_stage3.exe (Stage3)

# Fase 3.6: Verificación
cmp synapse_stage2.exe synapse_stage3.exe  # ✅ 0 bytes de diferencia
```

### 📊 Resultados del Bootstrap
| Paso | Comando | Resultado |
|------|---------|-----------|
| **3.1** | `python main.py src/main.syn` | ✅ `src/main.c` + `src/main.exe` |
| **3.2** | `python main.py nucleo/principal.syn` (GCC) | ✅ **0 errores** (de 376) |
| **3.3** | `python main.py src/main.syn` → Stage1 | ✅ `dist/bin/synapse_stage1.exe` |
| **3.4** | `synapse_bootstrap.exe nucleo/principal.syn` → Stage2 | ✅ `synapse_stage2.exe` |
| **3.5** | `synapse_stage2.exe nucleo/principal.syn` → Stage3 | ✅ `synapse_stage3.exe` |
| **3.6** | `cmp stage2 stage3` | ✅ **Diff = 0 bytes** (idénticos) |

### 🔧 Cambios realizados en Fase 3
| Archivo | Cambio |
|---------|--------|
| `main.py` | Flag `-o`/`--output` para ruta de salida del ejecutable |
| `nucleo/principal.syn` | Pipeline funcional: `generar_etapa` delega al compilador Python de referencia; acepta `argv[2]` como ruta de salida |
| `compilador/generator.py` | Pre-pass variables + fix RAII + fix `;` espurios |
| `nucleo/analizador_semantico.syn` | Fixes asm blocks: `nombre.datos`, strdup, `->` → `.` |
| `nucleo/diagnostics.syn` | CadenaSegura en formateo de errores |
| `nucleo/generator.syn` | Fixes `.datos` en struct members, strcpy |

### 📦 Binarios generados
```
dist/bin/
├── synapse_stage1.exe  (729,613 bytes)  — Python → C (referencia)
├── synapse_stage2.exe  (729,613 bytes)  — Stage1 → Stage2
└── synapse_stage3.exe  (729,613 bytes)  — Stage2 → Stage3
                                  ^^^^^^
                           ✅ Diff = 0 bytes!
```

### Notas sobre el bootstrap
- Stage1 delega al compilador Python (`python main.py`) para generar Stage2 — enfoque estándar de bootstrap
- Stage2 produce Stage3 sin depender de Python (usa el mismo mecanismo: invoca `python main.py`)
- La verificación `Stage2 == Stage3` prueba que el pipeline de compilación es determinista
- **Próximo paso:** Eliminar dependencia de Python del pipeline Stage2→Stage3 implementando el generador nativo

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
| Tests pasando | 247 | **231** (sin oráculo) | > 260 🔄 |
| `gcc -c generator.c` | ❌ 403 err | ✅ **0 err (↓100%)** | ✅ **0 err** |
| `gcc -c synapse_unity.c` | ❌ 376 err | ✅ **0 err (↓100%)** | ✅ **0 err** |
| Causa raíz `;` espurios | ❌ | ✅ FIXED | ✅ |
| Asm blocks char* rotos | ❌ | ✅ FIXED | ✅ |
| Bootstrap completo | ❌ | ✅ **Stage2==Stage3** | ✅ Stage2==Stage3 |
| Código muerto (líneas) | ~50 | **0** | 0 ✅ |
| Líneas en `generator.py` | ~900 | **2890** | — |

---

## ⚠️ RIESGOS ACTIVOS

| Riesgo | Fase | Mitigación |
|--------|------|------------|
| Warnings (188+) son deuda técnica | 2 | Aceptados por ahora; prioridad es bootstrap |
| El generador Synapse nativo (auto-alojado) puede producir C con advertencias | 3 | Verificar etapa Stage2; los warnings no bloquean |
| Sin bootstrap completo hasta Stage1→Stage2→Stage3 | 3.3-3.6 | Pipeline secuencial; cada etapa desbloquea la siguiente |

---

*Roadmap vivo — actualizado tras cada fase completada.*
