# Expediente de alineación r320_ld64_dup_flag

base: 11a0888  # commit sobre el que se leyó el manual
cambio_hash: 805b73291a740ffd

## pipeline.py
- manual: 9
  seccion: 6.2
  cita: "La suite de tests completa en cada target."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:1026
  oraculo: tests/auditoria/test_r320_ld64_dup_flag.py

- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: pipeline.py:182
  oraculo: tests/auditoria/test_r320_ld64_dup_flag.py

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "La suite de tests completa en cada target."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:804
  oraculo: tests/auditoria/test_r320_ld64_dup_flag.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:793
  oraculo: tests/auditoria/test_r320_ld64_dup_flag.py

- manual: 8
  seccion: 4.2
  cita: "| `--safe` | Activa verificación formal (ATP). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:89
  oraculo: tests/auditoria/test_r320_ld64_dup_flag.py

- manual: 8
  seccion: 3.1
  cita: "Synapse/Syquex incluye un debugger nativo que soporta **time‑travel debugging** (grabación y reproducción de la ejecución) y **breakpoints reversibles** (retroceder la ejecución)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1345
  oraculo: tests/auditoria/test_r320_ld64_dup_flag.py

- manual: 8
  seccion: 3.4
  cita: "El CLI unificado (`synapse`) incluye comandos para depuración:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1346
  oraculo: tests/auditoria/test_r320_ld64_dup_flag.py

- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:2
  oraculo: tests/auditoria/test_r320_ld64_dup_flag.py
