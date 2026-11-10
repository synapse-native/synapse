# Expediente de alineación r206_validation_loop

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: dc81f3f85c2e19f4

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/validation_loop.syn
- manual: 7
  seccion: 6.3
  cita: "Dado que OpenSyn no es perfecto y puede generar código con errores sintácticos o semánticos, se implementa un **bucle de validación y corrección automática** orquestado por el LSP (ver sección 4.2)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/validation_loop.syn:3
  oraculo: tests/opensyn/test_validation_loop_comportamiento.py
- manual: 7
  seccion: 6.3
  cita: "**Validación:** El LSP pasa el código al compilador de Synapse/Syquex en modo `--check` (solo validación, sin generar binario). Este modo es activado con el flag `--no-emit` (o similar) que debe estar implementado en el CLI de Synapse."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/validation_loop.syn:63
  oraculo: tests/opensyn/test_validation_loop_comportamiento.py
- manual: 7
  seccion: 6.3
  cita: "**Si falla:** El compilador devuelve el error exacto (línea, columna, mensaje) a través de su salida de error estándar. El LSP:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/validation_loop.syn:111
  oraculo: tests/opensyn/test_validation_loop_comportamiento.py
- manual: 7
  seccion: 6.3
  cita: "Construye un nuevo prompt añadiendo: *"El código anterior tiene el siguiente error: {mensaje_error}. Por favor, corrígelo."*"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/validation_loop.syn:165
  oraculo: tests/opensyn/test_validation_loop_comportamiento.py
- manual: 7
  seccion: 6.3
  cita: "**Mecanismo de Feedback Humano:**"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/validation_loop.syn:208
  oraculo: tests/opensyn/test_validation_loop_comportamiento.py
- manual: 7
  seccion: 6.3
  cita: "**Fallo definitivo:** Si el tercer intento falla, el LSP muestra el último código generado y los errores al usuario, con un mensaje: *"No se pudo generar código válido automáticamente. Intenta ajustar la instrucción o corrige manualmente."*"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/validation_loop.syn:294
  oraculo: tests/opensyn/test_validation_loop_comportamiento.py
