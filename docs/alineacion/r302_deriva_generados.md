# Expediente de alineación r302_deriva_generados

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 42ec57da65bfb713

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/bindings_generator.py
- manual: 7
  seccion: 2.1
  cita: "El orquestador es un proceso en C que gestiona el ciclo de vida del servidor de inferencia (`llama-server`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/bindings_generator.py:561
  oraculo: tests/auditoria/test_r302_generados_sin_deriva.py

## opensyn/full_pipeline.py
- manual: 7
  seccion: 2.1
  cita: "El orquestador es un proceso en C que gestiona el ciclo de vida del servidor de inferencia (`llama-server`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/full_pipeline.py:160
  oraculo: tests/auditoria/test_r302_generados_sin_deriva.py

## opensyn/generate_runtime_bindings.py
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/generate_runtime_bindings.py:1
  oraculo: tests/auditoria/test_r302_generados_sin_deriva.py
