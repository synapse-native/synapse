# Expediente de alineación r236_toolchain_gcc

base: HEAD  # commit sobre el que se leyó el manual (5227150)
cambio_hash: 4871e66aeb5e856c

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "La suite de tests completa en cada target."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:619
  oraculo: tests/auditoria/test_oraculos_r236_toolchain_gcc.py

- manual: 8
  seccion: 4.2
  cita: "| `--debug` | Compila con información de depuración. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:656
  oraculo: tests/auditoria/test_oraculos_r236_toolchain_gcc.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse build <archivo>` | Compila el archivo (`.syn` o `.syq`) a binario. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:738
  oraculo: tests/auditoria/test_oraculos_r236_toolchain_gcc.py
