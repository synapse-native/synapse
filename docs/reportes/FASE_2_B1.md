# REPORTE FASE 2 — ETAPA B1: INVENTARIO DE BRECHAS (tabla de símbolos y análisis semántico)

> Micro-entregable B1 de la Fase 2 del roadmap (tabla de símbolos y análisis semántico).
> Fuente de verdad: `GUIA_DE_GOBERNANZA.md` §PROTOCOLO DE ENTREGA, `docs/AUDITORIA_ALINEACION_MANUALES.md`
> (checklist 2.1-2.6), `ROADMAP.md` (Fase 2), `docs/manuales/MANUAL 2.md` §8/§9/§10/§12.
> Fecha: 2026-08-09. Criterio B1: *matriz de brechas documentada con evidencia file:line
> y priorización (P0-P3) para las sub-etapas B2/B3 de la Fase 2*.

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE 2 - Etapa B1 — Inventario de brechas del ANALISIS SEMANTICO entre el
       frontend nativo (nucleo/analizador_semantico.syn + tabla_simbolos.syn +
       lifetimes.syn + errores.syn) y el S1 (compilador/semantic_scope.py +
       semantic_types.py + semantic_checker.py + analizador_semantico.py +
       verificador_formal.py), contra el Manual 2 §8 (análisis semántico y sistema
       de tipos), §9 (ownership/borrowing/lifetimes), §10 (taxonomía de errores) y
       §12 (pruebas obligatorias). La matriz cubre los 6 puntos del checklist 2.1-2.6
       de la bitácora, con evidencia file:line en ambos frontends y brechas
       priorizadas (P0-P3) para las sub-etapas B2/B3.
FASE: 2 (tabla de símbolos y análisis semántico, Manual 2; ROADMAP Fase 2) - Etapa B1.
MANUAL REFERENCIADO: Manual 2, Seccion 8 (análisis semántico y sistema de tipos:
       §8.1 ejecución en tres fases; §8.2 inferencia de tipos Hindley-Milner;
       §8.3 ADTs y match exhaustivo), Seccion 9 (El Pacto: ownership & borrowing:
       §9.1 reglas de posesión, §9.2 préstamo, §9.3 análisis de lifetimes), Seccion 10
       (manejo de errores y taxonomía ERR_LEX_*/ERR_SYNTAX_*/ERR_SEM_*/ERR_MEM_*),
       Seccion 12 (pruebas obligatorias de la etapa); Manual 9, Seccion 9.7 (determinismo).
HASH COMMIT: **a44cc16** (bitácora se actualiza al commitear; convención
       'auditoria(FASE_2-B1): inventario de brechas analisis semantico').
COMPILACION: sin cambios de codigo en esta etapa (entregable documental puro).
TESTS: no aplica (ningun cambio de codigo). Se ejecutaron greps/lecturas de evidencia
       sobre ambos frontends, el unity build (principal.syn F8) y los tests existentes
       de la Fase 2 (test_semantico 41, test_borrow_checker 5, test_e2e_borrow_abort 1,
       integration test_borrowing 6, test_lifetimes 7, test_ownership 3, test_match 4).
COBERTURA: sin medicion nueva en este ME (la cobertura del generador quedo cerrada en
       D-5/FASE A con generator.py 95%; la cobertura del SEMANTICO se medira en B2).
MODIFICACIONES DE TESTS: ninguna.
MODULARIZACION: ninguna (inventario documental; la evaluacion de modularizacion de
       analizador_semantico.syn —872 líneas— se registra como hallazgo P2).
RIESGOS IDENTIFICADOS (nuevos, no anticipados por el cierre de FASE A):
  - Hindley-Milner (Manual 2 §8.2) NO esta implementado en ninguno de los dos
    frontends: el S1 usa inferencia DIRIGIDA POR SINTAXIS (_inferir_tipo,
    semantic_types.py L42+, case por tipo de nodo) y el nativo usa builtins con tipos
    fijos (analizador_semantico.syn L262-373). No hay TVar(id), unificacion ni
    occurs check -> el checklist 2.4 es la brecha P0 de la Fase 2.
  - El codigo de error ERR_SEM_TYPE_AMBIGUOUS (Manual 2 §8.2: expresion de tipo
    ambiguo, p.ej. []) NO existe en S1 ni en el nativo — atado a la brecha HM.
  - Los tests obligatorios del Manual 2 §12 tests/unit/test_type_inference.py y
    tests/unit/test_ast_serialization.py NO existen. Los demas tests del §12
    (lexer, parser, contracts, match, ownership, borrowing, lifetimes) SI existen.
  - Hallazgo estructural: el analizador nativo esta VIVO en el runtime S2/S3 — el
    flatten F8 de principal.syn (L224-370) aplana el AST a SemNodo[] y llama
    analizar(&_sem_est) (L366-370). A diferencia del frontend pre-FASE A (codigo
    muerto reescrito por _P_*), aqui NO hay espejo: el semantico nativo es la
    implementacion real de S2/S3 y el S1 debe mantener paridad.
  - Duplicacion de codigo de error: nucleo/errores.syn (38 líneas) y
    nucleo/diagnostics.syn comparten la numeracion ERR_*; verificar al cerrar HM que
    la numeracion canonica de diagnostics.syn manda (patron tokens.syn FASE A).
PROXIMO PASO: Etapa B2 — cerrar la brecha P0 (Hindley-Milner + ERR_SEM_TYPE_AMBIGUOUS
       + tests/unit/test_type_inference.py) y la P1 (tests/unit/test_ast_serialization.py);
       B3 — revision code-reviewer y cierre formal de la Fase 2 (ver matriz abajo).
--- FIN ---
```

---

## 1. RESUMEN EJECUTIVO

La Etapa B1 inventaría el estado real del **análisis semántico** (checklist 2.1-2.6 de
la bitácora, todos marcados ⬜) contra el Manual 2 §8-§10 y §12. Resultado principal:
**5 de los 6 checklist están implementados de facto en ambos frontends** (2.1 scopes,
2.2 tres pasadas, 2.3 taxonomía ERR_SEM_*, 2.5 ownership/borrowing, 2.6 match
exhaustivo), con tests de soporte; **el checklist 2.4 (Hindley-Milner) es la única
brecha estructural P0** — la inferencia actual es dirigida por sintaxis, no el
algoritmo W con TVar/unificación/occurs check del Manual 2 §8.2.

Además, el Manual 2 §12 exige **dos tests unitarios que no existen**:
`tests/unit/test_type_inference.py` (atado a la brecha HM) y
`tests/unit/test_ast_serialization.py` (serialización `.syn.json`).

```
Checklist 2.1 scopes          -> ✅ implementado (nativo + S1)
Checklist 2.2 3 pasadas       -> ✅ implementado (Estructuras->Firmas->Cuerpos)
Checklist 2.3 ERR_SEM_*       -> ✅ implementado (falta ERR_SEM_TYPE_AMBIGUOUS, atado a 2.4)
Checklist 2.4 Hindley-Milner  -> ⚠️ NO implementado (P0)
Checklist 2.5 ownership/borrow-> ✅ implementado (M21.1-M21.4 + S1)
Checklist 2.6 match exhaustivo-> ✅ implementado (ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED)
```

---

## 2. MATRIZ DE BRECHAS (checklist 2.1-2.6, evidencia file:line)

| # | Punto (checklist) | Manual 2 | Nativo (S2/S3) | S1 (Python) | Estado | Prio |
|---|---|---|---|---|---|---|
| 2.1 | `tabla_simbolos.syn`: scopes anidados | §8.1 | `nucleo/tabla_simbolos.syn` (structs `Simbolo`/`TablaSimbolos` + `PROPIEDAD_VIVO`/`PROPIEDAD_MOVIDO`); operaciones en `analizador_semantico.syn`: `tabla_declarar` L151, `tabla_buscar` L192, `tabla_entrar_scope` L211, `tabla_salir_scope` L215, `tabla_marcar_movido` L228, `tabla_esta_movido` L234; scopes anidados en si/mientras/inseguro/coincidir (L629-733) | `compilador/semantic_scope.py` `AnalizadorSemanticoScope`: `_scopes` por niveles, `declarar`/`buscar`/`entrar_scope`/`salir_scope` + `_FUNCIONES_BUILTIN` + `_inicializar_estructuras_nativas` | ✅ implementado en ambos | P2 (revisión) |
| 2.2 | `analizador_semantico.syn`: 3 pasadas (Estructuras→Firmas→Cuerpos) | §8.1 | `analizar_paso_estructuras` L770, `analizar_paso_funciones` L771, `analizar_paso_cuerpos` L801; `analizar` L854 llama las 3 en orden; invocado por el flatten F8 del runtime (`principal.syn` L366-370 `analizar(&_sem_est)`) | `AnalizadorSemanticoChecker.analizar()` (semantic_checker.py L230): bucle 1 estructuras/ADTs, bucle 2 firmas (funciones/externas/export/constantes), bucle 3 `_analizar_funcion` (cuerpos) | ✅ implementado en ambos, paridad de 3 pasadas | P2 (revisión) |
| 2.3 | `errores.syn`: taxonomía ERR_SEM_* | §10.1 | `nucleo/errores.syn`: ERR_SEM_* 14-24, 31-32 + ERR_MEM_LIFETIME_MISMATCH 34 / CYCLE 35; `nucleo/diagnostics.syn`: + ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED 33, ERR_MEM_BORROW_CONFLICT 39, mensajes multi-idioma es/en/fr/pt | `compilador/diagnostics.py` `ErrorCodes`: ERR_SEM_VAR_NO_DECLARADA…ERR_SEM_CONSTANTE_INMUTABLE, EXHAUSTIVE_MATCH_REQUIRED, ERR_MEM_USE_AFTER_MOVE/LIFETIME_MISMATCH/LIFETIME_CYCLE/BORROW_CONFLICT, mensajes 6 idiomas | ✅ implementado; **falta `ERR_SEM_TYPE_AMBIGUOUS` (Manual 2 §8.2)** | P0 (atado a 2.4) |
| 2.4 | Hindley-Milner (unificación, occurs check) | §8.2 | `analizador_semantico.syn` `_inferir_tipo` NO existe como algoritmo W: tipos por `es_builtin`/`builtin_tipo_retorno` (L262-373) + `analizar_expr` (L491-586) — sin TVar/unificación | `semantic_types.py` `_inferir_tipo` (L42+) = **inferencia dirigida por sintaxis** (case por tipo de nodo: literales, identificadores, OpBinaria, llamadas) — sin TVar/unificación/occurs check | ⚠️ **NO implementado (brecha P0)** | **P0** |
| 2.5 | Ownership/borrowing (use-after-move, préstamos) | §9 | `nucleo/lifetimes.syn` M21.1 (`LT_ESTATICO/LT_LOCAL/LT_PARAMETRICO/LT_ELIDIDO`) + M21.2 (`RegionConstraint`, `RegionGraph`, `UnionFind`, `uf_*`, `detectar_ciclo_outlives` L95+); `analizador_semantico.syn` M21.4 (`prestamo_activo` L461, `registrar_prestamo` L478, restricciones OUTLIVES en `analizar_expr` L504-510) | `semantic_checker.py` `Lifetime`/`RegionConstraint`/`UnionFind`/`RegionGraph` (L43-227) + `_verificar_prestamo` (semantic_types.py L267) + `_inicializar_lifetimes_funcion`/`_resolver_lifetimes_funcion` | ✅ implementado en ambos (M21.1-M21.4) | P2 (revisión) |
| 2.6 | Exhaustividad en `coincidir` para ADT | §4.2/§8.3 | `analizador_semantico.syn` NODO_COINCIDIR L678-733: flags `tiene_ok/err/algun/ninguno/wildcard` + validación post-bucle → `ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED` (L728-730) | `semantic_checker.py` NodoCoincidir L594-658 → `ERR_SEM_EXHAUSTIVE_MATCH_REQUIRED` | ✅ implementado en ambos, con test | P2 (revisión) |

---

## 3. PRUEBAS OBLIGATORIAS DEL MANUAL 2 §12 (estado)

| Test del Manual 2 §12 | Archivo | Estado |
|---|---|---|
| Lexer multi-idioma | `tests/unit/test_lexer.py` | ✅ existe (suite verde) |
| Parser EBNF | `tests/unit/test_parser.py` | ✅ existe |
| Contratos requiere/garantiza | `tests/integration/test_contracts.py` | ✅ existe |
| Tipos algebraicos (match exhaustivo) | `tests/integration/test_match.py` (4 tests) | ✅ existe |
| Ownership (move) | `tests/integration/test_ownership.py` (3) + `tests/test_e2e_borrow_abort.py` (1) | ✅ existe |
| Borrowing checker | `tests/integration/test_borrowing.py` (6) + `tests/test_borrow_checker.py` (5) | ✅ existe |
| Lifetimes | `tests/integration/test_lifetimes.py` (7) | ✅ existe |
| **Inferencia de tipos (Hindley-Milner)** | **`tests/unit/test_type_inference.py`** | ❌ **NO EXISTE (P0)** |
| **Serialización AST** | **`tests/unit/test_ast_serialization.py`** | ❌ **NO EXISTE (P1)** |

Además existe `tests/test_semantico.py` (41 tests) que cubre el análisis semántico S1
de forma integral (variables no declaradas, tipos incompatibles, redefinición, etc.).

---

## 4. PRIORIZACIÓN (P0-P3)

| Prio | Brecha | Evidencia | Sub-etapa |
|---|---|---|---|
| **P0** | Hindley-Milner (algoritmo W: TVar, unificación, occurs check) + `ERR_SEM_TYPE_AMBIGUOUS` + `tests/unit/test_type_inference.py` | Manual 2 §8.2; `semantic_types.py` L42+ (dirigida por sintaxis); sin TVar en nativo | B2 |
| **P1** | `tests/unit/test_ast_serialization.py` (Manual 2 §12: serialización/deserialización `.syn.json`) | Manual 2 §12; `compilador/canonical.py` (serializador existente sin test unitario dedicado) | B2 |
| **P2** | Revisión de paridad: (a) numeración de errores `errores.syn` vs `diagnostics.syn` (canónica manda, patrón tokens.syn FASE A); (b) cobertura del semántico S1 (medir con coverage en B2); (c) modularización de `analizador_semantico.syn` (872 líneas — evaluar, patrón D-9 FASE A); (d) mensajes 6 idiomas vs 4 en errores nativos | — | B3 |
| **P3** | Sin brechas P3 identificadas (el resto del checklist Fase 2 está implementado) | — | — |

---

## 5. ESTADO DE LA INTEGRACIÓN (VIVO vs código muerto)

A diferencia del frontend pre-FASE A (código muerto reescrito por el espejo `_P_*`),
el análisis semántico nativo es **código VIVO en el runtime S2/S3**:

- `nucleo/principal.syn` incluye los 4 módulos en `_files[]` del unity build (L65:
  `tabla_simbolos.syn`, `analizador_semantico.syn`, `lifetimes.syn`, `memoria.syn`).
- El flatten F8 (principal.syn L224-370) aplana el AST tipado a `SemNodo[]` plano
  (estructura del Manual 2 §7.3) y **llama `analizar(&_sem_est)`** (L366-370).
- No existe espejo `_G_*` del semántico: S2/S3 ejecutan el análisis nativo real, y el
  S1 (Python) debe mantener **paridad de comportamiento** (no de bytes).

Esto implica que la brecha HM (2.4) debe resolverse en **ambos frontends** con paridad
semántica (S1 `_inferir_tipo` → algoritmo W; nativo `analizar_expr`/builtins →
unificación), verificando la suite de la Fase 2 (67 tests existentes) + los nuevos
tests del Manual 2 §12.

---

## 6. DEUDA Y REGISTRO

Sin deuda nueva que no esté ya registrada: la brecha HM (2.4) y los tests faltantes del
Manual 2 §12 son el **contenido propio de la Fase 2** (no deuda diferida). El checklist
2.1-2.6 queda actualizado en la bitácora con su estado real (5 ✅ de facto + 2.4 ⚠️ P0).

---

## 7. REFERENCIAS

- `docs/manuales/MANUAL 2.md` §8 (3 fases, HM, ADT), §9 (ownership/borrowing/lifetimes),
  §10 (taxonomía ERR_*), §12 (pruebas obligatorias).
- `docs/AUDITORIA_ALINEACION_MANUALES.md` — checklist 2.1-2.6 (bitácora).
- `ROADMAP.md` — Fase 2 (tabla de símbolos y análisis semántico; criterios de aceptación).
- `docs/reportes/FASE_A.md` y `FASE_A_A1.md` — precedentes de inventario de brechas.
