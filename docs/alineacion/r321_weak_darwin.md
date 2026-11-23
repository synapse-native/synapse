# Expediente de alineación r321_weak_darwin

base: 23e023f  # commit sobre el que se leyó el manual
cambio_hash: 01820e03d39931d7

## compilador/generator/emit_declarations.py
- manual: 9
  seccion: 6.2
  cita: "La suite de tests completa en cada target."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_declarations.py:635
  oraculo: tests/auditoria/test_r321_weak_darwin.py

- manual: 2
  seccion: 1.3
  cita: "**Comentarios de línea:** comienzan con `//` y se extienden hasta el final de la línea."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_declarations.py:633
  oraculo: tests/auditoria/test_r321_weak_darwin.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: compilador/generator/emit_declarations.py:634
  oraculo: tests/auditoria/test_r321_weak_darwin.py

## nucleo/generador/funciones.syn
- manual: 9
  seccion: 6.2
  cita: "La suite de tests completa en cada target."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/funciones.syn:221
  oraculo: tests/auditoria/test_r321_weak_darwin.py

- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/generador/funciones.syn:220
  oraculo: tests/auditoria/test_r321_weak_darwin.py
