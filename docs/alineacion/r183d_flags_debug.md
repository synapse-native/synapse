# Expediente de alineación r183d

base: 3c91c58  # commit sobre el que se leyó el manual
cambio_hash: bf54ba579129ed4c

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas. DESVIACION exige
> `correccion: archivo:linea-linea` que toque el diff (o `decision: D-xxx`
> ratificada en la bitácora).

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: contrato
  estado: CUMPLE
  evidencia: nucleo/principal.syn:826
  oraculo: auditoria/oraculos/oraculo_r183d.py

- manual: 8
  seccion: 4.2
  cita: "| `--target` | `native`, `wasm`, `llvm` (por defecto `native`). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:954
  oraculo: auditoria/oraculos/oraculo_r183d.py

- manual: 8
  seccion: 4.2
  cita: "| `--output` | Especifica el nombre del binario de salida. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1150
  oraculo: auditoria/oraculos/oraculo_r183d.py

- manual: 9
  seccion: 6.1
  cita: "□ **Sanitizadores**: ASan/UBSan/TSan no reportan errores (en los targets que lo soportan)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:630
  oraculo: auditoria/oraculos/oraculo_r183d.py

- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1119
  oraculo: auditoria/oraculos/oraculo_r183d.py

## pipeline.py
- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:130
  oraculo: auditoria/oraculos/oraculo_r183d.py

- manual: 9
  seccion: 6.1
  cita: "□ **Sanitizadores**: ASan/UBSan/TSan no reportan errores (en los targets que lo soportan)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:670
  oraculo: auditoria/oraculos/oraculo_r183d.py
