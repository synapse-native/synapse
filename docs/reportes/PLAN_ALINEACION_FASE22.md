# PLAN DE ATAQUE — ALINEACIÓN COMPLETA FASE 22 (Syquex) A LOS MANUALES

**Propósito:** llevar Fase 22 de "SUBSET funcional" a "100% alineada con Manual 3 (y 1/2/4/6 según corresponda)", cerrando los hallazgos F1–F9 de la evaluación y los tests obligatorios del Manual 3 §13.
**Ejecuta:** Este documento NO se ejecuta aquí.
**Criterio de aceptación global:** `python auditoria/verificar_alineacion.py` → 0 brechas; regresión F22 verde; tests Manual 3 §13 → 100% pass; paridad `.syn`/`.syq` sobre el subset COMPLETO del manual.

---

## 0. PREÁMBULO DE GOBERNANZA (obligatorio por ME)
Para cada micro-entregable (ME) el agente ejecutor DEBE:
1. `python auditoria/registrar_lectura.py --pendientes` y leer las secciones listadas en `docs/mapa_manuales.md`.
2. `python auditoria/registrar_lectura.py --registrar --archivos "<rutas>" --cita "Manual N §S" --puntos "<requisitos>"`.
3. Codificar, luego validar: build del frontend (`scripts/build_syquex_frontend.py`), `pytest tests/syquex -v`, `pytest tests/integration -k syq`, y `python auditoria/verificar_alineacion.py`.
4. Entregar reporte canónico + fila en `docs/AUDITORIA_ALINEACION_MANUALES.md` + actualizar `MEMORIA_PROYECTO.md`.
**Decisiones que REQUIEREN al Arquitecto (regla: DETENTE Y PREGUNTA):** ver §5.

---

## 1. DESACOPLAMIENTO Y CONTRATO (prerrequisito, bajo riesgo)

### ME-1: Mover constantes 54–58 a fuente de verdad (F7)
- **Manual:** 6 §1.2 (única fuente de verdad = `nucleo/parser_constantes.syn`).
- **Archivos:** `nucleo/parser_constantes.syn` (añadir `NODO_INTENTO=54`, `NODO_LISTA_LIT=55`, `NODO_MAPA_LIT=56`, `NODO_PARA_EN=57`, `NODO_BLOQUE_SQ=58`), `syquex/expr.syn` (eliminar las definiciones locales líneas 17–21; ya importa `parser_constantes`), `syquex/traductor.syn` (confirmar que las usa vía import, no por concatenación).
- **Pasos:** definir en `parser_constantes.syn`; borrar duplicados en `expr.syn`; reconstruir frontend; compilar `tests/unit/test_syquex_lexer.py`/`test_syquex_parser.py`/`test_syquex_traductor.py`.
- **Verificación:** build sin `expr.syn` en el unity sigue compilando el traductor (ya no depende de concatenación). `verificar_alineacion` 0 brechas.
- **Riesgo:** el `build_syquex_frontend.py:27-36` concatena; tras este ME la concatenación es inocua (dedup primera-gana).

### ME-2: Corregir el contrato ABI v1 documentado (F8)
- **Manual:** 6 §1.2.
- **Archivos:** `nucleo/ast_abi.syn` (líneas 23–28), `compilador/ast_nodes.py`, `syquex/syq_json.syn` (12–16), `compilador/puente_canonico.py` (11–14).
- **Pasos:** decidir la FORMA REAL del SemNodo plano (hoy 10 campos `{tipo,linea,columna,valor_int,hizq,hder,herm,extra,span1,span2}`). O bien (a) ampliar `ast_abi_verificar()` para validar presencia/orden de esos 10 campos en el esquema JSON, o (b) corregir el comentario de `ast_abi.syn` para que el contrato refleje la forma real y eliminar la lista de campos inexistentes (`archivo/owner_id/scope_id/es_owned/...` que `ast_nodes.py` no tiene). Recomendado: (b) + self-check de campos.
- **Verificación:** `ast_abi_verificar()` congruente con el esquema emitido; 0 brechas.

---

## 2. CIERRE DE BRECHAS DE COMPILACIÓN (features del manual que hoy fallan)

### ME-3: `&T` en FFI → mapear NODO_PUNTERO en el puente (F2)
- **Manual:** 3 §9.1/§9.3 (ejemplo `externo funcion strlen(s: &texto)`), 2 §7.3 (NODO_PUNTERO=36 existe en S1).
- **Archivos:** `compilador/puente_canonico.py` (añadir rama `t == 36` → `ExprObtenerDireccion`/nodo puntero tipado del S1, y agregar 36 a `NOMBRE_NODO`), `tests/syquex/test_ffi_marshaling.py` (cubrir `&texto`).
- **Pasos:** inspeccionar cómo S1 mapea `&` (buscar en `compilador/ast_nodes.py` y `compilador/generator/`) y producir el nodo equivalente; asegurar que el marshaling zero-copy (§9.3) se preserve en el codegen compartido.
- **Verificación:** `tests/syquex/test_ffi_marshaling.py` con caso `&texto` rc=0 y ejecución correcta. Este ME desbloquea el ejemplo canónico de FFI.

### ME-4: Recepción de canal `c ->` (F3)
- **Manual:** 3 §8.1.
- **Archivos:** `syquex/expr.syn` (manejar `T_FLECHA` como operador postfijo de recepción dentro de `escuchar`, creando `NODO_RECIBIR_CANAL`), `syquex/parser.syn` (no consumir `->` como flecha de retorno en contexto de recepción), `compilador/puente_canonico.py` (mapear `t == 43` NODO_RECIBIR_CANAL → nodo de recepción S1), `tests/syquex/test_concurrency.py`.
- **Pasos:** definir sintaxis de recepción compatible con S1 (revisar cómo S1 parsea `recibir`/canal); emitir el nodo canónico; mapear en puente.
- **Verificación:** programa Manual 3 §8.1 (`escuchar c: let m = c ->`) compila y ejecuta; `test_concurrency.py` 0 deadlocks.

### ME-5: Asignación indexada `a[i] = x` (F4)
- **Manual:** 3 §3 L126.
- **Archivos:** `compilador/puente_canonico.py` (reemplazar el `PuenteError` de `t==29` como LHS por `AsignacionIndice` tipado del S1, líneas 237–240), backend S1 (`compilador/generator/`) si no existe asignación indexada.
- **Verificación:** `test_syquex_r90.py`/fixture con `a[i] = v` rc=0.

### ME-6: Literales lista/mapa (F1 — NODO_LISTA_LIT 55 / MAPA_LIT 56)
- **Manual:** 3 §5.2, §11.1, §12 (lib/lista, lib/mapa son Fase 24).
- **DECISIÓN ARQUITECTO (§5):** (a) backend nativo mínimo en S1 para `Lista<T>`/`Mapa<K,V>` (array + hash), o (b) desugar en el puente a llamadas de la std lib de Fase 24 (retrasado). Para "alineación completa" se requiere (a) o (b) funcional.
- **Archivos (vía a):** `compilador/puente_canonico.py` (mapear 55/56 a nodos de colección del S1), `compilador/generator/` (emision C de listas/mapas), `tests/syquex/test_structs.py` o `test_listas.py`.
- **Verificación:** `[1,2,3]` y `{"a":1}` compilan y ejecutan; acceso `lst[0]`, `m["a"]`.

### ME-7: `para x en ...` (F1 — NODO_PARA_EN 57)
- **Manual:** 3 §3 L133.
- **DECISIÓN ARQUITECTO (§5):** desugar en el puente a `mientras` con protocolo iterador sobre la colección (requiere ME-6), o implementar `NODO_PARA_EN` en S1.
- **Archivos:** `compilador/puente_canonico.py` (transformar 57 → bucle), `tests/syquex/test_concurrency.py` o `test_bucles.py`.
- **Verificación:** `para i en [1,2,3]: ...` compila y ejecuta.

### ME-8: `intentar/atrapar` (F1 — NODO_INTENTO 54)
- **Manual:** 3 §7.3.
- **DECISIÓN ARQUITECTO (§5):** Syquex no tiene excepciones; implementar como `try/catch` en C sobre la runtime de panic de Synapse (wrapper), o desugar a `Resultado` + `atrapar` como `si es_err`. 
- **Archivos:** `compilador/puente_canonico.py` (mapear 54), `compilador/generator/` (emision try/catch o desugar), `tests/syquex/test_result.py`.
- **Verificación:** `intentar: ... atrapar e: ...` compila y el `atrapar` captura panic/err; `test_result.py` propagación `?` correcta.

---

## 3. CORRECCIÓN DE LÓGICA OOP (F5, F6)

### ME-9: Detección de métodos sin `partition("_")` (F5)
- **Manual:** 3 §6.1/§6.3, 6 §1.3.
- **Archivos:** `syquex/parser.syn` + `syquex/traductor.syn` (marcar método con campo dedicado, p.ej. `valor_int`/slot de decoración explícita en vez de nombre `Struct_metodo`), `compilador/puente_canonico.py` (`_build_contexto` lee el marcador, no `partition("_")`).
- **Pasos:** definir convención de marcador (ej. bit en `valor_int` o campo `ptr_extra` del nodo de llamada); poblar en parser/traductor; el puente usa el marcador para el lowering y para registrar `_struct_metodos`.
- **Verificación:** funciones libres con `_` y structs cuyo nombre contiene `_` NO se confunden; `test_structs.py` con struct `Mi_Struct` y método.

### ME-10: Resolución de tipo de receptor completa (F6)
- **Manual:** 3 §6.2/§6.3.
- **Archivos:** `compilador/puente_canonico.py` (`_tipo_objeto` y `_build_contexto`): poblar `_var_tipo` desde (1) parámetros de función (escaneo de firmas estilo D-2 de S1), (2) retornos de función/llamadas, además de `let` directo; soportar receptor `a.b` (resolver tipo del campo si es struct).
- **Verificación:** `param.metodo()`, `x = factory(); x.metodo()`, `a.b.metodo()` compilan cuando el tipo es resoluble; `test_structs.py` cubre estos tres casos.

---

## 4. GLOBALES MUTABLES (F9)

### ME-11: Verificar y corregir `variable` global mutable
- **Manual:** 3 §3 L64/74 (variable a nivel de módulo), 2 §7 (modelo de bindings).
- **Archivos:** `compilador/generator/` (almacenamiento mutable de globals si S1 lo trata como inmutable), `tests/integration/test_syquex_r92_variable.py` (ampliar a escritura+lectura en otro ámbito y verificar mutación real).
- **Pasos:** ejecutar el fixture y comprobar que una escritura posterior a `variable GLOBAL` es visible; si no, implementar almacenamiento mutable en el backend compartido.
- **Verificación:** test de ejecución confirma mutabilidad real (no solo rc=0).

---

## 5. DECISIONES QUE REQUIEREN AL ARQUITECTO (no avanzar sin respuesta)
- **D1 (ME-6/7):** ¿listas/mapas/for-en se implementan como backend nativo en S1 (opción a) o se desugaran a la std lib de Fase 24 (opción b, retrasado)? Impacta el orden del roadmap y la frontera F22/F24.
- **D2 (ME-8):** ¿`intentar/atrapar` como try/catch en C sobre panic runtime, o desugar a `Resultado`?
- **D3 (ME-11):** ¿Se modifica el backend S1 para globals mutables de Syquex (podría afectar semántica de Synapse)? Confirmar que no rompe la inmutabilidad canónica de M2.

---

## 6. COBERTURA DE TESTS OBLIGATORIOS (Manual 3 §13) Y PARIDAD
### ME-12: Crear tests obligatorios ausentes
- **Manual:** 3 §13.
- **Archivos a crear:** `tests/syquex/test_structs.py`, `test_result.py`, `test_concurrency.py`, `test_ffi.py`, `test_export.py` (hoy NO existen; `tests/syquex/` solo tiene tests de memoria de Fase 23 + lexer/parser/traductor/r89/r90).
- **Criterios:** 100% pass; `test_ffi` usa `&` (ME-3); `test_concurrency` usa `escuchar c ->` (ME-4); `test_structs` cubre F5/F6; `test_result` cubre `?` y `intentar` (ME-8); `test_export` valida bindings `@export`.

### ME-13: Paridad real `.syn`/`.syq`
- **Manual:** 6 §1.2, ROADMAP F22 ("mismo AST canónico").
- **Archivos:** ampliar `tests/integration/test_paridad_syn_syq.py` y `tests/fixtures/paridad/*.syn|*.syq` a features COMPLETAS (listas, mapas, for-en, intentar, `&` FFI, métodos sobre parámetros).
- **Verificación:** dumps idénticos para cada par tras cerrar F1–F9.

---

## 7. ORDEN DE EJECUCIÓN RECOMENDADO
1. ME-1 → ME-2 (prerrequisitos, sin riesgo).
2. ME-3 (FFI `&`, pequeño, alto valor) → ME-9 → ME-10 (OOP) → ME-4 (canal) → ME-5 (asignación indexada).
3. D1/D2/D3 resueltos por Arquitecto → ME-6 → ME-7 → ME-8 (features grandes, tocan backend S1).
4. ME-11 (globales) tras D3.
5. ME-12 → ME-13 (tests + paridad).
6. Gates finales: `verificar_alineacion.py` 0 brechas + regresión F22 + reporte por ME + bitácora + memoria.

---

## 8. RIESGOS TRANSVERSALES
- **Cross-phase:** ME-6/7/8/11 tocan el backend S1 compartido (`compilador/generator/`, `nucleo/*.syn`) → riesgo de regresión en Synapse (.syn). Mitigación: regresión S1 completa en cada ME.
- **Falsos positivos de paridad:** `test_paridad_syn_syq.py` hoy solo cubre subset mínimo → da confianza falsa; no cerrar F22 hasta ME-13 con features completas.
- **Silent truncation:** `syq_main.syn:47-56` lee archivos a buffer de 1 MB sin error si excede; añadir detección de truncamiento (fuera de alcance crítico, pero recomendado en ME-1 o ME-12).
