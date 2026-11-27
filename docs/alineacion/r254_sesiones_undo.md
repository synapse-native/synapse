# Expediente de alineación r254_sesiones_undo

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: d02e0967b131eb7a

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/principal.syn
- manual: 7
  seccion: 2.1
  cita: "El orquestador es un proceso en C que gestiona el ciclo de vida del servidor de inferencia (`llama-server`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:18
  oraculo: tests/opensyn/test_sesiones_undo_comportamiento.py

- manual: 7
  seccion: 2.3
  cita: "El pipeline RAG (Retrieval-Augmented Generation) es el cerebro de OpenSyn."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:32
  oraculo: tests/opensyn/test_sesiones_undo_comportamiento.py

- manual: 7
  seccion: 4.2
  cita: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:469
  oraculo: tests/opensyn/test_sesiones_undo_comportamiento.py

- manual: 7
  seccion: 7.3
  cita: "Cero telemetría: Verificado con monitoreo de red (sin conexiones salientes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:281
  oraculo: tests/opensyn/test_sesiones_undo_comportamiento.py

## opensyn/run_manager.syn
- manual: 7
  seccion: 4.3
  cita: "Si el servidor de inferencia no responde en 30 segundos, el LSP devuelve un error al usuario."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/run_manager.syn:3
  oraculo: tests/opensyn/test_sesiones_undo_comportamiento.py
