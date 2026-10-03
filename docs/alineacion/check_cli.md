# Expediente de alineación check_cli

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 4fbd413e1b931cb4

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## cli.py
- manual: 1
  seccion: 3.2
  cita: "Convierte el AST de Syquex (alto nivel) al AST canónico `SemNodo[]` de Synapse."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: cli.py:1
  oraculo: tests/auditoria/test_oraculos_check_cli.py
- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: cli.py:988
  oraculo: tests/auditoria/test_oraculos_check_cli.py

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "La verificación del bootstrap (diff 0 bytes)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:32
  oraculo: tests/auditoria/test_oraculos_check_cli.py
- manual: 8
  seccion: 4.2
  cita: "| **`--check`** / **`--no-emit`** | **Modo de validación:** Solo verifica la sintaxis y semántica, sin generar código de salida."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:801
  oraculo: tests/auditoria/test_oraculos_check_cli.py
