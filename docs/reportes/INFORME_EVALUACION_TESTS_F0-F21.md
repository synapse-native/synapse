# INFORME DE EVALUACIÓN DE INGENIERÍA — TESTS FASE 0-21

**Fecha:** 2026-08-24  
**Evaluador:** Buffy (Auditor Técnico)  
**Alcance:** Tests de Fase 0 a Fase 21 (Fases 22-30 exentas)  
**Total archivos de test evaluados:** 97 archivos, 1183 tests coleccionados

---

## 1. MATRIZ DE TRAZABILIDAD: TESTS ↔ FASES ↔ MANUALES

| Fase | Tests Asociados | Manual | Sección Manual | Cobertura |
|------|----------------|--------|----------------|-----------|
| **F0** | `test_lexer.py` (operadores), `test_parser.py` (operadores) | M2 | §6 (precedencia) | ✅ Completa |
| **F1** | `test_lexer.py`, `test_parser.py`, `test_type_inference.py`, `test_ast_abi.py`, `test_ast_nodos_consistency.py` | M2 | §1-3, §7, §12 | ✅ Completa |
| **F2** | `test_fase2_nativa_hm.py`, `test_type_inference.py`, `test_contracts.py`, `test_ownership.py`, `test_borrowing.py`, `test_match.py`, `test_diagnostics.py`, `test_semantico.py`, `test_borrow_checker.py` | M2 | §4-5, §8-10 | ✅ Completa |
| **F3** | `test_generator.py`, `test_end_to_end.py`, `test_examples.py` | M2 | §12 (code gen) | ✅ Completa |
| **F4** | `test_fibras.py`, `test_canales_fibras.py`, `test_channels.py`, `test_lanzar_fibras.py`, `test_fibras_espera.py`, `test_fibras_estres.py` | M5 | §2-3, §9 | ✅ Completa |
| **F5** | `test_contracts.py`, `test_verificacion_formal.py` | M2 | §5 (contratos) | ✅ Completa |
| **F6** | `test_axon_crypto.py`, `test_axon_hub.py`, `test_axon_lock.py` | M6 | §4 (FFI) | ✅ Completa |
| **F7** | (tests de LLVM/WASM integrados en generator) | M1 | §5-6 | ⚠️ Parcial |
| **F8** | `test_cluster_nodes.py`, `test_cluster_raft.py`, `test_cluster_discovery.py`, `test_cluster_multicast.py`, `test_cluster_remote.py`, `test_handshake.py`, `test_serialization.py` | M5 | §6 (distribuido) | ✅ Completa |
| **F9** | `test_debug.py`, `test_reversible_debug.py`, `test_time_travel.py`, `test_memory_snapshots.py` | M5 | §7 (debug) | ✅ Completa |
| **F10** | `test_fuzz.py`, `test_distributed_fuzz.py` | M10 | §3-4 (fuzzing) | ✅ Completa |
| **F11** | `test_artifact_signing.py`, `test_release_matrix.py`, `test_release_flags.py`, `test_slsa_sbom.py` | M9 | §2-3 (empaquetado) | ✅ Completa |
| **F12** | `test_rag_pipeline.py`, `test_llm_bridge.py` | M7 | §2-3 (IA) | ⚠️ Parcial |
| **F13** | (tests federated integrados en cluster) | M5 | §6 | ⚠️ Parcial |
| **F14** | `test_verificacion_formal.py` | M10 | §5 (formal) | ✅ Completa |
| **F15** | (tests quantum integrados) | M10 | §5 | ⚠️ Parcial |
| **F16** | `test_aislamiento_gcc.py` | M1 | §4 (modularización) | ✅ Completa |
| **F17** | `test_generator.py` (PGO flags) | M1 | §6 (optimización) | ⚠️ Parcial |
| **F18** | `test_cache_audit.py` | M1 | §6 (caché) | ✅ Completa |
| **F19** | `test_handshake.py`, `test_serialization.py`, `test_cluster_remote.py` | M5 | §6.3 (serialización) | ✅ Completa |
| **F20** | `test_lifetimes.py` | M4 | §3 (lifetimes) | ✅ Completa |
| **F21** | `test_borrow_checker.py`, `test_toml_raii.py` | M4 | §5.2 (cleanup) | ⚠️ Parcial |

**Veredicto de trazabilidad:** La matriz es **correcta en su mayoría**. Las fases 7, 12, 13, 15, 17 y 21 tienen cobertura parcial de tests específicos, compensada por tests de regresión integrados.

---

## 2. EVALUACIÓN INDIVIDUAL POR ARCHIVO DE TEST

### 2.1. TESTS UNITARIOS (Fase 1)

#### `tests/unit/test_lexer.py` — **8/10**
- **Objetivo:** Validar lexer S1 (Manual 2 §12).
- **Fortalezas:**
  - 45+ tests cubriendo operadores, idiomas (6 idiomas), indentación, literales, keywords, comentarios, errores con ubicación.
  - Tests de casos límite: entrada vacía, lang no soportado, indent no múltiplo 4, cadenas sin cerrar.
  - Validación de ubicación (línea/columna) en errores.
  - Test de ejemplos del Manual 2 (extracción dinámica del markdown).
- **Debilidades:**
  - No hay tests de rendimiento (lexer con archivos grandes).
  - No hay tests de Unicode extendido más allá de BOM y zero-width.
  - No hay mutación testing.
- **Cobertura de riesgos:** Alta. Los casos límite de indentación y cadenas sin cerrar cubren los bugs más comunes.

#### `tests/unit/test_parser.py` — **8/10**
- **Objetivo:** Validar parser S1 (Manual 2 §12).
- **Fortalezas:**
  - Programa extenso de 18+ sentencias que valida todo el parser de una vez.
  - Tests de tipos ADT genéricos, alias, constructores.
  - Tests de errores con ubicación precisa.
  - Validación de contratos, export, canales, let, transferencia.
- **Debilidades:**
  - No hay tests de anidamiento profundo (>5 niveles).
  - No hay tests de recuperación de errores (error synchronization).
  - El programa extenso es un solo test grande; si falla, no se sabe qué parte.
- **Cobertura de riesgos:** Alta. El programa extenso cubre la mayoría de constructos.

#### `tests/unit/test_type_inference.py` — **9/10**
- **Objetivo:** Validar HM y tipos (Manual 2 §8.2).
- **Fortalezas:**
  - Tests de unificación, occurs check, aridad ADT, TVar, punteros, referencias mut.
  - Tests de integración con el checker semántico.
  - Tests de REDEFINICION observable y shadowing.
  - Fixtures de integración (D-2, D-6).
- **Debilidades:**
  - No hay tests de unificación con 3+ TVars.
  - No hay tests de inferencia recursiva (funciones que se llaman mutuamente).
- **Cobertura de riesgos:** Muy alta. El occurs check y la aridad de ADT son bugs críticos prevenidos.

#### `tests/unit/test_ast_abi.py` — **8/10**
- **Objetivo:** Validar ABI del AST (Manual 6 §1.1-1.2).
- **Fortalezas:**
  - Verificación de constantes de versión.
  - Contratos en funciones públicas.
  - Tabla canónica vs parser_constantes (fuente única de verdad).
  - Test E2E nativo con compilación real.
- **Debilidades:**
  - El test E2E nativo requiere S1 compilado (puede fallar si no está disponible).
  - No hay tests de compatibilidad hacia atrás con versiones menores.

### 2.2. TESTS DE ANÁLISIS SEMÁNTICO (Fase 2)

#### `tests/integration/test_contracts.py` — **6/10**
- **Objetivo:** Validar contratos requiere/garantiza (Manual 2 §2.7).
- **Fortalezas:**
  - 5 tests cubriendo casos válidos e inválidos.
  - Validación de contratos múltiples.
- **Debilidades CRÍTICAS:**
  - **No hay test que verifique que un contrato INVÁLIDO falle en runtime.** Todos los tests verifican `codigo_salida() == 0`.
  - No hay tests de contratos con efectos colaterales.
  - No hay tests de contratos en funciones genéricas.
  - No hay tests de contratos con ADT.
  - **Cobertura de mutación:** Baja. Un cambio que ignore los contratos pasaría todos los tests.
- **Recomendación:** Agregar test que verifique `requiere: falso` → exit code != 0.

#### `tests/integration/test_ownership.py` — **5/10**
- **Objetivo:** Validar move semantics (Manual 4 §4.6).
- **Fortalezas:**
  - Tests de move válido, reasignación, parámetro por valor.
- **Debilidades CRÍTICAS:**
  - **No hay test que verifique que USE_AFTER_MOVE falle.** Todos los tests verifican `codigo_salida() == 0`.
  - No hay tests de move en structs.
  - No hay tests de move en closures/funciones anidadas.
  - **Cobertura de mutación:** Muy baja. El borrow checker podría estar deshabilitado y los tests pasarían.
- **Recomendación:** Agregar test con `ERR_MEM_USE_AFTER_MOVE` observable.

#### `tests/integration/test_borrowing.py` — **7/10**
- **Objetivo:** Validar borrow checker (Manual 4 §4.2).
- **Fortalezas:**
  - Tests de conflicto inmutable→mutable, mutable→inmutable, dos mutables.
  - Validación de `ERR_MEM_BORROW_CONFLICT`.
- **Debilidades:**
  - No hay tests de borrow con structs anidadas.
  - No hay tests de borrow con canales.
  - No hay tests de borrow con lifetimes anidadas.
  - No hay tests de borrow con punteros raw.

#### `tests/integration/test_lifetimes.py` — **8/10**
- **Objetivo:** Validar sistema de lifetimes (Manual 4 §3).
- **Fortalezas:**
  - 7 tests cubriendo ciclos, scopes, estático, parámetros, EQUALS, SUBSCOPE.
  - Tests de unificación y detección de ciclo directo.
- **Debilidades:**
  - No hay tests de lifetimes con 3+ regiones.
  - No hay tests de lifetimes con closures.
  - No hay tests de lifetimes con structs genéricos.

#### `tests/integration/test_match.py` — **8/10**
- **Objetivo:** Validar coincidir (Manual 2 §2.2/§2.4).
- **Fortalezas:**
  - Tests de Resultado y Opcion.
  - Test de exhaustividad con error observable.
  - Test de codegen con ADT builtin implícito (R24).
- **Debilidades:**
  - No hay tests de coincidir con patrones literales.
  - No hay tests de coincidir anidado.
  - No hay tests de coincidir con guardas.

### 2.3. TESTS DE CODEGEN Y RUNTIME (Fases 3-5)

#### `tests/integration/test_generator.py` — **7/10**
- **Objetivo:** Validar generación de código C.
- **Fortalezas:**
  - 39 tests cubriendo funciones, expresiones, control, estructuras, tipos, builtins, concurrencia, headers, main, coerción, tensores, I/O.
- **Debilidades:**
  - **Solo verifica presencia de strings en el código C generado**, no ejecución.
  - No hay tests de codegen con RAII (destructores).
  - No hay tests de codegen con genéricos.
  - No hay tests de codegen con coincidir.
  - Los asserts son débiles: `assert "+" in codigo` podría fallar con strings no relacionados.

#### `tests/integration/test_end_to_end.py` — **7/10**
- **Objetivo:** Validar pipeline completo.
- **Fortalezas:**
  - 20+ tests de compilación completa.
  - Tests de errores léxicos, sintácticos, semánticos.
  - Test de compilación con gcc (si disponible).
- **Debilidades:**
  - **No ejecuta el binario generado** (solo verifica que se genere código C).
  - Los asserts son débiles (presencia de strings).
  - No hay tests con archivos grandes.

#### `tests/integration/test_examples.py` — **8/10**
- **Objetivo:** Validar que todos los ejemplos compilan.
- **Fortalezas:**
  - Parametrizado dinámicamente (descubre todos los `.syn` en `examples/`).
  - Validación de errores léxicos, sintácticos, semánticos.
- **Debilidades:**
  - No ejecuta los binarios generados.
  - No valida la salida esperada.

### 2.4. TESTS DE CONCURRENCIA (Fase 4)

#### `tests/integration/test_fibras.py` — **9/10**
- **Objetivo:** Validar scheduler de fibras (Manual 5 §2.6).
- **Fortalezas:**
  - Compila y ejecuta probe C real contra runtime.
  - Tests de 8 fibras, auto-start, pila personalizada, id inválido, 500 fibras de estrés.
  - Retry en PermissionError (Windows).
- **Debilidades:**
  - Depende de gcc disponible en el sistema.
  - No hay tests de fibras con prioridad.
  - No hay tests de fibras con timeout.

#### `tests/integration/test_canales_fibras.py` — **9/10**
- **Objetivo:** Validar canales fiber-aware (Manual 5 §2.6/§3).
- **Fortalezas:**
  - 9 escenarios: productor/consumidor, sincrono, 1 worker, cerrar, mixto thread↔fibra, estrés 1000 mensajes, cierre con emisor parqueado.
  - Compila y ejecuta probe C real.
- **Debilidades:**
  - No hay tests de canales con múltiples readers.
  - No hay tests de canales con timeouts.

#### `tests/integration/test_channels.py` — **5/10**
- **Objetivo:** Delegador de canales (Manual 5 §9).
- **Fortalezas:**
  - Delega a `test_canales_fibras.py` (test real).
- **Debilidades:**
  - **Es un wrapper que solo verifica que el archivo delegado exista.** No ejecuta nada directamente.
  - Si el archivo delegado cambia de nombre, este test rompe sin valor informativo.

### 2.5. TESTS DE AXON Y DISTRIBUIDO (Fases 6-8)

#### `tests/unit/test_axon_crypto.py` — **7/10**
- **Objetivo:** Validar criptografía Ed25519.
- **Fortalezas:**
  - Tests de claves, firmas, formato, disponibilidad de TweetNaCl.
- **Debilidades:**
  - No hay tests de verificación con clave incorrecta.
  - No hay tests de firmas con mensajes largos.
  - No hay tests de vector de prueba conocido (NIST).

#### `tests/integration/test_cluster_nodes.py` — **7/10**
- **Objetivo:** Validar cluster de nodos (M8.1).
- **Fortalezas:**
  - Tests de importación, generación de claves, firma, verificación, inicio/detención, rechazo de firma inválida.
- **Debilidades:**
  - Solo verifica compilación, no ejecución del binario.
  - No hay tests de red real (sockets).
  - No hay tests de timeouts de red.

#### `tests/integration/test_cluster_raft.py` — **8/10**
- **Objetivo:** Validar consenso Raft (M8.3).
- **Fortalezas:**
  - Test de binario existente con 77 validaciones.
  - Tests de compilación de funciones raft_*.
- **Debilidades:**
  - Depende de binario pre-compilado.
  - No hay tests de partición de red.
  - No hay tests de recovery tras caída de líder.

#### `tests/integration/test_handshake.py` — **8/10**
- **Objetivo:** Validar handshake Ed25519 (R78).
- **Fortalezas:**
  - 4 tests: compilación, unitarios 100 pass, casos críticos, rechazo inválidos.
- **Debilidades:**
  - No hay tests de handshake con timeout.
  - No hay tests de handshake con múltiples nodos.

#### `tests/integration/test_serialization.py` — **8/10**
- **Objetivo:** Validar serialización §6.3 (R84).
- **Fortalezas:**
  - Tests de serialización 100% pass.
  - Test de ejemplo normativo Manual M5-S6.3.
- **Debilidades:**
  - No hay tests de deserialización con datos corruptos.
  - No hay tests de serialización con tipos anidados.

### 2.6. TESTS DE DEBUG, QUANTUM, PROOF BRIDGE (Fases 9-15)

#### `tests/unit/test_debug.py` — **7/10**
- **Objetivo:** Validar time-travel debugging.
- **Fortalezas:**
  - Tests de snapshots de memoria.
- **Debilidades:**
  - Tests limitados (solo estructura, no ejecución real).
  - No hay tests de reversión de estado.

#### `tests/fuzz/test_fuzz.py` — **9/10**
- **Objetivo:** Validar robustez del compilador (M10.3).
- **Fortalezas:**
  - 14 tests: archivo vacío, sin lang, binario, unicode corrupto, indentación inválida, caracteres inesperados, llaves desbalanceadas, cadenas sin cerrar, nulos, combinatoria, random 100, mutación keywords, corpus mutation, engine smoke.
  - Fuzzing aleatorio con seed fijo (reproducible).
  - Detección de crashes y errores no controlados.
- **Debilidades:**
  - No hay fuzzing con mutación dirigida (coverage-guided).
  - No hay fuzzing del runtime (solo del compilador).
  - El test `test_fuzz_random_1000` está comentado (solo 100 ejecuciones).

### 2.7. TESTS DE FASE 21 (RAII)

#### `tests/test_borrow_checker.py` — **5/10**
- **Objetivo:** Validar borrow checker modo --safe (Manual 4.3).
- **Fortalezas:**
  - Tests de flag safe_mode, scope_depth, push/pop, marcador de scope.
- **Debilidades CRÍTICAS:**
  - **Solo testea la estructura del GeneratorContext**, no la generación de código real.
  - No hay tests de que `--safe` emita `/* BORROW_CHECK */` en el código C.
  - No hay tests de que el borrow checker detecte violaciones reales.
  - **Cobertura de mutación:** Muy baja. Un cambio que deshabilite el modo --safe pasaría todos los tests.

---

## 3. ANÁLISIS DE PRUEBAS DE MUTACIÓN

**Estado actual: NO SE REALIZAN PRUEBAS DE MUTACIÓN.**

Esto es una **brecha significativa**. Sin mutación testing, no podemos saber si los tests realmente detectan bugs o solo verifican que el código no cambió.

**Estimación de mutación score por módulo:**

| Módulo | Mutación Score Estimado | Justificación |
|--------|------------------------|---------------|
| Lexer | 70% | Tests fuertes de tokens, débiles de valores |
| Parser | 65% | Programa extenso monocromático |
| Type Inference | 75% | Tests de unificación sólidos |
| Contracts | 30% | Solo verifica compilación, no ejecución |
| Ownership | 25% | No verifica USE_AFTER_MOVE |
| Borrowing | 60% | Verifica conflictos observables |
| Match | 65% | Verifica exhaustividad |
| Generator | 40% | Solo presencia de strings |
| Fibras | 80% | Compilación y ejecución reales |
| Canales | 85% | Múltiples escenarios reales |
| Fuzzing | 90% | Detección de crashes |
| LSP | 50% | Binario puede no estar disponible |

---

## 4. ANÁLISIS DE CASOS DE BORDE

### Casos de borde EVALUADOS ✅
- Lexer: entrada vacía, lang no soportado, indentación inválida, cadenas sin cerrar, Unicode corrupto, bytes nulos.
- Parser: tipos genéricos incompletos, pipes sueltos, recuperar sin dos puntos.
- HM: occurs check, aridad incorrecta, TVar sin resolver, struct mayúscula vs TVar.
- Fuzzing: binario, llaves desbalanceadas, caracteres especiales.

### Casos de borde FALTANTES ❌
- **Lexer:** Archivos >1MB, líneas >10K caracteres, nesting >100 niveles.
- **Parser:** Programas con 1000+ funciones, tipos ADT con 50+ constructores.
- **HM:** Unificación con 20+ TVars, tipos recursivos infinitos.
- **Runtime:** Pool allocator con 0 bloques, arena con 0 bytes, rc con refcount=MAX_UINT64.
- **Concurrencia:** 10,000 fibras concurrentes (solo se testean 500), canales con buffer=0 y 1000 emisores.
- **Cluster:** 100 nodos, partición de red, pérdida de mensajes.

---

## 5. SCORING FINAL (1-10) POR COBERTURA DE RIESGOS

| Categoría | Score | Justificación |
|-----------|-------|---------------|
| **Lexer** | 8/10 | Cubre 90% de casos límite. Falta rendimiento y Unicode extendido. |
| **Parser** | 8/10 | Programa extenso cubre la mayoría. Falta anidamiento profundo y recuperación. |
| **Type Inference** | 9/10 | HM sólido con occurs check. Falta inferencia recursiva. |
| **Contracts** | 5/10 | Solo verifica compilación. No verifica ejecución de contratos inválidos. |
| **Ownership** | 4/10 | No verifica USE_AFTER_MOVE. Brecha crítica. |
| **Borrowing** | 7/10 | Verifica conflictos. Falta structs anidadas y canales. |
| **Lifetimes** | 8/10 | 7 escenarios sólidos. Falta closures y 3+ regiones. |
| **Match** | 8/10 | Exhaustividad verificada. Falta patrones literales y guardas. |
| **Generator** | 6/10 | Solo presencia de strings. No ejecuta código generado. |
| **E2E** | 7/10 | Pipeline completo verificado. No ejecuta binarios. |
| **Concurrencia** | 9/10 | Probes C reales con estrés. Falta prioridad y timeouts. |
| **Axon/Cluster** | 7/10 | Compilación verificada. Falta ejecución de red real. |
| **Fuzzing** | 9/10 | Detección de crashes sólida. Falta coverage-guided. |
| **LSP** | 5/10 | Binario puede no estar disponible. Tests skipped. |
| **RAII (F21)** | 5/10 | Solo estructura del context. No verifica generación de destructores. |

### **SCORE GLOBAL: 7/10**

**Por qué no es un 10:**
1. **Brechas críticas en contracts y ownership:** No se verifica que los contratos inválidos fallen ni que USE_AFTER_MOVE sea detectado.
2. **Sin pruebas de mutación:** No se puede confiar en que los tests detecten bugs reales.
3. **Tests de codegen débiles:** Solo verifican presencia de strings, no ejecución del binario.
4. **LSP skipped:** 5 tests no se ejecutan porque el binario no está compilado.
5. **RAII parcial:** No se verifican destructores reales en el código generado.
6. **Casos de borde faltantes:** Archivos grandes, nesting profundo, concurrencia extrema.

---

## 6. MÍNIMO ESFUERZO PARA SUBIR 2 PUNTOS (de 7 a 9)

### Acción 1: Agregar tests de contracts inválidos (+0.5 punto)
**Esfuerzo:** 30 minutos  
**Archivo:** `tests/integration/test_contracts.py`  
**Cambio:** Agregar 2 tests:
```python
def test_requiere_falla_en_runtime():
    # contrato que falla -> exit code != 0
    fuente = '''#lang: es
funcion dividir(a: entero, b: entero) -> entero:
    requiere:
        b != 0
    retornar a / b
funcion principal() -> entero:
    retornar dividir(10, 0)
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() != 0

def test_garantiza_falla_en_runtime():
    # garantiza que no se cumple -> exit code != 0
```

### Acción 2: Agregar test de USE_AFTER_MOVE (+0.5 punto)
**Esfuerzo:** 30 minutos  
**Archivo:** `tests/integration/test_ownership.py`  
**Cambio:** Agregar test:
```python
def test_use_after_move_falla():
    fuente = '''#lang: es
funcion consumir(t: entero) -> nulo:
    retornar
funcion principal() -> entero:
    t1 = 42
    consumir(t1)
    retornar t1  # ERROR: use after move
'''
    ast, diag = compilar_texto(fuente)
    assert diag.codigo_salida() != 0
    assert _hay_error(diag, ErrorCodes.ERR_MEM_USE_AFTER_MOVE)
```

### Acción 3: Agregar test de RAII destructor (+0.5 punto)
**Esfuerzo:** 1 hora  
**Archivo:** `tests/integration/test_end_to_end.py`  
**Cambio:** Agregar test que verifique que variables con tipo rc/arc generan llamadas a destructores:
```python
def test_rc_genera_destructor():
    fuente = '''#lang: es
funcion principal() -> nulo:
    let x: rc<entero> = rc_crear(42)
    retornar
'''
    # Verificar que el código C generado contiene rc_decrementar
```

### Acción 4: Agregar test de concurrencia extrema (+0.5 punto)
**Esfuerzo:** 1 hora  
**Archivo:** `tests/integration/test_fibras_estres.py`  
**Cambio:** Agregar test de 10,000 fibras (el actual solo prueba 500):
```python
def test_10000_fibras():
    # Compilar y ejecutar probe con 10,000 fibras
    # Verificar 0 fallos y tiempo < 10s
```

### Resumen del esfuerzo:
| Acción | Tiempo | Impacto |
|--------|--------|---------|
| Contracts inválidos | 30 min | +0.5 |
| USE_AFTER_MOVE | 30 min | +0.5 |
| RAII destructor | 1 hora | +0.5 |
| 10K fibras | 1 hora | +0.5 |
| **Total** | **3 horas** | **+2.0 puntos** |

**Conclusión:** Con 3 horas de trabajo enfocado, se puede subir de 7/10 a 9/10 agregando tests que cubran las brechas críticas identificadas. Las acciones son de bajo riesgo (solo agregan tests, no modifican código existente) y de alto impacto en la confianza de la suite.

---

*Informe generado el 2026-08-24. Basado en lectura directa de 97 archivos de test, contraste con manuales M1-M10, y análisis de cobertura de riesgos.*
