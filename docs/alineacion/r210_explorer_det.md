# Expediente de alineación r210_explorer_det

base: 12234cf  # commit sobre el que se leyó el manual
cambio_hash: 8c52618300038933

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/explorer_det.syn
- manual: 6
  seccion: 1.1
  cita: "El ecosistema Synapse se basa en un **Árbol de Sintaxis Abstracta (AST) canónico y unificado** denominado `SemNodo[]`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/explorer_det.syn:135
  oraculo: tests/opensyn/test_explorer_det_comportamiento.py

