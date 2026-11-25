# Expediente de alineacion r323b_gdir_escaping

base: HEAD
cambio_hash: cf45ed74d54ad723

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:711
  oraculo: tests/auditoria/test_r323b_gdir_escaping.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:953
  oraculo: tests/auditoria/test_r323b_gdir_escaping.py

- manual: 8
  seccion: 4.2
  cita: "| `--safe` | Activa verificación formal (ATP). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:72
  oraculo: tests/auditoria/test_r323b_gdir_escaping.py

- manual: 8
  seccion: 3.1
  cita: "Synapse/Syquex incluye un debugger nativo que soporta **time‑travel debugging** (grabación y reproducción de la ejecución) y **breakpoints reversibles** (retroceder la ejecución)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1390
  oraculo: tests/auditoria/test_r323b_gdir_escaping.py

- manual: 8
  seccion: 3.4
  cita: "El CLI unificado (`synapse`) incluye comandos para depuración:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1391
  oraculo: tests/auditoria/test_r323b_gdir_escaping.py

- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:2
  oraculo: tests/auditoria/test_r323b_gdir_escaping.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:56
  oraculo: tests/auditoria/test_r323b_gdir_escaping.py
