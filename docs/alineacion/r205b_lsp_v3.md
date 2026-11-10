# Expediente de alineación r205b_lsp_v3

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: c01c7e55ec8d56b9

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/lsp_v3.syn
- manual: 8
  seccion: 1.2
  cita: "El LSP lee cabeceras HTTP‑like de la entrada estándar. Cada mensaje comienza con una cabecera `Content-Length:` seguida del tamaño del cuerpo JSON."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:24
  oraculo: tests/unit/test_lsp_multimsg.py

- manual: 8
  seccion: 1.7.3
  cita: "Las funciones `contiene`, `indice_de` y `reemplazar` se implementan como builtins en C y se exponen en Synapse:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:25
  oraculo: tests/integration/test_lsp_workspace.py

- manual: 8
  seccion: 1.3
  cita: "**Finalización**: el LSP se cierra cuando el editor cierra la conexión."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:357
  oraculo: tests/integration/test_lsp_protocol_validation.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lsp_v3.syn:356
  oraculo: tests/integration/test_lsp_protocol_validation.py
