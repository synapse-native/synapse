# PLAN DE MEJORA — BATERÍA DE TESTS (CALIDAD INDUSTRIAL)

**Fecha de emisión:** 2026-08-25  
**Alcance:** Todos los tests del repositorio  
**Referencia:** Informe de Auditoría de Calidad (2026-08-25)  
**Objetivo:** Cumplimiento estricto M1-M9 + calidad industrial  
**Modalidad:** Solo plan — ejecución pendiente de aprobación

---

## 1. ESTADO ACTUAL VERIFICADO (segunda lectura)

### 1.1 Inventario corregido

| Categoría | Python (.py) | C (.c) | Total funciones |
|---|---|---|---|
| unit/ | 28 | 0 | ~350 |
| integration/ | 96 | 5 | ~700 |
| fuzz/ | 5 | 59 (57 tmp) | ~80 |
| security/ | 3 | 0 | ~40 |
| stress/ | 2 | 2 | ~30 |
| syquex/ | 11 | 0 | ~80 |
| opensyn/ | 8 | 0 | ~60 |
| root tests/ | 29 | 106 | ~450 |
| **TOTAL** | **172** | **172** | **~1,658** |

### 1.2 Hallazgos verificados (segunda lectura)

| # | Hallazgo | Verificado | Gravedad |
|---|---|---|---|
| V-1 | 2 tests vacíos (`pass`) | ✅ Confirmado | CRÍTICO |
| V-2 | 59 archivos tmp en fuzz/ | ✅ Confirmado | CRÍTICO |
| V-3 | 33 tests sin asserts explícitos | ✅ Confirmado | ALTO |
| V-4 | 0.5% parametrización (8/1658) | ✅ Confirmado | ALTO |
| V-5 | 12+ tests obligatorios con rutas incorrectas o faltantes | ✅ Confirmado | ALTO |
| V-6 | M8 solo 2/12 tests presentes | ✅ Confirmado | ALTO |
| V-7 | Sin pytest.ini / configuración central | ✅ Confirmado | MEDIO |
| V-8 | Sin conftest.py por subdirectorio | ✅ Confirmado | MEDIO |
| V-9 | 8+ archivos con 100% skip rate | ✅ Confirmado | MEDIO |
| V-10 | Código duplicado _find_gcc() en 8+ archivos | ✅ Confirmado | MEDIO |

---

## 2. DISTRIBUCIÓN POR DIRECTORIO (Manual 1 §2)

| Directorio | Función | Archivos actuales | Archivos planeados |
|---|---|---|---|
| tests/ (root) | Solo conftest.py + infraestructura + validate_*.c | 5 py + 23 validate + 11 smoke | — |
| tests/unit/ | Tests unitarios (M1, M2) | 23 | +1 (test_ast_serialization) |
| tests/integration/ | Tests integración (M2-M8) | 121 | +12 (M6: 3, M8: 9) |
| tests/syquex/ | Tests Syquex (M3, M4) | 16 | +2 (test_ffi, test_export) |
| tests/opensyn/ | Tests OpenSyn (M7) | 8 | — |
| tests/fuzz/ | Fuzzing destructivo (M1 §7.2) | 6 py | — |
| tests/stress/ | Pruebas de estrés | 2 py + 2 c | — |
| tests/security/ | Seguridad | 3 | — |
| tests/micro_bootstrap/ | Tests bootstrap (M1 §2) | 12 fixtures .syn | — |

**Nota:** Los archivos planeados se crearán en los ME-TQ-2 a ME-TQ-5. Los conftest.py por subdirectorio NO se crearán (decisión ME-TQ-1: el conftest raíz hereda jerárquicamente en pytest).

---

## 3. CATÁLOGO DE MICRO-ENTREGABLES

### ME-TQ-1: Limpieza y reorganización de estructura ✅ COMPLETADO

**Manual:** M1 §2 (estructura de directorios), M1 §7.2 (suite completa)  
**Fecha de ejecución:** 2026-08-25  
**Archivos afectados:** 32 movimientos + 67 eliminaciones + 4 creaciones

| Acción | Detalle | Criterio | Estado |
|---|---|---|---|
| Eliminar tmp*.c de fuzz/ | 63 archivos temporarios (.c + .syn) | `find tests/fuzz/ -name "tmp*" \| wc -l` = 0 | ✅ |
| Mover test_*.py de root a integration/ | 22 archivos Python | root tests/ solo infraestructura | ✅ |
| Mover test_syquex_*.py de unit/ a syquex/ | 5 archivos | Rutas coinciden con M3 §9 | ✅ |
| Mover test_cli.py de unit/ a integration/ | 1 archivo | Ruta coincide con M8 §9 | ✅ |
| Mover native_*_paridad.py a integration/ | 3 archivos | Parity tests en integración | ✅ |
| Crear tests/micro_bootstrap/ | Directorio + 12 fixtures .syn | M1 §2 lo requiere | ✅ |
| ~~Crear conftest.py por subdirectorios~~ | ~~5 archivos~~ | Decisión: NO crear (sombreado) | ✅ Descartado |
| Crear pytest.ini | 1 archivo | Config central: markers, testpaths | ✅ |
| Fix paths en archivos movidos | 13 archivos (dirname+1 nivel) | Paths relativos correctos | ✅ |

**Resultado:** 
- Root tests/: 29 → 5 archivos (solo conftest.py + infraestructura)
- 76 collection errors (preexistentes, no introducidos por este ME)
- 1052 tests coleccionables (mismos que antes)

**Estimación original:** 2-3 horas | **Real:** ~1.5 horas  
**Riesgo materializado:** Imports `from conftest import rt_objs` → resuelto eliminando conftest de subdirectorios (pytest hereda del raíz naturalmente)

---

### ME-TQ-2: Tests M2 — Serialización AST

**Manual:** M2 §12 — Serialización AST  
**Criterio:** Serialización y deserialización correcta a `.syn.json`  
**Estado actual:** Existe `test_ast_serialization_10.py` (no citado por M2)  
**Acción:** Crear test de serialización en unit/

| Test | Descripción |
|---|---|
| test_serializar_ast_a_json | Programa completo → JSON válido |
| test_deserializar_json_a_ast | JSON → AST reconstruido |
| test_roundtrip | Serializar → deserializar → verificar equivalencia |
| test_nodos_vacios | AST vacío serializa/deserializa correctamente |
| test_nodos_anidados | Expresiones anidadas preservan estructura |
| test_encoding_utf8 | Caracteres especiales en identificadores/strings |

**Estimación:** 1-2 horas  
**Dependencia:** Ninguna (puede ejecutarse independientemente)

---

### ME-TQ-3: Tests M3 — Lexer, Parser, FFI Syquex

**Manual:** M3 §9  
**Archivos a crear/mover:**

| Archivo | Acción | Tests mínimos |
|---|---|---|
| `tests/syquex/test_lexer.py` | MOVER desde `unit/test_syquex_lexer.py` | Verificar que la ruta coincide con M3 §9 |
| `tests/syquex/test_parser.py` | MOVER desde `unit/test_syquex_parser.py` | Verificar que la ruta coincide con M3 §9 |
| syquex/test_ffi.py | **NUEVO** | test_externo_declaracion, test_externo_llamada, test_ffi_tipos_basicos, test_ffi_conversion |
| syquex/test_export.py | **NUEVO** (stub F26) | test_export_valido, test_export_genera_binding, test_export_sin_parametros |

**Criterio M3:** 100% pass para cada test  
**Estimación:** 3-4 horas  
**Dependencia:** M3 (Syquex) implementación

---

### ME-TQ-4: Tests M6 — FFI C, Export Python, Transpile

**Manual:** M6 §9  
**Archivos a crear:**

| Archivo | Tests mínimos | Criterio |
|---|---|---|
| integration/test_ffi.py | test_llamada_c_basica, test_pasaje_tipos, test_retorno_valor, test_ffi_memoria | 100% pass |
| integration/test_export_python.py | test_genera_binding, test_binding_compila, test_binding_ejecuta | Bindings ejecutables |
| integration/test_transpile.py | test_python_a_syquex_sintaxis, test_codigo_generado_compila, test_funciones_mapeadas | Código generado compila |

**Estimación:** 4-5 horas  
**Dependencia:** M6 (Integración ecosistema) implementación

---

### ME-TQ-5: Tests M8 — LSP, AI, CLI, Debugger (MAYOR VOLUMEN)

**Manual:** M8 §9 — 12 tests requeridos, solo 2 existen  
**Archivos a crear:**

| Archivo | Tests mínimos | Criterio |
|---|---|---|
| integration/test_lsp_completion.py | test_inicializacion, test_sugerencias_basicas, test_sugerencias_contexto | Sugerencias correctas |
| integration/test_lsp_hover.py | test_hover_variable, test_hover_funcion, test_hover_tipo | Información precisa |
| integration/test_ai_explain.py | test_explicar_codigo, test_explicar_error | 100% pass |
| integration/test_ai_complete.py | test_completar_funcion, test_completar_expresion | Código generado compila |
| integration/test_ai_fix.py | test_fix_error_sintaxis, test_fix_error_semantico | Corrección válida |
| integration/test_ai_correction.py | test_correccion_un_intento, test_correccion_tres_intentos | ≤3 intentos |
| integration/test_cli_check.py | test_check_sin_errores, test_check_con_errores, test_no_genera_binario | Flag funciona correctamente |
| integration/test_debug_record.py | test_grabar_traza, test_traza_contiene_pasos | Traza generada |
| integration/test_debug_reverse.py | test_revertir_paso, test_revertir_multiple | Retroceso funciona |
| `tests/integration/test_cli.py` | `test_cli_help`, `test_cli_version`, `test_cli_compilar` | 100% pass |

**Estimación:** 8-10 horas  
**Dependencia:** M8 (Herramientas de desarrollo) implementación  
**Nota:** Estos tests pueden ser stubs con `pytest.skip` si el código aún no existe, pero la estructura DEBE estar lista

---

### ME-TQ-6: Tests vacíos y placeholder

**Manual:** Regla 5 gobernanza — tests inmodificables, solo endurecer  
**Acción:** Implementar los 2 tests con `pass`

| Archivo | Test | Implementación |
|---|---|---|
| `tests/syquex/test_concurrency.py` | `test_recepcion_canal` | Verificar recepción de valor por canal |
| `tests/syquex/test_result.py` | `test_intentar_atrapar` | Verificar propagación de errores con `?` |

**Estimación:** 1-2 horas  
**Dependencia:** M3/M4 implementación de concurrencia y Resultado

---

### ME-TQ-7: Quality hardening — Parametrización, Asserts, Fixtures

**Manual:** M2 §12 (>95% cobertura), Regla 5 gobernanza (calidad industrial)  
**Objetivo:** Subir ratio de parametrización de 0.5% a >15%, eliminar tests sin asserts

| Acción | Detalle | Criterio |
|---|---|---|
| Parametrizar tests multi-idioma | `test_lang_todos_idiomas`, `test_keywords_multi_idioma` → `@parametrize` | Cada idioma es caso independiente |
| Parametrizar tests de edge cases | `test.numero_*`, `test.cadena_*` → `@parametrize` | Granularidad de fallo |
| Agregar asserts a 33 tests | Verificar que cada test tiene al menos 1 assert o raises | `grep -c "assert\|raises" tests/` > 1658 |
| Extraer `_find_gcc()` a conftest compartido | Eliminar duplicación en 8+ archivos syquex/ | 1 definición en conftest |
| Crear fixture `compilar_texto` parametrizada | Reutilizar patrón de test_contracts.py | Todos los tests M2 la usan |
| Agregar markers pytest | `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow` | Selección por categoría |

**Estimación:** 6-8 horas  
**Dependencia:** Independiente (mejoras incrementales)

---

### ME-TQ-8: Infraestructura de testing

**Manual:** M1 §7.2 (suite completa), M9 §6.1 (Definition of Done)  
**Acciones:**

| Acción | Detalle |
|---|---|
| Crear `pytest.ini` o `[tool.pytest.ini_options]` en `pyproject.toml` | `testpaths = ["tests"]`, `markers = [unit, integration, syquex, fuzz, stress, security, opensyn]`, `timeout = 300` |
| ~~Crear conftest.py por subdirectorios~~ | ~~5 archivos~~ Descartado: sombrea el raíz |
| Crear `tests/micro_bootstrap/__init__.py` + tests stub | Directorio requerido por M1 §2 |
| Eliminar archivos `_*.py` raíz (código muerto) | Verificar que no son imports necesarios |

**Estimación:** 3-4 horas  
**Dependencia:** ME-TQ-1 (reorganización previa)

---

## 4. CRONOGRAMA Y DEPENDENCIAS

```
ME-TQ-1 (Limpieza) ─────────────────────────────┐
ME-TQ-8 (Infraestructura) ───────────────────────┤
                                                   ├──→ ME-TQ-7 (Quality hardening)
ME-TQ-2 (M2 Serialización) ──────────────────────┤
ME-TQ-3 (M3 Syquex) ─────────────────────────────┤
ME-TQ-6 (Tests vacíos) ──────────────────────────┤
                                                   │
ME-TQ-4 (M6 FFI/Export) ──────── depende de M6 ──┤
ME-TQ-5 (M8 LSP/AI/CLI) ─────── depende de M8 ──┘
```

**Orden recomendado:**
1. ME-TQ-1 + ME-TQ-8 (paralelo, base para todo)
2. ME-TQ-2 + ME-TQ-3 + ME-TQ-6 (paralelo, tests M2/M3)
3. ME-TQ-7 (hardening, después de reorganización)
4. ME-TQ-4 + ME-TQ-5 (paralelo, tests M6/M8 — dependen de implementación)

---

## 5. MÉTRICAS OBJETIVO

| Indicador | Actual | Objetivo |
|---|---|---|
| Tests obligatorios M1-M9 presentes en ruta correcta | ~60/85 | **85/85 (100%)** |
| Tests vacíos (placeholder) | 2 | **0** |
| Tests sin asserts | 33 | **<5** |
| Parametrización | 0.5% | **>15%** |
| Archivos tmp sin limpiar | 59 | **0** |
| conftest.py por directorio | 1/7 | **7/7** |
| Config pytest central | No | **Sí** |
| M8 cobertura | 2/12 | **12/12** |
| M6 cobertura | 4/7 | **7/7** |

---

## 6. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Imports rotos al mover archivos | Alta | Ejecutar `pytest --collect-only` después de cada movimiento |
| Tests M6/M8 dependen de código no implementado | Alta | Crear stubs con `pytest.skip(reason="M6 no implementado")` |
| conftest compartido rompe aislamiento | Baja | Tests por directorio con fixtures específicas |
| Movimientos rompen CI | Media | Verificar CI job antes de commitear |
| Parametrización incrementa tiempo de suite | Baja | Usar `pytest-xdist` para paralelización |

---

## 7. APROBACIONES

| Rol | Nombre | Fecha | Estado |
|---|---|---|---|
| Arquitecto | _____________ | ____/____/____ | ☐ Aprobado |
| QA Lead | _____________ | ____/____/____ | ☐ Aprobado |

---

**FIN DEL PLAN**
