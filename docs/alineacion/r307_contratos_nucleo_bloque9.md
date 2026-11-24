# Expediente de alineación r307_contratos_nucleo_bloque9

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: a04150e75dc30879

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/lexer.syn
- manual: 2
  seccion: 1.1
  cita: "Todo archivo fuente de Synapse **debe** comenzar con la directiva de idioma en la **línea 1**:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:559
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:1007
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 3
  cita: "| TokenID | Español (es) | Inglés (en) | Francés (fr) | Portugués (pt) |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:4
  oraculo: auditoria/verificar_contratos.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer.syn:1100
  oraculo: auditoria/verificar_contratos.py

## nucleo/lexer_keywords.syn
- manual: 2
  seccion: 3
  cita: "| TokenID | Español (es) | Inglés (en) | Francés (fr) | Portugués (pt) |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer_keywords.syn:2
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lexer_keywords.syn:21
  oraculo: auditoria/verificar_contratos.py

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:33
  oraculo: auditoria/verificar_contratos.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:33
  oraculo: auditoria/verificar_contratos.py

- manual: 8
  seccion: 4.2
  cita: "| `--safe` | Activa verificación formal (ATP). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:72
  oraculo: auditoria/verificar_contratos.py

- manual: 8
  seccion: 3.1
  cita: "Synapse/Syquex incluye un debugger nativo que soporta **time‑travel debugging** (grabación y reproducción de la ejecución) y **breakpoints reversibles** (retroceder la ejecución)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1388
  oraculo: auditoria/verificar_contratos.py

- manual: 8
  seccion: 3.4
  cita: "El CLI unificado (`synapse`) incluye comandos para depuración:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1389
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:2
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:56
  oraculo: auditoria/verificar_contratos.py

## nucleo/resolvedor_axon.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/resolvedor_axon.syn:12
  oraculo: auditoria/verificar_contratos.py

## nucleo/lsp.syn
- manual: 8
  seccion: 1.1
  cita: "Soporta Synapse (`.syn`) y Syquex (`.syq`) de forma transparente."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp.syn:2
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp.syn:37
  oraculo: auditoria/verificar_contratos.py

## nucleo/lsp_v3.syn
- manual: 8
  seccion: 1.1
  cita: "Soporta Synapse (`.syn`) y Syquex (`.syq`) de forma transparente."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:2
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:356
  oraculo: auditoria/verificar_contratos.py

## nucleo/analizador_semantico.syn
- manual: 2
  seccion: 4.2
  cita: "**Regla Semántica:** El uso de estos tipos exige de manera obligatoria la instrucción de control `coincidir`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:1198
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 8.1
  cita: "**Pasada 2 (Firmas de Funciones):** Analiza las cabeceras de todas las funciones, validando los tipos de los parámetros, los tipos de retorno y los contratos lógicos (`requiere`/`garantiza`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:1062
  oraculo: auditoria/verificar_contratos.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:170
  oraculo: auditoria/verificar_contratos.py

## nucleo/optimizador_ia.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/optimizador_ia.syn:61
  oraculo: auditoria/verificar_contratos.py

