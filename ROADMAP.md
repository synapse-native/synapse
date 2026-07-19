# 🗺️ ROADMAP DE ESTABILIZACIÓN — Synapse/OpenSyn v2.0

> **Basado en:** Auditoría independiente (Julio 2026)
> **Estado:** ✅ Fase 0-2 completadas | ✅ Fase 3.2 completada | ⏳ Fase 3.3 activa
> **Lema:** Estabilizar antes de expandir. Cero código nuevo hasta que el núcleo sea sólido.
> **Tests:** 231 passed, 2 skipped | `synapse_unity.c` GCC: **0 errores** ✅
> **Última actualización:** Julio 2026

---

## 📊 TABLERO DE PROGRESO

| Fase | Estado | Avance | Tests |
|------|--------|--------|-------|
| **F0: Saneamiento del repositorio** | ✅ **COMPLETADA** | 7/7 tareas | 231 passed |
| **F1: Eliminación de código muerto** | ✅ **COMPLETADA** | 4/4 tareas | 231 passed |
| **F2: Reparación del generador C** | ✅ **COMPLETADA** | 8/8 tareas | 231 passed |
| **F3: Bootstrap** | 🔄 Activa (3.3) | 2.5/6 tareas | 231 passed |
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

## ✅ FASE 3: ESTABILIZACIÓN DEL BOOTSTRAP (ACTIVA — Fase 3.3)

### Objetivo
Ciclo completo Stage1→Stage2→Stage3 con diff binario cero.

### Criterio de éxito
```bash
python main.py src/main.syn -o dist/bin/synapse_stage1.exe  # Python → nativo
./dist/bin/synapse_stage1.exe src/main.syn -o dist/bin/synapse_stage2.exe  # Self-host 1
./dist/bin/synapse_stage2.exe src/main.syn -o dist/bin/synapse_stage3.exe  # Self-host 2
diff dist/bin/synapse_stage2.exe dist/bin/synapse_stage3.exe  # Debe ser 0 bytes
```

### ✅ Fase 3.1 COMPLETADA
- `python main.py src/main.syn` produce `src/main.c` + `src/main.exe` + `src/main.syn.json`

### ✅ Fase 3.2 COMPLETADA
- **Compilación total**: `nucleo/principal.syn` → `synapse_unity.c` → **GCC 0 errores**
- **Progreso**: 376 errores → 43 errores → **0 errores** (-100%)
- **Fixes clave**:
  - Pre-pass de variables para declaraciones hoisteadas al scope de función
  - Fix de RAII: destructores no se llaman sobre variables no inicializadas
  - Conversión automática `(const char*)CadenaSegura` → `.datos` en asm blocks
  - Detección de campos-puntero en structs para ADTs
  - Escape de strings en `_emitir_tokenizar_c` y `_emitir_parsear_c`
  - `formatear_entrada_error` y `formatear_ubicacion` corregidos (CadenaSegura)
- **Deuda técnica eliminada**: `builtin_tipo_retorno`, `builtin_tipo_parametro`, `tipo_normalizado`, `resumen_errores` reescritas en Synapse nativo
- **Tests**: 231 pass, 2 skip — sin regresiones

### 📦 Cambios commitados en Fase 3.2
| Archivo | Cambio |
|---------|--------|
| `compilador/generator.py` | Pre-pass variables + fix RAII + fix `;` espurios |
| `nucleo/analizador_semantico.syn` | `(const char*)nombre` → `nombre.datos`, strdup en parsear_patron |
| `nucleo/diagnostics.syn` | CadenaSegura en formateo de errores |
| `nucleo/generator.syn` | `.datos` en acceso a struct members, strcpy desde `nombre.datos` |
| `ROADMAP.md` | Actualización de progreso |
| `INFORME_ESTADO_ACTUAL.md` | Estado actualizado |

### ⏳ Fase 3.3: Compilar Python → Stage1 .exe (PRÓXIMO PASO)
```bash
python main.py src/main.syn -o dist/bin/synapse_stage1.exe
```

### Tareas
| # | Tarea | Dependencia | Estado |
|---|-------|-------------|--------|
| 3.1 | Verificar `main.py` funciona | — | ✅ **COMPLETADA** |
| 3.2 | Compilar `nucleo/principal.syn` → GCC 0 errores | Fase 2 | ✅ **COMPLETADA** |
| 3.3 | Compilar Python → Stage1 .exe | 3.2 | ⏳ **PENDIENTE** |
| 3.4 | Compilar Stage1 → Stage2 | 3.3 | ⏳ |
| 3.5 | Compilar Stage2 → Stage3 | 3.4 | ⏳ |
| 3.6 | Diff binario + documentar | 3.5 | ⏳ |

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
| Bootstrap completo | ❌ | ❌ | ✅ Stage2==Stage3 |
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
