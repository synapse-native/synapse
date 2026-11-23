# Expediente de alineación r319_detect_hardware_mach_consts

base: a811a29  # commit sobre el que se leyó el manual
cambio_hash: ba28e765940f84b3

## runtime/core/detect_hardware.c
- manual: 9
  seccion: 6.2
  cita: "La suite de tests completa en cada target."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/detect_hardware.c:62
  oraculo: tests/auditoria/test_r319_detect_hardware_mach_consts.py

- manual: 9
  seccion: 5.7
  cita: "El módulo `std/os.syn` proporciona funciones de detección de hardware y sistema utilitarias, utilizadas por el instalador de OpenSyn (ver §5.1). Estas funciones están implementadas mediante FFI a llamadas del sistema operativo."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/detect_hardware.c:13
  oraculo: tests/auditoria/test_r319_detect_hardware_mach_consts.py
