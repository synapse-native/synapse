# Expediente de alineación r208_run_manager

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 10cc67173f42e68a

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/run_manager.syn
- manual: 7
  seccion: 4.3
  cita: "Si el servidor de inferencia no responde en 30 segundos, el LSP devuelve un error al usuario."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/run_manager.syn:199
  oraculo: tests/opensyn/test_run_manager_comportamiento.py

- manual: 7
  seccion: 4.3
  cita: "Si el código generado es inválido y se agotan los intentos, el LSP muestra un mensaje y ofrece regenerar (o pedir ayuda al usuario)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/run_manager.syn:131
  oraculo: tests/opensyn/test_run_manager_comportamiento.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/run_manager.syn:53
  oraculo: tests/opensyn/test_run_manager_comportamiento.py

- manual: 2
  seccion: 5.1
  cita: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/run_manager.syn:76
  oraculo: tests/opensyn/test_run_manager_comportamiento.py
