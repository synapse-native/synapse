# Expediente de alineación f31_deficiencias

base: HEAD
cambio_hash: 9ff428abd16eeafb

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## axon/axon_rt.c
- manual: 8
  seccion: 4.3
  cita: "El comando synapse init crea la siguiente estructura:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: axon/axon_rt.c:17
  oraculo: tests/axon/test_workspace.py

- manual: 6
  seccion: 5.1
  cita: "El formato de serialización para canales remotos es un subconjunto de MessagePack, optimizado para velocidad. Especificación normativa: el formato definitivo está en el Manual 5, §6.3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: axon/axon_rt.c:18
  oraculo: tests/axon/test_workspace.py

- manual: 8
  seccion: 4.4
  cita: "El CLI unificado gestiona las dependencias a través de Axon:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: axon/axon_rt.c:766
  oraculo: tests/axon/test_workspace.py

## nucleo/formatter.syn
- manual: 3
  seccion: 12
  cita: "Esta sección describe la estructura general de la biblioteca; las APIs específicas de cada módulo se especifican en los archivos .syq de la biblioteca estándar, cuyo diseño se detalla en la documentación de la Fase 24"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/formatter.syn:3
  oraculo: tests/nucleo/test_fmt.py

## nucleo/lint.syn
- manual: 3
  seccion: 12
  cita: "Esta sección describe la estructura general de la biblioteca; las APIs específicas de cada módulo se especifican en los archivos .syq de la biblioteca estándar, cuyo diseño se detalla en la documentación de la Fase 24"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/lint.syn:3
  oraculo: tests/nucleo/test_lint.py

## nucleo/principal.syn
- manual: 9
  seccion: 6.2
  cita: "Nuevo (Fase 31): synapse lint --check sobre el código fuente del compilador para verificar que el linter funciona correctamente."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/principal.syn:723
  oraculo: tests/nucleo/test_lint.py

## nucleo/reports.syn
- manual: 3
  seccion: 12
  cita: "Esta sección describe la estructura general de la biblioteca; las APIs específicas de cada módulo se especifican en los archivos .syq de la biblioteca estándar, cuyo diseño se detalla en la documentación de la Fase 24"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: nucleo/reports.syn:3
  oraculo: tests/integration/test_reports.py

## runtime/core/axon.c
- manual: 8
  seccion: 4.3
  cita: "El comando synapse init crea la siguiente estructura:"
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/axon.c:268
  oraculo: tests/axon/test_workspace.py

- manual: 6
  seccion: 5.1
  cita: "El formato de serialización para canales remotos es un subconjunto de MessagePack, optimizado para velocidad. Especificación normativa: el formato definitivo está en el Manual 5, §6.3."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/axon.c:270
  oraculo: tests/axon/test_workspace.py
