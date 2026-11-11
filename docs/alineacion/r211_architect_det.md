# Expediente de alineación r211_architect_det

base: 32139ff  # commit sobre el que se leyó el manual
cambio_hash: 6ac72a2f8744254a

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/architect_det.syn
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/architect_det.syn:3
  oraculo: tests/opensyn/test_architect_det_comportamiento.py
- manual: 6
  seccion: 1.1
  cita: "Tanto Synapse como Syquex traducen su código fuente a esta representación intermedia. El backend (análisis semántico, generación de código, optimizaciones) es **compartido** y solo opera sobre `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/architect_det.syn:196
  oraculo: tests/opensyn/test_architect_det_comportamiento.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: opensyn/architect_det.syn:4
  oraculo: tests/opensyn/test_architect_det_comportamiento.py
