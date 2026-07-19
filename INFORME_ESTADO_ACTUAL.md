# INFORME DE ESTADO ACTUAL — Synapse/OpenSyn v2.0

## 1. INFORMACIÓN GENERAL

| Componente | Valor |
|------------|-------|
| Proyecto | Synapse/OpenSyn v2.0 |
| Última actualización | Julio 2026 |
| Última verificación | Pipeline: 0 GCC errors ✅ | 231 tests ✅ |
| Bootstrap Stage2 (nuevo binario) | **❌ Segfault en parser self-hosting (F9.4 blocker)** |
| Bootstrap Stage2 (binario Jul 10) | ✅ Stage2==Stage3 verificado (binarios legacy) |
| Fase actual | **F9.4 activa** — Debugging segfault en gen_parse() |
| Tests | **231 passed, 0 failed, 2 skipped** |
| GCC errors (nucleo/principal.syn) | **0 errores** ✅ |

## 2. ARQUITECTURA MODULAR

```
/
├── compilador/
│   ├── ast_nodes.py            # Definiciones de nodos del AST
│   ├── lexer.py                # Analizador léxico
│   ├── parser.py               # Analizador sintáctico
│   ├── analizador_semantico.py # Análisis semántico
│   ├── generator/              # Generador de código C (7 submódulos)
│   │   ├── __init__.py         # Orquestador (GeneradorC, visitar)
│   │   ├── context.py          # GeneratorContext (estado centralizado)
│   │   ├── emit_control.py     # if, while, for, match
│   │   ├── emit_expressions.py # expr_a_c, tipo_de_expr, builtins
│   │   ├── emit_declarations.py# funciones, structs, variables
│   │   ├── emit_contracts.py   # requiere/garantiza → asserts
│   │   └── emit_selfhost.py    # EMISORES AUTO-HOSPEDAJE (parser, tokenizer, generator)
│   ├── symbol_table.py         # Tabla de símbolos
│   ├── diagnostics.py          # Sistema de errores/diagnósticos
│   └── resolvedor_axon.py      # Resolución de módulos Axon
├── nucleo/
│   ├── principal.syn           # Punto de entrada nativo (pipeline sin Python)
│   ├── generator.syn           # Generador C auto-hospedado
│   ├── analizador_semantico.syn# Analizador semántico nativo
│   ├── diagnostics.syn         # Diagnostics nativos
│   └── (otros .syn)            # Módulos del núcleo nativo
├── synapse_lsp/                # Servidor LSP (Python)
├── tests/
│   ├── unit/                   # Tests unitarios
│   ├── integration/            # Tests de integración
│   ├── fixtures/               # Fixtures de prueba
│   └── e2e/                    # Tests end-to-end
├── main.py                     # Punto de entrada CLI (Python)
├── synapse_bootstrap.exe       # Generado por pipeline (727,978 bytes) ❌ segfault
├── synapse_stage2.exe          # Stage2 legacy (729,613 bytes) ✅ funcional
├── synapse_stage3.exe          # Stage3 legacy (729,613 bytes) ✅ funcional
├── ROADMAP.md                  # Plan de estabilización (actualizado)
├── docs/                       # Documentación mdBook
├── .github/workflows/          # CI/CD (ci-tests, release, deploy-docs)
└── vscode-synapse/             # Extensión VS Code
```

## 3. ESTADO DEL PIPELINE (VERIFICADO EN VIVO)

### Pipeline Python (referencia) — ✅ 0 GCC errors
```bash
$ python main.py nucleo/principal.syn
[OK] C generado: synapse_unity.c
[OK] GCC: gcc -O2 ... -o "synapse_bootstrap.exe"
[OK] Ejecutable generado: synapse_bootstrap.exe
[OK] AST canonico guardado: nucleo/principal.syn.json
```

### Pipeline Nativa (sin Python) — ❌ Segfault en Stage2
```bash
$ ./synapse_bootstrap.exe
Uso: synapse_bootstrap.exe <archivo.syn> [salida.exe]    # ✅ Usage funciona

$ ./synapse_bootstrap.exe nucleo/principal.syn synapse_test_stage2.exe
# ❌ Segmentation fault (exit code 139)
# Causa: gen_parse() en emit_selfhost.py → parser self-hosting crash
```

### Bootstrap Binarios Legacy (Jul 10) — ✅ Funcionales
```bash
$ ./synapse_stage2.exe nucleo/principal.syn synapse_stage3.exe
# ✅ Compila correctamente
$ cmp synapse_stage2.exe synapse_stage3.exe
# ✅ 0 bytes de diferencia (builds reproducibles)
```

## 4. FASES COMPLETADAS Y EN CURSO

| Fase | Nombre | Estado | Detalle |
|------|--------|--------|---------|
| F0 | Saneamiento del repositorio | ✅ | 15 .exe movidos, 12 .syn.json archivados |
| F1 | Eliminación de código muerto | ✅ | ~50 líneas de función muerta eliminadas |
| F2 | Reparación del generador C | ✅ | 403→0 errores GCC |
| F3 | Bootstrap | ✅ (parcial) | Stage2==Stage3 con binarios legacy (Jul 10) |
| F4 | Refactor del generador | ✅ | generator.py → 7 submódulos |
| F4.5 | Post-processing asm() | ✅ | 280 errores GCC corregidos |
| F5 | CI/CD | ✅ | 4 workflows GitHub Actions |
| F6 | Eliminar TEMP + .syn fixes | ✅ | 6/6 pasos completados |
| F7 | Generador nativo (sin Python) | ✅ | Pipeline nativa creada |
| **F8** | Análisis semántico nativo | ⏳ **BLOQUEADA** | Esperando F9 estable |
| **F9** | Eliminar post-processing + fix emisores | ✅ **3/8 tareas** | 9.1, 9.2, 9.3 ✅; **9.4 🔴 ACTIVO** |
| F10 | Concurrencia (canales) | ⏳ Planificada | Esperando F8 |
| F11 | Fuzzing destructivo | ⏳ Planificada | Documento Maestro Parte VII |
| F12 | LSP nativo | ⏳ Planificada | Documento Maestro Parte VI |

### Progreso Fase 9 (detalle)
| # | Tarea | Estado |
|---|-------|--------|
| 9.1 | Fix gen_tok_c(): escape `\"` en strings | ✅ |
| 9.2 | Refactor principal.syn: coincidir → si/sino | ✅ |
| 9.3 | Eliminar debug fprintf de emitir_tokenizar() | ✅ |
| **9.4** | **Arreglar segfault en parser self-hosting (gen_parse())** | **🔴 ACTIVO (blocker)** |
| 9.5 | Agregar guardas #ifdef SYN_DEBUG | ⏳ |
| 9.6 | Arreglar emisiones (CadenaSegura) → eliminar post-proc paso 4 | ⏳ |
| 9.7 | Eliminar post-processing paso 4 de __init__.py | ⏳ |
| 9.8 | Verificar bootstrap Stage1→Stage2→Stage3 + cmp | ⏳ |

## 5. MÉTRICAS DE SEGUIMIENTO

| Métrica | Inicio | Actual | Objetivo |
|---------|--------|--------|----------|
| Tests pasando | 247 | **231** (sin oráculo) | > 260 🔄 |
| GCC errors (generator.c) | 403 | **0** ✅ | 0 ✅ |
| GCC errors (synapse_unity.c) | 376 | **0** ✅ | 0 ✅ |
| GCC errors (principal.syn completo) | 815 | **0** ✅ | 0 ✅ |
| Bootstrap Stage2==Stage3 (viejo) | ❌ | **✅ 0 bytes** | ✅ |
| Bootstrap Stage2 (nuevo) | ❌ | **❌ Segfault** | ✅ 0 errors |
| Archivos en raíz | ~80+ | **~15** | < 20 ✅ |
| Módulos generator/ | 0 | **7** | ✅ Modular |
| Dependencia Python en bootstrap | Sí | **No** | No ✅ |

## 6. DEUDA TÉCNICA

### Resuelta en sesiones recientes (Jul 2026)
| Ítem | Sesión | Solución |
|------|--------|----------|
| Debug fprintf en tokenizer (5 prints) | Jul 19 | Eliminados de emitir_tokenizar() |
| Debug fprintf en parser (1 print) | Jul 19 | Eliminado de gen_parse() |
| Escape `\n` roto en gen_parse() | Jul 19 | Corregido: `\n` → `\\n` |
| Código muerto en principal.syn | Jul 18 | tokenizar_etapa, parsear_etapa, analizar_etapa eliminadas |
| Stub old_generator.py (63B) | Jul 18 | Eliminado |
| Exclusión .flake8 huérfana | Jul 18 | Removida |
| principal.syn desactualizado | Jul 18 | Reescrito: pipeline nativa completa |

### Deuda técnica remanente
| Ítem | Impacto | Prioridad |
|------|---------|-----------|
| **Segfault en parser self-hosting (gen_parse())** | 🔴 **Bloquea bootstrap Stage2** | **🔴 P1** |
| Post-processing paso 4 en __init__.py | 🟢 No bloquea, deuda menor | 🟢 Baja |
| `emitir_token_defs` duplicado (2 archivos) | 🟢 Código muerto potencial | 🟢 Baja |
| Ruta `synapse_rt.o` hardcodeada (CWD-relative) | 🟡 Falla si CWD es otro directorio | 🟢 Baja |
| STRING_UNCLOSED silent break | 🟡 Diagnóstico perdido | 🟡 Media |
| Faltan guardas `#ifdef SYN_DEBUG` | 🟡 Debug requiere modificar fuente | 🟡 Media |

## 7. PRÓXIMA FASE SEGÚN DOCUMENTO MAESTRO

| Prioridad | Fase | Descripción | Justificación (DM) |
|-----------|------|-------------|---------------------|
| 🔴 **P1** | **F9.4** | Fix segfault en parser self-hosting | Parte VIII: Fallo estructural → congelar features |
| 🟡 P2 | F9.5 | Guardas #ifdef SYN_DEBUG | Parte VIII: Aislamiento de defecto |
| 🟡 P3 | F9.6-9.8 | Completar F9 + bootstrap Stage2 | Parte VIII: Pipeline estable primero |
| 🟢 P4 | F8 | Análisis semántico nativo | Solo después de F9 estable |
| 🟢 P5 | F10-F12 | Concurrencia, Fuzzing, LSP | Solo después de F8 estable |

---

> *Documento actualizado en vivo — Julio 2026. Pipeline Python: 0 GCC | 231 tests. Bootstrap: blocker F9.4.*
