# Expediente de alineación r217_integracion_determinista

base: 3c726fb  # commit sobre el que se leyó el manual
cambio_hash: c5e70770a1514592

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
- manual: 7
  seccion: 2.3
  cita: "El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn. Extrae el contexto más relevante del código fuente para construir un prompt eficiente y preciso."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/architect_det.syn:5
  oraculo: tests/opensyn/test_architect_det_comportamiento.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: opensyn/architect_det.syn:4
  oraculo: tests/opensyn/test_architect_det_comportamiento.py

## opensyn/pipeline_multiagente.syn
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/pipeline_multiagente.syn:4
  oraculo: tests/opensyn/test_pipeline_multiagente_comportamiento.py
- manual: 7
  seccion: 2.3
  cita: "El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn. Extrae el contexto más relevante del código fuente para construir un prompt eficiente y preciso."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/pipeline_multiagente.syn:5
  oraculo: tests/opensyn/test_pipeline_multiagente_comportamiento.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: opensyn/pipeline_multiagente.syn:3
  oraculo: tests/opensyn/test_pipeline_multiagente.py
