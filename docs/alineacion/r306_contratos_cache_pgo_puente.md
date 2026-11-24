# Expediente de alineación r306_contratos_cache_pgo_puente

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: f49fdc6236f05c23

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/cache.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/cache.syn:73
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: nucleo/cache.syn:53
  oraculo: auditoria/verificar_contratos.py

## nucleo/generator_pgo.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: nucleo/generator_pgo.syn:52
  oraculo: auditoria/verificar_contratos.py

## nucleo/puente_ast.syn
- manual: 2
  seccion: 7.2
  cita: "> Fuente canónica completa: `nucleo/parser_constantes.syn` (genera"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/puente_ast.syn:329
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: nucleo/puente_ast.syn:46
  oraculo: auditoria/verificar_contratos.py
