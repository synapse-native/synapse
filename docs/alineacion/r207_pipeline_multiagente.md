# Expediente de alineación r207_pipeline_multiagente

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 15b96b3c8f8fe172

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/grafo_conocimiento.syn
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/grafo_conocimiento.syn:632
  oraculo: tests/opensyn/test_grafo_comportamiento.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/grafo_conocimiento.syn:7
  oraculo: tests/opensyn/test_grafo_comportamiento.py

## opensyn/pipeline_multiagente.syn
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/pipeline_multiagente.syn:4
  oraculo: tests/opensyn/test_pipeline_multiagente_comportamiento.py
