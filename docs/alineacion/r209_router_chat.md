# Expediente de alineación r209_router_chat

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: d0a46a4e11076ea6

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/router.syn
- manual: 7
  seccion: 2.4
  cita: "**Formateo de respuesta:** Extrae el código de la respuesta del modelo (usando expresiones regulares o parseo de bloques), lo valida con el compilador, y lo muestra."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/router.syn:485
  oraculo: tests/opensyn/test_router_chat_comportamiento.py

- manual: 7
  seccion: 4.2
  cita: "**Validación (paso crítico):** El LSP toma el código generado y ejecuta el compilador de Synapse/Syquex en modo `--check` (solo validación, sin generar binario). Esto se hace mediante el CLI `synapse check --no-emit <archivo>`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/router.syn:875
  oraculo: tests/opensyn/test_router_chat_comportamiento.py

## opensyn/chat.syn
- manual: 7
  seccion: 6.2
  cita: "**Nota de restauración (2026-10-01):** Sección restaurada textualmente por decisión del Arquitecto (Opción A, ME barrido_citas_v820) tras su eliminación involuntaria en la revisión de manuales v8.2.0 (commit 154a544); con ella, la selección de modelo (`[modelo]` nombre/ruta) vuelve a tener hogar normativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/chat.syn:126
  oraculo: tests/opensyn/test_router_chat_comportamiento.py

- manual: 7
  seccion: 8
  cita: "El LSP valida con `synapse check --no-emit` (compila correctamente)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/chat.syn:177
  oraculo: tests/opensyn/test_router_chat_comportamiento.py
