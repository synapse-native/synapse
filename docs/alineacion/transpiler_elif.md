# Expediente de alineación transpiler_elif

base: 0107a58  # commit sobre el que se leyó el manual
cambio_hash: 152a82c2ad565065

> ME transpiler_elif: reparación de la deuda test_control_flow_pipeline (R166/R167).
> `opensyn/transpiler.py` emitía `sino_si` (L51/L197) — token que la gramática
> no define (M2 §7.2: `condicional_si ::= "si" ... [ "sino" ":" ... ]`; alias
> T_SINO | sino | else | sinon | senao) → el .syq generado NO compilaba
> (OBL-M7-03 violado, 4 errores reproducidos). Origen: R119 L60 ("Corregido de
> `sino si` a `sino_si`") — "arreglo" de Fase 26 que invirtió la forma correcta;
> su justificación citaba Manual 7 §5.1, sección inexistente (M7 termina en §4).
> Fix: emitir "sino si" (forma canónica, paridad con transpiler.syq L92).
> Aserción test_opensyn_integration.py:120 corregida sino_si → "sino si" con
> AUTORIZACIÓN EXPLÍCITA del Arquitecto (regla 5, sesión 2026-09-30) — único
> test del repo que codificaba la desviación; contradecía a
> test_full_pipeline.py:230 (inmutable, correcto).
> Anclaje: M6 §6.2 es la sección normativa real de la transpilación
> Python → Syquex; el requisito legacy del mapa (Manual 7 entero, sin
> oraciones §-indexadas de transpilación salvo §1.1) se cubre con ancla M7 §1.1.
> Plan: docs/plan_ME_transpiler_elif.md.

## opensyn/transpiler.py
- manual: 6
  seccion: 6.2
  cita: "OpenSyn puede tomar código Python y generar Syquex equivalente, mapeando tipos dinámicos a estáticos."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/transpiler.py:51
  oraculo: tests/test_full_pipeline.py
- manual: 6
  seccion: 6.2
  cita: "Para cada nodo Python, determina su equivalente en Syquex:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/transpiler.py:197
  oraculo: tests/test_full_pipeline.py
- manual: 7
  seccion: 1.1
  cita: "**Transpilación:** Puede convertir código Python a Syquex, y código C a Synapse/Syquex."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/transpiler.py:51
  oraculo: tests/test_full_pipeline.py
