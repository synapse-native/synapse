# Expediente de alineación r181_harness_gcc

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 940ab0dead0a47ff

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## compilador/generator/generator.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:1108
  oraculo: tests/auditoria/test_oraculos_harness_gcc.py

## nucleo/generador/orquestador.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/orquestador.syn:492
  oraculo: tests/auditoria/test_oraculos_harness_gcc.py

## nucleo/generator.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:5057
  oraculo: tests/auditoria/test_oraculos_harness_gcc.py

