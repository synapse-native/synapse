# Expediente de alineación r201_distribucion_real

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: a55d59bec59045c2

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## instaladores/common/auto_actualizar.py
- manual: 9
  seccion: 3.2
  cita: "**Verificación de versión**: Consulta el endpoint de versiones en GitHub Releases (o Axon Hub)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: instaladores/common/auto_actualizar.py:2
  oraculo: tests/installers/test_auto_actualizar_producto.py

- manual: 9
  seccion: 4.1
  cita: "Los artefactos se publican en la sección **Releases** del repositorio de GitHub."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: instaladores/common/auto_actualizar.py:3
  oraculo: tests/installers/test_auto_actualizar_producto.py

- manual: 1
  seccion: 3.1
  cita: "El compilador unificado procesa código fuente de Synapse (.syn), Syquex (.syq) e incluso prompts en lenguaje natural (via OpenSyn) a través de un pipeline compartido:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: instaladores/common/auto_actualizar.py:4
  oraculo: tests/installers/test_auto_actualizar_producto.py
