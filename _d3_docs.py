#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_d3_docs.py — Registra el cierre de la deuda D-3 (FASE A, Etapa A5) en la
documentacion de la auditoria:
  1. docs/AUDITORIA_ALINEACION_MANUALES.md  (fila de bitacora D-3 + registro de deuda)
  2. docs/FASE_A_PLAN.md                    (Etapa A5: D-3 completada)
  3. docs/reportes/FASE_A_A5_D3.md          (reporte formal del micro-entregable)
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FILA_D3 = (
    "| 2026-08-07 | FASE A — Etapa A5: cierre de la deuda **D-3** (divergencia cosmética "
    "S1 vs S2 en la declaración de variables de struct/Tensor sin inicializador) | "
    "✅ Completado | **Bug (S2, orquestador.syn)**: para `let t: Tensor` + `t = crear_tensor(...)` "
    "el pre-pass de hoisting ME-B7 recorría el cuerpo en orden INVERSO (pila LIFO `--_hp_top`) → "
    "la AsignacionVariable `t = ...` se registraba como auto=1 ANTES que la DeclaracionVariable "
    "`t` (auto=0), el hoisting emitía `int64_t t = {0};` (tipo por defecto) y `gen_visitar_declaracion` "
    "emitía `Tensor t = ;` (sin `{0}`) → C inválido (doble declaración + sintaxis). **Fix**: "
    "(1) pre-pass → recorrido FIFO (`_hp_head`/`_hp_tail`, orden de aparición) — paridad "
    "`_collect_vars` de S1 (`for s in stmts`: primera declaración gana); (2) `gen_visitar_declaracion` "
    "sin expresión → `= {0};` (paridad `visitar_declaracion` S1). **Revisión code-reviewer aplicada**: "
    "`_hp_stack` 1024→4096 (el FIFO consume el array monótonamente: total de sentencias/función, no "
    "profundidad) + divergencia documentada (bloques anidados al final de la cola; solo afecta a código "
    "que cruza ámbito, no permitido). **E2E**: `let t: Tensor` ahora emite `Tensor t = {0};` + "
    "`t = crear_tensor(2LL, 3LL);` y ejecuta imprimiendo `2` (antes C inválido). **Tests NUEVOS** "
    "`tests/fixtures/test_d3_declaracion.syn` + 3 en `test_a23_parity.py` (S1, S2, paridad S1==S2) → "
    "**9 passed, 1 skipped** en a23; suite paridad/codegen 35 passed + core 167 passed + paridades "
    "nativas rc=0. **bootstrap S1→S2→S3 rc 0 con C idéntico S2==S3** (tras el fix y tras el hardening). "
    "Sin cambios de tests existentes (solo añadidos). Reporte: `docs/reportes/FASE_A_A5_D3.md` |"
)

# ---------------------------------------------------------------- bitacora
ruta_bitacora = "docs/AUDITORIA_ALINEACION_MANUALES.md"
with open(ruta_bitacora, encoding="utf-8") as f:
    b = f.read()

cambios = []

# 1. Insertar la fila D-3 tras la fila A5 (D-7).
ancla = "Reporte: `docs/reportes/FASE_A_A5.md` |"
if ancla in b:
    b = b.replace(ancla, ancla + "\n" + FILA_D3, 1)
    cambios.append("fila D-3 insertada en la tabla de bitacora")
else:
    print("[ERROR] ancla fila A5 (D-7) no encontrada")

# 2. Estado general: actualizar "Pendientes A5" (D-3 cerrada).
old_pend = "Pendientes A5: D-6 (`?` postfijo), D-2 (ADT genéricos), D-3 (formato Tensor), D-5 (cobertura ≥70%). D-1 (runtime rc/arc/débil) → Fase 23."
new_pend = "Pendientes A5: D-6 (`?` postfijo), D-2 (ADT genéricos), D-5 (cobertura ≥70%). **D-3 ✅ CERRADA (2026-08-07, commit pendiente: pre-pass FIFO + `= {0};`)** — ver `docs/reportes/FASE_A_A5_D3.md`. D-1 (runtime rc/arc/débil) → Fase 23."
if old_pend in b:
    b = b.replace(old_pend, new_pend)
    cambios.append("estado general: D-3 marcada cerrada")
else:
    print("[ERROR] frase 'Pendientes A5' no encontrada")

# 3. Registro de deuda: bloque D-3 -> cerrado.
old_d3 = "**D-3** (formato `Tensor t;` vs `Tensor t = {0};` S1 vs S2, cosmético): FASE A."
new_d3 = "**D-3 — ✅ CERRADA (A5, 2026-08-07)**: divergencia `Tensor t;` vs `Tensor t = {0};` S1 vs S2 — el pre-pass de hoisting S2 recorría en LIFO (asignación ganaba al `let`) y `gen_visitar_declaracion` emitía `Tensor t = ;` sin `{0}`; fix FIFO + `= {0};`, reporte `docs/reportes/FASE_A_A5_D3.md`."
if old_d3 in b:
    b = b.replace(old_d3, new_d3, 1)
    cambios.append("REGISTRO DE DEUDA: D-3 marcada cerrada")
else:
    print("[ERROR] bloque D-3 del REGISTRO DE DEUDA no encontrado")

with open(ruta_bitacora, "w", encoding="utf-8", newline="") as f:
    f.write(b)

# ---------------------------------------------------------------- FASE_A_PLAN
ruta_plan = "docs/FASE_A_PLAN.md"
with open(ruta_plan, encoding="utf-8") as f:
    p = f.read()

old_plan = "- **D-3** (divergencia cosmética `Tensor t;` vs `Tensor t = {0};`): unificar emisión."
new_plan = "- **D-3 ✅ CERRADA (2026-08-07)**: divergencia `Tensor t;` vs `Tensor t = {0};` — fix pre-pass FIFO + `= {0};` en `gen_visitar_declaracion`; reporte `docs/reportes/FASE_A_A5_D3.md`."
if old_plan in p:
    p = p.replace(old_plan, new_plan, 1)
    cambios.append("FASE_A_PLAN: D-3 marcada cerrada")
else:
    print("[ERROR] bloque D-3 del FASE_A_PLAN no encontrado")

with open(ruta_plan, "w", encoding="utf-8", newline="") as f:
    f.write(p)

print("=== _d3_docs.py ===")
for c in cambios:
    print("[OK]", c)
print(f"Total: {len(cambios)}")
