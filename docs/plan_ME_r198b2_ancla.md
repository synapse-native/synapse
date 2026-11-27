# PLAN ME r198b2_ancla — cierre H-R198b1-2 (ancla MTS en desugar PARA_EN)

**Fecha:** 2026-10-28 · **Base:** 7b9ed2e · **Origen:** H-R198b1-2 (plan maestro),
hallazgo de R198b1: `test_paridad_nodos::test_emision_s1_cita_los_nodos_canonicos`
fallo PREEXISTENTE en HEAD (verificado por aislamiento con stash).

## TDD (dirección del Arquitecto, plan maestro): el test ya está RED

```markdown
requisito: Manual 2 §12
texto: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
implementacion: comentario ancla MTS `# cumple Manual 2 §12` en el desugar REAL de NODO_PARA_EN(57) (puente_canonico.py::_nodo_para_en) — la perspectiva es de documentación: el test paridad OBL-PAR-R1d (test_emision_s1_cita_los_nodos_canonicos, anti-ley de la emisión) exige `cumple Manual 2 §12` a nivel de ARCHIVO y HEAD 7b9ed2e tenía la brecha; el test exige también `NODO_PARA_EN(57)` (ya presente en L72)
oraculo: tests/auditoria/test_paridad_nodos.py
```

Requisito del test: test_emision_s1_cita_los_nodos_canonicos (OBL-PAR-R1d,
anti-regresión de emisión S1).

**texto (literal del test, tests/auditoria/test_paridad_nodos.py:139-155):**
"el desglose S1 (puente_canonico.py) referencia NODO_PARA_EN con su ancla de
manual — el punto donde el compilador Python consume el nodo canonico 57
(desugar a SentenciaMientras) no divergio de la ley."
assert `"NODO_PARA_EN(57)" in puente` + assert `"cumple Manual 2 §12" in puente`
("puente_canonico.py sin cita de manual en el desugar de PARA_EN").

**texto (Manual 2 §12, literal):** "PRUEBAS OBLIGATORIAS PARA ESTA ETAPA —
Contratos requiere/garantiza | pytest tests/integration/test_contracts.py |
100% pass."

**nota de aislamiento (R198b1):** el test exige la ancla en TODO
`puente_canonico.py` (leído completo); la brecha era solo la falta de la ancla
`cumple Manual 2 §12` — `NODO_PARA_EN(57)` YA está en la línea 72 (desugar de
r197). El archivo está alineado y el test pedía la ancla: se añade el comentario
MTS (no se modifica el test, inmutable).

## implementacion

- `compilador/puente_canonico.py::_nodo_para_en` (desugar real de
  NODO_PARA_EN(57), líneas ~597-620): añadir comentario ancla
  `# cumple Manual 2 §12` junto al comentario MTS existente
  (`# cumple Manual 3 §3 (H-R153-1)`), citando sección manual real:
  el desugar produce el nodo del pipeline cuyos tests son obligatorios de la
  etapa (M2 §12) —/documenta el vínculo, no cambia códigos generados/.

**oraculo (MTO, GREEN esperado):**
`pytest tests/auditoria/test_paridad_nodos.py -v` → 4/4 pass (RED→GREEN).
Regresión: `pytest tests/auditoria/ -q` sin fallos NUEVOS; cero diff binario
del nodo generado (el comentario es documentación, no emisión).

## gates (4b y cierre)

- `python auditoria/alineacion.py --leer --me r198b2_ancla` (HECHO, sello 0
  archivos base 7b9ed2e) → `--nuevo` (expediente con citas literales) →
  codificar → `--verificar --me r198b2_ancla`
- `python auditoria/contrastar.py --plan docs/plan_ME_r198b2_ancla.md` RC=0
- `python auditoria/verificar_alineacion.py` SIN BRECHAS
