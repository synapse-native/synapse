# Expediente de alineación r304_sbom_regeneracion

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 43531cfef7b85054

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## nucleo/sbom.py
- manual: 9
  seccion: 6.1
  cita: "□ **SBOM y SLSA**: generados y firmados correctamente."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/sbom.py:3
  oraculo: tests/auditoria/test_r304_sbom_determinista.py

