# Expediente de alineación r256_debugger

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: c3be53831d302078

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
  evidencia: nucleo/principal.syn:1220
  oraculo: tests/auditoria/test_oraculos_r256_debugger.py

- manual: 8
  seccion: 4.2
  cita: "| `--safe` | Activa verificación formal (ATP). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1221
  oraculo: tests/auditoria/test_oraculos_r256_debugger.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1222
  oraculo: tests/auditoria/test_oraculos_r256_debugger.py

## runtime/core/debug.c
- manual: 9
  seccion: 1
  cita: "| **Instalación de un solo clic** | El usuario descarga un instalador (o ejecuta un script) y, en pocos pasos, tiene Synapse (y opcionalmente Syquex y OpenSyn) listo para usar. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/debug.c:416
  oraculo: tests/auditoria/test_oraculos_r256_debugger.py

## runtime/core/debug.h
- manual: 5
  seccion: 2.6
  cita: "Se asigna una pila (por defecto 64 KB)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/debug.h:57
  oraculo: tests/auditoria/test_oraculos_r256_debugger.py
