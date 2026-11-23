# Expediente de alineación r301_generator_reconciliacion

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: efa482a07afbd0ae

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/generador/contexto.syn
- manual: 2
  seccion: 8.2
  cita: "Synapse utiliza un algoritmo de inferencia de tipos basado en **Hindley‑Milner** (algoritmo W)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/contexto.syn:3
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## nucleo/generador/emision_c.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/emision_c.syn:3
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## nucleo/generador/expr_eval.syn
- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/expr_eval.syn:470
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/expr_eval.syn:455
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## nucleo/generador/funciones.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/funciones.syn:212
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## nucleo/generador/nodos_flujo.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/nodos_flujo.syn:370
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## nucleo/generador/orquestador.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:336
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py

## nucleo/generator.syn
- manual: 2
  seccion: 8.2
  cita: "Synapse utiliza un algoritmo de inferencia de tipos basado en **Hindley‑Milner** (algoritmo W)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:10
  oraculo: tests/auditoria/test_r301_generator_reconciliacion.py
