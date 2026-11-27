# Expediente de alineación config_ruta_absoluta

base: HEAD  # commit sobre el que se leyó el manual
cambio_hash: 3bbc157ea5ebcec9

> Una ancla por requisito. `estado:` CUMPLE | DESVIACION.
> CUMPLE exige `evidencia: archivo:linea` con el comentario
> `// cumple Manual X §Y` en ±3 líneas y un `oraculo:` ejecutable.
> DESVIACION exige `correccion: archivo:linea-linea` que toque el diff
> (o `decision: D-xxx` ratificada en la bitácora).

## runtime/core/sistema.c
- manual: 2
  seccion: 9.1
  cita: "**Semántica de Movimiento (*Move Semantics*):** Al asignar una variable propietaria a otra o pasarla como argumento de función por valor, la posesión se transfiere (*move*). La variable original queda invalidada en el ámbito origen."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/sistema.c:99
  oraculo: tests/auditoria/test_oraculos_config_ruta.py
  ejecucion: pytest

- manual: 5
  seccion: 1
  cita: "**El estado mutable compartido entre hilos está prohibido** a nivel de compilación."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: runtime/core/sistema.c:44
  oraculo: tests/auditoria/test_oraculos_config_ruta.py
  ejecucion: pytest

## std/sistema.syn
- manual: 2
  seccion: 5.1
  cita: "**`requiere`:** Se evalúa antes de la primera instrucción del cuerpo. Todas las expresiones deben ser booleanas."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: std/sistema.syn:24
  oraculo: tests/auditoria/test_oraculos_config_ruta.py
  ejecucion: pytest

## opensyn/principal.syn
- manual: 7
  seccion: 2.1
  cita: "Se ejecuta en segundo plano y se comunica con el LSP mediante un socket local."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:209
  oraculo: tests/auditoria/test_oraculos_config_ruta.py
  ejecucion: pytest

- manual: 7
  seccion: 4.2
  cita: "El LSP es el responsable de orquestar el bucle de validación (descrito en la sección 6.3)."
  tipo: comportamiento
  estado: CUMPLE
  evidencia: opensyn/principal.syn:365
  oraculo: tests/auditoria/test_oraculos_config_ruta.py
  ejecucion: pytest
