# Expediente de alineación m7_s73_restauracion

base: bf90262  # commit sobre el que se leyó el manual
cambio_hash: 2fee9f2fa1cabff7

> ME m7_s73_restauracion: cierre de H-R171-1 — restauración de M7 §7.3
> "Pruebas de Privacidad y Seguridad" con el texto EXACTO pre-154a544
> (apéndice al final del manual, Nota de restauración 2026-10-01) + re-anclaje
> de la cabecera de opensyn/permisos.syn L3 al ancla ORIGINAL
> `cumple Manual 7 §7.3` (texto exacto de fef314b) preservando las anclas
> §1.1 del mapa. Cadena de causa: fef314b (ME-5/ME-6) citaba §7.3 existente →
> 154a544 (v8.2.0) eliminó el capítulo 7 → d040500 (R149) re-ancló a §1.1
> (correcto por gates; el test quedó atrás) → el oráculo R6
> (test_permisos_cita_r6, L324) quedó reclamando la sección fantasma.
> Precedente: restauro_bucle_validacion (b1ac1c2) — manual→test/código.
> Plan: docs/plan_ME_m7_s73_restauracion.md.

## opensyn/permisos.syn
- manual: 7
  seccion: 7.3
  cita: "**Cero telemetría:** Verificado con monitoreo de red (sin conexiones salientes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/permisos.syn:3
  oraculo: tests/integration/test_permisos_opensyn.py
- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/permisos.syn:3
  oraculo: tests/integration/test_permisos_opensyn.py
- manual: 7
  seccion: 1.1
  cita: "OpenSyn es el **asistente de inteligencia artificial local** del ecosistema Synapse."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/permisos.syn:4
  oraculo: tests/integration/test_permisos_opensyn.py
