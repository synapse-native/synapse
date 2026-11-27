# Expediente de alineación r27_ctor_aridad

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 1ff87d0097335768

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/analizador_semantico.syn
- manual: 2
  seccion: 8.2
  cita: "Synapse utiliza un algoritmo de inferencia de tipos basado en **Hindley‑Milner** (algoritmo W)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:733
  oraculo: tests/auditoria/test_oraculos_r27_ctor_aridad.py
