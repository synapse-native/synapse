# Plan MTS — ME m7_s73_restauracion

> Cierre de H-R171-1 (hallazgo de R171, verificación de la suite de integración).
> Tercera víctima de la truncación v8.2.0 (commit 154a544 del 2026-09-13): el
> capítulo 7 de MANUAL 7 fue eliminado completo, incluida §7.3 "Pruebas de
> Privacidad y Seguridad". El oráculo R6 (TestCitasCumpleManual::
> test_permisos_cita_r6, tests/integration/test_permisos_opensyn.py:324) exige
> el ancla `cumple Manual 7 §7.3` en permisos.syn — ancla que EXISTIÓ desde la
> creación del archivo (fef314b, ME-5/ME-6 R6) y fue re-anclada a §1.1 por
> d040500/R149 cuando la sección quedó fantasma (correcto por los gates de la
> época, pero el test quedó atrás). Precedente: restauro_bucle_validacion
> (b1ac1c2) — la verdad vive en el manual pre-154a544, la dirección de la
> reparación es manual→test/código.

requisito: Manual 7 §7.3 (Pruebas de Privacidad y Seguridad — restauración textual del estado pre-154a544)
texto: "Cero telemetría: Verificado con monitoreo de red (sin conexiones salientes)."
implementacion: docs/manuales/MANUAL 7.md — §7.3 restaurada byte-exacta del
  estado pre-154a544 (extraído de `git show 154a544^:"docs/manuales/MANUAL 7.md"`
  L848-876: "## 7. PRUEBAS Y VALIDACIÓN" → "### 7.3." con sus 3 bullets: Cero
  telemetría, Modelos firmados SHA‑256, Sandboxing) como apéndice al final del
  manual (tras §6.3), con Nota de restauración 2026-10-01 de procedencia. Con
  ella el ancla del oráculo R6 vuelve a resolver contra una sección real.
oraculo: tests/integration/test_permisos_opensyn.py

requisito: Manual 7 §7.3 (Sandboxing — ancla grep-chequeable del código)
texto: "Sandboxing: El servidor de inferencia se ejecuta con permisos mínimos."
implementacion: opensyn/permisos.syn L3 — re-anclaje de la cabecera: se restaura
  el ancla ORIGINAL `// cumple Manual 7 §7.3: "Sandboxing: El servidor de
  inferencia se ejecuta con permisos mínimos"` (texto exacto de fef314b) y se
  PRESERVAN las anclas §1.1 existentes (L4-L5) que exigen mapa_alineacion.md.
  Sin cambios de código ejecutable (línea de comentario).
oraculo: tests/integration/test_permisos_opensyn.py

## Notas de alcance
- Tests: NINGUNO modificado — el test tenía razón (su requisito es literal del
  docstring: "Manual 7 §7.3 — 'Cero telemetría + sandboxing'") y el manual se
  repara hacia el test (misma dirección que restauro_bucle_validacion).
- docs/gobernancia/mapa_alineacion.md: entrada de permisos.syn actualizada
  ["Manual 7 §1.1"] → ["Manual 7 §1.1", "Manual 7 §7.3"] (documenta el mapa
  real del archivo; precedente R158).
- docs/manuales/.indice.json regenerado (manuales=9, secciones=298,
  oraciones citables=1315; §7.3 indexada — validar_cita_textual confirma las
  2 oraciones usadas por el expediente).
- Producción: SOLO opensyn/permisos.syn (1 línea de comentario). Los manuales
  y su índice no son producción (precedente b1ac1c2: gates "no aplica" sin
  archivos de mapa).
