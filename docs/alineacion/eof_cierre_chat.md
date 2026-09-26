# Expediente de alineación eof_cierre_chat

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: e76364ddd0a7b712

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/principal.syn
- manual: 7
  seccion: 2.1
  cita: "Se ejecuta en segundo plano y se comunica con el LSP mediante un socket local."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:1490
  oraculo: tests/auditoria/test_oraculos_eof_cierre.py
  ejecucion: pytest

- manual: 7
  seccion: 4.2
  cita: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:336
  oraculo: tests/auditoria/test_oraculos_eof_cierre.py
  ejecucion: pytest

