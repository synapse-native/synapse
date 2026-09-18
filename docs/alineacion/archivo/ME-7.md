# Expediente de alineación ME-7

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash:

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## opensyn/principal.syn
- manual: 7
  seccion: 2.1
  cita: "Se ejecuta en segundo plano y se comunica con el LSP mediante un socket local."
  tipo: comportamiento
  estado: PENDIENTE
  evidencia: opensyn/principal.syn:0
  oraculo: tests/

- manual: 7
  seccion: 4.2
  cita: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
  tipo: comportamiento
  estado: PENDIENTE
  evidencia: opensyn/principal.syn:0
  oraculo: tests/

## opensyn/router.syn
- manual: 7
  seccion: 2.4
  cita: "**Selección de modelo:** Si el usuario tiene múltiples modelos (ej. uno para código, uno para chat), el router decide cuál usar según la instrucción."
  tipo: comportamiento
  estado: PENDIENTE
  evidencia: opensyn/router.syn:0
  oraculo: tests/

- manual: 7
  seccion: 4.2
  cita: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
  tipo: comportamiento
  estado: PENDIENTE
  evidencia: opensyn/router.syn:0
  oraculo: tests/

## opensyn/permisos.syn
- manual: 7
  seccion: 7.3
  cita: "(sin oraciones indexadas)"
  tipo: comportamiento
  estado: PENDIENTE
  evidencia: opensyn/permisos.syn:0
  oraculo: tests/

## opensyn/planificador.syn
- manual: 7
  seccion: 2.1
  cita: "Se ejecuta en segundo plano y se comunica con el LSP mediante un socket local."
  tipo: comportamiento
  estado: PENDIENTE
  evidencia: opensyn/planificador.syn:0
  oraculo: tests/

## opensyn/run_manager.syn
- manual: 7
  seccion: 4.3
  cita: "(sin oraciones indexadas)"
  tipo: comportamiento
  estado: PENDIENTE
  evidencia: opensyn/run_manager.syn:0
  oraculo: tests/

## opensyn/validation_loop.syn
- manual: 7
  seccion: 6.3
  cita: "(sin oraciones indexadas)"
  tipo: comportamiento
  estado: PENDIENTE
  evidencia: opensyn/validation_loop.syn:0
  oraculo: tests/

## runtime/core/tui.c
- manual: 5
  seccion: 1
  cita: "**El estado mutable compartido entre hilos está prohibido** a nivel de compilación."
  tipo: comportamiento
  estado: PENDIENTE
  evidencia: runtime/core/tui.c:0
  oraculo: tests/

