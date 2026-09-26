# Verificación ME 33_1_paridad_nodos — H-R153-NODE

**Fecha:** 2026-09-26
**Plan:** docs/plan_ME_33_1_paridad_nodos.md
**Oráculo:** tests/auditoria/test_paridad_nodos.py (4/4 GREEN, sin skips)

## R1 — Manual 2 §7.2: tabla corregida + filas 57/59 — Manual 2 §7.2 — CUMPLE
- Implementación: docs/manuales/MANUAL 2.md §7.2 con autorización explícita
  del Arquitecto (sesión 2026-09-26): filas NODO_PARA_EN=57 y NODO_METODO=59
  añadidas; 13 valores incorrectos corregidos contra parser_constantes.syn
  (fuente única que genera ast_nodos.h); nodos faltantes documentados
  (EXPR=6, IDENTIFICADOR=8, ACCESO_CAMPO=31, INTENTO=54, LISTA_LIT=55,
  MAPA_LIT=56, BLOQUE_SQ=58).
- Evidencia: oráculo OBL-PAR-R1a + OBL-PAR-R1b GREEN (comparación programática
  tabla ↔ nativo ↔ header, 0 divergencias).

## R2 — Oráculo de paridad 3-vías — Manual 2 §7.2 — CUMPLE
- Implementación: tests/auditoria/test_paridad_nodos.py NUEVO: (a) filas 57/59
  con descripción en la tabla; (b) paridad tabla↔parser_constantes.syn↔
  ast_nodos.h y nativo==header; (c) índice fresco (sha256 texto utf-8, mismo
  cálculo que indice_manual.py:157) con §7.2 indexando 57/59; (d) cita del
  nodo canónico en puente_canonico.py.
- Evidencia: 4/4 GREEN; el oráculo DEMOSTRÓ su valor detectando los 13 valores
  incorrectos de la tabla heredada en su primera ejecución.

## R3 — Índice de manuales regenerado — Manual 2 §7.2 — CUMPLE
- Implementación: `python auditoria/alineacion.py --indice` tras editar el
  manual; verificar_alineacion.py SIN BRECHAS (ninguna cita del repo apuntaba
  a los valores viejos de la tabla: el cambio documental no rompió nada).
- Evidencia: gates en verde; collect-only 3099 tests, 0 errores.

## Criterios de aceptación del roadmap 33.1
- Tabla §7.2 incluye 57 y 59 con su descripción: ✓ (OBL-PAR-R1a)
- Oráculo de paridad GREEN: 0 divergencias S1↔nativo: ✓ (OBL-PAR-R1b)
- Cambio documental + guard, sin tocar emisión → bootstrap sin riesgo de
  diff binario (verificado por no-tocar fuentes de emisión en el diff).

## Hallazgos del ME
- **H-331-TABLA (RESUELTO):** la tabla §7.2 heredada tenía ~13 valores que no
  correspondían al nativo operativo (derivaba de un diseño pre-unificación
  del AST canónico). Corregida contra la fuente única; el oráculo blindará
  toda divergencia futura.
- **H-R153-NODE (RESUELTA, cierre):** pasa de DESVIACION a CUMPLE — el manual
  hoy documenta exactamente lo que el código emite.

CUMPLE
