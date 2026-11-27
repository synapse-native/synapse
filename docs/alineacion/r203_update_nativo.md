# Expediente de alineación r203_update_nativo

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 7d62c4c4b9752ec9

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
  evidencia: nucleo/principal.syn:41
  oraculo: tests/integration/test_release_matrix.py

- manual: 8
  seccion: 4.2
  cita: "| `--safe` | Activa verificación formal (ATP). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:975
  oraculo: tests/integration/test_cli.py

- manual: 8
  seccion: 4.1
  cita: "| `synapse lsp` | Inicia el servidor LSP (normalmente usado por la extensión). |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:32
  oraculo: tests/integration/test_cli.py

## nucleo/actualizador.syn
- manual: 9
  seccion: 3.1
  cita: "`--check`: solo verifica si hay actualizaciones disponibles, sin instalarlas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/actualizador.syn:316
  oraculo: tests/integration/test_update_nativo.py

- manual: 9
  seccion: 3.2
  cita: "**Verificación de versión**: Consulta el endpoint de versiones en GitHub Releases (o Axon Hub)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/actualizador.syn:3
  oraculo: tests/integration/test_update_nativo.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: contrato
  estado: CUMPLE
  evidencia: nucleo/actualizador.syn:4
  oraculo: tests/integration/test_contracts.py

## runtime/core/actualizador.c
- manual: 9
  seccion: 3.1
  cita: "`--check`: solo verifica si hay actualizaciones disponibles, sin instalarlas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/actualizador.c:1
  oraculo: tests/integration/test_update_nativo.py

- manual: 9
  seccion: 3.2
  cita: "**Verificación de versión**: Consulta el endpoint de versiones en GitHub Releases (o Axon Hub)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/actualizador.c:2
  oraculo: tests/integration/test_update_nativo.py

## runtime/core/actualizador.h
- manual: 9
  seccion: 3.1
  cita: "`--check`: solo verifica si hay actualizaciones disponibles, sin instalarlas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/actualizador.h:1
  oraculo: tests/integration/test_update_nativo.py

- manual: 9
  seccion: 3.2
  cita: "**Verificación de versión**: Consulta el endpoint de versiones en GitHub Releases (o Axon Hub)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/actualizador.h:2
  oraculo: tests/integration/test_update_nativo.py
