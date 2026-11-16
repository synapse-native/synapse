# Expediente de alineación r222_std_texto_contracts

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: beb9f255cf3636f8

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## std/texto.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/texto.syn:13
  oraculo: tests/auditoria/test_oraculos_r222_std_texto.py

- manual: 2
  seccion: 5.1
  cita: "**`garantiza`:** Se evalúa inmediatamente antes de cada `retornar`. La variable `_resultado_` contiene el valor que se va a retornar."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/texto.syn:205
  oraculo: tests/auditoria/test_oraculos_r222_std_texto.py

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: contrato
  estado: CUMPLE
  evidencia: std/texto.syn:253
  oraculo: tests/auditoria/test_oraculos_r222_std_texto.py

- manual: 8
  seccion: 1.7.3
  cita: "Las funciones `contiene`, `indice_de` y `reemplazar` se implementan como builtins en C y se exponen en Synapse:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/texto.syn:14
  oraculo: tests/auditoria/test_oraculos_r222_std_texto.py
