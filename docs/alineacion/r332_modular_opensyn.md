# Expediente de alineación r332_modular_opensyn

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 8393b56afe956902

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.

## compilador/generator/emit_expressions.py
- manual: 2
  seccion: 12
  cita: "| Contratos requiere/garantiza | `pytest tests/integration/test_contracts.py -v` | 100% pass |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:840
  oraculo: tests/auditoria/test_oraculos_opensyn_exe.py

- manual: 6
  seccion: 3.1
  cita: "Tanto Synapse como Syquex permiten declarar funciones de C con la palabra clave `externo`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:841
  oraculo: tests/auditoria/test_oraculos_opensyn_exe.py

- manual: 5
  seccion: 3.6
  cita: "Cuando se cierra un canal (`cerrar()`), los receptores que intenten recibir obtienen un `Resultado<T, Error>` que indica cierre."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_expressions.py:842
  oraculo: tests/auditoria/test_oraculos_opensyn_exe.py

## compilador/generator/generator.py
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/generator.py:771
  oraculo: tests/auditoria/test_oraculos_opensyn_exe.py
