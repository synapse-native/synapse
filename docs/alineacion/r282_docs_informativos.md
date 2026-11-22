# Expediente de alineación r282_docs_informativos

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: pending

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## std/texto.syn (repetición de patrón)

- manual: 1
  seccion: 7.4
  cita: "Definition of Done - versión y changelog"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/texto.syn:1
  oraculo: tests/integration/test_axon_10.py

## nucleo/principal.syn (repetición de patrón)

- manual: 1
  seccion: 7.4
  cita: "Definition of Done - versión y changelog"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1
  oraculo: tests/integration/test_axon_10.py