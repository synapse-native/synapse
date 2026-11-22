# Expediente de alineación r274_bootstrap_contracts

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: dba5a0f898edb9e9

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/analizador_semantico.syn
- manual: 2
  seccion: 4.2
  cita: "**Regla Semántica:** El uso de estos tipos exige de manera obligatoria la instrucción de control `coincidir`."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:897
  oraculo: tests/integration/test_contracts.py

- manual: 2
  seccion: 8.1
  cita: "**Pasada 2 (Firmas de Funciones):** Analiza las cabeceras de todas las funciones, validando los tipos de los parámetros, los tipos de retorno y los contratos lógicos (`requiere`/`garantiza`)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/analizador_semantico.syn:803
  oraculo: tests/integration/test_contracts.py

## nucleo/generador/emision_c.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/emision_c.syn:3
  oraculo: tests/integration/test_contracts.py

## nucleo/generator.syn
- manual: 2
  seccion: 8.2
  cita: "Synapse utiliza un algoritmo de inferencia de tipos basado en **Hindley‑Milner** (algoritmo W)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generator.syn:4659
  oraculo: tests/integration/test_contracts.py

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:33
  oraculo: tests/auditoria/test_r274_observability_asm.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:33
  oraculo: tests/auditoria/test_r274_observability_asm.py

- manual: 8
  seccion: 4.2
  cita: "| `--safe` | Activa verificación formal (ATP). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:62
  oraculo: tests/auditoria/test_r274_observability_asm.py

- manual: 8
  seccion: 3.1
  cita: "Synapse/Syquex incluye un debugger nativo que soporta **time‑travel debugging** (grabación y reproducción de la ejecución) y **breakpoints reversibles** (retroceder la ejecución)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1323
  oraculo: tests/auditoria/test_r274_observability_asm.py

- manual: 8
  seccion: 3.4
  cita: "El CLI unificado (`synapse`) incluye comandos para depuración:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:1324
  oraculo: tests/auditoria/test_r274_observability_asm.py

- manual: 2
  seccion: 1.2
  cita: "Todos los archivos fuente deben estar codificados en **UTF‑8 sin BOM**."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:2
  oraculo: tests/auditoria/test_r274_observability_asm.py
