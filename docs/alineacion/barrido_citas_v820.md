# Expediente de alineación barrido_citas_v820

base: 449db38  # commit sobre el que se leyó el manual
cambio_hash: fe5ae9a7aa1147d7

> ME barrido_citas_v820: barrido de las 39 citas `cumple Manual` sin sección
> heredadas de la v8.2.0 (154a544) — restauración textual de §4.3, §6.1, §6.2,
> §6.4, §7.2 y §8 (texto exacto pre-154a544, notas de restauración 2026-10-01)
> + re-anclaje de las 3 citas al capítulo §6 (chat.syn L3/L54 → §6.2;
> ai_orchestrator.h L146 → §2.1). Resultado: citas_muertas_repo == 0.
> Plan: docs/plan_ME_barrido_citas_v820.md.

## nucleo/ai_orchestrator.h
- manual: 7
  seccion: 2.1
  cita: "El orquestador es un proceso en C que gestiona el ciclo de vida del servidor de inferencia (`llama-server`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/ai_orchestrator.h:146
  oraculo: tests/integration/test_opensyn_integration.py

## opensyn/chat.syn
- manual: 7
  seccion: 6.2
  cita: "**Nota de restauración (2026-10-01):** Sección restaurada textualmente por decisión del Arquitecto (Opción A, ME barrido_citas_v820) tras su eliminación involuntaria en la revisión de manuales v8.2.0 (commit 154a544); con ella, la selección de modelo (`[modelo]` nombre/ruta) vuelve a tener hogar normativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/chat.syn:3
  oraculo: tests/integration/test_opensyn_integration.py
- manual: 7
  seccion: 8
  cita: "El LSP valida con `synapse check --no-emit` (compila correctamente)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/chat.syn:4
  oraculo: tests/integration/test_opensyn_integration.py
