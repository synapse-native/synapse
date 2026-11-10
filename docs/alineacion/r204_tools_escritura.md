# Expediente de alineación r204_tools_escritura

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 24a7c2c76d9873d2

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/principal.syn
- manual: 7
  seccion: 2.1
  cita: "Se ejecuta en segundo plano y se comunica con el LSP mediante un socket local."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:21
  oraculo: tests/integration/test_herramientas_escritura.py

- manual: 7
  seccion: 2.3
  cita: "El nodo AST actual (función, estructura, bloque, etc.)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:1007
  oraculo: tests/integration/test_herramientas_escritura.py

- manual: 7
  seccion: 4.2
  cita: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:463
  oraculo: tests/integration/test_herramientas_escritura.py

- manual: 7
  seccion: 7.3
  cita: "**Nota de restauración (2026-10-01):** Sección restaurada textualmente por decisión del Arquitecto (Opción A, cierre de H-R171-1) tras su eliminación involuntaria en la revisión de manuales v8.2.0 (commit 154a544); con ella, la cita `cumple Manual 7 §7.3` del oráculo R6 (tests/integration/test_permisos_opensyn.py, TestCitasCumpleManual::test_permisos_cita_r6) vuelve a resolver contra una sección real — tercera víctima de la truncación v8.2.0 en repararse (tras §5.1/R119 y §6.3/restauro_bucle_validacion)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:1067
  oraculo: tests/integration/test_herramientas_escritura.py

## opensyn/herramientas.syn
- manual: 7
  seccion: 1.1
  cita: "**Completamente local:** Los modelos se descargan y ejecutan en el hardware del usuario. No hay dependencia de la nube."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/herramientas.syn:3
  oraculo: tests/integration/test_herramientas_escritura.py

- manual: 7
  seccion: 2.3
  cita: "El nodo AST actual (función, estructura, bloque, etc.)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/herramientas.syn:4
  oraculo: tests/integration/test_herramientas_escritura.py

- manual: 7
  seccion: 7.3
  cita: "**Nota de restauración (2026-10-01):** Sección restaurada textualmente por decisión del Arquitecto (Opción A, cierre de H-R171-1) tras su eliminación involuntaria en la revisión de manuales v8.2.0 (commit 154a544); con ella, la cita `cumple Manual 7 §7.3` del oráculo R6 (tests/integration/test_permisos_opensyn.py, TestCitasCumpleManual::test_permisos_cita_r6) vuelve a resolver contra una sección real — tercera víctima de la truncación v8.2.0 en repararse (tras §5.1/R119 y §6.3/restauro_bucle_validacion)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/herramientas.syn:5
  oraculo: tests/integration/test_herramientas_escritura.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/herramientas.syn:6
  oraculo: tests/integration/test_herramientas_escritura.py

## opensyn/permisos.syn
- manual: 7
  seccion: 1.1
  cita: "**Completamente local:** Los modelos se descargan y ejecutan en el hardware del usuario. No hay dependencia de la nube."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/permisos.syn:4
  oraculo: tests/integration/test_permisos_opensyn.py

- manual: 7
  seccion: 7.3
  cita: "**Nota de restauración (2026-10-01):** Sección restaurada textualmente por decisión del Arquitecto (Opción A, cierre de H-R171-1) tras su eliminación involuntaria en la revisión de manuales v8.2.0 (commit 154a544); con ella, la cita `cumple Manual 7 §7.3` del oráculo R6 (tests/integration/test_permisos_opensyn.py, TestCitasCumpleManual::test_permisos_cita_r6) vuelve a resolver contra una sección real — tercera víctima de la truncación v8.2.0 en repararse (tras §5.1/R119 y §6.3/restauro_bucle_validacion)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/permisos.syn:3
  oraculo: tests/integration/test_permisos_opensyn.py
