# Expediente de alineación r281_cache_runtime_nativa

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 8140c12bce93120e

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:854
  oraculo: tests/unit/test_r3_param_adt.py

- manual: 8
  seccion: 4.2
  cita: "| `--release` | Compila en modo release (optimizaciones). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:830
  oraculo: auditoria/oraculos/oraculo_r281_cache_nativa.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse build <archivo>` | Compila el archivo (`.syn` o `.syq`) a binario. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:796
  oraculo: auditoria/oraculos/oraculo_r281_cache_nativa.py
