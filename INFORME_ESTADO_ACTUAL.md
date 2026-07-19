# INFORME DE ESTADO ACTUAL — Synapse/OpenSyn

## 1. VERSIONES DETECTADAS

| Componente | Versión | Fuente |
|------------|---------|--------|
| Synapse (OpenSyn) | v1.1.0 | README.md |
| Synapse (Axon TOML) | v2.1.0 | axon.toml |
| Python | 3.12.10 | .venv |
| pytest | 9.1.1 | .venv |
| VS Code Extension (nueva) | v0.1.0 | vscode-synapse/package.json |
| VS Code Extension (antigua) | v1.0.0 | vscode-extension/package.json |
| Dist Synapse ZIP | v1.5.0 | dist/synapse-v1.5.0-windows-x64.zip |

## 2. ÁRBOL DE DIRECTORIOS (RESUMEN)

```
/
├── compilador/           # Núcleo modular (lexer, parser, ast_nodes, analizador_semantico, generator, symbol_table, diagnostics)
├── synapse_lsp/          # Servidor LSP (server.py, test_lsp.py, test_lsp2.py, _check_analizador.py)
├── tests/
│   ├── unit/             # Tests unitarios (test_lexer, test_parser, test_lsp)
│   ├── integration/      # Tests de integración (test_end_to_end, test_examples)
│   ├── fixtures/         # Fixtures de prueba (valid/, invalid/)
│   ├── auditoria/        # Test de auditoría en Synapse nativo
│   ├── axon_modules/     # Tests de módulos Axon
│   └── e2e/              # Tests end-to-end
├── vscode-synapse/       # Extensión VS Code (nueva, scaffolding)
├── vscode-extension/     # Extensión VS Code (antigua, completa con node_modules)
├── examples/             # Ejemplos (00_hola_mundo, 01_calculadora, 02_estructuras)
├── librerias/            # Librerías estándar (compiler/, std/)
├── dist/                 # Distribución empaquetada
├── docs/                 # Documentación mdBook
├── build/                # Build de PyInstaller (axon)
├── axon_src/             # Fuente del build Axon
├── axon_modules/         # Módulos Axon
├── opensyn/              # Orquestador OpenSyn (principal.syn + binario)
├── nucleo/               # Núcleo Synapse nativo
├── src/                  # Código fuente Synapse nativo (bootstrap)
├── paquetes_oficiales/   # Paquetes oficiales (std.*)
├── editor/               # Editor (vscode/)
├── .github/workflows/    # CI/CD (ci-tests.yml, deploy-docs.yml, release-binaries.yml)
├── main.py               # Punto de entrada CLI
├── ROADMAP.md            # Plan de mejora unificado (fuente de verdad)
├── *.py, *.md, *.syn     # Archivos en raíz (algunos stubs, algunos obsoletos)
```

## 3. ARCHIVOS SOSPECHOSOS / CANDIDATOS A ELIMINACIÓN

### 3.1. Stubs del monolito original (reemplazados por compilador/ modular)

| Archivo | Tamaño | Motivo |
|---------|--------|--------|
| `analizador_semantico.py` | 46 B | Sombra del módulo real en compilador/ |
| `ast_nodes.py` | 35 B | Sombra del módulo real en compilador/ |
| `diagnostics.py` | 37 B | Sombra del módulo real en compilador/ |
| `generator.py` | 35 B | Sombra del módulo real en compilador/ |
| `lexer.py` | 31 B | Sombra del módulo real en compilador/ |
| `parser.py` | 32 B | Sombra del módulo real en compilador/ |
| `symbol_table.py` | 38 B | Sombra del módulo real en compilador/ |
| `resolvedor_axon.py` | 1.3 KB | Dependencia del monolito original |

### 3.2. Archivos de documentación obsoletos o duplicados

| Archivo | Motivo |
|---------|--------|
| `EVALUACION_Y_PLAN.md` | Contenido anterior a la modularización; ROADMAP.md es la fuente de verdad |
| `PLAN_RELEASE_VERSIONADO.md` | Plan de versionado obsoleto |
| `ROADMAP_MADUREZ.md` | Roadmap anterior, reemplazado por ROADMAP.md |
| `--help.c` | Generado accidentalmente por CLI |
| `ast_nativo.txt` / `ast_python.txt` / `ast_python_tree.txt` | Volcados de AST de depuración |
| `ast_tree_diff.py` | Script de depuración de AST |

### 3.3. Artefactos de compilación (generados por el compilador)

| Categoría | Ejemplos |
|-----------|----------|
| `*.exe` en raíz | axon_build.exe, bootstrap_test.exe, generado.exe, hola.exe, programa.exe, salida_metal.exe, synapse.exe, synapse-windows-amd64.exe, synopsis_test.exe, test_*.exe |
| `*.c` en raíz | --help.c, axon_build.c, bootstrap_test.c, hola.c, main.c, main2.c, programa.c, test_*.c |
| `*.syn.json` en raíz | main.syn.json, generado.syn.json, test_*.syn.json |
| `.o` en raíz | synapse_rt.o |
| Tests/*.exe y *.c | Múltiples binarios y código C generado en tests/ |
| Tests/*.syn.json | Múltiples JSON de AST canónico |

### 3.4. Archivos de tests obsoletos o huérfanos

| Archivo | Motivo |
|---------|--------|
| `tests/fail_use_after_move.*` | Pruebas del sistema de ownership anterior |
| `tests/pass_safe_transfer.*` | Pruebas del sistema de ownership anterior |
| `tests/e2e_errores.*` | Test E2E sin suite automatizada |
| `tests/smoke_*.c/.exe/.syn.json` | Smokes generados individuales |
| `tests/demo_inferencia.*` | Demo de inferencia (no es test) |
| `tests/auditoria/` | Test de auditoría aislado |
| `tests/test_runner.py` | Runner antiguo, reemplazado por pytest |
| `tests/bootstraps_test.syn` | Test de bootstrap huérfano |
| `tests/stress_pool.syn` | Test de stress huérfano |

### 3.5. Directorios duplicados

| Directorio | Motivo |
|------------|--------|
| `vscode-extension/` (2.6 MB con node_modules) | Versión anterior; reemplazado por `vscode-synapse/` |
| `editor/vscode/` | Otra versión de extensión VS Code (TypeScript) |
| `librerias/` vs `dist/lib/librerias/` | Contenido similar, posible duplicación |

### 3.6. Otros residuos

| Archivo | Motivo |
|---------|--------|
| `axon.lock` | Archivo de lock de Axon (0 B) |
| `stderr.txt` / `stdout.txt` | Capturas de salida de depuración |
| `test_fs_output.txt` | Salida de test de filesystem |
| `patch.py` | Script de parcheo temporal |
| `fix_main_proper.py` | Script de corrección única |
| `_compilar_helper.py` | Helper de compilación |
| `_test_combinado_temp.exe` | Binario temporal |
| `verificar_ast.py` | Script de verificación |
| `qa_inquisidor.py` | Herramienta de QA |
| `generate_embedded_libs.py` | Script de generación |
| `build_dist.py` | Script de build |
| `dump_ast_manual.py` | Script de depuración |
| `test_lexer_smoke.py` | Smoke test manual |
| `smoke_test_coincidir.py` | Smoke test manual |
| `build/` (7.5 MB) | Artefactos de PyInstaller (axon) |
| `dist/synapse2.exe` | Binario duplicado en dist/ |
| `Synapse-v1.3.0-Windows.zip` / `synapse-v1.4.0-windows-x64.zip` | Zips de release antiguos |
| `COMENTARIOS.md` (si existe) | Residuos de sesiones anteriores |

## 4. ESTADO DEL BOOTSTRAP (Fase 3)

### ✅ Fase 3.1 COMPLETADA
- `python main.py src/main.syn` produce `src/main.c` + `src/main.exe` (stage 1 bootstrap)

### ✅ Fase 3.2 COMPLETADA
- Compilación de `nucleo/principal.syn` → `synapse_unity.c` → **GCC 0 errores**
- Progreso: 376 → ~43 → **0 errores** (-100%)
- Fixes: pre-pass de variables, RAII protegido, `.datos` en asm, escapes de strings
- **Tests:** 231 passed, 2 skipped (sin regresiones)

### ⏳ Fase 3.3 PENDIENTE
- `python main.py src/main.syn -o dist/bin/synapse_stage1.exe`

- **Binarios funcionales:** `build/bin/synapse.exe` (nativo), `src/main.exe` (bootstrap parcial)
- **Deuda técnica:** `builtin_tipo_retorno`, `builtin_tipo_parametro`, `tipo_normalizado`, `resumen_errores` reescritas en Synapse nativo

## 5. RESUMEN

- **Tests activos:** 231 pasando, 2 skipping
- **Cobertura funcional:** Léxico, sintáctico, semántico, generación C, LSP (completion, hover, definition), CLI
- **Estado bootstrap:** Fase 3.2 COMPLETADA ✅ — GCC 0 errores en synapse_unity.c
- **Próximo paso:** Fase 3.3 — Compilar Python → Stage1 .exe
