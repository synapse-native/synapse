# REPORTE FASE A — ETAPA A2.4: Cierre de deuda `es_mapeado`/struct-Tensor S1

> Micro-entregable A2.4 de la FASE A (plan: `docs/FASE_A_PLAN.md`).
> Fuente de verdad: `docs/AUDITORIA_ALINEACION_MANUALES.md` (deuda D-F1 / D-7; nota A2.3 L227).
> Fecha: 2026-08-06. Estado: **COMPLETADA**.
> Manuales referenciados: Manual 8 (tensor/Tensor, codegen C, lifetimes); Manual 9 §9.1
> (bootstrap S1→S2→S3) y §9.7 (determinismo diff 0).

---

## REPORTE DE MICRO-ENTREGABLE

```
--- REPORTE DE MICRO-ENTREGABLE ---
TAREA: FASE A - Etapa A2.4 — Cierre de la deuda `es_mapeado`/struct-Tensor S1 que bloqueaba
       el E2E S1 skip de A2.3 (test_e2e_s1_runtime en tests/test_a23_parity.py).
FASE: FASE A (migracion frontend embebido -> frontend nativo) - Etapa A2.4 (cierre A2.3).
MANUAL REFERENCIADO: Manual 8 (tensor->Tensor; lifetimes pool_free sobre datos mapeados);
      Manual 9 §9.1/§9.7 (bootstrap determinismo S1->S2->S3).
HASH COMMIT: **198707d** (tramo F1.3 — D-7 struct-Tensor es_mapeado incluido en el tramo; resuelto por el verificador de alineación).
COMPILACION: nucleo/generator.syn (unity) NO afectado (S2/S3 nativo ya emitia es_mapeado
      via generator.c:2501). S1 Python (compilador/generator/generator.py _emitir_encabezado)
      es el unico emisor con la Divergencia. principal.syn _files[] L58 (unity) no incluye
      tests/integration/_synapse_shared.h (header de test, no de build).
TESTS: tests/test_a23_parity.py — 7 passed (0 skipped) [antes 6+1skip]. Paridad red:
      tests/test_codegen_embebido_d_f1d.py + tests/native_lexer_paridad.py = 13 passed (0 regresiones).
COBERTURA: n/a (sin cambio de comportamiento de codegen, solo field anadido a struct).
MODIFICACIONES DE TESTS: tests/test_a23_parity.py — se levanta el pytest.skip(...) en
      test_e2e_s1_runtime (ya no aplica el bug); se endurece a hard assertion (returncode==0 + salida).
      tests/integration/_synapse_shared.h — alineacion canonica (no cambia comportamiento).
MODULARIZACION: N/A (deuda S1-Python, no S2 nativo; generator.syn/generador/*.syn inalterados).
RIESGOS: (1) el fix es S1-Python solo -> NO afecta S2/S3 ni el bootstrap diff 0 (verificado);
      (2) el E2E S1 ahora compila y ejecuta `15/hola/2` (paridad S1<->S2<->S3 confirmada);
      (3) la dualidad generator.py (S1) vs generator.c:2501 (nativo S2/S3) queda alineada
      (ambos emiten `int es_mapeado;`).
PROXIMO PASO: A3 (conmutacion runtime). Ingeniero Jefe: A3.1 gateado `--nativo-frontend`
      (flag de rollback conserva _P_* activo por defecto hasta validar el nativo end-to-end).
--- FIN ---
```

---

## 1. RESUMEN EJECUTIVO

La Etapa A2.4 cierra la **deuda `es_mapeado`/struct-Tensor S1** documentada como bloquete del
E2E S1 en A2.3 (`FASE_A_A2_3.md` L36, bitácora A2.3 L227). El runtime S1 (`main.py`, vía
`pipeline.py`) compila el `.c` generado enlazando `synapse_rt.c` (que **sí** define `Tensor`
con `es_mapeado` en `synapse_rt_types.h:14`) — pero el **typedef `Tensor` emitido por el
GeneradorC S1** (`generator.py` `_emitir_encabezado`) **no incluía** `es_mapeado`. Como el
codegen de lifetimes S1 (`emit_declarations.py:430`) emite `if (!{var}.es_mapeado)`, el
compilador GCC del E2E S1 fallaba con `'Tensor' has no member named 'es_mapeado'`, lo que
provocaba el `pytest.skip` en `test_e2e_s1_runtime`.

**Fix (alineación canónica):** añadido `int es_mapeado;` al typedef `Tensor` emitido por
`generator.py:425-428` (S1 Python) y a `tests/integration/_synapse_shared.h:21` (header de test
estático), coincidiendo exactamente con el canónico `synapse_rt_types.h:14` y con
`nucleo/generator.c:2501` (nativo S2/S3, ya correcto).

## 2. ¿Por qué es seguro?

- `generator.py` es **S1-Python exclusivamente** (el GeneradorC usado por `main.py` para
  `synapse_stage1.exe`). El nativo `nucleo/generator.syn` / `generator.c` (S2/S3) ya emitía
  `es_mapeado` en su typedef (L2501) — por lo que el binario S2/S3 es idéntico.
- Por tanto el criterio de la Etapa A2.3 (`bootstrap-full` S1→S2→S3, **diff 0 bytes**) se
  mantiene: el cambio no toca el nativo S2/S3 ni `principal.syn`.
- El cambio es **aditivo** (un field más en un `struct` que el canonical ya tenía).

## 3. Evidencia

| Verificación | Antes | Después |
|---|---|---|
| `tests/test_a23_parity.py` | 6 passed, 1 skipped | **7 passed, 0 skipped** |
| `test_codegen_embebido_d_f1d.py` | 8 passed | **8 passed** (sin regresión) |
| `tests/native_lexer_paridad.py` | 5 passed | **5 passed** (sin regresión) |
| `build.bat bootstrap-full` | diff 0 | **diff 0 bytes (S2==S3 byte-identical)** |
| `test_e2e_s1_runtime` (E2E S1) | skip (`es_mapeado`) | **PASS → salida `15/hola/2`** |

La paridad end-to-end S1↔S2↔S3 sobre el fixture (`tensor(2,3)`, `nulo`, `let`, `débil`) queda
cerrada: S1 (`main.py`), S2 y S3 producen el mismo `.c` y ejecutan `15/hola/2`.

## 4. Archivos modificados

- `compilador/generator/generator.py` — `_emitir_encabezado`: typedef `Tensor` += `int es_mapeado;`
  (alineado a `synapse_rt_types.h:14`).
- `tests/integration/_synapse_shared.h` — typedef `Tensor` += `int es_mapeado;` (consistencia).
- `tests/test_a23_parity.py` — quitado `pytest.skip` en `test_e2e_s1_runtime`; endurecida a
  hard assertion; docstring actualizado.

## 5. Próximo paso

A3.1 (gateado `--nativo-frontend`): añadir flag CLI, atenuar el hook de `generator.syn:4021-4022`
que intercambia el frontend nativo por `_P_*`, y validar el camino nativo con el flag sin tocar
el bootstrap por defecto. Ver plan en `docs/FASE_A_PLAN.md` §3 (A3) y bitácora A2.3 L227.
