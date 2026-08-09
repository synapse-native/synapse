# FASE 2 — Cierre de la brecha 2.4 P0: Hindley-Milner (Manual 2 §8.2)

- **Fecha:** 2026-08-09
- **Fase:** 2 (Tabla de símbolos y análisis semántico) — checklist 2.4 → ✅
- **Referencias:** inventario `docs/reportes/FASE_2_B1.md` · Manual 2 §8.2 (§8.1 pasadas, §8.2 HM, §8.3 ADT)
- **Decisión del Arquitecto:** Opción B — representación estructurada `TipoKind` (Manual 2 §8.2), ejecutada por etapas con validación continua.

---

## 1. Objetivo

El inventario B1 identificó como P0 que **la inferencia de tipos era dirigida por sintaxis** (strings
normalizados, sin `TVar`/unificación/`occurs check`), y que los argumentos de tipo de las
instanciaciones de ADT (`Resultado<entero,texto>`) **no se validaban** (ni aridad contra
`Resultado<T,E>`, ni que los argumentos fueran tipos conocidos). La brecha 2.4 cierra ambos puntos
con la máquina Hindley-Milner del Manual 2 §8.2.

## 2. Cambios

| Archivo | Cambio |
|---|---|
| `compilador/tipos.py` **(nuevo)** | Representación estructurada `Tipo`/`TipoKind` (los 9 kinds del Manual 2 §8.2); conversión cadena↔`Tipo` (`tipo_desde_cadena`/`tipo_a_cadena`, anidados/punteros/referencias/rc); `es_tipo_conocido` (aridad de ADT, argumentos conocidos); `UnificadorHM` (algoritmo W: sustitución, *occurs check* que prohíbe tipos recursivos `T = T*`, instanciación). |
| `compilador/diagnostics.py` | Nuevo `ERR_SEM_TYPE_AMBIGUOUS` (6 idiomas, §8.2). |
| `compilador/semantic_types.py` | Integración HM: `_validar_firma_funcion`/`_validar_aridad_instanciaciones` (pasada 2: aridad de ADT, base y argumentos conocidos, recursivo para anidados); `_recolectar_tvars_firma` (regla de TVar **desnudo**); `_inferir_llamada_hm` (TVar frescos por llamada con **cache por nombre**, unificación con occurs check, exenciones ABI `void*`/texto); `_instanciar_retorno` (`ERR_SEM_TYPE_AMBIGUOUS` en el sitio de llamada). |
| `compilador/semantic_checker.py` | Hook `_validar_firma_funcion(nodo)` en `_analizar_funcion` (pasada 2, L338). |
| `tests/unit/test_type_inference.py` **(nuevo)** | Test obligatorio del Manual 2 §12: **28 tests** (representación, unificación, occurs check, aridad, conocidos, checker e2e). |
| `tests/fixtures/test_a23_parity.c` | Harness regenerado: define `ERR_SEM_TYPE_AMBIGUOUS (40)`. |

## 3. Semántica implementada

1. **Validación de firmas (pasada 2, todas las funciones):** cada instanciación `Base<A,B>`
   en parámetros/retorno se valida contra el ADT registrado:
   - **Aridad:** `Resultado<entero>` → error (`ERR_SEM_TIPO_INCOMPATIBLE`), esperados 2.
   - **Base conocida:** typo `Resultados<entero,texto>` → error (revisión code-reviewer).
   - **Argumentos conocidos:** `Resultado<entero,NoExiste>` → error; anidados recursivos
     (`Resultado<Resultado<int,texto>,float>`) soportados.
2. **Funciones genéricas (TVar desnudo):** `funcion identidad(x: T) -> T` — el TVar se
   infiere de la llamada (`identidad(5)` → `int`) mediante unificación. Si un TVar del retorno
   queda sin resolver (`funcion generar() -> T`) → `ERR_SEM_TYPE_AMBIGUOUS` en la llamada.
3. **Regla de TVar desnudo:** solo un identificador en mayúscula que aparece como tipo exacto
   de parámetro/retorno es variable de tipo; los identificadores dentro de `<...>` son SIEMPRE
   tipos concretos (evita que un typo evada la validación). Los structs en mayúscula
   (`Persona`) se excluyen explícitamente de ser TVar (revisión code-reviewer).
4. **Compatibilidad:** el pipeline clásico (strings) no cambia; `tipo_desde_cadena`/`tipo_a_cadena`
   convierten sin tocar parser/codegen/puente. Exenciones de la ABI `void*` preservadas.

## 4. Validación

- **`tests/unit/test_type_inference.py`: 28/28 PASS** (nuevos).
- **Regresión:** `tests/unit/` **177 passed**; semántica (`test_semantico` + `test_borrow_checker`
  + `test_e2e_borrow_abort`) **47 passed**; D-6 (4+1 skip), D-2 (3+1 skip), a23 (3+7 skip);
  paridades nativas **RC 0**.
- 0 cambios en parser/codegen/puente; el bootstrap S2==S3 no se ve afectado (el checker S1
  no interviene en la auto-compilación nativa).

## 5. Revisión del código (code-reviewer)

| Hallazgo | Resolución |
|---|---|
| **Bug:** mayúsculas conocidas (`Persona`, `Resultado` desnudo) se convertían a TVar → unificación errónea en funciones genéricas | Corregido: `estructuras_conocidas` en `tipo_desde_cadena`; test `test_struct_mayuscula_*` (2) |
| **Gap:** base de ADT desconocida en firma pasaba silenciosa | Corregido: `_validar_aridad_instanciaciones` valida la base contra `_estructuras`/`_adt_parametros`; test `test_firma_base_desconocida` |
| **Gap:** `_validar_firma_funcion` duplicaba diagnósticos (pasada 2 + cada llamada) | Corregido: la llamada redundante en `_inferir_llamada_hm` se eliminó |
| AMBIGUOUS se reportaba en la definición, no en la expresión | Corregido: se reporta en el sitio de llamada (`nodo.linea/columna`) |

## 6. Riesgos documentados (deuda)

1. **Paridad nativo (P1):** `nucleo/analizador_semantico.syn` **no valida** aridad ni
   argumentos de instanciaciones (verificado: 0 refs a `instanciacion`/`aridad`/`tipo_conocido`).
   El S1 es ahora más estricto → divergencia S1/nativo documentada (patrón D-6 riesgo (e)).
   La implementación HM en el frontend nativo (`.syn`) queda como trabajo pendiente de Fase 2.
2. **Exención `void*`:** `_inferir_llamada_hm` exime `texto` genérico además de `CadenaSegura`
   (más permisivo que el flujo clásico) — divergencia menor aceptada por compatibilidad.
3. El heurístico de TVar desnudo cubre las firmas actuales (fixtures D-2 usan instanciaciones
   concretas); la sintaxis de funciones genéricas explícitas no está en el manual y no se añadió.

## 7. HASH COMMIT

**`15ba9fa`** — implementación (8 archivos, +911/−2).


## 8. Seguimiento de prioridades del Arquitecto (2026-08-09)

Orden del Arquitecto tras el cierre de 2.4, ejecutado con evidencia:

| # | Prioridad | Accion | Evidencia |
|---|---|---|---|
| 1 | **Documentar la divergencia (P1)** | `nucleo/README.md` **(nuevo)** con la tabla S1 vs nativo y la referencia de implementacion, para que los ingenieros del frontend nativo no asuman validacion inexistente | `nucleo/README.md` |
| 2 | **Tarea de roadmap Fase 2 nativa (P1)** | Entregable explicito anadido a ROADMAP.md → FASE 2 (aridad/base/argumentos de ADT + unificacion HM en `nucleo/analizador_semantico.syn`, paridad al S1) | `ROADMAP.md` (seccion FASE 2) |
| 3 | **Validar integracion D-6/D-2** | 2 tests nuevos que pasan los fixtures reales por el checker 2.4: `test_d2_genericos.syn` (ADT generico + ok/err + `?` + `.tag`) y `test_d6_propagar.syn` (ADT concreto + `?`) — **sin errores** | `test_integracion_fixture_d2` + `test_integracion_fixture_d6` (28 → **30 tests**) |
| 4 | **Evaluar rendimiento** | Benchmark del pipeline S1 (lexer/parser/analizar) con la validacion HM activa | ver tabla abajo |

**Benchmark (prioridad 4):** la validacion HM anade un coste despreciable. Solo las
firmas con TVar desnudo disparan la unificacion (algoritmo W); la validacion de
aridad es O(firmas x profundidad de tipos). El propio compilador se analiza en milisegundos:

| Carga | Lineas | Lexer | Parser | Analizar | Total |
|---|---|---|---|---|---|
| fixture D-2 (generico) | 26 | <1 ms | <1 ms | 1 ms | 2 ms |
| sintetico 300 funciones | 601 | 14 ms | 10 ms | 6 ms | 29 ms |
| `nucleo/principal.syn` (el compilador) | 582 | 19 ms | 11 ms | **2 ms** | 32 ms |

**Conclusion:** sin regresiones significativas; el coste HM es O(firmas genericas),
no O(codigo total), por lo que escala linealmente y es despreciable en cargas reales.

**Hash del seguimiento:** `5350927` (5 archivos, +100).
