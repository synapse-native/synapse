# Expediente de alineación r237_instalador_toolchain

base: HEAD  # commit sobre el que se leyó el manual (a08bcef)
cambio_hash: 7b4be78d842ad19e

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## instaladores/windows/empaquetar_toolchain.py
- manual: 9
  seccion: 2.5
  cita: "El script `installer.iss` de Inno Setup para Windows:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: instaladores/windows/empaquetar_toolchain.py:5
  oraculo: tests/auditoria/test_oraculos_r237_instalador_toolchain.py

- manual: 9
  seccion: 7
  cita: "| Instalación en Windows (limpiamente) | Ejecutar instalador en máquina virtual Windows limpia | Instalación exitosa, PATH configurado, `synapse --version` funciona. |"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: instaladores/windows/empaquetar_toolchain.py:139
  oraculo: tests/auditoria/test_oraculos_r237_instalador_toolchain.py
