# Expediente de alineación r242_native_opensyn_cli

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 4437bc919e048bd1

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:32
  oraculo: tests/auditoria/test_oraculos_r242_opensyn_nativo.py

- manual: 8
  seccion: 4.2
  cita: "| `--target` | `native`, `wasm`, `llvm` (por defecto `native`). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1199
  oraculo: tests/auditoria/test_oraculos_r242_opensyn_nativo.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse opensyn <subcomando>` | Comandos de OpenSyn (status, download, finetune, bindings, transpile). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1193
  oraculo: tests/auditoria/test_oraculos_r242_opensyn_nativo.py
