# Expediente de alineación r222b_wrappers_regression

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 74f53ae26613e627

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/lsp_v3.syn
- manual: 8
  seccion: 1.1
  cita: "El LSP es **nativo**, **sin telemetría** y **sin dependencias externas** (excepto el binario `synapse.exe` para compilar y analizar código)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:1106
  oraculo: tests/auditoria/test_oraculos_r222b_wrappers.py

## opensyn/router.syn
- manual: 7
  seccion: 2.4
  cita: "El router está escrito en Synapse y actúa como el cerebro de alto nivel de OpenSyn."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/router.syn:26
  oraculo: tests/auditoria/test_oraculos_r222b_wrappers.py

- manual: 7
  seccion: 4.2
  cita: "La respuesta se procesa (router) para extraer el código (si lo hay)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/router.syn:854
  oraculo: tests/auditoria/test_oraculos_r222b_wrappers.py
