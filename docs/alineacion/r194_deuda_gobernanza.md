# Expediente de alineación r194_deuda_gobernanza

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 060024ceeb5779fb

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## compilador/generator/emit_expressions.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:1
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:663
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

- manual: 5
  seccion: 3.6
  cita: "Cuando se cierra un canal (`cerrar()`), los receptores que intenten recibir obtienen un `Resultado<T, Error>` que indica cierre."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:1123
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

## compilador/generator/generator.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:680
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: seguridad
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:830
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

## nucleo/generador/expr_eval.syn
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/expr_eval.syn:470
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/expr_eval.syn:455
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: seguridad
  estado: CUMPLE
  evidencia: nucleo/generador/expr_eval.syn:508
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

## nucleo/generador/orquestador.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:336
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: seguridad
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:487
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

## nucleo/generator.syn
- manual: 2
  seccion: 5
  cita: "CONTRATOS LÓGICOS (`requiere` / `garantiza`)"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:11
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: seguridad
  estado: CUMPLE
  evidencia: nucleo/generator.syn:1040
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

## runtime/core/sistema.c
- manual: 2
  seccion: 9.1
  cita: "**Semántica de Movimiento (*Move Semantics*):** Al asignar una variable propietaria a otra o pasarla como argumento de función por valor, la posesión se transfiere (*move*). La variable original queda invalidada en el ámbito origen."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/sistema.c:32
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

- manual: 5
  seccion: 1
  cita: "**El estado mutable compartido entre hilos está prohibido** a nivel de compilación."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/sistema.c:44
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: seguridad
  estado: CUMPLE
  evidencia: runtime/core/sistema.c:156
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

## runtime/core/sistema.h
- manual: 5
  seccion: 1
  cita: "**El estado mutable compartido entre hilos está prohibido** a nivel de compilación."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/sistema.c:44
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py

- manual: 7
  seccion: 7.3
  cita: "**Sandboxing:** El servidor de inferencia se ejecuta con permisos mínimos."
  tipo: seguridad
  estado: CUMPLE
  evidencia: runtime/core/sistema.h:17
  oraculo: tests/auditoria/test_oraculos_r194_sandbox.py
