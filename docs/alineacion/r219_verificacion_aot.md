# Expediente de alineación r219_verificacion_aot

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: c0a201a1ecbe7d72

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/verificacion_aot.syn
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un **árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/verificacion_aot.syn:6
  oraculo: tests/opensyn/test_verificacion_aot.py

- manual: 7
  seccion: 4.2
  cita: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/verificacion_aot.syn:3
  oraculo: tests/integration/test_verificacion_aot_e2e.py

- manual: 7
  seccion: 6.3
  cita: "**Nota de restauración (2026-09-30):** Sección restaurada textualmente por decisión del Arquitecto (Opción A, ME validation_loop_fix) tras su eliminación involuntaria en la revisión de manuales v8.2.0 (commit 154a544); con ella, las referencias internas (secciones 1 y 4.2 de este manual) y la del Manual 8 (§5.1) vuelven a resolver."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/verificacion_aot.syn:4
  oraculo: tests/integration/test_verificacion_aot_e2e.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/verificacion_aot.syn:5
  oraculo: tests/opensyn/test_verificacion_aot.py
