# Expediente de alineación r323_darwin_bootstrap_selfhost

base: 63a2881
cambio_hash: 40618c77d1474b6a

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:665
  oraculo: tests/auditoria/test_r322_darwin_gcc.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:188
  oraculo: tests/auditoria/test_r322_darwin_gcc.py

- manual: 8
  seccion: 4.2
  cita: "| `--safe` | Activa verificación formal (ATP). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:62
  oraculo: tests/auditoria/test_r322_darwin_gcc.py

- manual: 8
  seccion: 3.1
  cita: "Synapse/Syquex incluye un debugger nativo que soporta **time‑travel debugging** (grabación y reproducción de la ejecución) y **breakpoints reversibles** (retroceder la ejecución)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1363
  oraculo: tests/auditoria/test_r322_darwin_gcc.py

- manual: 8
  seccion: 3.4
  cita: "El CLI unificado (`synapse`) incluye comandos para depuración:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1364
  oraculo: tests/auditoria/test_r322_darwin_gcc.py

- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:2
  oraculo: tests/auditoria/test_r322_darwin_gcc.py

## nucleo/generador/compilar.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/compilar.syn:70
  oraculo: tests/auditoria/test_r322_darwin_gcc.py
