# Expediente de alineación r317_detect_hardware_macos

base: 499afd9  # commit sobre el que se leyó el manual
cambio_hash:

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## runtime/core/detect_hardware.c
- manual: 9
  seccion: 5.7
  cita: "El módulo `std/os.syn` proporciona funciones de detección de hardware y sistema utilitarias, utilizadas por el instalador de OpenSyn (ver §5.1). Estas funciones están implementadas mediante FFI a llamadas del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/detect_hardware.c:13
  oraculo: tests/auditoria/test_r317_detect_hardware_macos.py

- manual: 9
  seccion: 6.2
  cita: "La suite de tests completa en cada target."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/detect_hardware.c:59
  oraculo: tests/auditoria/test_r317_detect_hardware_macos.py

## nucleo/detect_hardware.c
- manual: 9
  seccion: 5.7
  cita: "El módulo `std/os.syn` proporciona funciones de detección de hardware y sistema utilitarias, utilizadas por el instalador de OpenSyn (ver §5.1). Estas funciones están implementadas mediante FFI a llamadas del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/detect_hardware.c:14
  oraculo: tests/auditoria/test_r317_detect_hardware_macos.py

- manual: 9
  seccion: 6.2
  cita: "La suite de tests completa en cada target."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/detect_hardware.c:132
  oraculo: tests/auditoria/test_r317_detect_hardware_macos.py
